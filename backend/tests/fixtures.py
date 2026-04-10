from datetime import datetime

from app.models.driver_models import Driver
from app.models.location_models import Location
from app.models.resident_models import Resident
from app.models.trip_models import EstimateSource, Trip
from app.models.vehicle_models import Vehicle

RESIDENT_DATA = [
    {"id": 1, "first_name": "Alice", "last_name": "Anderson", "home_address": "101 Maple Ave"},
    {"id": 2, "first_name": "Bob", "last_name": "Brown", "home_address": "202 Oak St"},
    {"id": 3, "first_name": "Cora", "last_name": "Campbell", "home_address": "303 Pine Rd"},
]

DRIVER_DATA = [
    {"id": 1, "first_name": "Diana", "last_name": "Driver"},
    {"id": 2, "first_name": "Eli", "last_name": "Edwards"},
]

VEHICLE_DATA = [
    {"id": 1, "name": "Van 1", "vehicle_type": "van", "capacity": 4},
    {"id": 2, "name": "Car 2", "vehicle_type": "sedan", "capacity": 3},
]

LOCATION_DATA = [
    {
        "id": 1,
        "name": "Resident A Home",
        "address": "101 Maple Ave",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "location_type": "home",
        "resident_id": 1,
    },
    {
        "id": 2,
        "name": "Clinic",
        "address": "900 Health Dr",
        "latitude": 37.7840,
        "longitude": -122.4090,
        "location_type": "facility",
    },
    {
        "id": 3,
        "name": "Resident B Home",
        "address": "202 Oak St",
        "latitude": 37.7640,
        "longitude": -122.4290,
        "location_type": "home",
        "resident_id": 2,
    },
    {
        "id": 4,
        "name": "No Coordinates Facility",
        "address": "404 Unknown Ln",
        "latitude": None,
        "longitude": None,
        "location_type": "facility",
    },
]

TRIP_DATA = [
    {
        "id": 1,
        "resident_id": 1,
        "pickup_location_id": 1,
        "dropoff_location_id": 2,
        "pickup_time": datetime(2026, 4, 15, 9, 0),
        "dropoff_time": datetime(2026, 4, 15, 9, 40),
        "estimated_distance_meters": 2200,
        "estimated_duration_minutes": 12,
        "estimate_source": EstimateSource.ROUTE_ESTIMATOR,
        "estimate_updated_at": datetime(2026, 4, 1, 8, 0),
        "status": "scheduled",
        "driver_id": 1,
        "vehicle_id": 1,
    },
    {
        "id": 2,
        "resident_id": 2,
        "pickup_location_id": 3,
        "dropoff_location_id": 2,
        "pickup_time": datetime(2026, 4, 15, 10, 0),
        "dropoff_time": datetime(2026, 4, 15, 10, 45),
        "estimated_distance_meters": 3100,
        "estimated_duration_minutes": 17,
        "estimate_source": EstimateSource.ROUTE_ESTIMATOR,
        "estimate_updated_at": datetime(2026, 4, 1, 8, 5),
        "status": "scheduled",
        "driver_id": 2,
        "vehicle_id": 2,
    },
    {
        "id": 3,
        "resident_id": 3,
        "pickup_location_id": 2,
        "dropoff_location_id": 1,
        "pickup_time": datetime(2026, 4, 16, 8, 30),
        "dropoff_time": datetime(2026, 4, 16, 9, 0),
        "estimated_distance_meters": 1900,
        "estimated_duration_minutes": 10,
        "estimate_source": EstimateSource.ROUTE_ESTIMATOR,
        "estimate_updated_at": datetime(2026, 4, 1, 8, 10),
        "status": "scheduled",
        "driver_id": None,
        "vehicle_id": None,
    },
]


def build_seed_records():
    return {
        "residents": [Resident(**payload) for payload in RESIDENT_DATA],
        "drivers": [Driver(**payload) for payload in DRIVER_DATA],
        "vehicles": [Vehicle(**payload) for payload in VEHICLE_DATA],
        "locations": [Location(**payload) for payload in LOCATION_DATA],
        "trips": [Trip(**payload) for payload in TRIP_DATA],
    }
