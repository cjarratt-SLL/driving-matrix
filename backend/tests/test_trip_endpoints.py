from datetime import date, datetime

import pytest
from fastapi import HTTPException

from app.routers import trip_routes
from app.schemas.trip_schemas import TripCreate, TripUpdate


def test_create_trip_rejects_conflicting_driver_assignment(session):
    with pytest.raises(HTTPException) as exc:
        trip_routes.create_trip(
            TripCreate(
                resident_id=2,
                pickup_location_id=3,
                dropoff_location_id=2,
                pickup_time=datetime(2026, 4, 15, 9, 15),
                dropoff_time=datetime(2026, 4, 15, 9, 45),
                driver_id=1,
                vehicle_id=2,
            ),
            session=session,
        )

    assert exc.value.status_code == 400
    detail = exc.value.detail
    assert detail["resource_type"] == "driver"
    assert detail["resource_id"] == 1
    assert detail["conflicting_trip_id"] == 1


def test_update_trip_rejects_conflicting_vehicle_assignment(session):
    with pytest.raises(HTTPException) as exc:
        trip_routes.update_trip(
            trip_id=2,
            trip_update=TripUpdate(
                pickup_time=datetime(2026, 4, 15, 9, 10),
                dropoff_time=datetime(2026, 4, 15, 9, 30),
                vehicle_id=1,
            ),
            session=session,
        )

    assert exc.value.status_code == 400
    detail = exc.value.detail
    assert detail["resource_type"] == "vehicle"
    assert detail["resource_id"] == 1
    assert detail["conflicting_trip_id"] == 1


def test_schedule_and_grouped_schedule_endpoints_use_trip_date_and_sorting(session):
    schedule = trip_routes.list_trips_for_date(trip_date=date(2026, 4, 15), session=session)
    assert [trip.id for trip in schedule] == [1, 2]

    driver_groups = trip_routes.list_trips_grouped_by_driver(
        trip_date=date(2026, 4, 15),
        session=session,
    ).groups
    assert [group.driver_name for group in driver_groups] == ["Diana Driver", "Eli Edwards"]
    assert [trip.id for trip in driver_groups[0].trips] == [1]
    assert [trip.id for trip in driver_groups[1].trips] == [2]

    vehicle_groups = trip_routes.list_trips_grouped_by_vehicle(
        trip_date=date(2026, 4, 15),
        session=session,
    ).groups
    assert [group.vehicle_name for group in vehicle_groups] == ["Car 2", "Van 1"]
    assert [trip.id for trip in vehicle_groups[0].trips] == [2]
    assert [trip.id for trip in vehicle_groups[1].trips] == [1]


def test_trip_responses_include_estimate_fields_with_expected_shape(session):
    trip_summary = trip_routes.list_trips(session=session)[0].model_dump()
    assert set(
        [
            "estimated_distance_meters",
            "estimated_duration_minutes",
            "estimate_source",
            "estimate_updated_at",
        ]
    ).issubset(trip_summary.keys())
    assert isinstance(trip_summary["estimated_duration_minutes"], int)
    assert str(trip_summary["estimate_source"]) in {
        "EstimateSource.SCHEDULED",
        "EstimateSource.SCHEDULED_WINDOW",
        "EstimateSource.ROUTE_ESTIMATOR",
    }
    assert isinstance(trip_summary["estimate_updated_at"], datetime)

    trip_detail = trip_routes.list_trip_details(session=session)[0].model_dump()
    assert "estimate_source" in trip_detail
    assert "estimated_distance_meters" in trip_detail
    assert isinstance(trip_detail["estimated_duration_minutes"], int)
    assert isinstance(trip_detail["estimate_updated_at"], datetime)


def test_create_trip_falls_back_to_scheduled_window_when_route_estimation_unavailable(session):
    trip = trip_routes.create_trip(
        TripCreate(
            resident_id=1,
            pickup_location_id=1,
            dropoff_location_id=4,
            pickup_time=datetime(2026, 4, 17, 11, 0),
            dropoff_time=datetime(2026, 4, 17, 12, 30),
            driver_id=None,
            vehicle_id=None,
        ),
        session=session,
    )

    assert trip.estimated_distance_meters is None
    assert trip.estimated_duration_minutes == 90
    assert str(trip.estimate_source) == "EstimateSource.SCHEDULED_WINDOW"
    assert isinstance(trip.estimate_updated_at, datetime)
