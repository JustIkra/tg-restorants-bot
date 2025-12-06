/**
 * Test Data Helpers
 *
 * Helpers for creating and managing test data via API.
 */

import { getTestUserToken } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Create a test cafe
 * Requires manager role token
 */
export async function createTestCafe(
  name: string,
  address: string,
  managerToken: string
): Promise<{ id: number; name: string; address: string }> {
  const response = await fetch(`${API_URL}/cafes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${managerToken}`
    },
    body: JSON.stringify({ name, address })
  });

  if (!response.ok) {
    throw new Error(`Failed to create cafe: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Create a test combo for a cafe
 */
export async function createTestCombo(
  cafeId: number,
  name: string,
  price: number,
  managerToken: string
): Promise<{ id: number; name: string; price: number }> {
  const response = await fetch(`${API_URL}/cafes/${cafeId}/combos`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${managerToken}`
    },
    body: JSON.stringify({ name, price, is_active: true })
  });

  if (!response.ok) {
    throw new Error(`Failed to create combo: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Create a test menu item for a cafe
 */
export async function createTestMenuItem(
  cafeId: number,
  data: {
    name: string;
    category: string;
    price: number;
    description?: string;
  },
  managerToken: string
): Promise<any> {
  const response = await fetch(`${API_URL}/cafes/${cafeId}/menu`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${managerToken}`
    },
    body: JSON.stringify({
      ...data,
      is_active: true
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to create menu item: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Delete all orders for test user
 * Used for cleanup after tests
 */
export async function deleteUserOrders(tgid = 968116200): Promise<void> {
  try {
    const token = await getTestUserToken(tgid);

    // Get all orders for user
    const ordersResponse = await fetch(`${API_URL}/orders`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!ordersResponse.ok) {
      console.warn(`Failed to fetch orders for cleanup: ${ordersResponse.status}`);
      return;
    }

    const orders = await ordersResponse.json();

    // Delete each order
    for (const order of orders) {
      const deleteResponse = await fetch(`${API_URL}/orders/${order.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!deleteResponse.ok) {
        console.warn(`Failed to delete order ${order.id}: ${deleteResponse.status}`);
      }
    }

    console.log(`[Cleanup] Deleted ${orders.length} orders for user ${tgid}`);
  } catch (error) {
    console.warn(`Cleanup failed: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Check API health
 * Useful to verify backend is running before tests
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET'
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * Wait for API to be ready
 * Retries health check with exponential backoff
 */
export async function waitForApi(
  maxRetries = 10,
  initialDelay = 100
): Promise<void> {
  let delay = initialDelay;

  for (let i = 0; i < maxRetries; i++) {
    const isHealthy = await checkApiHealth();

    if (isHealthy) {
      console.log(`[API] Backend ready at ${API_URL}`);
      return;
    }

    console.log(`[API] Waiting for backend... (attempt ${i + 1}/${maxRetries})`);
    await new Promise(resolve => setTimeout(resolve, delay));
    delay *= 2; // Exponential backoff
  }

  throw new Error(
    `Backend not available at ${API_URL} after ${maxRetries} retries. ` +
    `Make sure the backend is running.`
  );
}
