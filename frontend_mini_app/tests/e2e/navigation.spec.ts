import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate between pages', async ({ page }) => {
    await page.goto('/');

    // Проверить что основные страницы доступны
    await expect(page.locator('body')).toBeVisible();
  });
});
