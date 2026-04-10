from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.models.trip_models import EstimateSource


class TripCreate(BaseModel):
    resident_id: int
    pickup_location_id: int
    dropoff_location_id: int
    pickup_time: datetime
    dropoff_time: datetime
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None


class TripRead(BaseModel):
    id: Optional[int] = None
    resident_id: int
    pickup_location_id: int
    dropoff_location_id: int
    pickup_time: datetime
    dropoff_time: datetime
    estimated_distance_meters: Optional[int] = None
    estimated_duration_minutes: int = 30
    estimate_source: EstimateSource = EstimateSource.SCHEDULED
    estimate_updated_at: datetime
    status: str = "scheduled"
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    vehicle_id: Optional[int] = None
    vehicle_name: Optional[str] = None


class TripDetailRead(BaseModel):
    id: Optional[int] = None
    resident_id: int
    resident_name: str
    pickup_location_id: int
    pickup_location_name: str
    dropoff_location_id: int
    dropoff_location_name: str
    pickup_time: datetime
    dropoff_time: datetime
    duration_minutes: int
    estimated_distance_meters: Optional[int] = None
    estimated_duration_minutes: int = 30
    estimate_source: EstimateSource = EstimateSource.SCHEDULED
    estimate_updated_at: datetime
    status: str = "scheduled"
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    vehicle_id: Optional[int] = None
    vehicle_name: Optional[str] = None


class TripUpdate(BaseModel):
    resident_id: Optional[int] = None
    pickup_location_id: Optional[int] = None
    dropoff_location_id: Optional[int] = None
    pickup_time: Optional[datetime] = None
    dropoff_time: Optional[datetime] = None
    status: Optional[str] = None
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
