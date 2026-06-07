import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status

from exercise_3.domain.exceptions import EnrichmentError
from exercise_3.domain.models import Alert, AuditLogEntry, EnrichmentData
from exercise_3.domain.filters import AlertFilters
from exercise_3.domain.ports import (
    AlertRepository,
    AuditLogRepository,
    ThreatEnrichmentService,
)
from exercise_3.infrastructure.api.schemas import (
    AlertCreateRequest,
    SeverityEnum,
)


class AlertService:
    def __init__(
        self,
        repository: AlertRepository,
        audit_repository: AuditLogRepository,
        enrichment_service: ThreatEnrichmentService,
    ):
        self._repository = repository
        self._audit_repository = audit_repository
        self._enrichment_service = enrichment_service

    async def create_alert(
        self,
        request: AlertCreateRequest,
    ) -> tuple[Alert, EnrichmentData | None]:
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

        # Helper function to safely call enrichment service without failing the entire request
        async def safe_enrichment():
            try:
                return await self._enrichment_service.get_context(
                    str(request.source_ip)
                )
            except EnrichmentError:
                return None

        existing_alert = await self._repository.find_latest_by_title_and_ip(
            title=request.title,
            source_ip=str(request.source_ip),
        )
        if existing_alert:
            updated_alert, enrichment_data = await asyncio.gather(
                self.change_alert_status(
                    alert=existing_alert,
                    new_status="updated",
                    changed_by="system",
                    reason="Duplicate alert detected, updating existing alert.",
                ),
                safe_enrichment(),
            )
            return updated_alert, enrichment_data

        alert = Alert(
            alert_id=str(uuid4()),
            title=request.title,
            severity=request.severity,
            source_ip=str(request.source_ip),
            description=request.description,
            tags=request.tags or [],
            status="new",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        saved_alert, enrichment_data = await asyncio.gather(
            self._repository.save(alert), safe_enrichment()
        )
        return saved_alert, enrichment_data

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

    async def change_alert_status(
        self,
        alert: Alert,
        new_status: str,
        changed_by: str,
        reason: str | None = None,
    ) -> Alert:
        """
        Updates the status of an alert and records an immutable audit log entry.
        """
        # Update status and save
        saved_alert = await self._repository.update_status(
            alert_id=alert.alert_id,
            new_status=new_status,
            expected_version=alert.version,
        )

        # Record immutable audit entry
        audit_entry = AuditLogEntry(
            id=uuid4(),
            alert_id=alert.alert_id,
            from_status=alert.status,
            to_status=new_status,
            changed_by=changed_by,
            changed_at=datetime.now(timezone.utc),
            reason=reason,
        )

        await self._audit_repository.insert(audit_entry)
        return saved_alert

    async def enrich_alert(self, alert_id: str) -> EnrichmentData:
        """
        Retrieves threat context for the given alert's source IP.
        """
        alert = await self._repository.find_by_id(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found.",
            )

        return await self._enrichment_service.get_context(alert.source_ip)
