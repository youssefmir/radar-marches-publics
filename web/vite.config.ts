import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Base GitHub Pages : https://youssefmir.github.io/radar-marches-publics/
export default defineConfig({
  base: "/radar-marches-publics/",
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
});
