// Thin API client over the CAWASMA REST backend.
// If the backend is unreachable, it transparently falls back to mock data and
// flips `demoMode` so the UI can show a banner. This keeps the FYP demo safe.

import { API_BASE } from "../config.js";
import { MOCK } from "./mock.js";

let demoMode = false;
const listeners = new Set();

export function onDemoModeChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
export function isDemoMode() {
  return demoMode;
}
function setDemo(on) {
  if (demoMode !== on) {
    demoMode = on;
    listeners.forEach((fn) => fn(on));
  }
}

async function req(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.error?.message || body?.detail || detail;
    } catch { /* ignore */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  setDemo(false);
  if (res.status === 204) return null;
  return res.json();
}

// Wrap a live call; on network failure, use the mock fallback.
async function withFallback(liveFn, mockValue) {
  try {
    return await liveFn();
  } catch (e) {
    if (e.status) throw e; // real HTTP error (e.g. 404) — surface it
    setDemo(true); // network/connection failure -> demo mode
    return typeof mockValue === "function" ? mockValue() : mockValue;
  }
}

export const api = {
  async health() {
    return withFallback(() => req("/api/health"), MOCK.health);
  },

  async createScan(targetUrl) {
    return withFallback(
      () =>
        req("/api/scans", {
          method: "POST",
          body: JSON.stringify({ target_url: targetUrl }),
        }),
      () => ({ scan_id: MOCK.SCAN_ID, status: "QUEUED" })
    );
  },

  async listScans(page = 1, limit = 20) {
    return withFallback(
      () => req(`/api/scans?page=${page}&limit=${limit}`),
      () => ({ items: MOCK.scans, meta: { page: 1, limit, total: MOCK.scans.length, pages: 1 } })
    );
  },

  async getScan(id) {
    return withFallback(() => req(`/api/scans/${id}`), () => MOCK.scan);
  },

  async getStatus(id) {
    return withFallback(
      () => req(`/api/scans/${id}/status`),
      () => ({ scan_id: id, status: MOCK.scan.status, progress: 100, current_stage: "completed" })
    );
  },

  async listFindings(id, page = 1, limit = 100) {
    return withFallback(
      () => req(`/api/scans/${id}/findings?page=${page}&limit=${limit}`),
      () => ({ items: MOCK.findings, meta: { page: 1, limit, total: MOCK.findings.length, pages: 1 } })
    );
  },

  async listEndpoints(id, page = 1, limit = 100) {
    return withFallback(
      () => req(`/api/scans/${id}/endpoints?page=${page}&limit=${limit}`),
      () => ({ items: MOCK.endpoints, meta: { page: 1, limit, total: MOCK.endpoints.length, pages: 1 } })
    );
  },

  async listChains(id) {
    return withFallback(() => req(`/api/scans/${id}/chains`), () => MOCK.chains);
  },

  async deleteScan(id) {
    return withFallback(() => req(`/api/scans/${id}`, { method: "DELETE" }), null);
  },

  reportUrl(id, format) {
    return `${API_BASE}/api/scans/${id}/report?format=${format}&download=true`;
  },
};
