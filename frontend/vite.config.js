import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/workspaces": "http://localhost:8000",
      "/channels": "http://localhost:8000",
      "/messages": "http://localhost:8000",
      "/macros": "http://localhost:8000",
    },
  },
});
