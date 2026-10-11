import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { useScanProgress } from "../hooks/useScanProgress.js";
import {
  SeverityBadge, ContextBadge, StatusChip, ScoreMeter, StatCard,
  CenterLoad, EmptyState, SeverityDistribution, Spinner,
} from "../components/common.jsx";
import {
  fmtDate, fmtDuration, categoryLabel, SEVERITIES, scoreColor,
} from "../lib/format.js";
import {
  IconArrowLeft, IconDownload, IconBug, IconEndpoint, IconChain,
  IconGlobe, IconClose, IconLightning, IconDoc, IconExternal,
} from "../lib/icons.jsx";

const STAGE_LABEL = {
  initializing: "Initializing", crawling: "Discovering endpoints",
  tls: "Probing TLS", analyzing: "Running security checks",
  correlating: "Correlating attack chains", completed: "Completed",
};

export default function ScanDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try { setScan(await api.getScan(id)); } finally { setLoading(false); }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  const { progress, stage, status } = useScanProgress(id, scan?.status);

  // When the scan reaches a terminal state, reload the full detail (summary).
  useEffect(() => {
    if (["COMPLETED", "FAILED", "CANCELLED"].includes(status)) {
      load();
    }
  }, [status, load]);

  if (loading) return <CenterLoad text="Loading scan…" />;
  if (!scan) return <EmptyState icon={<IconBug />} title="Scan not found" />;

  const liveStatus = status || scan.status;
  const isDone = liveStatus === "COMPLETED";
  const isFailed = liveStatus === "FAILED";
  const running = ["QUEUED", "RUNNING"].includes(liveStatus);

  return (
    <div>
      <button className="btn btn-ghost btn-sm" onClick={() => nav("/")} style={{ marginBottom: 14 }}>
        <IconArrowLeft /> Back
      </button>

      <div className="card spread wrap" style={{ marginBottom: 20 }}>
        <div>
          <div className="row gap-sm">
            <IconGlobe style={{ color: "var(--accent)", width: 18, height: 18 }} />
            <h2 style={{ fontSize: 17, fontFamily: "var(--mono)" }}>{scan.target_url}</h2>
          </div>
          <div className="row wrap gap-sm" style={{ marginTop: 8 }}>
            <StatusChip status={liveStatus} />
            <span className="faint" style={{ fontSize: 12 }}>
              Started {fmtDate(scan.started_at || scan.created_at)} · Duration {fmtDuration(scan.duration_seconds)}
            </span>
          </div>
        </div>
        {isDone && <ReportButtons id={id} />}
      </div>

      {running && <LiveProgress progress={progress} stage={stage} />}
      {isFailed && (
        <div className="limit-box" style={{ color: "var(--crit)", background: "var(--crit-bg)", borderColor: "rgba(240,82,107,0.25)" }}>
          Scan failed: {scan.error_message || "unknown error"}
        </div>
      )}
      {isDone && <Results id={id} summary={scan.summary} />}
    </div>
  );
}

function LiveProgress({ progress, stage }) {
  return (
    <div className="card" style={{ textAlign: "center", padding: "40px 24px" }}>
      <div className="row" style={{ justifyContent: "center", marginBottom: 18 }}>
        <Spinner large />
      </div>
      <h3 style={{ fontSize: 16 }}>{STAGE_LABEL[stage] || "Scanning…"}</h3>
      <p className="muted" style={{ marginTop: 4 }}>Live progress — this page updates automatically.</p>
      <div style={{ maxWidth: 480, margin: "22px auto 0" }}>
        <div className="progress-track" style={{ height: 10 }}>
          <div className={`progress-fill ${progress ? "" : "indeterminate"}`} style={{ width: `${progress || 0}%` }} />
        </div>
        <div className="mono mt-16" style={{ fontSize: 22, fontWeight: 700, color: "var(--accent)" }}>{progress || 0}%</div>
      </div>
    </div>
  );
}

function ReportButtons({ id }) {
  const fmts = [
    { f: "html", label: "HTML" },
    { f: "pdf", label: "PDF" },
    { f: "csv", label: "CSV" },
    { f: "json", label: "JSON" },
  ];
  return (
    <div className="row wrap gap-sm">
      <span className="faint" style={{ fontSize: 12 }}>Report:</span>
      {fmts.map(({ f, label }) => (
        <a key={f} className="btn btn-sm" href={api.reportUrl(id, f)} target="_blank" rel="noreferrer">
          <IconDownload style={{ width: 14, height: 14 }} /> {label}
        </a>
      ))}
    </div>
  );
}

/* ----------------------------- results ------------------------------- */
function Results({ id, summary }) {
  const [tab, setTab] = useState("findings");
  const [findings, setFindings] = useState(null);
  const [endpoints, setEndpoints] = useState(null);
  const [chains, setChains] = useState(null);

  useEffect(() => {
    // Page through results (backend caps page size at 100).
    async function loadAll(fn) {
      let page = 1, pages = 1, all = [];
      do {
        const r = await fn(page, 100);
        all = all.concat(r.items || []);
        pages = r.meta?.pages || 1;
        page += 1;
      } while (page <= pages);
      return all;
    }
    loadAll((p, l) => api.listFindings(id, p, l)).then(setFindings).catch(() => setFindings([]));
    loadAll((p, l) => api.listEndpoints(id, p, l)).then(setEndpoints).catch(() => setEndpoints([]));
    api.listChains(id).then(setChains).catch(() => setChains([]));
  }, [id]);

  const sum = summary || { endpoints: 0, findings: 0, critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  const highest = findings?.reduce((m, f) => Math.max(m, f.cawasma_final_score || 0), 0) || 0;

  return (
    <div>
      <div className="grid cols-4" style={{ marginBottom: 18 }}>
        <StatCard label="Endpoints" value={sum.endpoints} color="var(--accent)" />
        <StatCard label="Findings" value={sum.findings} color="var(--high)" />
        <StatCard label="Attack Chains" value={chains?.length ?? "—"} color="var(--crit)" />
        <StatCard label="Highest Score" value={highest.toFixed(1)} sub="context-aware" color={scoreColor(highest)} />
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-title">Severity Distribution</div>
        <SeverityDistribution summary={sum} />
      </div>

      <div className="tabs">
        <button className={`tab ${tab === "findings" ? "active" : ""}`} onClick={() => setTab("findings")}>
          Findings <span className="count">{findings?.length ?? "…"}</span>
        </button>
        <button className={`tab ${tab === "chains" ? "active" : ""}`} onClick={() => setTab("chains")}>
          Attack Chains <span className="count">{chains?.length ?? "…"}</span>
        </button>
        <button className={`tab ${tab === "endpoints" ? "active" : ""}`} onClick={() => setTab("endpoints")}>
          Endpoints <span className="count">{endpoints?.length ?? "…"}</span>
        </button>
      </div>

      {tab === "findings" && <FindingsTab findings={findings} />}
      {tab === "chains" && <ChainsTab chains={chains} />}
      {tab === "endpoints" && <EndpointsTab endpoints={endpoints} />}
    </div>
  );
}

/* ---- findings ---- */
function FindingsTab({ findings }) {
  const [filter, setFilter] = useState("ALL");
  const [selected, setSelected] = useState(null);
  if (!findings) return <CenterLoad text="Loading findings…" />;
  if (findings.length === 0) return <div className="card"><EmptyState icon={<IconBug />} title="No findings" >No misconfigurations were detected.</EmptyState></div>;

  const counts = findings.reduce((a, f) => ((a[f.severity] = (a[f.severity] || 0) + 1), a), {});
  const shown = findings
    .filter((f) => filter === "ALL" || f.severity === filter)
    .sort((a, b) => (b.cawasma_final_score || 0) - (a.cawasma_final_score || 0));

  return (
    <div>
      <div className="row wrap gap-sm" style={{ marginBottom: 14 }}>
        <Chip active={filter === "ALL"} onClick={() => setFilter("ALL")}>All <b>{findings.length}</b></Chip>
        {SEVERITIES.filter((s) => counts[s]).map((s) => (
          <Chip key={s} active={filter === s} onClick={() => setFilter(s)} sev={s}>{s} <b>{counts[s]}</b></Chip>
        ))}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Severity</th><th>Score</th><th>Rule</th><th>Finding</th>
              <th>Context</th><th>CVSS Base</th><th></th>
            </tr>
          </thead>
          <tbody>
            {shown.map((f) => (
              <tr key={f.id} className="clickable" onClick={() => setSelected(f)}>
                <td><SeverityBadge severity={f.severity} /></td>
                <td style={{ width: 130 }}><ScoreMeter score={f.cawasma_final_score} /></td>
                <td><span className="pill">{f.rule_id}</span></td>
                <td>
                  <div style={{ fontWeight: 500 }}>{f.title}</div>
                  {f.limitation && <div className="faint" style={{ fontSize: 11, marginTop: 2 }}>⚠ limitation noted</div>}
                </td>
                <td><ContextBadge ctx={f.context_class} /></td>
                <td className="mono muted" style={{ fontSize: 12.5 }}>{f.cvss_base_score?.toFixed(1)}</td>
                <td style={{ textAlign: "right" }}><IconExternal style={{ width: 15, height: 15, color: "var(--text-faint)" }} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && <FindingDrawer finding={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function Chip({ active, onClick, children, sev }) {
  const style = sev && active ? { color: `var(--${sevVar(sev)})`, borderColor: "currentColor" } : {};
  return (
    <button className="btn btn-sm" onClick={onClick} style={{ background: active ? "var(--panel-hover)" : "transparent", ...style }}>
      {children}
    </button>
  );
}
const sevVar = (s) => ({ CRITICAL: "crit", HIGH: "high", MEDIUM: "med", LOW: "low", INFO: "info" }[s]);

function FindingDrawer({ finding: f, onClose }) {
  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div className="spread" style={{ alignItems: "flex-start" }}>
          <div>
            <div className="row gap-sm" style={{ marginBottom: 6 }}>
              <SeverityBadge severity={f.severity} />
              <span className="pill">{f.rule_id}</span>
              <span className="pill">{categoryLabel(f.category)}</span>
            </div>
            <h3>{f.title}</h3>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><IconClose /></button>
        </div>

        <div className="card mt-16" style={{ background: "var(--bg-grid)" }}>
          <div className="card-title mb-0" style={{ marginBottom: 12 }}>Context-Aware Score</div>
          <div className="row" style={{ justifyContent: "space-between", fontSize: 13, fontFamily: "var(--mono)" }}>
            <span className="muted">CVSS base</span><b>{f.cvss_base_score?.toFixed(1)}</b>
          </div>
          <ScoreLine label="× context multiplier" value={`×${f.cawasma_context_multiplier}`} />
          <ScoreLine label="+ response bonus" value={`+${f.response_bonus ?? 0}`} />
          <div className="row" style={{ justifyContent: "space-between", fontSize: 15, fontFamily: "var(--mono)", marginTop: 10, paddingTop: 10, borderTop: "1px solid var(--border-soft)" }}>
            <b>Final score</b>
            <b style={{ color: scoreColor(f.cawasma_final_score) }}>{f.cawasma_final_score?.toFixed(1)}</b>
          </div>
          <div className="faint" style={{ fontSize: 11, marginTop: 8 }}>
            Final = min(10, base × context + bonus). This is CAWASMA's custom prioritization metric, not an official CVSS score.
          </div>
        </div>

        <dl className="kv">
          <dt>CVSS vector</dt><dd className="mono" style={{ fontSize: 11.5, wordBreak: "break-all" }}>{f.cvss_vector || "—"}</dd>
          <dt>Endpoint context</dt><dd><ContextBadge ctx={f.context_class} /> {f.context_confidence != null && <span className="faint">({(f.context_confidence * 100).toFixed(0)}% conf.)</span>}</dd>
        </dl>

        {f.impact && <Block title="Impact">{f.impact}</Block>}
        {f.evidence && <Block title="Evidence (redacted)"><div className="evidence-box">{f.evidence}</div></Block>}
        {f.recommendation && <Block title="Recommendation">{f.recommendation}</Block>}
        {f.limitation && (
          <div className="section-block">
            <h4>Black-box limitation</h4>
            <div className="limit-box">{f.limitation}</div>
          </div>
        )}
        {f.references?.length > 0 && (
          <Block title="References">
            {f.references.map((r, i) => (
              <div key={i}><a href={r} target="_blank" rel="noreferrer" style={{ color: "var(--accent)", fontSize: 12.5 }}>{r}</a></div>
            ))}
          </Block>
        )}
      </div>
    </>
  );
}
const ScoreLine = ({ label, value }) => (
  <div className="row" style={{ justifyContent: "space-between", fontSize: 13, fontFamily: "var(--mono)", marginTop: 6 }}>
    <span className="muted">{label}</span><span>{value}</span>
  </div>
);
const Block = ({ title, children }) => (
  <div className="section-block"><h4>{title}</h4><div style={{ fontSize: 13 }}>{children}</div></div>
);

/* ---- chains ---- */
function ChainsTab({ chains }) {
  if (!chains) return <CenterLoad text="Loading chains…" />;
  if (chains.length === 0) return <div className="card"><EmptyState icon={<IconChain />} title="No attack chains" >No finding combinations matched a known exploitation path.</EmptyState></div>;
  return (
    <div className="grid" style={{ gap: 14 }}>
      {chains.map((c) => {
        const steps = c.name.split(/→|->/).map((s) => s.trim());
        return (
          <div key={c.id} className="chain-card">
            <div className="spread wrap">
              <div className="row gap-sm">
                <IconLightning style={{ color: "var(--crit)", width: 18, height: 18 }} />
                <span className="pill">{c.chain_code}</span>
                <SeverityBadge severity={c.severity} />
              </div>
              <div className="row gap-sm">
                <span className="faint" style={{ fontSize: 12 }}>Composite</span>
                <span className="mono" style={{ fontSize: 17, fontWeight: 700, color: scoreColor(c.template_composite_score) }}>{c.template_composite_score}</span>
              </div>
            </div>
            <div className="chain-flow">
              {steps.map((s, i) => (
                <span key={i} className="row gap-sm">
                  <span className="chain-node">{s}</span>
                  {i < steps.length - 1 && <span className="chain-arrow">→</span>}
                </span>
              ))}
            </div>
            {c.description && <p className="muted" style={{ margin: 0, fontSize: 12.5 }}>{c.description}</p>}
          </div>
        );
      })}
    </div>
  );
}

/* ---- endpoints ---- */
function EndpointsTab({ endpoints }) {
  if (!endpoints) return <CenterLoad text="Loading endpoints…" />;
  if (endpoints.length === 0) return <div className="card"><EmptyState icon={<IconEndpoint />} title="No endpoints" /></div>;
  const order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  const sorted = [...endpoints].sort((a, b) => (order[a.context_class] ?? 9) - (order[b.context_class] ?? 9));
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Path</th><th>Method</th><th>Status</th><th>Context</th><th>Confidence</th><th>Discovered</th></tr>
        </thead>
        <tbody>
          {sorted.map((e) => (
            <tr key={e.id}>
              <td className="mono" style={{ fontSize: 12.5 }}><span className="truncate" style={{ display: "inline-block" }}>{e.path}</span></td>
              <td><span className="pill">{e.method}</span></td>
              <td className="mono muted">{e.status_code ?? "—"}</td>
              <td><ContextBadge ctx={e.context_class} /></td>
              <td className="mono muted" style={{ fontSize: 12.5 }}>{e.context_confidence != null ? `${(e.context_confidence * 100).toFixed(0)}%` : "—"}</td>
              <td><span className="pill">{e.discovered_by}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
