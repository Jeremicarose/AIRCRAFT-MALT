import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = path.resolve(import.meta.dirname, '..');
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');

test('orients every major page with purpose, current state, and a next step', () => {
  const orientation = read('components/data-source-banner.tsx');
  const shell = read('components/app-shell.tsx');
  for (const label of ['What you are viewing', 'Current state', 'Next step']) {
    assert.match(orientation, new RegExp(label));
  }
  assert.match(shell, /<PageOrientation/);
  assert.match(orientation, /aria-live="polite"/);
});

test('groups receiver details by Registry, operational, and MLAT source of truth', () => {
  const inspector = read('components/receiver-inspector.tsx');
  for (const heading of ['Registry facts', 'Operational observations', 'MLAT-derived state']) {
    assert.match(inspector, new RegExp(heading));
  }
  assert.match(inspector, /Owner-declared stream endpoint/);
  assert.match(inspector, /do not prove hardware existence, location, feed honesty, or clock accuracy/);
});

test('keeps the receiver next action visible while placing all eight stages in an accessible disclosure', () => {
  const journey = read('components/receiver-readiness-journey.tsx');
  assert.match(journey, /Recommended next action/);
  assert.match(journey, /View all 8 readiness stages/);
  assert.match(journey, /<details/);
  assert.match(journey, /focus-visible:ring-2/);
});

test('puts explicit provenance inside every map workspace', () => {
  const badge = read('components/map-source-badge.tsx');
  const overview = read('components/pages/overview-page.tsx');
  const localization = read('components/pages/live-map-page.tsx');
  const aircraft = read('components/pages/aircraft-page.tsx');
  assert.match(badge, /Map source:/);
  assert.match(badge, /data-map-source/);
  assert.match(badge, /\$\{source\.label\} MAP/);
  for (const source of [overview, localization, aircraft]) assert.match(source, /<MapSourceBadge/);
});

test('uses higher-contrast supporting text and readable shared fact labels', () => {
  const styles = read('app/globals.css');
  const shared = read('components/operations-ui.tsx');
  assert.match(styles, /--color-ink-quiet: #8f99a6/);
  assert.match(shared, /<dt className="text-xs font-medium text-ink-quiet">/);
  assert.match(shared, /text-\[13px\] font-semibold/);
});

test('receiver details require selection and expose an accessible collapse control', () => {
  const receiversPage = read('components/pages/receivers-page.tsx');
  const receiverInspector = read('components/receiver-inspector.tsx');
  const operations = read('components/operations-ui.tsx');

  assert.doesNotMatch(receiversPage, /storedSelectedId/);
  assert.doesNotMatch(receiversPage, /selectedUi\s*=.*filtered\[0\]/);
  assert.match(receiversPage, /receiverDetailsExpanded/);
  assert.match(receiverInspector, /collapsible/);
  assert.match(operations, /aria-expanded/);
  assert.match(operations, /Collapse .* details/);
});

test('contract verification rows wrap technical sources without overlapping status', () => {
  const verification = read('components/registry-contract-verification.tsx');
  const statusChip = read('components/ui/status-chip.tsx');

  assert.match(verification, /xl:grid-cols-3/);
  assert.match(verification, /break-all/);
  assert.match(statusChip, /whitespace-nowrap/);
});
