from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TripCreate(BaseModel):
    resident_id: int
    pickup_location_id: int
    dropoff_location_id: int
    arrival_time: datetime
    driver_id: Optional[int] = None


class TripRead(BaseModel):
    id: Optional[int] = None
    resident_id: int
    pickup_location_id: int
    dropoff_location_id: int
    arrival_time: datetime
    status: str = "scheduled"
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    assigned_vehicle: Optional[str] = None

class TripDetailRead(BaseModel):
    id: Optional[int] = None
    resident_id: int
    resident_name: str
    pickup_location_id: int
    pickup_location_name: str
    dropoff_location_id: int
    dropoff_location_name: str
    arrival_time: datetime
    status: str = "scheduled"
    driver_id: Optional[int] = None
    assigned_vehicle: Optional[str] = None