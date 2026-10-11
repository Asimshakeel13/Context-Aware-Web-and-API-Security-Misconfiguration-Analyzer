import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { api, onDemoModeChange, isDemoMode } from "../api/client.js";
import { IconShield, IconGrid, IconPlus } from "../lib/icons.jsx";

export default function Layout({ children }) {
  const [health, setHealth] = useState(null);
  const [demo, setDemo] = useState(isDemoMode());
  const loc = useLocation();

  useEffect(() => {
    const off = onDemoModeChange(setDemo);
    api.health().then(setHealth).catch(() => {});
    return off;
  }, []);

  const dbState = health?.dependencies?.database;
  const healthClass =
    health?.status === "demo" ? "health-degraded"
      : health?.status === "ok" || health?.status === "healthy" ? "health-ok"
      : health?.status ? "health-degraded" : "health-down";

  const title =
    loc.pathname === "/" ? "Dashboard"
      : loc.pathname.startsWith("/new") ? "New Scan"
      : loc.pathname.startsWith("/scans/") ? "Scan Report"
      : "CAWASMA";

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <IconShield className="brand-logo" style={{ color: "var(--accent)" }} />
          <div>
            <div className="brand-name">CAWASMA</div>
            <div className="brand-sub">Security Analyzer</div>
          </div>
        </div>

        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <IconGrid /> Dashboard
          </NavLink>
          <NavLink to="/new" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <IconPlus /> New Scan
          </NavLink>
        </nav>

        <div className="sidebar-foot">
          <div>
            <span className={`health-dot ${healthClass}`} />
            Backend: {health ? (health.status === "demo" ? "offline (demo)" : health.status) : "checking…"}
          </div>
          {dbState && <div style={{ marginTop: 4 }}>DB: {dbState} · Redis: {health?.dependencies?.redis}</div>}
          <div style={{ marginTop: 10, opacity: 0.7 }}>Context-Aware Web &amp; API<br />Misconfiguration Analyzer</div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <h1>{title}</h1>
          <NavLink to="/new" className="btn btn-primary btn-sm">
            <IconPlus /> New Scan
          </NavLink>
        </header>
        <div className="content">
          {demo && (
            <div className="demo-banner">
              ⚠ Backend not reachable — showing <b>&nbsp;demo data</b>. Start the backend
              (<code>docker compose up</code>) to run real scans.
            </div>
          )}
          {children}
        </div>
      </main>
    </div>
  );
}
