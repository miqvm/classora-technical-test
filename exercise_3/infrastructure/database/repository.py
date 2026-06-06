from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from exercise_3.domain.models import Alert, Page
from exercise_3.domain.filters import AlertFilters
from exercise_3.domain.ports import AlertRepository


class MongoAlertRepository(AlertRepository):
    def __init__(self, collection: AsyncIOMotorCollection):
        self._collection = collection

    async def create_indexes(self) -> None:
        """
        Call once during application startup.
        """
        await self._collection.create_index("source_ip")
        await self._collection.create_index("severity")
        await self._collection.create_index("created_at")

        # Helpful for duplicate detection
        await self._collection.create_index(
            [
                ("title", 1),
                ("source_ip", 1),
                ("created_at", -1),
            ]
        )

    async def save(self, alert: Alert) -> Alert:
        document = self._to_document(alert)

        await self._collection.replace_one(
            {"_id": alert.alert_id},
            document,
            upsert=True,
        )

        return alert

    async def find_by_id(self, alert_id: str) -> Alert | None:
        document = await self._collection.find_one({"_id": alert_id})

        if document is None:
            return None

        return self._to_domain(document)

    async def find_recent_duplicate(
        self,
        title: str,
        source_ip: str,
        within_seconds: int,
    ) -> Alert | None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)

        document = await self._collection.find_one(
            {
                "title": title,
                "source_ip": source_ip,
                "created_at": {"$gte": cutoff},
            },
            sort=[("created_at", -1)],
        )

        if document is None:
            return None

        return self._to_domain(document)

    async def list_alerts(
        self,
        filters: AlertFilters,
        cursor: str | None,
        limit: int,
    ) -> Page[Alert]:
        query: dict[str, Any] = {}

        if filters.severity:
            query["severity"] = filters.severity

        if filters.source_ip:
            query["source_ip"] = filters.source_ip

        if cursor:
            query["created_at"] = {"$lt": datetime.fromisoformat(cursor)}

        mongo_cursor = (
            self._collection.find(query).sort("created_at", -1).limit(limit + 1)
        )

        documents = await mongo_cursor.to_list(length=limit + 1)

        has_next = len(documents) > limit

        if has_next:
            documents = documents[:limit]

        items = [self._to_domain(doc) for doc in documents]

        next_cursor = None

        if has_next and items:
            next_cursor = items[-1].created_at.isoformat()

        return Page(
            items=items,
            next_cursor=next_cursor,
        )

    @staticmethod
    def _to_document(alert: Alert) -> dict[str, Any]:
        return {
            "_id": alert.alert_id,
            "title": alert.title,
            "severity": alert.severity,
            "source_ip": alert.source_ip,
            "description": alert.description,
            "tags": alert.tags,
            "status": alert.status,
            "created_at": alert.created_at,
        }

    @staticmethod
    def _to_domain(document: dict[str, Any]) -> Alert:
        return Alert(
            alert_id=document["_id"],
            title=document["title"],
            severity=document["severity"],
            source_ip=document["source_ip"],
            description=document["description"],
            tags=document.get("tags", []),
            status=document["status"],
            created_at=document["created_at"],
        )
