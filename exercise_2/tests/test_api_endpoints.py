import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from httpx import ASGITransport, AsyncClient

# --- FIX: Mock environment variables BEFORE importing the app ---
# This prevents Pydantic's Settings() from throwing a ValidationError during pytest collection
os.environ["MONGO_HOST"] = "localhost"
os.environ["MONGO_USER"] = "test_user"
os.environ["MONGO_PASSWORD"] = "test_pass"
os.environ["MONGO_DATABASE"] = "test_db"

from exercise_2.domain.models import Alert, Page
from exercise_2.infrastructure.api.schemas import SeverityEnum
from exercise_2.main import app
from exercise_2.dependencies import get_alert_service


# Pytest fixture to provide a mocked AlertService
@pytest_asyncio.fixture
def mock_service():
    return AsyncMock()


# Pytest fixture to override the FastAPI dependency before each test
@pytest_asyncio.fixture(autouse=True)
def override_dependency(mock_service):
    # Override the get_alert_service dependency to return our mock
    app.dependency_overrides[get_alert_service] = lambda: mock_service
    yield
    # Clean up overrides after the test
    app.dependency_overrides.clear()


# Test the creation endpoint returns a successful response
@pytest.mark.asyncio
async def test_create_alert_endpoint_success(mock_service):
    # 1. Setup the mock service to return a dummy Alert
    mock_service.create_alert.return_value = Alert(
        alert_id="123e4567-e89b-12d3-a456-426614174000",
        title="Port Scan Detected",
        severity=SeverityEnum.MEDIUM,
        source_ip="192.168.1.50",
        description="Frequent SYN packets.",
        status="new",
        created_at=datetime.now(timezone.utc),
        tags=["recon"],
    )

    payload = {
        "title": "Port Scan Detected",
        "severity": "medium",
        "source_ip": "192.168.1.50",
        "description": "Frequent SYN packets.",
        "tags": ["recon"],
    }

    # 2. Execute the request
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/alerts", json=payload)

    # 3. Assertions
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["alert_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert data["title"] == payload["title"]

    # Verify the service was actually called by the router
    mock_service.create_alert.assert_called_once()


# Test endpoint correctly maps service exceptions (like 409 Conflict)
@pytest.mark.asyncio
async def test_create_alert_endpoint_duplicate_409(mock_service):
    # 1. Setup the mock to raise the duplicate HTTPException
    mock_service.create_alert.side_effect = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Duplicate alert",
    )

    payload = {
        "title": "Port Scan Detected",
        "severity": "medium",
        "source_ip": "192.168.1.50",
        "description": "Frequent SYN packets.",
    }

    # 2. Execute the request
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/alerts", json=payload)

    # 3. Assertions
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Duplicate alert" in response.json()["detail"]


# Test validation framework catches bad requests before reaching the service
@pytest.mark.asyncio
async def test_create_alert_endpoint_validation_error_raises_422(mock_service):
    # Invalid payload: short title, bad ip, bad enum
    payload = {
        "title": "A",
        "severity": "invalid",
        "source_ip": "not-an-ip",
        "description": "Too short title and invalid IP",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/alerts", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Ensure Pydantic caught the errors, meaning the service shouldn't even be called
    errors = response.json()["detail"]
    assert len(errors) == 3
    mock_service.create_alert.assert_not_called()


# Test GET endpoint maps service pagination correctly
@pytest.mark.asyncio
async def test_get_alerts_endpoint(mock_service):
    # 1. Setup the mock to return a Page object
    mock_service.get_alerts.return_value = Page(
        items=[
            Alert(
                alert_id="1",
                title="Malware Download",
                severity=SeverityEnum.CRITICAL,
                source_ip="10.0.0.99",
                description="File hash matched ransomware.",
                status="new",
                created_at=datetime.now(timezone.utc),
                tags=[],
            )
        ],
        next_cursor=None,
    )

    # 2. Execute the request
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/alerts?limit=10")

    # 3. Assertions
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "alerts" in data
    assert "pagination" in data
    assert len(data["alerts"]) == 1
    assert data["pagination"]["limit"] == 10

    # Verify the query parameters were correctly passed to the service layer
    mock_service.get_alerts.assert_called_once()
