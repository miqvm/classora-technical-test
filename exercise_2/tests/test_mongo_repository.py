from datetime import datetime, timedelta, timezone

import pytest

from exercise_2.domain.models import Alert
from exercise_2.domain.filters import AlertFilters

from exercise_2.infrastructure.database.repository import (
    MongoAlertRepository,
)


class FakeCollection:
    def __init__(self):
        self.documents = {}

    async def replace_one(
        self,
        filter_,
        document,
        upsert=False,
    ):
        self.documents[filter_["_id"]] = document

    async def find_one(
        self,
        query,
        sort=None,
    ):
        if "_id" in query:
            return self.documents.get(query["_id"])

        matches = []

        for doc in self.documents.values():

            if doc["title"] != query["title"]:
                continue

            if doc["source_ip"] != query["source_ip"]:
                continue

            if doc["created_at"] < query["created_at"]["$gte"]:
                continue

            matches.append(doc)

        if not matches:
            return None

        matches.sort(
            key=lambda x: x["created_at"],
            reverse=True,
        )

        return matches[0]

    def find(self, query):
        docs = list(self.documents.values())

        if "severity" in query:
            docs = [d for d in docs if d["severity"] == query["severity"]]

        if "source_ip" in query:
            docs = [d for d in docs if d["source_ip"] == query["source_ip"]]

        if "created_at" in query:
            docs = [d for d in docs if d["created_at"] < query["created_at"]["$lt"]]

        return FakeCursor(docs)

    async def create_index(self, *args, **kwargs):
        pass


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, field, direction):
        self.docs.sort(
            key=lambda x: x[field],
            reverse=True,
        )
        return self

    def limit(self, value):
        self.docs = self.docs[:value]
        return self

    async def to_list(self, length):
        return self.docs[:length]


@pytest.fixture
def repository():
    return MongoAlertRepository(FakeCollection())


def build_alert(
    alert_id="1",
    severity="high",
):
    return Alert(
        alert_id=alert_id,
        title="SQL Injection",
        severity=severity,
        source_ip="192.168.1.10",
        description="attack",
        tags=[],
        status="new",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_save_and_find_by_id(
    repository,
):
    alert = build_alert()

    await repository.save(alert)

    found = await repository.find_by_id(alert.alert_id)

    assert found is not None
    assert found.alert_id == alert.alert_id
    assert found.title == alert.title


@pytest.mark.asyncio
async def test_find_by_id_returns_none(
    repository,
):
    result = await repository.find_by_id("missing")

    assert result is None


@pytest.mark.asyncio
async def test_find_recent_duplicate_found(
    repository,
):
    alert = build_alert()

    await repository.save(alert)

    duplicate = await repository.find_recent_duplicate(
        title=alert.title,
        source_ip=alert.source_ip,
        within_seconds=300,
    )

    assert duplicate is not None


@pytest.mark.asyncio
async def test_find_recent_duplicate_not_found(
    repository,
):
    old_alert = build_alert()

    old_alert.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)

    await repository.save(old_alert)

    duplicate = await repository.find_recent_duplicate(
        title=old_alert.title,
        source_ip=old_alert.source_ip,
        within_seconds=300,
    )

    assert duplicate is None


@pytest.mark.asyncio
async def test_list_alerts_filters_by_severity(
    repository,
):
    await repository.save(
        build_alert(
            alert_id="1",
            severity="high",
        )
    )

    await repository.save(
        build_alert(
            alert_id="2",
            severity="low",
        )
    )

    page = await repository.list_alerts(
        filters=AlertFilters(severity="high"),
        cursor=None,
        limit=10,
    )

    assert len(page.items) == 1
    assert page.items[0].severity == "high"


@pytest.mark.asyncio
async def test_list_alerts_pagination(
    repository,
):
    for i in range(5):
        await repository.save(build_alert(alert_id=str(i)))

    page = await repository.list_alerts(
        filters=AlertFilters(),
        cursor=None,
        limit=2,
    )

    assert len(page.items) == 2
