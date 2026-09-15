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
  for (const label of ['MLAT overview', 'Live Map', 'Aircraft', 'MLAT receivers', 'Pipeline', 'Metrics']) {
    await expect(mlat.getByRole('link', { name: label, exact: true })).toBeVisible();
  }
  for (const label of ['Diagnostics', 'Settings']) {
    await expect(system.getByRole('link', { name: label, exact: true })).toBeVisible();
  }
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

test('shows the selected aircraft contributing receivers', async ({ page }) => {
  const pageErrors = capturePageErrors(page);
  await page.goto('/app/localization');

  await expect(page.getByRole('heading', { level: 1, name: 'Live map' })).toBeVisible();
  await expect(page.getByRole('heading', { level: 2, name: /^[0-9A-F]{6}$/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /^RECV_[A-Z]+_001 / })).toHaveCount(4);
  await expect(page.getByText(/replay/i).first()).toBeVisible();
  expect(pageErrors).toEqual([]);
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
  await expect(page.getByRole('heading', { level: 1, name: 'Live map' })).toBeVisible();
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

  await expect(page.getByRole('heading', { level: 1, name: 'Live map' })).toBeVisible();
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
  await expect(page.getByText(/^(Replay data|Live polling)$/).first()).toBeVisible();
});

for (const route of ['/app/localization', '/app/environment']) {
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

test('fits the Live Map in a narrow mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/app/localization');
  await expect(page.getByRole('heading', { level: 1, name: 'Live map' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Interactive aircraft and receiver map' })).toBeVisible();
  await expect(page.locator('.aircraft-map-marker').first()).toBeVisible();
  await expect(page.locator('.receiver-map-marker').first()).toBeVisible();
  await expect(page.locator('.maplibregl-ctrl-zoom-in').last()).toBeVisible();

  const width = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(width.scroll).toBeLessThanOrEqual(width.client);
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
