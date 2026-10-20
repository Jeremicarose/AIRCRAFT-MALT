import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('historical observations reach stored solutions and the replay debugger', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/app/replay?event=5711382');
  await expect(page.getByRole('heading', { name: 'Historical replay', exact: true, level: 1 })).toBeVisible();
  await expect(page.getByRole('main').getByText('362 events · 270 solved · 92 rejected')).toBeVisible();
  await expect(page.getByRole('main').getByText(/Calculated position:/)).toBeVisible();
  await expect(page.getByRole('main').getByText(/UTC epoch is not supplied/)).toBeVisible();
  await page.getByRole('button', { name: 'Next stage', exact: true }).click();
  await expect(page.getByRole('main').getByText('Unique dataset identities, integer arrival timestamps and finite receiver geometry.')).toBeVisible();
  await page.getByRole('button', { name: 'Next stage', exact: true }).click();
  await expect(page.getByRole('main').getByText(/Raw Mode-S frame correlation cannot be tested/)).toBeVisible();
  const receivers = await page.request.get('/api/receivers');
  for (const receiver of (await receivers.json()).receivers) {
    expect(receiver.last_seen).toBe(0);
    expect(receiver.qualification.state).toBe('UNQUALIFIED');
  }
  expect(errors).toEqual([]);
});

test('historical replay retains rejected events and supports mobile keyboard use', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/app/replay');
  const listing = await (await page.request.get('/api/replay?limit=100')).json();
  const failed = listing.events.find((event) => !event.solved);
  expect(failed).toBeTruthy();
  await page.goto(`/app/replay?event=${failed.event_id}`);
  await expect(page.getByRole('main').getByText(/No position was stored: altitude out of bounds/)).toBeVisible();
  const next = page.getByRole('button', { name: 'Next stage', exact: true });
  await next.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: '2. validation', exact: true })).toHaveAttribute('aria-pressed', 'true');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  const audit = await new AxeBuilder({ page }).analyze();
  expect(audit.violations).toEqual([]);
});

test('event links open rejected outcomes and pagination preserves navigation', async ({ page }) => {
  await page.goto('/app/replay');
  await page.getByRole('link', { name: '26543', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Event 26543', exact: true })).toBeVisible();
  await expect(page.getByRole('main').getByText(/No position was stored: altitude out of bounds/)).toBeVisible();
  await page.getByRole('link', { name: 'Next events', exact: true }).click();
  await expect(page).toHaveURL(/offset=50/);
  await page.getByRole('link', { name: 'Previous events', exact: true }).click();
  await expect(page.getByRole('link', { name: '26543', exact: true })).toBeVisible();
});

test('replay mission needs an explicit solver-stage inspection and retains historical qualification', async ({ page }) => {
  await page.goto('/app/replay?event=26543');
  await expect(page.getByRole('main').getByText(/No position was stored: altitude out of bounds/)).toBeVisible();
  const saved = () => page.evaluate(() => JSON.parse(localStorage.getItem('receiver-console-missions-v1') || '{"state":{"completed":[]}}').state.completed);
  expect(await saved()).not.toContain('replay');
  await page.getByRole('button', { name: '5. solver', exact: true }).click();
  await expect.poll(saved).toContain('replay');
  await page.getByRole('button', { name: '5. solver', exact: true }).click();
  expect((await saved()).filter((id) => id === 'replay')).toHaveLength(1);
  const receivers = await (await page.request.get('/api/receivers')).json();
  expect(receivers.receivers.every((receiver) => receiver.qualification.state === 'UNQUALIFIED')).toBe(true);
});
