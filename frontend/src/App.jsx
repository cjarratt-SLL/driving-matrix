import { useEffect, useState } from "react";

function App() {
  const [apiStatus, setApiStatus] = useState("Checking backend...");
  const [apiError, setApiError] = useState("");

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch("http://127.0.0.1:8000/health");

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        setApiStatus(`Backend status: ${data.status}`);
        setApiError("");
      } catch (error) {
        setApiStatus("Backend connection failed");
        setApiError(error.message || String(error));
      }
    }

    checkBackend();
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        margin: 0,
        padding: "32px",
        fontFamily: "Arial, sans-serif",
        backgroundColor: "#f4f7fb",
        color: "#1f2937",
      }}
    >
      <div
        style={{
          maxWidth: "900px",
          margin: "0 auto",
          backgroundColor: "#564ac7",
          borderRadius: "16px",
          padding: "32px",
          boxShadow: "0 10px 30px rgba(0,0,0,0.08)",
        }}
      >
        <h1 style={{ marginTop: 0 }}>Driving Matrix</h1>

        <p style={{ fontSize: "18px", lineHeight: 1.6 }}>
          Transportation scheduling and dispatch coordination for resident support.
        </p>

        <section style={{ marginTop: "24px" }}>
          <h2>API Connection</h2>
          <p>{apiStatus}</p>
          {apiError ? (
            <p style={{ color: "#b91c1c" }}>Error: {apiError}</p>
          ) : null}
        </section>

        <section style={{ marginTop: "32px" }}>
          <h2>Planned Modules</h2>
          <ul style={{ lineHeight: 1.8 }}>
            <li>Resident scheduling</li>
            <li>Driver and vehicle assignment</li>
            <li>Trip optimization</li>
            <li>Live dispatch updates</li>
            <li>Reporting and history</li>
            <li>Role-based secure access</li>
          </ul>
        </section>
      </div>
    </main>
  );
}

export default App;