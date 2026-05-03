from __future__ import annotations

from redis.asyncio import Redis


class RedisStore:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def close(self) -> None:
        await self.redis.aclose()
