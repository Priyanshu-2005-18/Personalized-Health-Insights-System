import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";

const MODELS = [
  {
    id: "sleep_clf",
    name: "Sleep quality classifier",
    type: "XGBoost",
    status: "production",
    accuracy: 87.3,
    f1: 0.85,
    lastTrained: "2 days ago",
    features: ["sleep_hours", "hrv_avg", "steps_lag1", "stress_index", "caffeine_pm"],
    version: "v4.2",
  },
  {
    id: "lstm_trend",
    name: "Activity trend predictor",
    type: "LSTM",
    status: "production",
    accuracy: 91.2,
    f1: 0.89,
    lastTrained: "5 days ago",
    features: ["steps_7d", "calories_7d", "active_min", "resting_hr", "weekday"],
    version: "v2.1",
  },
  {
    id: "risk_flag",
    name: "Health risk classifier",
    type: "XGBoost",
    status: "staging",
    accuracy: 79.6,
    f1: 0.78,
    lastTrained: "1 day ago",
    features: ["bmi", "resting_hr", "sleep_debt_7d", "stress_avg_14d", "age"],
    version: "v1.3",
  },
  {
    id: "collab_filter",
    name: "Recommendation engine",
    type: "Collaborative filtering",
    status: "production",
    accuracy: 84.1,
    f1: 0.82,
    lastTrained: "7 days ago",
    features: ["user_embeddings", "interaction_history", "goal_vector"],
    version: "v3.0",
  },
];

const trainingHistory = [
  { run: "Run 1", sleep: 71.2, activity: 80.5, risk: 68.3 },
  { run: "Run 2", sleep: 75.8, activity: 83.1, risk: 71.0 },
  { run: "Run 3", sleep: 79.4, activity: 86.7, risk: 73.5 },
  { run: "Run 4", sleep: 82.1, activity: 88.0, risk: 75.8 },
  { run: "Run 5", sleep: 85.0, activity: 90.2, risk: 77.2 },
  { run: "Run 6", sleep: 87.3, activity: 91.2, risk: 79.6 },
];

const featureImportance = [
  { feature: "sleep_hours", importance: 0.31 },
  { feature: "hrv_avg", importance: 0.24 },
  { feature: "stress_index", importance: 0.18 },
  { feature: "steps_lag1", importance: 0.15 },
  { feature: "caffeine_pm", importance: 0.12 },
];

const STATUS_COLORS = {
  production: { bg: "#E1F5EE", text: "#085041" },
  staging: { bg: "#FAEEDA", text: "#633806" },
  training: { bg: "#EEEDFE", text: "#26215C" },
};

function ModelCard({ model, selected, onClick }) {
  const sc = STATUS_COLORS[model.status];
  return (
    <div
      onClick={onClick}
      style={{
        background: "#fff",
        border: selected ? "2px solid #1D9E75" : "0.5px solid rgba(0,0,0,0.12)",
        borderRadius: 10, padding: "14px 16px", cursor: "pointer",
        transition: "border 0.2s",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 2px", color: "#1a1a18" }}>{model.name}</p>
          <p style={{ fontSize: 11, color: "#888780", margin: 0 }}>{model.type} · {model.version}</p>
        </div>
        <span style={{
          fontSize: 10, fontWeight: 500, padding: "2px 8px", borderRadius: 6,
          background: sc.bg, color: sc.text,
        }}>
          {model.status}
        </span>
      </div>
      <div style={{ display: "flex", gap: 16 }}>
        <div>
          <p style={{ fontSize: 10, color: "#888780", margin: "0 0 2px" }}>Accuracy</p>
          <p style={{ fontSize: 18, fontWeight: 500, margin: 0, color: "#1a1a18" }}>{model.accuracy}%</p>
        </div>
        <div>
          <p style={{ fontSize: 10, color: "#888780", margin: "0 0 2px" }}>F1 score</p>
          <p style={{ fontSize: 18, fontWeight: 500, margin: 0, color: "#1a1a18" }}>{model.f1}</p>
        </div>
      </div>
      <p style={{ fontSize: 11, color: "#888780", margin: "8px 0 0" }}>Trained {model.lastTrained}</p>
    </div>
  );
}

function FeatureBar({ feature, importance }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
      <span style={{ fontSize: 12, color: "#1a1a18", minWidth: 120, fontFamily: "monospace" }}>{feature}</span>
      <div style={{ flex: 1, height: 6, background: "#e5e5e5", borderRadius: 3, overflow: "hidden" }}>
        <div style={{
          width: `${importance * 100}%`, height: "100%",
          background: "#7F77DD", borderRadius: 3, transition: "width 0.6s ease",
        }} />
      </div>
      <span style={{ fontSize: 12, color: "#888780", minWidth: 32, textAlign: "right" }}>
        {(importance * 100).toFixed(0)}%
      </span>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#fff", border: "0.5px solid rgba(0,0,0,0.2)",
      borderRadius: 8, padding: "8px 12px", fontSize: 12,
    }}>
      <p style={{ margin: "0 0 4px", fontWeight: 500 }}>{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ margin: 0, color: p.color }}>{p.name}: {p.value}%</p>
      ))}
    </div>
  );
};

export default function MLModelingEngine() {
  const [selected, setSelected] = useState("sleep_clf");
  const activeModel = MODELS.find((m) => m.id === selected);

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      color: "#1a1a18", padding: "1.5rem 0", maxWidth: 900,
    }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <p style={{ fontSize: 11, color: "#888780", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.07em" }}>
          Module 4
        </p>
        <h1 style={{ fontSize: 22, fontWeight: 500, margin: 0 }}>ML modeling engine</h1>
        <p style={{ fontSize: 13, color: "#888780", margin: "4px 0 0" }}>
          4 models · 3 in production · Tracked via MLflow
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 12 }}>
        {[
          { label: "Models in prod", value: "3" },
          { label: "Avg accuracy", value: "87.6%" },
          { label: "Training runs", value: "142" },
          { label: "Features tracked", value: "38" },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: "#f3f2ee", borderRadius: 8, padding: "10px 14px" }}>
            <p style={{ fontSize: 12, color: "#888780", margin: "0 0 2px" }}>{label}</p>
            <p style={{ fontSize: 18, fontWeight: 500, margin: 0 }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Model cards */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10, marginBottom: 12,
      }}>
        {MODELS.map((m) => (
          <ModelCard
            key={m.id}
            model={m}
            selected={selected === m.id}
            onClick={() => setSelected(m.id)}
          />
        ))}
      </div>

      {/* Detail: selected model */}
      <div style={{
        display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: 12, marginBottom: 12,
      }}>
        {/* Feature importance */}
        <div style={{
          background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
          borderRadius: 12, padding: "1.25rem",
        }}>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 4px" }}>
            Feature importance — {activeModel.name}
          </p>
          <p style={{ fontSize: 12, color: "#888780", margin: "0 0 1rem" }}>
            Top drivers from {activeModel.type}
          </p>
          {featureImportance.map((f) => (
            <FeatureBar key={f.feature} {...f} />
          ))}
        </div>

        {/* Input features */}
        <div style={{
          background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
          borderRadius: 12, padding: "1.25rem",
        }}>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 4px" }}>Input features</p>
          <p style={{ fontSize: 12, color: "#888780", margin: "0 0 1rem" }}>
            Raw features fed into this model
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {activeModel.features.map((f) => (
              <span key={f} style={{
                fontSize: 12, fontFamily: "monospace",
                background: "#EEEDFE", color: "#3C3489",
                padding: "4px 10px", borderRadius: 6,
              }}>
                {f}
              </span>
            ))}
          </div>
          <div style={{
            marginTop: "1.25rem",
            background: "#f3f2ee", borderRadius: 8, padding: "12px 14px",
          }}>
            <p style={{ fontSize: 12, fontWeight: 500, margin: "0 0 6px" }}>Model metadata</p>
            {[
              ["Type", activeModel.type],
              ["Version", activeModel.version],
              ["Status", activeModel.status],
              ["Last trained", activeModel.lastTrained],
              ["Accuracy", `${activeModel.accuracy}%`],
              ["F1 score", activeModel.f1],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: "#888780" }}>{k}</span>
                <span style={{ fontSize: 12, fontWeight: 500 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Training history chart */}
      <div style={{
        background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
        borderRadius: 12, padding: "1.25rem",
      }}>
        <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 4px" }}>Training history</p>
        <p style={{ fontSize: 12, color: "#888780", margin: "0 0 1rem" }}>
          Accuracy across runs — all models
        </p>
        <div style={{ display: "flex", gap: 16, marginBottom: 12, fontSize: 12, color: "#888780" }}>
          {[
            { color: "#7F77DD", label: "Sleep classifier" },
            { color: "#1D9E75", label: "Activity predictor" },
            { color: "#D85A30", label: "Risk classifier" },
          ].map(({ color, label }) => (
            <span key={label} style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 10, height: 2, background: color, display: "inline-block", borderRadius: 2 }} />
              {label}
            </span>
          ))}
        </div>
        <div style={{ width: "100%", height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trainingHistory} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
              <XAxis dataKey="run" tick={{ fontSize: 11, fill: "#888780" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#888780" }} axisLine={false} tickLine={false} domain={[60, 100]} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="sleep" name="Sleep" stroke="#7F77DD" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="activity" name="Activity" stroke="#1D9E75" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="risk" name="Risk" stroke="#D85A30" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
