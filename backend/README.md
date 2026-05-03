# Incident Management System Backend

A production-oriented IMS stack built with FastAPI, Redis Streams, PostgreSQL, MongoDB, and a React/Vite frontend.

## Architecture

- `routers/` exposes HTTP endpoints and keeps orchestration thin.
- `services/` contains business logic and workflow coordination.
- `repositories/` contains persistence and cache adapters.
- `models/` contains domain objects, enums, state pattern classes, and alert strategies.
- `workers/` consumes the Redis Stream and performs async processing.
- `core/` centralizes configuration and infrastructure clients.

## Features

- Async FastAPI ingestion API with validation and rate limiting.
- Non-blocking queueing using Redis Streams.
- Debounce-based incident creation.
- PostgreSQL source of truth for incidents and RCA.
- MongoDB storage for raw signals.
- Redis caching for active incidents and dashboard reads.
- State pattern for incident lifecycle rules.
- Strategy pattern for alerting by severity.
- Health endpoint and operational metrics.

## Run locally

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Start the stack:

```bash
docker compose up --build
```

3. Frontend: `http://localhost:5173`
4. API base URL: `http://localhost:8000`

## Endpoints

- `POST /signal`
- `GET /incidents`
- `GET /incident/{id}`
- `PUT /incident/{id}/state`
- `POST /incident/{id}/rca`
- `GET /health`

## Signal flow

1. Ingestion API validates the payload.
2. Redis rate limiting checks burst behavior.
3. Event is pushed to Redis Streams immediately.
4. Worker consumes the stream.
5. Worker stores the raw signal in MongoDB.
6. Worker applies debounce logic using Redis.
7. First signal creates a PostgreSQL incident.
8. Subsequent signals attach to the existing incident.
9. Redis dashboard cache is refreshed.

## Notes

- The queue absorbs load if PostgreSQL or MongoDB slows down.
- `CLOSED` transitions are blocked unless an RCA exists.
- MTTR is computed from `end_time - start_time` when RCA is stored or the incident is closed.

## Architecture Diagram

```mermaid
flowchart LR
	subgraph Ingestion
		A[Clients / Agents] -->|HTTP POST /signal| API[FastAPI Ingestion]
		API --> RedisStream[Redis Streams]
	end

	subgraph Processing
		RedisStream --> Worker[Async Worker (Redis consumer)]
		Worker --> Mongo[MongoDB (raw signals, audit)]
		Worker --> Postgres[PostgreSQL (incidents & RCA)]
		Worker --> RedisCache[Redis (active incidents cache)]
	end

	subgraph Frontend
		RedisCache --> UI[React Dashboard]
		UI -->|RCA / State| API
	end

	click Mongo "https://www.mongodb.com/" "MongoDB"
	click RedisStream "https://redis.io/" "Redis Streams"
	click Postgres "https://www.postgresql.org/" "Postgres"
```

## Backpressure & Resilience

- Ingestion is non-blocking: `/signal` immediately enqueues into Redis Streams so the API thread never waits on DB I/O.
- Redis Streams act as a durable buffer. If Mongo/Postgres are slow, the worker can consume at its own pace; the stream retains messages until acknowledged.
- Worker reads in configurable batches (`queue_read_count`) and blocks (`queue_block_ms`) to control memory and I/O pressure.
- Debounce is implemented in Redis (`debounce_ttl_seconds`): concurrent signals for the same `component_id` are coalesced into one Work Item. This prevents incident-store storming.
- Rate limiting at the API layer (sliding-window using Redis) prevents cascade overload from noisy sources.

## Seeding & Sample Data

Use the built-in seeder endpoints to generate load that flows through the queue and worker (recommended):

```
# generate 100 signals in burst mode
curl "http://localhost:8000/seed?count=100&mode=burst"

# check status
curl "http://localhost:8000/seed/status"
```

Or run the included script to simulate an RDBMS outage (posts multiple P0 signals):

```
python scripts/simulate_rdbms_outage.py --count 200 --rate 200
```

## Prompts, Specs & Plans

- All design notes, prompts used to scaffold this repo, and plan artifacts are checked into the repository under `docs/` and `prompts/` (see repo root).

