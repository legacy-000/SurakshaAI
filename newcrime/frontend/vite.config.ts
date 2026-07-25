import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Catalyst serves the client under /app/, so production assets must be
// referenced from there. Dev stays at / so the vite proxy works unchanged.
export default defineConfig(({ mode }) => ({
  base: mode === "production" ? "/app/" : "/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8077",
    },
  },
}));
