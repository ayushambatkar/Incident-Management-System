# Incident Management System Backend

A production-oriented IMS backend built with FastAPI, Redis Streams, PostgreSQL, and MongoDB.

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

3. API base URL: `http://localhost:8000`

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
