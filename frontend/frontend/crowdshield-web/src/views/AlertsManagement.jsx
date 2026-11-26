import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BellRing,
  CheckCircle2,
  Clock3,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  UserRound,
  XCircle,
} from "lucide-react";

const palette = {
  page: "#07111f",
  panel: "#0b1728",
  panel2: "#0e1c30",
  border: "#203149",
  text: "#e2e8f0",
  muted: "#94a3b8",
  orange: "#fb923c",
  red: "#fb7185",
  teal: "#2dd4bf",
  blue: "#38bdf8",
};

function levelColor(level) {
  const value = String(level || "").toUpperCase();
  if (value === "CRITICAL") return palette.red;
  if (value === "HIGH") return palette.orange;
  return palette.muted;
}

function prettyDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function statusColor(status) {
  const value = String(status || "OPEN").toUpperCase();
  if (value === "RESOLVED") return palette.teal;
  if (value === "ACKNOWLEDGED") return palette.blue;
  return palette.orange;
}

export default function AlertsManagement({ api, cameras = [] }) {
  const [alerts, setAlerts] = useState([]);
  const [historyByAlert, setHistoryByAlert] = useState({});
  const [expandedAlert, setExpandedAlert] = useState(null);
  const [cameraFilter, setCameraFilter] = useState("ALL");
  const [levelFilter, setLevelFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [officers, setOfficers] = useState({});
  const [notes, setNotes] = useState({});
  const [busyAlert, setBusyAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadAlerts = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);
    try {
      const result = await api.alerts({
        cameraId: cameraFilter === "ALL" ? undefined : cameraFilter,
        riskLevel: levelFilter === "ALL" ? undefined : levelFilter,
        status: statusFilter === "ALL" ? undefined : statusFilter,
        limit: 500,
      });
      setAlerts(Array.isArray(result?.alerts) ? result.alerts : []);
      setError("");
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to load persisted alerts:", err);
      setError(err?.message || "Unable to load alerts from the backend.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [api, cameraFilter, levelFilter, statusFilter]);

  useEffect(() => {
    loadAlerts(false);
    const timer = setInterval(() => loadAlerts(true), 5000);
    return () => clearInterval(timer);
  }, [loadAlerts]);

  const counts = useMemo(() => {
    const total = alerts.length;
    const critical = alerts.filter((a) => String(a.risk_level).toUpperCase() === "CRITICAL").length;
    const high = alerts.filter((a) => String(a.risk_level).toUpperCase() === "HIGH").length;
    const open = alerts.filter((a) => !["RESOLVED"].includes(String(a.status || "OPEN").toUpperCase())).length;
    return { total, critical, high, open };
  }, [alerts]);

  const runAction = async (alert, action, payload = {}) => {
    const id = alert.alert_id;
    if (!id) return;
    setBusyAlert(id);
    setError("");
    try {
      if (action === "acknowledge") await api.acknowledgeAlert(id, { actor: "operator" });
      if (action === "assign") {
        const officer = String(officers[id] || "").trim();
        if (!officer) throw new Error("Enter an officer name or ID before assigning.");
        await api.assignAlert(id, { actor: "operator", officer });
      }
      if (action === "resolve") await api.resolveAlert(id, { actor: "operator", note: notes[id] || "" });
      if (action === "reopen") await api.reopenAlert(id, { actor: "operator" });
      await loadAlerts(true);
      if (expandedAlert === id) await loadHistory(id);
    } catch (err) {
      setError(err?.message || `Could not ${action} this alert.`);
    } finally {
      setBusyAlert(null);
    }
  };

  const loadHistory = async (alertId) => {
    try {
      const result = await api.incidentHistory(alertId, 200);
      setHistoryByAlert((previous) => ({
        ...previous,
        [alertId]: Array.isArray(result?.history) ? result.history : [],
      }));
    } catch (err) {
      setError(err?.message || "Unable to load incident history.");
    }
  };

  const toggleHistory = async (alertId) => {
    if (expandedAlert === alertId) {
      setExpandedAlert(null);
      return;
    }
    setExpandedAlert(alertId);
    if (!historyByAlert[alertId]) await loadHistory(alertId);
  };

  const buttonStyle = (kind = "neutral") => ({
    border: `1px solid ${kind === "danger" ? "#7f3344" : kind === "primary" ? "#245477" : palette.border}`,
    background: kind === "danger" ? "#351522" : kind === "primary" ? "#102b42" : "#101f33",
    color: kind === "danger" ? palette.red : kind === "primary" ? palette.blue : palette.text,
    borderRadius: 7,
    padding: "7px 10px",
    fontSize: 11,
    fontWeight: 700,
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
  });

  const inputStyle = {
    background: "#081321",
    color: palette.text,
    border: `1px solid ${palette.border}`,
    borderRadius: 7,
    padding: "9px 10px",
    fontSize: 12,
    outline: "none",
    minWidth: 0,
  };

  return (
    <div style={{ color: palette.text, display: "grid", gap: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ color: palette.blue, fontSize: 10, fontWeight: 800, letterSpacing: 1.5 }}>INCIDENT RESPONSE / HUMAN-IN-THE-LOOP</div>
          <h2 style={{ margin: "7px 0 4px", fontSize: 22 }}>Alert Management</h2>
          <p style={{ margin: 0, color: palette.muted, fontSize: 12 }}>Persisted HIGH and CRITICAL operational risk alerts from the SQLite alert store.</p>
        </div>
        <button style={buttonStyle("primary")} onClick={() => loadAlerts(true)} disabled={refreshing}>
          <RefreshCw size={14} className={refreshing ? "cs-spin" : ""} /> Refresh
        </button>
      </div>

      {error && <div style={{ border: "1px solid #7f3344", background: "#2a1420", color: "#fecdd3", borderRadius: 9, padding: 11, fontSize: 12, display: "flex", gap: 8 }}><AlertTriangle size={15} />{error}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12 }}>
        {[
          ["TOTAL ALERTS", counts.total, palette.blue, BellRing],
          ["OPEN / ACTIVE", counts.open, palette.orange, ShieldAlert],
          ["HIGH", counts.high, palette.orange, AlertTriangle],
          ["CRITICAL", counts.critical, palette.red, XCircle],
        ].map(([label, value, color, Icon]) => (
          <div key={label} style={{ background: palette.panel, border: `1px solid ${palette.border}`, borderRadius: 10, padding: 15 }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: palette.muted, fontSize: 10, fontWeight: 800, letterSpacing: 1 }}><span>{label}</span><Icon size={15} color={color} /></div>
            <div style={{ color, fontSize: 27, fontWeight: 800, marginTop: 8 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 9, flexWrap: "wrap", background: palette.panel, border: `1px solid ${palette.border}`, borderRadius: 10, padding: 12 }}>
        <select aria-label="Filter by camera" style={inputStyle} value={cameraFilter} onChange={(e) => setCameraFilter(e.target.value)}>
          <option value="ALL">All cameras</option>
          {cameras.map((camera) => <option key={camera.camera_id} value={camera.camera_id}>{camera.camera_name || camera.camera_id}</option>)}
        </select>
        <select aria-label="Filter by risk level" style={inputStyle} value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
          <option value="ALL">All risk levels</option><option value="CRITICAL">Critical</option><option value="HIGH">High</option>
        </select>
        <select aria-label="Filter by status" style={inputStyle} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="ALL">All statuses</option><option value="OPEN">Open</option><option value="ACKNOWLEDGED">Acknowledged</option><option value="RESOLVED">Resolved</option>
        </select>
        <span style={{ marginLeft: "auto", color: palette.muted, fontSize: 10, alignSelf: "center" }}>Auto-refresh: 5 seconds{lastUpdated ? ` · Updated ${lastUpdated.toLocaleTimeString()}` : ""}</span>
      </div>

      <div style={{ display: "grid", gap: 11 }}>
        {loading ? (
          <div style={{ background: palette.panel, border: `1px solid ${palette.border}`, borderRadius: 10, padding: 28, textAlign: "center", color: palette.muted }}><RefreshCw size={18} className="cs-spin" /> <div style={{ marginTop: 8 }}>Loading persisted alerts…</div></div>
        ) : alerts.length === 0 ? (
          <div style={{ background: palette.panel, border: `1px solid ${palette.border}`, borderRadius: 10, padding: 32, textAlign: "center" }}>
            <CheckCircle2 size={25} color={palette.teal} />
            <h3 style={{ margin: "10px 0 5px", fontSize: 15 }}>No matching alerts</h3>
            <p style={{ margin: 0, color: palette.muted, fontSize: 12 }}>Only HIGH and CRITICAL risk windows are persisted as live alerts. Moderate and low windows are not listed here.</p>
          </div>
        ) : alerts.map((alert) => {
          const id = alert.alert_id;
          const level = String(alert.risk_level || "HIGH").toUpperCase();
          const status = String(alert.status || "OPEN").toUpperCase();
          const busy = busyAlert === id;
          const signals = Array.isArray(alert.active_signals) ? alert.active_signals : (alert.active_signals ? [String(alert.active_signals)] : []);
          return (
            <article key={id} style={{ background: palette.panel, border: `1px solid ${palette.border}`, borderLeft: `3px solid ${levelColor(level)}`, borderRadius: 10, overflow: "hidden" }}>
              <div style={{ padding: 15, display: "grid", gap: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                    <span style={{ color: levelColor(level), background: `${levelColor(level)}18`, border: `1px solid ${levelColor(level)}55`, borderRadius: 6, padding: "5px 8px", fontSize: 10, fontWeight: 900 }}>{level}</span>
                    <strong style={{ fontSize: 13 }}>{alert.camera_name || alert.camera_id || "Unknown camera"}</strong>
                    <span style={{ color: palette.muted, fontSize: 10 }}>{alert.camera_id}</span>
                  </div>
                  <span style={{ color: statusColor(status), background: `${statusColor(status)}18`, borderRadius: 6, padding: "5px 8px", fontSize: 10, fontWeight: 800 }}>{status}</span>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(125px, 1fr))", gap: 10 }}>
                  <Metric label="RISK SCORE" value={Number.isFinite(Number(alert.risk_score)) ? Number(alert.risk_score).toFixed(1) : "—"} />
                  <Metric label="DOMINANT FACTOR" value={alert.dominant_factor || "—"} />
                  <Metric label="RESPONSE ACTION" value={alert.response_action || "—"} />
                  <Metric label="PRIORITY" value={alert.response_priority || "—"} />
                  <Metric label="GENERATED" value={prettyDate(alert.created_at || alert.start_time)} />
                  <Metric label="WINDOW" value={alert.window_id ?? "—"} />
                </div>

                {alert.response_reason && <p style={{ margin: 0, color: palette.muted, fontSize: 12, lineHeight: 1.5 }}>{alert.response_reason}</p>}
                {signals.length > 0 && <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>{signals.map((signal, index) => <span key={`${signal}-${index}`} style={{ background: palette.panel2, border: `1px solid ${palette.border}`, borderRadius: 20, padding: "4px 8px", color: palette.muted, fontSize: 10 }}>{signal}</span>)}</div>}
                {alert.assigned_officer && <div style={{ color: palette.muted, fontSize: 11 }}><UserRound size={12} style={{ verticalAlign: "-2px", marginRight: 5 }} />Assigned to: {alert.assigned_officer}</div>}

                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", borderTop: `1px solid ${palette.border}`, paddingTop: 12 }}>
                  {status === "OPEN" && <button style={buttonStyle("primary")} disabled={busy} onClick={() => runAction(alert, "acknowledge")}> <CheckCircle2 size={13} /> Acknowledge</button>}
                  {status !== "RESOLVED" && <>
                    <input aria-label={`Officer for ${id}`} style={{ ...inputStyle, width: 160 }} placeholder="Officer name / ID" value={officers[id] || ""} onChange={(e) => setOfficers((p) => ({ ...p, [id]: e.target.value }))} />
                    <button style={buttonStyle()} disabled={busy} onClick={() => runAction(alert, "assign")}><UserRound size={13} /> Assign</button>
                    <input aria-label={`Resolution note for ${id}`} style={{ ...inputStyle, flex: "1 1 180px" }} placeholder="Resolution note (optional)" value={notes[id] || ""} onChange={(e) => setNotes((p) => ({ ...p, [id]: e.target.value }))} />
                    <button style={buttonStyle("danger")} disabled={busy} onClick={() => runAction(alert, "resolve")}><CheckCircle2 size={13} /> Resolve</button>
                  </>}
                  {status === "RESOLVED" && <button style={buttonStyle()} disabled={busy} onClick={() => runAction(alert, "reopen")}><RotateCcw size={13} /> Reopen</button>}
                  <button style={{ ...buttonStyle(), marginLeft: "auto" }} onClick={() => toggleHistory(id)}><Clock3 size={13} /> {expandedAlert === id ? "Hide history" : "Incident history"}</button>
                  {busy && <span style={{ color: palette.muted, fontSize: 10 }}>Saving…</span>}
                </div>
              </div>

              {expandedAlert === id && <div style={{ borderTop: `1px solid ${palette.border}`, background: "#081321", padding: 14 }}>
                <strong style={{ display: "block", fontSize: 11, marginBottom: 10 }}>AUDIT TRAIL</strong>
                {(historyByAlert[id] || []).length === 0 ? <span style={{ color: palette.muted, fontSize: 11 }}>No history events returned yet.</span> : <div style={{ display: "grid", gap: 9 }}>{historyByAlert[id].map((event, index) => <div key={`${event.id || event.created_at || index}`} style={{ display: "flex", justifyContent: "space-between", gap: 12, borderBottom: `1px solid ${palette.border}`, paddingBottom: 8, fontSize: 11 }}><div><strong>{event.action || event.event_type || "EVENT"}</strong><div style={{ color: palette.muted, marginTop: 3 }}>{event.actor || "system"}{event.note ? ` · ${event.note}` : ""}</div></div><span style={{ color: palette.muted, whiteSpace: "nowrap" }}>{prettyDate(event.created_at || event.timestamp)}</span></div>)}</div>}
              </div>}
            </article>
          );
        })}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8, color: palette.muted, fontSize: 10 }}><ShieldAlert size={13} /> AI-generated decision support only. Human review is required; no autonomous emergency action is performed.</div>
    </div>
  );
}

function Metric({ label, value }) {
  return <div style={{ minWidth: 0 }}><div style={{ color: palette.muted, fontSize: 9, fontWeight: 800, letterSpacing: 0.8, marginBottom: 4 }}>{label}</div><div title={String(value)} style={{ color: palette.text, fontSize: 11, fontWeight: 700, overflowWrap: "anywhere" }}>{value}</div></div>;
}