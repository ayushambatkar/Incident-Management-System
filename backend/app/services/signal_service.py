from __future__ import annotations

import time

from app.domain.exceptions import RateLimitExceeded
from app.schemas.signal import SignalIn
from app.repositories.interfaces import QueueRepository, RateLimiter


class SignalIngestionService:
    def __init__(
        self,
        queue_repo: QueueRepository,
        rate_limiter: RateLimiter,
        *,
        rate_limit_per_minute: int,
        rate_limit_window_seconds: int,
    ) -> None:
        self.queue_repo = queue_repo
        self.rate_limiter = rate_limiter
        self.rate_limit_per_minute = rate_limit_per_minute
        self.rate_limit_window_seconds = rate_limit_window_seconds

    async def ingest(self, signal: SignalIn) -> str:
        allowed = await self.rate_limiter.allow(
            signal.component_id,
            self.rate_limit_per_minute,
            self.rate_limit_window_seconds,
        )
        if not allowed:
            raise RateLimitExceeded(
                f"rate limit exceeded for component {signal.component_id}"
            )

        payload = signal.model_dump()
        payload["queued_at"] = time.time()
        return await self.queue_repo.enqueue_signal(payload)
