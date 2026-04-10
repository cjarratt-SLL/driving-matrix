from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import Optional


EARTH_RADIUS_METERS = 6_371_000
DEFAULT_AVERAGE_SPEED_METERS_PER_SECOND = 11.176  # ~25 mph deterministic stub


@dataclass(frozen=True)
class RouteEstimate:
    distance_meters: int
    duration_seconds: int

    @property
    def duration_minutes(self) -> int:
        return max(1, int(round(self.duration_seconds / 60)))


def estimate_route(
    pickup_location,
    dropoff_location,
    departure_time: datetime,
) -> Optional[RouteEstimate]:
    """Provider-agnostic route estimate interface with deterministic fallback logic.

    This implementation is intentionally deterministic and does not call any
    external routing provider yet. It can later be replaced or extended with
    pluggable provider integrations while preserving the same return contract.
    """
    del departure_time  # reserved for future provider logic

    pickup_latitude = read_coordinate(pickup_location, "latitude")
    pickup_longitude = read_coordinate(pickup_location, "longitude")
    dropoff_latitude = read_coordinate(dropoff_location, "latitude")
    dropoff_longitude = read_coordinate(dropoff_location, "longitude")

    if (
        pickup_latitude is None
        or pickup_longitude is None
        or dropoff_latitude is None
        or dropoff_longitude is None
    ):
        return None

    distance_meters = haversine_distance_meters(
        pickup_latitude,
        pickup_longitude,
        dropoff_latitude,
        dropoff_longitude,
    )

    # Inflate straight-line distance to approximate road-network distance.
    routed_distance_meters = max(1, int(round(distance_meters * 1.25)))
    duration_seconds = max(
        60,
        int(round(routed_distance_meters / DEFAULT_AVERAGE_SPEED_METERS_PER_SECOND)),
    )

    return RouteEstimate(
        distance_meters=routed_distance_meters,
        duration_seconds=duration_seconds,
    )


def read_coordinate(location, coordinate_name: str) -> Optional[float]:
    if not hasattr(location, coordinate_name):
        location_type = type(location).__name__
        raise AttributeError(
            f"{location_type} is missing '{coordinate_name}' required for routing estimates"
        )

    coordinate = getattr(location, coordinate_name)
    if coordinate is None:
        return None

    return float(coordinate)


def haversine_distance_meters(
    latitude_one: float,
    longitude_one: float,
    latitude_two: float,
    longitude_two: float,
) -> float:
    latitude_one_radians = radians(latitude_one)
    longitude_one_radians = radians(longitude_one)
    latitude_two_radians = radians(latitude_two)
    longitude_two_radians = radians(longitude_two)

    delta_latitude = latitude_two_radians - latitude_one_radians
    delta_longitude = longitude_two_radians - longitude_one_radians

    haversine = (
        sin(delta_latitude / 2) ** 2
        + cos(latitude_one_radians)
        * cos(latitude_two_radians)
        * sin(delta_longitude / 2) ** 2
    )

    return 2 * EARTH_RADIUS_METERS * asin(sqrt(haversine))
