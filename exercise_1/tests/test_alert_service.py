from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from exercise_1.services import AlertDatabase
from exercise_1.schemas import (
    AlertCreateRequest,
    SeverityEnum,
)


# Pytest fixture providing an in-memory database instance
@pytest.fixture
def database():
    # Create and return a fresh AlertDatabase instance for each test
    return AlertDatabase()


# Pytest fixture providing a default alert request payload
@pytest.fixture
def alert_request():
    return AlertCreateRequest(
        title="SQL Injection",
        severity=SeverityEnum.HIGH,
        source_ip="192.168.1.10",
        description="Attack detected",
        tags=["security"],
    )


# Helper function to build test AlertCreateRequest objects
def build_alert_request(
    title="SQL Injection",
    severity=SeverityEnum.HIGH,
    source_ip="192.168.1.10",
):
    # Create and return an AlertCreateRequest instance with test data
    return AlertCreateRequest(
        title=title,
        severity=severity,
        source_ip=source_ip,
        description="attack",
        tags=[],
    )


# Test saving an alert successfully
@pytest.mark.asyncio
async def test_add_alert_success(
    database,
    alert_request,
):
    # Call the database method to create an alert
    alert = await database.add_alert(alert_request)

    # Verify alert was created successfully
    assert alert is not None
    # Verify alert ID was automatically generated
    assert alert.alert_id is not None
    # Verify alert title matches
    assert alert.title == alert_request.title

    # Verify that the alert was persisted to the internal list
    assert len(database._alerts) == 1


# Test creating a duplicate alert raises an HTTP 409 Conflict
@pytest.mark.asyncio
async def test_add_alert_duplicate_raises_409(
    database,
    alert_request,
):
    # Save the initial alert to the database
    await database.add_alert(alert_request)

    # Attempt to create an alert and verify it raises HTTPException with 409 status
    with pytest.raises(HTTPException) as exc:
        await database.add_alert(alert_request)

    # Assert the status code is 409 Conflict for duplicate alert
    assert exc.value.status_code == 409


# Test that old alerts are not considered duplicates
@pytest.mark.asyncio
async def test_add_alert_past_5_minutes_is_allowed(
    database,
    alert_request,
):
    # Save the initial alert to the database
    first_alert = await database.add_alert(alert_request)

    # Set creation time to 10 minutes ago
    first_alert.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)

    # Search for recent duplicate within 300 seconds (5 minutes) by trying to add again
    second_alert = await database.add_alert(alert_request)

    # Verify no duplicate conflict was raised and both exist
    assert second_alert is not None
    assert len(database._alerts) == 2


# Test listing alerts with severity filter
@pytest.mark.asyncio
async def test_get_alerts_filters_by_severity(
    database,
):
    # Save high severity alert
    await database.add_alert(
        build_alert_request(
            title="High Alert",
            severity=SeverityEnum.HIGH,
        )
    )

    # Save low severity alert
    await database.add_alert(
        build_alert_request(
            title="Low Alert",
            severity=SeverityEnum.LOW,
        )
    )

    # List alerts filtered by high severity
    alerts, next_cursor, total = await database.get_alerts(
        severity=SeverityEnum.HIGH,
        source_ip=None,
        limit=10,
        cursor=None,
    )

    # Verify only one alert returned
    assert len(alerts) == 1
    # Verify returned alert has high severity
    assert alerts[0].severity == SeverityEnum.HIGH


# Test pagination of alerts
@pytest.mark.asyncio
async def test_get_alerts_pagination(
    database,
):
    # Save 5 test alerts
    for i in range(5):
        await database.add_alert(
            build_alert_request(
                title=f"Alert {i}",
            )
        )

    # List alerts with limit of 2
    alerts, next_cursor, total = await database.get_alerts(
        severity=None,
        source_ip=None,
        limit=2,
        cursor=None,
    )

    # Verify only 2 alerts returned on this page
    assert len(alerts) == 2
    # Verify total matches the total documents in memory
    assert total == 5
    # Verify cursor is returned for further pagination
    assert next_cursor is not None
