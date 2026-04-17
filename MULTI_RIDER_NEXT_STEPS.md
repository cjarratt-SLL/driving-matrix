# Multi-Rider Development Next Steps (April 17, 2026)

## Current backend reality (what exists today)

1. **Trips are one resident per row**
   - The `Trip` model has a single `resident_id` field and no join table for multiple riders. This structurally limits every trip to one rider even when vehicles have extra capacity.  
2. **Assignment logic is conflict-prevention only**
   - The backend currently checks whether a selected driver/vehicle overlaps in time with another trip and rejects conflicts. It does not auto-assign riders, drivers, or vehicles.  
3. **Vehicle capacity exists but is not used in scheduling decisions**
   - `Vehicle.capacity` is modeled, but no scheduling endpoint uses capacity to pack multiple residents into shared trips.  
4. **Route estimate is deterministic fallback logic**
   - Distance and duration estimation is a deterministic in-process estimator based on coordinates, not a true road routing provider.  
5. **Frontend supports basic CRUD and trip creation**
   - The UI can create standalone trips but does not expose a batching/optimization workflow for dispatch.

## Gaps blocking shared-trip optimization

- No data model for many-to-one relationship between residents and an operational trip run.
- No availability model for drivers/vehicles beyond overlap checks (e.g., shift windows, breaks, out-of-service periods).
- No assignment service that evaluates compatibility across destination, pickup windows, travel time, and capacity.
- No optimization endpoint (e.g., "propose schedule for date").
- No UI workflow for reviewing/approving algorithmic assignments.

## Recommended development sequence

### Phase 1 — Data model foundation (must-do first)

1. **Separate "trip request" from "vehicle run"**
   - Introduce `TripRequest` (one resident request) with:
     - resident_id
     - earliest_pickup / latest_pickup (or scheduled window)
     - pickup/dropoff location
     - service constraints (mobility, wheelchair requirement, etc.)
     - status lifecycle (`pending`, `scheduled`, `in_progress`, `completed`, `cancelled`)
2. **Add "Run" (shared ride) entity**
   - Introduce `TripRun` with:
     - driver_id (nullable until assignment)
     - vehicle_id (nullable until assignment)
     - planned_start/planned_end
     - run_status
3. **Add join table between run and requests**
   - `RunStop` or `RunAssignment` to map many requests to one run.
   - Include stop order and per-rider planned pickup/dropoff times.
4. **Normalize availability and constraints**
   - Add driver availability windows and vehicle availability windows.
   - Add vehicle capabilities (wheelchair, seating type) as explicit constraints for matching.

### Phase 2 — Scheduling domain logic

1. **Build a candidate grouping engine**
   - Group requests by:
     - destination proximity (same/nearby dropoff)
     - compatible time windows
     - estimated detour tolerance
2. **Add a feasibility checker**
   - For each candidate run, enforce:
     - vehicle capacity
     - driver availability window
     - vehicle availability window
     - max ride duration increase per resident
3. **Add objective scoring**
   - Score feasible options with weighted factors:
     - total miles/minutes
     - on-time reliability
     - number of residents served per run
     - dispatch fairness / load balancing across drivers
4. **Produce assignment proposal output**
   - Return a deterministic proposal payload (`runs`, `unassigned_requests`, and `reasons`).

### Phase 3 — API additions for dispatch workflow

1. **Create planning endpoints**
   - `POST /planning/generate` for a day/time window.
   - `GET /planning/{plan_id}` to inspect grouped runs and constraints.
   - `POST /planning/{plan_id}/commit` to write accepted runs into operational tables.
2. **Add explainability in responses**
   - Include why residents were grouped and why requests were unassigned.
3. **Support partial manual overrides**
   - Allow dispatcher to pin a resident/driver/vehicle and re-run optimization around those locks.

### Phase 4 — Frontend dispatch board evolution

1. Build a schedule board by date with grouped runs (driver and vehicle lanes).
2. Show capacity utilization per run and conflict warnings.
3. Add planner actions:
   - Generate plan
   - Accept/reject individual run
   - Commit approved plan
4. Add "what changed" diff between current schedule and proposed schedule.

### Phase 5 — Reliability, performance, and governance

1. **Testing**
   - Unit tests for grouping/scoring/feasibility logic.
   - Scenario tests for edge cases (capacity full, no driver available, route estimate unavailable).
   - Contract tests for planning endpoints.
2. **Operational safeguards**
   - Idempotent plan generation keys.
   - Soft locks for dispatcher editing collisions.
   - Audit log of assignment decisions and manual overrides.
3. **Metrics**
   - Fill rate, average ride-share occupancy, unassigned count, and on-time performance.

## Suggested first implementation milestone (2–3 sprints)

Deliver a **"shared-run v1"** that can:
- accept trip requests,
- group requests with same destination within a configurable pickup window,
- assign to first available eligible vehicle/driver,
- enforce capacity and no-overlap constraints,
- and persist dispatcher-approved run plans.

That milestone is intentionally simple but unlocks real multi-rider scheduling and gives a practical base for later optimization sophistication.
