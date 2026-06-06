from typing import Protocol

from exercise_3.domain.models import Alert, Page, AuditLogEntry, EnrichmentData
from exercise_3.domain.filters import AlertFilters


class AlertRepository(Protocol):
    """Repository protocol for managing Alert persistence."""
    async def save(self, alert: Alert) -> Alert: ...

    async def find_by_id(self, alert_id: str) -> Alert | None: ...

    async def find_recent_duplicate(
        self,
        title: str,
        source_ip: str,
        within_seconds: int,
    ) -> Alert | None: ...

    async def list_alerts(
        self,
        filters: AlertFilters,
        cursor: str | None,
        limit: int,
    ) -> Page[Alert]: ...

    async def find_latest_by_title_and_ip(
        self, title: str, source_ip: str
    ) -> Alert | None: ...

    async def update_status(
        self,
        alert_id: str,
        new_status: str,
        expected_version: int,
    ) -> Alert: ...


class AuditLogRepository(Protocol):
    """Repository protocol for managing AuditLogEntry persistence."""
    async def insert(self, entry: AuditLogEntry) -> None: ...


class ThreatEnrichmentService(Protocol):
    """Protocol for an external threat enrichment service."""
    async def get_context(self, source_ip: str) -> EnrichmentData: ...
