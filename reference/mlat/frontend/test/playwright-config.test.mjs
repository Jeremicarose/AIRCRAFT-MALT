import assert from 'node:assert/strict';
import path from 'node:path';
import test from 'node:test';

import config from '../playwright.config.mjs';

test('starts browser QA API with the repository Python environment', () => {
  const apiServer = config.webServer[0];
  const firstPathEntry = apiServer.env.PATH.split(path.delimiter)[0];

  assert.equal(firstPathEntry, path.resolve('../../..', '.venv/bin'));
  assert.equal(apiServer.env.VIRTUAL_ENV, path.resolve('../../..', '.venv'));
});
