from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, IPvAnyAddress, ConfigDict


class SeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCreateRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="The title of the security alert (3 to 120 characters).",
        examples=["Unauthorized SSH Access Attempt"],
    )
    severity: SeverityEnum = Field(
        ...,
        description="The severity level of the alert ('low', 'medium', 'high', or 'critical').",
        examples=[SeverityEnum.HIGH],
    )
    source_ip: IPvAnyAddress = Field(
        ...,
        description="The source IP address (valid IPv4 or IPv6 address) from which the alert originated.",
        examples=["192.168.1.1"],
    )
    description: str = Field(
        ...,
        max_length=2000,
        description="Detailed description of the security alert (maximum 2000 characters).",
        examples=[
            "Multiple failed root login attempts detected on host-01 in less than 10 seconds."
        ],
    )
    tags: Optional[List[str]] = Field(
        default=None,
        max_length=10,
        description="Optional list of tags for categorization (maximum of 10 items).",
        examples=[["brute-force", "auth-failure"]],
    )


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str = Field(
        ...,
        description="Unique identifier of the alert (UUID v4).",
        examples=["f81d4fae-7dec-11d0-a765-00a0c91e6bf6"],
    )
    title: str = Field(
        ...,
        description="The title of the security alert.",
        examples=["Unauthorized SSH Access Attempt"],
    )
    severity: SeverityEnum = Field(
        ...,
        description="The severity level of the alert.",
        examples=[SeverityEnum.HIGH],
    )
    source_ip: str = Field(
        ...,
        description="Standardized string representation of the source IP address.",
        examples=["192.168.1.1"],
    )
    status: str = Field(
        ..., description="Current status of the alert (e.g., 'new').", examples=["new"]
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp indicating when the alert was created (ISO-8601 UTC).",
        examples=["2026-06-05T16:30:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp indicating when the alert was last updated (ISO-8601 UTC).",
        examples=["2026-06-05T17:00:00Z"],
    )
    version: int = Field(
        ...,
        description="Current version of the alert.",
    )


class PaginationInfo(BaseModel):
    next_cursor: Optional[str] = Field(
        None,
        description="Opaque base64-encoded cursor indicating the starting point of the next page, or null if no more pages exist.",
        examples=["ZjgxZDRmYWUtN2RlYy0xMWQwLWE3NjUtMDBhMGM5MWU2YmY2"],
    )
    limit: int = Field(
        ...,
        description="The page size limit used in the request.",
        examples=[10],
    )
    total: int = Field(
        ...,
        description="The total number of alerts matching the filters in the database.",
        examples=[1],
    )


class AlertsListResponse(BaseModel):
    alerts: List[AlertResponse] = Field(
        ..., description="List of security alerts for the current page."
    )
    pagination: PaginationInfo = Field(..., description="Pagination metadata.")


class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="Error details describing the validation or operational conflict.",
        examples=[
            "Duplicate alert: an alert with the same title and source_ip was created within the last 5 minutes."
        ],
    )


# OpenAPI response examples for GET combinations
GET_EXAMPLES = {
    "no_filters": {
        "summary": "No filters applied",
        "description": "Retrieves the most recent alerts with default pagination.",
        "value": {
            "alerts": [
                {
                    "alert_id": "893c52a0-47b2-4d2a-89a1-cb9e8c4596fa",
                    "title": "Unauthorized SSH Access Attempt",
                    "severity": "high",
                    "source_ip": "192.168.1.1",
                    "status": "new",
                    "created_at": "2026-06-05T16:30:00Z",
                    "updated_at": "2026-06-05T17:00:00Z",
                },
                {
                    "alert_id": "d0413bc4-0fb4-4df1-8e01-1b918b9595cd",
                    "title": "SQL Injection Detected",
                    "severity": "critical",
                    "source_ip": "10.0.0.5",
                    "status": "new",
                    "created_at": "2026-06-05T16:28:15Z",
                    "updated_at": "2026-06-05T16:28:15Z",
                },
            ],
            "pagination": {
                "next_cursor": "ZDA0MTNiYzQtMGZiNC00ZGYxLThlMDEtMWI5MThiOTU5NWNk",
                "limit": 10,
                "total": 2,
            },
        },
    },
    "filter_by_severity": {
        "summary": "Filter by severity (critical)",
        "description": "Retrieves only alerts that have critical severity.",
        "value": {
            "alerts": [
                {
                    "alert_id": "d0413bc4-0fb4-4df1-8e01-1b918b9595cd",
                    "title": "SQL Injection Detected",
                    "severity": "critical",
                    "source_ip": "10.0.0.5",
                    "status": "new",
                    "created_at": "2026-06-05T16:28:15Z",
                    "updated_at": "2026-06-05T16:28:15Z",
                }
            ],
            "pagination": {"next_cursor": None, "limit": 10, "total": 1},
        },
    },
    "filter_by_source_ip": {
        "summary": "Filter by source IP",
        "description": "Retrieves only alerts that originated from the IP 192.168.1.1.",
        "value": {
            "alerts": [
                {
                    "alert_id": "893c52a0-47b2-4d2a-89a1-cb9e8c4596fa",
                    "title": "Unauthorized SSH Access Attempt",
                    "severity": "high",
                    "source_ip": "192.168.1.1",
                    "status": "new",
                    "created_at": "2026-06-05T16:30:00Z",
                    "updated_at": "2026-06-05T17:00:00Z",
                }
            ],
            "pagination": {"next_cursor": None, "limit": 10, "total": 1},
        },
    },
    "filter_by_both": {
        "summary": "Filter by severity and source IP",
        "description": "Retrieves only critical severity alerts originating from 10.0.0.5.",
        "value": {
            "alerts": [
                {
                    "alert_id": "d0413bc4-0fb4-4df1-8e01-1b918b9595cd",
                    "title": "SQL Injection Detected",
                    "severity": "critical",
                    "source_ip": "10.0.0.5",
                    "status": "new",
                    "created_at": "2026-06-05T16:28:15Z",
                    "updated_at": "2026-06-05T16:28:15Z",
                }
            ],
            "pagination": {"next_cursor": None, "limit": 10, "total": 1},
        },
    },
    "cursor_pagination": {
        "summary": "Retrieve next page via cursor",
        "description": "Retrieves results after the item pointed to by the cursor.",
        "value": {
            "alerts": [
                {
                    "alert_id": "d0413bc4-0fb4-4df1-8e01-1b918b9595cd",
                    "title": "SQL Injection Detected",
                    "severity": "critical",
                    "source_ip": "10.0.0.5",
                    "status": "new",
                    "created_at": "2026-06-05T16:28:15Z",
                    "updated_at": "2026-06-05T16:28:15Z",
                }
            ],
            "pagination": {"next_cursor": None, "limit": 1, "total": 2},
        },
    },
}
