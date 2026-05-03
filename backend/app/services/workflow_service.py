from __future__ import annotations

import asyncio
from typing import Any

from app.core.time import to_datetime, utc_now
from app.domain.enums import IncidentState, Severity
from app.domain.exceptions import MissingRCA
from app.domain.models import SignalEvent
from app.repositories.interfaces import (
    AlertDispatcher,
    CacheRepository,
    DebounceStore,
    IncidentRepository,
    SignalRepository,
)
from app.schemas.signal import SignalPayload

_SEVERITY_RANK = {Severity.P0: 0, Severity.P1: 1, Severity.P2: 2, Severity.P3: 3}


class IncidentWorkflowService:
    def __init__(
        self,
        incident_repo: IncidentRepository,
        signal_repo: SignalRepository,
        debounce_store: DebounceStore,
        cache_repo: CacheRepository,
        alert_dispatcher: AlertDispatcher,
        *,
        debounce_ttl_seconds: int,
    ) -> None:
        self.incident_repo = incident_repo
        self.signal_repo = signal_repo
        self.debounce_store = debounce_store
        self.cache_repo = cache_repo
        self.alert_dispatcher = alert_dispatcher
        self.debounce_ttl_seconds = debounce_ttl_seconds

    @staticmethod
    def _to_event(payload: dict[str, str]) -> SignalEvent:
        signal = SignalPayload(
            component_id=payload["component_id"],
            severity=Severity(payload["severity"]),
            message=payload["message"],
            timestamp=float(payload["timestamp"]),
            queued_at=(
                float(payload["queued_at"])
                if payload.get("queued_at") is not None
                else None
            ),
        )
        return SignalEvent(
            component_id=signal.component_id,
            severity=signal.severity,
            message=signal.message,
            timestamp=to_datetime(signal.timestamp),
            raw_timestamp=signal.timestamp,
        )

    async def handle_signal(self, payload: dict[str, str]) -> None:
        event = self._to_event(payload)
        work_item_id = await self.debounce_store.get_work_item(event.component_id)

        if work_item_id is None:
            reserved = await self.debounce_store.reserve(
                event.component_id, self.debounce_ttl_seconds
            )
            if not reserved:
                for _ in range(20):
                    await asyncio.sleep(0.05)
                    work_item_id = await self.debounce_store.get_work_item(
                        event.component_id
                    )
                    if work_item_id is not None:
                        break
                if work_item_id is None:
                    return

            incident = await self.incident_repo.create(
                event.component_id, event.severity, event.timestamp
            )
            await self.debounce_store.finalize(
                event.component_id, incident.id, self.debounce_ttl_seconds
            )
            await self.signal_repo.save_raw_signal(
                component_id=event.component_id,
                work_item_id=incident.id,
                payload={
                    "component_id": event.component_id,
                    "severity": event.severity.value,
                    "message": event.message,
                    "timestamp": event.raw_timestamp,
                },
                timestamp=event.timestamp,
            )
            await self.cache_repo.upsert_incident(self._incident_to_cache(incident))
            await self.alert_dispatcher.alert_new_incident(
                event.component_id, event.severity, event.message
            )
            return

        incident = await self.incident_repo.get(work_item_id)
        if incident is None:
            await self.debounce_store.clear(event.component_id)
            return await self.handle_signal(payload)

        if _SEVERITY_RANK[event.severity] < _SEVERITY_RANK[incident.severity]:
            incident = await self.incident_repo.update_severity(
                incident.id, event.severity
            )

        await self.signal_repo.save_raw_signal(
            component_id=event.component_id,
            work_item_id=incident.id,
            payload={
                "component_id": event.component_id,
                "severity": event.severity.value,
                "message": event.message,
                "timestamp": event.raw_timestamp,
            },
            timestamp=event.timestamp,
        )
        await self.cache_repo.upsert_incident(self._incident_to_cache(incident))

    @staticmethod
    def _incident_to_cache(incident) -> dict[str, Any]:
        return {
            "id": incident.id,
            "component_id": incident.component_id,
            "severity": incident.severity.value,
            "state": incident.state.value,
            "start_time": incident.start_time.isoformat(),
            "end_time": incident.end_time.isoformat() if incident.end_time else None,
        }
