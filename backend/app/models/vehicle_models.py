from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Vehicle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    vehicle_type: Optional[str] = None
    capacity: int = 1

    is_active: bool = True
    wheelchair_accessible: bool = False

    license_plate: Optional[str] = None
    notes: Optional[str] = None

    availability_windows: list["VehicleAvailabilityWindow"] = Relationship(back_populates="vehicle")
    capabilities: list["VehicleCapability"] = Relationship(back_populates="vehicle")


class VehicleAvailabilityWindow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    vehicle_id: int = Field(foreign_key="vehicle.id", index=True)
    start_time: datetime
    end_time: datetime

    vehicle: Optional[Vehicle] = Relationship(back_populates="availability_windows")


class VehicleCapability(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    vehicle_id: int = Field(foreign_key="vehicle.id", index=True)
    capability: str = Field(index=True)
    value: Optional[str] = None

    vehicle: Optional[Vehicle] = Relationship(back_populates="capabilities")
