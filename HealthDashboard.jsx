import { useState } from "react";
import {
  LineChart, Line, AreaChart, Area,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from "recharts";

// ── Palette (no CSS vars in Recharts — using hex from the teal/purple/amber/coral ramps) ──
const C = {
  teal: "#1D9E75",
  tealLight: "#E1F5EE",
  purple: "#7F77DD",
  purpleLight: "#EEEDFE",
  amber: "#BA7517",
  amberLight: "#FAEEDA",
  coral: "#D85A30",
  coralLight: "#FAECE7",
  green: "#639922",
  greenLight: "#EAF3DE",
  muted: "#888780",
};

// ── Mock data ──
const sleepData = [
  { day: "Mon", hours: 6.2, deep: 1.1 },
  { day: "Tue", hours: 7.8, deep: 1.9 },
  { day: "Wed", hours: 5.5, deep: 0.9 },
  { day: "Thu", hours: 8.1, deep: 2.1 },
  { day: "Fri", hours: 7.3, deep: 1.7 },
  { day: "Sat", hours: 9.0, deep: 2.4 },
  { day: "Sun", hours: 7.6, deep: 1.8 },
];

const activityData = [
  { day: "Mon", steps: 8200, calories: 420, active: 45 },
  { day: "Tue", steps: 11400, calories: 560, active: 72 },
  { day: "Wed", steps: 6800, calories: 310, active: 30 },
  { day: "Thu", steps: 13200, calories: 640, active: 88 },
  { day: "Fri", steps: 9700, calories: 490, active: 58 },
  { day: "Sat", steps: 15100, calories: 720, active: 95 },
  { day: "Sun", steps: 7400, calories: 380, active: 42 },
];

const stressData = [
  { time: "6am", level: 28 },
  { time: "9am", level: 52 },
  { time: "12pm", level: 61 },
  { time: "3pm", level: 74 },
  { time: "6pm", level: 45 },
  { time: "9pm", level: 33 },
  { time: "12am", level: 19 },
];

const recommendations = [
  {
    icon: "ti-moon",
    color: C.purple,
    bg: C.purpleLight,
    title: "Sleep earlier tonight",
    detail: "You averaged 6.8 hrs this week. Aim for 7.5+ by going to bed 45 min sooner.",
    impact: "High impact",
    impactColor: C.teal,
    impactBg: C.tealLight,
  },
  {
    icon: "ti-walk",
    color: C.teal,
    bg: C.tealLight,
    title: "Hit 10k steps today",
    detail: "You're at 4,200 steps. A 30-min evening walk gets you there.",
    impact: "Medium impact",
    impactColor: C.amber,
    impactBg: C.amberLight,
  },
  {
    icon: "ti-brain",
    color: C.coral,
    bg: C.coralLight,
    title: "Stress spike at 3 PM",
    detail: "Your HRV drops daily around this time. Try a 5-min breathing reset.",
    impact: "High impact",
    impactColor: C.teal,
    impactBg: C.tealLight,
  },
  {
    icon: "ti-droplet",
    color: C.amber,
    bg: C.amberLight,
    title: "Hydration reminder",
    detail: "Logging shows 1.2 L today. Target is 2.5 L before 8 PM.",
    impact: "Medium impact",
    impactColor: C.amber,
    impactBg: C.amberLight,
  },
];

// ── Sub-components ──

function HealthScoreRing({ score }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const color = score >= 75 ? C.teal : score >= 50 ? C.amber : C.coral;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
      <svg width={136} height={136} viewBox="0 0 136 136" aria-label={`Health score: ${score} out of 100`}>
        <circle cx={68} cy={68} r={r} fill="none" stroke="#e5e5e5" strokeWidth={10} />
        <circle
          cx={68} cy={68} r={r}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeLinecap="round"
          transform="rotate(-90 68 68)"
          style={{ transition: "stroke-dasharray 0.8s ease" }}
        />
        <text x={68} y={62} textAnchor="middle" fontSize={28} fontWeight={500} fill={color}>{score}</text>
        <text x={68} y={80} textAnchor="middle" fontSize={12} fill={C.muted}>/ 100</text>
      </svg>
      <div>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 4px" }}>Weekly average</p>
        <p style={{ fontSize: 22, fontWeight: 500, margin: "0 0 12px", color: "var(--color-text-primary)" }}>Good</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {[
            { label: "Sleep", val: 71, color: C.purple },
            { label: "Activity", val: 84, color: C.teal },
            { label: "Stress", val: 63, color: C.coral },
          ].map(({ label, val, color }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 12, color: "var(--color-text-secondary)", width: 46 }}>{label}</span>
              <div style={{ flex: 1, height: 4, borderRadius: 2, background: "#e5e5e5", overflow: "hidden" }}>
                <div style={{ width: `${val}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.8s ease" }} />
              </div>
              <span style={{ fontSize: 12, fontWeight: 500, width: 26, textAlign: "right", color: "var(--color-text-primary)" }}>{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatBadge({ label, value, unit }) {
  return (
    <div style={{ background: "var(--color-background-secondary)", borderRadius: 8, padding: "10px 14px" }}>
      <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>{label}</p>
      <p style={{ fontSize: 18, fontWeight: 500, margin: 0, color: "var(--color-text-primary)" }}>
        {value}<span style={{ fontSize: 12, color: "var(--color-text-secondary)", marginLeft: 3 }}>{unit}</span>
      </p>
    </div>
  );
}

function SectionCard({ title, icon, children }) {
  return (
    <div style={{
      background: "var(--color-background-primary)",
      border: "0.5px solid var(--color-border-tertiary)",
      borderRadius: 12,
      padding: "1.25rem",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "1rem" }}>
        <i className={`ti ${icon}`} aria-hidden="true" style={{ fontSize: 18, color: "var(--color-text-secondary)" }} />
        <h2 style={{ fontSize: 15, fontWeight: 500, margin: 0, color: "var(--color-text-primary)" }}>{title}</h2>
      </div>
      {children}
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--color-background-primary)",
      border: "0.5px solid var(--color-border-secondary)",
      borderRadius: 8, padding: "8px 12px", fontSize: 12,
    }}>
      <p style={{ margin: "0 0 4px", fontWeight: 500, color: "var(--color-text-primary)" }}>{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ margin: 0, color: p.color || "var(--color-text-secondary)" }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
};

// ── Main Dashboard ──
export default function HealthDashboard() {
  const [activeTab, setActiveTab] = useState("week");

  return (
    <div style={{ fontFamily: "var(--font-sans)", color: "var(--color-text-primary)", padding: "1.5rem 0", maxWidth: 900 }}>
      <h2 className="sr-only">Personalized Health Insights Dashboard</h2>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem", flexWrap: "wrap", gap: 12 }}>
        <div>
          <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Health dashboard
          </p>
          <h1 style={{ fontSize: 22, fontWeight: 500, margin: 0 }}>Good morning, Alex</h1>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "4px 0 0" }}>
            Wednesday, June 24 · Synced 12 min ago
          </p>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {["week", "month"].map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              style={{
                padding: "6px 14px", borderRadius: 8, fontSize: 13, cursor: "pointer",
                border: "0.5px solid var(--color-border-secondary)",
                background: activeTab === t ? "var(--color-background-secondary)" : "transparent",
                color: activeTab === t ? "var(--color-text-primary)" : "var(--color-text-secondary)",
                fontWeight: activeTab === t ? 500 : 400,
              }}
            >
              This {t}
            </button>
          ))}
        </div>
      </div>

      {/* Row 1: Health Score + Quick Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1.2fr) minmax(0,1fr)", gap: 12, marginBottom: 12 }}>
        <SectionCard title="Health score" icon="ti-heart-rate-monitor">
          <HealthScoreRing score={74} />
        </SectionCard>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <StatBadge label="Avg sleep" value="7.4" unit="hrs" />
            <StatBadge label="Daily steps" value="10.2k" unit="avg" />
            <StatBadge label="Resting HR" value="62" unit="bpm" />
            <StatBadge label="Stress index" value="48" unit="/ 100" />
          </div>
          <div style={{
            background: C.tealLight,
            borderRadius: 10,
            padding: "10px 14px",
            display: "flex", alignItems: "center", gap: 10,
            flex: 1,
          }}>
            <i className="ti ti-trending-up" aria-hidden="true" style={{ fontSize: 20, color: C.teal }} />
            <div>
              <p style={{ margin: 0, fontSize: 13, fontWeight: 500, color: "#085041" }}>Up 6 pts from last week</p>
              <p style={{ margin: 0, fontSize: 12, color: "#0F6E56" }}>Sleep and activity both improved</p>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Sleep Trends */}
      <div style={{ marginBottom: 12 }}>
        <SectionCard title="Sleep trends" icon="ti-moon-stars">
          <div style={{ display: "flex", gap: 16, marginBottom: 12 }}>
            {[
              { label: "Avg total", value: "7.4 hrs" },
              { label: "Avg deep", value: "1.7 hrs" },
              { label: "Best night", value: "Sat · 9 hrs" },
            ].map(({ label, value }) => (
              <div key={label}>
                <p style={{ fontSize: 11, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>{label}</p>
                <p style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>{value}</p>
              </div>
            ))}
          </div>
          <div style={{ position: "relative", width: "100%", height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sleepData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="sleepGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={C.purple} stopOpacity={0.18} />
                    <stop offset="95%" stopColor={C.purple} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="deepGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={C.teal} stopOpacity={0.18} />
                    <stop offset="95%" stopColor={C.teal} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: C.muted }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: C.muted }} axisLine={false} tickLine={false} domain={[0, 10]} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={7.5} stroke={C.purple} strokeDasharray="4 3" strokeOpacity={0.5} label={{ value: "target", fontSize: 10, fill: C.purple, position: "right" }} />
                <Area type="monotone" dataKey="hours" name="Total sleep" stroke={C.purple} strokeWidth={2} fill="url(#sleepGrad)" dot={{ r: 3, fill: C.purple, strokeWidth: 0 }} activeDot={{ r: 5 }} />
                <Area type="monotone" dataKey="deep" name="Deep sleep" stroke={C.teal} strokeWidth={2} fill="url(#deepGrad)" dot={{ r: 3, fill: C.teal, strokeWidth: 0 }} activeDot={{ r: 5 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 10, fontSize: 12, color: "var(--color-text-secondary)" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 10, height: 2, background: C.purple, display: "inline-block", borderRadius: 2 }} />Total sleep
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 10, height: 2, background: C.teal, display: "inline-block", borderRadius: 2 }} />Deep sleep
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 18, height: 0, border: `1.5px dashed ${C.purple}`, display: "inline-block", opacity: 0.6 }} />7.5 hr target
            </span>
          </div>
        </SectionCard>
      </div>

      {/* Row 3: Activity + Stress side-by-side */}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: 12, marginBottom: 12 }}>

        {/* Activity Trends */}
        <SectionCard title="Activity trends" icon="ti-run">
          <div style={{ display: "flex", gap: 16, marginBottom: 12 }}>
            {[
              { label: "Avg steps", value: "10.3k" },
              { label: "Active min", value: "61 min" },
            ].map(({ label, value }) => (
              <div key={label}>
                <p style={{ fontSize: 11, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>{label}</p>
                <p style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>{value}</p>
              </div>
            ))}
          </div>
          <div style={{ position: "relative", width: "100%", height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: C.muted }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: C.muted }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={10000} stroke={C.teal} strokeDasharray="4 3" strokeOpacity={0.5} />
                <Bar dataKey="steps" name="Steps" fill={C.teal} fillOpacity={0.75} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 10, fontSize: 12, color: "var(--color-text-secondary)" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 10, height: 10, background: C.teal, display: "inline-block", borderRadius: 2, opacity: 0.75 }} />Steps
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 18, height: 0, border: `1.5px dashed ${C.teal}`, display: "inline-block", opacity: 0.6 }} />10k goal
            </span>
          </div>
        </SectionCard>

        {/* Stress Trends */}
        <SectionCard title="Stress trends" icon="ti-brain">
          <div style={{ display: "flex", gap: 16, marginBottom: 12 }}>
            {[
              { label: "Avg level", value: "45 / 100" },
              { label: "Peak", value: "3 PM · 74" },
            ].map(({ label, value }) => (
              <div key={label}>
                <p style={{ fontSize: 11, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>{label}</p>
                <p style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>{value}</p>
              </div>
            ))}
          </div>
          <div style={{ position: "relative", width: "100%", height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stressData} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
                <defs>
                  <linearGradient id="stressGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={C.coral} stopOpacity={0.2} />
                    <stop offset="95%" stopColor={C.coral} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: C.muted }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: C.muted }} axisLine={false} tickLine={false} domain={[0, 100]} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={60} stroke={C.coral} strokeDasharray="4 3" strokeOpacity={0.4} label={{ value: "high", fontSize: 10, fill: C.coral, position: "right" }} />
                <Area type="monotone" dataKey="level" name="Stress" stroke={C.coral} strokeWidth={2} fill="url(#stressGrad)" dot={{ r: 3, fill: C.coral, strokeWidth: 0 }} activeDot={{ r: 5 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 10, fontSize: 12, color: "var(--color-text-secondary)" }}>
            {[
              { color: C.green, label: "Low (< 40)" },
              { color: C.amber, label: "Moderate (40–60)" },
              { color: C.coral, label: "High (> 60)" },
            ].map(({ color, label }) => (
              <span key={label} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 8, height: 8, background: color, display: "inline-block", borderRadius: "50%" }} />{label}
              </span>
            ))}
          </div>
        </SectionCard>
      </div>

      {/* Row 4: Daily Recommendations */}
      <SectionCard title="Today's recommendations" icon="ti-sparkles">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 }}>
          {recommendations.map(({ icon, color, bg, title, detail, impact, impactColor, impactBg }) => (
            <div key={title} style={{
              background: "var(--color-background-secondary)",
              borderRadius: 10,
              padding: "12px 14px",
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: 8,
                background: bg, display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <i className={`ti ${icon}`} aria-hidden="true" style={{ fontSize: 18, color }} />
              </div>
              <p style={{ fontSize: 13, fontWeight: 500, margin: 0, color: "var(--color-text-primary)", lineHeight: 1.35 }}>{title}</p>
              <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: 0, lineHeight: 1.5 }}>{detail}</p>
              <span style={{
                alignSelf: "flex-start", fontSize: 11, fontWeight: 500,
                background: impactBg, color: impactColor,
                borderRadius: 6, padding: "2px 8px",
              }}>
                {impact}
              </span>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
