from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.schemas.seed import SeedStartResponse
from app.schemas.seed import SeedMode

router = APIRouter(prefix="/seed", tags=["seed"])


@router.post("", status_code=202, response_model=SeedStartResponse)
async def start_seed(
    request: Request,
    count: int = Query(100),
    mode: SeedMode = Query("burst"),
    rate: int = Query(10),
):
    container = request.app.state.container
    seeder = getattr(container, "seeder_service", None)
    if seeder is None:
        return JSONResponse(status_code=404, content={"detail": "Seeder not available"})
    job_id = await seeder.start_seed_job(count=count, mode=mode, rate=rate)
    return SeedStartResponse(status=f"started:{job_id}")


@router.get("/status")
async def seed_status(request: Request):
    container = request.app.state.container
    seeder = getattr(container, "seeder_service", None)
    if seeder is None:
        return JSONResponse(status_code=404, content={"detail": "Seeder not available"})
    status = await seeder.status()
    return status
