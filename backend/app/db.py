from sqlmodel import Session, SQLModel, create_engine
from app.models.dispatch_models import RunAssignment, TripRequest, TripRun
from app.models.driver_models import Driver
from app.models.location_models import Location
from app.models.resident_models import Resident
from app.models.trip_models import Trip
from app.models.vehicle_models import Vehicle

DATABASE_URL = "sqlite:///driving_matrix.db"

engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
    