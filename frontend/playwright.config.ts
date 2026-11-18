import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/browser",
  outputDir: "../.cache/playwright",
  workers: 1,
  reporter: "list",
  timeout: 30000,
  webServer: {
    command: "npm run dev -- --port 5173",
    cwd: import.meta.dirname,
    url: "http://127.0.0.1:5173/prophet-sentinel/",
    reuseExistingServer: true,
    timeout: 15000,
  },
  use: {
    baseURL: "http://localhost:5173/prophet-sentinel/",
    headless: true,
    launchOptions: { executablePath: "/usr/bin/google-chrome" },
  },
});
