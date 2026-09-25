import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API to Django during local dev to avoid CORS
      // (backend has no CORS allow-all configured).
      // Set VITE_API_BASE_URL to override in production.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
