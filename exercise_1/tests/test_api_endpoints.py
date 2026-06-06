import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from exercise_1.main import app
from exercise_1.routers.alerts import alert_db


# Use pytest_asyncio.fixture for async fixtures to prevent the PytestRemovedIn9Warning
@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    # Clear all documents before each test runs
    await alert_db.clear_all()
    # It's good practice to yield in async fixtures to ensure proper cleanup if needed later
    yield


# Test the creation endpoint returns a successful response
@pytest.mark.asyncio
async def test_create_alert_endpoint_success():
    # Define payload matching the request schema
    payload = {
        "title": "Port Scan Detected",
        "severity": "medium",
        "source_ip": "192.168.1.50",
        "description": "Frequent SYN packets sent to multiple ports.",
        "tags": ["reconnaissance"],
    }

    # Create an async test client connected to the FastAPI app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        # Execute the POST request
        response = await client.post(
            "/api/v1/alerts",
            json=payload,
        )

    # Verify response status is 201 Created
    assert response.status_code == 201

    # Verify response body schema mapped correctly
    data = response.json()
    assert "alert_id" in data
    assert data["title"] == payload["title"]
    assert data["status"] == "new"


# Test validation framework correctly catches bad requests
@pytest.mark.asyncio
async def test_create_alert_endpoint_validation_error_raises_422():
    # Define an invalid payload (short title, bad ip, bad enum)
    payload = {
        "title": "A",
        "severity": "invalid_severity",
        "source_ip": "not-an-ip",
        "description": "Too short title and invalid IP",
    }

    # Create an async test client connected to the FastAPI app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        # Execute the POST request
        response = await client.post(
            "/api/v1/alerts",
            json=payload,
        )

    # Verify status code is 422 Unprocessable Entity
    assert response.status_code == 422

    # Ensure Pydantic caught all 3 field errors
    errors = response.json()["detail"]
    assert len(errors) == 3
