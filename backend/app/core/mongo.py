from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class MongoStore:
    def __init__(self, client: AsyncIOMotorClient, database: AsyncIOMotorDatabase) -> None:
        self.client = client
        self.database = database

    async def close(self) -> None:
        self.client.close()
