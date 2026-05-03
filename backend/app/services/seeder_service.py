from __future__ import annotations

import asyncio
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from typing import TYPE_CHECKING

from app.domain.enums import Severity
from app.schemas.seed import SeedJobView

if TYPE_CHECKING:
    # avoid runtime import cycles for typing
    pass

from app.repositories.interfaces import QueueRepository
from app.schemas.seed import SeedMode, SeedStatusResponse
from app.schemas.signal import SignalIn

_COMPONENTS = ["CACHE_CLUSTER_01", "RDBMS_PRIMARY", "API_GATEWAY"]
_SEVERITIES = ["P0", "P1", "P2"]
_MESSAGES = [
    "Error rate crossed threshold",
    "Latency spike detected",
    "Service dependency timeout",
    "Database connection saturation",
    "Cache miss storm observed",
    "High CPU pressure detected",
]


@dataclass(slots=True)
class SeedJob:
    job_id: str
    mode: SeedMode
    requested_count: int
    rate: int | None
    status: Literal["running", "completed", "failed"]
    started_at: datetime
    sent_count: int = 0
    finished_at: datetime | None = None
    error: str | None = None


class SeederService:
    def __init__(
        self,
        queue_repo: QueueRepository,
        *,
        max_burst_batch: int = 200,
        max_recent_jobs: int = 100,
    ) -> None:
        self.queue_repo = queue_repo
        self.max_burst_batch = max_burst_batch
        self.max_recent_jobs = max_recent_jobs
        self._jobs: dict[str, SeedJob] = {}
        self._task_index: dict[str, asyncio.Task[None]] = {}
        self._total_signals_sent = 0
        self._lock = asyncio.Lock()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _build_signal(self) -> SignalIn:
        return SignalIn(
            component_id=random.choice(_COMPONENTS),
            severity=Severity(random.choice(_SEVERITIES)),
            message=random.choice(_MESSAGES),
            timestamp=time.time(),
        )

    async def _enqueue_signal(self) -> None:
        signal = self._build_signal()
        payload = signal.model_dump()
        payload["queued_at"] = time.time()
        await self.queue_repo.enqueue_signal(payload)

    async def start_seed_job(self, *, count: int, mode: SeedMode, rate: int) -> str:
        job_id = str(uuid.uuid4())
        job = SeedJob(
            job_id=job_id,
            mode=mode,
            requested_count=count,
            rate=rate if mode == "stream" else None,
            status="running",
            started_at=self._now(),
        )
        async with self._lock:
            self._jobs[job_id] = job

        task = asyncio.create_task(
            self._run_seed_job(job_id), name=f"seed-job-{job_id}"
        )
        self._task_index[job_id] = task
        task.add_done_callback(lambda _done_task: self._task_index.pop(job_id, None))
        return job_id

    async def _run_seed_job(self, job_id: str) -> None:
        job = self._jobs[job_id]
        try:
            if job.mode == "burst":
                await self._run_burst(job)
            else:
                await self._run_stream(job)
            job.status = "completed"
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
        finally:
            job.finished_at = self._now()
            await self._prune_jobs()

    async def _run_burst(self, job: SeedJob) -> None:
        remaining = job.requested_count
        while remaining > 0:
            batch_size = min(self.max_burst_batch, remaining)
            await asyncio.gather(*(self._enqueue_signal() for _ in range(batch_size)))
            async with self._lock:
                job.sent_count += batch_size
                self._total_signals_sent += batch_size
            remaining -= batch_size

    async def _run_stream(self, job: SeedJob) -> None:
        assert job.rate is not None
        interval = 1.0 / float(job.rate)
        next_tick = time.perf_counter()

        for _ in range(job.requested_count):
            await self._enqueue_signal()
            async with self._lock:
                job.sent_count += 1
                self._total_signals_sent += 1

            next_tick += interval
            sleep_for = next_tick - time.perf_counter()
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)

    async def _prune_jobs(self) -> None:
        async with self._lock:
            if len(self._jobs) <= self.max_recent_jobs:
                return
            ordered = sorted(self._jobs.values(), key=lambda item: item.started_at)
            for job in ordered[: len(self._jobs) - self.max_recent_jobs]:
                if job.status != "running":
                    self._jobs.pop(job.job_id, None)

    async def status(self) -> SeedStatusResponse:
        async with self._lock:
            jobs = sorted(
                self._jobs.values(), key=lambda item: item.started_at, reverse=True
            )
            active_jobs = sum(1 for job in jobs if job.status == "running")
            return SeedStatusResponse(
                active_jobs=active_jobs,
                total_signals_sent=self._total_signals_sent,
                jobs=[
                    SeedJobView(
                        job_id=job.job_id,
                        mode=job.mode,
                        requested_count=job.requested_count,
                        sent_count=job.sent_count,
                        rate=job.rate,
                        status=job.status,
                        started_at=job.started_at,
                        finished_at=job.finished_at,
                        error=job.error,
                    )
                    for job in jobs
                ],
            )
