from datetime import datetime

from sqlmodel import select

from app.models.dispatch_models import TripRequest, TripRequestStatus, TripRun, TripRunStatus
from app.models.driver_models import DriverAvailabilityWindow
from app.models.location_models import Location
from app.models.vehicle_models import VehicleAvailabilityWindow
from app.services.planning_engine import (
    PlanningHeuristics,
    PlanningScoreWeights,
    _score_metrics,
    build_planning_proposal,
    group_requests_by_destination_and_window,
    load_pending_trip_requests,
)


def _request(
    request_id: int,
    resident_id: int,
    pickup_location_id: int,
    dropoff_location_id: int,
    pickup_window_start: datetime,
    pickup_window_end: datetime,
) -> TripRequest:
    return TripRequest(
        id=request_id,
        resident_id=resident_id,
        pickup_location_id=pickup_location_id,
        dropoff_location_id=dropoff_location_id,
        pickup_window_start=pickup_window_start,
        pickup_window_end=pickup_window_end,
        status=TripRequestStatus.PENDING,
    )


def test_build_planning_proposal_assigns_compatible_requests(session):
    session.add_all(
        [
            DriverAvailabilityWindow(driver_id=1, start_time=datetime(2026, 4, 20, 8, 0), end_time=datetime(2026, 4, 20, 12, 0)),
            DriverAvailabilityWindow(driver_id=2, start_time=datetime(2026, 4, 20, 8, 0), end_time=datetime(2026, 4, 20, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=1, start_time=datetime(2026, 4, 20, 8, 0), end_time=datetime(2026, 4, 20, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=2, start_time=datetime(2026, 4, 20, 8, 0), end_time=datetime(2026, 4, 20, 12, 0)),
            _request(101, 1, 1, 2, datetime(2026, 4, 20, 9, 0), datetime(2026, 4, 20, 9, 20)),
            _request(102, 2, 3, 2, datetime(2026, 4, 20, 9, 5), datetime(2026, 4, 20, 9, 25)),
            _request(103, 3, 1, 4, datetime(2026, 4, 20, 11, 0), datetime(2026, 4, 20, 11, 15)),
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
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=10, max_detour_meters=4_000, max_occupancy=4),
    )

    assert len(proposal.runs) == 2
    assert proposal.runs[0]["request_ids"] == [101, 102]
    assert proposal.runs[0]["driver_id"] == 2
    assert proposal.runs[0]["vehicle_id"] == 2
    assert proposal.runs[1]["request_ids"] == [103]
    assert proposal.runs[1]["driver_id"] == 1
    assert proposal.runs[1]["vehicle_id"] == 2
    assert proposal.unassigned_requests == []
    assert proposal.reasons == {}


def test_build_planning_proposal_chunks_group_by_max_occupancy(session):
    session.add_all(
        [
            DriverAvailabilityWindow(driver_id=1, start_time=datetime(2026, 4, 22, 8, 0), end_time=datetime(2026, 4, 22, 12, 0)),
            DriverAvailabilityWindow(driver_id=2, start_time=datetime(2026, 4, 22, 8, 0), end_time=datetime(2026, 4, 22, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=1, start_time=datetime(2026, 4, 22, 8, 0), end_time=datetime(2026, 4, 22, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=2, start_time=datetime(2026, 4, 22, 8, 0), end_time=datetime(2026, 4, 22, 12, 0)),
            _request(301, 1, 1, 2, datetime(2026, 4, 22, 9, 0), datetime(2026, 4, 22, 9, 20)),
            _request(302, 2, 3, 2, datetime(2026, 4, 22, 9, 1), datetime(2026, 4, 22, 9, 21)),
            _request(303, 3, 1, 2, datetime(2026, 4, 22, 9, 2), datetime(2026, 4, 22, 9, 22)),
            _request(304, 1, 3, 2, datetime(2026, 4, 22, 9, 3), datetime(2026, 4, 22, 9, 23)),
            _request(305, 2, 1, 2, datetime(2026, 4, 22, 9, 4), datetime(2026, 4, 22, 9, 24)),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 22, 8, 0),
        window_end=datetime(2026, 4, 22, 12, 0),
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=10, max_detour_meters=4_000, max_occupancy=3),
    )

    assert len(proposal.runs) == 2
    assert sorted(len(run["request_ids"]) for run in proposal.runs) == [2, 3]

    assigned_request_ids = sorted(request_id for run in proposal.runs for request_id in run["request_ids"])
    assert assigned_request_ids == [301, 302, 303, 304, 305]

    run_resources = {(run["driver_id"], run["vehicle_id"]) for run in proposal.runs}
    assert len(run_resources) == 2
    assert proposal.unassigned_requests == []


def test_build_planning_proposal_marks_unassigned_requests_with_reasons(session):
    session.add_all(
        [
            DriverAvailabilityWindow(driver_id=1, start_time=datetime(2026, 4, 21, 8, 0), end_time=datetime(2026, 4, 21, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=2, start_time=datetime(2026, 4, 21, 8, 0), end_time=datetime(2026, 4, 21, 9, 10)),
            _request(201, 1, 1, 2, datetime(2026, 4, 21, 9, 0), datetime(2026, 4, 21, 9, 30)),
            _request(202, 2, 3, 2, datetime(2026, 4, 21, 9, 5), datetime(2026, 4, 21, 9, 35)),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 21, 8, 0),
        window_end=datetime(2026, 4, 21, 12, 0),
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=10, max_detour_meters=4_000, max_occupancy=4),
    )

    assert proposal.runs == []
    assert proposal.unassigned_requests == [201, 202]
    assert proposal.reasons == {201: ["vehicle_unavailable_or_capacity"], 202: ["vehicle_unavailable_or_capacity"]}


def test_build_planning_proposal_marks_unassigned_requests_with_generic_reason(session):
    session.add_all(
        [
            _request(401, 1, 1, 2, datetime(2026, 4, 23, 9, 0), datetime(2026, 4, 23, 9, 20)),
            _request(402, 2, 3, 2, datetime(2026, 4, 23, 9, 2), datetime(2026, 4, 23, 9, 22)),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 23, 8, 0),
        window_end=datetime(2026, 4, 23, 12, 0),
    )

    assert proposal.runs == []
    assert proposal.unassigned_requests == [401, 402]
    assert proposal.reasons == {401: ["unassigned"], 402: ["unassigned"]}


def test_build_planning_proposal_marks_unassigned_when_all_resources_blocked_by_committed_runs(session):
    session.add_all(
        [
            DriverAvailabilityWindow(driver_id=1, start_time=datetime(2026, 4, 24, 8, 0), end_time=datetime(2026, 4, 24, 12, 0)),
            DriverAvailabilityWindow(driver_id=2, start_time=datetime(2026, 4, 24, 8, 0), end_time=datetime(2026, 4, 24, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=1, start_time=datetime(2026, 4, 24, 8, 0), end_time=datetime(2026, 4, 24, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=2, start_time=datetime(2026, 4, 24, 8, 0), end_time=datetime(2026, 4, 24, 12, 0)),
            TripRun(
                window_start=datetime(2026, 4, 24, 9, 0),
                window_end=datetime(2026, 4, 24, 10, 0),
                driver_id=1,
                vehicle_id=1,
                status=TripRunStatus.PLANNED,
            ),
            TripRun(
                window_start=datetime(2026, 4, 24, 9, 0),
                window_end=datetime(2026, 4, 24, 10, 0),
                driver_id=2,
                vehicle_id=2,
                status=TripRunStatus.ACTIVE,
            ),
            _request(501, 1, 1, 2, datetime(2026, 4, 24, 9, 5), datetime(2026, 4, 24, 9, 25)),
            _request(502, 2, 3, 2, datetime(2026, 4, 24, 9, 8), datetime(2026, 4, 24, 9, 28)),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 24, 8, 0),
        window_end=datetime(2026, 4, 24, 12, 0),
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=10, max_detour_meters=4_000, max_occupancy=4),
    )

    assert proposal.runs == []
    assert proposal.unassigned_requests == [501, 502]
    assert proposal.reasons == {501: ["driver_unavailable"], 502: ["driver_unavailable"]}


def test_grouping_sensitive_to_pickup_tolerance_and_max_detour(session):
    location_5 = Location(
        id=5,
        name="Near Clinic",
        address="910 Health Dr",
        latitude=37.7844,
        longitude=-122.409,
        location_type="facility",
    )
    session.add(location_5)
    session.add_all(
        [
            _request(601, 1, 1, 2, datetime(2026, 4, 25, 9, 0), datetime(2026, 4, 25, 9, 5)),
            _request(602, 2, 3, 5, datetime(2026, 4, 25, 9, 14), datetime(2026, 4, 25, 9, 19)),
        ]
    )
    session.commit()

    pending_requests = load_pending_trip_requests(
        session,
        window_start=datetime(2026, 4, 25, 8, 0),
        window_end=datetime(2026, 4, 25, 12, 0),
    )
    location_by_id = {
        location.id: location
        for location in session.exec(select(Location).where(Location.id.in_([2, 5]))).all()
        if location.id is not None
    }

    loose_groups = group_requests_by_destination_and_window(
        pending_requests,
        location_by_id=location_by_id,
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=10, max_detour_meters=100, max_occupancy=4),
    )
    tight_detour_groups = group_requests_by_destination_and_window(
        pending_requests,
        location_by_id=location_by_id,
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=10, max_detour_meters=20, max_occupancy=4),
    )
    tight_tolerance_groups = group_requests_by_destination_and_window(
        pending_requests,
        location_by_id=location_by_id,
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=2, max_detour_meters=100, max_occupancy=4),
    )

    assert [group.request_ids for group in loose_groups] == [[601, 602]]
    assert [group.request_ids for group in tight_detour_groups] == [[601], [602]]
    assert [group.request_ids for group in tight_tolerance_groups] == [[601], [602]]


def test_build_planning_proposal_includes_weighted_score_metrics(session):
    session.add_all(
        [
            DriverAvailabilityWindow(driver_id=1, start_time=datetime(2026, 4, 26, 8, 0), end_time=datetime(2026, 4, 26, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=1, start_time=datetime(2026, 4, 26, 8, 0), end_time=datetime(2026, 4, 26, 12, 0)),
            _request(701, 1, 1, 2, datetime(2026, 4, 26, 9, 0), datetime(2026, 4, 26, 9, 20)),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 26, 8, 0),
        window_end=datetime(2026, 4, 26, 12, 0),
        score_weights=PlanningScoreWeights(
            total_minutes=-1.0,
            total_miles=-1.0,
            on_time_reliability=5.0,
            riders_served=2.0,
            load_balance=0.0,
            capacity_utilization=3.0,
            empty_seat_penalty=-1.5,
        ),
    )

    assert len(proposal.runs) == 1
    run = proposal.runs[0]
    assert set(run["score_metrics"]) == {
        "total_minutes",
        "total_miles",
        "on_time_reliability",
        "riders_served",
        "load_balance",
        "capacity_utilization",
        "empty_seat_penalty",
    }
    assert isinstance(run["score"], float)


def test_build_planning_proposal_uses_deterministic_tie_breaking(session):
    session.add_all(
        [
            DriverAvailabilityWindow(driver_id=1, start_time=datetime(2026, 4, 27, 8, 0), end_time=datetime(2026, 4, 27, 12, 0)),
            DriverAvailabilityWindow(driver_id=2, start_time=datetime(2026, 4, 27, 8, 0), end_time=datetime(2026, 4, 27, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=1, start_time=datetime(2026, 4, 27, 8, 0), end_time=datetime(2026, 4, 27, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=2, start_time=datetime(2026, 4, 27, 8, 0), end_time=datetime(2026, 4, 27, 12, 0)),
            _request(801, 1, 1, 2, datetime(2026, 4, 27, 9, 0), datetime(2026, 4, 27, 9, 15)),
            _request(802, 2, 3, 2, datetime(2026, 4, 27, 9, 0), datetime(2026, 4, 27, 9, 15)),
        ]
    )
    session.commit()

    first = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 27, 8, 0),
        window_end=datetime(2026, 4, 27, 12, 0),
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=0, max_detour_meters=1, max_occupancy=1),
        score_weights=PlanningScoreWeights(
            total_minutes=-1.0,
            total_miles=0.0,
            on_time_reliability=0.0,
            riders_served=0.0,
            load_balance=0.0,
            capacity_utilization=0.0,
            empty_seat_penalty=0.0,
        ),
    )
    second = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 27, 8, 0),
        window_end=datetime(2026, 4, 27, 12, 0),
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=0, max_detour_meters=1, max_occupancy=1),
        score_weights=PlanningScoreWeights(
            total_minutes=-1.0,
            total_miles=0.0,
            on_time_reliability=0.0,
            riders_served=0.0,
            load_balance=0.0,
            capacity_utilization=0.0,
            empty_seat_penalty=0.0,
        ),
    )

    assert first.runs == second.runs
    assert [(run["driver_id"], run["vehicle_id"], run["request_ids"]) for run in first.runs] == [
        (1, 1, [801]),
        (2, 2, [802]),
    ]


def test_build_planning_proposal_prefers_higher_capacity_utilization_vehicle(session):
    session.add_all(
        [
            DriverAvailabilityWindow(driver_id=1, start_time=datetime(2026, 4, 28, 8, 0), end_time=datetime(2026, 4, 28, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=1, start_time=datetime(2026, 4, 28, 8, 0), end_time=datetime(2026, 4, 28, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=2, start_time=datetime(2026, 4, 28, 8, 0), end_time=datetime(2026, 4, 28, 12, 0)),
            _request(901, 1, 1, 2, datetime(2026, 4, 28, 9, 0), datetime(2026, 4, 28, 9, 20)),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 28, 8, 0),
        window_end=datetime(2026, 4, 28, 12, 0),
        score_weights=PlanningScoreWeights(
            total_minutes=0.0,
            total_miles=0.0,
            on_time_reliability=0.0,
            riders_served=0.0,
            load_balance=0.0,
            capacity_utilization=20.0,
            empty_seat_penalty=0.0,
        ),
    )

    assert len(proposal.runs) == 1
    run = proposal.runs[0]
    assert run["vehicle_id"] == 2
    assert run["score_metrics"]["capacity_utilization"] > 0.3


def test_score_metrics_load_balance_is_bounded_between_zero_and_one():
    request = _request(1001, 1, 1, 2, datetime(2026, 4, 29, 9, 0), datetime(2026, 4, 29, 9, 10))

    heavily_loaded_metrics = _score_metrics(
        request_slice=[request.id],
        requests_by_id={request.id: request},
        location_by_id={},
        driver_assigned_run_counts={1: 100, 2: 0},
        max_assigned_run_count=100,
        driver_id=1,
        vehicle_id=1,
        vehicle_capacity=4,
    )
    lightly_loaded_metrics = _score_metrics(
        request_slice=[request.id],
        requests_by_id={request.id: request},
        location_by_id={},
        driver_assigned_run_counts={1: 100, 2: 0},
        max_assigned_run_count=100,
        driver_id=2,
        vehicle_id=1,
        vehicle_capacity=4,
    )

    assert 0.0 <= heavily_loaded_metrics["load_balance"] <= 1.0
    assert 0.0 <= lightly_loaded_metrics["load_balance"] <= 1.0


def test_score_metrics_load_balance_is_maximal_when_all_drivers_have_zero_runs():
    request = _request(1002, 1, 1, 2, datetime(2026, 4, 29, 9, 0), datetime(2026, 4, 29, 9, 10))

    zero_load_metrics_driver_1 = _score_metrics(
        request_slice=[request.id],
        requests_by_id={request.id: request},
        location_by_id={},
        driver_assigned_run_counts={1: 0, 2: 0},
        max_assigned_run_count=0,
        driver_id=1,
        vehicle_id=1,
        vehicle_capacity=4,
    )
    zero_load_metrics_driver_2 = _score_metrics(
        request_slice=[request.id],
        requests_by_id={request.id: request},
        location_by_id={},
        driver_assigned_run_counts={1: 0, 2: 0},
        max_assigned_run_count=0,
        driver_id=2,
        vehicle_id=1,
        vehicle_capacity=4,
    )

    assert zero_load_metrics_driver_1["load_balance"] == 1.0
    assert zero_load_metrics_driver_2["load_balance"] == 1.0


def test_build_planning_proposal_repeated_assignments_do_not_produce_negative_load_balance(session):
    session.add_all(
        [
            DriverAvailabilityWindow(driver_id=1, start_time=datetime(2026, 4, 29, 8, 0), end_time=datetime(2026, 4, 29, 12, 0)),
            VehicleAvailabilityWindow(vehicle_id=1, start_time=datetime(2026, 4, 29, 8, 0), end_time=datetime(2026, 4, 29, 12, 0)),
            _request(1101, 1, 1, 2, datetime(2026, 4, 29, 9, 0), datetime(2026, 4, 29, 9, 10)),
            _request(1102, 2, 3, 2, datetime(2026, 4, 29, 9, 15), datetime(2026, 4, 29, 9, 25)),
            _request(1103, 3, 1, 2, datetime(2026, 4, 29, 9, 30), datetime(2026, 4, 29, 9, 40)),
        ]
    )
    session.commit()

    proposal = build_planning_proposal(
        session,
        window_start=datetime(2026, 4, 29, 8, 0),
        window_end=datetime(2026, 4, 29, 12, 0),
        heuristics=PlanningHeuristics(pickup_window_tolerance_minutes=0, max_detour_meters=1, max_occupancy=1),
        score_weights=PlanningScoreWeights(
            total_minutes=0.0,
            total_miles=0.0,
            on_time_reliability=0.0,
            riders_served=0.0,
            load_balance=1.0,
            capacity_utilization=0.0,
            empty_seat_penalty=0.0,
        ),
    )

    assert len(proposal.runs) == 3
    assert all(run["score_metrics"]["load_balance"] >= 0.0 for run in proposal.runs)
    assert all(run["score_metrics"]["load_balance"] <= 1.0 for run in proposal.runs)


def test_score_metrics_load_balance_prefers_less_loaded_drivers():
    request = _request(1201, 1, 1, 2, datetime(2026, 4, 30, 9, 0), datetime(2026, 4, 30, 9, 10))

    overloaded_metrics = _score_metrics(
        request_slice=[request.id],
        requests_by_id={request.id: request},
        location_by_id={},
        driver_assigned_run_counts={1: 3, 2: 1},
        max_assigned_run_count=3,
        driver_id=1,
        vehicle_id=1,
        vehicle_capacity=4,
    )
    underloaded_metrics = _score_metrics(
        request_slice=[request.id],
        requests_by_id={request.id: request},
        location_by_id={},
        driver_assigned_run_counts={1: 3, 2: 1},
        max_assigned_run_count=3,
        driver_id=2,
        vehicle_id=1,
        vehicle_capacity=4,
    )

    assert underloaded_metrics["load_balance"] > overloaded_metrics["load_balance"]
