import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const frontendRoot = path.resolve(import.meta.dirname, '..');
const mapSource = fs.readFileSync(path.join(frontendRoot, 'components/airspace-map.tsx'), 'utf8');
const nextConfig = fs.readFileSync(path.join(frontendRoot, 'next.config.mjs'), 'utf8');

test('keeps the production OpenStreetMap source and an explicit unavailable state', () => {
  assert.match(mapSource, /const OSM_TILE_URL = 'https:\/\/tile\.openstreetmap\.org\/\{z\}\/\{x\}\/\{y\}\.png';/);
  assert.match(mapSource, /data-map-tile-provider="openstreetmap"/);
  assert.match(mapSource, /data-map-state=\{mapError \? 'unavailable' : ready \? 'ready' : 'loading'\}/);
  assert.match(mapSource, /Map unavailable/);
  assert.match(mapSource, /Aircraft and receiver information remains available/);
});

test('uses a cross-origin referrer policy compatible with OSM tiles without dropping security headers', () => {
  assert.match(nextConfig, /key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin'/);
  assert.doesNotMatch(nextConfig, /key: 'Referrer-Policy', value: 'no-referrer'/);
  assert.match(nextConfig, /key: 'X-Content-Type-Options', value: 'nosniff'/);
  assert.match(nextConfig, /key: 'X-Frame-Options', value: 'DENY'/);
  assert.match(nextConfig, /key: 'Permissions-Policy', value: 'camera=\(\), microphone=\(\), geolocation=\(\)'/);
});
