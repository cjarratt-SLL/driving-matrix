from typing import Optional

from sqlmodel import Field, SQLModel


class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    address: str
    location_type: str
    resident_id: Optional[int] = None
    notes: Optional[str] = None