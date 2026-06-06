import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar

from exercise_3.infrastructure.api.schemas import SeverityEnum


@dataclass(slots=True)
class Alert:
    alert_id: str
    title: str
    severity: SeverityEnum
    source_ip: str
    description: str
    status: str
    created_at: datetime
    tags: list[str] = field(default_factory=list)
    version: int = 1


T = TypeVar("T")


@dataclass(slots=True)
class Page(Generic[T]):
    items: list[T]
    next_cursor: str | None


@dataclass(slots=True, frozen=True)
class AuditLogEntry:
    """
    Domain model representing an immutable audit log entry
    for status changes in an alert.
    """

    id: uuid.UUID
    alert_id: str
    from_status: str
    to_status: str
    changed_by: str
    changed_at: datetime
    reason: str | None = None


@dataclass(slots=True)
class EnrichmentData:
    """
    Domain model representing the threat context fetched
    from the external enrichment service.
    """

    reputation_score: int
    last_seen: datetime | str  # Usually an ISO-8601 string or datetime object
    country: str
    categories: list[str] = field(default_factory=list)
