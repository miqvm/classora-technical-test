from typing import Protocol

from exercise_2.domain.models import Alert, Page
from exercise_2.domain.filters import AlertFilters


class AlertRepository(Protocol):
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
