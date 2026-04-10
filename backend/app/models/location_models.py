from typing import Optional

from sqlmodel import Field, SQLModel


class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    geocode_status: Optional[str] = None
    location_type: str
    resident_id: Optional[int] = None
    notes: Optional[str] = None
