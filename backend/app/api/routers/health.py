from __future__ import annotations

from fastapi import APIRouter, Depends
from typing import Any

from app.api.deps import get_container
from app.core.container import AppContainer
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(container: AppContainer = Depends(get_container)) -> HealthResponse:
    redis_status = "ok"
    postgres_status = "ok"
    mongo_status = "ok"

    try:
        redis_client: Any = container.redis_store.redis
        await redis_client.ping()
    except Exception:  # noqa: BLE001
        redis_status = "degraded"

    try:
        await container.postgres_store.fetchval("SELECT 1")
    except Exception:  # noqa: BLE001
        postgres_status = "degraded"

    try:
        await container.mongo_store.database.command("ping")
    except Exception:  # noqa: BLE001
        mongo_status = "degraded"

    return HealthResponse(
        status=(
            "ok"
            if {redis_status, postgres_status, mongo_status} == {"ok"}
            else "degraded"
        ),
        services={
            "redis": redis_status,
            "postgres": postgres_status,
            "mongo": mongo_status,
        },
    )
