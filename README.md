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
