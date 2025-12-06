/**
 * Centralized Selectors
 *
 * Reusable page selectors for e2e tests.
 * Prefer getByRole, getByText over CSS selectors where possible.
 */

/**
 * Cafe selection selectors
 */
export const cafeSelectors = {
  // Container for cafe selector
  container: '[data-testid="cafe-selector"]',

  // Cafe button by name (using text content)
  cafeButton: (name: string) => `button:has-text("${name}")`,

  // Active cafe indicator
  activeCafe: '.cafe-active',
};

/**
 * Combo selection selectors
 */
export const comboSelectors = {
  // Container for combo selector
  container: '[data-testid="combo-selector"]',

  // Combo card by name
  comboCard: (name: string) => `[data-testid="combo-${name}"]`,

  // Active combo indicator
  activeCombo: '.combo-active',
};

/**
 * Category selection selectors
 */
export const categorySelectors = {
  // Category button by name
  categoryButton: (name: string) => `button:has-text("${name}")`,

  // Active category indicator
  activeCategory: '.category-active',
};

/**
 * Menu selectors
 */
export const menuSelectors = {
  // Menu section by category
  section: (category: string) => `[data-testid="menu-section-${category}"]`,

  // Menu item by name (prefer getByRole('button', { name: '...' }))
  item: (name: string) => `[data-testid="menu-item-${name}"]`,

  // Menu item card
  itemCard: '[data-testid^="menu-item-"]',

  // Add to cart button within menu item
  addButton: 'button:has-text("+")',

  // Remove from cart button
  removeButton: 'button:has-text("-")',

  // Item quantity display
  quantity: '.item-quantity',
};

/**
 * Extras section selectors
 */
export const extrasSelectors = {
  // Extras container
  container: '[data-testid="extras-section"]',

  // Add extra button by item ID
  addButton: (itemId: number) => `[data-testid="add-extra-${itemId}"]`,

  // Remove extra button
  removeButton: (itemId: number) => `[data-testid="remove-extra-${itemId}"]`,

  // Extra quantity display
  quantity: (itemId: number) => `[data-testid="extra-quantity-${itemId}"]`,

  // Extra item card
  itemCard: (itemId: number) => `[data-testid="extra-item-${itemId}"]`,
};

/**
 * Cart selectors
 */
export const cartSelectors = {
  // Cart summary container
  summary: '[data-testid="cart-summary"]',

  // Total items count
  totalItems: '[data-testid="total-items"]',

  // Total price
  totalPrice: '[data-testid="total-price"]',

  // Cart icon badge
  cartBadge: '.cart-badge',

  // Checkout button (using text content)
  checkoutButton: 'button:has-text("Оформить заказ")',
};

/**
 * Checkout and order selectors
 */
export const checkoutSelectors = {
  // Checkout button
  button: 'button:has-text("Оформить заказ")',

  // Date selection
  dateSelector: '[data-testid="date-selector"]',
  dateOption: (date: string) => `[data-testid="date-option-${date}"]`,

  // Selected date display
  selectedDate: '[data-testid="selected-date"]',

  // Availability indicator
  availabilityStatus: '[data-testid="availability-status"]',

  // Order confirmation
  confirmButton: 'button:has-text("Подтвердить")',

  // Success message
  successMessage: '[data-testid="order-success"]',
};

/**
 * Common UI selectors
 */
export const commonSelectors = {
  // Loading spinner
  spinner: '[data-testid="loading-spinner"]',

  // Error message
  errorMessage: '[data-testid="error-message"]',

  // Success message
  successMessage: '[data-testid="success-message"]',

  // Modal/dialog
  modal: '[role="dialog"]',
  modalClose: '[aria-label="Close"]',

  // Telegram fallback
  telegramFallback: 'text=/Откройте через Telegram/i',
};

/**
 * Helper to build data-testid selector
 */
export function testId(id: string): string {
  return `[data-testid="${id}"]`;
}

/**
 * Helper to build text selector
 */
export function hasText(text: string): string {
  return `text=${text}`;
}

/**
 * Helper to build role selector
 */
export function role(
  role: string,
  options?: { name?: string; exact?: boolean }
): string {
  if (options?.name) {
    return `role=${role}[name="${options.name}"${options.exact ? 'i' : ''}]`;
  }
  return `role=${role}`;
}
