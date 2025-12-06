import { test, expect } from '@playwright/test';

/**
 * API Health tests are skipped because they require a running backend server.
 * These tests should be run as part of integration testing with the backend.
 */

test.describe.skip('API Health', () => {
  test('backend health check', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
  });

  test('backend health check all services', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health/all');
    expect(response.ok()).toBeTruthy();
  });
});
