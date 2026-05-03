from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.db import PostgresStore
from app.domain.enums import IncidentState, Severity
from app.domain.models import Incident, RCA
from app.repositories.interfaces import IncidentRepository, RCARepository

_SEVERITY_ORDER = {Severity.P0: 0, Severity.P1: 1, Severity.P2: 2, Severity.P3: 3}


class PostgresIncidentRepository(IncidentRepository):
    def __init__(self, store: PostgresStore) -> None:
        self.store = store

    @staticmethod
    def _to_incident(row) -> Incident:
        return Incident(
            id=int(row["id"]),
            component_id=row["component_id"],
            severity=Severity(row["severity"]),
            state=IncidentState(row["state"]),
            start_time=row["start_time"],
            end_time=row["end_time"],
        )

    async def create(
        self, component_id: str, severity: Severity, start_time: datetime
    ) -> Incident:
        row = await self.store.fetchrow(
            """
            INSERT INTO incidents (component_id, severity, state, start_time)
            VALUES ($1, $2, $3, $4)
            RETURNING *
            """,
            component_id,
            severity.value,
            IncidentState.OPEN.value,
            start_time,
        )
        return self._to_incident(row)

    async def get(self, incident_id: int) -> Incident | None:
        row = await self.store.fetchrow(
            "SELECT * FROM incidents WHERE id = $1", incident_id
        )
        return self._to_incident(row) if row else None

    async def list_active(self) -> list[Incident]:
        rows = await self.store.fetch("""
            SELECT *
            FROM incidents
            WHERE state <> 'CLOSED'
            ORDER BY
                CASE severity
                    WHEN 'P0' THEN 0
                    WHEN 'P1' THEN 1
                    WHEN 'P2' THEN 2
                    ELSE 3
                END,
                start_time DESC
            """)
        return [self._to_incident(row) for row in rows]

    async def update_state(
        self, incident_id: int, state: IncidentState, end_time: datetime | None = None
    ) -> Incident:
        row = await self.store.fetchrow(
            """
            UPDATE incidents
            SET state = $2,
                end_time = CASE
                    WHEN $2 = 'CLOSED' THEN COALESCE(end_time, $3)
                    ELSE end_time
                END
            WHERE id = $1
            RETURNING *
            """,
            incident_id,
            state.value,
            end_time,
        )
        return self._to_incident(row)

    async def update_severity(self, incident_id: int, severity: Severity) -> Incident:
        row = await self.store.fetchrow(
            """
            UPDATE incidents
            SET severity = $2
            WHERE id = $1
            RETURNING *
            """,
            incident_id,
            severity.value,
        )
        return self._to_incident(row)

    async def incident_has_rca(self, incident_id: int) -> bool:
        value = await self.store.fetchval(
            "SELECT EXISTS (SELECT 1 FROM rca WHERE work_item_id = $1)", incident_id
        )
        return bool(value)


class PostgresRCARepository(RCARepository):
    def __init__(self, store: PostgresStore) -> None:
        self.store = store

    @staticmethod
    def _to_rca(row) -> RCA:
        return RCA(
            work_item_id=int(row["work_item_id"]),
            root_cause=row["root_cause"],
            fix=row["fix"],
            prevention=row["prevention"],
        )

    async def upsert(
        self, work_item_id: int, root_cause: str, fix: str, prevention: str
    ) -> RCA:
        row = await self.store.fetchrow(
            """
            INSERT INTO rca (work_item_id, root_cause, fix, prevention)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (work_item_id)
            DO UPDATE SET
                root_cause = EXCLUDED.root_cause,
                fix = EXCLUDED.fix,
                prevention = EXCLUDED.prevention
            RETURNING *
            """,
            work_item_id,
            root_cause,
            fix,
            prevention,
        )
        return self._to_rca(row)

    async def get(self, work_item_id: int) -> RCA | None:
        row = await self.store.fetchrow(
            "SELECT * FROM rca WHERE work_item_id = $1", work_item_id
        )
        return self._to_rca(row) if row else None
