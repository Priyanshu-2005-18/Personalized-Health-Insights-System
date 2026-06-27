import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const RECOMMENDATIONS = [
  {
    id: 1,
    category: "sleep",
    priority: "high",
    title: "Go to bed by 10:30 PM tonight",
    rationale: "Your HRV is 14% below your 30-day average. Earlier sleep onset has improved your deep sleep by 22 min on similar days.",
    model: "LSTM + rule engine",
    confidence: 91,
    impact: "+18 min deep sleep",
    variant: "A",
    ctr: 68,
    icon: "🌙",
    color: "#7F77DD",
    bg: "#EEEDFE",
  },
  {
    id: 2,
    category: "activity",
    priority: "medium",
    title: "Take a 20-min walk after lunch",
    rationale: "Post-meal walks in your data correlate with a 9-point drop in afternoon stress index. Today's stress is already at 61.",
    model: "Collaborative filter",
    confidence: 84,
    impact: "−9 stress pts",
    variant: "B",
    ctr: 54,
    icon: "🚶",
    color: "#1D9E75",
    bg: "#E1F5EE",
  },
  {
    id: 3,
    category: "nutrition",
    priority: "medium",
    title: "Add protein to your next meal",
    rationale: "You've logged 38g protein today vs. your 90g target. Reaching it is associated with better energy scores in your history.",
    model: "Rule engine",
    confidence: 77,
    impact: "+12 energy score",
    variant: "A",
    ctr: 41,
    icon: "🥗",
    color: "#639922",
    bg: "#EAF3DE",
  },
  {
    id: 4,
    category: "stress",
    priority: "high",
    title: "5-min box breathing at 3 PM",
    rationale: "Physiological stress peaks at 3 PM in your data, 6 out of 7 days this week. Breathing resets reduce your evening HR by ~6 bpm.",
    model: "LSTM + rule engine",
    confidence: 88,
    impact: "−6 bpm evening HR",
    variant: "B",
    ctr: 73,
    icon: "🧘",
    color: "#D85A30",
    bg: "#FAECE7",
  },
];

const AB_DATA = [
  { name: "Variant A", opened: 68, acted: 41, dismissed: 27 },
  { name: "Variant B", opened: 73, acted: 56, dismissed: 17 },
];

const PRIORITY_COLORS = {
  high: { bg: "#FAECE7", text: "#993C1D" },
  medium: { bg: "#FAEEDA", text: "#633806" },
  low: { bg: "#f3f2ee", text: "#888780" },
};

function ConfidenceRing({ value, color }) {
  const r = 20, circ = 2 * Math.PI * r;
  const dash = (value / 100) * circ;
  return (
    <svg width={52} height={52} viewBox="0 0 52 52" aria-label={`Confidence: ${value}%`}>
      <circle cx={26} cy={26} r={r} fill="none" stroke="#e5e5e5" strokeWidth={4} />
      <circle
        cx={26} cy={26} r={r} fill="none"
        stroke={color} strokeWidth={4}
        strokeDasharray={`${dash} ${circ - dash}`}
        strokeLinecap="round"
        transform="rotate(-90 26 26)"
      />
      <text x={26} y={30} textAnchor="middle" fontSize={11} fontWeight={500} fill={color}>{value}%</text>
    </svg>
  );
}

function RecommendationCard({ rec, expanded, onToggle }) {
  const pc = PRIORITY_COLORS[rec.priority];
  return (
    <div style={{
      background: "#fff",
      border: expanded ? `2px solid ${rec.color}` : "0.5px solid rgba(0,0,0,0.12)",
      borderRadius: 12, overflow: "hidden", transition: "border 0.2s",
    }}>
      <div
        onClick={onToggle}
        style={{ padding: "14px 16px", cursor: "pointer", display: "flex", gap: 14, alignItems: "flex-start" }}
      >
        <div style={{
          width: 42, height: 42, borderRadius: 10, background: rec.bg,
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0,
        }}>
          {rec.icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: "#1a1a18" }}>{rec.title}</span>
            <span style={{
              fontSize: 10, fontWeight: 500, padding: "2px 7px", borderRadius: 5,
              background: pc.bg, color: pc.text,
            }}>
              {rec.priority}
            </span>
            <span style={{
              fontSize: 10, padding: "2px 7px", borderRadius: 5,
              background: "#f3f2ee", color: "#888780",
            }}>
              Variant {rec.variant}
            </span>
          </div>
          <p style={{ fontSize: 12, color: "#888780", margin: 0 }}>
            {rec.impact} · {rec.model}
          </p>
        </div>
        <ConfidenceRing value={rec.confidence} color={rec.color} />
      </div>

      {expanded && (
        <div style={{
          padding: "0 16px 16px", borderTop: "0.5px solid rgba(0,0,0,0.08)",
          paddingTop: 14,
        }}>
          <p style={{ fontSize: 13, color: "#1a1a18", margin: "0 0 12px", lineHeight: 1.6 }}>
            {rec.rationale}
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={{
              flex: 1, padding: "8px 0", borderRadius: 8, fontSize: 13, cursor: "pointer",
              border: "none", background: rec.color, color: "#fff", fontWeight: 500,
            }}>
              ✓ Log action
            </button>
            <button style={{
              flex: 1, padding: "8px 0", borderRadius: 8, fontSize: 13, cursor: "pointer",
              border: "0.5px solid rgba(0,0,0,0.2)", background: "transparent", color: "#1a1a18",
            }}>
              ✕ Dismiss
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const CTip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#fff", border: "0.5px solid rgba(0,0,0,0.2)", borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
      <p style={{ margin: "0 0 4px", fontWeight: 500 }}>{label}</p>
      {payload.map((p) => <p key={p.name} style={{ margin: 0, color: p.color }}>{p.name}: {p.value}%</p>)}
    </div>
  );
};

export default function RecommendationEngine() {
  const [expanded, setExpanded] = useState(1);
  const [filter, setFilter] = useState("all");

  const filtered = filter === "all" ? RECOMMENDATIONS : RECOMMENDATIONS.filter((r) => r.category === filter);

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      color: "#1a1a18", padding: "1.5rem 0", maxWidth: 900,
    }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <p style={{ fontSize: 11, color: "#888780", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.07em" }}>
          Module 5
        </p>
        <h1 style={{ fontSize: 22, fontWeight: 500, margin: 0 }}>Recommendation engine</h1>
        <p style={{ fontSize: 13, color: "#888780", margin: "4px 0 0" }}>
          4 personalised insights · Ranked by predicted impact · A/B testing active
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 12 }}>
        {[
          { label: "Generated today", value: "4" },
          { label: "Avg confidence", value: "85%" },
          { label: "Avg CTR (7d)", value: "59%" },
          { label: "Goal alignment", value: "3 / 3" },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: "#f3f2ee", borderRadius: 8, padding: "10px 14px" }}>
            <p style={{ fontSize: 12, color: "#888780", margin: "0 0 2px" }}>{label}</p>
            <p style={{ fontSize: 18, fontWeight: 500, margin: 0 }}>{value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1.2fr) minmax(0,1fr)", gap: 12 }}>
        {/* Recommendations list */}
        <div>
          {/* Filter tabs */}
          <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
            {["all", "sleep", "activity", "nutrition", "stress"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  padding: "5px 12px", borderRadius: 8, fontSize: 12, cursor: "pointer",
                  border: "0.5px solid rgba(0,0,0,0.2)",
                  background: filter === f ? "#1D9E75" : "transparent",
                  color: filter === f ? "#fff" : "#888780",
                  fontWeight: filter === f ? 500 : 400,
                }}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {filtered.map((rec) => (
              <RecommendationCard
                key={rec.id}
                rec={rec}
                expanded={expanded === rec.id}
                onToggle={() => setExpanded(expanded === rec.id ? null : rec.id)}
              />
            ))}
          </div>
        </div>

        {/* A/B Testing panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{
            background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
            borderRadius: 12, padding: "1.25rem",
          }}>
            <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 4px" }}>A/B test results</p>
            <p style={{ fontSize: 12, color: "#888780", margin: "0 0 1rem" }}>Engagement by variant (7 days)</p>
            <div style={{ display: "flex", gap: 12, marginBottom: 12, fontSize: 12, color: "#888780" }}>
              {[
                { color: "#7F77DD", label: "Opened" },
                { color: "#1D9E75", label: "Acted" },
                { color: "#e5e5e5", label: "Dismissed" },
              ].map(({ color, label }) => (
                <span key={label} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 10, height: 10, background: color, display: "inline-block", borderRadius: 2 }} />
                  {label}
                </span>
              ))}
            </div>
            <div style={{ width: "100%", height: 160 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={AB_DATA} margin={{ top: 4, right: 8, left: -28, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#888780" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#888780" }} axisLine={false} tickLine={false} domain={[0, 100]} />
                  <Tooltip content={<CTip />} />
                  <Bar dataKey="opened" name="Opened" fill="#7F77DD" fillOpacity={0.75} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="acted" name="Acted" fill="#1D9E75" fillOpacity={0.75} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="dismissed" name="Dismissed" fill="#e5e5e5" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div style={{
              marginTop: 12, background: "#E1F5EE", borderRadius: 8, padding: "10px 12px",
            }}>
              <p style={{ fontSize: 12, fontWeight: 500, color: "#085041", margin: "0 0 2px" }}>
                Variant B is winning
              </p>
              <p style={{ fontSize: 11, color: "#0F6E56", margin: 0 }}>
                +37% action rate vs Variant A (p = 0.03)
              </p>
            </div>
          </div>

          {/* Ranking logic */}
          <div style={{
            background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
            borderRadius: 12, padding: "1.25rem",
          }}>
            <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 1rem" }}>Ranking logic</p>
            {[
              { label: "Model confidence", weight: "35%" },
              { label: "Predicted impact", weight: "30%" },
              { label: "Goal alignment", weight: "20%" },
              { label: "Recency & novelty", weight: "15%" },
            ].map(({ label, weight }) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 12, color: "#1a1a18" }}>{label}</span>
                <span style={{ fontSize: 12, fontWeight: 500, color: "#7F77DD" }}>{weight}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
