from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.interfaces import SignalRepository


class MongoSignalRepository(SignalRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database.signals

    async def ensure_indexes(self) -> None:
        await self.collection.create_index([("work_item_id", 1), ("timestamp", 1)])
        await self.collection.create_index([("component_id", 1), ("timestamp", -1)])

    async def save_raw_signal(
        self,
        *,
        component_id: str,
        work_item_id: int,
        payload: dict[str, Any],
        timestamp,
    ) -> None:
        await self.collection.insert_one(
            {
                "component_id": component_id,
                "work_item_id": work_item_id,
                "payload": payload,
                "timestamp": timestamp,
            }
        )

    async def list_signals(self, work_item_id: int) -> list[dict[str, Any]]:
        cursor = self.collection.find({"work_item_id": work_item_id}).sort(
            "timestamp", 1
        )
        documents: list[dict[str, Any]] = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            timestamp = document.get("timestamp")
            if hasattr(timestamp, "isoformat"):
                document["timestamp"] = timestamp.isoformat()
            documents.append(document)
        return documents
