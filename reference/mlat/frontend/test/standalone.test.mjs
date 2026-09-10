import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { prepareStandaloneAssets, resolveStandalonePaths } from '../lib/standalone.mjs';

test('prepares static assets beside the nested standalone server', async () => {
  const repositoryRoot = await mkdtemp(path.join(os.tmpdir(), 'mlat-standalone-'));
  const projectRoot = path.join(repositoryRoot, 'reference', 'mlat', 'frontend');
  const paths = resolveStandalonePaths({ projectRoot, tracingRoot: repositoryRoot });

  try {
    await mkdir(paths.staticSource, { recursive: true });
    await mkdir(paths.standaloneProjectRoot, { recursive: true });
    await writeFile(paths.server, 'server');
    await writeFile(path.join(paths.staticSource, 'app.css'), 'body { color: red; }');

    await prepareStandaloneAssets({ projectRoot, tracingRoot: repositoryRoot });

    assert.equal(await readFile(path.join(paths.standaloneStatic, 'app.css'), 'utf8'), 'body { color: red; }');
  } finally {
    await rm(repositoryRoot, { recursive: true, force: true });
  }
});
