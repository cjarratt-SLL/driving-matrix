from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Driver(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    first_name: str
    last_name: str

    is_active: bool = True

    phone_number: Optional[str] = None

    vehicle_assigned: Optional[str] = None

    notes: Optional[str] = None

    availability_windows: list["DriverAvailabilityWindow"] = Relationship(back_populates="driver")


class DriverAvailabilityWindow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    driver_id: int = Field(foreign_key="driver.id", index=True)
    start_time: datetime
    end_time: datetime

    driver: Optional[Driver] = Relationship(back_populates="availability_windows")
