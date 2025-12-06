/**
 * Telegram WebApp SDK Wrapper
 *
 * Provides a clean interface for interacting with the Telegram Mini App SDK.
 * Handles cases where the app runs outside Telegram (for development).
 */

import WebApp from '@twa-dev/sdk';

let mainButtonCallback: (() => void) | null = null;

/**
 * Initialize Telegram WebApp
 * Call this once at app startup
 */
export function initTelegramWebApp(): void {
  if (typeof window === 'undefined') {
    return; // SSR safety
  }

  if (isTelegramWebApp()) {
    WebApp.ready();
    WebApp.expand();
  }
}

/**
 * Get Telegram initData for backend authentication
 * Returns null if not running in Telegram or if initData is not available
 */
export function getTelegramInitData(): string | null {
  if (typeof window === 'undefined') {
    return null; // SSR safety
  }

  if (!isTelegramWebApp()) {
    // Development fallback - return mock data or null
    console.warn('Not running in Telegram WebApp. initData unavailable.');
    return null;
  }

  const initData = WebApp.initData;

  if (!initData) {
    console.warn('Telegram WebApp initData is empty');
    return null;
  }

  return initData;
}

/**
 * Close the Telegram Mini App
 */
export function closeTelegramWebApp(): void {
  if (typeof window === 'undefined') {
    return; // SSR safety
  }

  if (isTelegramWebApp()) {
    WebApp.close();
  } else {
    console.log('Close requested, but not in Telegram WebApp');
  }
}

/**
 * Show the main button at the bottom of the Telegram app
 *
 * @param text - Button text to display
 * @param onClick - Callback function when button is clicked
 */
export function showMainButton(text: string, onClick: () => void): void {
  if (typeof window === 'undefined') {
    return; // SSR safety
  }

  if (!isTelegramWebApp()) {
    console.log('showMainButton called, but not in Telegram WebApp');
    return;
  }

  mainButtonCallback = onClick;
  WebApp.MainButton.setText(text);
  WebApp.MainButton.onClick(onClick);
  WebApp.MainButton.show();
}

/**
 * Hide the main button
 */
export function hideMainButton(): void {
  if (typeof window === 'undefined') {
    return; // SSR safety
  }

  if (!isTelegramWebApp()) {
    return;
  }

  if (mainButtonCallback) {
    WebApp.MainButton.offClick(mainButtonCallback);
    mainButtonCallback = null;
  }
  WebApp.MainButton.hide();
}

/**
 * Check if the app is running inside Telegram
 * Returns false during SSR or when not in Telegram
 */
export function isTelegramWebApp(): boolean {
  if (typeof window === 'undefined') {
    return false; // SSR
  }

  // Check if Telegram WebApp object exists
  return Boolean(WebApp && WebApp.initData);
}

/**
 * Get the current Telegram user (if available)
 * Useful for displaying user info in development
 */
export function getTelegramUser() {
  if (typeof window === 'undefined' || !isTelegramWebApp()) {
    return null;
  }

  return WebApp.initDataUnsafe?.user || null;
}

/**
 * Get the theme parameters from Telegram
 * Useful for matching app colors to Telegram theme
 */
export function getTelegramTheme() {
  if (typeof window === 'undefined' || !isTelegramWebApp()) {
    return null;
  }

  return WebApp.themeParams || null;
}
