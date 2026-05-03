from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routers.health import router as health_router
from app.api.routers.incidents import router as incidents_router
from app.api.routers.signals import router as signals_router
from app.api.routers.seed import router as seed_router
from app.core.config import get_settings
from app.core.container import AppContainer, build_container
from app.domain.exceptions import InvalidStateTransition, MissingRCA, RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    container = await build_container(settings)
    app.state.container = container
    try:
        yield
    finally:
        await container.close()


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)
app.include_router(health_router)
app.include_router(signals_router)
app.include_router(incidents_router)
app.include_router(seed_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": str(exc)})


@app.exception_handler(InvalidStateTransition)
async def state_handler(request: Request, exc: InvalidStateTransition):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(MissingRCA)
async def missing_rca_handler(request: Request, exc: MissingRCA):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
