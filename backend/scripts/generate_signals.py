from __future__ import annotations

import argparse
import asyncio
import random
import time

import httpx


COMPONENTS = ["auth", "billing", "search", "notifications", "checkout", "profile"]
SEVERITIES = ["P0", "P1", "P2", "P3"]
MESSAGES = [
    "latency spike detected",
    "timeout rate elevated",
    "error budget burning",
    "dependency unavailable",
    "memory pressure high",
    "database slow query observed",
]


async def send_signal(client: httpx.AsyncClient, url: str) -> None:
    payload = {
        "component_id": random.choice(COMPONENTS),
        "severity": random.choices(SEVERITIES, weights=[1, 2, 3, 6], k=1)[0],
        "message": random.choice(MESSAGES),
        "timestamp": time.time(),
    }
    response = await client.post(url, json=payload)
    response.raise_for_status()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000/signal")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()

    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient(timeout=10.0) as client:
        async def worker() -> None:
            async with semaphore:
                await send_signal(client, args.url)

        await asyncio.gather(*(worker() for _ in range(args.count)))


if __name__ == "__main__":
    asyncio.run(main())
