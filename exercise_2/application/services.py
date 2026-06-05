from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status

from exercise_2.domain.models import Alert
from exercise_2.domain.filters import AlertFilters
from exercise_2.domain.ports import AlertRepository

from exercise_2.infrastructure.api.schemas import (
    AlertCreateRequest,
    SeverityEnum,
)


class AlertService:
    def __init__(
        self,
        repository: AlertRepository,
    ):
        self._repository = repository

    async def create_alert(
        self,
        request: AlertCreateRequest,
    ) -> Alert:

        duplicate = await self._repository.find_recent_duplicate(
            title=request.title,
            source_ip=str(request.source_ip),
            within_seconds=300,
        )

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Duplicate alert: an alert with the same "
                    "title and source_ip was created within "
                    "the last 5 minutes."
                ),
            )

        alert = Alert(
            alert_id=str(uuid4()),
            title=request.title,
            severity=request.severity,
            source_ip=str(request.source_ip),
            description=request.description,
            tags=request.tags or [],
            status="new",
            created_at=datetime.now(timezone.utc),
        )

        return await self._repository.save(alert)

    async def get_alert_by_id(
        self,
        alert_id: str,
    ) -> Alert | None:
        return await self._repository.find_by_id(alert_id)

    async def get_alerts(
        self,
        severity: SeverityEnum | None = None,
        source_ip: str | None = None,
        cursor: str | None = None,
        limit: int = 10,
    ):
        filters = AlertFilters(
            severity=severity,
            source_ip=source_ip,
        )

        return await self._repository.list_alerts(
            filters=filters,
            cursor=cursor,
            limit=limit,
        )
