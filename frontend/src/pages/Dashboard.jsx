import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { useToast } from "../components/Toast.jsx";
import { StatusChip, CenterLoad, EmptyState } from "../components/common.jsx";
import { fmtDate, fmtDuration } from "../lib/format.js";
import { IconScan, IconTrash, IconGlobe, IconPlus } from "../lib/icons.jsx";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();
  const toast = useToast();

  async function load() {
    try {
      const res = await api.listScans(1, 50);
      setData(res);
    } catch {
      setData({ items: [], meta: { total: 0 } });
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); }, []);

  // Auto-refresh while any scan is active.
  useEffect(() => {
    const active = data?.items?.some((s) => ["QUEUED", "RUNNING"].includes(s.status));
    if (!active) return;
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, [data]);

  async function del(e, id) {
    e.stopPropagation();
    if (!confirm("Delete this scan and all its findings?")) return;
    try {
      await api.deleteScan(id);
      toast("Scan deleted", "ok");
      load();
    } catch {
      toast("Delete failed", "err");
    }
  }

  if (loading) return <CenterLoad text="Loading scans…" />;

  const scans = data?.items || [];
  const totals = scans.reduce(
    (a, s) => {
      a.total++;
      if (s.status === "RUNNING" || s.status === "QUEUED") a.active++;
      if (s.status === "COMPLETED") a.done++;
      return a;
    },
    { total: 0, active: 0, done: 0 }
  );

  return (
    <div>
      <div className="grid cols-3" style={{ marginBottom: 22 }}>
        <Stat label="Total Scans" value={totals.total} color="var(--accent)" />
        <Stat label="Active" value={totals.active} color="var(--med)" sub={totals.active ? "running now" : "idle"} />
        <Stat label="Completed" value={totals.done} color="var(--low)" />
      </div>

      <div className="spread" style={{ marginBottom: 14 }}>
        <h2 style={{ fontSize: 16 }}>Scan History</h2>
      </div>

      {scans.length === 0 ? (
        <div className="card">
          <EmptyState icon={<IconScan />} title="No scans yet" >
            Launch your first scan to see endpoints, findings, attack chains and context-aware
            risk scoring here.
          </EmptyState>
          <div style={{ textAlign: "center", marginTop: -20, paddingBottom: 24 }}>
            <button className="btn btn-primary" onClick={() => nav("/new")}><IconPlus /> New Scan</button>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Target</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Started</th>
                <th>Duration</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id} className="clickable" onClick={() => nav(`/scans/${s.id}`)}>
                  <td>
                    <div className="row gap-sm">
                      <IconGlobe style={{ width: 15, height: 15, color: "var(--text-faint)" }} />
                      <span className="truncate" style={{ fontFamily: "var(--mono)", fontSize: 12.5 }}>{s.target_url}</span>
                    </div>
                  </td>
                  <td><StatusChip status={s.status} /></td>
                  <td style={{ width: 160 }}>
                    {["RUNNING", "QUEUED"].includes(s.status) ? (
                      <div className="progress-track"><div className="progress-fill" style={{ width: `${s.progress}%` }} /></div>
                    ) : (
                      <span className="faint mono" style={{ fontSize: 12 }}>{s.progress}%</span>
                    )}
                  </td>
                  <td className="muted" style={{ fontSize: 12.5 }}>{fmtDate(s.started_at || s.created_at)}</td>
                  <td className="muted mono" style={{ fontSize: 12.5 }}>{fmtDuration(s.duration_seconds)}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-ghost btn-sm" onClick={(e) => del(e, s.id)} title="Delete">
                      <IconTrash style={{ width: 15, height: 15 }} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, sub, color }) {
  return (
    <div className="card stat">
      <span className="stat-accent" style={{ background: color }} />
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}
