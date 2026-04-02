from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from pydantic import BaseModel

from app.db import get_session
from app.models.driver_models import Driver
from app.models.location_models import Location
from app.models.resident_models import Resident
from app.models.trip_models import Trip
from app.models.vehicle_models import Vehicle
from app.schemas.trip_schemas import TripCreate, TripRead, TripDetailRead, TripUpdate

router = APIRouter(prefix="/trips", tags=["Trips"])

class TripConflictItem(BaseModel):
    trip_id: int
    arrival_time: str
    resident_name: str
    driver_name: Optional[str] = None
    vehicle_name: Optional[str] = None


class DailyScheduleConflicts(BaseModel):
    driver_conflicts: list[TripConflictItem]
    vehicle_conflicts: list[TripConflictItem]

class DriverScheduleGroup(BaseModel):
    driver_id: Optional[int] = None
    driver_name: str
    trips: list[TripDetailRead]

class DriverGroupedSchedule(BaseModel):
    groups: list[DriverScheduleGroup]

class VehicleScheduleGroup(BaseModel):
    vehicle_id: Optional[int] = None
    vehicle_name: str
    trips: list[TripDetailRead]

class VehicleGroupedSchedule(BaseModel):
    groups: list[VehicleScheduleGroup]

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

    if trip.vehicle_id is not None:
        vehicle = session.get(Vehicle, trip.vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
    if trip.dropoff_time <= trip.pickup_time:
        raise HTTPException(
            status_code=400,
            detail="dropoff_time must be after pickup_time",
        )
    
    new_trip = Trip(
        resident_id=trip.resident_id,
        pickup_location_id=trip.pickup_location_id,
        dropoff_location_id=trip.dropoff_location_id,
        pickup_time=trip.pickup_time,
        dropoff_time=trip.dropoff_time,
        estimated_duration_minutes=trip.estimated_duration_minutes,
        status="scheduled",
        driver_id=trip.driver_id,
        vehicle_id=trip.vehicle_id,
    )
    session.add(new_trip)
    session.commit()
    session.refresh(new_trip)
    return new_trip

@router.patch("/{trip_id}", response_model=TripRead)
def update_trip(
    trip_id: int,
    trip_update: TripUpdate,
    session: Session = Depends(get_session),
):
    trip = session.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    update_data = trip_update.model_dump(exclude_unset=True)

    if "resident_id" in update_data:
        resident_id = update_data["resident_id"]
        if resident_id is None:
            raise HTTPException(status_code=400, detail="resident_id cannot be null")
        resident = session.get(Resident, resident_id)
        if resident is None:
            raise HTTPException(status_code=404, detail="Resident not found")
        trip.resident_id = resident_id

    if "pickup_location_id" in update_data:
        pickup_location_id = update_data["pickup_location_id"]
        if pickup_location_id is None:
            raise HTTPException(status_code=400, detail="pickup_location_id cannot be null")
        pickup_location = session.get(Location, pickup_location_id)
        if pickup_location is None:
            raise HTTPException(status_code=404, detail="Pickup location not found")
        trip.pickup_location_id = pickup_location_id

    if "dropoff_location_id" in update_data:
        dropoff_location_id = update_data["dropoff_location_id"]
        if dropoff_location_id is None:
            raise HTTPException(status_code=400, detail="dropoff_location_id cannot be null")
        dropoff_location = session.get(Location, dropoff_location_id)
        if dropoff_location is None:
            raise HTTPException(status_code=404, detail="Dropoff location not found")
        trip.dropoff_location_id = dropoff_location_id

    if "driver_id" in update_data:
        driver_id = update_data["driver_id"]
        if driver_id is not None:
            driver = session.get(Driver, driver_id)
            if driver is None:
                raise HTTPException(status_code=404, detail="Driver not found")
        trip.driver_id = driver_id

    if "vehicle_id" in update_data:
        vehicle_id = update_data["vehicle_id"]
        if vehicle_id is not None:
            vehicle = session.get(Vehicle, vehicle_id)
            if vehicle is None:
                raise HTTPException(status_code=404, detail="Vehicle not found")
        trip.vehicle_id = vehicle_id

    if "pickup_time" in update_data:
        pickup_time = update_data["pickup_time"]
        if pickup_time is None:
            raise HTTPException(status_code=400, detail="pickup_time cannot be null")
        trip.pickup_time = pickup_time

    if "dropoff_time" in update_data:
        dropoff_time = update_data["dropoff_time"]
        if dropoff_time is None:
            raise HTTPException(status_code=400, detail="dropoff_time cannot be null")
        trip.dropoff_time = dropoff_time

    if "estimated_duration_minutes" in update_data:
        estimated_duration_minutes = update_data["estimated_duration_minutes"]
        if estimated_duration_minutes is None:
            raise HTTPException(
                status_code=400,
                detail="estimated_duration_minutes cannot be null",
            )
        trip.estimated_duration_minutes = estimated_duration_minutes

    if "status" in update_data:
        status = update_data["status"]
        if status is None:
            raise HTTPException(status_code=400, detail="status cannot be null")
        trip.status = status

    if trip.dropoff_time <= trip.pickup_time:
        raise HTTPException(
            status_code=400,
            detail="dropoff_time must be after pickup_time",
        )

    session.add(trip)
    session.commit()
    session.refresh(trip)
    return trip

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
        vehicle = session.get(Vehicle, trip.vehicle_id) if trip.vehicle_id is not None else None

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
            pickup_time=trip.pickup_time,
            dropoff_time=trip.dropoff_time,
            estimated_duration_minutes=trip.estimated_duration_minutes,
            status=trip.status,
            driver_id=trip.driver_id,
            driver_name=f"{driver.first_name} {driver.last_name}" if driver else None,
            vehicle_id=trip.vehicle_id,
            vehicle_name=vehicle.name if vehicle else None,
        )
    )

    return trip_details

@router.get("/schedule", response_model=list[TripDetailRead])
def list_trips_for_date(
    trip_date: date,
    session: Session = Depends(get_session),
):
    trips = session.exec(select(Trip)).all()
    trip_details = []

    for trip in trips:
        if trip.pickup_time.date() != trip_date:
            continue

        resident = session.get(Resident, trip.resident_id)
        pickup_location = session.get(Location, trip.pickup_location_id)
        dropoff_location = session.get(Location, trip.dropoff_location_id)
        driver = session.get(Driver, trip.driver_id) if trip.driver_id is not None else None
        vehicle = session.get(Vehicle, trip.vehicle_id) if trip.vehicle_id is not None else None

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
                pickup_time=trip.pickup_time,
                dropoff_time=trip.dropoff_time,
                estimated_duration_minutes=trip.estimated_duration_minutes,
                status=trip.status,
                driver_id=trip.driver_id,
                driver_name=f"{driver.first_name} {driver.last_name}" if driver else None,
                vehicle_id=trip.vehicle_id,
                vehicle_name=vehicle.name if vehicle else None,
            )
        )

    return sorted(trip_details, key=lambda t: t.pickup_time)

@router.get("/schedule/conflicts", response_model=DailyScheduleConflicts)
def get_schedule_conflicts(
    trip_date: date,
    session: Session = Depends(get_session),
):
    trips = session.exec(select(Trip)).all()

    driver_conflicts = []
    vehicle_conflicts = []

    driver_seen = {}
    vehicle_seen = {}

    for trip in trips:
        if trip.pickup_time.date() != trip_date:
            continue

        resident = session.get(Resident, trip.resident_id)
        driver = session.get(Driver, trip.driver_id) if trip.driver_id is not None else None
        vehicle = session.get(Vehicle, trip.vehicle_id) if trip.vehicle_id is not None else None

        resident_name = f"{resident.first_name} {resident.last_name}" if resident else "Unknown Resident"
        driver_name = f"{driver.first_name} {driver.last_name}" if driver else None
        vehicle_name = vehicle.name if vehicle else None

        if trip.driver_id is not None:
            driver_key = (trip.driver_id, trip.arrival_time)
            if driver_key in driver_seen:
                driver_conflicts.append(
                    TripConflictItem(
                        trip_id=trip.id,
                        arrival_time=trip.arrival_time.isoformat(),
                        resident_name=resident_name,
                        driver_name=driver_name,
                        vehicle_name=vehicle_name,
                    )
                )
                first_trip = driver_seen[driver_key]
                if all(item.trip_id != first_trip["trip_id"] for item in driver_conflicts):
                    driver_conflicts.append(
                        TripConflictItem(
                            trip_id=first_trip["trip_id"],
                            arrival_time=first_trip["arrival_time"],
                            resident_name=first_trip["resident_name"],
                            driver_name=first_trip["driver_name"],
                            vehicle_name=first_trip["vehicle_name"],
                        )
                    )
            else:
                driver_seen[driver_key] = {
                    "trip_id": trip.id,
                    "arrival_time": trip.arrival_time.isoformat(),
                    "resident_name": resident_name,
                    "driver_name": driver_name,
                    "vehicle_name": vehicle_name,
                }

        if trip.vehicle_id is not None:
            vehicle_key = (trip.vehicle_id, trip.pickup_time, trip.dropoff_time)
            if vehicle_key in vehicle_seen:
                vehicle_conflicts.append(
                    TripConflictItem(
                        trip_id=trip.id,
                        arrival_time=trip.arrival_time.isoformat(),
                        resident_name=resident_name,
                        driver_name=driver_name,
                        vehicle_name=vehicle_name,
                    )
                )
                first_trip = vehicle_seen[vehicle_key]
                if all(item.trip_id != first_trip["trip_id"] for item in vehicle_conflicts):
                    vehicle_conflicts.append(
                        TripConflictItem(
                            trip_id=first_trip["trip_id"],
                            arrival_time=first_trip["arrival_time"],
                            resident_name=first_trip["resident_name"],
                            driver_name=first_trip["driver_name"],
                            vehicle_name=first_trip["vehicle_name"],
                        )
                    )
            else:
                vehicle_seen[vehicle_key] = {
                    "trip_id": trip.id,
                    "arrival_time": trip.arrival_time.isoformat(),
                    "resident_name": resident_name,
                    "driver_name": driver_name,
                    "vehicle_name": vehicle_name,
                }

    return DailyScheduleConflicts(
        driver_conflicts=driver_conflicts,
        vehicle_conflicts=vehicle_conflicts,
    )

@router.get("/schedule/by-driver", response_model=DriverGroupedSchedule)
def list_trips_grouped_by_driver(
    trip_date: date,
    session: Session = Depends(get_session),
):
    trips = session.exec(select(Trip)).all()
    grouped = {}

    for trip in trips:
        if trip.pickup_time.date() != trip_date:
            continue

        resident = session.get(Resident, trip.resident_id)
        pickup_location = session.get(Location, trip.pickup_location_id)
        dropoff_location = session.get(Location, trip.dropoff_location_id)
        driver = session.get(Driver, trip.driver_id) if trip.driver_id is not None else None
        vehicle = session.get(Vehicle, trip.vehicle_id) if trip.vehicle_id is not None else None

        if resident is None or pickup_location is None or dropoff_location is None:
            continue

        if driver is not None:
            group_key = driver.id
            group_name = f"{driver.first_name} {driver.last_name}"
        else:
            group_key = None
            group_name = "Unassigned"

        trip_detail = TripDetailRead(
            id=trip.id,
            resident_id=trip.resident_id,
            resident_name=f"{resident.first_name} {resident.last_name}",
            pickup_location_id=trip.pickup_location_id,
            pickup_location_name=pickup_location.name,
            dropoff_location_id=trip.dropoff_location_id,
            dropoff_location_name=dropoff_location.name,
            pickup_time=trip.pickup_time,
            dropoff_time=trip.dropoff_time,
            estimated_duration_minutes=trip.estimated_duration_minutes,
            status=trip.status,
            driver_id=trip.driver_id,
            driver_name=f"{driver.first_name} {driver.last_name}" if driver else None,
            vehicle_id=trip.vehicle_id,
            vehicle_name=vehicle.name if vehicle else None,
        )

        if group_key not in grouped:
            grouped[group_key] = {
                "driver_id": group_key,
                "driver_name": group_name,
                "trips": [],
            }

        grouped[group_key]["trips"].append(trip_detail)

    groups = []
    for group in grouped.values():
        sorted_trips = sorted(group["trips"], key=lambda t: t.pickup_time)
        groups.append(
            DriverScheduleGroup(
                driver_id=group["driver_id"],
                driver_name=group["driver_name"],
                trips=sorted_trips,
            )
        )

    groups = sorted(
        groups,
        key=lambda g: (g.driver_name == "Unassigned", g.driver_name.lower())
    )

    return DriverGroupedSchedule(groups=groups)

@router.get("/schedule/by-vehicle", response_model=VehicleGroupedSchedule)
def list_trips_grouped_by_vehicle(
    trip_date: date,
    session: Session = Depends(get_session),
):
    trips = session.exec(select(Trip)).all()
    grouped = {}

    for trip in trips:
        if trip.pickup_time.date() != trip_date:
            continue

        resident = session.get(Resident, trip.resident_id)
        pickup_location = session.get(Location, trip.pickup_location_id)
        dropoff_location = session.get(Location, trip.dropoff_location_id)
        driver = session.get(Driver, trip.driver_id) if trip.driver_id is not None else None
        vehicle = session.get(Vehicle, trip.vehicle_id) if trip.vehicle_id is not None else None

        if resident is None or pickup_location is None or dropoff_location is None:
            continue

        if vehicle is not None:
            group_key = vehicle.id
            group_name = vehicle.name
        else:
            group_key = None
            group_name = "Unassigned"

        trip_detail = TripDetailRead(
            id=trip.id,
            resident_id=trip.resident_id,
            resident_name=f"{resident.first_name} {resident.last_name}",
            pickup_location_id=trip.pickup_location_id,
            pickup_location_name=pickup_location.name,
            dropoff_location_id=trip.dropoff_location_id,
            dropoff_location_name=dropoff_location.name,
            pickup_time=trip.pickup_time,
            dropoff_time=trip.dropoff_time,
            estimated_duration_minutes=trip.estimated_duration_minutes,
            status=trip.status,
            driver_id=trip.driver_id,
            driver_name=f"{driver.first_name} {driver.last_name}" if driver else None,
            vehicle_id=trip.vehicle_id,
            vehicle_name=vehicle.name if vehicle else None,
        )

        if group_key not in grouped:
            grouped[group_key] = {
                "vehicle_id": group_key,
                "vehicle_name": group_name,
                "trips": [],
            }

        grouped[group_key]["trips"].append(trip_detail)

    groups = []
    for group in grouped.values():
        sorted_trips = sorted(group["trips"], key=lambda t: t.pickup_time)
        groups.append(
            VehicleScheduleGroup(
                vehicle_id=group["vehicle_id"],
                vehicle_name=group["vehicle_name"],
                trips=sorted_trips,
            )
        )

    groups = sorted(
        groups,
        key=lambda g: (g.vehicle_name == "Unassigned", g.vehicle_name.lower())
    )

    return VehicleGroupedSchedule(groups=groups)