from __future__ import annotations

import asyncio

from app.core.container import AppContainer


class ProcessingMetrics:
    def __init__(self) -> None:
        self._processed = 0
        self._lock = asyncio.Lock()

    async def record(self, count: int = 1) -> None:
        async with self._lock:
            self._processed += count

    async def snapshot_and_reset(self) -> int:
        async with self._lock:
            value = self._processed
            self._processed = 0
            return value


async def metrics_loop(container: AppContainer, metrics: ProcessingMetrics) -> None:
    while True:
        await asyncio.sleep(container.settings.metrics_interval_seconds)
        processed = await metrics.snapshot_and_reset()
        signals_per_second = processed / container.settings.metrics_interval_seconds
        queue_lag = await container.queue_repo.stream_lag()
        print(f"[metrics] signals/sec={signals_per_second:.2f} queue_lag={queue_lag}")
