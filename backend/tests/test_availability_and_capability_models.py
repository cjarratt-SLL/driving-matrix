from datetime import datetime

import pytest
from pydantic import ValidationError
from sqlmodel import select

from app.models.driver_models import DriverAvailabilityWindow
from app.models.vehicle_models import VehicleAvailabilityWindow, VehicleCapability
from app.schemas.driver_schemas import DriverAvailabilityWindowCreate
from app.schemas.vehicle_schemas import VehicleAvailabilityWindowCreate


def test_driver_availability_window_relationship_is_bidirectional(session):
    window = DriverAvailabilityWindow(
        driver_id=1,
        start_time=datetime(2026, 4, 17, 8, 0),
        end_time=datetime(2026, 4, 17, 12, 0),
    )
    session.add(window)
    session.commit()

    db_window = session.exec(select(DriverAvailabilityWindow)).first()
    assert db_window is not None
    assert db_window.driver is not None
    assert db_window.driver.id == 1
    assert any(saved_window.id == db_window.id for saved_window in db_window.driver.availability_windows)


def test_vehicle_capability_and_window_relationships_are_bidirectional(session):
    capability = VehicleCapability(vehicle_id=1, capability="seat_type", value="captain")
    window = VehicleAvailabilityWindow(
        vehicle_id=1,
        start_time=datetime(2026, 4, 17, 13, 0),
        end_time=datetime(2026, 4, 17, 17, 0),
    )

    session.add(capability)
    session.add(window)
    session.commit()

    db_capability = session.exec(select(VehicleCapability)).first()
    assert db_capability is not None
    assert db_capability.vehicle is not None
    assert db_capability.vehicle.id == 1
    assert any(saved_capability.id == db_capability.id for saved_capability in db_capability.vehicle.capabilities)

    db_window = session.exec(select(VehicleAvailabilityWindow)).first()
    assert db_window is not None
    assert db_window.vehicle is not None
    assert db_window.vehicle.id == 1
    assert any(saved_window.id == db_window.id for saved_window in db_window.vehicle.availability_windows)


@pytest.mark.parametrize(
    "schema_cls,payload",
    [
        (
            DriverAvailabilityWindowCreate,
            {
                "driver_id": 1,
                "start_time": datetime(2026, 4, 17, 10, 0),
                "end_time": datetime(2026, 4, 17, 9, 0),
            },
        ),
        (
            VehicleAvailabilityWindowCreate,
            {
                "vehicle_id": 1,
                "start_time": datetime(2026, 4, 17, 18, 0),
                "end_time": datetime(2026, 4, 17, 18, 0),
            },
        ),
    ],
)
def test_availability_schemas_reject_invalid_intervals(schema_cls, payload):
    with pytest.raises(ValidationError):
        schema_cls(**payload)
