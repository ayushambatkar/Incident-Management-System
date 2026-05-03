"""Simulate an RDBMS outage by posting a burst of P0 signals to the ingestion API."""

from __future__ import annotations

import argparse
import asyncio
import random
import time

import httpx

COMPONENT = "RDBMS_PRIMARY"
MESSAGES = [
    "Connection refused",
    "Too many connections",
    "Lock wait timeout",
    "Replication lag high",
]


async def send_signal(client: httpx.AsyncClient):
    payload = {
        "component_id": COMPONENT,
        "severity": "P0",
        "message": random.choice(MESSAGES),
        "timestamp": time.time(),
    }
    try:
        await client.post("http://localhost:8000/signal", json=payload, timeout=5.0)
    except Exception:
        pass


async def run(count: int, rate: int) -> None:
    interval = 1.0 / float(rate) if rate and rate > 0 else 0
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(count):
            tasks.append(asyncio.create_task(send_signal(client)))
            if interval > 0:
                await asyncio.sleep(interval)
        if tasks:
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--count", type=int, default=100, help="number of signals to send"
    )
    parser.add_argument(
        "--rate", type=int, default=1000, help="signals per second (approx)"
    )
    args = parser.parse_args()
    asyncio.run(run(args.count, args.rate))
