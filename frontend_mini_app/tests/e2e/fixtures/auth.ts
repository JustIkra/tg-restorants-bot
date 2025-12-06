/**
 * Authentication Fixture
 *
 * Handles JWT token acquisition and injection for e2e tests.
 */

import type { Page } from '@playwright/test';
import { mockTelegramWebApp, generateMockInitData } from './telegram-mock';

// API URL from environment or default
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get JWT token for test user from backend
 */
export async function getTestUserToken(tgid = 968116200): Promise<string> {
  const initData = generateMockInitData(tgid);

  const response = await fetch(`${API_URL}/auth/telegram`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      init_data: initData
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Auth failed (${response.status}): ${errorText}`);
  }

  const data = await response.json();

  if (!data.access_token) {
    throw new Error('No access_token in auth response');
  }

  return data.access_token;
}

/**
 * Setup authenticated page with Telegram mock and JWT token
 * Call this in test setup before navigating to pages
 */
export async function setupAuthenticatedPage(page: Page, tgid = 968116200): Promise<void> {
  // 1. Mock Telegram WebApp
  await mockTelegramWebApp(page, tgid);

  // 2. Get JWT token from backend
  let token: string;
  try {
    token = await getTestUserToken(tgid);
  } catch (error) {
    throw new Error(
      `Failed to authenticate test user (tgid=${tgid}). ` +
      `Make sure backend is running at ${API_URL}. ` +
      `Error: ${error instanceof Error ? error.message : String(error)}`
    );
  }

  // 3. Inject token into localStorage before navigation
  await page.addInitScript((authToken: string) => {
    localStorage.setItem('jwt_token', authToken);
    console.log('[Auth] JWT token injected into localStorage');
  }, token);
}

/**
 * Clear authentication state
 */
export async function clearAuth(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem('jwt_token');
    console.log('[Auth] JWT token cleared from localStorage');
  });
}

/**
 * Check if page is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  return await page.evaluate(() => {
    const token = localStorage.getItem('jwt_token');
    return Boolean(token);
  });
}

/**
 * Get current JWT token from page
 */
export async function getCurrentToken(page: Page): Promise<string | null> {
  return await page.evaluate(() => {
    return localStorage.getItem('jwt_token');
  });
}
