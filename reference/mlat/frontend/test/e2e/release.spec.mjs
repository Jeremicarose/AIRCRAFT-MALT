import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

function capturePageErrors(page) {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  return errors;
}

test('starts on the Registry with shared Registry and MLAT navigation', async ({ page }) => {
  const pageErrors = capturePageErrors(page);
  await page.goto('/');

  await expect(page).toHaveURL(/\/app\/registry$/);
  await expect(page.getByRole('heading', { level: 1, name: 'Receiver directory' })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Registry' })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'MLAT reference' })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'System' })).toBeVisible();
  const registry = page.getByRole('navigation', { name: 'Registry' });
  const mlat = page.getByRole('navigation', { name: 'MLAT reference' });
  const system = page.getByRole('navigation', { name: 'System' });
  await expect(registry.getByRole('link', { name: 'Receiver directory', exact: true })).toBeVisible();
  for (const label of ['MLAT overview', 'Airspace map', 'Aircraft', 'MLAT receivers', 'Pipeline', 'Metrics', 'Accuracy benchmark']) {
    await expect(mlat.getByRole('link', { name: label, exact: true })).toBeVisible();
  }
  for (const label of ['Diagnostics', 'Settings']) {
    await expect(system.getByRole('link', { name: label, exact: true })).toBeVisible();
  }
  expect(pageErrors).toEqual([]);
});

test('presents a truthful public operator pilot without opening an unfunded application', async ({ page }) => {
  const pageErrors = capturePageErrors(page);
  await page.goto('/pilot');

  await expect(page.getByRole('heading', { level: 1, name: 'CKB Receiver Registry Pilot' })).toBeVisible();
  await expect(page.getByRole('status')).toContainText('Programme preparation');
  await expect(page.getByText('Applications are not open', { exact: true }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Two operating roles, one shared question' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Privacy and safety' })).toBeVisible();
  await expect(page.getByText(/Funding is not confirmed yet, so this is not a promise of payment/)).toBeVisible();
  await expect(page.getByRole('link', { name: 'Explore the Registry' })).toHaveAttribute('href', '/app/registry');
  expect(pageErrors).toEqual([]);
});

test('serves every static asset required by the receiver page', async ({ page }) => {
  const assetFailures = [];
  page.on('response', (response) => {
    const pathname = new URL(response.url()).pathname;
    if (pathname.startsWith('/_next/static/') && !response.ok()) {
      assetFailures.push(`${response.status()} ${pathname}`);
    }
  });
  page.on('requestfailed', (request) => {
    const pathname = new URL(request.url()).pathname;
    if (pathname.startsWith('/_next/static/')) {
      assetFailures.push(`request failed ${pathname}`);
    }
  });

  await page.goto('/app/receivers');
  await expect(page.getByRole('heading', { level: 1, name: 'Receivers' })).toBeVisible();
  await page.waitForLoadState('networkidle');

  expect(assetFailures).toEqual([]);
});

test('moves from an aircraft to a receiver and back to related aircraft', async ({ page }) => {
  const pageErrors = capturePageErrors(page);
  await page.goto('/app/aircraft');

  const receiverButton = page.getByRole('button', { name: /^Inspect receiver RECV_[A-Z]+_001$/ }).first();
  await expect(receiverButton).toBeVisible();
  const aircraftId = await page.getByRole('heading', { level: 2, name: /^[0-9A-F]{6}$/ }).textContent();
  expect(aircraftId).toBeTruthy();
  const receiverName = (await receiverButton.getAttribute('aria-label'))?.replace('Inspect receiver ', '');
  expect(receiverName).toBeTruthy();
  await receiverButton.click();

  const inspector = page.getByRole('dialog', { name: 'Investigation inspector' });
  await expect(inspector).toBeVisible();
  await expect(inspector.getByText('Canonical identity', { exact: true })).toBeVisible();
  await expect(inspector.getByText('Not registered', { exact: true }).first()).toBeVisible();
  const receiverDetails = inspector.getByRole('link', { name: 'Open receiver details' });
  await expect(receiverDetails).toHaveAttribute('href', new RegExp(`fromAircraft=${aircraftId}`));
  await receiverDetails.click();

  await expect(page).toHaveURL(/\/app\/receivers\?receiver=/);
  await expect(page).toHaveURL(new RegExp(`fromAircraft=${aircraftId}`));
  await expect(page.getByRole('heading', { level: 2, name: receiverName, exact: true })).toBeVisible();
  const returnToAircraft = page.getByRole('link', { name: `Return to ${aircraftId}` });
  await expect(returnToAircraft).toBeVisible();
  await returnToAircraft.click();
  await expect(page).toHaveURL(`/app/aircraft?aircraft=${aircraftId}`);
  expect(pageErrors).toEqual([]);
});

test('shows the selected aircraft contributing receivers with explicit synthetic provenance', async ({ page }) => {
  const pageErrors = capturePageErrors(page);
  await page.goto('/app/localization');

  await expect(page.getByRole('heading', { level: 1, name: 'Airspace map' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Data source: SYNTHETIC' })).toBeVisible();
  await expect(page.getByText(/Synthetic demonstration observations/).first()).toBeVisible();
  await expect(page.getByRole('heading', { level: 2, name: /^[0-9A-F]{6}$/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /^RECV_[A-Z]+_001 / })).toHaveCount(4);
  await expect(page.getByText(/synthetic/i).first()).toBeVisible();
  await expect(page.getByRole('status', { name: 'Map source: SYNTHETIC' })).toBeVisible();
  await expect(page.getByText('SYNTHETIC MAP', { exact: true })).toBeVisible();
  expect(pageErrors).toEqual([]);
});

test('orients every major workspace with purpose, state, and next step', async ({ page }) => {
  for (const route of ['/app/registry', '/app/overview', '/app/localization', '/app/aircraft', '/app/receivers', '/app/pipeline', '/app/metrics', '/app/benchmark', '/app/environment', '/app/settings']) {
    await page.goto(route);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    const orientation = page.getByRole('region', { name: route.includes('/registry') || route.includes('/settings') || route.includes('/environment') ? 'Page orientation' : /Data source:/ });
    await expect(orientation.getByText('What you are viewing', { exact: true })).toBeVisible();
    await expect(orientation.getByText('Current state', { exact: true })).toBeVisible();
    await expect(orientation.getByText('Next step', { exact: true })).toBeVisible();
  }
});

test('keeps persistent replay and pinned context out of actionable notifications', async ({ page }) => {
  await page.goto('/app/registry');
  await page.getByRole('button', { name: /^Notifications/ }).click();

  await expect(page.getByText('Errors and warnings that require action')).toBeVisible();
  await expect(page.getByText('Replay source active', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Pinned aircraft context', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Pinned receiver context', { exact: true })).toHaveCount(0);
});

test('opens the explanatory pipeline stage when a blocker is selected', async ({ page }) => {
  await page.goto('/app/pipeline');

  const blocker = page.getByRole('button', { name: 'Inspect MLAT solve blocker' }).first();
  await expect(blocker).toBeVisible();
  await blocker.click();
  await expect(blocker).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByRole('heading', { name: 'MLAT solve details' })).toBeVisible();
});

test('explains Registry contract configuration without claiming a live verification', async ({ page }) => {
  await page.goto('/app/registry');

  await expect(page.getByRole('heading', { name: 'Registry contract verification' })).toBeVisible();
  await expect(page.getByText('Runtime contract code hash', { exact: true })).toBeVisible();
  await expect(page.getByText('RECEIVER_REGISTRY_TYPE_HASH', { exact: true })).toBeVisible();
  await expect(page.getByText('SAVED EVIDENCE', { exact: true })).toBeVisible();
  await expect(page.getByText(/does not prove a physical receiver exists/)).toBeVisible();
});

test('separates synthetic contribution, Registry identity, and receiver operation on aircraft', async ({ page }) => {
  await page.goto('/app/aircraft');

  await expect(page.getByText('MLAT-derived position', { exact: true })).toBeVisible();
  await expect(page.getByText('MLAT solution → contributing receivers', { exact: true })).toBeVisible();
  await expect(page.getByText('SYNTHETIC CONTRIBUTION', { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/^Registry: /).first()).toBeVisible();
  await expect(page.getByText(/^Operational: /).first()).toBeVisible();
});

if (process.env.RUN_EXTERNAL_MAP_TEST === 'true') {
test('loads real OpenStreetMap tiles and keeps MLAT overlays usable', async ({ page }) => {

  const tileRequests = [];
  const tileResponses = [];
  const tileFailures = [];
  page.on('request', (request) => {
    if (request.url().includes('tile.openstreetmap.org')) tileRequests.push(request);
  });
  page.on('response', (response) => {
    if (response.url().includes('tile.openstreetmap.org')) tileResponses.push(response);
  });
  page.on('requestfailed', (request) => {
    if (!request.url().includes('tile.openstreetmap.org')) return;
    const reason = request.failure()?.errorText ?? 'unknown tile request failure';
    // MapLibre cancels tiles that leave the viewport during automatic fit,
    // zoom, and pan. Those cancellations are expected browser behavior.
    if (reason !== 'net::ERR_ABORTED') tileFailures.push(reason);
  });

  await page.goto('/app/localization');
  await expect(page.getByRole('heading', { level: 1, name: 'Airspace map' })).toBeVisible();
  await expect(page.locator('[data-map-tile-provider="openstreetmap"]')).toHaveAttribute('data-map-state', 'ready');
  const aircraftMarker = page.locator('.aircraft-map-marker').first();
  await expect(aircraftMarker).toBeVisible();
  await expect(page.locator('.receiver-map-marker').first()).toBeVisible();
  await expect.poll(() => tileResponses.length, { timeout: 30_000 }).toBeGreaterThan(0);

  const applicationOrigin = new URL(page.url()).origin;
  const requestHeaders = await Promise.all(tileRequests.map((request) => request.allHeaders()));
  for (const headers of requestHeaders) {
    expect(headers.referer).toBeTruthy();
    const referer = new URL(headers.referer);
    expect(referer.origin).toBe(applicationOrigin);
    expect(referer.pathname).toBe('/');
  }
  expect(tileFailures).toEqual([]);
  expect(tileResponses.every((response) => response.status() >= 200 && response.status() < 400)).toBe(true);
  for (const response of tileResponses) {
    expect(response.headers()['content-type'] ?? '').toMatch(/^image\//i);
    const body = await response.body();
    expect(body.toString('utf8')).not.toContain('Access blocked');
  }
  await expect(page.getByText('Map unavailable', { exact: true })).toHaveCount(0);

  const aircraftLabel = await aircraftMarker.getAttribute('aria-label');
  await aircraftMarker.click();
  expect(aircraftLabel).toMatch(/^Select aircraft [0-9A-F]{6}$/);
  await expect(page).toHaveURL(/aircraft=[0-9A-F]{6}/);
  const contributingReceiver = page.getByRole('button', { name: /^RECV_[A-Z]+_001 / }).first();
  await expect(contributingReceiver).toBeVisible();
  await contributingReceiver.click();
  await expect(page).toHaveURL(/receiver=/);
  await expect(page.getByText('Registry identity', { exact: true })).toBeVisible();
  await expect(page.getByText('Not registered', { exact: true })).toBeVisible();

  const mapRegion = page.getByRole('region', { name: 'Interactive aircraft and receiver map' });
  const zoomBefore = Number(await mapRegion.getAttribute('data-map-zoom'));
  await page.locator('.maplibregl-ctrl-zoom-in').last().click();
  await expect.poll(async () => Number(await mapRegion.getAttribute('data-map-zoom'))).toBeGreaterThan(zoomBefore);

  const mapCanvas = page.locator('.maplibregl-canvas').last();
  await expect(mapCanvas).toBeVisible();
  const centerBefore = await mapRegion.getAttribute('data-map-center');
  await mapCanvas.focus();
  await page.keyboard.press('ArrowRight');
  await expect.poll(async () => mapRegion.getAttribute('data-map-center')).not.toBe(centerBefore);
});
}

test('shows a map-only failure state when the tile provider is unavailable', async ({ page }) => {
  await page.route('https://tile.openstreetmap.org/**', (route) => route.abort('failed'));
  await page.goto('/app/localization');

  await expect(page.getByRole('heading', { level: 1, name: 'Airspace map' })).toBeVisible();
  await expect(page.getByRole('alert').getByText('Map unavailable', { exact: true })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/Aircraft and receiver information remains available/)).toBeVisible();
  await expect(page.locator('.aircraft-map-marker').first()).toBeVisible();
  await expect(page.locator('.receiver-map-marker').first()).toBeVisible();
  await expect(page.getByText('Contributing receivers', { exact: true })).toBeVisible();
});

test('recovers the air picture after a failed refresh without reloading the page', async ({ page }) => {
  await page.goto('/app/localization');
  await expect(page.locator('.aircraft-map-marker').first()).toBeVisible();

  const failPositions = (route) => route.abort('failed');
  await page.route('**/api/positions/recent**', failPositions);
  await page.getByRole('button', { name: 'Refresh map' }).click();

  const notice = page.getByRole('alert').filter({ hasText: 'The air picture could not be refreshed' });
  await expect(notice).toBeVisible();
  await expect(notice.getByRole('button', { name: 'Try again' })).toBeVisible();
  await expect(notice.getByText('Technical details')).toBeVisible();
  await expect(page.locator('.aircraft-map-marker').first()).toBeVisible();

  await page.unroute('**/api/positions/recent**', failPositions);
  await notice.getByRole('button', { name: 'Try again' }).click();
  await expect(notice).toBeHidden();
  await expect(page.getByText(/^(HISTORICAL REPLAY|LIVE|SYNTHETIC|UNKNOWN)( \(CACHED\))?$/).first()).toBeVisible();
});

for (const route of ['/pilot', '/app/localization', '/app/aircraft', '/app/receivers', '/app/pipeline', '/app/benchmark', '/app/environment', '/app/settings']) {
  test(`has no automated WCAG A or AA violations on ${route}`, async ({ page }) => {
    await page.goto(route);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    if (route === '/app/localization') {
      await expect(page.locator('.maplibregl-map').last()).toBeVisible();
      await expect(page.locator('.maplibregl-map[aria-hidden="true"]')).toHaveCount(0);
    }

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });
}

test('visualizes the historical solver benchmark without implying live accuracy', async ({ page }, testInfo) => {
  const pageErrors = capturePageErrors(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/app/benchmark');

  await expect(page.getByRole('heading', { level: 1, name: 'Accuracy benchmark' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Data source: Historical recording' })).toBeVisible();
  await expect(page.getByText('Historical recording', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('Solver only', { exact: true }).first()).toBeVisible();
  await expect(page.getByRole('main').getByText('Not live', { exact: true })).toBeVisible();
  await expect(page.getByRole('img', { name: /Median and 95th-percentile horizontal/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Solve outcome' })).toBeVisible();
  await expect(page.getByText('270', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('92', { exact: true }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Inspectable event geometry' })).toBeVisible();
  await expect(page.getByRole('row')).toHaveCount(6);
  await expect(page.getByRole('heading', { name: 'What this does not prove' })).toBeVisible();
  expect(pageErrors).toEqual([]);

  const accessibility = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath('benchmark-desktop.png'), fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(page.getByRole('heading', { level: 1, name: 'Accuracy benchmark' })).toBeVisible();
  await expect(page.getByRole('main').getByText('Not live', { exact: true })).toBeVisible();
  const tableRegion = page.getByRole('region', { name: 'Receiver geometry table, horizontally scrollable' });
  await expect(tableRegion).toBeVisible();
  const tableWidth = await tableRegion.evaluate((element) => ({ client: element.clientWidth, scroll: element.scrollWidth }));
  expect(tableWidth.scroll).toBeGreaterThan(tableWidth.client);
  const documentWidth = await page.evaluate(() => ({ client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(documentWidth.scroll).toBeLessThanOrEqual(documentWidth.client);
  await page.screenshot({ path: testInfo.outputPath('benchmark-mobile.png'), fullPage: true });
});

test('fits the airspace map in a narrow mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/app/localization');
  await expect(page.getByRole('heading', { level: 1, name: 'Airspace map' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Interactive aircraft and receiver map' })).toBeVisible();
  await expect(page.getByRole('status', { name: 'Map source: SYNTHETIC' })).toBeVisible();
  await expect(page.locator('.aircraft-map-marker').first()).toBeVisible();
  await expect(page.locator('.receiver-map-marker').first()).toBeVisible();
  await expect(page.locator('.maplibregl-ctrl-zoom-in').last()).toBeVisible();

  const width = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(width.scroll).toBeLessThanOrEqual(width.client);
});

test('explains one receiver from Registry identity through MLAT contribution', async ({ page }) => {
  const pageErrors = capturePageErrors(page);
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.goto('/app/receivers?receiver=0x74b25d0f23d0fb20fa3016bccd00f58358fb546cd14ecd368a69eafbaf2c7b78');
  await expect(page.getByRole('heading', { level: 1, name: 'Receivers' })).toBeVisible();
  await page.waitForTimeout(1_000);
  expect(pageErrors).toEqual([]);
  expect(consoleErrors).toEqual([]);
  await expect(page.getByText('Registry identity', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('Operational state', { exact: true })).toBeVisible();
  await expect(page.getByText('MLAT state', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Registry to MLAT journey' })).toBeVisible();
  await expect(page.getByText(/Next action:/)).toBeVisible();
  const stages = page.locator('summary').filter({ hasText: 'View all 8 readiness stages' });
  await expect(stages).toBeVisible();
  await stages.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText('8. Used in aircraft position', { exact: true })).toBeVisible();
  for (const heading of ['Registry facts', 'Operational observations', 'MLAT-derived state']) {
    await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible();
  }
});

test('opens a revoked receiver from the Registry directory', async ({ page }) => {
  const activeReceiver = '0x74b25d0f23d0fb20fa3016bccd00f58358fb546cd14ecd368a69eafbaf2c7b78';
  const revokedReceiver = '0x1d6855f20486a023c92df0c613a3141e385f3766c4c844d2935fe18cfcf220ce';
  await page.goto(`/app/registry?receiver=${activeReceiver}`);

  await page.getByRole('button', { name: 'All states' }).click();
  const revokedRow = page.getByRole('row', { name: 'RECV_REGISTRY_V2_EVIDENCE' });
  await expect(revokedRow).toBeVisible();
  await revokedRow.click();

  await expect(page).toHaveURL(`/app/registry?receiver=${revokedReceiver}`);
  await expect(page.getByRole('heading', { level: 2, name: 'RECV_REGISTRY_V2_EVIDENCE' })).toBeVisible();
  await expect(page.getByText('Revocation is permanent', { exact: true })).toBeVisible();
});

test('finds a revoked Registry identity from global search', async ({ page }) => {
  const revokedReceiver = '0x1d6855f20486a023c92df0c613a3141e385f3766c4c844d2935fe18cfcf220ce';
  await page.goto('/app/registry');

  await page.getByRole('button', { name: 'Search console' }).click();
  await page.getByPlaceholder('Search routes, entities, or console actions').fill('RECV_REGISTRY_V2_EVIDENCE');
  const result = page.getByRole('option', { name: /RECV_REGISTRY_V2_EVIDENCE/ });
  await expect(result).toBeVisible();
  await result.click();

  await expect(page).toHaveURL(`/app/registry?receiver=${revokedReceiver}`);
  await expect(page.getByRole('heading', { level: 2, name: 'RECV_REGISTRY_V2_EVIDENCE' })).toBeVisible();
  await expect(page.getByText('Revocation is permanent', { exact: true })).toBeVisible();
});

test('gives recovery instructions for missing backend Registry configuration', async ({ page }) => {
  await page.goto('/app/environment');
  const discoveryCheck = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Backend Registry discovery' }) });
  await expect(discoveryCheck).toBeVisible();
  await expect(discoveryCheck.getByText(/RECEIVER_REGISTRY_TYPE_HASH/).first()).toBeVisible();
  await expect(discoveryCheck.getByText('What to do', { exact: true })).toBeVisible();
  await expect(discoveryCheck.getByText('What success looks like', { exact: true })).toBeVisible();
});

test('does not enter an update loop when revisiting a selected receiver', async ({ page }) => {
  const pageErrors = capturePageErrors(page);
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  const receiverUrl = '/app/receivers?receiver=0x74b25d0f23d0fb20fa3016bccd00f58358fb546cd14ecd368a69eafbaf2c7b78';
  for (const route of [receiverUrl, '/app/settings', receiverUrl, '/app/environment', receiverUrl]) {
    await page.goto(route);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  }
  expect(pageErrors).toEqual([]);
  expect(consoleErrors.filter((message) => message.includes('Maximum update depth exceeded'))).toEqual([]);
});

test('keeps an operational data grid readable on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/app/aircraft');

  const gridRegion = page.getByRole('region', { name: /Aircraft inventory, horizontally scrollable/ });
  await expect(gridRegion).toBeVisible();
  const gridWidth = await gridRegion.evaluate((element) => ({ client: element.clientWidth, scroll: element.scrollWidth }));
  expect(gridWidth.scroll).toBeGreaterThan(gridWidth.client);
  const documentWidth = await page.evaluate(() => ({ client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
  expect(documentWidth.scroll).toBeLessThanOrEqual(documentWidth.client);
});

test('returns the required browser security headers', async ({ request }) => {
  const response = await request.get('/app/localization');

  expect(response.status()).toBe(200);
  expect(response.headers()['x-content-type-options']).toBe('nosniff');
  expect(response.headers()['x-frame-options']).toBe('DENY');
  expect(response.headers()['referrer-policy']).toBe('strict-origin-when-cross-origin');
  expect(response.headers()['permissions-policy']).toContain('camera=()');
});
