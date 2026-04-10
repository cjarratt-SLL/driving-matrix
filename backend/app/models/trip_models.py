from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class EstimateSource(str, Enum):
    SCHEDULED = "scheduled"
    SCHEDULED_WINDOW = "scheduled_window"
    ROUTE_ESTIMATOR = "route_estimator"


class Trip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    resident_id: int
    pickup_location_id: int
    dropoff_location_id: int

    pickup_time: datetime
    dropoff_time: datetime

    estimated_distance_meters: Optional[int] = None
    estimated_duration_minutes: int = 30
    estimate_source: EstimateSource = EstimateSource.SCHEDULED
    estimate_updated_at: datetime = Field(default_factory=datetime.utcnow)

    status: str = "scheduled"

    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
