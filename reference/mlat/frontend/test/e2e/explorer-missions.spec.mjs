import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function completions(page) {
  return page.evaluate(() => JSON.parse(localStorage.getItem('receiver-console-missions-v1') || '{"state":{"completed":[]}}').state.completed);
}

test('keeps the console frame mounted through navigation, slow loading, back and forward', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/app/guide');
  await expect(page.getByRole('heading', { name: 'Explorer missions', level: 1 })).toBeVisible();
  await page.locator('[data-console-frame]').evaluate((element) => { element.dataset.identityCheck = 'persistent-frame'; });
  await page.route('**/app/metrics?*', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 800));
    await route.continue();
  });
  for (const [label, title] of [['Metrics', 'Metrics'], ['Settings', 'Settings'], ['Diagnostics', 'Diagnostics']]) {
    await page.getByRole('navigation').getByRole('link', { name: label, exact: true }).click();
    await expect(page.getByRole('heading', { name: title, level: 1 })).toBeVisible();
    await expect(page.locator('[data-console-frame]')).toHaveAttribute('data-identity-check', 'persistent-frame');
    await expect(page.locator('main#main-content')).toHaveCount(1);
  }
  await page.goBack();
  await expect(page.getByRole('heading', { name: 'Settings', level: 1 })).toBeVisible();
  await page.goForward();
  await expect(page.getByRole('heading', { name: 'Diagnostics', level: 1 })).toBeVisible();
  await expect(page.locator('[data-console-frame]')).toHaveAttribute('data-identity-check', 'persistent-frame');
  expect(errors).toEqual([]);
});

test('earns learning points for correct answers, persists once, pauses and resets', async ({ page }) => {
  await page.goto('/app/guide');
  const challenge = page.getByRole('region', { name: 'Source challenge' });
  await challenge.getByRole('button', { name: /physically present/ }).click();
  await expect(challenge.getByRole('status')).toContainText('Try again');
  expect(await completions(page)).toEqual([]);
  await challenge.getByRole('button', { name: /current owner authorized/ }).click();
  await expect(page.getByRole('complementary', { name: 'Learning progress' })).toContainText('25 / 300 XP');
  await page.reload();
  await expect(challenge).toContainText('Badge earned');
  expect(await completions(page)).toEqual(['source']);
  await page.getByRole('button', { name: 'Pause missions' }).click();
  await page.getByRole('navigation').getByRole('link', { name: 'Accuracy benchmark', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Benchmark challenge' }).getByRole('button').first()).toBeDisabled();
  await page.getByRole('navigation').getByRole('link', { name: 'Explorer missions', exact: true }).click();
  await page.getByRole('button', { name: 'Resume missions' }).click();
  await page.getByRole('button', { name: 'Reset learning progress' }).click();
  await page.getByRole('button', { name: 'Keep progress' }).click();
  expect(await completions(page)).toEqual(['source']);
  await page.getByRole('button', { name: 'Reset learning progress' }).click();
  await page.getByRole('button', { name: 'Reset progress', exact: true }).click();
  await expect(challenge.getByRole('button', { name: /current owner authorized/ })).toBeEnabled();
  expect(await completions(page)).toEqual([]);
});

test('rewards successful diagnostic exports and never a failed download', async ({ page }) => {
  await page.goto('/app/environment');
  await page.route('**/api/diagnostics/bundle', (route) => route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":"unavailable"}' }));
  await page.getByRole('button', { name: 'Export diagnostics' }).click();
  await expect(page.getByText(/report could not be downloaded/)).toBeVisible();
  expect(await completions(page)).not.toContain('diagnostics');
  await page.unroute('**/api/diagnostics/bundle');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export diagnostics' }).click();
  expect((await download).suggestedFilename()).toBe('mlat-diagnostics.json');
  await expect.poll(() => completions(page)).toContain('diagnostics');
  expect((await completions(page)).filter((id) => id === 'diagnostics')).toHaveLength(1);
});

test('real receiver and pipeline inspections earn their missions, mere visits do not', async ({ page }) => {
  await page.goto('/app/receivers');
  expect(await completions(page)).not.toContain('receiver');
  await page.getByRole('row', { name: /^RECV_[A-Z]+_001$/ }).first().click();
  await expect.poll(() => completions(page)).toContain('receiver');
  await page.getByRole('navigation').getByRole('link', { name: 'Pipeline', exact: true }).click();
  expect(await completions(page)).not.toContain('pipeline');
  await page.getByRole('button', { name: /Inspect .* (blocker|stage)/ }).first().click();
  await expect.poll(() => completions(page)).toContain('pipeline');
  await page.getByRole('navigation').getByRole('link', { name: 'Accuracy benchmark', exact: true }).click();
  await page.getByRole('region', { name: 'Benchmark challenge' }).getByRole('button', { name: /timing observations fit the model/ }).click();
  await expect.poll(() => completions(page)).toContain('benchmark');
  expect(await completions(page)).not.toContain('replay');
});

test('mission guide supports mobile, keyboard, reduced motion and unavailable storage', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.addInitScript(() => {
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function(key, value) {
      if (key === 'receiver-console-missions-v1') throw new DOMException('Storage blocked');
      return original.call(this, key, value);
    };
  });
  await page.goto('/app/guide');
  const correct = page.getByRole('button', { name: /current owner authorized/ });
  await correct.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('region', { name: 'Source challenge' })).toContainText('Badge earned');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(await page.locator('.workspace-enter').evaluate((element) => getComputedStyle(element).animationName)).toBe('none');
  const audit = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  expect(audit.violations).toEqual([]);
});

test('learning and navigation remain available when runtime APIs fail', async ({ page }) => {
  await page.route('**/api/**', (route) => route.abort());
  await page.goto('/app/guide');
  await expect(page.getByRole('heading', { name: 'Explorer missions', level: 1 })).toBeVisible();
  await page.getByRole('button', { name: /current owner authorized/ }).click();
  await expect(page.getByRole('region', { name: 'Source challenge' })).toContainText('Badge earned');
  await page.getByRole('navigation').getByRole('link', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Settings', level: 1 })).toBeVisible();
  expect(await completions(page)).toEqual(['source']);
});
