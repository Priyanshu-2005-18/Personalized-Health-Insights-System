import { useState } from "react";

const COMPLIANCE_ITEMS = [
  { id: "hipaa", label: "HIPAA compliance", status: "pass", detail: "PHI handling, audit logs, and BAA in place", last: "Reviewed Jun 10" },
  { id: "gdpr", label: "GDPR compliance", status: "pass", detail: "Consent management, right-to-erasure pipeline active", last: "Reviewed Jun 1" },
  { id: "encryption", label: "AES-256 encryption at rest", status: "pass", detail: "All InfluxDB and Postgres volumes encrypted", last: "Verified daily" },
  { id: "tls", label: "TLS 1.3 in transit", status: "pass", detail: "All API endpoints enforce TLS 1.3 minimum", last: "Verified daily" },
  { id: "pentest", label: "Penetration testing", status: "warn", detail: "Last external pentest was 5 months ago — schedule due", last: "Jan 2024" },
  { id: "anon", label: "Anonymisation pipeline", status: "pass", detail: "ML training data stripped of all PII before use", last: "Active" },
];

const AUDIT_LOG = [
  { time: "09:42", user: "alex@example.com", action: "Viewed sleep data", resource: "sleep_records", ip: "192.168.1.10", ok: true },
  { time: "09:40", user: "system", action: "ML inference run", resource: "feature_store", ip: "internal", ok: true },
  { time: "08:55", user: "alex@example.com", action: "Updated profile", resource: "user_profile", ip: "192.168.1.10", ok: true },
  { time: "08:21", user: "admin@healthapp.io", action: "Exported anonymised dataset", resource: "ml_dataset", ip: "10.0.0.4", ok: true },
  { time: "07:14", user: "unknown", action: "Failed login attempt", resource: "auth", ip: "45.33.32.156", ok: false },
  { time: "06:59", user: "system", action: "Backup completed", resource: "postgres + influxdb", ip: "internal", ok: true },
];

const DATA_CATEGORIES = [
  { label: "Biometric data", retention: "2 years", encrypted: true, exportable: true, deletable: true },
  { label: "Activity logs", retention: "1 year", encrypted: true, exportable: true, deletable: true },
  { label: "Nutrition logs", retention: "1 year", encrypted: true, exportable: true, deletable: true },
  { label: "ML model inputs", retention: "Anonymised, indefinite", encrypted: true, exportable: false, deletable: false },
  { label: "Audit logs", retention: "6 years (HIPAA)", encrypted: true, exportable: false, deletable: false },
];

const STATUS_STYLES = {
  pass: { bg: "#E1F5EE", text: "#085041", icon: "✓" },
  warn: { bg: "#FAEEDA", text: "#633806", icon: "⚠" },
  fail: { bg: "#FAECE7", text: "#993C1D", icon: "✕" },
};

function ComplianceRow({ item }) {
  const ss = STATUS_STYLES[item.status];
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 14, padding: "12px 0",
      borderBottom: "0.5px solid rgba(0,0,0,0.08)",
    }}>
      <span style={{
        width: 24, height: 24, borderRadius: "50%",
        background: ss.bg, color: ss.text,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 12, fontWeight: 700, flexShrink: 0,
      }}>
        {ss.icon}
      </span>
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 2px", color: "#1a1a18" }}>{item.label}</p>
        <p style={{ fontSize: 12, color: "#888780", margin: 0 }}>{item.detail}</p>
      </div>
      <span style={{ fontSize: 11, color: "#888780", flexShrink: 0 }}>{item.last}</span>
    </div>
  );
}

function CheckBadge({ value }) {
  return (
    <span style={{ fontSize: 12, color: value ? "#1D9E75" : "#888780" }}>
      {value ? "✓" : "—"}
    </span>
  );
}

export default function PrivacySecurity() {
  const [userDataOpen, setUserDataOpen] = useState(false);
  const passCount = COMPLIANCE_ITEMS.filter((i) => i.status === "pass").length;

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      color: "#1a1a18", padding: "1.5rem 0", maxWidth: 900,
    }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <p style={{ fontSize: 11, color: "#888780", margin: "0 0 2px", textTransform: "uppercase", letterSpacing: "0.07em" }}>
          Module 8
        </p>
        <h1 style={{ fontSize: 22, fontWeight: 500, margin: 0 }}>Privacy, security & compliance</h1>
        <p style={{ fontSize: 13, color: "#888780", margin: "4px 0 0" }}>
          HIPAA-aware · GDPR-ready · AES-256 encrypted
        </p>
      </div>

      {/* Summary stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 12 }}>
        {[
          { label: "Checks passing", value: `${passCount} / ${COMPLIANCE_ITEMS.length}` },
          { label: "Encryption", value: "AES-256" },
          { label: "Audit events today", value: AUDIT_LOG.length.toString() },
          { label: "Failed logins (24h)", value: "1" },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: "#f3f2ee", borderRadius: 8, padding: "10px 14px" }}>
            <p style={{ fontSize: 12, color: "#888780", margin: "0 0 2px" }}>{label}</p>
            <p style={{ fontSize: 18, fontWeight: 500, margin: 0 }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Overall status banner */}
      <div style={{
        background: "#E1F5EE", borderRadius: 10, padding: "14px 16px",
        display: "flex", gap: 12, alignItems: "center", marginBottom: 12,
        border: "0.5px solid #9FE1CB",
      }}>
        <span style={{ fontSize: 24 }}>🔒</span>
        <div>
          <p style={{ fontSize: 13, fontWeight: 500, color: "#085041", margin: "0 0 2px" }}>
            System security posture: Good
          </p>
          <p style={{ fontSize: 12, color: "#0F6E56", margin: 0 }}>
            5 of 6 checks passing. 1 warning: external pentest is overdue.
          </p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: 12, marginBottom: 12 }}>

        {/* Compliance checklist */}
        <div style={{
          background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
          borderRadius: 12, padding: "1.25rem",
        }}>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 0.25rem" }}>Compliance checklist</p>
          <p style={{ fontSize: 12, color: "#888780", margin: "0 0 0.75rem" }}>Regulatory & security controls</p>
          <div>
            {COMPLIANCE_ITEMS.map((item) => <ComplianceRow key={item.id} item={item} />)}
          </div>
        </div>

        {/* Data categories */}
        <div style={{
          background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
          borderRadius: 12, padding: "1.25rem",
        }}>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 0.25rem" }}>Data governance</p>
          <p style={{ fontSize: 12, color: "#888780", margin: "0 0 0.75rem" }}>Retention, encryption and user rights</p>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: "0.5px solid rgba(0,0,0,0.1)" }}>
                {["Category", "Retention", "Enc.", "Export", "Delete"].map((h) => (
                  <th key={h} style={{
                    textAlign: "left", padding: "0 0 8px",
                    color: "#888780", fontWeight: 500, fontSize: 11,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DATA_CATEGORIES.map((row, i) => (
                <tr key={row.label} style={{
                  borderBottom: i < DATA_CATEGORIES.length - 1 ? "0.5px solid rgba(0,0,0,0.06)" : "none",
                }}>
                  <td style={{ padding: "9px 0", color: "#1a1a18", fontWeight: 500 }}>{row.label}</td>
                  <td style={{ padding: "9px 0", color: "#888780" }}>{row.retention}</td>
                  <td style={{ padding: "9px 0" }}><CheckBadge value={row.encrypted} /></td>
                  <td style={{ padding: "9px 0" }}><CheckBadge value={row.exportable} /></td>
                  <td style={{ padding: "9px 0" }}><CheckBadge value={row.deletable} /></td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* User data controls */}
          <div style={{
            marginTop: "1rem",
            background: "#f3f2ee", borderRadius: 8, padding: "12px 14px",
          }}>
            <p style={{ fontSize: 12, fontWeight: 500, margin: "0 0 8px" }}>Your data rights</p>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {["Export all data", "Delete account", "Revoke consent"].map((action) => (
                <button key={action} style={{
                  padding: "6px 12px", borderRadius: 7, fontSize: 12, cursor: "pointer",
                  border: "0.5px solid rgba(0,0,0,0.2)", background: "#fff",
                  color: action === "Delete account" ? "#D85A30" : "#1a1a18",
                }}>
                  {action}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Audit log */}
      <div style={{
        background: "#fff", border: "0.5px solid rgba(0,0,0,0.12)",
        borderRadius: 12, padding: "1.25rem",
      }}>
        <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 1rem" }}>Audit log</p>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: "0.5px solid rgba(0,0,0,0.1)" }}>
                {["Time", "User", "Action", "Resource", "IP", "Result"].map((h) => (
                  <th key={h} style={{
                    textAlign: "left", padding: "0 12px 8px 0",
                    color: "#888780", fontWeight: 500, fontSize: 11, whiteSpace: "nowrap",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {AUDIT_LOG.map((ev, i) => (
                <tr key={i} style={{
                  borderBottom: i < AUDIT_LOG.length - 1 ? "0.5px solid rgba(0,0,0,0.06)" : "none",
                  background: ev.ok ? "transparent" : "#FFF5F5",
                }}>
                  <td style={{ padding: "9px 12px 9px 0", color: "#888780", whiteSpace: "nowrap" }}>{ev.time}</td>
                  <td style={{ padding: "9px 12px 9px 0", color: "#1a1a18", fontFamily: "monospace", fontSize: 11 }}>{ev.user}</td>
                  <td style={{ padding: "9px 12px 9px 0", color: "#1a1a18" }}>{ev.action}</td>
                  <td style={{ padding: "9px 12px 9px 0", color: "#888780", fontFamily: "monospace", fontSize: 11 }}>{ev.resource}</td>
                  <td style={{ padding: "9px 12px 9px 0", color: "#888780", fontFamily: "monospace", fontSize: 11 }}>{ev.ip}</td>
                  <td style={{ padding: "9px 0" }}>
                    <span style={{
                      fontSize: 10, fontWeight: 500,
                      padding: "2px 7px", borderRadius: 5,
                      background: ev.ok ? "#E1F5EE" : "#FAECE7",
                      color: ev.ok ? "#085041" : "#993C1D",
                    }}>
                      {ev.ok ? "OK" : "FAILED"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
