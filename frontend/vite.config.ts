import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Frontend dev server always runs on :3100 (docs/DECISIONS.md #11).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3100,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
