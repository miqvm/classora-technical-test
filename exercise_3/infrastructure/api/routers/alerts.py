from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from pydantic import IPvAnyAddress

from exercise_3.infrastructure.api.schemas import (
    AlertCreateRequest,
    AlertResponse,
    AlertsListResponse,
    PaginationInfo,
    SeverityEnum,
    ErrorResponse,
    GET_EXAMPLES,
)

from exercise_3.application.services import AlertService
from exercise_3.dependencies import get_alert_service

router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["Alerts"],
)


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a security alert",
    description=(
        "Registers a security alert event. "
        "If the same title and IP occurred in the last 5 minutes, it is rejected as a duplicate. "
        "If it occurred older than 5 minutes ago, it applies an update to the status using optimistic locking."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "model": AlertResponse,
            "description": "Alert successfully created.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Duplicate alert detected.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Validation error.",
        },
    },
)
async def create_alert(
    request: AlertCreateRequest,
    service: AlertService = Depends(get_alert_service),
):
    alert, enrichment = await service.create_alert(request)

    response_data = {
        "alert_id": alert.alert_id,
        "title": alert.title,
        "severity": alert.severity,
        "source_ip": alert.source_ip,
        "status": alert.status,
        "created_at": alert.created_at,
        "updated_at": alert.updated_at,
        "version": alert.version,
    }

    # If the enrichment call was successful, attach it to the response
    if enrichment:
        last_seen_str = (
            enrichment.last_seen.isoformat()
            if hasattr(enrichment.last_seen, "isoformat")
            else str(enrichment.last_seen)
        )

        response_data["enrichment"] = {
            "reputation_score": enrichment.reputation_score,
            "categories": enrichment.categories,
            "last_seen": last_seen_str,
            "country": enrichment.country,
        }

    return AlertResponse(**response_data)


@router.get(
    "",
    response_model=AlertsListResponse,
    summary="List security alerts",
    description=("Retrieve alerts with filtering " "and cursor-based pagination."),
    responses={
        status.HTTP_200_OK: {
            "model": AlertsListResponse,
            "description": "Alerts retrieved successfully.",
            "content": {"application/json": {"examples": GET_EXAMPLES}},
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Validation error."},
    },
)
async def get_alerts(
    severity: Optional[SeverityEnum] = Query(
        None,
        description="Filter by severity.",
    ),
    source_ip: Optional[IPvAnyAddress] = Query(
        None,
        description="Filter by source IP.",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Page size.",
    ),
    cursor: Optional[str] = Query(
        None,
        description="Pagination cursor.",
    ),
    service: AlertService = Depends(get_alert_service),
):
    page = await service.get_alerts(
        severity=severity,
        source_ip=str(source_ip) if source_ip else None,
        cursor=cursor,
        limit=limit,
    )

    return AlertsListResponse(
        alerts=[
            AlertResponse(
                alert_id=alert.alert_id,
                title=alert.title,
                severity=alert.severity,
                source_ip=alert.source_ip,
                status=alert.status,
                created_at=alert.created_at,
                updated_at=alert.updated_at,
                version=alert.version,
            )
            for alert in page.items
        ],
        pagination=PaginationInfo(
            next_cursor=page.next_cursor,
            limit=limit,
            total=len(page.items),
        ),
    )
