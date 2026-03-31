from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.resident_models import Resident
from app.schemas.resident_schemas import ResidentCreate, ResidentRead

router = APIRouter(prefix="/residents", tags=["Residents"])


@router.post("", response_model=ResidentRead)
def create_resident(
    resident: ResidentCreate,
    session: Session = Depends(get_session),
):
    new_resident = Resident(
        first_name=resident.first_name,
        last_name=resident.last_name,
        is_active=resident.is_active,
        rideshare_able=resident.rideshare_able,
        home_address=resident.home_address,
        notes=resident.notes,
    )
    session.add(new_resident)
    session.commit()
    session.refresh(new_resident)
    return new_resident


@router.get("", response_model=list[ResidentRead])
def list_residents(session: Session = Depends(get_session)):
    residents = session.exec(select(Resident)).all()
    return residents