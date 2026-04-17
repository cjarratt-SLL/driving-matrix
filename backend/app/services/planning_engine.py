from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select
from sqlalchemy import or_

from app.models.dispatch_models import TripRequest, TripRequestStatus, TripRun, TripRunStatus
from app.models.driver_models import Driver, DriverAvailabilityWindow
from app.models.location_models import Location
from app.models.vehicle_models import Vehicle, VehicleAvailabilityWindow
from app.services.routing_estimates import haversine_distance_meters


@dataclass(frozen=True)
class PlanningHeuristics:
    pickup_window_tolerance_minutes: int = 15
    max_detour_meters: int = 5_000
    max_occupancy: int = 4


@dataclass(frozen=True)
class PlanningRequestGroup:
    request_ids: list[int]
    request_count: int
    pickup_window_start: datetime
    pickup_window_end: datetime
    anchor_dropoff_location_id: int


@dataclass(frozen=True)
class PlanningRunProposal:
    request_ids: list[int]
    pickup_window_start: datetime
    pickup_window_end: datetime
    driver_id: int
    vehicle_id: int


@dataclass(frozen=True)
class PlanningProposal:
    runs: list[dict]
    unassigned_requests: list[int]
    reasons: dict[int, list[str]]


@dataclass
class _MutableGroup:
    anchor_request: TripRequest
    request_ids: list[int] = field(default_factory=list)
    pickup_window_start: Optional[datetime] = None
    pickup_window_end: Optional[datetime] = None


@dataclass(frozen=True)
class _AvailabilityWindow:
    start_time: datetime
    end_time: datetime


def build_planning_proposal(
    session: Session,
    window_start: datetime,
    window_end: datetime,
    heuristics: Optional[PlanningHeuristics] = None,
) -> PlanningProposal:
    heuristics = heuristics or PlanningHeuristics()

    pending_requests = load_pending_trip_requests(session, window_start=window_start, window_end=window_end)
    requests_by_id = {request.id: request for request in pending_requests if request.id is not None}
    location_ids = {
        location_id
        for request in pending_requests
        for location_id in (request.pickup_location_id, request.dropoff_location_id)
    }
    location_by_id = _load_locations_by_id(session, location_ids=location_ids)
    grouped_requests = group_requests_by_destination_and_window(
        pending_requests,
        location_by_id=location_by_id,
        heuristics=heuristics,
    )

    driver_availability = _load_driver_availability(
        session,
        window_start=window_start,
        window_end=window_end,
    )
    vehicle_availability = _load_vehicle_availability(
        session,
        window_start=window_start,
        window_end=window_end,
    )
    committed_driver_windows, committed_vehicle_windows = _load_committed_run_windows(
        session,
        window_start=window_start,
        window_end=window_end,
    )

    proposals: list[PlanningRunProposal] = []
    reasons: dict[int, list[str]] = {}

    for group in grouped_requests:
        for request_slice in _chunk_request_ids(group.request_ids, heuristics.max_occupancy):
            run_window_start = min(
                requests_by_id[request_id].pickup_window_start for request_id in request_slice
            )
            run_window_end = max(
                requests_by_id[request_id].pickup_window_end for request_id in request_slice
            )

            selected_driver_id = _select_driver(
                run_window_start,
                run_window_end,
                driver_availability,
                committed_driver_windows,
            )
            if selected_driver_id is None:
                if driver_availability:
                    _append_reason(reasons, request_slice, "driver_unavailable")
                continue

            required_capacity = len(request_slice)
            selected_vehicle_id = _select_vehicle(
                run_window_start,
                run_window_end,
                required_capacity,
                vehicle_availability,
                committed_vehicle_windows,
            )
            if selected_vehicle_id is None:
                if vehicle_availability:
                    _append_reason(reasons, request_slice, "vehicle_unavailable_or_capacity")
                continue

            committed_driver_windows.setdefault(selected_driver_id, []).append(
                _AvailabilityWindow(start_time=run_window_start, end_time=run_window_end)
            )
            committed_vehicle_windows.setdefault(selected_vehicle_id, []).append(
                _AvailabilityWindow(start_time=run_window_start, end_time=run_window_end)
            )

            proposals.append(
                PlanningRunProposal(
                    request_ids=sorted(request_slice),
                    pickup_window_start=run_window_start,
                    pickup_window_end=run_window_end,
                    driver_id=selected_driver_id,
                    vehicle_id=selected_vehicle_id,
                )
            )

    assigned_request_ids = {request_id for proposal in proposals for request_id in proposal.request_ids}
    pending_request_ids = {request.id for request in pending_requests if request.id is not None}
    unassigned_request_ids = sorted(pending_request_ids - assigned_request_ids)

    for request_id in unassigned_request_ids:
        reasons.setdefault(request_id, ["unassigned"])

    runs_payload = [
        {
            "request_ids": proposal.request_ids,
            "pickup_window_start": proposal.pickup_window_start.isoformat(),
            "pickup_window_end": proposal.pickup_window_end.isoformat(),
            "driver_id": proposal.driver_id,
            "vehicle_id": proposal.vehicle_id,
        }
        for proposal in sorted(
            proposals,
            key=lambda proposal: (proposal.pickup_window_start, proposal.pickup_window_end, proposal.request_ids),
        )
    ]

    return PlanningProposal(
        runs=runs_payload,
        unassigned_requests=unassigned_request_ids,
        reasons={request_id: sorted(set(reason_codes)) for request_id, reason_codes in sorted(reasons.items())},
    )


def load_pending_trip_requests(
    session: Session,
    window_start: datetime,
    window_end: datetime,
) -> list[TripRequest]:
    statement = (
        select(TripRequest)
        .where(TripRequest.status == TripRequestStatus.PENDING)
        .where(TripRequest.pickup_window_start < window_end)
        .where(TripRequest.pickup_window_end > window_start)
        .order_by(TripRequest.pickup_window_start, TripRequest.pickup_window_end, TripRequest.id)
    )
    return list(session.exec(statement).all())


def group_requests_by_destination_and_window(
    pending_requests: list[TripRequest],
    location_by_id: dict[int, Location],
    heuristics: PlanningHeuristics,
) -> list[PlanningRequestGroup]:
    tolerance = timedelta(minutes=heuristics.pickup_window_tolerance_minutes)
    groups: list[_MutableGroup] = []

    for request in sorted(
        pending_requests,
        key=lambda trip_request: (
            trip_request.pickup_window_start,
            trip_request.pickup_window_end,
            trip_request.id or 0,
        ),
    ):
        request_id = request.id
        if request_id is None:
            continue

        matching_group = None
        for group in groups:
            if _is_group_compatible(group, request, location_by_id, heuristics.max_detour_meters, tolerance):
                matching_group = group
                break

        if matching_group is None:
            matching_group = _MutableGroup(anchor_request=request)
            groups.append(matching_group)

        matching_group.request_ids.append(request_id)
        matching_group.pickup_window_start = _min_datetime(matching_group.pickup_window_start, request.pickup_window_start)
        matching_group.pickup_window_end = _max_datetime(matching_group.pickup_window_end, request.pickup_window_end)

    return [
        PlanningRequestGroup(
            request_ids=sorted(group.request_ids),
            request_count=len(group.request_ids),
            pickup_window_start=group.pickup_window_start or group.anchor_request.pickup_window_start,
            pickup_window_end=group.pickup_window_end or group.anchor_request.pickup_window_end,
            anchor_dropoff_location_id=group.anchor_request.dropoff_location_id,
        )
        for group in groups
    ]


def _is_group_compatible(
    group: _MutableGroup,
    request: TripRequest,
    location_by_id: dict[int, Location],
    max_detour_meters: int,
    window_tolerance: timedelta,
) -> bool:
    if not _windows_overlap_with_tolerance(
        group.anchor_request.pickup_window_start,
        group.anchor_request.pickup_window_end,
        request.pickup_window_start,
        request.pickup_window_end,
        window_tolerance,
    ):
        return False

    anchor_dropoff = location_by_id.get(group.anchor_request.dropoff_location_id)
    request_dropoff = location_by_id.get(request.dropoff_location_id)

    if anchor_dropoff is None or request_dropoff is None:
        return False

    if (
        anchor_dropoff.latitude is None
        or anchor_dropoff.longitude is None
        or request_dropoff.latitude is None
        or request_dropoff.longitude is None
    ):
        return group.anchor_request.dropoff_location_id == request.dropoff_location_id

    distance_meters = haversine_distance_meters(
        anchor_dropoff.latitude,
        anchor_dropoff.longitude,
        request_dropoff.latitude,
        request_dropoff.longitude,
    )
    return distance_meters <= max_detour_meters


def _load_locations_by_id(session: Session, location_ids: set[int]) -> dict[int, Location]:
    if not location_ids:
        return {}

    locations = session.exec(select(Location).where(Location.id.in_(location_ids))).all()
    return {location.id: location for location in locations if location.id is not None}


def _load_driver_availability(
    session: Session,
    window_start: datetime,
    window_end: datetime,
) -> dict[int, list[_AvailabilityWindow]]:
    driver_windows: dict[int, list[_AvailabilityWindow]] = {}
    active_driver_ids = {
        driver.id
        for driver in session.exec(select(Driver).where(Driver.is_active == True)).all()  # noqa: E712
        if driver.id is not None
    }

    availability_statement = (
        select(DriverAvailabilityWindow)
        .where(DriverAvailabilityWindow.start_time < window_end)
        .where(DriverAvailabilityWindow.end_time > window_start)
    )
    for window in session.exec(availability_statement).all():
        if window.driver_id not in active_driver_ids:
            continue

        driver_windows.setdefault(window.driver_id, []).append(
            _AvailabilityWindow(start_time=window.start_time, end_time=window.end_time)
        )

    for driver_id in driver_windows:
        driver_windows[driver_id].sort(key=lambda window: (window.start_time, window.end_time))

    return dict(sorted(driver_windows.items()))


def _load_vehicle_availability(
    session: Session,
    window_start: datetime,
    window_end: datetime,
) -> dict[int, tuple[int, list[_AvailabilityWindow]]]:
    vehicles = [
        vehicle
        for vehicle in session.exec(select(Vehicle).where(Vehicle.is_active == True)).all()  # noqa: E712
        if vehicle.id is not None
    ]
    vehicle_capacities = {vehicle.id: vehicle.capacity for vehicle in vehicles}

    vehicle_windows: dict[int, list[_AvailabilityWindow]] = {vehicle.id: [] for vehicle in vehicles}
    availability_statement = (
        select(VehicleAvailabilityWindow)
        .where(VehicleAvailabilityWindow.start_time < window_end)
        .where(VehicleAvailabilityWindow.end_time > window_start)
    )
    for window in session.exec(availability_statement).all():
        if window.vehicle_id not in vehicle_windows:
            continue

        vehicle_windows[window.vehicle_id].append(
            _AvailabilityWindow(start_time=window.start_time, end_time=window.end_time)
        )

    for vehicle_id in vehicle_windows:
        vehicle_windows[vehicle_id].sort(key=lambda window: (window.start_time, window.end_time))

    return {
        vehicle_id: (vehicle_capacities[vehicle_id], vehicle_windows[vehicle_id])
        for vehicle_id in sorted(vehicle_windows)
    }


def _load_committed_run_windows(
    session: Session,
    window_start: datetime,
    window_end: datetime,
) -> tuple[dict[int, list[_AvailabilityWindow]], dict[int, list[_AvailabilityWindow]]]:
    committed_statuses = (TripRunStatus.PLANNED, TripRunStatus.ACTIVE)
    committed_statement = (
        select(TripRun)
        .where(TripRun.status.in_(committed_statuses))
        .where(TripRun.window_start < window_end)
        .where(TripRun.window_end > window_start)
        .where(or_(TripRun.driver_id.is_not(None), TripRun.vehicle_id.is_not(None)))
    )
    committed_runs = session.exec(committed_statement).all()

    driver_windows: dict[int, list[_AvailabilityWindow]] = {}
    vehicle_windows: dict[int, list[_AvailabilityWindow]] = {}

    for run in committed_runs:
        run_window = _AvailabilityWindow(start_time=run.window_start, end_time=run.window_end)

        if run.driver_id is not None:
            driver_windows.setdefault(run.driver_id, []).append(run_window)

        if run.vehicle_id is not None:
            vehicle_windows.setdefault(run.vehicle_id, []).append(run_window)

    for windows in (driver_windows, vehicle_windows):
        for resource_id in windows:
            windows[resource_id].sort(key=lambda window: (window.start_time, window.end_time))

    return dict(sorted(driver_windows.items())), dict(sorted(vehicle_windows.items()))


def _select_driver(
    run_window_start: datetime,
    run_window_end: datetime,
    driver_availability: dict[int, list[_AvailabilityWindow]],
    blocked_driver_windows: dict[int, list[_AvailabilityWindow]],
) -> Optional[int]:
    for driver_id, availability_windows in driver_availability.items():
        if not _window_fits_any(availability_windows, run_window_start, run_window_end):
            continue

        if _overlaps_any(blocked_driver_windows.get(driver_id, []), run_window_start, run_window_end):
            continue

        return driver_id

    return None


def _select_vehicle(
    run_window_start: datetime,
    run_window_end: datetime,
    required_capacity: int,
    vehicle_availability: dict[int, tuple[int, list[_AvailabilityWindow]]],
    blocked_vehicle_windows: dict[int, list[_AvailabilityWindow]],
) -> Optional[int]:
    for vehicle_id, (capacity, availability_windows) in vehicle_availability.items():
        if capacity < required_capacity:
            continue

        if not _window_fits_any(availability_windows, run_window_start, run_window_end):
            continue

        if _overlaps_any(blocked_vehicle_windows.get(vehicle_id, []), run_window_start, run_window_end):
            continue

        return vehicle_id

    return None


def _window_fits_any(
    availability_windows: list[_AvailabilityWindow],
    run_window_start: datetime,
    run_window_end: datetime,
) -> bool:
    return any(
        window.start_time <= run_window_start and run_window_end <= window.end_time
        for window in availability_windows
    )


def _overlaps_any(
    windows: list[_AvailabilityWindow],
    window_start: datetime,
    window_end: datetime,
) -> bool:
    return any(_windows_overlap(window.start_time, window.end_time, window_start, window_end) for window in windows)


def _windows_overlap(start_one: datetime, end_one: datetime, start_two: datetime, end_two: datetime) -> bool:
    return start_one < end_two and start_two < end_one


def _windows_overlap_with_tolerance(
    start_one: datetime,
    end_one: datetime,
    start_two: datetime,
    end_two: datetime,
    tolerance: timedelta,
) -> bool:
    return (start_one - tolerance) < end_two and (start_two - tolerance) < end_one


def _append_reason(reasons: dict[int, list[str]], request_ids: list[int], reason_code: str) -> None:
    for request_id in request_ids:
        reasons.setdefault(request_id, []).append(reason_code)


def _chunk_request_ids(request_ids: list[int], max_occupancy: int) -> list[list[int]]:
    if max_occupancy <= 0:
        return [sorted(request_ids)]

    sorted_ids = sorted(request_ids)
    return [sorted_ids[index:index + max_occupancy] for index in range(0, len(sorted_ids), max_occupancy)]


def _min_datetime(first: Optional[datetime], second: datetime) -> datetime:
    if first is None:
        return second
    return min(first, second)


def _max_datetime(first: Optional[datetime], second: datetime) -> datetime:
    if first is None:
        return second
    return max(first, second)
