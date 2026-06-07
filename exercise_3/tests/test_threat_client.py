import pytest
import httpx

from exercise_3.infrastructure.external.dummy_threat_client import (
    HttpxThreatEnrichmentService,
)
from exercise_3.domain.exceptions import EnrichmentError


# Success
@pytest.mark.asyncio
async def test_enrichment_success_parses_data():
    def mock_handler(request: httpx.Request):
        return httpx.Response(
            200,
            json={
                "reputation_score": 85,
                "categories": ["botnet", "spam"],
                "last_seen": "2026-06-05T12:00:00Z",
                "country": "US",
            },
        )

    transport = httpx.MockTransport(mock_handler)
    service = HttpxThreatEnrichmentService(transport=transport)

    result = await service.get_context("192.168.1.5")

    assert result.reputation_score == 85
    assert result.categories == ["botnet", "spam"]
    assert result.country == "US"


# Retry Logic
@pytest.mark.asyncio
async def test_enrichment_retries_on_5xx_and_succeeds():
    call_count = 0

    def mock_handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        # Fail the first two times, succeed on the third
        if call_count < 3:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "reputation_score": 50,
                "categories": [],
                "last_seen": "2026-06-05T12:00:00Z",
                "country": "ES",
            },
        )

    transport = httpx.MockTransport(mock_handler)
    service = HttpxThreatEnrichmentService(transport=transport)

    result = await service.get_context("192.168.1.5")

    assert call_count == 3
    assert result.reputation_score == 50


# Max Retries Failure
@pytest.mark.asyncio
async def test_enrichment_fails_after_max_retries():
    call_count = 0

    def mock_handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(500)

    transport = httpx.MockTransport(mock_handler)
    service = HttpxThreatEnrichmentService(transport=transport)

    with pytest.raises(EnrichmentError) as exc_info:
        await service.get_context("192.168.1.5")

    assert call_count == 3
    assert "HTTP 500" in str(exc_info.value)


# Timeout
@pytest.mark.asyncio
async def test_enrichment_raises_error_on_timeout():
    def mock_handler(request: httpx.Request):
        raise httpx.ReadTimeout("Request timed out.")

    transport = httpx.MockTransport(mock_handler)
    service = HttpxThreatEnrichmentService(transport=transport)

    with pytest.raises(EnrichmentError) as exc_info:
        await service.get_context("192.168.1.5")

    # Assert the domain error wraps the underlying timeout gracefully
    assert "timed out" in str(exc_info.value).lower()
