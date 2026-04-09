# Build Path Review (April 9, 2026)

## Current State
- Backend has working FastAPI endpoints for residents, drivers, vehicles, locations, and trips.
- The trip workflow already validates references and checks assignment conflicts.
- Frontend is currently a connectivity shell (health check + static module list).

## Gaps on the Critical Path
1. No authentication/authorization yet (high priority before operational rollout).
2. No automated test suite for API behavior and scheduling rules.
3. Frontend is not yet connected to live scheduling data beyond `/health`.
4. Driver/vehicle API contracts were inconsistent with other resources (model objects were used directly as request payloads).

## Immediate Upgrade Applied
Standardized driver/vehicle API contracts to use explicit `Create`/`Read` schemas and added basic capacity validation for vehicle inputs.

## Proposed Next Logical Change
**Build a thin scheduling board in the frontend backed by `GET /trips/schedule/day` (or equivalent day schedule endpoint) and role-gate write actions.**

Why this is next:
- It converts existing backend scheduling logic into real operator value.
- It validates API shape and data quality with real UI usage.
- It sets up the right place to integrate authentication/roles right after.

## Acceptance Criteria for Next Change
- Frontend can fetch and render a day schedule grouped by driver.
- Basic filters: date + status.
- Read-only mode available to non-dispatch users.
- Loading/error/empty states implemented.
- End-to-end smoke check documented.
