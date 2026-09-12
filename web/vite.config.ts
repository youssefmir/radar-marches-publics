import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages par défaut ; BASE_PATH=/ pour un hébergement à la racine.
export default defineConfig(({ mode }) => ({
  base: loadEnv(mode, ".", "").BASE_PATH ?? "/radar-marches-publics/",
  plugins: [react()],
  build: {
    outDir: "dist",
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: { manualChunks: { echarts: ["echarts/core", "echarts/charts", "echarts/components", "echarts/renderers"] } },
    },
  },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
}));
