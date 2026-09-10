import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { prepareStandaloneAssets } from '../lib/standalone.mjs';

const projectRoot = path.resolve(fileURLToPath(new URL('..', import.meta.url)));

let paths;
try {
  paths = await prepareStandaloneAssets({ projectRoot });
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

server.once('exit', (code, signal) => {
  process.exit(code ?? (signal ? 1 : 0));
});
