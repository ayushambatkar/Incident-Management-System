from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_datetime(timestamp: int | float) -> datetime:
    normalized = float(timestamp)
    if normalized > 1_000_000_000_000:
        normalized /= 1000.0
    return datetime.fromtimestamp(normalized, tz=timezone.utc)
