import { defineConfig } from "@playwright/test";

/**
 * E2E tests (spec quality bar: one happy path per feature).
 * Run `npm run dev` first, or let Playwright start the dev server itself
 * via `webServer` below (it reuses an already-running server).
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
