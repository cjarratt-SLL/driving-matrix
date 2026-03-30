from typing import Optional

from pydantic import BaseModel


class LocationCreate(BaseModel):
    name: str
    address: str
    location_type: str
    resident_id: Optional[int] = None
    notes: Optional[str] = None


class LocationRead(BaseModel):
    id: Optional[int] = None
    name: str
    address: str
    location_type: str
    resident_id: Optional[int] = None
    notes: Optional[str] = None