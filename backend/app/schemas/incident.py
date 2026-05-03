from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import IncidentState, Severity


class RCAIn(BaseModel):
    root_cause: str = Field(min_length=1, max_length=10_000)
    fix: str = Field(min_length=1, max_length=10_000)
    prevention: str = Field(min_length=1, max_length=10_000)


class IncidentStateUpdate(BaseModel):
    state: IncidentState


class IncidentSummary(BaseModel):
    id: int
    component_id: str
    severity: Severity
    state: IncidentState
    start_time: datetime
    end_time: datetime | None = None
    mttr_seconds: float | None = None


class IncidentDetailResponse(IncidentSummary):
    rca: RCAIn | None = None
    signals: list[dict] = Field(default_factory=list)
