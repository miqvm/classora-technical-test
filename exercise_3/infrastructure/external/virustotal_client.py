import httpx
from datetime import datetime, timezone

from exercise_3.domain.models import EnrichmentData
from exercise_3.domain.exceptions import EnrichmentError
from exercise_3.domain.ports import ThreatEnrichmentService


class VirusTotalEnrichmentService(ThreatEnrichmentService):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://www.virustotal.com/api/v3",
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = httpx.Timeout(3.0)
        self._transport = transport

    async def get_context(self, source_ip: str) -> EnrichmentData:
        # Endpoint expects exactly this format
        url = f"{self._base_url}/ip_addresses/{source_ip}"

        headers = {"x-apikey": self._api_key, "accept": "application/json"}

        max_attempts = 3

        async with httpx.AsyncClient(
            timeout=self._timeout, transport=self._transport
        ) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()

                    # Drill down into the "data" -> "attributes" object from your JSON
                    attributes = response.json().get("data", {}).get("attributes", {})

                    # 1. Reputation Score
                    # We use the "malicious" detections out of "last_analysis_stats"
                    stats = attributes.get("last_analysis_stats", {})
                    malicious_votes = stats.get("malicious", 0)

                    # Convert raw votes into a 0-100 score (e.g. 5 malicious vendors = 50 score)
                    reputation_score = min(malicious_votes * 10, 100)

                    # 2. Last Seen Date
                    # Fallback to last_modification_date if last_analysis_date is missing (as seen in your payload)
                    date_unix = attributes.get("last_analysis_date") or attributes.get(
                        "last_modification_date"
                    )
                    if date_unix:
                        last_seen = datetime.fromtimestamp(
                            date_unix, tz=timezone.utc
                        ).isoformat()
                    else:
                        last_seen = "Unknown"

                    # 3. Map to our application's Domain Model
                    return EnrichmentData(
                        reputation_score=reputation_score,
                        categories=attributes.get("tags", []),
                        last_seen=last_seen,
                        country=attributes.get("country", "Unknown"),
                    )

                except httpx.HTTPStatusError as e:
                    # Retry x2 on 5xx Server Errors (VirusTotal occasionally throws 503s under load)
                    if e.response.status_code >= 500 and attempt < max_attempts:
                        continue

                    # If VirusTotal returns 404, the IP has never been seen by them
                    if e.response.status_code == 404:
                        return EnrichmentData(
                            reputation_score=0,
                            categories=[],
                            last_seen="Never",
                            country="Unknown",
                        )

                    raise EnrichmentError(
                        f"VirusTotal enrichment failed with HTTP {e.response.status_code} for IP {source_ip}"
                    ) from e

                except httpx.RequestError as e:
                    raise EnrichmentError(
                        f"VirusTotal request failed for IP {source_ip}: {str(e)}"
                    ) from e
