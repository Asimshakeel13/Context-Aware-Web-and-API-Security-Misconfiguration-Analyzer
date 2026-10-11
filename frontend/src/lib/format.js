export const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];

export const SEV_COLOR = {
  CRITICAL: "var(--crit)",
  HIGH: "var(--high)",
  MEDIUM: "var(--med)",
  LOW: "var(--low)",
  INFO: "var(--info)",
};

export function scoreColor(score) {
  if (score >= 9) return "var(--crit)";
  if (score >= 7) return "var(--high)";
  if (score >= 4) return "var(--med)";
  if (score >= 0.1) return "var(--low)";
  return "var(--info)";
}

export function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export function fmtDuration(seconds) {
  if (seconds == null) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

export function categoryLabel(c) {
  return { REST_API: "REST API", INFO_DISCLOSURE: "Info Disclosure" }[c] ||
    c?.charAt(0) + c?.slice(1).toLowerCase();
}

export function shortId(id) {
  return String(id).slice(0, 8);
}
