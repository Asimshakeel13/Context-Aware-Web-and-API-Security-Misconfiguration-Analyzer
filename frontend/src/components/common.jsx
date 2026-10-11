import { scoreColor, SEV_COLOR } from "../lib/format.js";

export function SeverityBadge({ severity }) {
  return <span className={`badge sev-${severity}`}>{severity}</span>;
}

export function ContextBadge({ ctx }) {
  if (!ctx) return <span className="faint">—</span>;
  return <span className={`ctx ctx-${ctx}`}>{ctx}</span>;
}

export function StatusChip({ status }) {
  return <span className={`status-chip st-${status}`}>{status}</span>;
}

export function ScoreMeter({ score }) {
  const pct = Math.max(0, Math.min(100, (score / 10) * 100));
  const color = scoreColor(score);
  return (
    <div className="score-meter">
      <div className="score-bar">
        <div style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="score-num" style={{ color }}>{score?.toFixed(1)}</span>
    </div>
  );
}

export function StatCard({ label, value, sub, color }) {
  return (
    <div className="card stat">
      {color && <span className="stat-accent" style={{ background: color }} />}
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={color ? { color } : undefined}>{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export function Spinner({ large }) {
  return <div className={`spinner ${large ? "spinner-lg" : ""}`} />;
}

export function CenterLoad({ text = "Loading…" }) {
  return (
    <div className="center-load">
      <Spinner large />
      <span>{text}</span>
    </div>
  );
}

export function EmptyState({ icon, title, children }) {
  return (
    <div className="empty">
      {icon}
      <h3 style={{ color: "var(--text-dim)", fontWeight: 600, marginBottom: 6 }}>{title}</h3>
      {children && <p className="faint" style={{ maxWidth: 420, margin: "0 auto" }}>{children}</p>}
    </div>
  );
}

export function SeverityDistribution({ summary }) {
  const order = ["critical", "high", "medium", "low", "info"];
  const total = order.reduce((a, k) => a + (summary[k] || 0), 0);
  return (
    <div>
      <div className="sevdist">
        {total === 0 && <div style={{ width: "100%", background: "var(--border-soft)" }} />}
        {order.map((k) =>
          summary[k] ? (
            <div
              key={k}
              title={`${k}: ${summary[k]}`}
              style={{ width: `${(summary[k] / total) * 100}%`, background: SEV_COLOR[k.toUpperCase()] }}
            />
          ) : null
        )}
      </div>
      <div className="sevdist-legend">
        {order.map((k) => (
          <span key={k}>
            <i className="dot" style={{ background: SEV_COLOR[k.toUpperCase()] }} />
            {k.charAt(0).toUpperCase() + k.slice(1)} <b style={{ color: "var(--text)", fontFamily: "var(--mono)" }}>{summary[k] || 0}</b>
          </span>
        ))}
      </div>
    </div>
  );
}
