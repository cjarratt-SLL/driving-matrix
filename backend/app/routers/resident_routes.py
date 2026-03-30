from fastapi import APIRouter

from app.schemas.resident_schemas import ResidentCreate, ResidentRead
from app.storage import residents_db

router = APIRouter(prefix="/residents", tags=["Residents"])


@router.post("", response_model=ResidentRead)
def create_resident(resident: ResidentCreate):
    new_resident = ResidentRead(
        id=len(residents_db) + 1,
        first_name=resident.first_name,
        last_name=resident.last_name,
        is_active=resident.is_active,
        rideshare_able=resident.rideshare_able,
        home_address=resident.home_address,
        notes=resident.notes,
    )
    residents_db.append(new_resident)
    return new_resident


@router.get("", response_model=list[ResidentRead])
def list_residents():
    return residents_db