from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.driver_models import Driver
from app.models.location_models import Location
from app.models.resident_models import Resident
from app.models.trip_models import Trip
from app.schemas.trip_schemas import TripCreate, TripRead, TripDetailRead

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("", response_model=TripRead)
def create_trip(
    trip: TripCreate,
    session: Session = Depends(get_session),
):
    resident = session.get(Resident, trip.resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Resident not found")

    pickup_location = session.get(Location, trip.pickup_location_id)
    if pickup_location is None:
        raise HTTPException(status_code=404, detail="Pickup location not found")

    dropoff_location = session.get(Location, trip.dropoff_location_id)
    if dropoff_location is None:
        raise HTTPException(status_code=404, detail="Dropoff location not found")

    if trip.driver_id is not None:
        driver = session.get(Driver, trip.driver_id)
        if driver is None:
            raise HTTPException(status_code=404, detail="Driver not found")

    new_trip = Trip(
        resident_id=trip.resident_id,
        pickup_location_id=trip.pickup_location_id,
        dropoff_location_id=trip.dropoff_location_id,
        arrival_time=trip.arrival_time,
        status="scheduled",
        driver_id=trip.driver_id,
        assigned_vehicle=None,
    )
    session.add(new_trip)
    session.commit()
    session.refresh(new_trip)
    return new_trip


@router.get("", response_model=list[TripRead])
def list_trips(session: Session = Depends(get_session)):
    trips = session.exec(select(Trip)).all()
    return trips


@router.get("/details", response_model=list[TripDetailRead])
def list_trip_details(session: Session = Depends(get_session)):
    trips = session.exec(select(Trip)).all()
    trip_details = []

    for trip in trips:
        resident = session.get(Resident, trip.resident_id)
        pickup_location = session.get(Location, trip.pickup_location_id)
        dropoff_location = session.get(Location, trip.dropoff_location_id)
        driver = session.get(Driver, trip.driver_id) if trip.driver_id is not None else None

        if resident is None or pickup_location is None or dropoff_location is None:
            continue

        trip_details.append(
            TripDetailRead(
                id=trip.id,
                resident_id=trip.resident_id,
                resident_name=f"{resident.first_name} {resident.last_name}",
                pickup_location_id=trip.pickup_location_id,
                pickup_location_name=pickup_location.name,
                dropoff_location_id=trip.dropoff_location_id,
                dropoff_location_name=dropoff_location.name,
                arrival_time=trip.arrival_time,
                status=trip.status,
                driver_id=trip.driver_id,
                driver_name=f"{driver.first_name} {driver.last_name}" if driver else None,
                assigned_vehicle=trip.assigned_vehicle,
            )
        )

    return trip_details