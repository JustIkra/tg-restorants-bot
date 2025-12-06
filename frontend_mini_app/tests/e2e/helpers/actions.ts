/**
 * Reusable User Actions
 *
 * Common actions that users perform in the app.
 * These helpers encapsulate complex interactions for reuse in tests.
 */

import type { Page } from '@playwright/test';
import { cafeSelectors, categorySelectors, menuSelectors, extrasSelectors, checkoutSelectors } from './selectors';

/**
 * Select a cafe by name
 * Waits for navigation/state update to complete
 */
export async function selectCafe(page: Page, cafeName: string): Promise<void> {
  // Find and click cafe button by text content
  await page.getByRole('button', { name: cafeName }).click();

  // Wait for any network requests to settle
  // Using waitForLoadState('load') instead of deprecated 'networkidle'
  await page.waitForLoadState('load');

  // Optional: wait for menu to load
  await page.waitForTimeout(500); // Brief pause for state updates
}

/**
 * Select a combo by name
 */
export async function selectCombo(page: Page, comboName: string): Promise<void> {
  await page.getByRole('button', { name: comboName }).click();
  await page.waitForLoadState('load');
  await page.waitForTimeout(500);
}

/**
 * Select a category by name
 */
export async function selectCategory(page: Page, categoryName: string): Promise<void> {
  await page.getByRole('button', { name: categoryName }).click();

  // Wait for filtered menu to render
  await page.waitForTimeout(300);
}

/**
 * Add menu item to cart by name
 * Clicks the "+" button on the menu item
 */
export async function addMenuItem(page: Page, itemName: string, quantity = 1): Promise<void> {
  // Find the menu item card containing the item name
  const itemCard = page.locator(`text=${itemName}`).locator('..').locator('..');

  // Click add button multiple times for quantity
  for (let i = 0; i < quantity; i++) {
    await itemCard.getByRole('button', { name: '+' }).click();
    await page.waitForTimeout(100); // Brief pause between clicks
  }
}

/**
 * Remove menu item from cart
 */
export async function removeMenuItem(page: Page, itemName: string, quantity = 1): Promise<void> {
  const itemCard = page.locator(`text=${itemName}`).locator('..').locator('..');

  for (let i = 0; i < quantity; i++) {
    await itemCard.getByRole('button', { name: '-' }).click();
    await page.waitForTimeout(100);
  }
}

/**
 * Add extra item to cart by item name
 */
export async function addExtra(page: Page, itemName: string, quantity = 1): Promise<void> {
  // Extras section should be visible
  const extrasSection = page.locator('[data-testid="extras-section"]').or(
    page.locator('text=/Дополнительно/i').locator('..')
  );

  // Find extra item by name
  const extraItem = extrasSection.locator(`text=${itemName}`).locator('..').locator('..');

  // Click add button
  for (let i = 0; i < quantity; i++) {
    await extraItem.getByRole('button', { name: '+' }).click();
    await page.waitForTimeout(100);
  }
}

/**
 * Remove extra item from cart
 */
export async function removeExtra(page: Page, itemName: string, quantity = 1): Promise<void> {
  const extrasSection = page.locator('[data-testid="extras-section"]').or(
    page.locator('text=/Дополнительно/i').locator('..')
  );

  const extraItem = extrasSection.locator(`text=${itemName}`).locator('..').locator('..');

  for (let i = 0; i < quantity; i++) {
    await extraItem.getByRole('button', { name: '-' }).click();
    await page.waitForTimeout(100);
  }
}

/**
 * Get cart total items count
 */
export async function getCartItemsCount(page: Page): Promise<number> {
  // Look for cart badge or total items display
  const cartBadge = page.locator('.cart-badge').or(
    page.locator('[data-testid="total-items"]')
  );

  const text = await cartBadge.textContent();
  return text ? parseInt(text.trim(), 10) : 0;
}

/**
 * Get cart total price
 */
export async function getCartTotalPrice(page: Page): Promise<number> {
  const totalPriceElement = page.locator('[data-testid="total-price"]').or(
    page.locator('text=/Итого:/').locator('..')
  );

  const text = await totalPriceElement.textContent();

  // Extract number from text like "1500 ₽" or "Итого: 1500"
  if (!text) return 0;

  const match = text.match(/(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
}

/**
 * Select order date
 */
export async function selectOrderDate(page: Page, date: string): Promise<void> {
  // Find date selector/picker
  const dateOption = page.locator(`[data-testid="date-option-${date}"]`).or(
    page.locator(`text=${date}`)
  );

  await dateOption.click();
  await page.waitForTimeout(200);
}

/**
 * Click checkout button
 */
export async function clickCheckout(page: Page): Promise<void> {
  const checkoutButton = page.getByRole('button', { name: /Оформить заказ/i });

  await checkoutButton.click();

  // Wait for order creation request
  await page.waitForResponse(
    (response) => response.url().includes('/orders') && response.request().method() === 'POST',
    { timeout: 10000 }
  ).catch(() => {
    // Timeout is acceptable if order was already created
    console.warn('No order creation request detected within timeout');
  });
}

/**
 * Wait for success message after order creation
 */
export async function waitForOrderSuccess(page: Page): Promise<void> {
  // Look for success indicator
  await page.locator('[data-testid="order-success"]').or(
    page.locator('text=/Заказ создан/i')
  ).or(
    page.locator('text=/Успешно/i')
  ).waitFor({ state: 'visible', timeout: 10000 });
}

/**
 * Wait for error message
 */
export async function waitForErrorMessage(page: Page, timeout = 5000): Promise<string | null> {
  try {
    const errorElement = page.locator('[data-testid="error-message"]').or(
      page.locator('text=/Ошибка/i')
    );

    await errorElement.waitFor({ state: 'visible', timeout });

    return await errorElement.textContent();
  } catch {
    return null;
  }
}

/**
 * Clear cart (remove all items)
 */
export async function clearCart(page: Page): Promise<void> {
  // Switch cafe to reset cart, or remove items manually
  // Easiest approach: refresh page or switch cafe

  // Get all items in cart and remove them
  const removeButtons = page.getByRole('button', { name: '-' });
  const count = await removeButtons.count();

  // Click all remove buttons until cart is empty
  for (let i = 0; i < count * 10; i++) { // Safety limit
    const itemsCount = await getCartItemsCount(page);
    if (itemsCount === 0) break;

    const firstRemoveButton = removeButtons.first();
    if (await firstRemoveButton.isVisible()) {
      await firstRemoveButton.click();
      await page.waitForTimeout(100);
    } else {
      break;
    }
  }
}

/**
 * Wait for page to be fully loaded
 * Checks for loading indicators to disappear
 */
export async function waitForPageReady(page: Page): Promise<void> {
  // Wait for main load state
  await page.waitForLoadState('load');

  // Wait for any spinners to disappear
  const spinner = page.locator('[data-testid="loading-spinner"]').or(
    page.locator('.animate-spin')
  );

  try {
    await spinner.waitFor({ state: 'hidden', timeout: 10000 });
  } catch {
    // Spinner might not exist, which is fine
  }

  // Brief pause for React hydration
  await page.waitForTimeout(500);
}

/**
 * Complete full order flow
 * Helper for happy path tests
 */
export async function completeOrder(
  page: Page,
  options: {
    cafe: string;
    items: Array<{ name: string; quantity?: number }>;
    extras?: Array<{ name: string; quantity?: number }>;
    date?: string;
  }
): Promise<void> {
  // Select cafe
  await selectCafe(page, options.cafe);

  // Add menu items
  for (const item of options.items) {
    await addMenuItem(page, item.name, item.quantity || 1);
  }

  // Add extras if provided
  if (options.extras) {
    for (const extra of options.extras) {
      await addExtra(page, extra.name, extra.quantity || 1);
    }
  }

  // Select date if provided
  if (options.date) {
    await selectOrderDate(page, options.date);
  }

  // Click checkout
  await clickCheckout(page);

  // Wait for success
  await waitForOrderSuccess(page);
}
