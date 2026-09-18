import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const frontendRoot = path.resolve(import.meta.dirname, '..');
const actionPanelSource = fs.readFileSync(path.join(frontendRoot, 'components/registry-action-panel.tsx'), 'utf8');

test('keeps the selected receiver visible for every existing-identity action', () => {
  assert.match(actionPanelSource, /action !== 'create' && selected \? <ActionTarget receiver=\{selected\} \/>/);
  assert.match(actionPanelSource, /value=\{receiver\.receiver_identity\}/);
  assert.match(actionPanelSource, /receiver\.record\.sequence\.toString\(\)/);
  assert.match(actionPanelSource, /receiver\.provenance\.ownerLock\.args/);
});

test('names the exact receiver in the permanent revoke confirmation', () => {
  assert.match(actionPanelSource, /Revoking \$\{selected\.record\.receiver_id\} is permanent\./);
  assert.match(actionPanelSource, /`Permanently revoke \$\{selected\.record\.receiver_id\}`/);
  assert.match(actionPanelSource, /Type \$\{expectedConfirmation/);
});
