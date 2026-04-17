BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS triprequest (
    id INTEGER PRIMARY KEY,
    resident_id INTEGER NOT NULL,
    pickup_location_id INTEGER NOT NULL,
    dropoff_location_id INTEGER NOT NULL,
    pickup_window_start DATETIME NOT NULL,
    pickup_window_end DATETIME NOT NULL,
    constraints TEXT,
    status VARCHAR(11) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY(resident_id) REFERENCES resident (id),
    FOREIGN KEY(pickup_location_id) REFERENCES location (id),
    FOREIGN KEY(dropoff_location_id) REFERENCES location (id)
);

CREATE TABLE IF NOT EXISTS triprun (
    id INTEGER PRIMARY KEY,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    driver_id INTEGER,
    vehicle_id INTEGER,
    status VARCHAR(9) NOT NULL DEFAULT 'planned',
    created_at DATETIME NOT NULL,
    FOREIGN KEY(driver_id) REFERENCES driver (id),
    FOREIGN KEY(vehicle_id) REFERENCES vehicle (id)
);

CREATE TABLE IF NOT EXISTS runassignment (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL,
    trip_request_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    planned_pickup_at DATETIME,
    planned_dropoff_at DATETIME,
    CONSTRAINT uq_run_assignment_run_request UNIQUE (run_id, trip_request_id),
    CONSTRAINT uq_run_assignment_run_stop_order UNIQUE (run_id, stop_order),
    FOREIGN KEY(run_id) REFERENCES triprun (id),
    FOREIGN KEY(trip_request_id) REFERENCES triprequest (id)
);

-- request status and pickup-window querying
CREATE INDEX IF NOT EXISTS ix_trip_request_status_pickup_window
    ON triprequest (status, pickup_window_start, pickup_window_end);
CREATE INDEX IF NOT EXISTS ix_triprequest_resident_id ON triprequest (resident_id);

-- run time-window lookup
CREATE INDEX IF NOT EXISTS ix_trip_run_window ON triprun (window_start, window_end);
CREATE INDEX IF NOT EXISTS ix_triprun_driver_id ON triprun (driver_id);
CREATE INDEX IF NOT EXISTS ix_triprun_vehicle_id ON triprun (vehicle_id);

-- assignment uniqueness and sequencing
CREATE INDEX IF NOT EXISTS ix_run_assignment_run_stop_order
    ON runassignment (run_id, stop_order);
CREATE INDEX IF NOT EXISTS ix_runassignment_trip_request_id ON runassignment (trip_request_id);

COMMIT;
