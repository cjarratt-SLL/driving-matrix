from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Trip(BaseModel):
    id: Optional[int] = None

    resident_name: str

    pickup_location: str
    dropoff_location: str

    arrival_time: datetime

    status: str = "scheduled"

    assigned_driver: Optional[str] = None
    assigned_vehicle: Optional[str] = None