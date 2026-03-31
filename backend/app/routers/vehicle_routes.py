from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.vehicle_models import Vehicle

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post("", response_model=Vehicle)
def create_vehicle(
    vehicle: Vehicle,
    session: Session = Depends(get_session),
):
    new_vehicle = Vehicle(
        name=vehicle.name,
        vehicle_type=vehicle.vehicle_type,
        capacity=vehicle.capacity,
        is_active=vehicle.is_active,
        wheelchair_accessible=vehicle.wheelchair_accessible,
        license_plate=vehicle.license_plate,
        notes=vehicle.notes,
    )
    session.add(new_vehicle)
    session.commit()
    session.refresh(new_vehicle)
    return new_vehicle


@router.get("", response_model=list[Vehicle])
def list_vehicles(session: Session = Depends(get_session)):
    vehicles = session.exec(select(Vehicle)).all()
    return vehicles