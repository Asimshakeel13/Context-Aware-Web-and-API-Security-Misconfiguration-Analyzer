// Live scan progress via WebSocket, with graceful polling fallback.
import { useEffect, useRef, useState } from "react";
import { WS_BASE } from "../config.js";
import { api } from "../api/client.js";

const TERMINAL = new Set(["COMPLETED", "FAILED", "CANCELLED"]);

export function useScanProgress(scanId, initialStatus) {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState(null);
  const [status, setStatus] = useState(initialStatus || "QUEUED");
  const wsRef = useRef(null);
  const pollRef = useRef(null);

  useEffect(() => {
    if (!scanId) return;
    if (TERMINAL.has(initialStatus)) {
      setStatus(initialStatus);
      setProgress(100);
      return;
    }

    let closed = false;

    // Primary: WebSocket.
    try {
      const ws = new WebSocket(`${WS_BASE}/ws/scans/${scanId}`);
      wsRef.current = ws;
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data.percent != null) setProgress(data.percent);
          if (data.stage) setStage(data.stage);
          if (data.status) setStatus(data.status);
          if (data.percent >= 100 || data.stage === "completed") {
            setStatus((s) => (TERMINAL.has(s) ? s : "COMPLETED"));
          }
        } catch { /* ignore */ }
      };
      ws.onerror = () => startPolling();
      ws.onclose = () => { if (!closed) ensureFinal(); };
    } catch {
      startPolling();
    }

    // Fallback / safety net: poll status.
    function startPolling() {
      if (pollRef.current) return;
      pollRef.current = setInterval(async () => {
        try {
          const st = await api.getStatus(scanId);
          setProgress(st.progress ?? 0);
          setStage(st.current_stage);
          setStatus(st.status);
          if (TERMINAL.has(st.status)) stopPolling();
        } catch { /* ignore */ }
      }, 1500);
    }
    function stopPolling() {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    }
    async function ensureFinal() {
      try {
        const st = await api.getStatus(scanId);
        setStatus(st.status);
        setProgress(st.progress ?? 100);
      } catch { /* ignore */ }
    }

    // Always run a slow poll too, in case WS silently stalls.
    startPolling();

    return () => {
      closed = true;
      stopPolling();
      try { wsRef.current?.close(); } catch { /* ignore */ }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanId]);

  return { progress, stage, status, isTerminal: TERMINAL.has(status) };
}
