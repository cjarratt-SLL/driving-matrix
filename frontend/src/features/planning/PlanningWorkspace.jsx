import { useCallback, useEffect, useMemo, useState } from "react";
import "./PlanningWorkspace.css";

function parseRunIdFromSearch(search) {
  const params = new URLSearchParams(search);
  const rawRunId = params.get("runId");
  if (!rawRunId) {
    return null;
  }

  const parsed = Number(rawRunId);
  return Number.isFinite(parsed) ? parsed : null;
}

function buildRunIdUrl(runId) {
  const params = new URLSearchParams(window.location.search);
  if (runId == null) {
    params.delete("runId");
  } else {
    params.set("runId", String(runId));
  }

  const nextQuery = params.toString();
  return `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}${window.location.hash}`;
}

function useRunIdFromUrl() {
  const [runId, setRunId] = useState(() => parseRunIdFromSearch(window.location.search));

  useEffect(() => {
    const onPopState = () => {
      setRunId(parseRunIdFromSearch(window.location.search));
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const updateRunId = useCallback((nextRunId, replace = false) => {
    setRunId(nextRunId);
    const nextUrl = buildRunIdUrl(nextRunId);

    if (replace) {
      window.history.replaceState(null, "", nextUrl);
      return;
    }

    window.history.pushState(null, "", nextUrl);
  }, []);

  return [runId, updateRunId];
}

function formatTripSummary(trip) {
  return `Resident #${trip.resident_id} · ${new Date(trip.pickup_time).toLocaleString()}`;
}

function PlanningControlsPanel({
  canMutateTrips,
  dataSources,
  createRun,
  saving,
  listError,
  createError,
  onCreateErrorClear,
}) {
  const [form, setForm] = useState({
    resident_id: "",
    pickup_location_id: "",
    dropoff_location_id: "",
    pickup_time: "",
    dropoff_time: "",
    driver_id: "",
    vehicle_id: "",
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!canMutateTrips) {
      return;
    }

    onCreateErrorClear();

    const payload = {
      resident_id: Number(form.resident_id),
      pickup_location_id: Number(form.pickup_location_id),
      dropoff_location_id: Number(form.dropoff_location_id),
      pickup_time: new Date(form.pickup_time).toISOString(),
      dropoff_time: new Date(form.dropoff_time).toISOString(),
      driver_id: form.driver_id ? Number(form.driver_id) : null,
      vehicle_id: form.vehicle_id ? Number(form.vehicle_id) : null,
    };

    const createdRun = await createRun(payload);
    if (createdRun) {
      setForm({
        resident_id: "",
        pickup_location_id: "",
        dropoff_location_id: "",
        pickup_time: "",
        dropoff_time: "",
        driver_id: "",
        vehicle_id: "",
      });
    }
  };

  return (
    <section className="panel planning-region planning-controls-panel">
      <header className="panel-header">
        <h2>Planning Controls</h2>
      </header>

      {!canMutateTrips ? <p className="status-pill">Read-only: run creation is disabled.</p> : null}
      {listError ? <p className="error-text">{listError}</p> : null}
      {createError ? <p className="error-text">{createError}</p> : null}

      <form className="entry-form" onSubmit={handleSubmit}>
        <fieldset disabled={!canMutateTrips || saving}>
          <label>
            <span>Resident</span>
            <select
              value={form.resident_id}
              required
              onChange={(event) => setForm((current) => ({ ...current, resident_id: event.target.value }))}
            >
              <option value="">Select resident</option>
              {dataSources.residents.map((resident) => (
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
              {dataSources.locations.map((location) => (
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
              {dataSources.locations.map((location) => (
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
              {dataSources.drivers.map((driver) => (
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
              {dataSources.vehicles.map((vehicle) => (
                <option key={vehicle.id} value={vehicle.id}>
                  {vehicle.name}
                </option>
              ))}
            </select>
          </label>

          <button type="submit" disabled={saving || !canMutateTrips}>
            {saving ? "Saving..." : "Create Run"}
          </button>
        </fieldset>
      </form>
    </section>
  );
}

function PlanningRunsList({ runs, loading, selectedRunId, onSelectRun, onRefresh }) {
  return (
    <section className="panel planning-region planning-runs-list">
      <header className="panel-header">
        <h2>Planning Runs</h2>
        <button type="button" onClick={onRefresh} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>
      </header>

      <ul className="record-list planning-run-list-items">
        {runs.length === 0 ? <li className="empty-row">No runs yet.</li> : null}
        {runs.map((run) => (
          <li key={run.id}>
            <button
              type="button"
              className={`run-list-item-button ${selectedRunId === run.id ? "is-selected" : ""}`}
              onClick={() => onSelectRun(run.id)}
            >
              <span>{formatTripSummary(run)}</span>
              <code>#{run.id}</code>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function PlanningRunDetailsPanel({ run, canMutateTrips, onReestimate, reestimatingRunId, reestimateError }) {
  return (
    <section className="panel planning-region planning-run-details-panel">
      <header className="panel-header">
        <h2>Run Details</h2>
      </header>

      {reestimateError ? <p className="error-text">{reestimateError}</p> : null}

      {!run ? (
        <p className="empty-row">Select a run from the list to view details.</p>
      ) : (
        <div className="planning-run-details">
          <p><strong>Run ID:</strong> #{run.id}</p>
          <p><strong>Resident:</strong> #{run.resident_id}</p>
          <p><strong>Pickup:</strong> {new Date(run.pickup_time).toLocaleString()}</p>
          <p><strong>Dropoff:</strong> {new Date(run.dropoff_time).toLocaleString()}</p>
          <p><strong>Driver:</strong> {run.driver_id ? `#${run.driver_id}` : "Unassigned"}</p>
          <p><strong>Vehicle:</strong> {run.vehicle_id ? `#${run.vehicle_id}` : "Unassigned"}</p>
          <p><strong>Distance (meters):</strong> {run.estimated_distance_meters ?? "N/A"}</p>
          <p><strong>Duration (seconds):</strong> {run.estimated_duration_seconds ?? "N/A"}</p>
          <button
            type="button"
            onClick={() => onReestimate(run.id)}
            disabled={!canMutateTrips || reestimatingRunId === run.id}
            title={canMutateTrips ? "Recalculate estimate" : "Read-only role"}
          >
            {reestimatingRunId === run.id ? "Re-estimating..." : "Re-estimate Run"}
          </button>
        </div>
      )}
    </section>
  );
}

function PlanningWorkspace({ apiBaseUrl, buildAuthHeaders, dataSources, canMutateTrips }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [reestimatingRunId, setReestimatingRunId] = useState(null);
  const [listError, setListError] = useState("");
  const [createError, setCreateError] = useState("");
  const [reestimateError, setReestimateError] = useState("");
  const [selectedRunId, setSelectedRunIdInUrl] = useRunIdFromUrl();
  const [mobileTab, setMobileTab] = useState("controls");
  const [tabletDetailsExpanded, setTabletDetailsExpanded] = useState(false);

  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) || null,
    [runs, selectedRunId],
  );

  const loadRuns = useCallback(async () => {
    setLoading(true);
    setListError("");

    try {
      const response = await fetch(`${apiBaseUrl}/trips`, {
        headers: buildAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Unable to load runs (${response.status})`);
      }

      const payload = await response.json();
      setRuns(payload);
    } catch (loadError) {
      setListError(loadError.message || "Unable to load runs");
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, buildAuthHeaders]);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  useEffect(() => {
    if (selectedRunId == null) {
      return;
    }

    const stillExists = runs.some((run) => run.id === selectedRunId);
    if (!stillExists) {
      setSelectedRunIdInUrl(null, true);
    }
  }, [runs, selectedRunId, setSelectedRunIdInUrl]);

  const handleSelectRun = (runId) => {
    setSelectedRunIdInUrl(runId, false);
    setMobileTab("details");
    setTabletDetailsExpanded(true);
  };

  const createRun = async (payload) => {
    if (!canMutateTrips) {
      setCreateError("You have read-only access for run creation.");
      return null;
    }

    setSaving(true);
    setCreateError("");

    try {
      const response = await fetch(`${apiBaseUrl}/trips`, {
        method: "POST",
        headers: buildAuthHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const details = await response.json().catch(() => ({}));
        throw new Error(details.detail?.detail || details.detail || `Unable to create run (${response.status})`);
      }

      const createdRun = await response.json();
      await loadRuns();
      handleSelectRun(createdRun.id);
      return createdRun;
    } catch (createRunError) {
      setCreateError(createRunError.message || "Unable to create run");
      return null;
    } finally {
      setSaving(false);
    }
  };

  const reestimateRun = async (runId) => {
    if (!canMutateTrips) {
      setReestimateError("You have read-only access for estimate recalculation.");
      return;
    }

    setReestimatingRunId(runId);
    setReestimateError("");

    try {
      const response = await fetch(`${apiBaseUrl}/trips/${runId}/reestimate`, {
        method: "POST",
        headers: buildAuthHeaders(),
      });

      if (!response.ok) {
        const details = await response.json().catch(() => ({}));
        throw new Error(details.detail || `Unable to re-estimate run (${response.status})`);
      }

      await loadRuns();
    } catch (reestimateRunError) {
      setReestimateError(reestimateRunError.message || "Unable to re-estimate run");
    } finally {
      setReestimatingRunId(null);
    }
  };

  const rootClassName = `planning-workspace ${tabletDetailsExpanded ? "details-expanded" : ""}`;

  return (
    <section className={rootClassName}>
      <nav className="planning-mobile-tabs" aria-label="Planning workspace sections">
        <button
          type="button"
          className={mobileTab === "controls" ? "is-active" : ""}
          onClick={() => setMobileTab("controls")}
        >
          Controls
        </button>
        <button
          type="button"
          className={mobileTab === "runs" ? "is-active" : ""}
          onClick={() => setMobileTab("runs")}
        >
          Runs
        </button>
        <button
          type="button"
          className={mobileTab === "details" ? "is-active" : ""}
          onClick={() => setMobileTab("details")}
        >
          Details
        </button>
      </nav>

      <div className="planning-tablet-details-toggle-wrap">
        <button
          type="button"
          className="planning-tablet-details-toggle"
          onClick={() => setTabletDetailsExpanded((current) => !current)}
        >
          {tabletDetailsExpanded ? "Hide Details" : "Show Details"}
        </button>
      </div>

      <div className={`planning-controls-slot ${mobileTab === "controls" ? "mobile-active" : ""}`}>
        <PlanningControlsPanel
          canMutateTrips={canMutateTrips}
          dataSources={dataSources}
          createRun={createRun}
          saving={saving}
          listError={listError}
          createError={createError}
          onCreateErrorClear={() => setCreateError("")}
        />
      </div>

      <div className={`planning-runs-slot ${mobileTab === "runs" ? "mobile-active" : ""}`}>
        <PlanningRunsList
          runs={runs}
          loading={loading}
          selectedRunId={selectedRunId}
          onSelectRun={handleSelectRun}
          onRefresh={loadRuns}
        />
      </div>

      <div className={`planning-details-slot ${mobileTab === "details" ? "mobile-active" : ""}`}>
        <PlanningRunDetailsPanel
          run={selectedRun}
          canMutateTrips={canMutateTrips}
          onReestimate={reestimateRun}
          reestimatingRunId={reestimatingRunId}
          reestimateError={reestimateError}
        />
      </div>
    </section>
  );
}

export default PlanningWorkspace;
