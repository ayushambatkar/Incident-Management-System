from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.domain.enums import IncidentState, Severity
from app.domain.models import Incident, RCA


@runtime_checkable
class RateLimiter(Protocol):
    async def allow(
        self, component_id: str, limit_per_minute: int, window_seconds: int
    ) -> bool: ...


@runtime_checkable
class QueueRepository(Protocol):
    async def ensure_group(self) -> None: ...

    async def enqueue_signal(self, payload: dict[str, Any]) -> str: ...

    async def read_batch(
        self, *, count: int, block_ms: int
    ) -> list[tuple[str, dict[str, str]]]: ...

    async def ack(self, message_id: str) -> None: ...

    async def stream_lag(self) -> int: ...


@runtime_checkable
class DebounceStore(Protocol):
    async def reserve(self, component_id: str, ttl_seconds: int) -> bool: ...

    async def finalize(
        self, component_id: str, work_item_id: int, ttl_seconds: int
    ) -> bool: ...

    async def get_work_item(self, component_id: str) -> int | None: ...

    async def clear(self, component_id: str) -> None: ...


@runtime_checkable
class IncidentRepository(Protocol):
    async def create(
        self, component_id: str, severity: Severity, start_time
    ) -> Incident: ...

    async def get(self, incident_id: int) -> Incident | None: ...

    async def list_active(self) -> list[Incident]: ...

    async def update_state(
        self, incident_id: int, state: IncidentState, end_time=None
    ) -> Incident: ...

    async def update_severity(
        self, incident_id: int, severity: Severity
    ) -> Incident: ...

    async def incident_has_rca(self, incident_id: int) -> bool: ...


@runtime_checkable
class RCARepository(Protocol):
    async def upsert(
        self, work_item_id: int, root_cause: str, fix: str, prevention: str
    ) -> RCA: ...

    async def get(self, work_item_id: int) -> RCA | None: ...


@runtime_checkable
class SignalRepository(Protocol):
    async def save_raw_signal(
        self,
        *,
        component_id: str,
        work_item_id: int,
        payload: dict[str, Any],
        timestamp,
    ) -> None: ...

    async def list_signals(self, work_item_id: int) -> list[dict[str, Any]]: ...


@runtime_checkable
class CacheRepository(Protocol):
    async def get_active_incidents(self) -> list[dict[str, Any]] | None: ...

    async def set_active_incidents(self, incidents: list[dict[str, Any]]) -> None: ...

    async def upsert_incident(self, incident: dict[str, Any]) -> None: ...

    async def remove_incident(self, incident_id: int) -> None: ...


@runtime_checkable
class AlertDispatcher(Protocol):
    async def alert_new_incident(
        self, component_id: str, severity: Severity, message: str
    ) -> None: ...
