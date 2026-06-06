from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from exercise_3.application.services import AlertService
from exercise_3.domain.models import Alert, EnrichmentData
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
    enrichment_service,
    alert_request,
):
    # Mock repository
    repository.find_recent_duplicate.return_value = None
    repository.find_latest_by_title_and_ip.return_value = None

    saved_alert = Alert(
        alert_id="123",
        title=alert_request.title,
        severity=alert_request.severity,
        source_ip=str(alert_request.source_ip),
        description=alert_request.description,
        tags=alert_request.tags,
        status="new",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repository.save.return_value = saved_alert

    # Mock enrichment service
    mock_enrichment = EnrichmentData(
        reputation_score=95,
        categories=["botnet"],
        last_seen="2026-06-05T12:00:00Z",
        country="RU",
    )
    enrichment_service.get_context.return_value = mock_enrichment

    # Call the service method (Unpacking the tuple)
    result_alert, result_enrichment = await service.create_alert(alert_request)

    # Assert the alert was created successfully
    assert result_alert.alert_id == "123"

    # Assert enrichment data is returned correctly
    assert result_enrichment is not None
    assert result_enrichment.reputation_score == 95
    assert result_enrichment.country == "RU"

    # Verify both methods were called in parallel via gather
    repository.save.assert_called_once()
    enrichment_service.get_context.assert_called_once_with("192.168.1.10")


@pytest.mark.asyncio
async def test_create_alert_duplicate_raises_409(
    service,
    repository,
    enrichment_service,
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
        updated_at=datetime.now(timezone.utc),
    )

    # Attempt to create an alert and verify it raises HTTPException
    with pytest.raises(HTTPException) as exc:
        await service.create_alert(alert_request)

    assert exc.value.status_code == 409

    # Verify neither save nor enrichment was called because validation failed first
    repository.save.assert_not_called()
    enrichment_service.get_context.assert_not_called()
