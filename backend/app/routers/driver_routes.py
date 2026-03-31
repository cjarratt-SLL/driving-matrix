from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.driver_models import Driver

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.post("", response_model=Driver)
def create_driver(
    driver: Driver,
    session: Session = Depends(get_session),
):
    new_driver = Driver(
        first_name=driver.first_name,
        last_name=driver.last_name,
        is_active=driver.is_active,
        phone_number=driver.phone_number,
        vehicle_assigned=driver.vehicle_assigned,
        notes=driver.notes,
    )
    session.add(new_driver)
    session.commit()
    session.refresh(new_driver)
    return new_driver


@router.get("", response_model=list[Driver])
def list_drivers(session: Session = Depends(get_session)):
    drivers = session.exec(select(Driver)).all()
    return drivers
