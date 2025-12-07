# Frontend Components

**Location:** `frontend_mini_app/src/`

Telegram Mini App for lunch ordering. Stack: Next.js 16, React 19, Tailwind CSS 4, TypeScript.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [API Client Layer](#api-client-layer)
3. [Telegram WebApp Integration](#telegram-webapp-integration)
4. [UI Components](#ui-components)
5. [Profile Components](#profile-components)
6. [Main Page Flow](#main-page-flow)
7. [State Management](#state-management)
8. [Testing](#testing)

---

## Project Structure

```
frontend_mini_app/src/
├── app/
│   ├── layout.tsx          # Root layout with Geist fonts
│   ├── page.tsx            # Main page with order flow (user role)
│   ├── profile/
│   │   └── page.tsx        # User profile page (all users)
│   ├── manager/
│   │   └── page.tsx        # Manager admin panel (manager role)
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
    ├── Cart/
    │   └── CheckoutButton.tsx
    ├── Profile/            # Profile page components
    │   ├── ProfileStats.tsx
    │   ├── ProfileRecommendations.tsx
    │   └── ProfileBalance.tsx
    └── Manager/            # Manager-only components
        ├── UserList.tsx
        ├── UserForm.tsx
        ├── CafeList.tsx
        ├── CafeForm.tsx
        ├── MenuManager.tsx
        ├── ComboForm.tsx
        ├── MenuItemForm.tsx
        ├── RequestsList.tsx
        ├── ReportsList.tsx
        └── BalanceManager.tsx
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

interface BalanceResponse {
  tgid: number;
  weekly_limit: number | null;
  spent_this_week: number;
  remaining: number | null;
}

interface OrderStats {
  orders_last_30_days: number;
  categories: { [category: string]: { count: number; percent: number } };
  unique_dishes: number;
  favorite_dishes: { name: string; count: number }[];
}

interface RecommendationsResponse {
  summary: string | null;
  tips: string[];
  stats: OrderStats;
  generated_at: string | null;
}

interface DeadlineItem {
  weekday: number;          // 0=Пн, 1=Вт, ..., 6=Вс
  deadline_time: string;    // "10:00"
  is_enabled: boolean;
  advance_days: number;     // 0-6
}

interface DeadlineScheduleResponse {
  cafe_id: number;
  schedule: DeadlineItem[];
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

// Fetch user recommendations (AI-generated)
useUserRecommendations(tgid: number | null): {
  data: RecommendationsResponse | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}

// Fetch user balance information
useUserBalance(tgid: number | null): {
  data: BalanceResponse | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}

// Update user balance limit (manager only)
useUpdateBalanceLimit(): {
  updateLimit: (tgid: number, weekly_limit: number | null) => Promise<User>;
}

// Fetch deadline schedule for a cafe (manager only)
useDeadlineSchedule(cafeId: number | null): {
  data: DeadlineScheduleResponse | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}

// Update deadline schedule for a cafe (manager only)
useUpdateDeadlineSchedule(): {
  updateSchedule: (cafeId: number, schedule: DeadlineItem[]) => Promise<DeadlineScheduleResponse>;
  isLoading: boolean;
  error: Error | undefined;
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

// Profile page hooks
const { data: recommendations } = useUserRecommendations(user.tgid);
const { data: balance } = useUserBalance(user.tgid);
const { updateLimit } = useUpdateBalanceLimit();

// Manager deadline schedule hooks
const { data: schedule } = useDeadlineSchedule(selectedCafeId);
const { updateSchedule } = useUpdateDeadlineSchedule();
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

## Profile Components

Components for displaying user profile information, statistics, and balance management.

**Location:** `frontend_mini_app/src/components/Profile/`

### ProfileStats

**Path:** `frontend_mini_app/src/components/Profile/ProfileStats.tsx`

**Назначение:** Отображает статистику заказов пользователя за последние 30 дней

**Props:**
| Prop | Тип | Описание |
|------|-----|----------|
| stats | OrderStats | Статистика заказов пользователя |

**Использование:**
```tsx
import ProfileStats from "@/components/Profile/ProfileStats";

<ProfileStats stats={recommendations.stats} />
```

**Особенности:**
- Отображает количество заказов за последние 30 дней
- Показывает распределение по категориям (суп, салат, основное и т.д.) с процентами
- Отображает количество уникальных блюд
- Показывает топ-5 любимых блюд с количеством заказов
- Empty state: "Пока нет заказов" если нет заказов за 30 дней

**Category Labels Mapping:**
```typescript
const categoryLabels: { [key: string]: string } = {
  soup: "Супы",
  salad: "Салаты",
  main: "Основное",
  extra: "Дополнительно",
  side: "Гарниры",
  drink: "Напитки",
  dessert: "Десерты",
};
```

**Дизайн:**
- Semi-transparent card с backdrop blur
- Purple gradient header icon (FaChartLine)
- Nested cards для каждого раздела статистики
- Русская pluralization для "заказ/заказа/заказов"
- Процентные значения с одним знаком после запятой

---

### ProfileRecommendations

**Path:** `frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx`

**Назначение:** Отображает AI-рекомендации по питанию на основе истории заказов

**Props:**
| Prop | Тип | Описание |
|------|-----|----------|
| recommendations | RecommendationsResponse | Объект с рекомендациями и статистикой |

**Использование:**
```tsx
import ProfileRecommendations from "@/components/Profile/ProfileRecommendations";

<ProfileRecommendations recommendations={recommendations} />
```

**Особенности:**
- Отображает текстовый summary (персональное резюме привычек питания)
- Показывает список рекомендаций (tips) как маркированный список
- Отображает дату генерации рекомендаций в формате "DD Month YYYY"
- Empty state: "Сделайте минимум 5 заказов для получения рекомендаций" если summary === null

**Date Formatting:**
```typescript
const formatDate = (isoString: string | null) => {
  if (!isoString) return null;
  return new Date(isoString).toLocaleDateString("ru-RU", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};
```

**Дизайн:**
- Semi-transparent card с backdrop blur
- Purple gradient header icon (FaLightbulb)
- Tips отображаются с `list-disc list-inside` для bullet points
- Generated date в правом нижнем углу мелким текстом

---

### ProfileBalance

**Path:** `frontend_mini_app/src/components/Profile/ProfileBalance.tsx`

**Назначение:** Отображает информацию о корпоративном балансе пользователя

**Props:**
| Prop | Тип | Описание |
|------|-----|----------|
| balance | BalanceResponse | Объект с балансом пользователя |

**Использование:**
```tsx
import ProfileBalance from "@/components/Profile/ProfileBalance";

<ProfileBalance balance={balance} />
```

**Особенности:**
- Отображает недельный лимит (weekly_limit) или "Не установлен"
- Показывает потраченную сумму (spent_this_week) с двумя знаками после запятой
- Отображает остаток (remaining) или "—" если лимит не установлен
- Progress bar с динамическим цветом:
  - Зеленый: < 70% лимита потрачено
  - Желтый: 70-90% лимита потрачено
  - Красный: > 90% лимита потрачено
- Progress bar показывается только если weekly_limit !== null

**Progress Bar Logic:**
```typescript
const getProgressColor = (percent: number) => {
  if (percent < 70) return "bg-green-500";
  if (percent < 90) return "bg-yellow-500";
  return "bg-red-500";
};

const percent =
  balance.weekly_limit !== null
    ? (balance.spent_this_week / balance.weekly_limit) * 100
    : 0;
```

**Дизайн:**
- Semi-transparent card с backdrop blur
- Purple gradient header icon (FaWallet)
- Все суммы форматируются с `.toFixed(2)` → "XXX.XX ₽"
- Progress bar: `bg-gray-700` background, динамический цвет для прогресса
- Progress bar ограничен 100% максимумом (`Math.min(percent, 100)`)

---

### Profile Page

**Path:** `frontend_mini_app/src/app/profile/page.tsx`

**Назначение:** Страница профиля пользователя с отображением статистики, рекомендаций и баланса

**Route:** `/profile`

**Доступ:** Все пользователи (user и manager)

**Features:**

1. **Authentication:**
   - Получает user object из localStorage
   - Redirect на `/` если user не найден
   - Error handling для invalid JSON

2. **Data Fetching:**
   - `useUserRecommendations(user.tgid)` - параллельная загрузка рекомендаций
   - `useUserBalance(user.tgid)` - параллельная загрузка баланса
   - Conditional fetching: skip if user is null

3. **Layout:**
   - Header: "Мой профиль" + back button (FaArrowLeft → `/`)
   - ProfileStats component
   - ProfileRecommendations component
   - ProfileBalance component

4. **States:**
   - Loading: Skeleton placeholders с shimmer эффектом
   - Error: Red error banners с сообщениями
   - Empty: Gray placeholder cards
   - Loaded: Display components с данными

**Navigation:**
```tsx
// Header button в app/page.tsx
<button
  onClick={() => router.push("/profile")}
  className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B23CB]/50 to-[#A020F0]/50 border border-white/20 backdrop-blur-md shadow-lg"
  aria-label="Профиль"
>
  <FaUser className="text-white text-xl" />
</button>
```

**Background:**
- Dark background: `#130F30`
- Purple gradient blurs для визуального эффекта
- Consistent с дизайн-системой главной страницы

**Example Usage:**
```typescript
// Redirect to profile
router.push("/profile");

// From main page
const handleProfileClick = () => {
  router.push("/profile");
};
```

---

## Navigation Components

### Manager Navigation Button

**Location:** `frontend_mini_app/src/app/page.tsx` (lines 320-329)

**Description:** Fixed position button that allows managers to navigate to the admin panel.

**Visibility:** Only visible for users with `role === "manager"`

**Features:**
- Fixed positioning in top-right corner
- Purple gradient background
- Responsive text (icon only on mobile, icon + text on desktop)
- Smooth hover effect
- Accessibility support (aria-label)

**Implementation:**
```tsx
{user?.role === "manager" && (
  <button
    onClick={() => router.push("/manager")}
    className="fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-lg text-white shadow-lg hover:opacity-90 transition-opacity"
    aria-label="Панель менеджера"
  >
    <FaUserShield className="text-lg" />
    <span className="hidden sm:inline text-sm font-medium">Панель менеджера</span>
  </button>
)}
```

**Icon:** `FaUserShield` from `react-icons/fa6`

**Styling:**
- Position: `fixed top-4 right-4 z-50`
- Background: `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- Text visibility: `hidden sm:inline` (mobile: icon only, desktop: icon + text)
- Dimensions: `px-4 py-3` (touch-friendly ~44-48px)

---

### User Interface Button (Manager Panel)

**Location:** `frontend_mini_app/src/app/manager/page.tsx` (lines 206-214)

**Description:** Button in manager panel header that allows managers to navigate to the user ordering interface.

**Visibility:** Always visible on manager panel (managers only have access to this page)

**Features:**
- Header positioning
- Purple gradient background
- Responsive text (icon only on mobile, icon + text on desktop)
- Smooth hover effect
- Accessibility support (aria-label)

**Implementation:**
```tsx
<button
  onClick={() => router.push("/")}
  className="flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-lg text-white shadow-lg hover:opacity-90 transition-opacity"
  aria-label="Сделать заказ"
>
  <FaCartShopping className="text-lg" />
  <span className="hidden sm:inline text-sm font-medium">Сделать заказ</span>
</button>
```

**Icon:** `FaCartShopping` from `react-icons/fa6`

**Styling:**
- Background: `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- Text visibility: `hidden sm:inline` (mobile: icon only, desktop: icon + text)
- Dimensions: `px-4 py-3` (touch-friendly ~44-48px)

---

## Access Request Components

Components for handling new user access requests.

**Location:** `frontend_mini_app/src/components/AccessRequestForm/`

### AccessRequestForm

**Path:** `frontend_mini_app/src/components/AccessRequestForm/AccessRequestForm.tsx`

**Назначение:** Форма для запроса доступа к системе для незарегистрированных пользователей

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Имя пользователя из Telegram |
| username | string \| null | Yes | Username из Telegram |
| onSubmit | (office: string) => Promise<void> | Yes | Callback отправки формы |
| onSuccess | () => void | Yes | Callback успешной отправки |

**States:**
- Idle: кнопка активна
- Loading: кнопка disabled + spinner
- Error: показ ошибки

**Использование:**
```tsx
<AccessRequestForm
  name="Иван Иванов"
  username="ivan"
  onSubmit={async (office) => {
    await authenticateWithTelegram(initData, office);
  }}
  onSuccess={() => setAuthState("pending")}
/>
```

**Особенности:**
- Три поля формы:
  - Имя (readonly, предзаполнено из Telegram)
  - Username (readonly, опционально, показывается только если есть)
  - Офис (input, обязательное поле)
- Валидация: офис не должен быть пустым
- Loading state при отправке с анимацией spinner
- Обработка и отображение ошибок
- Кнопка disabled во время отправки

**Стилизация:**
- Glassmorphism дизайн: `bg-white/5 backdrop-blur-md border border-white/10`
- Purple gradient для кнопки: `from-[#8B23CB] to-[#A020F0]`
- Background: `bg-[#130F30]`
- Иконки: FaUser, FaBuilding, FaPaperPlane, FaSpinner из react-icons/fa6
- Центрированный layout с максимальной шириной 28rem
- Responsive дизайн с padding и адаптивными размерами

**Form Fields:**
```typescript
// Name (readonly)
<input
  type="text"
  value={name}
  readOnly
  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white"
/>

// Username (readonly, optional)
{username && (
  <input
    type="text"
    value={`@${username}`}
    readOnly
    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-gray-400"
  />
)}

// Office (input, required)
<input
  type="text"
  value={office}
  onChange={(e) => setOffice(e.target.value)}
  placeholder="Например: Офис A, Москва"
  required
  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white"
/>
```

**Submit Button:**
```tsx
<button
  type="submit"
  disabled={isSubmitting}
  className="w-full px-6 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-semibold rounded-lg disabled:opacity-50"
>
  {isSubmitting ? (
    <>
      <FaSpinner className="animate-spin" />
      Отправка...
    </>
  ) : (
    <>
      <FaPaperPlane />
      Отправить запрос
    </>
  )}
</button>
```

**Error Handling:**
```tsx
{error && (
  <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
    <p className="text-red-200 text-sm">{error}</p>
  </div>
)}
```

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

**Multi-State Authentication (TSK-020):**

The authentication flow now supports 6 different states to handle new users, pending access requests, and rejected requests:

```typescript
type AuthState = "loading" | "needs_request" | "success" | "pending" | "rejected" | "error";

const [authState, setAuthState] = useState<AuthState>("loading");
const [telegramUserData, setTelegramUserData] = useState<{
  name: string;
  username: string | null;
} | null>(null);
```

**Authentication States:**

1. **loading** - Initial state while authenticating
2. **needs_request** - New user needs to submit access request
3. **pending** - Access request is pending manager approval
4. **rejected** - Access request was rejected
5. **success** - User authenticated successfully
6. **error** - Authentication error

**Authentication Logic:**

```typescript
useEffect(() => {
  initTelegramWebApp();
}, []);

useEffect(() => {
  const initData = getTelegramInitData();
  if (!initData) {
    setAuthState("error");
    setAuthError("Telegram initData недоступен");
    return;
  }

  // Get Telegram user data for form pre-fill
  const tgUser = getTelegramUser();
  if (tgUser) {
    setTelegramUserData({
      name: `${tgUser.first_name} ${tgUser.last_name || ""}`.trim(),
      username: tgUser.username || null,
    });
  }

  // Try authentication
  authenticateWithTelegram(initData)
    .then((response) => {
      setIsAuthenticated(true);
      setUser(response.user);
      setAuthState("success");
      localStorage.setItem("user", JSON.stringify(response.user));
    })
    .catch(err => {
      const errorMessage = err instanceof Error ? err.message : String(err);

      // Parse 403 errors for access request states
      if (errorMessage.includes("Access request created")) {
        setAuthState("pending");
      } else if (errorMessage.includes("Access request pending")) {
        setAuthState("pending");
      } else if (errorMessage.includes("Access request rejected")) {
        setAuthState("rejected");
      } else {
        setAuthError(errorMessage);
        setAuthState("error");
      }
    });
}, []);
```

**Access Request Handlers:**

```typescript
const handleAccessRequestSubmit = async (office: string) => {
  const initData = getTelegramInitData();
  if (!initData) {
    throw new Error("Telegram initData недоступен");
  }

  await authenticateWithTelegram(initData, office);
};

const handleAccessRequestSuccess = () => {
  setAuthState("pending");
};
```

**UI Rendering by State:**

```typescript
// Loading state
if (authState === "loading") {
  return <LoadingScreen />;
}

// Access request form
if (authState === "needs_request" && telegramUserData) {
  return (
    <AccessRequestForm
      name={telegramUserData.name}
      username={telegramUserData.username}
      onSubmit={handleAccessRequestSubmit}
      onSuccess={handleAccessRequestSuccess}
    />
  );
}

// Pending approval
if (authState === "pending") {
  return <PendingApprovalScreen />;
}

// Request rejected
if (authState === "rejected") {
  return <RejectedScreen />;
}

// Auth error
if (authState === "error") {
  return <ErrorScreen message={authError} />;
}

// Success - show main app
return <MainAppUI />;
```

**Key Features (TSK-010, TSK-020):**
- Managers no longer automatically redirected to `/manager` after authentication
- User object saved to `localStorage` and component state
- Managers can access both `/` (user interface) and `/manager` (admin panel)
- Navigation between interfaces handled by dedicated buttons
- New users see access request form instead of generic error
- Clear UI states for pending and rejected access requests
- Office parameter passed to authentication for new users

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

## Manager Components

Administrative interface components for managers.

**Location:** `frontend_mini_app/src/components/Manager/`

### Manager Panel (/manager)

**Location:** `frontend_mini_app/src/app/manager/page.tsx`

Main admin panel with tab-based navigation. Features:
- Role-based access control (manager only)
- Automatic redirect for non-managers to `/`
- Horizontal scrollable tabs with gradient navigation
- 5 main sections: Users, Cafes, Menu, Requests, Reports
- **Navigation button "Сделать заказ" to switch to user interface** (TSK-010)

**Authentication Flow:**
1. Initialize Telegram WebApp
2. Authenticate via `authenticateWithTelegram()`
3. Check `user.role === "manager"`
4. Redirect non-managers to `/`
5. Store user object in localStorage

**Header:**
- App title: "Панель менеджера"
- Navigation button: "Сделать заказ" → navigates to `/` (user interface)
- Purple gradient styling consistent with design system

**Tabs:**
- Users - User management
- Balances - Corporate balance management
- Cafes - Cafe management
- Menu - Menu and combo management
- Deadlines - Deadline schedule management
- Requests - Cafe connection requests
- Reports - Order summaries and reports

---

### Manager Panel Architecture (TSK-011)

**Tab Structure:**

The manager panel consists of 5 tabs with fully integrated components:

```
┌─────────────────────────────────────────┐
│ Пользователи │ Кафе │ Меню │ Запросы │ Отчёты │
└─────────────────────────────────────────┘
```

**State Management Patterns:**

1. **Props-Based Components** (Users, Cafes)
   - Parent page manages data fetching and state
   - Components receive data via props
   - Callbacks for mutations passed from parent
   - Parent controls form visibility

2. **Self-Contained Components** (Menu, Requests, Reports)
   - Components manage their own data fetching
   - Internal state management
   - No props required from parent
   - Can be dropped directly into layout

**Tab Implementation:**

#### 1. Users Tab

**Components:** `UserList` + `UserForm`

**State Management:**
```typescript
// Parent (manager/page.tsx) manages:
const [showUserForm, setShowUserForm] = useState(false);
const { data: users, error, isLoading } = useUsers();
const { createUser } = useCreateUser();
const { updateAccess } = useUpdateUserAccess();
const { deleteUser } = useDeleteUser();
```

**Integration Pattern:**
- Toggle button "Добавить пользователя" controls form visibility
- UserForm receives callback for submission with data
- UserList receives data and callbacks as props
- Parent wraps callbacks in try/catch for error handling

**Props:**
```typescript
// UserList
interface UserListProps {
  users: User[] | undefined;
  isLoading: boolean;
  error: Error | undefined;
  onToggleAccess: (tgid: number, newStatus: boolean) => Promise<void>;
  onDelete: (tgid: number) => Promise<void>;
}

// UserForm
interface UserFormProps {
  onSubmit: (data: { tgid: number; name: string; office: string }) => Promise<void>;
  onCancel: () => void;
}
```

#### 2. Cafes Tab

**Components:** `CafeList` + `CafeForm`

**State Management:**
```typescript
// Parent manages:
const [showCafeForm, setShowCafeForm] = useState(false);
const [editingCafe, setEditingCafe] = useState<Cafe | null>(null);
```

**Integration Pattern:**
- CafeList fetches data internally via `useCafes(false)`
- CafeForm handles API calls internally (createCafe/updateCafe)
- Parent only manages form visibility and edit mode
- Form has dual mode: create (showCafeForm=true) / edit (editingCafe!=null)

**Props:**
```typescript
// CafeList
interface CafeListProps {
  onEdit?: (cafe: Cafe) => void;
}

// CafeForm
interface CafeFormProps {
  mode: "create" | "edit";
  initialData?: Cafe;
  onSubmit: () => void;  // No parameters - form handles API internally
  onCancel: () => void;
}
```

**Note:** CafeForm differs from UserForm - it calls API internally and only notifies parent of completion via `onSubmit()`.

#### 3. Menu Tab

**Component:** `MenuManager`

**Integration Pattern:**
- Completely self-contained
- No props required
- Manages cafe selection, combo/menu CRUD internally
- Drop-in component: `<MenuManager />`

**Internal Features:**
- Cafe selector dropdown
- Combo sets section with ComboForm
- Menu items section with MenuItemForm
- Category grouping
- Toggle availability
- Edit/delete actions

#### 4. Requests Tab

**Component:** `RequestsList`

**Integration Pattern:**
- Self-contained
- No props required
- Fetches data via `useCafeRequests()` internally
- Drop-in component: `<RequestsList />`

**Internal Features:**
- Display pending cafe requests
- Approve/reject actions
- Auto-refresh after mutations

#### 5. Reports Tab

**Component:** `ReportsList`

**Integration Pattern:**
- Self-contained
- No props required
- Fetches data via `useSummaries()` internally
- Drop-in component: `<ReportsList />`

**Internal Features:**
- Create summary form (cafe + date)
- Display existing summaries
- Delete summaries
- Summary details display

**API Hooks Used:**

```typescript
// Users Tab
useUsers()
useCreateUser()
useUpdateUserAccess()
useDeleteUser()

// Cafes Tab (only in CafeForm component, not in page.tsx)
useCafes(false)  // inside CafeList
useCreateCafe()  // inside CafeForm
useUpdateCafe()  // inside CafeForm
useUpdateCafeStatus()  // inside CafeList
useDeleteCafe()  // inside CafeList

// Menu Tab (all inside MenuManager)
useCombos(cafeId)
useMenu(cafeId, category?)
useCreateCombo(), useUpdateCombo(), useDeleteCombo()
useCreateMenuItem(), useUpdateMenuItem(), useDeleteMenuItem()

// Requests Tab (inside RequestsList)
useCafeRequests()
useApproveCafeRequest()
useRejectCafeRequest()

// Reports Tab (inside ReportsList)
useSummaries()
useCreateSummary()
useDeleteSummary()
```

**Error Handling:**

All callbacks wrapped in try/catch:
```typescript
onSubmit={async (data) => {
  try {
    await createUser(data);
    setShowUserForm(false);
  } catch (err) {
    console.error("Failed to create user:", err);
  }
}}
```

**UI Consistency:**

All components use the same design system:
- Background: `bg-white/5 backdrop-blur-md`
- Borders: `border border-white/10`
- Buttons: `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- Spacing: `space-y-6` between sections
- Loading states: skeleton placeholders
- Error states: red banners
- Empty states: gray text messages

### UserList / UserForm

**Components:**
- `UserList.tsx` - Display and manage users
- `UserForm.tsx` - Create new users

**Features:**
- List all users with status badges (Active/Blocked)
- Toggle user access (block/unblock)
- Delete users with confirmation
- Create new users (name, telegram ID, office, role)
- Role display (Manager/Employee)

**Hooks:**
- `useUsers()` - Fetch user list
- `useCreateUser()` - Create new user
- `useUpdateUserAccess()` - Toggle user access
- `useDeleteUser()` - Delete user

**UI States:**
- Loading - Skeleton placeholders (3 items)
- Error - Red error banner
- Empty - "No users" message
- Loaded - User cards with action buttons

### CafeList / CafeForm

**Components:**
- `CafeList.tsx` - Display and manage cafes
- `CafeForm.tsx` - Create/edit cafes

**Features:**
- List all cafes with status indicators
- Create new cafes (name, description)
- Edit existing cafes
- Toggle cafe status (active/inactive)
- Delete cafes with confirmation

**Hooks:**
- `useCafes(activeOnly: boolean)` - Fetch cafes
- `useCreateCafe()` - Create cafe
- `useUpdateCafe()` - Update cafe details
- `useUpdateCafeStatus()` - Toggle active status
- `useDeleteCafe()` - Delete cafe

**Form Fields:**
- Name (required)
- Description (optional)

### MenuManager / ComboForm / MenuItemForm

**Components:**
- `MenuManager.tsx` - Main menu management interface
- `ComboForm.tsx` - Create/edit combo sets
- `MenuItemForm.tsx` - Create/edit menu items

**MenuManager Features:**
- Cafe selector dropdown
- Two sections: Combo sets and Menu items
- Category grouping (Soup, Salad, Main, Extra)
- Toggle availability for items and combos
- Edit and delete functionality
- Price display

**ComboForm:**
- Name input
- Category multi-select (soup, salad, main, extra)
- Price input
- Create/Edit modes

**MenuItemForm:**
- Name input
- Description input (optional)
- Category select
- Price input (optional for combo items)
- Create/Edit modes

**Hooks:**
- `useCreateCombo()` - Create combo set
- `useUpdateCombo()` - Update combo
- `useDeleteCombo()` - Delete combo
- `useCreateMenuItem()` - Create menu item
- `useUpdateMenuItem()` - Update menu item
- `useDeleteMenuItem()` - Delete menu item

**Category Labels Mapping:**
```typescript
{
  soup: "Первое",
  salad: "Салат",
  main: "Второе",
  extra: "Дополнительно"
}
```

### RequestsList

**Component:** `RequestsList.tsx`

**Features:**
- Display cafe connection requests
- Approve requests - converts request to active cafe
- Reject requests with confirmation
- Request details: cafe name, description, requester

**Hooks:**
- `useCafeRequests()` - Fetch pending requests
- `useApproveCafeRequest()` - Approve request
- `useRejectCafeRequest()` - Reject request

**Request States:**
- Pending - Awaiting manager action
- Approved - Converted to active cafe
- Rejected - Request denied

### ReportsList

**Component:** `ReportsList.tsx`

**Features:**
- View order summaries by cafe and date
- Create new summaries
- Delete summaries with confirmation
- Summary details display

**Hooks:**
- `useSummaries()` - Fetch all summaries
- `useCreateSummary()` - Create new summary
- `useDeleteSummary()` - Delete summary

**Summary Creation:**
- Cafe selector
- Date picker
- Generates report for selected cafe and date

---

### BalanceManager

**Component:** `BalanceManager.tsx`

**Location:** `frontend_mini_app/src/components/Manager/BalanceManager.tsx`

**Назначение:** Управление корпоративными балансами пользователей (недельные лимиты расходов)

**Access:** Manager only (via manager panel `/manager` → tab "Балансы")

**Features:**

1. **User List Display:**
   - Отображает всех пользователей с балансами
   - Для каждого пользователя показывает:
     - Имя, офис, Telegram ID
     - Недельный лимит (weekly_limit)
     - Потрачено на этой неделе (spent_this_week)
     - Остаток (remaining)
   - Кнопка редактирования для каждого пользователя

2. **Edit Modal:**
   - Input поле для установки нового лимита
   - Кнопка "Сохранить" - устанавливает новый лимит
   - Кнопка "Снять лимит" - устанавливает weekly_limit = null
   - Validation: только положительные числа
   - Confirm dialog перед снятием лимита

3. **Lazy Loading:**
   - Использует `UserBalanceRow` компонент для каждого пользователя
   - Каждый row загружает свой баланс через `useUserBalance(user.tgid)`
   - SWR кэширование смягчает N+1 запросы

4. **States:**
   - Loading: Skeleton placeholders (3 items)
   - Error: Red error banner
   - Empty: "Нет пользователей" message
   - Saving: Disabled buttons с spinner

**Hooks:**
```typescript
const { data: users, isLoading, error } = useUsers();
const { data: balance } = useUserBalance(user.tgid); // в UserBalanceRow
const { updateLimit } = useUpdateBalanceLimit();
```

**Usage:**
```tsx
// В manager/page.tsx
{activeTab === "balances" && (
  <div className="text-white">
    <BalanceManager />
  </div>
)}
```

**Edit Limit Examples:**
```typescript
// Set limit to 5000 руб
await updateLimit(user.tgid, 5000.00);

// Remove limit
await updateLimit(user.tgid, null);

// Update limit to 3500 руб
await updateLimit(user.tgid, 3500.00);
```

**UserBalanceRow Component:**
- Sub-component внутри BalanceManager
- Lazy загружает баланс для каждого пользователя
- Отображает user info + balance info
- Кнопка редактирования открывает modal

**Validation:**
```typescript
const limitValue = newLimit.trim() === "" ? null : parseFloat(newLimit);

if (limitValue !== null && (isNaN(limitValue) || limitValue < 0)) {
  alert("Введите корректное положительное число");
  return;
}
```

**Confirmation Dialog:**
```typescript
if (!confirm(`Снять лимит для пользователя ${editingUser.name}?`)) {
  return;
}
```

**Дизайн:**
- Таблица/список с semi-transparent rows
- Purple gradient кнопки редактирования
- Modal overlay с темным фоном
- Decimal formatting `.toFixed(2)` для всех сумм
- Loading states во время операций
- Disabled buttons во время saving

**Tab Integration:**

В `manager/page.tsx`:

```typescript
const tabs: { id: TabId; name: string; icon: JSX.Element }[] = [
  { id: "users", name: "Пользователи", icon: <FaUser /> },
  { id: "balances", name: "Балансы", icon: <FaWallet /> },  // New tab
  { id: "cafes", name: "Кафе", icon: <FaStore /> },
  { id: "menu", name: "Меню", icon: <FaUtensils /> },
  { id: "requests", name: "Запросы", icon: <FaEnvelope /> },
  { id: "reports", name: "Отчёты", icon: <FaFileAlt /> },
];

// Render
{activeTab === "balances" && <BalanceManager />}
```

**Trade-offs:**
- N+1 запросов для балансов (нет batch endpoint `/users/balances`)
- Mitigation: SWR кэширование, lazy loading через UserBalanceRow
- Alternative: создать batch endpoint на backend (future improvement)

---

### DeadlineSchedule

**Component:** `DeadlineSchedule.tsx`

**Location:** `frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx`

**Назначение:** Управление расписанием дедлайнов заказов для каждого кафе

**Access:** Manager only (via manager panel `/manager` → tab "Расписание")

**Features:**

1. **Cafe Selection:**
   - Dropdown для выбора кафе
   - Загружает доступные кафе через `useCafes(true, false)`
   - При смене кафе очищает сообщения и перезагружает расписание

2. **Schedule Configuration:**
   - Форма с 7 днями недели (Понедельник - Воскресенье)
   - Для каждого дня:
     - Checkbox `is_enabled` — включить/выключить приём заказов
     - Input time `deadline_time` — время дедлайна (формат HH:MM)
     - Input number `advance_days` — за сколько дней заранее можно заказать (0-6)
   - Условный рендеринг полей — время и дни заранее показываются только для enabled дней

3. **Data Handling:**
   - Загружает существующее расписание через `useDeadlineSchedule(cafeId)`
   - Инициализирует дефолтными значениями если расписания нет
   - Дефолты: все дни `is_enabled: false`, время `10:00`, `advance_days: 0`
   - Обновляет расписание через `useUpdateDeadlineSchedule()`

4. **States:**
   - Loading: Spinner с сообщением "Загрузка..."
   - Empty (no cafe selected): "Выберите кафе для настройки расписания"
   - Success: Green banner с auto-hide через 3 секунды
   - Error: Red banner с сообщением об ошибке
   - Saving: Disabled form с spinner на кнопке

**Hooks:**
```typescript
const { data: cafes } = useCafes(true, false);
const { data: scheduleData, isLoading } = useDeadlineSchedule(selectedCafeId);
const { updateSchedule, isLoading: isUpdating } = useUpdateDeadlineSchedule();
```

**Usage:**
```tsx
// В manager/page.tsx
{activeTab === "deadlines" && (
  <div className="text-white">
    <DeadlineSchedule />
  </div>
)}
```

**Data Types:**
```typescript
// DeadlineItem (один день в расписании)
interface DeadlineItem {
  weekday: number;          // 0=Пн, 1=Вт, ..., 6=Вс
  deadline_time: string;    // "10:00"
  is_enabled: boolean;
  advance_days: number;     // 0-6
}

// DeadlineScheduleResponse (ответ API)
interface DeadlineScheduleResponse {
  cafe_id: number;
  schedule: DeadlineItem[];
}
```

**Form State Management:**
```typescript
const [formData, setFormData] = useState<DeadlineItem[]>([]);

// Initialize from API or defaults
useEffect(() => {
  if (scheduleData?.schedule) {
    setFormData(scheduleData.schedule);
  } else if (selectedCafeId) {
    setFormData(
      Array.from({ length: 7 }, (_, i) => ({
        weekday: i,
        deadline_time: "10:00",
        is_enabled: false,
        advance_days: 0,
      }))
    );
  }
}, [scheduleData, selectedCafeId]);

// Update field
const handleFieldChange = (
  weekday: number,
  field: keyof DeadlineItem,
  value: string | boolean | number
) => {
  setFormData((prev) =>
    prev.map((item) =>
      item.weekday === weekday ? { ...item, [field]: value } : item
    )
  );
};
```

**Submit Logic:**
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  if (!selectedCafeId) {
    setErrorMessage("Пожалуйста, выберите кафе");
    return;
  }

  try {
    await updateSchedule(selectedCafeId, formData);
    setSuccessMessage("Расписание успешно обновлено");
    setTimeout(() => setSuccessMessage(null), 3000);
  } catch (err) {
    setErrorMessage(err instanceof Error ? err.message : "Не удалось обновить расписание");
  }
};
```

**Дизайн:**
- Glass effect: `bg-white/5 backdrop-blur-md border border-white/10`
- Inputs: `bg-white/10 border border-white/20`
- Success banner: `bg-green-500/20 border border-green-500/30 text-green-400`
- Error banner: `bg-red-500/20 border border-red-500/30 text-red-400`
- Submit button: gradient `from-[#8B23CB] to-[#A020F0]`
- Checkbox styling: purple accent color
- Responsive grid: `grid-cols-1 md:grid-cols-2` для полей времени и дней

**Layout:**
```
┌─────────────────────────────────┐
│ Расписание дедлайнов            │
├─────────────────────────────────┤
│ [Dropdown: Выберите кафе     ▼] │
├─────────────────────────────────┤
│ ☑ Понедельник                   │
│   Время: [10:00] Дней: [1]      │
├─────────────────────────────────┤
│ ☑ Вторник                       │
│   Время: [10:00] Дней: [1]      │
├─────────────────────────────────┤
│ ☐ Среда                         │
├─────────────────────────────────┤
│ ...                             │
├─────────────────────────────────┤
│ [Сохранить расписание]          │
└─────────────────────────────────┘
```

**Tab Integration:**

В `manager/page.tsx`:

```typescript
import { FaCalendar } from "react-icons/fa6";
import DeadlineSchedule from "@/components/Manager/DeadlineSchedule";

const tabs = [
  { id: "users", name: "Пользователи", icon: <FaUser /> },
  { id: "balances", name: "Балансы", icon: <FaWallet /> },
  { id: "cafes", name: "Кафе", icon: <FaStore /> },
  { id: "menu", name: "Меню", icon: <FaUtensils /> },
  { id: "deadlines", name: "Расписание", icon: <FaCalendar /> },
  { id: "requests", name: "Запросы", icon: <FaEnvelope /> },
  { id: "reports", name: "Отчёты", icon: <FaFileAlt /> },
];

// Render
{activeTab === "deadlines" && (
  <div className="text-white">
    <DeadlineSchedule />
  </div>
)}
```

**Backend API:**
- `GET /cafes/{cafe_id}/deadlines` — загрузка расписания
- `PUT /cafes/{cafe_id}/deadlines` — обновление расписания
  - Body: `{ schedule: DeadlineItem[] }`
  - Response: `{ cafe_id: number, schedule: DeadlineItem[] }`

**Weekday Names:**
```typescript
const WEEKDAY_NAMES = [
  "Понедельник",   // 0
  "Вторник",       // 1
  "Среда",         // 2
  "Четверг",       // 3
  "Пятница",       // 4
  "Суббота",       // 5
  "Воскресенье",   // 6
];
```

**Validation:**
- Cafe selection required before submit
- Advance days range: 0-6
- Time format: HH:MM (browser native time input)
- All validations display error banner

**Auto-hide Success:**
```typescript
setSuccessMessage("Расписание успешно обновлено");
setTimeout(() => setSuccessMessage(null), 3000);
```

### Common Manager Component Patterns

**Loading States:**
- Skeleton placeholders during data fetch
- Spinner icons for actions in progress
- Disabled buttons during operations

**Error Handling:**
- Red error banners for fetch errors
- Alert dialogs for operation errors
- Console error logging

**Empty States:**
- Centered gray text messages
- Semi-transparent card backgrounds

**Action Buttons:**
- Purple gradient for primary actions (Create, Add)
- Red tones for destructive actions (Delete, Block)
- Green tones for positive actions (Activate, Approve)
- Toggle icons for availability (FaToggleOn/FaToggleOff)

**Confirmation Dialogs:**
- Browser confirm() for destructive actions
- Custom messages for context

**Data Revalidation:**
- SWR `mutate()` after successful operations
- Automatic UI refresh on data changes

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

### User Endpoints

| Endpoint | Hook | Purpose |
|----------|------|---------|
| `POST /auth/telegram` | `authenticateWithTelegram()` | Get JWT token |
| `GET /cafes?active_only=true` | `useCafes(true)` | Fetch cafe list |
| `GET /cafes/{id}/combos` | `useCombos(cafeId)` | Fetch combos for cafe |
| `GET /cafes/{id}/menu` | `useMenu(cafeId)` | Fetch menu items |
| `GET /cafes/{id}/menu?category=extra` | `useMenu(cafeId, "extra")` | Fetch extras |
| `POST /orders` | `useCreateOrder()` | Create new order |
| `GET /users/{tgid}/recommendations` | `useUserRecommendations(tgid)` | Fetch AI recommendations |
| `GET /users/{tgid}/balance` | `useUserBalance(tgid)` | Fetch user balance |

### Manager Endpoints

**User Management:**

| Endpoint | Hook | Purpose |
|----------|------|---------|
| `GET /users` | `useUsers()` | Fetch all users |
| `POST /users` | `useCreateUser()` | Create new user |
| `PATCH /users/{tgid}/access` | `useUpdateUserAccess()` | Toggle user access |
| `DELETE /users/{tgid}` | `useDeleteUser()` | Delete user |
| `PATCH /users/{tgid}/balance/limit` | `useUpdateBalanceLimit()` | Update weekly limit |

**Cafe Management:**

| Endpoint | Hook | Purpose |
|----------|------|---------|
| `GET /cafes` | `useCafes(false)` | Fetch all cafes (including inactive) |
| `POST /cafes` | `useCreateCafe()` | Create new cafe |
| `PATCH /cafes/{id}` | `useUpdateCafe()` | Update cafe details |
| `PATCH /cafes/{id}/status` | `useUpdateCafeStatus()` | Toggle cafe status |
| `DELETE /cafes/{id}` | `useDeleteCafe()` | Delete cafe |

**Menu Management:**

| Endpoint | Hook | Purpose |
|----------|------|---------|
| `POST /cafes/{id}/combos` | `useCreateCombo()` | Create combo set |
| `PATCH /cafes/{id}/combos/{combo_id}` | `useUpdateCombo()` | Update combo |
| `DELETE /cafes/{id}/combos/{combo_id}` | `useDeleteCombo()` | Delete combo |
| `POST /cafes/{id}/menu` | `useCreateMenuItem()` | Create menu item |
| `PATCH /cafes/{id}/menu/{item_id}` | `useUpdateMenuItem()` | Update menu item |
| `DELETE /cafes/{id}/menu/{item_id}` | `useDeleteMenuItem()` | Delete menu item |

**Deadline Schedule:**

| Endpoint | Hook | Purpose |
|----------|------|---------|
| `GET /cafes/{cafe_id}/deadlines` | `useDeadlineSchedule(cafeId)` | Fetch deadline schedule |
| `PUT /cafes/{cafe_id}/deadlines` | `useUpdateDeadlineSchedule()` | Update deadline schedule |

**Cafe Requests:**

| Endpoint | Hook | Purpose |
|----------|------|---------|
| `GET /cafe-requests` | `useCafeRequests()` | Fetch pending requests |
| `POST /cafe-requests/{id}/approve` | `useApproveCafeRequest()` | Approve request |
| `POST /cafe-requests/{id}/reject` | `useRejectCafeRequest()` | Reject request |

**Reports:**

| Endpoint | Hook | Purpose |
|----------|------|---------|
| `GET /summaries` | `useSummaries()` | Fetch all summaries |
| `POST /summaries` | `useCreateSummary()` | Create summary |
| `DELETE /summaries/{id}` | `useDeleteSummary()` | Delete summary |

---

## Notes

- **SSR Safety:** All API and Telegram functions check for `window` object
- **Development Mode:** App works outside Telegram with graceful degradation
- **Caching:** SWR automatically caches all GET requests
- **Token Persistence:** JWT token stored in localStorage
- **Error Handling:** All errors displayed to user via alerts
- **Validation:** Order submission disabled until all combo categories filled
- **Order date:** выбирается по доступности (сначала сегодня, иначе ближайший доступный день), не жёстко `today + 1`.
