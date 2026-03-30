from fastapi import APIRouter, HTTPException

from app.schemas.trip_schemas import TripCreate, TripRead, TripDetailRead
from app.storage import locations_db, residents_db, trips_db

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("", response_model=TripRead)
def create_trip(trip: TripCreate):
    resident = next((r for r in residents_db if r.id == trip.resident_id), None)
    if resident is None:
        raise HTTPException(status_code=404, detail="Resident not found")

    pickup_location = next(
        (loc for loc in locations_db if loc.id == trip.pickup_location_id),
        None,
    )
    if pickup_location is None:
        raise HTTPException(status_code=404, detail="Pickup location not found")

    dropoff_location = next(
        (loc for loc in locations_db if loc.id == trip.dropoff_location_id),
        None,
    )
    if dropoff_location is None:
        raise HTTPException(status_code=404, detail="Dropoff location not found")

    new_trip = TripRead(
        id=len(trips_db) + 1,
        resident_id=trip.resident_id,
        pickup_location_id=trip.pickup_location_id,
        dropoff_location_id=trip.dropoff_location_id,
        arrival_time=trip.arrival_time,
        status="scheduled",
        assigned_driver=None,
        assigned_vehicle=None,
    )
    trips_db.append(new_trip)
    return new_trip


@router.get("", response_model=list[TripRead])
def list_trips():
    return trips_db

@router.get("/details", response_model=list[TripDetailRead])
def list_trip_details():
    trip_details = []

    for trip in trips_db:
        resident = next((r for r in residents_db if r.id == trip.resident_id), None)
        pickup_location = next(
            (loc for loc in locations_db if loc.id == trip.pickup_location_id),
            None,
        )
        dropoff_location = next(
            (loc for loc in locations_db if loc.id == trip.dropoff_location_id),
            None,
        )

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
                assigned_driver=trip.assigned_driver,
                assigned_vehicle=trip.assigned_vehicle,
            )
        )

    return trip_details