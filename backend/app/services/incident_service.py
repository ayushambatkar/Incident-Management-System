from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.time import utc_now
from app.domain.enums import IncidentState
from app.domain.exceptions import InvalidStateTransition, MissingRCA
from app.domain.models import Incident
from app.domain.states import STATE_REGISTRY
from app.repositories.interfaces import (
    CacheRepository,
    IncidentRepository,
    RCARepository,
    SignalRepository,
)
from app.schemas.incident import (
    IncidentDetailResponse,
    IncidentSummary,
    IncidentStateUpdate,
    RCAIn,
)


class IncidentQueryService:
    def __init__(
        self,
        incident_repo: IncidentRepository,
        rca_repo: RCARepository,
        signal_repo: SignalRepository,
        cache_repo: CacheRepository,
    ) -> None:
        self.incident_repo = incident_repo
        self.rca_repo = rca_repo
        self.signal_repo = signal_repo
        self.cache_repo = cache_repo

    @staticmethod
    def _summary(
        incident: Incident, mttr_seconds: float | None = None
    ) -> IncidentSummary:
        return IncidentSummary(
            id=incident.id,
            component_id=incident.component_id,
            severity=incident.severity,
            state=incident.state,
            start_time=incident.start_time,
            end_time=incident.end_time,
            mttr_seconds=mttr_seconds,
        )

    async def list_active_incidents(self) -> list[IncidentSummary]:
        cached = await self.cache_repo.get_active_incidents()
        if cached is not None:
            return [IncidentSummary(**item) for item in cached]

        incidents = await self.incident_repo.list_active()
        summaries = [self._summary(incident) for incident in incidents]
        await self.cache_repo.set_active_incidents(
            [summary.model_dump(mode="json") for summary in summaries]
        )
        return summaries

    async def get_incident_detail(self, incident_id: int) -> IncidentDetailResponse:
        incident = await self.incident_repo.get(incident_id)
        if incident is None:
            raise KeyError(f"incident {incident_id} not found")

        rca = await self.rca_repo.get(incident_id)
        signals = await self.signal_repo.list_signals(incident_id)
        mttr_seconds = None
        if incident.end_time is not None:
            mttr_seconds = float(
                (incident.end_time - incident.start_time).total_seconds()
            )

        return IncidentDetailResponse(
            **self._summary(incident, mttr_seconds=mttr_seconds).model_dump(),
            rca=(
                RCAIn(root_cause=rca.root_cause, fix=rca.fix, prevention=rca.prevention)
                if rca
                else None
            ),
            signals=signals,
        )


class IncidentStateService:
    def __init__(
        self,
        incident_repo: IncidentRepository,
        rca_repo: RCARepository,
        cache_repo: CacheRepository,
    ) -> None:
        self.incident_repo = incident_repo
        self.rca_repo = rca_repo
        self.cache_repo = cache_repo

    async def transition_state(
        self, incident_id: int, update: IncidentStateUpdate
    ) -> IncidentSummary:
        incident = await self.incident_repo.get(incident_id)
        if incident is None:
            raise KeyError(f"incident {incident_id} not found")

        target_state = update.state
        current_state = incident.state
        if current_state == target_state:
            return IncidentSummary(
                id=incident.id,
                component_id=incident.component_id,
                severity=incident.severity,
                state=incident.state,
                start_time=incident.start_time,
                end_time=incident.end_time,
            )

        state_behavior = STATE_REGISTRY[current_state]
        if not state_behavior.can_transition_to(target_state):
            raise InvalidStateTransition(
                f"cannot transition from {current_state.value} to {target_state.value}"
            )

        if (
            target_state == IncidentState.CLOSED
            and not await self.incident_repo.incident_has_rca(incident_id)
        ):
            raise MissingRCA("incident cannot be closed without RCA")

        closed_at = utc_now() if target_state == IncidentState.CLOSED else None
        updated = await self.incident_repo.update_state(
            incident_id, target_state, end_time=closed_at
        )
        if updated.state == IncidentState.CLOSED:
            await self.cache_repo.remove_incident(incident_id)
        else:
            await self.cache_repo.upsert_incident(
                {
                    "id": updated.id,
                    "component_id": updated.component_id,
                    "severity": updated.severity.value,
                    "state": updated.state.value,
                    "start_time": updated.start_time.isoformat(),
                    "end_time": (
                        updated.end_time.isoformat() if updated.end_time else None
                    ),
                }
            )

        return IncidentSummary(
            id=updated.id,
            component_id=updated.component_id,
            severity=updated.severity,
            state=updated.state,
            start_time=updated.start_time,
            end_time=updated.end_time,
            mttr_seconds=(
                float((updated.end_time - updated.start_time).total_seconds())
                if updated.end_time
                else None
            ),
        )


class RCAService:
    def __init__(
        self,
        incident_repo: IncidentRepository,
        rca_repo: RCARepository,
        signal_repo: SignalRepository,
        cache_repo: CacheRepository,
    ) -> None:
        self.incident_repo = incident_repo
        self.rca_repo = rca_repo
        self.signal_repo = signal_repo
        self.cache_repo = cache_repo

    async def create_rca(
        self, incident_id: int, payload: RCAIn
    ) -> IncidentDetailResponse:
        incident = await self.incident_repo.get(incident_id)
        if incident is None:
            raise KeyError(f"incident {incident_id} not found")

        rca = await self.rca_repo.upsert(
            incident_id, payload.root_cause, payload.fix, payload.prevention
        )
        updated_incident = incident
        if incident.state != IncidentState.CLOSED:
            updated_incident = await self.incident_repo.update_state(
                incident_id, IncidentState.CLOSED, end_time=utc_now()
            )
            await self.cache_repo.remove_incident(incident_id)

        mttr_seconds = (
            float(
                (
                    updated_incident.end_time - updated_incident.start_time
                ).total_seconds()
            )
            if updated_incident.end_time
            else None
        )
        signals = await self.signal_repo.list_signals(incident_id)
        return IncidentDetailResponse(
            id=updated_incident.id,
            component_id=updated_incident.component_id,
            severity=updated_incident.severity,
            state=updated_incident.state,
            start_time=updated_incident.start_time,
            end_time=updated_incident.end_time,
            mttr_seconds=mttr_seconds,
            rca=RCAIn(
                root_cause=rca.root_cause, fix=rca.fix, prevention=rca.prevention
            ),
            signals=signals,
        )
