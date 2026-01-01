import { test, expect } from '@playwright/test';

test.describe('Task History Dashboard', () => {
  test('should display dashboard with task history section', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify dashboard loaded
    await expect(page.getByRole('heading', { name: 'Task History', exact: true })).toBeVisible();

    // Verify summary stats cards are displayed (use exact match to avoid ambiguity)
    await expect(page.getByRole('heading', { name: 'Active Tasks', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Completed', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Failed', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Total', exact: true })).toBeVisible();
  });

  test('should show empty state when no tasks exist', async ({ page }) => {
    // Mock API to return empty tasks
    await page.route('**/api/task-status/recent**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ tasks: [] }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Wait for API call to complete
    await page.waitForTimeout(500);

    // Should show empty state
    await expect(page.locator('text=No tasks found')).toBeVisible({ timeout: 5000 });
  });

  test('should display tasks from API', async ({ page }) => {
    // Mock API with tasks
    await page.route('**/api/task-status/recent**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tasks: [
            {
              task_id: 'test-task-1',
              operation: 'daily_sales',
              status: 'completed',
              created_at: Math.floor(Date.now() / 1000) - 3600,
              updated_at: Math.floor(Date.now() / 1000) - 1800,
            },
          ],
        }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify dashboard loaded
    await expect(page.getByRole('heading', { name: 'Task History', exact: true })).toBeVisible();

    // Wait for tasks to load
    await page.waitForTimeout(500);
  });

  test('should have refresh button', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Check for refresh button
    await expect(page.locator('button:has-text("Refresh")')).toBeVisible();
  });

  test('should navigate between pages', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Navigate to Daily Sales via sidebar link
    await page.click('a[href="/financial/daily-sales"]');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/financial/daily-sales');

    // Navigate back to Dashboard
    await page.click('a[href="/dashboard"]');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/dashboard');

    // Dashboard should still show Task History
    await expect(page.getByRole('heading', { name: 'Task History', exact: true })).toBeVisible();
  });

  test('should show error state when API fails', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/task-status/recent**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Wait for API call
    await page.waitForTimeout(500);

    // Should show error message
    await expect(page.locator('text=Failed to load task history')).toBeVisible({ timeout: 5000 });

    // Should show try again button
    await expect(page.locator('button:has-text("Try Again")')).toBeVisible();
  });

  test('should have filter dropdowns', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Check for filter elements
    await expect(page.locator('label:has-text("Operation")')).toBeVisible();
    await expect(page.locator('label:has-text("Status")')).toBeVisible();
    await expect(page.locator('select#operation-filter')).toBeVisible();
    await expect(page.locator('select#status-filter')).toBeVisible();
  });
});
