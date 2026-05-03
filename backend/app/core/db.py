from __future__ import annotations

from dataclasses import dataclass

import asyncpg

from app.core.time import utc_now

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS incidents (
    id BIGSERIAL PRIMARY KEY,
    component_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('P0', 'P1', 'P2', 'P3')),
    state TEXT NOT NULL CHECK (state IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_incidents_state_severity ON incidents (state, severity, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_component_state ON incidents (component_id, state);

CREATE TABLE IF NOT EXISTS rca (
    work_item_id BIGINT PRIMARY KEY REFERENCES incidents(id) ON DELETE CASCADE,
    root_cause TEXT NOT NULL,
    fix TEXT NOT NULL,
    prevention TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION ensure_closed_has_rca() RETURNS trigger AS $$
BEGIN
    IF NEW.state = 'CLOSED' AND NOT EXISTS (SELECT 1 FROM rca WHERE work_item_id = NEW.id) THEN
        RAISE EXCEPTION 'cannot close incident without RCA';
    END IF;

    IF NEW.state = 'CLOSED' AND NEW.end_time IS NULL THEN
        NEW.end_time := now();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_incidents_closed_has_rca ON incidents;
CREATE TRIGGER trg_incidents_closed_has_rca
BEFORE UPDATE OF state ON incidents
FOR EACH ROW EXECUTE FUNCTION ensure_closed_has_rca();
"""


@dataclass(slots=True)
class PostgresStore:
    dsn: str
    pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=20)
            assert self.pool is not None
            async with self.pool.acquire() as conn:
                await conn.execute(SCHEMA_SQL)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    async def fetch(self, query: str, *args):
        assert self.pool is not None
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        assert self.pool is not None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        assert self.pool is not None
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args):
        assert self.pool is not None
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
