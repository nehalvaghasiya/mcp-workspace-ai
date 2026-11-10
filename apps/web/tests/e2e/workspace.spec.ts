import { expect, test } from '@playwright/test';

test.describe('real mock backend workflows', () => {
  test.skip(!process.env.E2E_BACKEND, 'Set E2E_BACKEND=1 with the mock API running on port 8000.');
  test('creates a sourced cross-app report, downloads artifacts, and restores history', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/');
    await page.getByRole('button', { name: 'Explore demo' }).click();
    await expect(page.getByText('Synthetic demo data', { exact: true })).toBeVisible();
    await page
      .getByRole('textbox', { name: 'Message Workspace AI' })
      .fill(
        'Review recent Northstar launch messages, check this week’s meetings, find the launch checklist in Drive, and create PDF, Word, PowerPoint and Excel reports with sources.',
      );
    await page.getByRole('button', { name: 'Send message' }).click();
    await expect(page.getByRole('button', { name: 'Cancel run' })).toBeHidden({ timeout: 60_000 });
    await expect(page.getByRole('link', { name: /^Download / })).toHaveCount(4);
    const download = page.waitForEvent('download');
    await page
      .getByRole('link', { name: /^Download / })
      .first()
      .click();
    expect((await download).suggestedFilename()).toBeTruthy();
    await expect(page.locator('.sources')).not.toHaveCount(0);
    await expect(page.locator('.tool-timeline li')).not.toHaveCount(0);
    const providers = await page.locator('.message.assistant .source-provider').allTextContents();
    expect(providers).toEqual(expect.arrayContaining(['gmail', 'calendar', 'drive']));
    const servers = await page.locator('.tool-server').allTextContents();
    expect(servers).toEqual(expect.arrayContaining(['gmail', 'calendar', 'drive', 'artifact']));
    await page.locator('.chat-scroll').evaluate((element) => {
      element.scrollTop = 0;
    });
    await page.screenshot({
      path: '../../demo/screenshots/reorganization/workspace-desktop.png',
      fullPage: true,
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('.activity-panel').getByRole('button', { name: 'Hide activity' }).click();
    await page.locator('.chat-scroll').evaluate((element) => {
      element.scrollTop = 0;
    });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
    await page.screenshot({
      path: '../../demo/screenshots/reorganization/workspace-mobile.png',
      fullPage: true,
    });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.getByRole('button', { name: 'Artifacts', exact: true }).click();
    await expect(page.getByRole('link', { name: /^Download / })).toHaveCount(4);
    await page.screenshot({
      path: '../../demo/screenshots/reorganization/artifact-library-desktop.png',
      fullPage: true,
    });
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
    await page.screenshot({
      path: '../../demo/screenshots/reorganization/artifact-library-mobile.png',
      fullPage: true,
    });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.getByRole('button', { name: 'MCP Explorer', exact: true }).click();
    await expect(
      page.getByRole('heading', { name: 'See how your workspace connects.' }),
    ).toBeVisible();
    await expect(page.locator('.catalog-tool')).not.toHaveCount(0);
    await page.reload();
    await expect(page.getByRole('button', { name: 'Workspace', exact: true })).toBeVisible();
    await page.locator('.history-item').first().click();
    await expect(page.getByRole('link', { name: /^Download / })).toHaveCount(4);
  });
  test('rejects a proposed external action without approving it', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/');
    await page.getByRole('button', { name: 'Explore demo' }).click();
    await page
      .getByRole('textbox', { name: 'Message Workspace AI' })
      .fill('Send a launch update email to alex@example.invalid.');
    await page.getByRole('button', { name: 'Send message' }).click();
    await expect(page.getByRole('button', { name: 'Approve exact action' })).toBeVisible();
    await expect(page.locator('.action-fields')).toContainText('alex@example.invalid');
    await page.getByRole('button', { name: 'Approve exact action' }).scrollIntoViewIfNeeded();
    await page.screenshot({
      path: '../../demo/screenshots/reorganization/exact-action-approval.png',
      fullPage: true,
    });
    await page.getByRole('button', { name: 'Reject', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Cancel run' })).toBeHidden();
    await expect(page.locator('.tool-timeline')).not.toContainText('send_draft');
  });
  test('approves a synthetic draft and its separate send action once each', async ({ page }) => {
    const decisions: string[] = [];
    page.on('request', (request) => {
      if (
        request.method() === 'POST' &&
        /\/api\/approvals\/[^/]+\/decide$/.test(new URL(request.url()).pathname)
      )
        decisions.push(request.url());
    });
    await page.goto('/');
    await page.getByRole('button', { name: 'Explore demo' }).click();
    await expect(page.getByText('Synthetic demo data', { exact: true })).toBeVisible();
    await page
      .getByRole('textbox', { name: 'Message Workspace AI' })
      .fill('Send a launch update email to alex@example.invalid.');
    await page.getByRole('button', { name: 'Send message' }).click();
    await expect(page.getByRole('heading', { name: 'Create this email draft' })).toBeVisible();
    await page.getByRole('button', { name: 'Approve exact action' }).click();
    await expect(page.getByRole('heading', { name: 'Send this email' })).toBeVisible();
    await expect(page.locator('.action-fields')).toContainText('alex@example.invalid');
    await page.getByRole('button', { name: 'Approve exact action' }).click();
    await expect(page.getByRole('button', { name: 'Cancel run' })).toBeHidden();
    await expect(
      page.locator('.tool-timeline .tool-step strong').filter({ hasText: /^send_draft$/ }),
    ).toHaveCount(1);
    expect(decisions).toHaveLength(2);
    expect(new Set(decisions).size).toBe(2);
  });
});
