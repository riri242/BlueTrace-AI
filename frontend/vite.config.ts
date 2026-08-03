import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  build: {
    // Mapbox GL is intentionally loaded by the analysis route and is larger
    // than Vite's default generic chunk warning threshold.
    chunkSizeWarningLimit: 2200
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src")
    }
  },
  server: {
    port: 5173
  }
});
