from datetime import datetime

from app.models.dispatch_models import TripRequest, TripRequestStatus, TripRun, TripRunStatus
from app.models.driver_models import DriverAvailabilityWindow
from app.models.vehicle_models import VehicleAvailabilityWindow
from app.services.planning_engine import PlanningHeuristics, build_planning_proposal


def test_build_planning_proposal_assigns_compatible_requests(session):
    session.add_all(
        [
            DriverAvailabilityWindow(
                driver_id=1,
                start_time=datetime(2026, 4, 20, 8, 0),
                end_time=datetime(2026, 4, 20, 12, 0),
            ),
            DriverAvailabilityWindow(
                driver_id=2,
                start_time=datetime(2026, 4, 20, 8, 0),
                end_time=datetime(2026, 4, 20, 12, 0),
            ),
            VehicleAvailabilityWindow(
                vehicle_id=1,
                start_time=datetime(2026, 4, 20, 8, 0),
                end_time=datetime(2026, 4, 20, 12, 0),
            ),
            VehicleAvailabilityWindow(
                vehicle_id=2,
                start_time=datetime(2026, 4, 20, 8, 0),
                end_time=datetime(2026, 4, 20, 12, 0),
            ),
            TripRequest(
                id=101,
                resident_id=1,
                pickup_location_id=1,
                dropoff_location_id=2,
                pickup_window_start=datetime(2026, 4, 20, 9, 0),
                pickup_window_end=datetime(2026, 4, 20, 9, 20),
                status=TripRequestStatus.PENDING,
            ),
            TripRequest(
                id=102,
                resident_id=2,
                pickup_location_id=3,
                dropoff_location_id=2,
                pickup_window_start=datetime(2026, 4, 20, 9, 5),
                pickup_window_end=datetime(2026, 4, 20, 9, 25),
                status=TripRequestStatus.PENDING,
            ),
            TripRequest(
                id=103,
                resident_id=3,
                pickup_location_id=1,
                dropoff_location_id=4,
                pickup_window_start=datetime(2026, 4, 20, 11, 0),
                pickup_window_end=datetime(2026, 4, 20, 11, 15),
                status=TripRequestStatus.PENDING,
            ),
            TripRun(
                window_start=datetime(2026, 4, 20, 9, 0),
                window_end=datetime(2026, 4, 20, 9, 35),
                driver_id=1,
                vehicle_id=1,
                status=TripRunStatus.PLANNED,
            ),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 20, 8, 0),
        window_end=datetime(2026, 4, 20, 12, 0),
        heuristics=PlanningHeuristics(
            pickup_window_tolerance_minutes=10,
            max_detour_meters=4_000,
            max_occupancy=4,
        ),
    )

    assert len(proposal.runs) == 2

    first_run = proposal.runs[0]
    second_run = proposal.runs[1]

    assert first_run["request_ids"] == [101, 102]
    assert first_run["driver_id"] == 2
    assert first_run["vehicle_id"] == 2

    assert second_run["request_ids"] == [103]
    assert second_run["driver_id"] == 1
    assert second_run["vehicle_id"] == 1

    assert proposal.unassigned_requests == []
    assert proposal.reasons == {}


def test_build_planning_proposal_marks_unassigned_requests_with_reasons(session):
    session.add_all(
        [
            DriverAvailabilityWindow(
                driver_id=1,
                start_time=datetime(2026, 4, 21, 8, 0),
                end_time=datetime(2026, 4, 21, 12, 0),
            ),
            VehicleAvailabilityWindow(
                vehicle_id=2,
                start_time=datetime(2026, 4, 21, 8, 0),
                end_time=datetime(2026, 4, 21, 9, 10),
            ),
            TripRequest(
                id=201,
                resident_id=1,
                pickup_location_id=1,
                dropoff_location_id=2,
                pickup_window_start=datetime(2026, 4, 21, 9, 0),
                pickup_window_end=datetime(2026, 4, 21, 9, 30),
                status=TripRequestStatus.PENDING,
            ),
            TripRequest(
                id=202,
                resident_id=2,
                pickup_location_id=3,
                dropoff_location_id=2,
                pickup_window_start=datetime(2026, 4, 21, 9, 5),
                pickup_window_end=datetime(2026, 4, 21, 9, 35),
                status=TripRequestStatus.PENDING,
            ),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 21, 8, 0),
        window_end=datetime(2026, 4, 21, 12, 0),
        heuristics=PlanningHeuristics(
            pickup_window_tolerance_minutes=10,
            max_detour_meters=4_000,
            max_occupancy=4,
        ),
    )

    assert proposal.runs == []
    assert proposal.unassigned_requests == [201, 202]
    assert proposal.reasons == {
        201: ["vehicle_unavailable_or_capacity"],
        202: ["vehicle_unavailable_or_capacity"],
    }
