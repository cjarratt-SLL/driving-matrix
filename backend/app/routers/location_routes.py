from fastapi import APIRouter

from app.schemas.location_schemas import LocationCreate, LocationRead
from app.storage import locations_db

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.post("", response_model=LocationRead)
def create_location(location: LocationCreate):
    new_location = LocationRead(
        id=len(locations_db) + 1,
        name=location.name,
        address=location.address,
        location_type=location.location_type,
        resident_id=location.resident_id,
        notes=location.notes,
    )
    locations_db.append(new_location)
    return new_location


@router.get("", response_model=list[LocationRead])
def list_locations():
    return locations_db