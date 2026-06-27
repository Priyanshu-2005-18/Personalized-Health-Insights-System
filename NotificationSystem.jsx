import { useState } from "react";

const NOTIFICATIONS = [
  {
    id: 1, type: "nudge", status: "sent", time: "9:00 AM",
    title: "Morning check-in",
    body: "Good morning, Alex! Your sleep score last night was 82 — a personal best this week. Log your energy level to keep the streak.",
    channel: "Push", opened: true, acted: true,
    icon: "☀️", color: "#BA7517", bg: "#FAEEDA",
  },
  {
    id: 2, type: "alert", status: "sent", time: "3:02 PM",
    title: "Stress spike detected",
    body: "Your HRV just dropped 18% below baseline. This usually precedes an elevated stress period. Try a 5-min breathing reset now.",
    channel: "Push", opened: true, acted: false,
    icon: "⚠️", color: "#D85A30", bg: "#FAECE7",
  },
  {
    id: 3, type: "nudge", status: "scheduled", time: "8:30 PM",
    title: "Wind-down reminder",
    body: "It's time to start winding down. Dim your screens and try to avoid food for the next 2 hours to improve your sleep quality.",
    channel: "Push", opened: false, acted: false,
    icon: "🌙", color: "#7F77DD", bg: "#EEEDFE",
  },
  {
    id: 4, type: "weekly", status: "scheduled", time: "Sun 8:00 AM",
    title: "Weekly health summary",
    body: "Your weekly health report will include sleep trends, activity highlights, and 3 priority goals for next week.",
    channel: "Email", opened: false, acted: false,
    icon: "📊", color: "#1D9E75", bg: "#E1F5EE",
  },
];

const RULES = [
  { id: 1, trigger: "HRV drops > 15% below 30-day avg", action: "Send stress alert immediately", active: true },
  { id: 2, trigger: "Steps < 5,000 by 6 PM", action: "Nudge: suggest evening walk", active: true },
  { id: 3, trigger: "Sleep < 6.5 hrs for 2 consecutive nights", action: "Sleep coaching push notification", active: true },
  { id: 4, trigger: "Goal streak ≥ 5 days", action: "Send celebration + share prompt", active: false },
  { id: 5, trigger: "No log entry in > 24 hrs", action: "Gentle re-engagement email", active: true },
];

const TIMING_DATA = [
  { hour: "6am", engagement: 42 },
  { hour: "8am", engagement: 68 },
  { hour: "9am", engagement: 74 },
  { hour: "12pm", engagement: 55 },
  { hour: "3pm", engagement: 48 },
  { hour: "6pm", engagement: 61 },
  { hour: "8pm", engagement: 79 },
  { hour: "9pm", engagement: 71 },
  { hour: "10pm", engagement: 38 },
];

const STATUS_STYLES = {
  sent: { bg: "#E1F5EE", text: "#085041" },
  scheduled: { bg: "#FAEEDA", text: "#633806" },
  failed: { bg: "#FAECE7", text: "#993C1D" },
};

function Toggle({ active, onToggle }) {
  return (
    <div
      onClick={onToggle}
      style={{
        width: 36, height: 20, borderRadius: 10, cursor: "pointer",
        background: active ? "#1D9E75" : "#c0c0c0",
        position: "relative", transition: "background 0.2s", flexShrink: 0,
      }}
    >
      <div style={{
        position: "absolute", top: 3, left: active ? 18 : 3,
        width: 14, height: 14, borderRadius: "50%", background: "#fff",
        transition: "left 0.2s",
      }} />
    </div>
  );
}

export default function NotificationSystem() {
  const [rules, setRules] = useState(RULES);
  const [notifications] = useState(NOTIFICATIONS);

  const toggleRule = (id) => {
    setRules((rs) => rs.map((r) => r.id === id ? { ...r, active: !r.active } : r));
  };

  const maxEng = Math.max(...TIMING_DATA.map((d) => d.engagement));

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      color: "#1a1a18", padding: "1.5rem 0", maxWidth: 900,
    }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <p style={{ fontSize: 11, color: "#888780", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.07em" }}>
          Module 7
        </p>
        <h1 style={{ fontSize: 22, fontWeight: 500, margin: 0 }}>Notification & nudge system</h1>
        <p style={{ fontSize: 13, color: "#888780", margin: "4px 0 0" }}>
          Timely, personalised prompts via Firebase FCM + Celery
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 12 }}>
        {[
          { label: "Sent today", value: "2" },
          { label: "Open rate (7d)", value: "71%" },
          { label: "Action rate (7d)", value: "48%" },
          { label: "Active rules", value: rules.filter((r) => r.active).length.toString() },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: "#f3f2ee", borderRadius: 8, padding: "10px 14px" }}>
            <p style={{ fontSize: 12, color: "#888780", margin: "0 0 2px" }}>{label}</p>
            <p style={{ fontSize: 18, fontWeight: 500, margin: 0 }}>{value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1.2fr) minmax(0,1fr)", gap: 12, marginBottom: 12 }}>

        {/* Notification feed */}
        <div style={{
          background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
          borderRadius: 12, padding: "1.25rem",
        }}>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 1rem" }}>Today's notifications</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {notifications.map((n) => {
              const ss = STATUS_STYLES[n.status];
              return (
                <div key={n.id} style={{
                  display: "flex", gap: 12, padding: "12px 14px",
                  background: "#f9f9f8", borderRadius: 10,
                  border: "0.5px solid rgba(0,0,0,0.08)",
                  opacity: n.status === "scheduled" ? 0.75 : 1,
                }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 9, background: n.bg,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 18, flexShrink: 0,
                  }}>
                    {n.icon}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 3 }}>
                      <span style={{ fontSize: 13, fontWeight: 500, color: "#1a1a18" }}>{n.title}</span>
                      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                        <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: "#f3f2ee", color: "#888780" }}>
                          {n.channel}
                        </span>
                        <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: ss.bg, color: ss.text, fontWeight: 500 }}>
                          {n.status}
                        </span>
                      </div>
                    </div>
                    <p style={{ fontSize: 12, color: "#888780", margin: "0 0 6px", lineHeight: 1.5 }}>{n.body}</p>
                    <div style={{ display: "flex", gap: 10, fontSize: 11, color: "#888780" }}>
                      <span>{n.time}</span>
                      {n.status === "sent" && (
                        <>
                          <span style={{ color: n.opened ? "#1D9E75" : "#888780" }}>
                            {n.opened ? "✓ Opened" : "Not opened"}
                          </span>
                          <span style={{ color: n.acted ? "#1D9E75" : "#888780" }}>
                            {n.acted ? "✓ Acted" : "No action"}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Optimal timing chart */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{
            background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
            borderRadius: 12, padding: "1.25rem",
          }}>
            <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 4px" }}>Optimal send times</p>
            <p style={{ fontSize: 12, color: "#888780", margin: "0 0 1rem" }}>
              Predicted engagement by hour (Alex's pattern)
            </p>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 100 }}>
              {TIMING_DATA.map(({ hour, engagement }) => {
                const isOptimal = engagement >= 70;
                return (
                  <div key={hour} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                    <div style={{
                      width: "100%",
                      height: `${(engagement / maxEng) * 80}px`,
                      background: isOptimal ? "#1D9E75" : "#c0e8da",
                      borderRadius: "3px 3px 0 0",
                      transition: "height 0.4s ease",
                    }} />
                    <span style={{ fontSize: 9, color: "#888780", textAlign: "center" }}>{hour}</span>
                  </div>
                );
              })}
            </div>
            <div style={{ display: "flex", gap: 12, marginTop: 8, fontSize: 11, color: "#888780" }}>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 8, height: 8, background: "#1D9E75", display: "inline-block", borderRadius: 2 }} />
                High engagement (≥70%)
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 8, height: 8, background: "#c0e8da", display: "inline-block", borderRadius: 2 }} />
                Moderate
              </span>
            </div>
          </div>

          {/* Channels */}
          <div style={{
            background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
            borderRadius: 12, padding: "1.25rem",
          }}>
            <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 1rem" }}>Channel preferences</p>
            {[
              { channel: "Push notifications", pct: 62, enabled: true },
              { channel: "Email (daily digest)", pct: 28, enabled: true },
              { channel: "In-app banners", pct: 10, enabled: false },
            ].map(({ channel, pct, enabled }) => (
              <div key={channel} style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: "#1a1a18" }}>{channel}</span>
                  <span style={{ fontSize: 12, color: "#888780" }}>{pct}%</span>
                </div>
                <div style={{ height: 4, background: "#e5e5e5", borderRadius: 2, overflow: "hidden" }}>
                  <div style={{
                    width: `${pct}%`, height: "100%",
                    background: enabled ? "#1D9E75" : "#c0c0c0", borderRadius: 2,
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Rules engine */}
      <div style={{
        background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
        borderRadius: 12, padding: "1.25rem",
      }}>
        <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 1rem" }}>Nudge rules</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {rules.map((rule, i) => (
            <div key={rule.id} style={{
              display: "flex", alignItems: "flex-start", gap: 14, padding: "12px 0",
              borderBottom: i < rules.length - 1 ? "0.5px solid rgba(0,0,0,0.08)" : "none",
            }}>
              <Toggle active={rule.active} onToggle={() => toggleRule(rule.id)} />
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 12, fontWeight: 500, margin: "0 0 2px", color: rule.active ? "#1a1a18" : "#888780" }}>
                  If: {rule.trigger}
                </p>
                <p style={{ fontSize: 12, color: "#888780", margin: 0 }}>Then: {rule.action}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
