from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_container
from app.core.container import AppContainer
from app.schemas.signal import SignalAccepted, SignalIn

router = APIRouter(tags=["signals"])


@router.post(
    "/signal", response_model=SignalAccepted, status_code=status.HTTP_202_ACCEPTED
)
async def ingest_signal(
    signal: SignalIn, container: AppContainer = Depends(get_container)
) -> SignalAccepted:
    await container.signal_service.ingest(signal)
    return SignalAccepted()
