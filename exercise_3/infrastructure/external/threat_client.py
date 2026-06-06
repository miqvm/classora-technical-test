import httpx

from exercise_3.domain.models import EnrichmentData
from exercise_3.domain.exceptions import EnrichmentError
from exercise_3.domain.ports import ThreatEnrichmentService


class HttpxThreatEnrichmentService(ThreatEnrichmentService):
    def __init__(
        self,
        base_url: str = "https://threat-intel.example.com",
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._base_url = base_url
        self._timeout = httpx.Timeout(3.0)
        self._transport = transport

    async def get_context(self, source_ip: str) -> EnrichmentData:
        url = f"{self._base_url}/v1/enrich"
        params = {"ip": source_ip}

        max_attempts = 3  # 1 initial request + 2 retries

        async with httpx.AsyncClient(
            timeout=self._timeout, transport=self._transport
        ) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()

                    data = response.json()

                    # Map the raw JSON dictionary to our pure Domain Model
                    return EnrichmentData(
                        reputation_score=data["reputation_score"],
                        categories=data.get("categories", []),
                        last_seen=data["last_seen"],
                        country=data["country"],
                    )

                except httpx.HTTPStatusError as e:
                    # Retry x2 on 5xx Server Errors
                    if e.response.status_code >= 500 and attempt < max_attempts:
                        continue

                    # If it's a 4xx error (or we ran out of retries for 5xx), raise our domain exception
                    raise EnrichmentError(
                        f"Enrichment failed with HTTP {e.response.status_code} for IP {source_ip}"
                    ) from e

                except httpx.RequestError as e:
                    # Covers timeouts, DNS resolution failures, connection drops, etc.
                    raise EnrichmentError(
                        f"Enrichment request failed for IP {source_ip}: {str(e)}"
                    ) from e
