from __future__ import annotations

from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis, from_url

from app.core.config import Settings
from app.core.db import PostgresStore
from app.core.mongo import MongoStore
from app.core.redis import RedisStore
from app.repositories.mongo import MongoSignalRepository
from app.repositories.postgres import PostgresIncidentRepository, PostgresRCARepository
from app.repositories.redis import (
    RedisDebounceStore,
    RedisIncidentCacheRepository,
    RedisRateLimiter,
    RedisStreamQueueRepository,
)
from app.services.alert_service import AlertService
from app.services.incident_service import (
    IncidentQueryService,
    IncidentStateService,
    RCAService,
)
from app.services.signal_service import SignalIngestionService
from app.services.workflow_service import IncidentWorkflowService
from app.services.seeder_service import SeederService


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    redis_store: RedisStore
    postgres_store: PostgresStore
    mongo_store: MongoStore
    queue_repo: RedisStreamQueueRepository
    rate_limiter: RedisRateLimiter
    debounce_store: RedisDebounceStore
    incident_repo: PostgresIncidentRepository
    rca_repo: PostgresRCARepository
    signal_repo: MongoSignalRepository
    cache_repo: RedisIncidentCacheRepository
    alert_service: AlertService
    signal_service: SignalIngestionService
    workflow_service: IncidentWorkflowService
    incident_query_service: IncidentQueryService
    incident_state_service: IncidentStateService
    rca_service: RCAService
    seeder_service: SeederService

    async def close(self) -> None:
        await self.redis_store.close()
        await self.mongo_store.close()
        await self.postgres_store.close()


async def build_container(settings: Settings) -> AppContainer:
    redis_client: Redis = from_url(settings.redis_url, decode_responses=True)
    redis_store = RedisStore(redis_client)

    postgres_store = PostgresStore(settings.postgres_dsn)
    await postgres_store.connect()

    mongo_client = AsyncIOMotorClient(settings.mongo_url)
    mongo_database = mongo_client[settings.mongo_db]
    mongo_store = MongoStore(mongo_client, mongo_database)

    queue_repo = RedisStreamQueueRepository(
        redis_client,
        settings.queue_stream,
        settings.queue_group,
        settings.queue_consumer,
    )
    rate_limiter = RedisRateLimiter(redis_client)
    debounce_store = RedisDebounceStore(redis_client)
    incident_repo = PostgresIncidentRepository(postgres_store)
    rca_repo = PostgresRCARepository(postgres_store)
    signal_repo = MongoSignalRepository(mongo_database)
    cache_repo = RedisIncidentCacheRepository(redis_client)
    alert_service = AlertService()

    await queue_repo.ensure_group()
    await signal_repo.ensure_indexes()

    signal_service = SignalIngestionService(
        queue_repo,
        rate_limiter,
        rate_limit_per_minute=settings.rate_limit_per_minute,
        rate_limit_window_seconds=settings.rate_limit_window_seconds,
    )
    workflow_service = IncidentWorkflowService(
        incident_repo,
        signal_repo,
        debounce_store,
        cache_repo,
        alert_service,
        debounce_ttl_seconds=settings.debounce_ttl_seconds,
    )
    incident_query_service = IncidentQueryService(
        incident_repo, rca_repo, signal_repo, cache_repo
    )
    incident_state_service = IncidentStateService(incident_repo, rca_repo, cache_repo)
    rca_service = RCAService(incident_repo, rca_repo, signal_repo, cache_repo)
    seeder_service = SeederService(queue_repo)

    return AppContainer(
        settings=settings,
        redis_store=redis_store,
        postgres_store=postgres_store,
        mongo_store=mongo_store,
        queue_repo=queue_repo,
        rate_limiter=rate_limiter,
        debounce_store=debounce_store,
        incident_repo=incident_repo,
        rca_repo=rca_repo,
        signal_repo=signal_repo,
        cache_repo=cache_repo,
        alert_service=alert_service,
        signal_service=signal_service,
        workflow_service=workflow_service,
        incident_query_service=incident_query_service,
        incident_state_service=incident_state_service,
        rca_service=rca_service,
        seeder_service=seeder_service,
    )
