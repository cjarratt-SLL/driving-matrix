from typing import Optional

from pydantic import BaseModel


class DriverCreate(BaseModel):
    first_name: str
    last_name: str
    is_active: bool = True
    phone_number: Optional[str] = None
    vehicle_assigned: Optional[str] = None
    notes: Optional[str] = None


class DriverRead(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    is_active: bool = True
    phone_number: Optional[str] = None
    vehicle_assigned: Optional[str] = None
    notes: Optional[str] = None
