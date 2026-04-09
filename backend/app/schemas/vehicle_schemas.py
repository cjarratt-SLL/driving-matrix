from typing import Optional

from pydantic import BaseModel, Field


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
