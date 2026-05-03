from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import Severity


class SignalIn(BaseModel):
    component_id: str = Field(min_length=1, max_length=128)
    severity: Severity
    message: str = Field(min_length=1, max_length=10_000)
    timestamp: int | float = Field(gt=0)

    @field_validator("component_id", "message")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class SignalAccepted(BaseModel):
    status: str = "accepted"
    queued: bool = True


class SignalPayload(BaseModel):
    component_id: str
    severity: Severity
    message: str
    timestamp: int | float
    queued_at: int | float | None = None
