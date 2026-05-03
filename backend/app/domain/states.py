from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import IncidentState


class StateBehavior(Protocol):
    @property
    def name(self) -> IncidentState: ...

    def can_transition_to(self, target: IncidentState) -> bool: ...


@dataclass(frozen=True, slots=True)
class OpenState:
    name: IncidentState = IncidentState.OPEN

    def can_transition_to(self, target: IncidentState) -> bool:
        return target in {IncidentState.INVESTIGATING, IncidentState.RESOLVED}


@dataclass(frozen=True, slots=True)
class InvestigatingState:
    name: IncidentState = IncidentState.INVESTIGATING

    def can_transition_to(self, target: IncidentState) -> bool:
        return target in {IncidentState.RESOLVED, IncidentState.INVESTIGATING}


@dataclass(frozen=True, slots=True)
class ResolvedState:
    name: IncidentState = IncidentState.RESOLVED

    def can_transition_to(self, target: IncidentState) -> bool:
        return target in {
            IncidentState.CLOSED,
            IncidentState.INVESTIGATING,
            IncidentState.RESOLVED,
        }


@dataclass(frozen=True, slots=True)
class ClosedState:
    name: IncidentState = IncidentState.CLOSED

    def can_transition_to(self, target: IncidentState) -> bool:
        return target == IncidentState.CLOSED


STATE_REGISTRY: dict[IncidentState, StateBehavior] = {
    IncidentState.OPEN: OpenState(),
    IncidentState.INVESTIGATING: InvestigatingState(),
    IncidentState.RESOLVED: ResolvedState(),
    IncidentState.CLOSED: ClosedState(),
}
