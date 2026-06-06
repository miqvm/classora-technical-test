from datetime import datetime, timedelta, timezone

import pytest

from exercise_2.domain.models import Alert
from exercise_2.domain.filters import AlertFilters
from exercise_2.infrastructure.database.repository import (
    MongoAlertRepository,
)


class FakeCollection:
    """
    A simple in-memory collection to simulate MongoDB operations for testing.
    """
    def __init__(self):
        self.documents = {}

    # Replace or insert a document by ID (upsert operation)
    async def replace_one(
        self,
        filter_,
        document,
        upsert=False,
    ):
        # Store document using filter ID as key
        self.documents[filter_["_id"]] = document

    # Find a single document matching query criteria
    async def find_one(
        self,
        query,
        sort=None,
    ):
        # If searching by ID, return document directly
        if "_id" in query:
            return self.documents.get(query["_id"])

        # List to store matching documents
        matches = []

        # Iterate through all stored documents
        for doc in self.documents.values():

            # Skip if title doesn't match
            if doc["title"] != query["title"]:
                continue

            # Skip if source IP doesn't match
            if doc["source_ip"] != query["source_ip"]:
                continue

            # Skip if updated_at is before threshold
            if doc["updated_at"] < query["updated_at"]["$gte"]:
                continue

            # Add matching document to results
            matches.append(doc)

        # Return None if no matches found
        if not matches:
            return None

        # Sort matches by creation date in descending order
        matches.sort(
            key=lambda x: x["updated_at"],
            reverse=True,
        )

        # Return most recent match
        return matches[0]

    # Find multiple documents matching query criteria
    def find(self, query):
        # Start with all documents
        docs = list(self.documents.values())

        # Filter by severity if provided
        if "severity" in query:
            docs = [d for d in docs if d["severity"] == query["severity"]]

        # Filter by source IP if provided
        if "source_ip" in query:
            docs = [d for d in docs if d["source_ip"] == query["source_ip"]]

        # Filter by creation date if provided
        if "created_at" in query:
            docs = [d for d in docs if d["created_at"] < query["created_at"]["$lt"]]

        # Return cursor for document iteration
        return FakeCursor(docs)

    # Create an index (no-op for fake implementation)
    async def create_index(self, *args, **kwargs):
        pass


# Fake cursor for iterating through documents
class FakeCursor:
    # Initialize cursor with list of documents
    def __init__(self, docs):
        self.docs = docs

    # Sort documents by field in descending order
    def sort(self, field, direction):
        # Sort documents by specified field
        self.docs.sort(
            key=lambda x: x[field],
            reverse=True,
        )
        # Return self for method chaining
        return self

    # Limit number of documents returned
    def limit(self, value):
        # Truncate documents list to limit value
        self.docs = self.docs[:value]
        # Return self for method chaining
        return self

    # Convert cursor to list of documents asynchronously
    async def to_list(self, length):
        # Return documents up to specified length
        return self.docs[:length]


# Pytest fixture providing a repository instance with fake collection
@pytest.fixture
def repository():
    # Create and return MongoAlertRepository with FakeCollection
    return MongoAlertRepository(FakeCollection())


# Helper function to build test Alert objects
def build_alert(
    alert_id="1",
    severity="high",
):
    # Create and return an Alert instance with test data
    return Alert(
        alert_id=alert_id,
        title="SQL Injection",
        severity=severity,
        source_ip="192.168.1.10",
        description="attack",
        tags=[],
        status="new",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# Test saving and retrieving an alert by ID
@pytest.mark.asyncio
async def test_save_and_find_by_id(
    repository,
):
    # Create a test alert
    alert = build_alert()

    # Save alert to repository
    await repository.save(alert)

    # Retrieve alert by ID
    found = await repository.find_by_id(alert.alert_id)

    # Verify alert was found
    assert found is not None
    # Verify alert ID matches
    assert found.alert_id == alert.alert_id
    # Verify alert title matches
    assert found.title == alert.title


# Test finding non-existent alert returns None
@pytest.mark.asyncio
async def test_find_by_id_returns_none(
    repository,
):
    # Try to find missing alert
    result = await repository.find_by_id("missing")

    # Verify result is None
    assert result is None


# Test finding a recent duplicate alert
@pytest.mark.asyncio
async def test_find_recent_duplicate_found(
    repository,
):
    # Create test alert
    alert = build_alert()

    # Save alert to repository
    await repository.save(alert)

    # Search for recent duplicate
    duplicate = await repository.find_recent_duplicate(
        title=alert.title,
        source_ip=alert.source_ip,
        within_seconds=300,
    )

    # Verify duplicate was found
    assert duplicate is not None


# Test that old alerts are not considered duplicates
@pytest.mark.asyncio
async def test_find_recent_duplicate_not_found(
    repository,
):
    # Create old test alert
    old_alert = build_alert()

    # Set creation time to 10 minutes ago
    old_alert.updated_at = datetime.now(timezone.utc) - timedelta(minutes=10)

    # Save old alert to repository
    await repository.save(old_alert)

    # Search for recent duplicate within 300 seconds
    duplicate = await repository.find_recent_duplicate(
        title=old_alert.title,
        source_ip=old_alert.source_ip,
        within_seconds=300,
    )

    # Verify no duplicate found (alert is too old)
    assert duplicate is None


# Test listing alerts with severity filter
@pytest.mark.asyncio
async def test_list_alerts_filters_by_severity(
    repository,
):
    # Save high severity alert
    await repository.save(
        build_alert(
            alert_id="1",
            severity="high",
        )
    )

    # Save low severity alert
    await repository.save(
        build_alert(
            alert_id="2",
            severity="low",
        )
    )

    # List alerts filtered by high severity
    page = await repository.list_alerts(
        filters=AlertFilters(severity="high"),
        cursor=None,
        limit=10,
    )

    # Verify only one alert returned
    assert len(page.items) == 1
    # Verify returned alert has high severity
    assert page.items[0].severity == "high"


# Test pagination of alerts
@pytest.mark.asyncio
async def test_list_alerts_pagination(
    repository,
):
    # Save 5 test alerts
    for i in range(5):
        await repository.save(build_alert(alert_id=str(i)))

    # List alerts with limit of 2
    page = await repository.list_alerts(
        filters=AlertFilters(),
        cursor=None,
        limit=2,
    )

    # Verify only 2 alerts returned
    assert len(page.items) == 2
