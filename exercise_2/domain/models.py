from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar

from exercise_2.infrastructure.api.schemas import SeverityEnum


@dataclass(slots=True)
class Alert:
    alert_id: str
    title: str
    severity: SeverityEnum
    source_ip: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    tags: list[str] = field(default_factory=list)
    version: int = 1


T = TypeVar("T")


@dataclass(slots=True)
class Page(Generic[T]):
    items: list[T]
    next_cursor: str | None
