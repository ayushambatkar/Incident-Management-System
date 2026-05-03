from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.container import build_container
from app.workers.metrics import ProcessingMetrics, metrics_loop


async def consume() -> None:
    settings = get_settings()
    container = await build_container(settings)
    metrics = ProcessingMetrics()

    await container.queue_repo.ensure_group()

    async def stream_loop() -> None:
        while True:
            batch = await container.queue_repo.read_batch(
                count=settings.queue_read_count, block_ms=settings.queue_block_ms
            )
            if not batch:
                continue

            for message_id, payload in batch:
                try:
                    await container.workflow_service.handle_signal(payload)
                    await container.queue_repo.ack(message_id)
                    await metrics.record()
                except Exception as exc:  # noqa: BLE001
                    print(f"[worker] failed message_id={message_id} error={exc}")

    try:
        await asyncio.gather(stream_loop(), metrics_loop(container, metrics))
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(consume())
