import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should show dashboard for authenticated users', async ({ page }) => {
    // In E2E test mode, auth is mocked and users are always authenticated
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Should be on dashboard
    const url = page.url();
    expect(url).toContain('/dashboard');

    // Should see dashboard content (use more specific selector)
    await expect(page.getByRole('heading', { name: 'Task History', exact: true })).toBeVisible();
  });

  test('should navigate between pages when authenticated', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Root should show dashboard in test mode
    await expect(page.getByRole('heading', { name: 'Task History', exact: true })).toBeVisible();

    // Navigate to Daily Sales via sidebar
    await page.click('a[href="/financial/daily-sales"]');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/financial/daily-sales');

    // Navigate back to Dashboard
    await page.click('a[href="/dashboard"]');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/dashboard');
  });

  test('should display navigation sidebar', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Check sidebar navigation links exist
    await expect(page.locator('a[href="/dashboard"]')).toBeVisible();
    await expect(page.locator('a[href="/financial/daily-sales"]')).toBeVisible();
  });
});
