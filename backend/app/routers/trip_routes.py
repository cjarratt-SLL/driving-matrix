from fastapi import APIRouter
from app.models.trip_models import Trip

router = APIRouter(prefix="/trips", tags=["Trips"])

trips_db = []


@router.post("")
def create_trip(trip: Trip):
    trip.id = len(trips_db) + 1
    trips_db.append(trip)
    return trip


@router.get("")
def list_trips():
    return trips_db