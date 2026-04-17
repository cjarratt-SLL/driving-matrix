from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class VehicleCreate(BaseModel):
    name: str
    vehicle_type: Optional[str] = None
    capacity: int = Field(default=1, ge=1)
    is_active: bool = True
    wheelchair_accessible: bool = False
    license_plate: Optional[str] = None
    notes: Optional[str] = None


class VehicleRead(BaseModel):
    id: Optional[int] = None
    name: str
    vehicle_type: Optional[str] = None
    capacity: int = Field(default=1, ge=1)
    is_active: bool = True
    wheelchair_accessible: bool = False
    license_plate: Optional[str] = None
    notes: Optional[str] = None


class VehicleAvailabilityWindowBase(BaseModel):
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "VehicleAvailabilityWindowBase":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class VehicleAvailabilityWindowCreate(VehicleAvailabilityWindowBase):
    vehicle_id: int


class VehicleAvailabilityWindowUpdate(VehicleAvailabilityWindowBase):
    pass


class VehicleAvailabilityWindowRead(VehicleAvailabilityWindowBase):
    id: int
    vehicle_id: int


class VehicleCapabilityBase(BaseModel):
    capability: str = Field(min_length=1)
    value: Optional[str] = None


class VehicleCapabilityCreate(VehicleCapabilityBase):
    vehicle_id: int


class VehicleCapabilityUpdate(VehicleCapabilityBase):
    pass


class VehicleCapabilityRead(VehicleCapabilityBase):
    id: int
    vehicle_id: int
