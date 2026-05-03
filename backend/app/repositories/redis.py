from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any, cast
from enum import Enum
from enum import Enum

from redis.asyncio import Redis

from app.domain.enums import Severity
from app.domain.models import Incident
from app.repositories.interfaces import (
    CacheRepository,
    DebounceStore,
    QueueRepository,
    RateLimiter,
)


class RedisRateLimiter(RateLimiter):
    def __init__(self, redis: Redis, prefix: str = "rate_limit") -> None:
        self.redis = redis
        self.prefix = prefix
        self._script = self.redis.register_script("""
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])

            redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
            local count = redis.call('ZCARD', key)
            if count >= limit then
                return 0
            end

            local member = redis.sha1hex(tostring(now) .. '-' .. tostring(count))
            redis.call('ZADD', key, now, member)
            redis.call('EXPIRE', key, math.ceil(window / 1000))
            return 1
            """)

    async def allow(
        self, component_id: str, limit_per_minute: int, window_seconds: int
    ) -> bool:
        now_ms = int(time.time() * 1000)
        key = f"{self.prefix}:{component_id}"
        result = await self._script(
            keys=[key], args=[now_ms, window_seconds * 1000, limit_per_minute]
        )
        return bool(result)


class RedisDebounceStore(DebounceStore):
    def __init__(self, redis: Redis, prefix: str = "debounce") -> None:
        self.redis = redis
        self.prefix = prefix

    def _key(self, component_id: str) -> str:
        return f"{self.prefix}:{component_id}"

    async def reserve(self, component_id: str, ttl_seconds: int) -> bool:
        key = self._key(component_id)
        return bool(await self.redis.set(key, "PENDING", ex=ttl_seconds, nx=True))

    async def finalize(
        self, component_id: str, work_item_id: int, ttl_seconds: int
    ) -> bool:
        key = self._key(component_id)
        return bool(
            await self.redis.set(key, str(work_item_id), ex=ttl_seconds, xx=True)
        )

    async def get_work_item(self, component_id: str) -> int | None:
        value = await self.redis.get(self._key(component_id))
        if value is None or value == "PENDING":
            return None
        return int(value)

    async def clear(self, component_id: str) -> None:
        await self.redis.delete(self._key(component_id))


class RedisStreamQueueRepository(QueueRepository):
    def __init__(
        self, redis: Redis, stream_name: str, group_name: str, consumer_name: str
    ) -> None:
        self.redis = redis
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name

    async def ensure_group(self) -> None:
        try:
            await self.redis.xgroup_create(
                self.stream_name, self.group_name, id="0", mkstream=True
            )
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            if (
                "busygroup" not in message
                and "group name already exists" not in message
            ):
                raise

    async def enqueue_signal(self, payload: dict[str, Any]) -> str:
        message: dict[str, str] = {}
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                message[key] = json.dumps(value)
            elif isinstance(value, Enum):
                message[key] = str(value.value)
            else:
                message[key] = str(value)
        # redis-py type signatures are strict; cast to bypass editor type mismatch
        return await self.redis.xadd(self.stream_name, cast(dict, message))

    async def read_batch(
        self, *, count: int, block_ms: int
    ) -> list[tuple[str, dict[str, str]]]:
        response = await self.redis.xreadgroup(
            groupname=self.group_name,
            consumername=self.consumer_name,
            streams={self.stream_name: ">"},
            count=count,
            block=block_ms,
        )
        batch: list[tuple[str, dict[str, str]]] = []
        for _stream, entries in response:
            for message_id, payload in entries:
                batch.append(
                    (message_id, {key: value for key, value in payload.items()})
                )
        return batch

    async def ack(self, message_id: str) -> None:
        await self.redis.xack(self.stream_name, self.group_name, message_id)

    async def stream_lag(self) -> int:
        try:
            groups = await self.redis.xinfo_groups(self.stream_name)
            for group in groups:
                if group.get("name") == self.group_name:
                    lag = group.get("lag")
                    if lag is not None:
                        return int(lag)
        except Exception:  # noqa: BLE001
            return 0
        return 0


class RedisIncidentCacheRepository(CacheRepository):
    def __init__(
        self,
        redis: Redis,
        prefix: str = "incident_cache",
        active_key: str = "active_incidents",
    ) -> None:
        self.redis = redis
        self.prefix = prefix
        self.active_key = active_key

    def _incident_key(self, incident_id: int) -> str:
        return f"{self.prefix}:{incident_id}"

    @staticmethod
    def _severity_score(severity: str | Severity) -> int:
        mapping = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        key = severity.value if isinstance(severity, Enum) else str(severity)
        return mapping.get(key, 3)

    @staticmethod
    def _serialize_incident(incident: dict[str, Any]) -> str:
        return json.dumps(incident, default=str)

    async def get_active_incidents(self) -> list[dict[str, Any]] | None:
        incident_ids = await self.redis.zrange(self.active_key, 0, -1)
        if not incident_ids:
            return None

        incidents: list[dict[str, Any]] = []
        for incident_id in incident_ids:
            payload = await self.redis.get(self._incident_key(int(incident_id)))
            if payload is not None:
                incidents.append(json.loads(payload))
        return incidents

    async def set_active_incidents(self, incidents: list[dict[str, Any]]) -> None:
        existing_ids = await self.redis.zrange(self.active_key, 0, -1)
        pipeline = self.redis.pipeline()
        if existing_ids:
            pipeline.delete(
                self.active_key,
                *[self._incident_key(int(incident_id)) for incident_id in existing_ids],
            )
        else:
            pipeline.delete(self.active_key)
        for incident in incidents:
            incident_id = int(incident["id"])
            pipeline.set(
                self._incident_key(incident_id), self._serialize_incident(incident)
            )
            pipeline.zadd(
                self.active_key,
                {str(incident_id): self._severity_score(incident["severity"])},
            )
        await pipeline.execute()

    async def upsert_incident(self, incident: dict[str, Any]) -> None:
        pipeline = self.redis.pipeline()
        incident_id = int(incident["id"])
        pipeline.set(
            self._incident_key(incident_id), self._serialize_incident(incident)
        )
        pipeline.zadd(
            self.active_key,
            {str(incident_id): self._severity_score(incident["severity"])},
        )
        await pipeline.execute()

    async def remove_incident(self, incident_id: int) -> None:
        pipeline = self.redis.pipeline()
        pipeline.delete(self._incident_key(incident_id))
        pipeline.zrem(self.active_key, str(incident_id))
        await pipeline.execute()
