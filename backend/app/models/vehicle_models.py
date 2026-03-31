from typing import Optional

from sqlmodel import Field, SQLModel


class Vehicle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    vehicle_type: Optional[str] = None
    capacity: int = 1

    is_active: bool = True
    wheelchair_accessible: bool = False

    license_plate: Optional[str] = None
    notes: Optional[str] = None