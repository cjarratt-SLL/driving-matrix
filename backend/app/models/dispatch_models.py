from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class TripRequestStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class TripRunStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"


class TripRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    resident_id: int = Field(foreign_key="resident.id", index=True)
    pickup_location_id: int = Field(foreign_key="location.id")
    dropoff_location_id: int = Field(foreign_key="location.id")

    pickup_window_start: datetime = Field(sa_type=DateTime(timezone=True))
    pickup_window_end: datetime = Field(sa_type=DateTime(timezone=True))

    constraints: Optional[str] = None

    status: TripRequestStatus = Field(
        default=TripRequestStatus.PENDING,
        sa_type=SAEnum(TripRequestStatus, name="trip_request_status"),
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_type=DateTime(timezone=True))

    __table_args__ = (
        Index(
            "ix_trip_request_status_pickup_window",
            "status",
            "pickup_window_start",
            "pickup_window_end",
        ),
    )


class TripRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    window_start: datetime = Field(sa_type=DateTime(timezone=True))
    window_end: datetime = Field(sa_type=DateTime(timezone=True))

    driver_id: Optional[int] = Field(default=None, foreign_key="driver.id", index=True)
    vehicle_id: Optional[int] = Field(default=None, foreign_key="vehicle.id", index=True)

    status: TripRunStatus = Field(
        default=TripRunStatus.PLANNED,
        sa_type=SAEnum(TripRunStatus, name="trip_run_status"),
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, sa_type=DateTime(timezone=True))

    __table_args__ = (
        Index("ix_trip_run_window", "window_start", "window_end"),
    )


class RunAssignment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    run_id: int = Field(foreign_key="triprun.id", index=True)
    trip_request_id: int = Field(foreign_key="triprequest.id", index=True)

    stop_order: int = Field(index=True)
    planned_pickup_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    planned_dropoff_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("run_id", "trip_request_id", name="uq_run_assignment_run_request"),
        UniqueConstraint("run_id", "stop_order", name="uq_run_assignment_run_stop_order"),
        Index("ix_run_assignment_run_stop_order", "run_id", "stop_order"),
    )
