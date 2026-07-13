import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

// ============================================================
// Vitest configuration
// ============================================================
// Tests import from `@/…` (resolved via vite-tsconfig-paths from
// tsconfig.json) and run in a jsdom environment so browser globals
// like sessionStorage — and React component rendering via
// @testing-library/react — are available. The React plugin handles
// JSX/TSX transform for component tests.
// ============================================================

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    setupFiles: ["./vitest.setup.ts"],
  },
});
