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

test('opens receiver context only after row selection and allows it to collapse', async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 900 });
  await page.goto('/app/registry', { waitUntil: 'networkidle' });

  const workflow = page.locator('[data-registry-workflow]');
  await expect(workflow).toBeVisible();
  await expect(workflow.locator('[data-registry-workflow-item="receiver-context"]')).toHaveCount(0);

  await page.getByText('RECV_NAIROBI_001', { exact: true }).click();
  const receiverContext = workflow.locator('[data-registry-workflow-item="receiver-context"]');
  await expect(receiverContext).toBeVisible();

  const collapse = receiverContext.getByRole('button', { name: 'Collapse RECV_NAIROBI_001 details' });
  await expect(collapse).toHaveAttribute('aria-expanded', 'true');
  await collapse.click();
  await expect(receiverContext.getByRole('heading', { name: 'Registry facts' })).toBeHidden();

  const expand = receiverContext.getByRole('button', { name: 'Expand RECV_NAIROBI_001 details' });
  await expect(expand).toHaveAttribute('aria-expanded', 'false');
  await expand.click();
  await expect(receiverContext.getByRole('heading', { name: 'Registry facts' })).toBeVisible();

  const order = await workflow.locator('[data-registry-workflow-item]').evaluateAll((items) =>
    items.map((item) => item.getAttribute('data-registry-workflow-item')),
  );
  expect(order).toEqual(['directory', 'receiver-context', 'owner-actions']);

  const directoryBox = await workflow.locator('[data-registry-workflow-item="directory"]').boundingBox();
  const contextBox = await receiverContext.boundingBox();
  const actionsBox = await workflow.locator('[data-registry-workflow-item="owner-actions"]').boundingBox();
  expect(directoryBox).not.toBeNull();
  expect(contextBox).not.toBeNull();
  expect(actionsBox).not.toBeNull();
  expect(contextBox.y).toBeGreaterThan(directoryBox.y + directoryBox.height - 1);
  expect(actionsBox.y).toBeGreaterThan(contextBox.y + contextBox.height - 1);
});
