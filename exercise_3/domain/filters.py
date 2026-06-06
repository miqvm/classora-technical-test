from dataclasses import dataclass

from exercise_3.infrastructure.api.schemas import SeverityEnum


@dataclass(slots=True)
class AlertFilters:
    severity: SeverityEnum | None = None
    source_ip: str | None = None
