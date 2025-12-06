# Frontend Components

**Location:** `frontend_mini_app/src/`

Telegram Mini App for lunch ordering. Stack: Next.js 16, React 19, Tailwind CSS 4, TypeScript.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [API Client Layer](#api-client-layer)
3. [Telegram WebApp Integration](#telegram-webapp-integration)
4. [UI Components](#ui-components)
5. [Main Page Flow](#main-page-flow)
6. [State Management](#state-management)
7. [Testing](#testing)

---

## Project Structure

```
frontend_mini_app/src/
├── app/
│   ├── layout.tsx          # Root layout with Geist fonts
│   ├── page.tsx            # Main page with order flow
│   └── globals.css         # Tailwind + custom styles
├── lib/
│   ├── api/
│   │   ├── client.ts       # HTTP client with JWT auth
│   │   ├── types.ts        # TypeScript types from API
│   │   └── hooks.ts        # SWR hooks for data fetching
│   └── telegram/
│       └── webapp.ts       # Telegram WebApp SDK wrapper
└── components/
    ├── CafeSelector/
    │   └── CafeSelector.tsx
    ├── ComboSelector/
    │   └── ComboSelector.tsx
    ├── Menu/
    │   └── MenuSection.tsx
    ├── ExtrasSection/
    │   └── ExtrasSection.tsx
    └── Cart/
        └── CheckoutButton.tsx
```

---

## API Client Layer

### client.ts

HTTP client with JWT authentication and error handling.

**Location:** `frontend_mini_app/src/lib/api/client.ts`

**Features:**
- JWT token management (localStorage)
- Authorization header injection
- HTTP error handling (401, 403, 404, 5xx)
- SSR-safe (checks for `window` object)
- Automatic token cleanup on 401

**Key Functions:**

```typescript
// Token management
getToken(): string | null
setToken(token: string): void
removeToken(): void

// HTTP requests
apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T>

// Authentication
authenticateWithTelegram(initData: string): Promise<{ access_token: string; user: User }>
```

**Configuration:**
- Base URL: `process.env.NEXT_PUBLIC_API_URL` or `http://localhost:8000/api/v1`
- Token storage key: `"jwt_token"`

**Error Handling:**
- 401 Unauthorized → clears token, throws error
- 403 Forbidden → "Access denied"
- 404 Not Found → "Resource not found"
- 5xx Server Error → "Server error: {detail}"
- Network errors → descriptive error message

---

### types.ts

TypeScript interfaces for all API entities.

**Location:** `frontend_mini_app/src/lib/api/types.ts`

**Core Entities:**

```typescript
interface User {
  tgid: number;
  name: string;
  office: string;
  role: "user" | "manager";
  is_active: boolean;
  created_at: string;
}

interface Cafe {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

interface Combo {
  id: number;
  cafe_id: number;
  name: string;
  categories: string[];       // ["salad", "soup", "main"]
  price: number;
  is_available: boolean;
}

interface MenuItem {
  id: number;
  cafe_id: number;
  name: string;
  description: string | null;
  category: string;           // "salad" | "soup" | "main" | "extra" | etc.
  price: number | null;
  is_available: boolean;
}

interface Order {
  id: number;
  user_tgid: number;
  cafe_id: number;
  combo: OrderCombo;
  extras: OrderExtra[];
  total_price: number;
  status: "pending" | "confirmed" | "cancelled";
  order_date: string;
  created_at: string;
}
```

**Request Payloads:**

```typescript
interface CreateOrderRequest {
  cafe_id: number;
  order_date: string;         // YYYY-MM-DD
  combo_id: number;
  combo_items: {
    category: string;
    menu_item_id: number;
  }[];
  extras?: {
    menu_item_id: number;
    quantity: number;
  }[];
  notes?: string;
}
```

**Response Wrappers:**

```typescript
interface ListResponse<T> {
  items: T[];
  total?: number;
}
```

---

### hooks.ts

SWR hooks for data fetching with caching and revalidation.

**Location:** `frontend_mini_app/src/lib/api/hooks.ts`

**Dependencies:**
- `swr` - Data fetching library with caching
- `apiRequest` from client.ts

**Hooks:**

```typescript
// Fetch active cafes
useCafes(activeOnly = true): {
  data: Cafe[] | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}

// Fetch combos for a cafe
useCombos(cafeId: number | null): {
  data: Combo[] | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}

// Fetch menu items for a cafe, optionally filtered by category
useMenu(cafeId: number | null, category?: string): {
  data: MenuItem[] | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}

// Create order mutation
useCreateOrder(): {
  createOrder: (data: CreateOrderRequest) => Promise<Order>;
  isLoading: boolean;
  error: Error | undefined;
}

// Fetch user orders with filters
useOrders(filters?: { date?: string; cafeId?: number; status?: string }): {
  data: Order[] | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}
```

**Features:**
- Automatic caching by endpoint URL
- Revalidation on window focus
- Conditional fetching (pass `null` to skip)
- TypeScript type inference
- Error handling

**Example Usage:**

```typescript
const { data: cafes, isLoading } = useCafes(true);
const { data: combos } = useCombos(selectedCafe?.id ?? null);
const { data: menuItems } = useMenu(selectedCafe?.id ?? null);
const { data: extras } = useMenu(selectedCafe?.id ?? null, "extra");
const { createOrder, isLoading: orderLoading } = useCreateOrder();
```

---

## Telegram WebApp Integration

### webapp.ts

Wrapper for Telegram WebApp SDK with SSR safety.

**Location:** `frontend_mini_app/src/lib/telegram/webapp.ts`

**Dependencies:**
- `@twa-dev/sdk` - Official Telegram WebApp SDK

**Functions:**

```typescript
// Initialize WebApp (call once on app startup)
initTelegramWebApp(): void

// Get initData string for backend authentication
getTelegramInitData(): string | null

// Close Telegram Mini App
closeTelegramWebApp(): void

// Show Telegram main button with text and callback
showMainButton(text: string, onClick: () => void): void

// Hide Telegram main button
hideMainButton(): void

// Check if running inside Telegram WebApp
isTelegramWebApp(): boolean

// Get current Telegram user info
getTelegramUser(): WebAppUser | undefined

// Get Telegram theme parameters
getTelegramTheme(): ThemeParams | undefined
```

**Features:**
- SSR-safe (checks for `window` object)
- Development mode support (graceful fallback when not in Telegram)
- Main button callback management
- Warning logs for debugging

**Example Usage:**

```typescript
// On app mount
useEffect(() => {
  initTelegramWebApp();
}, []);

// Authentication
useEffect(() => {
  const initData = getTelegramInitData();
  if (initData) {
    authenticateWithTelegram(initData)
      .then(() => console.log("Authenticated"))
      .catch(err => console.error("Auth failed:", err));
  }
}, []);

// After order creation
const handleCheckout = async () => {
  const order = await createOrder(orderData);
  alert(`Order #${order.id} created!`);
  closeTelegramWebApp();
};
```

---

## UI Components

### CafeSelector

Horizontal scrollable cafe selector.

**Location:** `frontend_mini_app/src/components/CafeSelector/CafeSelector.tsx`

**Props:**
```typescript
interface CafeSelectorProps {
  cafes: { id: number; name: string }[];
  activeCafeId: number;
  onCafeClick: (id: number) => void;
}
```

**Features:**
- Horizontal scroll without scrollbar
- Gradient animation on active cafe
- Hover effects
- Responsive design

**Styling:**
- Active: purple gradient with animation
- Inactive: semi-transparent background
- Hover: gradient fade-in

---

### ComboSelector

Combo set selector with prices.

**Location:** `frontend_mini_app/src/components/ComboSelector/ComboSelector.tsx`

**Props:**
```typescript
interface ComboSelectorProps {
  combos: Combo[];
  selectedComboId: number | null;
  onComboSelect: (id: number) => void;
}
```

**Features:**
- Displays combo name and price
- Radio-style selection (only one active)
- Gradient highlight for selected combo
- Disabled state for unavailable combos
- Horizontal scrollable layout

**Layout:**
```
┌────────────────┐  ┌────────────────┐
│ Салат + Суп    │  │ Салат + Основн.│
│ 450 ₽          │  │ 500 ₽          │
└────────────────┘  └────────────────┘
   ▲ selected         inactive
```

**Styling:**
- Selected: gradient background with animation
- Available: semi-transparent background, hover effect
- Unavailable: gray tones, no interaction

---

### MenuSection

Category-based menu item selector with radio selection.

**Location:** `frontend_mini_app/src/components/Menu/MenuSection.tsx`

**Props:**
```typescript
interface MenuSectionProps {
  category: string;              // "soup" | "salad" | "main"
  categoryLabel: string;         // "Супы", "Салаты", "Основные блюда"
  items: MenuItem[];
  selectedItemId: number | null;
  onItemSelect: (itemId: number) => void;
}
```

**Features:**
- Category title display
- Radio button selection (one item per category)
- Item name and description display
- Selected item highlighted with gradient
- Responsive layout

**Layout:**
```
Супы
┌──────────────────────────────┐
│ ○ Борщ украинский            │
│   Традиционный украинский... │
├──────────────────────────────┤
│ ● Куриный бульон             │  ← selected
│   С домашней лапшой          │
└──────────────────────────────┘
```

**Styling:**
- Selected: gradient background, filled radio button
- Unselected: semi-transparent background, empty radio button
- Hover: brighter background

---

### ExtrasSection

Additional items selector with quantity controls.

**Location:** `frontend_mini_app/src/components/ExtrasSection/ExtrasSection.tsx`

**Props:**
```typescript
interface ExtrasSectionProps {
  extras: MenuItem[];                      // category = "extra"
  cart: { [itemId: number]: number };
  addToCart: (itemId: number) => void;
  removeFromCart: (itemId: number) => void;
}
```

**Features:**
- Displays extra items with name, description, price
- "Добавить" button when quantity is 0
- Quantity controls (-/+) when item is in cart
- Empty state handling (returns null if no extras)
- Grid layout

**Layout:**
```
Дополнительно
┌────────────────────────────────┐
│ Фокачча с пряным маслом   [+]  │  ← not in cart
│ 60 г.                          │
│ 50 ₽                           │
├────────────────────────────────┤
│ Салат Цезарь        [−] 2 [+]  │  ← in cart
│ 200 г.                         │
│ 150 ₽                          │
└────────────────────────────────┘
```

**Styling:**
- Card background: semi-transparent with border
- Add button: purple gradient
- Quantity controls: white buttons on semi-transparent background
- Hover: brighter background

---

### CheckoutButton

Order submission button.

**Location:** `frontend_mini_app/src/components/Cart/CheckoutButton.tsx`

**Props:**
```typescript
interface CheckoutButtonProps {
  disabled: boolean;
  onClick?: () => void;
}
```

**States:**
- Active: purple gradient, clickable
- Disabled: gray background, cursor not-allowed

**Text:** "Оформить заказ"

---

## Main Page Flow

### page.tsx

Main application page with complete order flow.

**Location:** `frontend_mini_app/src/app/page.tsx`

### State Management

```typescript
// Selections
const [selectedCafe, setSelectedCafe] = useState<Cafe | null>(null);
const [selectedComboId, setSelectedComboId] = useState<number | null>(null);
const [comboItems, setComboItems] = useState<{ [category: string]: number }>({});
const [extrasCart, setExtrasCart] = useState<{ [itemId: number]: number }>({});

// Authentication
const [isAuthenticated, setIsAuthenticated] = useState(false);
```

### Data Fetching

```typescript
// SWR hooks
const { data: cafes } = useCafes(true);
const { data: combos } = useCombos(selectedCafe?.id ?? null);
const { data: menuItems } = useMenu(selectedCafe?.id ?? null);
const { data: extras } = useMenu(selectedCafe?.id ?? null, "extra");
const { createOrder, isLoading } = useCreateOrder();
```

### Computed Values

```typescript
// Selected combo object
const selectedCombo = combos?.find(c => c.id === selectedComboId) ?? null;

// Prices
const comboPrice = selectedCombo?.price ?? 0;
const extrasTotal = Object.entries(extrasCart).reduce((sum, [id, qty]) => {
  const extra = extras?.find(e => e.id === +id);
  return sum + (extra?.price ?? 0) * qty;
}, 0);
const totalPrice = comboPrice + extrasTotal;

// Validation
const isOrderComplete = selectedCombo &&
  selectedCombo.categories.every(cat => comboItems[cat]);
```

### Authentication Flow

```typescript
useEffect(() => {
  initTelegramWebApp();
}, []);

useEffect(() => {
  const initData = getTelegramInitData();
  if (!initData) {
    console.error("Not in Telegram WebApp");
    return;
  }

  authenticateWithTelegram(initData)
    .then(() => setIsAuthenticated(true))
    .catch(err => {
      console.error("Auth failed:", err);
      alert("Ошибка авторизации. Пожалуйста, перезапустите приложение.");
    });
}, []);
```

### Order Date Selection + Submission

- Доступность дат берём из `/orders/availability/week?cafe_id={id}` или точечного `/orders/availability/{date}?cafe_id={id}`.
- Логика выбора: если сегодня `can_order === true` — ставим сегодняшнюю дату; иначе выбираем ближайший день из ответа `week`.
- Перед отправкой валидируем, что `selectedDate` не `null`; если доступных дат нет — блокируем кнопку с текстом/ошибкой, показываем причину из availability.

```typescript
const [selectedDate, setSelectedDate] = useState<string | null>(null);

// Получаем доступные даты после выбора кафе
useEffect(() => {
  if (!selectedCafe) return;
  fetch(`/api/v1/orders/availability/week?cafe_id=${selectedCafe.id}`)
    .then(res => res.json())
    .then(data => {
      const nextAvailable = data.days.find((d: any) => d.can_order);
      setSelectedDate(nextAvailable?.date ?? null);
    })
    .catch(() => setSelectedDate(null));
}, [selectedCafe]);

const handleCheckout = async () => {
  if (!isOrderComplete || !selectedCafe || !selectedCombo || !selectedDate) return;

  const orderData: CreateOrderRequest = {
    cafe_id: selectedCafe.id,
    order_date: selectedDate, // ISO YYYY-MM-DD из доступности
    combo_id: selectedCombo.id,
    combo_items: Object.entries(comboItems).map(([category, itemId]) => ({
      category,
      menu_item_id: itemId
    })),
    extras: Object.entries(extrasCart).map(([itemId, quantity]) => ({
      menu_item_id: +itemId,
      quantity
    }))
  };

  try {
    const order = await createOrder(orderData);
    alert(`Заказ №${order.id} оформлен!`);
    closeTelegramWebApp();
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : "Неизвестная ошибка";
    alert(`Ошибка: ${errorMessage}`);
  }
};
```

### UI Layout

```typescript
<div>
  {/* Header */}
  <h1>Food Delivery</h1>
  <p>Выберите кафе и соберите свой обед</p>

  {/* Cafe Selector - always visible */}
  <CafeSelector cafes={cafes} activeCafeId={selectedCafe?.id} />

  {/* Combo Selector - visible after cafe selection */}
  {selectedCafe && (
    <ComboSelector combos={combos} selectedComboId={selectedComboId} />
  )}

  {/* Menu Sections - one per combo category */}
  {selectedCombo && selectedCombo.categories.map(category => (
    <MenuSection
      key={category}
      category={category}
      categoryLabel={categoryLabels[category]}
      items={menuItems.filter(item => item.category === category)}
      selectedItemId={comboItems[category] ?? null}
      onItemSelect={(itemId) => handleMenuItemSelect(category, itemId)}
    />
  ))}

  {/* Extras Section */}
  {selectedCombo && extras.length > 0 && (
    <ExtrasSection
      extras={extras}
      cart={extrasCart}
      addToCart={addToExtrasCart}
      removeFromCart={removeFromExtrasCart}
    />
  )}

  {/* Fixed Bottom: Order Summary + Checkout */}
  {selectedCombo && (
    <div className="fixed bottom-0">
      {/* Combo name and price */}
      <div>{summaryCombo.name} - {summaryCombo.price} ₽</div>

      {/* Selected items */}
      {summaryComboItems.map(item => (
        <div>{categoryLabels[item.category]}: {item.itemName}</div>
      ))}

      {/* Extras */}
      {summaryExtras.map(extra => (
        <div>{extra.name} x{extra.quantity} - {extra.subtotal} ₽</div>
      ))}

      {/* Total */}
      <div>Итого: {totalPrice} ₽</div>

      {/* Checkout button */}
      <CheckoutButton
        disabled={!isOrderComplete || isLoading}
        onClick={handleCheckout}
      />
    </div>
  )}
</div>
```

### Category Labels Mapping

```typescript
const categoryLabels: { [key: string]: string } = {
  salad: "Салаты",
  soup: "Супы",
  main: "Основное",
  side: "Гарниры",
  drink: "Напитки",
  dessert: "Десерты"
};
```

---

## State Management

### Flow Diagram

```
1. User opens app
   ├─> Telegram WebApp initializes
   ├─> Authenticate with backend via initData
   └─> Fetch cafes (useCafes hook)

2. User selects cafe
   ├─> setSelectedCafe(cafe)
   ├─> Reset combo and carts
   └─> Fetch combos (useCombos hook)

3. User selects combo
   ├─> setSelectedComboId(id)
   ├─> Reset comboItems
   └─> Fetch menu items (useMenu hook)

4. User selects items for each combo category
   ├─> setComboItems({ category: itemId, ... })
   └─> Validate: all categories filled?

5. User adds extras (optional)
   └─> setExtrasCart({ itemId: quantity, ... })

6. User clicks "Оформить заказ"
   ├─> Validate order completeness
   ├─> Create order payload (CreateOrderRequest)
   ├─> Submit via createOrder hook
   ├─> On success: show alert, close WebApp
   └─> On error: show error message
```

### State Reset Rules

- Change cafe → reset combo, comboItems, extrasCart
- Change combo → reset comboItems (keep extrasCart)
- Select item for category → update only that category in comboItems

---

## Testing

### Test Infrastructure

**Dependencies:**
- `@testing-library/react` v16.3.0 - Component testing
- `@testing-library/jest-dom` v6.9.1 - Custom matchers
- `@testing-library/user-event` v14.6.1 - User interaction simulation
- `jest` v30.2.0 - Test runner
- `jest-environment-jsdom` v30.2.0 - DOM environment
- `msw` v2.12.4 - API mocking

**Configuration:**
- `jest.config.js` - Next.js integration, jsdom environment
- `jest.setup.js` - Custom matchers, mocks (localStorage, matchMedia)

**Scripts:**
```bash
npm test              # Run all tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
```

### Test Suites

**API Client Tests** (`src/lib/api/__tests__/client.test.ts`) - 14 tests
- Token management (getToken, setToken, removeToken)
- apiRequest function (auth headers, error handling, JSON parsing)
- authenticateWithTelegram (success, error)

**SWR Hooks Tests** (`src/lib/api/__tests__/hooks.test.tsx`) - 7 tests
- useCafes (default filter, custom filter)
- useCombos (fetch, conditional fetching)
- useMenu (fetch, category filter, conditional fetching)
- useCreateOrder (success, error)

**Telegram WebApp Tests** (`src/lib/telegram/__tests__/webapp.test.ts`) - 8 tests
- isTelegramWebApp, initTelegramWebApp, getTelegramInitData
- closeTelegramWebApp, showMainButton, hideMainButton
- getTelegramUser, getTelegramTheme

**Component Tests:**
- ComboSelector (`__tests__/ComboSelector.test.tsx`) - 10 tests
- MenuSection (`__tests__/MenuSection.test.tsx`) - 11 tests
- ExtrasSection (`__tests__/ExtrasSection.test.tsx`) - 16 tests

**Total: 6 test suites, 66 tests, all passing**

### Test Coverage Areas

- ✓ Happy paths (successful operations)
- ✓ Error paths (network errors, validation errors)
- ✓ Edge cases (null values, empty arrays, disabled states)
- ✓ SSR safety (window checks)
- ✓ User interactions (clicks, selections, cart operations)
- ✓ Loading states
- ✓ Authentication flow

---

## Design System

### Color Palette

```typescript
const theme = {
  background: "#130F30",        // Dark background
  accent: "#A020F0",            // Purple
  accentDark: "#8B23CB",        // Dark purple
  card: "#7B6F9C",              // Cards (20-30% opacity)
  text: "white",
  textMuted: "gray-300",
};
```

### Gradients

```css
/* Active elements */
.gradient-active {
  background: linear-gradient(to right, #8B23CB, #A020F0, #7723B6);
}

/* Buttons */
.gradient-button {
  background: linear-gradient(to right, rgba(139, 35, 203, 0.8), rgba(160, 32, 240, 0.8));
}

/* Blur background */
.blur-bg {
  backdrop-filter: blur(12px);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

### Animations

```css
@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
```

---

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1  # Backend API URL
```

---

## API Integration Summary

| Endpoint | Hook | Purpose |
|----------|------|---------|
| `POST /auth/telegram` | `authenticateWithTelegram()` | Get JWT token |
| `GET /cafes?active_only=true` | `useCafes(true)` | Fetch cafe list |
| `GET /cafes/{id}/combos` | `useCombos(cafeId)` | Fetch combos for cafe |
| `GET /cafes/{id}/menu` | `useMenu(cafeId)` | Fetch menu items |
| `GET /cafes/{id}/menu?category=extra` | `useMenu(cafeId, "extra")` | Fetch extras |
| `POST /orders` | `useCreateOrder()` | Create new order |

---

## Notes

- **SSR Safety:** All API and Telegram functions check for `window` object
- **Development Mode:** App works outside Telegram with graceful degradation
- **Caching:** SWR automatically caches all GET requests
- **Token Persistence:** JWT token stored in localStorage
- **Error Handling:** All errors displayed to user via alerts
- **Validation:** Order submission disabled until all combo categories filled
- **Order date:** выбирается по доступности (сначала сегодня, иначе ближайший доступный день), не жёстко `today + 1`.
