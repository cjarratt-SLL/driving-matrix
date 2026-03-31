from typing import Optional

from sqlmodel import Field, SQLModel


class Driver(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    first_name: str
    last_name: str

    is_active: bool = True

    phone_number: Optional[str] = None

    vehicle_assigned: Optional[str] = None

    notes: Optional[str] = None