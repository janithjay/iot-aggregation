# IoT Aggregation Starter

This repository is scaffolded for a 5-member team with separated roles:

1. Lead/Integrator + Worker/Processor Developer
2. Backend Developer
3. API Developer
4. Database Administrator
5. Frontend/DevOps

## Structure

- api/: REST endpoints
- backend/: business logic layer
- db/: schema and database access layer
- worker/: queue consumer and processing
- frontend/: simple browser UI
- shared/: shared project configuration
- tests/: baseline test files

## Quick Start (local)

1. Build and run with Docker Compose:
   - docker compose up --build
2. Open API health endpoint:
   - http://localhost:5000/health

## Notes

This is a starter scaffold. Replace stubs with full implementations as each role progresses.

## Worker/Processor Scope (Implemented)

- Worker consumes jobs from RabbitMQ queue `iot-jobs`.
- Worker transitions DB status: `pending -> processing -> done|failed`.
- Worker computes summaries from sensor values and writes them to DB.
- Worker retries failed jobs up to `MAX_JOB_RETRIES` before marking failed.

## Lead/Integrator Scope (Implemented)

- Integrated API ingestion with queue publishing for background processing.
- Added worker-focused unit tests in `tests/test_worker.py`.
- Added integration smoke script in `scripts/integration_smoke.ps1`.
- Standardized shared env defaults and compose wiring for queue + DB integration.

## Integration Validation Flow

1. Start stack:
   - `docker compose up --build -d`
2. Run integration smoke:
   - `powershell -ExecutionPolicy Bypass -File scripts/integration_smoke.ps1`
3. Optional: run tests
   - `pytest -q`
