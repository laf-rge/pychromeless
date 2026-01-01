import { test, expect } from '@playwright/test';

test.describe('Daily Sales Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/financial/daily-sales');
    await page.waitForLoadState('networkidle');
  });

  test('should display the daily sales form', async ({ page }) => {
    // Check page title (use getByRole for specificity)
    await expect(page.getByRole('heading', { name: 'Daily Sales' })).toBeVisible();

    // Check form elements exist
    await expect(page.locator('label[for="date"]')).toContainText('Date');
    await expect(page.locator('input#date')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should have yesterday as default date', async ({ page }) => {
    const dateInput = page.locator('input#date');
    const value = await dateInput.inputValue();

    // Calculate yesterday's date
    const today = new Date();
    today.setDate(today.getDate() - 1);
    const expectedDate = today.toISOString().split('T')[0];

    expect(value).toBe(expectedDate);
  });

  test('should not allow future dates via max attribute', async ({ page }) => {
    const dateInput = page.locator('input#date');

    // Verify the date input has a max attribute set to yesterday
    const maxAttr = await dateInput.getAttribute('max');
    expect(maxAttr).toBeDefined();

    // The max date should be yesterday (today - 1 day)
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const expectedMax = yesterday.toISOString().split('T')[0];
    expect(maxAttr).toBe(expectedMax);
  });

  test('should show warning for dates older than 2 months', async ({ page }) => {
    const dateInput = page.locator('input#date');

    // Set a date from 3 months ago (but after Jan 1, 2025 cutoff)
    const oldDate = new Date();
    oldDate.setMonth(oldDate.getMonth() - 3);
    // Ensure it's after the cutoff
    if (oldDate < new Date('2025-01-01')) {
      oldDate.setFullYear(2025);
      oldDate.setMonth(1); // February 2025
    }
    const oldDateString = oldDate.toISOString().split('T')[0];

    await dateInput.fill(oldDateString);

    // Should show warning message about old date
    await expect(page.locator('text=more than 2 months old')).toBeVisible({ timeout: 5000 });
  });

  test('should have submit button that can be clicked', async ({ page }) => {
    // Verify submit button exists and is enabled
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeEnabled();

    // Verify the button contains appropriate text
    await expect(submitButton).toContainText(/Submit|Run|Process/i);
  });

  test('should navigate from dashboard to daily sales', async ({ page }) => {
    // Start at dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Click on Daily Sales link
    await page.click('a[href="/financial/daily-sales"]');
    await page.waitForLoadState('networkidle');

    // Should be on daily sales page
    expect(page.url()).toContain('/financial/daily-sales');
    await expect(page.getByRole('heading', { name: 'Daily Sales' })).toBeVisible();
  });
});
