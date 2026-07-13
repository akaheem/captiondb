// ============================================================
// Vitest global setup
// ============================================================
// Runs before each test file. Registers jest-dom matchers, unmounts
// rendered React trees, and resets jsdom storage between tests so
// component and TokenStorage cases stay isolated.
// ============================================================

import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
  sessionStorage.clear();
  localStorage.clear();
});
