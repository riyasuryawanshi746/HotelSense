import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development every request to /api/... is forwarded to the FastAPI backend,
// so the browser only ever talks to one origin (no CORS problems).
export default defineConfig({
  plugins: [react()],
  // Plotly alone is ~1.3 MB minified; that is expected, so don't warn about it.
  build: { chunkSizeWarningLimit: 1500 },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
