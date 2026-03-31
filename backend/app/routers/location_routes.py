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
    new_location = Location(
        name=location.name,
        address=location.address,
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
