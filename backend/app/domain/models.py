from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.enums import IncidentState, Severity


@dataclass(slots=True)
class SignalEvent:
    component_id: str
    severity: Severity
    message: str
    timestamp: datetime
    raw_timestamp: int | float


@dataclass(slots=True)
class Incident:
    id: int
    component_id: str
    severity: Severity
    state: IncidentState
    start_time: datetime
    end_time: datetime | None


@dataclass(slots=True)
class RCA:
    work_item_id: int
    root_cause: str
    fix: str
    prevention: str


@dataclass(slots=True)
class IncidentDetail:
    incident: Incident
    rca: RCA | None
    signals: list[dict[str, Any]]
    mttr_seconds: float | None = None
