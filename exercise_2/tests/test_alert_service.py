import pytest

from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi import HTTPException

from exercise_2.application.services import AlertService
from exercise_2.domain.models import Alert

from exercise_2.infrastructure.api.schemas import (
    AlertCreateRequest,
    SeverityEnum,
)


@pytest.fixture
def repository():
    return AsyncMock()


@pytest.fixture
def service(repository):
    return AlertService(repository)


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
    repository.find_recent_duplicate.return_value = None

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

    repository.save.return_value = saved_alert

    result = await service.create_alert(alert_request)

    assert result.alert_id == "123"

    repository.find_recent_duplicate.assert_called_once()
    repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_alert_duplicate_raises_409(
    service,
    repository,
    alert_request,
):
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

    with pytest.raises(HTTPException) as exc:
        await service.create_alert(alert_request)

    assert exc.value.status_code == 409

    repository.save.assert_not_called()
