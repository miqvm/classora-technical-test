import base64
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import asyncio

from fastapi import HTTPException, status

from pydantic import IPvAnyAddress

from exercise_1.schemas import (
    AlertCreateRequest,
    SeverityEnum,
)


class StoredAlert:
    """
    Internal representation of an alert stored in the in-memory database.
    Contains both the original string IP and the parsed ipaddress object for efficient matching.
    """

    def __init__(
        self,
        alert_id: str,
        title: str,
        severity: SeverityEnum,
        source_ip: str,  # Standardized string representation of the IP
        parsed_ip: object,  # ipaddress.IPv4Address or ipaddress.IPv6Address
        description: str,
        tags: List[str],
        status: str,
        created_at: datetime,
    ):
        self.alert_id = alert_id
        self.title = title
        self.severity = severity
        self.source_ip = source_ip
        self.parsed_ip = parsed_ip
        self.description = description
        self.tags = tags
        self.status = status
        self.created_at = created_at


class AlertDatabase:
    """
    Thread-safe in-memory database for storing alerts. Implements duplicate detection logic
    and supports filtering and cursor-based pagination.
    """

    def __init__(self):
        self._alerts: List[StoredAlert] = []
        self._lock = asyncio.Lock()

    async def add_alert(self, request: AlertCreateRequest) -> StoredAlert:
        """
        Add a new alert thread-safely after verifying duplicate rules.
        A duplicate is defined as having the same title and parsed source_ip
        within the last 5 minutes.
        """
        async with self._lock:
            now = datetime.now(timezone.utc)

            # Check for duplicates in-memory (optimized reverse scan)
            for alert in reversed(self._alerts):
                time_diff = now - alert.created_at
                if time_diff >= timedelta(minutes=5):
                    # Chronologically, all previous items are older than 5 minutes.
                    break

                if (
                    alert.title == request.title
                    and alert.parsed_ip == request.source_ip
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Duplicate alert: an alert with the same title and source_ip was created within the last 5 minutes.",
                    )

            # Create the alert record
            alert_id = str(uuid.uuid4())
            new_alert = StoredAlert(
                alert_id=alert_id,
                title=request.title,
                severity=request.severity,
                source_ip=str(request.source_ip),
                parsed_ip=request.source_ip,
                description=request.description,
                tags=request.tags or [],
                status="new",
                created_at=now,
            )
            self._alerts.append(new_alert)
            return new_alert

    async def get_alerts(
        self,
        severity: Optional[SeverityEnum] = None,
        source_ip: Optional[IPvAnyAddress] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> tuple[List[StoredAlert], Optional[str], int]:
        """
        Retrieve a filtered, paginated page of alerts (newest first).
        """
        # Filter database alerts
        filtered = []
        for alert in self._alerts:
            # Filter by severity
            if severity and alert.severity != severity:
                continue
            # Filter by source IP (canonical check)
            if source_ip and alert.parsed_ip != source_ip:
                continue
            filtered.append(alert)

        # Sort by creation time descending (newest first)
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        total = len(filtered)

        # Locate page start index from cursor (base64 encoded uuid)
        start_idx = 0
        if cursor:
            try:
                decoded_id = base64.b64decode(cursor.encode()).decode()
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination cursor format. Must be a valid base64-encoded string.",
                )

            # Find the index of the alert with alert_id == decoded_id
            cursor_found = False
            for idx, alert in enumerate(filtered):
                if alert.alert_id == decoded_id:
                    start_idx = idx + 1
                    cursor_found = True
                    break

            if not cursor_found:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination cursor: referenced alert ID not found in results.",
                )

        # Slice the page
        page_alerts = filtered[start_idx : start_idx + limit]

        # Generate next_cursor if there are more alerts remaining
        next_cursor = None
        if start_idx + limit < total and page_alerts:
            last_alert_id = page_alerts[-1].alert_id
            next_cursor = base64.b64encode(last_alert_id.encode()).decode()

        return page_alerts, next_cursor, total

    async def clear_all(self):
        """Helper method to reset DB state in tests."""
        async with self._lock:
            self._alerts.clear()
