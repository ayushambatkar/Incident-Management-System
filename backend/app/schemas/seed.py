from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SeedMode = Literal["burst", "stream"]


class SeedStartResponse(BaseModel):
    status: str = "started"


class SeedJobView(BaseModel):
    job_id: str
    mode: SeedMode
    requested_count: int
    sent_count: int
    rate: int | None = None
    status: Literal["running", "completed", "failed"]
    started_at: datetime
    finished_at: datetime | None = None
    error: str | None = None


class SeedStatusResponse(BaseModel):
    active_jobs: int
    total_signals_sent: int
    jobs: list[SeedJobView] = Field(default_factory=list)
