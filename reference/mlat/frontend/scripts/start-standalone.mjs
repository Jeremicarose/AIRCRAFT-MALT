import path from 'node:path';
import { spawn } from 'node:child_process';
import { rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { stageStandaloneBuild } from '../lib/standalone.mjs';

const projectRoot = path.resolve(fileURLToPath(new URL('..', import.meta.url)));

let paths;
try {
  paths = await stageStandaloneBuild({ projectRoot });
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
}

const server = spawn(process.execPath, ['server.js'], {
  cwd: paths.standaloneProjectRoot,
  env: process.env,
  stdio: 'inherit',
});

const forwardSignal = (signal) => server.kill(signal);
process.once('SIGINT', () => forwardSignal('SIGINT'));
process.once('SIGTERM', () => forwardSignal('SIGTERM'));

let finalizing = false;
async function finalize(code) {
  if (finalizing) return;
  finalizing = true;
  await rm(paths.runtimeContainer, { recursive: true, force: true });
  process.exit(code);
}

server.once('error', (error) => {
  console.error(error);
  void finalize(1);
});

server.once('exit', (code, signal) => {
  void finalize(code ?? (signal ? 1 : 0));
});
