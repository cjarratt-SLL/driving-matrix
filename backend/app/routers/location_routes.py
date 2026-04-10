from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.location_models import Location
from app.schemas.location_schemas import LocationCreate, LocationRead

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.post("", response_model=LocationRead)
def create_location(
    location: LocationCreate,
    session: Session = Depends(get_session),
):
    # Keep `address` for operator readability, but prefer coordinates for
    # downstream distance/time estimation workflows when latitude/longitude
    # are present.
    new_location = Location(
        name=location.name,
        address=location.address,
        latitude=location.latitude,
        longitude=location.longitude,
        timezone=location.timezone,
        geocode_status=location.geocode_status,
        location_type=location.location_type,
        resident_id=location.resident_id,
        notes=location.notes,
    )
    session.add(new_location)
    session.commit()
    session.refresh(new_location)
    return new_location


@router.get("", response_model=list[LocationRead])
def list_locations(session: Session = Depends(get_session)):
    locations = session.exec(select(Location)).all()
    return locations
