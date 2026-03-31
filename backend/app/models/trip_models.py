from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Trip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    resident_id: int
    pickup_location_id: int
    dropoff_location_id: int

    pickup_time: datetime
    arrival_time: datetime
    estimated_duration_minutes: int = 30

    status: str = "scheduled"

    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None