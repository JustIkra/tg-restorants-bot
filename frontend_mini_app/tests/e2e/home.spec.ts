import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load home page with correct title', async ({ page }) => {
    await page.goto('/');

    // Check that the page loaded with correct title
    await expect(page).toHaveTitle(/Lunch Bot/i);
  });

  test('should display Telegram fallback when accessed outside Telegram', async ({ page }) => {
    await page.goto('/');

    // Wait for React useEffect to determine isInTelegram state and render TelegramFallback
    // Since we're not running in Telegram WebApp, should show fallback message
    await expect(page.getByRole('heading', { name: /Откройте через Telegram/i })).toBeVisible({ timeout: 10000 });

    // Check for fallback content
    await expect(page.getByText(/Это приложение работает только внутри Telegram/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display Telegram icon in fallback', async ({ page }) => {
    await page.goto('/');

    // Wait for React useEffect to complete and render TelegramFallback
    // Fallback should have the Telegram-themed UI
    await expect(page.getByText(/Найдите бот в поиске/i)).toBeVisible({ timeout: 10000 });
  });
});
