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

test('keeps receiver context before owner actions in the stacked registry workflow', async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 900 });
  await page.goto('/app/registry', { waitUntil: 'networkidle' });

  const workflow = page.locator('[data-registry-workflow]');
  await expect(workflow).toBeVisible();
  const order = await workflow.locator('[data-registry-workflow-item]').evaluateAll((items) =>
    items.map((item) => item.getAttribute('data-registry-workflow-item')),
  );
  expect(order).toEqual(['directory', 'receiver-context', 'owner-actions']);

  const directoryBox = await workflow.locator('[data-registry-workflow-item="directory"]').boundingBox();
  const contextBox = await workflow.locator('[data-registry-workflow-item="receiver-context"]').boundingBox();
  const actionsBox = await workflow.locator('[data-registry-workflow-item="owner-actions"]').boundingBox();
  expect(directoryBox).not.toBeNull();
  expect(contextBox).not.toBeNull();
  expect(actionsBox).not.toBeNull();
  expect(contextBox.y).toBeGreaterThan(directoryBox.y + directoryBox.height - 1);
  expect(actionsBox.y).toBeGreaterThan(contextBox.y + contextBox.height - 1);
});
