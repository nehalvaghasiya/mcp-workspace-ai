import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { fixtureApi, proposal } from './fixtures';

test('demo entry is explicit, synthetic labeling persists, connector controls use CSRF', async ({
  page,
}) => {
  const mutations = await fixtureApi(page, { signedIn: false });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /A little more clarity/ })).toBeVisible();
  expect(mutations).toHaveLength(0);
  await page.getByRole('button', { name: 'Explore demo' }).click();
  await expect(page.getByRole('heading', { name: /What can we make/ })).toBeVisible();
  await expect(page.getByText('Synthetic demo data', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Connectors', exact: true }).click();
  await page.getByRole('switch', { name: 'Enable Gmail' }).click();
  await expect
    .poll(() => mutations.find((request) => request.path === '/api/connectors/gmail')?.csrf)
    .toBe('synthetic-csrf-fixture');
  await expect(page.getByRole('switch', { name: 'Enable Gmail' })).not.toBeChecked();
});

test('approval exposes exact action, allows one decision, and prevents expired actions', async ({
  page,
}) => {
  const mutations = await fixtureApi(page, {
    approvals: [
      proposal,
      {
        ...proposal,
        id: 'expired',
        summary: 'Expired send request',
        expires_at: '2000-01-01T00:00:00Z',
      },
    ],
  });
  await page.goto('/#approvals');
  const active = page
    .getByRole('article')
    .filter({ hasText: 'Send the launch review follow-up to Alex' });
  await expect(active).toContainText('alex@example.invalid');
  await expect(active).toContainText('Thursday at 3:00 PM America/Chicago');
  const expired = page.getByRole('article').filter({ hasText: 'Expired send request' });
  await expect(expired.getByRole('button', { name: 'Approve exact action' })).toBeDisabled();
  await active.getByRole('button', { name: 'Approve exact action' }).click();
  await expect(active.getByRole('button', { name: 'Approve exact action' })).toBeDisabled();
  expect(mutations.filter((request) => request.path.endsWith('/decide'))).toHaveLength(1);
});

test('MCP schemas and source metadata expand, artifacts link to authenticated downloads', async ({
  page,
}) => {
  await fixtureApi(page);
  await page.goto('/#mcp');
  await page.getByRole('searchbox', { name: 'Search tools' }).fill('send_draft');
  await expect(page.locator('.catalog-tool')).toHaveCount(1);
  await page.locator('.catalog-tool > summary').click();
  await expect(page.getByText('INPUT SCHEMA')).toBeVisible();
  await expect(page.locator('.catalog-tool')).toContainText('EXTERNAL EFFECT');
  await page.getByRole('link', { name: 'Skip to content' }).focus();
  await page.keyboard.press('Enter');
  await expect(
    page.getByRole('heading', { name: 'See how your workspace connects.' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Artifacts', exact: true }).click();
  const download = page.getByRole('link', { name: 'Download Northstar launch brief.pdf' });
  await expect(download).toHaveAttribute('href', '/api/artifacts/artifact-0/download');
  await expect(download).toHaveAttribute('download', '');
  const artifact = page.locator('.artifact-card').first();
  await artifact.locator('.artifact-info > details > summary').click();
  await artifact.locator('.source > summary').first().click();
  await expect(
    artifact.getByText('Synthetic demo source · no external link').first(),
  ).toBeVisible();
});

test('loading, offline, failed requests, and partial responses disclose actual state', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await fixtureApi(page, { delay: 500, partial: true });
  await page.goto('/');
  await expect(page.getByText('Opening your workspace')).toBeVisible();
  expect(
    await page
      .locator('.loading .spin')
      .evaluate((element) => getComputedStyle(element).animationName),
  ).toBe('none');
  await page.locator('.history-item').click();
  await expect(page.getByText(/Calendar and Drive are unavailable/)).toBeVisible();
  await expect(page.getByRole('alert')).toContainText('This run stopped before completing');
  await page.evaluate(() => window.dispatchEvent(new Event('offline')));
  await expect(page.getByText(/You’re offline/)).toBeVisible();
  await page.getByRole('textbox', { name: 'Message Workspace AI' }).fill('Try another request');
  await expect(page.getByRole('button', { name: 'Send message' })).toBeDisabled();
  await page.evaluate(() => window.dispatchEvent(new Event('online')));
  await expect(page.getByRole('button', { name: 'Send message' })).toBeEnabled();
  await page.getByRole('button', { name: 'Send message' }).click();
  await expect(
    page.getByRole('alert').filter({ hasText: 'Browser fixture endpoint not implemented' }),
  ).toBeVisible();
});

test('live mode only offers Google sign-in', async ({ page }) => {
  await fixtureApi(page, { signedIn: false, mode: 'live' });
  await page.goto('/');
  await expect(page.getByRole('link', { name: 'Sign in with Google' })).toHaveAttribute(
    'href',
    '/api/auth/google/start',
  );
  await expect(page.getByRole('button', { name: 'Explore demo' })).toHaveCount(0);
});

for (const viewport of [
  { width: 390, height: 844 },
  { width: 1440, height: 900 },
]) {
  test(`renders and supports keyboard navigation at ${viewport.width}x${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await fixtureApi(page);
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /What can we make/ })).toBeVisible();
    const accessibility = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    expect(accessibility.violations).toEqual([]);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
    await page.keyboard.press('Tab');
    await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('#main')).toBeFocused();
    await page.screenshot({ path: `qa/workspace-empty-${viewport.width}.png`, fullPage: true });
    if (viewport.width < 760) {
      await page.getByRole('button', { name: 'Open navigation' }).click();
      await expect(
        page.getByRole('button', { name: 'Close navigation', exact: true }),
      ).toBeFocused();
      await page.keyboard.press('Escape');
      await expect(page.getByRole('button', { name: 'Open navigation' })).toBeFocused();
      await page.getByRole('button', { name: 'Open navigation' }).click();
      await page.locator('.history-item').click();
    } else await page.locator('.history-item').click();
    await expect(page.getByText('The launch is close. One decision remains.')).toBeVisible();
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
    await page.screenshot({ path: `qa/workspace-response-${viewport.width}.png`, fullPage: true });
    if (viewport.width < 760) await page.getByRole('button', { name: 'Open navigation' }).click();
    await page.getByRole('button', { name: 'Approvals', exact: true }).click();
    await expect(page.getByText('Nothing waiting on your approval')).toBeVisible();
  });
}
