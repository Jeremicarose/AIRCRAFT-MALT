import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';

const root = '../../..';
const historicalReplay = process.env.PLAYWRIGHT_DATA_MODE === 'historical';
const apiPort = process.env.PLAYWRIGHT_API_PORT || '4312';
const frontendPort = process.env.PLAYWRIGHT_FRONTEND_PORT || '4311';
const reuseExistingServers = process.env.PLAYWRIGHT_REUSE_EXISTING_SERVERS === 'true';
const distDir = process.env.PLAYWRIGHT_DIST_DIR || '.next-production';
const pythonEnvironment = process.env.PLAYWRIGHT_PYTHON_DIR || path.resolve(root, '.venv');
const pythonPath = [path.join(pythonEnvironment, 'bin'), process.env.PATH]
  .filter(Boolean)
  .join(path.delimiter);
const apiURL = `http://127.0.0.1:${apiPort}`;
const frontendURL = `http://127.0.0.1:${frontendPort}`;

export default defineConfig({
  testDir: './test/e2e',
  testMatch: historicalReplay ? '**/historical-replay.spec.mjs' : '**/*.spec.mjs',
  testIgnore: historicalReplay ? undefined : '**/historical-replay.spec.mjs',
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  outputDir: 'test-results/artifacts',
  reporter: [
    ['line'],
    ['./test/e2e/evidence-reporter.mjs'],
  ],
  use: {
    baseURL: frontendURL,
    launchOptions: process.env.PLAYWRIGHT_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH }
      : undefined,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: `${root}/${historicalReplay ? 'run-replay.sh' : 'run-demo.sh'}`,
      url: `${apiURL}/healthz`,
      reuseExistingServer: reuseExistingServers,
      timeout: 120_000,
      env: {
        ...process.env,
        PATH: pythonPath,
        VIRTUAL_ENV: pythonEnvironment,
        API_PORT: apiPort,
        DATABASE_PATH: `/tmp/ckb-registry-playwright-${process.pid}.db`,
        RATE_LIMIT_ENABLED: 'true',
        RATE_LIMIT_REQUESTS: '10000',
      },
    },
    {
      command: 'npm start',
      url: `${frontendURL}/healthz`,
      reuseExistingServer: reuseExistingServers,
      timeout: 120_000,
      env: {
        ...process.env,
        HOSTNAME: '127.0.0.1',
        PORT: frontendPort,
        NEXT_DIST_DIR: distDir,
        MLAT_API_INTERNAL_URL: apiURL,
      },
    },
  ],
});
