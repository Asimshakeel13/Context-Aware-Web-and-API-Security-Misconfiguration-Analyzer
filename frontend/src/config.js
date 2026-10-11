// Backend base URL. Overridable at build/run time via VITE_API_BASE.
// In the browser the API is reached on the host (not the docker network),
// so this defaults to localhost:8000.
export const API_BASE =
  import.meta.env.VITE_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";

export const WS_BASE = API_BASE.replace(/^http/, "ws");
