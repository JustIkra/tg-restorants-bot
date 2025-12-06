/**
 * Telegram WebApp Mock Fixture
 *
 * Mocks window.Telegram.WebApp for e2e tests.
 * Provides fake initData for test user (tgid=968116200).
 */

import type { Page } from '@playwright/test';

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

export interface TelegramWebAppMock {
  initData: string;
  initDataUnsafe: {
    user?: TelegramUser;
    query_id?: string;
  };
  ready: () => void;
  expand: () => void;
  close: () => void;
  MainButton: {
    setText: (text: string) => void;
    show: () => void;
    hide: () => void;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
  };
  themeParams?: Record<string, string>;
}

/**
 * Generate mock initData for test user
 * Default tgid: 968116200
 */
export function generateMockInitData(tgid = 968116200): string {
  // Simplified initData format for tests
  // In production, this would include hash validation
  const userData = {
    id: tgid,
    first_name: "Test",
    username: "testuser"
  };

  const userJson = encodeURIComponent(JSON.stringify(userData));
  return `query_id=AAAAAAA&user=${userJson}`;
}

/**
 * Mock Telegram WebApp in page context
 * Must be called before page.goto()
 */
export async function mockTelegramWebApp(page: Page, tgid = 968116200): Promise<void> {
  const initData = generateMockInitData(tgid);

  await page.addInitScript(({ mockInitData, mockTgid }: { mockInitData: string; mockTgid: number }) => {
    // Create Telegram WebApp mock
    (window as any).Telegram = {
      WebApp: {
        initData: mockInitData,
        initDataUnsafe: {
          user: {
            id: mockTgid,
            first_name: "Test",
            username: "testuser",
            language_code: "en"
          },
          query_id: "AAAAAAA"
        },
        ready: () => {
          console.log('[Mock] Telegram.WebApp.ready()');
        },
        expand: () => {
          console.log('[Mock] Telegram.WebApp.expand()');
        },
        close: () => {
          console.log('[Mock] Telegram.WebApp.close()');
        },
        MainButton: {
          text: '',
          isVisible: false,
          setText: function(text: string) {
            this.text = text;
            console.log('[Mock] MainButton.setText:', text);
          },
          show: function() {
            this.isVisible = true;
            console.log('[Mock] MainButton.show()');
          },
          hide: function() {
            this.isVisible = false;
            console.log('[Mock] MainButton.hide()');
          },
          onClick: (callback: () => void) => {
            console.log('[Mock] MainButton.onClick');
            // Store callback for testing
          },
          offClick: (callback: () => void) => {
            console.log('[Mock] MainButton.offClick');
          }
        },
        themeParams: {
          bg_color: '#ffffff',
          text_color: '#000000',
          hint_color: '#999999',
          link_color: '#007aff',
          button_color: '#007aff',
          button_text_color: '#ffffff'
        }
      }
    };

    console.log('[Mock] Telegram WebApp initialized for user:', mockTgid);
  }, { mockInitData: initData, mockTgid: tgid });
}
