from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_container
from app.core.container import AppContainer
from app.domain.exceptions import InvalidStateTransition, MissingRCA, RateLimitExceeded
from app.schemas.incident import (
    IncidentDetailResponse,
    IncidentStateUpdate,
    IncidentSummary,
    RCAIn,
)

router = APIRouter(tags=["incidents"])


@router.get("/incidents", response_model=list[IncidentSummary])
async def list_incidents(
    container: AppContainer = Depends(get_container),
) -> list[IncidentSummary]:
    return await container.incident_query_service.list_active_incidents()


@router.get("/incident/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: int, container: AppContainer = Depends(get_container)
) -> IncidentDetailResponse:
    try:
        return await container.incident_query_service.get_incident_detail(incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/incident/{incident_id}/state", response_model=IncidentSummary)
async def update_state(
    incident_id: int,
    update: IncidentStateUpdate,
    container: AppContainer = Depends(get_container),
) -> IncidentSummary:
    try:
        return await container.incident_state_service.transition_state(
            incident_id, update
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (InvalidStateTransition, MissingRCA) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/incident/{incident_id}/rca", response_model=IncidentDetailResponse)
async def add_rca(
    incident_id: int, rca: RCAIn, container: AppContainer = Depends(get_container)
) -> IncidentDetailResponse:
    try:
        return await container.rca_service.create_rca(incident_id, rca)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
