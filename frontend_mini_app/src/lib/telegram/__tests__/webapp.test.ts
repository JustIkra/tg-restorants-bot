/**
 * Tests for Telegram WebApp wrapper
 */

import {
  initTelegramWebApp,
  getTelegramInitData,
  closeTelegramWebApp,
  showMainButton,
  hideMainButton,
  isTelegramWebApp,
  getTelegramUser,
  getTelegramTheme,
} from '../webapp';

// Mock @twa-dev/sdk
jest.mock('@twa-dev/sdk', () => ({
  ready: jest.fn(),
  expand: jest.fn(),
  close: jest.fn(),
  initData: 'mock-init-data',
  initDataUnsafe: {
    user: {
      id: 123456789,
      first_name: 'John',
      last_name: 'Doe',
      username: 'johndoe',
    },
  },
  themeParams: {
    bg_color: '#ffffff',
    text_color: '#000000',
    hint_color: '#999999',
    link_color: '#0000ff',
    button_color: '#0088cc',
    button_text_color: '#ffffff',
  },
  MainButton: {
    setText: jest.fn(),
    show: jest.fn(),
    hide: jest.fn(),
    onClick: jest.fn(),
    offClick: jest.fn(),
  },
}));

import WebApp from '@twa-dev/sdk';

describe('Telegram WebApp Wrapper', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset console methods
    jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('isTelegramWebApp', () => {
    it('should return true when WebApp is available', () => {
      expect(isTelegramWebApp()).toBe(true);
    });
  });

  describe('initTelegramWebApp', () => {
    it('should call ready() and expand()', () => {
      initTelegramWebApp();

      expect(WebApp.ready).toHaveBeenCalled();
      expect(WebApp.expand).toHaveBeenCalled();
    });
  });

  describe('getTelegramInitData', () => {
    it('should return initData when available', () => {
      const initData = getTelegramInitData();

      expect(initData).toBe('mock-init-data');
    });

    it('should return null and warn when initData is empty', () => {
      const originalInitData = WebApp.initData;
      (WebApp as any).initData = '';

      const initData = getTelegramInitData();

      expect(initData).toBeNull();
      expect(console.warn).toHaveBeenCalledWith('Telegram WebApp initData is empty');

      // Restore
      (WebApp as any).initData = originalInitData;
    });
  });

  describe('closeTelegramWebApp', () => {
    it('should call WebApp.close()', () => {
      closeTelegramWebApp();

      expect(WebApp.close).toHaveBeenCalled();
    });
  });

  describe('showMainButton', () => {
    it('should set button text and show button', () => {
      const onClick = jest.fn();

      showMainButton('Test Button', onClick);

      expect(WebApp.MainButton.setText).toHaveBeenCalledWith('Test Button');
      expect(WebApp.MainButton.onClick).toHaveBeenCalledWith(onClick);
      expect(WebApp.MainButton.show).toHaveBeenCalled();
    });
  });

  describe('hideMainButton', () => {
    it('should hide button and remove callback', () => {
      const onClick = jest.fn();

      // First show button
      showMainButton('Test', onClick);

      // Then hide it
      hideMainButton();

      expect(WebApp.MainButton.offClick).toHaveBeenCalledWith(onClick);
      expect(WebApp.MainButton.hide).toHaveBeenCalled();
    });

    it('should handle hiding when no callback exists', () => {
      hideMainButton();

      expect(WebApp.MainButton.hide).toHaveBeenCalled();
    });
  });

  describe('getTelegramUser', () => {
    it('should return user data when available', () => {
      const user = getTelegramUser();

      expect(user).toEqual({
        id: 123456789,
        first_name: 'John',
        last_name: 'Doe',
        username: 'johndoe',
      });
    });
  });

  describe('getTelegramTheme', () => {
    it('should return theme parameters', () => {
      const theme = getTelegramTheme();

      expect(theme).toEqual({
        bg_color: '#ffffff',
        text_color: '#000000',
        hint_color: '#999999',
        link_color: '#0000ff',
        button_color: '#0088cc',
        button_text_color: '#ffffff',
      });
    });
  });
});
