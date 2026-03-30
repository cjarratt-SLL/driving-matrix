from typing import Optional

from pydantic import BaseModel


class ResidentCreate(BaseModel):
    first_name: str
    last_name: str
    is_active: bool = True
    rideshare_able: bool = True
    home_address: Optional[str] = None
    notes: Optional[str] = None


class ResidentRead(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    is_active: bool = True
    rideshare_able: bool = True
    home_address: Optional[str] = None
    notes: Optional[str] = None