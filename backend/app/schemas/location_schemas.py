from typing import Optional

from pydantic import BaseModel


class LocationCreate(BaseModel):
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    geocode_status: Optional[str] = None
    location_type: str
    resident_id: Optional[int] = None
    notes: Optional[str] = None


class LocationRead(BaseModel):
    id: Optional[int] = None
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    geocode_status: Optional[str] = None
    location_type: str
    resident_id: Optional[int] = None
    notes: Optional[str] = None
