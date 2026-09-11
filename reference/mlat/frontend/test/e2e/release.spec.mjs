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

  const width = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(width.scroll).toBeLessThanOrEqual(width.client);
});

test('returns the required browser security headers', async ({ request }) => {
  const response = await request.get('/app/localization');

  expect(response.status()).toBe(200);
  expect(response.headers()['x-content-type-options']).toBe('nosniff');
  expect(response.headers()['x-frame-options']).toBe('DENY');
  expect(response.headers()['referrer-policy']).toBe('no-referrer');
  expect(response.headers()['permissions-policy']).toContain('camera=()');
});
