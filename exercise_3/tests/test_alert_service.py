from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from exercise_3.application.services import AlertService
from exercise_3.domain.models import Alert
from exercise_3.infrastructure.api.schemas import (
    AlertCreateRequest,
    SeverityEnum,
)


@pytest.fixture
def repository():
    return AsyncMock()


@pytest.fixture
def audit_repository():
    return AsyncMock()


@pytest.fixture
def enrichment_service():
    return AsyncMock()


@pytest.fixture
def service(repository, audit_repository, enrichment_service):
    return AlertService(
        repository=repository,
        audit_repository=audit_repository,
        enrichment_service=enrichment_service,
    )


@pytest.fixture
def alert_request():
    return AlertCreateRequest(
        title="SQL Injection",
        severity=SeverityEnum.HIGH,
        source_ip="192.168.1.10",
        description="Attack detected",
        tags=["security"],
    )


@pytest.mark.asyncio
async def test_create_alert_success(
    service,
    repository,
    alert_request,
):
    # Mock repository to return no duplicate alerts
    repository.find_recent_duplicate.return_value = None

    # Create an alert object that will be returned by repository.save()
    saved_alert = Alert(
        alert_id="123",
        title=alert_request.title,
        severity=alert_request.severity,
        source_ip=str(alert_request.source_ip),
        description=alert_request.description,
        tags=alert_request.tags,
        status="new",
        created_at=datetime.now(timezone.utc),
    )

    # Mock repository.save() to return the created alert
    repository.save.return_value = saved_alert

    # Call the service method to create an alert
    result = await service.create_alert(alert_request)

    # Assert the alert was created successfully with correct ID
    assert result.alert_id == "123"

    # Verify that duplicate check and save operations were called exactly once
    repository.find_recent_duplicate.assert_called_once()
    repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_alert_duplicate_raises_409(
    service,
    repository,
    alert_request,
):
    # Mock repository to return an existing duplicate alert
    repository.find_recent_duplicate.return_value = Alert(
        alert_id="existing",
        title=alert_request.title,
        severity=alert_request.severity,
        source_ip=str(alert_request.source_ip),
        description="duplicate",
        tags=[],
        status="new",
        created_at=datetime.now(timezone.utc),
    )

    # Attempt to create an alert and verify it raises HTTPException with 409 status
    with pytest.raises(HTTPException) as exc:
        await service.create_alert(alert_request)

    # Assert the status code is 409 Conflict for duplicate alert
    assert exc.value.status_code == 409

    # Verify that save was never called since duplicate was detected
    repository.save.assert_not_called()
