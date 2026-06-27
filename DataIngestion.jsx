import { useState, useEffect } from "react";

const SOURCES = [
  {
    id: "fitbit",
    name: "Fitbit",
    type: "Wearable",
    status: "active",
    lastSync: "2 min ago",
    metrics: ["steps", "heart_rate", "sleep", "calories"],
    recordsToday: 1440,
    color: "#00B0B9",
  },
  {
    id: "apple",
    name: "Apple Health",
    type: "Wearable",
    status: "active",
    lastSync: "5 min ago",
    metrics: ["steps", "hrv", "blood_oxygen", "workouts"],
    recordsToday: 864,
    color: "#FF3B30",
  },
  {
    id: "food",
    name: "Open Food Facts",
    type: "Nutrition API",
    status: "active",
    lastSync: "On demand",
    metrics: ["calories", "macros", "micronutrients"],
    recordsToday: 12,
    color: "#639922",
  },
  {
    id: "manual",
    name: "Manual logs",
    type: "User input",
    status: "active",
    lastSync: "3 hrs ago",
    metrics: ["mood", "energy", "water", "notes"],
    recordsToday: 3,
    color: "#7F77DD",
  },
  {
    id: "garmin",
    name: "Garmin",
    type: "Wearable",
    status: "disconnected",
    lastSync: "—",
    metrics: ["gps", "vo2max", "stress", "body_battery"],
    recordsToday: 0,
    color: "#007CC3",
  },
];

const PIPELINE_STAGES = [
  { id: "ingest", label: "Ingest", icon: "⬇", desc: "Raw data pulled from APIs" },
  { id: "validate", label: "Validate", icon: "✓", desc: "Schema & range checks" },
  { id: "normalize", label: "Normalize", icon: "⇄", desc: "Units & time zones aligned" },
  { id: "store", label: "Store", icon: "◉", desc: "Written to InfluxDB + Postgres" },
  { id: "feature", label: "Features", icon: "∫", desc: "ML features computed" },
];

const RECENT_EVENTS = [
  { time: "09:42", source: "Fitbit", type: "sync", message: "1,440 records synced successfully", ok: true },
  { time: "09:40", source: "Apple Health", type: "sync", message: "HRV batch: 288 readings ingested", ok: true },
  { time: "09:38", source: "Validator", type: "warning", message: "3 HR values out of range (>220 bpm) — dropped", ok: false },
  { time: "09:31", source: "Open Food Facts", type: "sync", message: "Lunch entry matched: 'Brown rice bowl'", ok: true },
  { time: "09:15", source: "Normalizer", type: "info", message: "Timezone adjusted: UTC+5:30 → UTC", ok: true },
  { time: "08:59", source: "Garmin", type: "error", message: "OAuth token expired — reconnect required", ok: false },
];

function StatusDot({ status }) {
  const color = status === "active" ? "#1D9E75" : status === "warning" ? "#BA7517" : "#D85A30";
  return (
    <span style={{
      display: "inline-block", width: 8, height: 8, borderRadius: "50%",
      background: color, marginRight: 6,
      boxShadow: status === "active" ? `0 0 0 3px ${color}33` : "none",
    }} />
  );
}

function PipelineFlow({ activeStage }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, overflowX: "auto", paddingBottom: 4 }}>
      {PIPELINE_STAGES.map((stage, i) => {
        const done = i < activeStage;
        const active = i === activeStage;
        return (
          <div key={stage.id} style={{ display: "flex", alignItems: "center" }}>
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center", gap: 6, minWidth: 90,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: "50%",
                background: done ? "#1D9E75" : active ? "#E1F5EE" : "#f3f2ee",
                border: active ? "2px solid #1D9E75" : done ? "none" : "0.5px solid rgba(0,0,0,0.15)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 16, color: done ? "#fff" : active ? "#1D9E75" : "#888780",
                transition: "all 0.3s",
              }}>
                {done ? "✓" : stage.icon}
              </div>
              <span style={{ fontSize: 11, fontWeight: active ? 500 : 400, color: active ? "#1D9E75" : "#888780", textAlign: "center" }}>
                {stage.label}
              </span>
              <span style={{ fontSize: 10, color: "#888780", textAlign: "center", maxWidth: 80 }}>
                {stage.desc}
              </span>
            </div>
            {i < PIPELINE_STAGES.length - 1 && (
              <div style={{
                flex: 1, height: 2, minWidth: 20,
                background: done ? "#1D9E75" : "#e5e5e5",
                margin: "-18px 4px 0",
                transition: "background 0.3s",
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function DataIngestion() {
  const [activeStage, setActiveStage] = useState(2);

  useEffect(() => {
    const id = setInterval(() => {
      setActiveStage((s) => (s >= PIPELINE_STAGES.length - 1 ? 0 : s + 1));
    }, 2000);
    return () => clearInterval(id);
  }, []);

  const totalToday = SOURCES.reduce((s, x) => s + x.recordsToday, 0);

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      color: "#1a1a18", padding: "1.5rem 0", maxWidth: 900,
    }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <p style={{ fontSize: 11, color: "#888780", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.07em" }}>
          Module 2
        </p>
        <h1 style={{ fontSize: 22, fontWeight: 500, margin: 0 }}>Data ingestion</h1>
        <p style={{ fontSize: 13, color: "#888780", margin: "4px 0 0" }}>
          {totalToday.toLocaleString()} records processed today · Last run 2 min ago
        </p>
      </div>

      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 12 }}>
        {[
          { label: "Active sources", value: SOURCES.filter((s) => s.status === "active").length },
          { label: "Records today", value: totalToday.toLocaleString() },
          { label: "Validation rate", value: "99.8%" },
          { label: "Avg latency", value: "1.4 s" },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: "#f3f2ee", borderRadius: 8, padding: "10px 14px" }}>
            <p style={{ fontSize: 12, color: "#888780", margin: "0 0 2px" }}>{label}</p>
            <p style={{ fontSize: 18, fontWeight: 500, margin: 0 }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Pipeline flow */}
      <div style={{
        background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
        borderRadius: 12, padding: "1.25rem", marginBottom: 12,
      }}>
        <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 1.25rem", color: "#1a1a18" }}>Pipeline status</p>
        <PipelineFlow activeStage={activeStage} />
      </div>

      {/* Source cards */}
      <div style={{
        background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
        borderRadius: 12, padding: "1.25rem", marginBottom: 12,
      }}>
        <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 1rem" }}>Connected sources</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {SOURCES.map((src) => (
            <div key={src.id} style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "12px 14px", borderRadius: 10, background: "#f9f9f8",
              border: "0.5px solid rgba(0,0,0,0.08)",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: src.color + "22", display: "flex", alignItems: "center",
                  justifyContent: "center", fontSize: 14, fontWeight: 700, color: src.color,
                }}>
                  {src.name[0]}
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <StatusDot status={src.status} />
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{src.name}</span>
                    <span style={{
                      fontSize: 10, padding: "2px 7px", borderRadius: 4,
                      background: "#f3f2ee", color: "#888780",
                    }}>
                      {src.type}
                    </span>
                  </div>
                  <p style={{ fontSize: 11, color: "#888780", margin: "2px 0 0" }}>
                    {src.metrics.join(" · ")}
                  </p>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>{src.recordsToday.toLocaleString()}</p>
                <p style={{ fontSize: 11, color: "#888780", margin: "2px 0 0" }}>
                  {src.status === "disconnected" ? "Disconnected" : `Synced ${src.lastSync}`}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Event log */}
      <div style={{
        background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
        borderRadius: 12, padding: "1.25rem",
      }}>
        <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 1rem" }}>Event log</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {RECENT_EVENTS.map((ev, i) => (
            <div key={i} style={{
              display: "flex", gap: 12, padding: "10px 0",
              borderBottom: i < RECENT_EVENTS.length - 1 ? "0.5px solid rgba(0,0,0,0.08)" : "none",
            }}>
              <span style={{ fontSize: 11, color: "#888780", minWidth: 36, paddingTop: 1 }}>{ev.time}</span>
              <span style={{
                fontSize: 11, fontWeight: 500, minWidth: 90,
                color: ev.type === "error" ? "#D85A30" : ev.type === "warning" ? "#BA7517" : "#1D9E75",
              }}>
                {ev.source}
              </span>
              <span style={{ fontSize: 12, color: ev.ok ? "#1a1a18" : "#888780" }}>{ev.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
