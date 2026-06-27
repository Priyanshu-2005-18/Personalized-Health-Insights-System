import { useState } from "react";

const STEPS = ["Profile", "Goals", "Wearables", "Baseline"];

const GOALS = [
  { id: "sleep", icon: "🌙", label: "Better sleep" },
  { id: "weight", icon: "⚖️", label: "Weight management" },
  { id: "stress", icon: "🧘", label: "Stress reduction" },
  { id: "fitness", icon: "🏃", label: "Fitness improvement" },
  { id: "energy", icon: "⚡", label: "More energy" },
  { id: "nutrition", icon: "🥗", label: "Healthier nutrition" },
];

const WEARABLES = [
  { id: "fitbit", name: "Fitbit", color: "#00B0B9" },
  { id: "apple", name: "Apple Health", color: "#FF3B30" },
  { id: "garmin", name: "Garmin", color: "#007CC3" },
  { id: "whoop", name: "WHOOP", color: "#1A1A1A" },
];

function ProgressBar({ current, total }) {
  return (
    <div style={{ marginBottom: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        {STEPS.map((s, i) => (
          <span
            key={s}
            style={{
              fontSize: 12,
              fontWeight: i === current ? 500 : 400,
              color: i <= current ? "#1D9E75" : "#888780",
            }}
          >
            {s}
          </span>
        ))}
      </div>
      <div style={{ height: 4, background: "#e5e5e5", borderRadius: 2, overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            width: `${((current + 1) / total) * 100}%`,
            background: "#1D9E75",
            borderRadius: 2,
            transition: "width 0.4s ease",
          }}
        />
      </div>
    </div>
  );
}

function StepProfile({ data, onChange }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, margin: 0 }}>Create your health profile</h2>
      <p style={{ fontSize: 14, color: "#888780", margin: 0 }}>
        This helps us personalise your baseline and recommendations.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {[
          { key: "firstName", label: "First name", type: "text", placeholder: "Alex" },
          { key: "lastName", label: "Last name", type: "text", placeholder: "Chen" },
          { key: "age", label: "Age", type: "number", placeholder: "32" },
          { key: "sex", label: "Biological sex", type: "select", options: ["Prefer not to say", "Male", "Female", "Other"] },
          { key: "height", label: "Height (cm)", type: "number", placeholder: "175" },
          { key: "weight", label: "Weight (kg)", type: "number", placeholder: "72" },
        ].map(({ key, label, type, placeholder, options }) => (
          <div key={key} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <label style={{ fontSize: 12, color: "#888780", fontWeight: 500 }}>{label}</label>
            {type === "select" ? (
              <select
                value={data[key] || ""}
                onChange={(e) => onChange(key, e.target.value)}
                style={{
                  padding: "8px 12px", borderRadius: 8, border: "0.5px solid rgba(0,0,0,0.2)",
                  fontSize: 14, background: "#fff", color: "#1a1a18",
                }}
              >
                {options.map((o) => <option key={o}>{o}</option>)}
              </select>
            ) : (
              <input
                type={type}
                placeholder={placeholder}
                value={data[key] || ""}
                onChange={(e) => onChange(key, e.target.value)}
                style={{
                  padding: "8px 12px", borderRadius: 8, border: "0.5px solid rgba(0,0,0,0.2)",
                  fontSize: 14, background: "#fff", color: "#1a1a18",
                }}
              />
            )}
          </div>
        ))}
      </div>
      <div>
        <label style={{ fontSize: 12, color: "#888780", fontWeight: 500, display: "block", marginBottom: 4 }}>
          Any existing conditions (optional)
        </label>
        <textarea
          rows={2}
          placeholder="e.g. Type 2 diabetes, hypertension…"
          value={data.conditions || ""}
          onChange={(e) => onChange("conditions", e.target.value)}
          style={{
            width: "100%", padding: "8px 12px", borderRadius: 8,
            border: "0.5px solid rgba(0,0,0,0.2)", fontSize: 14,
            resize: "vertical", fontFamily: "inherit", color: "#1a1a18",
          }}
        />
      </div>
    </div>
  );
}

function StepGoals({ selected, onToggle }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, margin: 0 }}>What are your health goals?</h2>
      <p style={{ fontSize: 14, color: "#888780", margin: 0 }}>Pick up to 3. We'll weight your insights accordingly.</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
        {GOALS.map(({ id, icon, label }) => {
          const active = selected.includes(id);
          return (
            <button
              key={id}
              onClick={() => onToggle(id)}
              style={{
                padding: "14px 12px", borderRadius: 10, cursor: "pointer",
                border: active ? "2px solid #1D9E75" : "0.5px solid rgba(0,0,0,0.15)",
                background: active ? "#E1F5EE" : "#fff",
                display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
                transition: "all 0.2s",
              }}
            >
              <span style={{ fontSize: 24 }}>{icon}</span>
              <span style={{ fontSize: 12, fontWeight: active ? 500 : 400, color: active ? "#085041" : "#1a1a18" }}>
                {label}
              </span>
            </button>
          );
        })}
      </div>
      {selected.length > 0 && (
        <p style={{ fontSize: 12, color: "#1D9E75", margin: 0 }}>
          ✓ {selected.length} goal{selected.length > 1 ? "s" : ""} selected
        </p>
      )}
    </div>
  );
}

function StepWearables({ connected, onToggle }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, margin: 0 }}>Connect your devices</h2>
      <p style={{ fontSize: 14, color: "#888780", margin: 0 }}>
        Link wearables to pull biometric data automatically. You can add more later.
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {WEARABLES.map(({ id, name, color }) => {
          const isConnected = connected.includes(id);
          return (
            <div
              key={id}
              style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "14px 16px", borderRadius: 10,
                border: isConnected ? "2px solid #1D9E75" : "0.5px solid rgba(0,0,0,0.15)",
                background: isConnected ? "#E1F5EE" : "#fff",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: color + "22", border: `1px solid ${color}44`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, fontWeight: 700, color,
                }}>
                  {name[0]}
                </div>
                <span style={{ fontSize: 14, fontWeight: 500, color: "#1a1a18" }}>{name}</span>
              </div>
              <button
                onClick={() => onToggle(id)}
                style={{
                  padding: "6px 14px", borderRadius: 8, fontSize: 12, cursor: "pointer",
                  border: isConnected ? "none" : "0.5px solid rgba(0,0,0,0.2)",
                  background: isConnected ? "#1D9E75" : "transparent",
                  color: isConnected ? "#fff" : "#1a1a18", fontWeight: 500,
                }}
              >
                {isConnected ? "Connected ✓" : "Connect"}
              </button>
            </div>
          );
        })}
      </div>
      <p style={{ fontSize: 12, color: "#888780", margin: 0 }}>
        No wearable? You can log data manually from your dashboard.
      </p>
    </div>
  );
}

function StepBaseline() {
  const metrics = [
    { label: "Average sleep", value: "7.2 hrs", trend: "+0.3" },
    { label: "Daily steps", value: "8,450", trend: "-1,200" },
    { label: "Resting HR", value: "68 bpm", trend: "stable" },
    { label: "Stress index", value: "54 / 100", trend: "+6" },
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, margin: 0 }}>Your health baseline</h2>
      <p style={{ fontSize: 14, color: "#888780", margin: 0 }}>
        We've calculated your starting point from the last 30 days of data.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {metrics.map(({ label, value, trend }) => (
          <div key={label} style={{
            background: "#f3f2ee", borderRadius: 10, padding: "14px 16px",
          }}>
            <p style={{ fontSize: 12, color: "#888780", margin: "0 0 6px" }}>{label}</p>
            <p style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px", color: "#1a1a18" }}>{value}</p>
            <p style={{
              fontSize: 11, margin: 0,
              color: trend.startsWith("+") ? "#D85A30" : trend === "stable" ? "#888780" : "#1D9E75",
            }}>
              {trend !== "stable" ? `${trend} vs population avg` : "Within population avg"}
            </p>
          </div>
        ))}
      </div>
      <div style={{
        background: "#EEEDFE", borderRadius: 10, padding: "14px 16px",
        borderLeft: "3px solid #7F77DD",
      }}>
        <p style={{ fontSize: 13, fontWeight: 500, color: "#3C3489", margin: "0 0 4px" }}>
          Your personalised health score: 74
        </p>
        <p style={{ fontSize: 12, color: "#534AB7", margin: 0 }}>
          This will update daily as new data comes in. Your first insights are ready.
        </p>
      </div>
    </div>
  );
}

export default function UserOnboarding() {
  const [step, setStep] = useState(0);
  const [profile, setProfile] = useState({});
  const [goals, setGoals] = useState([]);
  const [wearables, setWearables] = useState([]);

  const updateProfile = (key, val) => setProfile((p) => ({ ...p, [key]: val }));
  const toggleGoal = (id) => {
    setGoals((g) =>
      g.includes(id) ? g.filter((x) => x !== id) : g.length < 3 ? [...g, id] : g
    );
  };
  const toggleWearable = (id) =>
    setWearables((w) => (w.includes(id) ? w.filter((x) => x !== id) : [...w, id]));

  const canAdvance = () => {
    if (step === 0) return profile.firstName && profile.age;
    if (step === 1) return goals.length > 0;
    return true;
  };

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      maxWidth: 560, margin: "0 auto", padding: "2rem 1rem",
    }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <p style={{ fontSize: 11, color: "#888780", margin: "0 0 4px", textTransform: "uppercase", letterSpacing: "0.07em" }}>
          Health Insights
        </p>
        <h1 style={{ fontSize: 18, fontWeight: 500, margin: 0, color: "#1a1a18" }}>Get started</h1>
      </div>

      <ProgressBar current={step} total={STEPS.length} />

      <div style={{
        background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
        borderRadius: 12, padding: "1.5rem", marginBottom: "1rem",
      }}>
        {step === 0 && <StepProfile data={profile} onChange={updateProfile} />}
        {step === 1 && <StepGoals selected={goals} onToggle={toggleGoal} />}
        {step === 2 && <StepWearables connected={wearables} onToggle={toggleWearable} />}
        {step === 3 && <StepBaseline />}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          style={{
            padding: "10px 20px", borderRadius: 8, fontSize: 14, cursor: step === 0 ? "default" : "pointer",
            border: "0.5px solid rgba(0,0,0,0.2)", background: "transparent",
            color: step === 0 ? "#c0c0c0" : "#1a1a18",
          }}
        >
          Back
        </button>
        <button
          onClick={() => step < STEPS.length - 1 ? setStep((s) => s + 1) : null}
          disabled={!canAdvance()}
          style={{
            padding: "10px 24px", borderRadius: 8, fontSize: 14, cursor: canAdvance() ? "pointer" : "default",
            border: "none", background: canAdvance() ? "#1D9E75" : "#c0c0c0",
            color: "#fff", fontWeight: 500,
          }}
        >
          {step === STEPS.length - 1 ? "Go to dashboard →" : "Continue →"}
        </button>
      </div>
    </div>
  );
}
