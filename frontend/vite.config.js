import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server runs on 5173 (matches the backend's default FRONTEND_ORIGIN / CORS).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
  preview: {
    host: true,
    port: 5173,
  },
});
