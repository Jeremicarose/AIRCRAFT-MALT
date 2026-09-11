import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('Registry directory has no serious or critical accessibility violations', async ({ page }, testInfo) => {
  await page.goto('/app/registry', { waitUntil: 'networkidle' });
  await expect(page).toHaveTitle(/Receiver Registry/);
  await expect(page.getByRole('heading', { name: 'Receiver directory' })).toBeVisible();
  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(hasHorizontalOverflow).toBe(false);

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();
  const serious = results.violations.filter((violation) =>
    violation.impact === 'serious' || violation.impact === 'critical',
  );
  await testInfo.attach('axe-serious-critical', {
    body: Buffer.from(JSON.stringify(serious)),
    contentType: 'application/json',
  });
  expect(serious).toEqual([]);
});
