import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { resolvePilotProgramme } from '../lib/pilot-programme.ts';

const root = path.resolve(import.meta.dirname, '..');
const page = fs.readFileSync(path.join(root, 'app/pilot/page.tsx'), 'utf8');

test('pilot page cannot claim paid applications are open without funding and a private form URL', () => {
  assert.match(page, /Applications are not open/);
  assert.match(page, /Funding is not confirmed yet, so this is not a promise of payment/);

  assert.equal(resolvePilotProgramme({ applicationStatus: 'open', fundingStatus: 'seeking', applicationUrl: 'https://forms.example/apply' }).applicationsOpen, false);
  assert.equal(resolvePilotProgramme({ applicationStatus: 'open', fundingStatus: 'funded' }).applicationsOpen, false);
  assert.equal(resolvePilotProgramme({ applicationStatus: 'open', fundingStatus: 'funded', applicationUrl: 'http://forms.example/apply' }).applicationsOpen, false);
  assert.equal(resolvePilotProgramme({ applicationStatus: 'open', fundingStatus: 'funded', applicationUrl: 'https://forms.example/apply' }).applicationsOpen, true);
});

test('interest collection remains distinct from a funded paid application', () => {
  const state = resolvePilotProgramme({ applicationStatus: 'interest', fundingStatus: 'seeking', applicationUrl: 'https://forms.example/interest' });
  assert.equal(state.interestOpen, true);
  assert.equal(state.applicationsOpen, false);
  assert.equal(state.fundingStatus, 'seeking');
});

test('pilot page states the Registry and MLAT responsibility boundary', () => {
  assert.match(page, /Registry lifecycle evidence and MLAT operation are related, but they are not the same proof/);
  assert.match(page, /Feed binding, timing, freshness, geometry, observations, and contribution remain separate checks/);
  assert.match(page, /must not be used for aviation safety decisions/);
});

test('pilot page protects participant secrets and private locations', () => {
  assert.match(page, /Never share a private key, seed phrase, password, feed credential, or IP address/);
  assert.match(page, /fictional or deliberately coarse coordinates/);
  assert.match(page, /Registry records are public/);
});
