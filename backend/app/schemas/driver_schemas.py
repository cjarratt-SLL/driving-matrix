from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class DriverCreate(BaseModel):
    first_name: str
    last_name: str
    is_active: bool = True
    phone_number: Optional[str] = None
    vehicle_assigned: Optional[str] = None
    notes: Optional[str] = None


class DriverRead(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    is_active: bool = True
    phone_number: Optional[str] = None
    vehicle_assigned: Optional[str] = None
    notes: Optional[str] = None


class DriverAvailabilityWindowBase(BaseModel):
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "DriverAvailabilityWindowBase":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class DriverAvailabilityWindowCreate(DriverAvailabilityWindowBase):
    driver_id: int


class DriverAvailabilityWindowUpdate(DriverAvailabilityWindowBase):
    pass


class DriverAvailabilityWindowRead(DriverAvailabilityWindowBase):
    id: int
    driver_id: int
