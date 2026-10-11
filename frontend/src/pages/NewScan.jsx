import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { useToast } from "../components/Toast.jsx";
import { Spinner } from "../components/common.jsx";
import { IconScan, IconShield, IconGlobe, IconChain } from "../lib/icons.jsx";

const EXAMPLES = ["https://example.com", "https://scanme.nmap.org", "https://badssl.com"];

export default function NewScan() {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const nav = useNavigate();
  const toast = useToast();

  async function submit(e) {
    e.preventDefault();
    setError(null);
    const target = url.trim();
    if (!/^https:\/\/.+/.test(target)) {
      setError("Target must be a valid HTTPS URL (e.g. https://example.com).");
      return;
    }
    setBusy(true);
    try {
      const { scan_id } = await api.createScan(target);
      toast("Scan queued", "ok");
      nav(`/scans/${scan_id}`);
    } catch (err) {
      setError(err.message || "Failed to create scan.");
      toast("Could not start scan", "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 680, margin: "0 auto" }}>
      <div className="card" style={{ padding: "28px 30px" }}>
        <div className="row" style={{ marginBottom: 6 }}>
          <IconScan style={{ color: "var(--accent)", width: 22, height: 22 }} />
          <h2 style={{ fontSize: 19 }}>Start a new scan</h2>
        </div>
        <p className="muted" style={{ marginTop: 0 }}>
          Enter an HTTPS target. CAWASMA runs a safe, black-box analysis: endpoint discovery,
          context classification, 58 security checks, and context-aware risk scoring.
        </p>

        <form onSubmit={submit} className="mt-20">
          <label className="label">Target URL</label>
          <input
            className="input"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            autoFocus
            spellCheck={false}
          />
          <div className="row wrap gap-sm mt-16">
            <span className="faint" style={{ fontSize: 12 }}>Try:</span>
            {EXAMPLES.map((ex) => (
              <button type="button" key={ex} className="pill" style={{ cursor: "pointer" }} onClick={() => setUrl(ex)}>
                {ex}
              </button>
            ))}
          </div>

          {error && (
            <div className="limit-box" style={{ color: "var(--crit)", background: "var(--crit-bg)", borderColor: "rgba(240,82,107,0.25)", marginTop: 16 }}>
              {error}
            </div>
          )}

          <button className="btn btn-primary mt-20" disabled={busy} style={{ width: "100%", padding: "12px" }}>
            {busy ? <Spinner /> : <IconScan />} {busy ? "Starting…" : "Launch Scan"}
          </button>
        </form>
      </div>

      <div className="grid cols-3 mt-20">
        <Feature icon={<IconGlobe />} title="Black-box & safe" text="HTTPS-only, SSRF-guarded, non-destructive GET/HEAD/OPTIONS probing." />
        <Feature icon={<IconShield />} title="Context-aware" text="Risk is weighted by endpoint sensitivity and response data." />
        <Feature icon={<IconChain />} title="Attack chains" text="Correlates findings into higher-impact exploitation paths." />
      </div>
    </div>
  );
}

function Feature({ icon, title, text }) {
  return (
    <div className="card">
      <span style={{ color: "var(--accent)" }}>{icon}</span>
      <h4 style={{ marginTop: 10, fontSize: 14 }}>{title}</h4>
      <p className="muted" style={{ margin: "6px 0 0", fontSize: 12.5 }}>{text}</p>
    </div>
  );
}
