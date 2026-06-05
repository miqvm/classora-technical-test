from typing import Optional

from fastapi import APIRouter, status, Query
from pydantic import IPvAnyAddress

from exercise_1.schemas import (
    AlertCreateRequest,
    AlertResponse,
    AlertsListResponse,
    PaginationInfo,
    SeverityEnum,
    ErrorResponse,
    GET_EXAMPLES,
)
from exercise_1.services import AlertDatabase

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


# Global database instance
alert_db = AlertDatabase()


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a security alert",
    description=(
        "Registers a security alert event. Validates that the payload is well-formed "
        "and checks for duplicates. If an alert with the same 'title' and 'source_ip' "
        "has been created within the last 5 minutes, returns 409 Conflict."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "model": AlertResponse,
            "description": "Alert successfully created.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Duplicate alert detected within the last 5 minutes.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Validation error of request fields."
        },
    },
)
async def create_alert(request: AlertCreateRequest):
    return await alert_db.add_alert(request)


@router.get(
    "",
    response_model=AlertsListResponse,
    summary="List security alerts with filtering and cursor pagination",
    description=(
        "Retrieves a list of security alerts sorted by creation time (newest first). "
        "Allows filtering by severity level and source IP, and implements "
        "cursor-based pagination for performant retrieval."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": AlertsListResponse,
            "description": "Successfully retrieved paginated alerts.",
            "content": {"application/json": {"examples": GET_EXAMPLES}},
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Validation error of query parameters."
        },
    },
)
async def get_alerts(
    severity: Optional[SeverityEnum] = Query(
        None,
        description="Filter alerts by severity level ('low', 'medium', 'high', 'critical').",
    ),
    source_ip: Optional[IPvAnyAddress] = Query(
        None,
        description="Filter alerts by source IP. Formats are canonicalized during matching.",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of alerts to return on a page (1 to 100).",
    ),
    cursor: Optional[str] = Query(
        None,
        description="Opaque base64-encoded cursor pointing to the next page of results.",
    ),
):
    alerts, next_cursor, total = await alert_db.get_alerts(
        severity=severity, source_ip=source_ip, limit=limit, cursor=cursor
    )
    formatted_alerts = [
        AlertResponse(
            alert_id=a.alert_id,
            title=a.title,
            severity=a.severity,
            source_ip=a.source_ip,
            status=a.status,
            created_at=a.created_at,
        )
        for a in alerts
    ]
    return AlertsListResponse(
        alerts=formatted_alerts,
        pagination=PaginationInfo(next_cursor=next_cursor, limit=limit, total=total),
    )
