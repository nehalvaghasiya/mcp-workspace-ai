import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.E2E_WEB_URL || 'http://127.0.0.1:5173';
const port = new URL(baseURL).port || '5173';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `pnpm run dev --port ${Number(port)}`,
    url: baseURL,
    reuseExistingServer: !process.env.E2E_WEB_URL && !process.env.CI,
    timeout: 30_000,
  },
});
