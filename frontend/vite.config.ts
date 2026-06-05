import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: proxy /api to the FastAPI server. Build: emit into the package's
// static dir so `falk-api` can serve the SPA from a single origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "../src/falk/api/static",
    emptyOutDir: true,
  },
});
