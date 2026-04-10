import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const API_USER_ROLE = import.meta.env.VITE_USER_ROLE?.toLowerCase();
const API_USER_ID = import.meta.env.VITE_USER_ID || "frontend-user";

function buildAuthHeaders(extraHeaders = {}) {
  const headers = {
    ...extraHeaders,
    "x-user-id": API_USER_ID,
  };

  if (API_USER_ROLE) {
    headers["x-user-role"] = API_USER_ROLE;
  }

  return headers;
}

const resourceConfig = {
  residents: {
    label: "Residents",
    endpoint: "/residents",
    emptyMessage: "No residents yet.",
    formFields: [
      { name: "first_name", label: "First name", type: "text", required: true },
      { name: "last_name", label: "Last name", type: "text", required: true },
      { name: "home_address", label: "Home address", type: "text" },
      { name: "is_active", label: "Active", type: "checkbox", defaultValue: true },
      {
        name: "rideshare_able",
        label: "Rideshare compatible",
        type: "checkbox",
        defaultValue: true,
      },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
    listItem: (resident) =>
      `${resident.first_name} ${resident.last_name} · ${resident.is_active ? "Active" : "Inactive"}`,
  },
  drivers: {
    label: "Drivers",
    endpoint: "/drivers",
    emptyMessage: "No drivers yet.",
    formFields: [
      { name: "first_name", label: "First name", type: "text", required: true },
      { name: "last_name", label: "Last name", type: "text", required: true },
      { name: "phone_number", label: "Phone number", type: "text" },
      { name: "vehicle_assigned", label: "Vehicle assigned", type: "text" },
      { name: "is_active", label: "Active", type: "checkbox", defaultValue: true },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
    listItem: (driver) =>
      `${driver.first_name} ${driver.last_name}${driver.phone_number ? ` · ${driver.phone_number}` : ""}`,
  },
  vehicles: {
    label: "Vehicles",
    endpoint: "/vehicles",
    emptyMessage: "No vehicles yet.",
    formFields: [
      { name: "name", label: "Name", type: "text", required: true },
      { name: "vehicle_type", label: "Vehicle type", type: "text" },
      { name: "capacity", label: "Capacity", type: "number", min: 1, defaultValue: 1 },
      {
        name: "wheelchair_accessible",
        label: "Wheelchair accessible",
        type: "checkbox",
        defaultValue: false,
      },
      { name: "license_plate", label: "License plate", type: "text" },
      { name: "is_active", label: "Active", type: "checkbox", defaultValue: true },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
    listItem: (vehicle) => `${vehicle.name} · Capacity ${vehicle.capacity}`,
  },
  locations: {
    label: "Locations",
    endpoint: "/locations",
    emptyMessage: "No locations yet.",
    formFields: [
      { name: "name", label: "Name", type: "text", required: true },
      { name: "address", label: "Address", type: "text", required: true },
      { name: "location_type", label: "Location type", type: "text", required: true },
      { name: "resident_id", label: "Resident ID", type: "number" },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
    listItem: (location) => `${location.name} · ${location.location_type}`,
  },
};

function defaultValues(fields) {
  return fields.reduce((acc, field) => {
    if (field.type === "checkbox") {
      acc[field.name] = field.defaultValue ?? false;
    } else if (field.type === "number") {
      acc[field.name] = field.defaultValue ?? "";
    } else {
      acc[field.name] = "";
    }
    return acc;
  }, {});
}

function cleanPayload(values, fields) {
  const payload = {};

  fields.forEach((field) => {
    const value = values[field.name];

    if (field.type === "checkbox") {
      payload[field.name] = Boolean(value);
      return;
    }

    if (field.type === "number") {
      payload[field.name] = value === "" ? null : Number(value);
      return;
    }

    payload[field.name] = value === "" ? null : value;
  });

  return payload;
}

function ResourcePanel({ config, records, loading, error, onRefresh, onCreate }) {
  const [formValues, setFormValues] = useState(() => defaultValues(config.formFields));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setFormValues(defaultValues(config.formFields));
  }, [config]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);

    try {
      await onCreate(cleanPayload(formValues, config.formFields));
      setFormValues(defaultValues(config.formFields));
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="panel">
      <header className="panel-header">
        <h2>{config.label}</h2>
        <button type="button" onClick={onRefresh} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>
      </header>

      {error ? <p className="error-text">{error}</p> : null}

      <ul className="record-list">
        {records.length === 0 ? <li className="empty-row">{config.emptyMessage}</li> : null}
        {records.map((record) => (
          <li key={record.id ?? `${config.label}-${Math.random()}`}>
            <span>{config.listItem(record)}</span>
            <code>#{record.id}</code>
          </li>
        ))}
      </ul>

      <form className="entry-form" onSubmit={handleSubmit}>
        {config.formFields.map((field) => (
          <label key={field.name}>
            <span>{field.label}</span>
            {field.type === "textarea" ? (
              <textarea
                value={formValues[field.name]}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, [field.name]: event.target.value }))
                }
              />
            ) : field.type === "checkbox" ? (
              <input
                type="checkbox"
                checked={Boolean(formValues[field.name])}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, [field.name]: event.target.checked }))
                }
              />
            ) : (
              <input
                type={field.type}
                value={formValues[field.name]}
                required={field.required}
                min={field.min}
                onChange={(event) =>
                  setFormValues((current) => ({ ...current, [field.name]: event.target.value }))
                }
              />
            )}
          </label>
        ))}

        <button type="submit" disabled={saving}>
          {saving ? "Saving..." : `Add ${config.label.slice(0, -1)}`}
        </button>
      </form>
    </section>
  );
}

function TripPanel({ dataSources, canMutateTrips }) {
  const [trips, setTrips] = useState([]);
  const [tripError, setTripError] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    resident_id: "",
    pickup_location_id: "",
    dropoff_location_id: "",
    pickup_time: "",
    dropoff_time: "",
    driver_id: "",
    vehicle_id: "",
  });

  const loadTrips = async () => {
    setLoading(true);
    setTripError("");
    try {
      const response = await fetch(`${API_BASE_URL}/trips`, {
        headers: buildAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error(`Unable to load trips (${response.status})`);
      }
      setTrips(await response.json());
    } catch (error) {
      setTripError(error.message || "Unable to load trips");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTrips();
  }, []);

  const selectableData = useMemo(
    () => ({
      residents: dataSources.residents,
      locations: dataSources.locations,
      drivers: dataSources.drivers,
      vehicles: dataSources.vehicles,
    }),
    [dataSources],
  );

  const createTrip = async (event) => {
    event.preventDefault();
    if (!canMutateTrips) {
      setTripError("You have read-only access for trip updates.");
      return;
    }

    setSaving(true);
    setTripError("");
    try {
      const payload = {
        resident_id: Number(form.resident_id),
        pickup_location_id: Number(form.pickup_location_id),
        dropoff_location_id: Number(form.dropoff_location_id),
        pickup_time: new Date(form.pickup_time).toISOString(),
        dropoff_time: new Date(form.dropoff_time).toISOString(),
        driver_id: form.driver_id ? Number(form.driver_id) : null,
        vehicle_id: form.vehicle_id ? Number(form.vehicle_id) : null,
      };

      const response = await fetch(`${API_BASE_URL}/trips`, {
        method: "POST",
        headers: buildAuthHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const details = await response.json().catch(() => ({}));
        throw new Error(details.detail?.detail || details.detail || `Unable to create trip (${response.status})`);
      }

      setForm({
        resident_id: "",
        pickup_location_id: "",
        dropoff_location_id: "",
        pickup_time: "",
        dropoff_time: "",
        driver_id: "",
        vehicle_id: "",
      });
      await loadTrips();
    } catch (error) {
      setTripError(error.message || "Unable to create trip");
    } finally {
      setSaving(false);
    }
  };

  const recalculateTripEstimate = async (tripId) => {
    if (!canMutateTrips) {
      setTripError("You have read-only access for estimate recalculation.");
      return;
    }

    setTripError("");

    try {
      const response = await fetch(`${API_BASE_URL}/trips/${tripId}/reestimate`, {
        method: "POST",
        headers: buildAuthHeaders(),
      });

      if (!response.ok) {
        const details = await response.json().catch(() => ({}));
        throw new Error(details.detail || `Unable to re-estimate trip (${response.status})`);
      }

      await loadTrips();
    } catch (error) {
      setTripError(error.message || "Unable to re-estimate trip");
    }
  };

  return (
    <section className="panel trip-panel">
      <header className="panel-header">
        <h2>Trips</h2>
        <button type="button" onClick={loadTrips} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>
      </header>

      {tripError ? <p className="error-text">{tripError}</p> : null}
      {!canMutateTrips ? <p className="status-pill">Read-only: trip mutations disabled for this role.</p> : null}

      <ul className="record-list">
        {trips.length === 0 ? <li className="empty-row">No trips yet.</li> : null}
        {trips.map((trip) => (
          <li key={trip.id}>
            <span>
              Resident #{trip.resident_id} · {new Date(trip.pickup_time).toLocaleString()} →{" "}
              {new Date(trip.dropoff_time).toLocaleString()}
            </span>
            <div className="trip-row-actions">
              <button
                type="button"
                onClick={() => recalculateTripEstimate(trip.id)}
                disabled={!canMutateTrips}
                title={canMutateTrips ? "Recalculate estimate" : "Read-only role"}
              >
                Re-estimate
              </button>
              <code>#{trip.id}</code>
            </div>
          </li>
        ))}
      </ul>

      <form className="entry-form" onSubmit={createTrip}>
        <fieldset disabled={!canMutateTrips}>
        <label>
          <span>Resident</span>
          <select
            value={form.resident_id}
            required
            onChange={(event) => setForm((current) => ({ ...current, resident_id: event.target.value }))}
          >
            <option value="">Select resident</option>
            {selectableData.residents.map((resident) => (
              <option key={resident.id} value={resident.id}>
                {resident.first_name} {resident.last_name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Pickup location</span>
          <select
            value={form.pickup_location_id}
            required
            onChange={(event) =>
              setForm((current) => ({ ...current, pickup_location_id: event.target.value }))
            }
          >
            <option value="">Select location</option>
            {selectableData.locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Dropoff location</span>
          <select
            value={form.dropoff_location_id}
            required
            onChange={(event) =>
              setForm((current) => ({ ...current, dropoff_location_id: event.target.value }))
            }
          >
            <option value="">Select location</option>
            {selectableData.locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Pickup time</span>
          <input
            type="datetime-local"
            value={form.pickup_time}
            required
            onChange={(event) => setForm((current) => ({ ...current, pickup_time: event.target.value }))}
          />
        </label>

        <label>
          <span>Dropoff time</span>
          <input
            type="datetime-local"
            value={form.dropoff_time}
            required
            onChange={(event) => setForm((current) => ({ ...current, dropoff_time: event.target.value }))}
          />
        </label>

        <label>
          <span>Driver (optional)</span>
          <select
            value={form.driver_id}
            onChange={(event) => setForm((current) => ({ ...current, driver_id: event.target.value }))}
          >
            <option value="">Unassigned</option>
            {selectableData.drivers.map((driver) => (
              <option key={driver.id} value={driver.id}>
                {driver.first_name} {driver.last_name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Vehicle (optional)</span>
          <select
            value={form.vehicle_id}
            onChange={(event) => setForm((current) => ({ ...current, vehicle_id: event.target.value }))}
          >
            <option value="">Unassigned</option>
            {selectableData.vehicles.map((vehicle) => (
              <option key={vehicle.id} value={vehicle.id}>
                {vehicle.name}
              </option>
            ))}
          </select>
        </label>

        <button type="submit" disabled={saving || !canMutateTrips}>
          {saving ? "Saving..." : "Create Trip"}
        </button>
        </fieldset>
      </form>
    </section>
  );
}

function App() {
  const [apiStatus, setApiStatus] = useState("Checking backend...");
  const [data, setData] = useState({
    residents: [],
    drivers: [],
    vehicles: [],
    locations: [],
  });
  const [errors, setErrors] = useState({});
  const [loadingStates, setLoadingStates] = useState({});
  const [authPolicy, setAuthPolicy] = useState({
    default_role: "viewer",
    trip_mutation_roles: [],
  });
  const activeUserRole = API_USER_ROLE || authPolicy.default_role;
  const canMutateTrips = authPolicy.trip_mutation_roles.includes(activeUserRole);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        headers: buildAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = await response.json();
      setApiStatus(`Backend status: ${payload.status} (${API_BASE_URL})`);
    } catch (error) {
      setApiStatus(`Backend connection failed: ${error.message || String(error)}`);
    }
  };

  const fetchAuthPolicy = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/policy`, {
        headers: buildAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Unable to load auth policy (${response.status})`);
      }

      const payload = await response.json();
      setAuthPolicy(payload);
    } catch {
      setApiStatus((current) => `${current} · Auth policy fallback active`);
    }
  };

  const fetchResource = async (key) => {
    const config = resourceConfig[key];
    if (!config) {
      return;
    }

    setLoadingStates((current) => ({ ...current, [key]: true }));
    setErrors((current) => ({ ...current, [key]: "" }));

    try {
      const response = await fetch(`${API_BASE_URL}${config.endpoint}`, {
        headers: buildAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error(`Unable to load ${config.label.toLowerCase()} (${response.status})`);
      }
      const payload = await response.json();
      setData((current) => ({ ...current, [key]: payload }));
    } catch (error) {
      setErrors((current) => ({ ...current, [key]: error.message || "Request failed" }));
    } finally {
      setLoadingStates((current) => ({ ...current, [key]: false }));
    }
  };

  const createResource = async (key, payload) => {
    const config = resourceConfig[key];

    const response = await fetch(`${API_BASE_URL}${config.endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const details = await response.json().catch(() => ({}));
      throw new Error(details.detail || `Unable to create ${config.label.slice(0, -1).toLowerCase()}`);
    }

    await fetchResource(key);
  };

  useEffect(() => {
    checkHealth();
    fetchAuthPolicy();
    Object.keys(resourceConfig).forEach((key) => {
      fetchResource(key);
    });
  }, []);

  return (
    <main className="app-shell">
      <header className="app-header">
        <h1>Driving Matrix</h1>
        <p>Frontend connector basics for core entities and trip creation.</p>
        <p className="status-pill">{apiStatus}</p>
        <p className="status-pill">Role: {activeUserRole}</p>
      </header>

      <section className="grid-layout">
        {Object.entries(resourceConfig).map(([key, config]) => (
          <ResourcePanel
            key={key}
            config={config}
            records={data[key]}
            loading={Boolean(loadingStates[key])}
            error={errors[key]}
            onRefresh={() => fetchResource(key)}
            onCreate={(payload) => createResource(key, payload)}
          />
        ))}
        <TripPanel dataSources={data} canMutateTrips={canMutateTrips} />
      </section>
    </main>
  );
}

export default App;
