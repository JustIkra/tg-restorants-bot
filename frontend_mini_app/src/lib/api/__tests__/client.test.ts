/**
 * Tests for API client
 */

import { apiRequest, authenticateWithTelegram, getToken, setToken, removeToken } from '../client';

// Mock fetch
global.fetch = jest.fn();

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('Token management', () => {
    it('should store token in localStorage', () => {
      setToken('test-token');
      expect(localStorage.getItem('jwt_token')).toBe('test-token');
    });

    it('should retrieve token from localStorage', () => {
      localStorage.setItem('jwt_token', 'stored-token');
      const token = getToken();
      expect(token).toBe('stored-token');
    });

    it('should remove token from localStorage', () => {
      localStorage.setItem('jwt_token', 'test-token');
      removeToken();
      expect(localStorage.getItem('jwt_token')).toBeNull();
    });

    it('should return null when no token exists', () => {
      const token = getToken();
      expect(token).toBeNull();
    });
  });

  describe('apiRequest', () => {
    it('should add Authorization header when token exists', async () => {
      localStorage.setItem('jwt_token', 'test-token');
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: 'test' }),
      });

      await apiRequest('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should not add Authorization header when no token exists', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: 'test' }),
      });

      await apiRequest('/test');

      const callArgs = (global.fetch as jest.Mock).mock.calls[0][1];
      expect(callArgs.headers['Authorization']).toBeUndefined();
    });

    it('should parse JSON response successfully', async () => {
      const mockData = { id: 1, name: 'Test' };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockData,
      });

      const result = await apiRequest('/test');
      expect(result).toEqual(mockData);
    });

    it('should handle 204 No Content', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 204,
      });

      const result = await apiRequest('/test');
      expect(result).toBeUndefined();
    });

    it('should handle 401 Unauthorized and clear token', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ detail: 'Invalid token' }),
      });

      await expect(apiRequest('/test')).rejects.toThrow('Unauthorized. Please log in again.');
      expect(localStorage.getItem('jwt_token')).toBeNull();
    });

    it('should handle 403 Forbidden', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
        json: async () => ({ detail: 'Access denied' }),
      });

      await expect(apiRequest('/test')).rejects.toThrow('Access denied.');
    });

    it('should handle 404 Not Found', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Resource not found' }),
      });

      await expect(apiRequest('/test')).rejects.toThrow('Resource not found.');
    });

    it('should handle 500 Server Error', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'Database connection failed' }),
      });

      await expect(apiRequest('/test')).rejects.toThrow('Server error: Database connection failed');
    });

    it('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new TypeError('Network error'));

      await expect(apiRequest('/test')).rejects.toThrow('Network error');
    });

    it('should parse error detail from response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: 'Invalid request body' }),
      });

      await expect(apiRequest('/test')).rejects.toThrow('Invalid request body');
    });

    it('should use statusText when detail is not available', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({}),
      });

      await expect(apiRequest('/test')).rejects.toThrow('HTTP 400: Bad Request');
    });
  });

  describe('authenticateWithTelegram', () => {
    it('should send initData and store token', async () => {
      const mockResponse = {
        access_token: 'new-token',
        user: { tgid: 123, name: 'Test User', office: 'Moscow', role: 'user', is_active: true },
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      });

      const result = await authenticateWithTelegram('telegram-init-data');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/telegram'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ init_data: 'telegram-init-data' }),
        })
      );

      expect(localStorage.getItem('jwt_token')).toBe('new-token');
      expect(result).toEqual(mockResponse);
    });

    it('should throw error on failed authentication', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: 'Invalid initData' }),
      });

      await expect(authenticateWithTelegram('invalid-data')).rejects.toThrow('Invalid initData');
    });
  });
});
