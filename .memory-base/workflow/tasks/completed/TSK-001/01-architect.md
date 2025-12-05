---
agent: architect
task_id: TSK-001
status: completed
next: coder
created_at: 2025-12-05T23:30:00
---

# Архитектурное решение: Интеграция frontend с API

## 1. Обзор задачи

Текущий frontend (Telegram Mini App) использует захардкоженные данные. Необходимо интегрировать его с backend API, переделав UI под систему комбо-заказов вместо традиционного выбора блюд по категориям.

## 2. Анализ текущего состояния

### 2.1 Текущая архитектура UI

```
page.tsx (Главная страница)
├── State: activeCafeId, activeCategoryId, cart
├── CafeSelector — горизонтальный выбор кафе
├── CategorySelector — выбор категории блюд (удалить)
├── MenuSection — список блюд с добавлением в корзину (переделать)
└── CartSummary + CheckoutButton — итоговая корзина (заменить)
```

### 2.2 Целевая архитектура UI (комбо-система)

```
page.tsx (Главная страница)
├── State:
│   ├── selectedCafe: Cafe | null
│   ├── selectedComboId: number | null
│   ├── comboItems: { [category: string]: number }  // category -> menu_item_id
│   └── extrasCart: { [itemId: number]: number }    // item_id -> quantity
├── CafeSelector — выбор кафе (сохранить)
├── ComboSelector — выбор комбо-набора (создать)
├── MenuSection (x N) — для каждой категории комбо (переделать под radio)
├── ExtrasSection — дополнительные товары (создать)
└── OrderSummary + CheckoutButton — итог заказа (создать)
```

## 3. Архитектурное решение

### 3.1 Слой API клиента

Создаём три уровня абстракции для работы с API:

```
src/lib/
├── api/
│   ├── client.ts       # Базовый fetch клиент с JWT авторизацией
│   ├── types.ts        # TypeScript типы из API спецификации
│   └── hooks.ts        # React hooks для запросов (SWR)
└── telegram/
    └── webapp.ts       # Обёртка над @twa-dev/sdk
```

#### 3.1.1 client.ts — Fetch клиент

**Обязанности:**
- Базовый метод `apiRequest<T>(endpoint, options)` для всех запросов
- Добавление JWT токена в заголовок `Authorization: Bearer {token}`
- Обработка HTTP статусов (401, 403, 404, 500)
- Retry логика для 5xx ошибок
- Хранение токена в localStorage

**Пример API:**
```typescript
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T>

export async function authenticateWithTelegram(
  initData: string
): Promise<{ access_token: string; user: User }>
```

#### 3.1.2 types.ts — TypeScript типы

Определяем типы для всех сущностей API:

```typescript
// Entities
export interface User { tgid: number; name: string; office: string; ... }
export interface Cafe { id: number; name: string; is_active: boolean; ... }
export interface Combo { id: number; cafe_id: number; name: string; categories: string[]; price: number; ... }
export interface MenuItem { id: number; cafe_id: number; name: string; category: string; price: number | null; ... }
export interface Order { id: number; user_tgid: number; cafe_id: number; combo: OrderCombo; extras: OrderExtra[]; ... }
export interface OrderCombo { combo_id: number; items: OrderComboItem[]; ... }
export interface OrderExtra { menu_item_id: number; quantity: number; ... }

// Request payloads
export interface CreateOrderRequest { cafe_id: number; order_date: string; combo_id: number; combo_items: { category: string; menu_item_id: number }[]; extras?: { menu_item_id: number; quantity: number }[]; ... }

// Response wrappers
export interface ListResponse<T> { items: T[]; total?: number }
```

#### 3.1.3 hooks.ts — SWR hooks

Создаём React hooks для каждого API endpoint с использованием SWR:

**Преимущества SWR:**
- Автоматический кэш
- Revalidation при фокусе окна
- Retry при ошибках
- Optimistic updates
- TypeScript типизация

**Хуки для frontend:**
```typescript
export function useCafes(activeOnly = true): SWRResponse<Cafe[]>
export function useCombos(cafeId: number | null): SWRResponse<Combo[]>
export function useMenu(cafeId: number | null, category?: string): SWRResponse<MenuItem[]>
export function useCreateOrder(): { createOrder: (data: CreateOrderRequest) => Promise<Order>; isLoading: boolean }
```

#### 3.1.4 webapp.ts — Telegram WebApp SDK

Инкапсулируем логику Telegram WebApp:

```typescript
export function initTelegramWebApp(): void
export function getTelegramInitData(): string | null
export function closeTelegramWebApp(): void
export function showMainButton(text: string, onClick: () => void): void
export function hideMainButton(): void
```

### 3.2 Компоненты UI

#### 3.2.1 ComboSelector (новый компонент)

**Путь:** `src/components/ComboSelector/ComboSelector.tsx`

**Props:**
```typescript
interface ComboSelectorProps {
  combos: Combo[];
  selectedComboId: number | null;
  onComboSelect: (id: number) => void;
}
```

**Функционал:**
- Получает список комбо через пропс (загружаются в page.tsx)
- Отображает карточки с названием и ценой
- Подсвечивает выбранное комбо градиентом
- При клике вызывает `onComboSelect(id)`

**Layout:**
```
[Карточка комбо]
  Салат + Суп
  450 ₽
```

#### 3.2.2 MenuSection (переделка существующего)

**Путь:** `src/components/Menu/MenuSection.tsx`

**Изменения:**
- Вместо списка с кнопками `+`/`-` → radio selection (одно блюдо)
- Props меняются:

```typescript
// Было
interface MenuSectionProps {
  dishes: Dish[];
  cart: { [id: number]: number };
  addToCart: (id: number) => void;
  removeFromCart: (id: number) => void;
}

// Стало
interface MenuSectionProps {
  category: string;              // "soup" | "salad" | "main"
  categoryLabel: string;         // "Супы", "Салаты", "Основные блюда"
  items: MenuItem[];
  selectedItemId: number | null;
  onItemSelect: (itemId: number) => void;
}
```

**Layout:**
```
Супы
  ◯ Борщ украинский
  ● Куриный бульон  ← выбрано
  ◯ Солянка сборная
```

#### 3.2.3 ExtrasSection (новый компонент)

**Путь:** `src/components/ExtrasSection/ExtrasSection.tsx`

**Props:**
```typescript
interface ExtrasSectionProps {
  extras: MenuItem[];                      // category = "extra"
  cart: { [itemId: number]: number };
  addToCart: (itemId: number) => void;
  removeFromCart: (itemId: number) => void;
}
```

**Функционал:**
- Показывает дополнительные товары (category="extra")
- Карточка: название, описание, цена
- Кнопка "+ Добавить" или счётчик `[-] [qty] [+]`

**Layout:**
```
[Карточка extra]
  Фокачча с пряным маслом
  60 г.
  50 ₽
  [+ Добавить]
```

#### 3.2.4 OrderSummary (замена CartSummary)

**Путь:** `src/components/OrderSummary/OrderSummary.tsx`

**Props:**
```typescript
interface OrderSummaryProps {
  combo: { name: string; price: number } | null;
  comboItems: { category: string; itemName: string }[];
  extras: { name: string; quantity: number; subtotal: number }[];
  totalPrice: number;
}
```

**Функционал:**
- Показывает выбранное комбо с ценой
- Список выбранных блюд по категориям
- Список дополнительных товаров с количеством
- Итоговая сумма

**Layout:**
```
Салат + Суп + Основное — 550 ₽
  Салат: Цезарь с курицей
  Суп: Борщ украинский
  Основное: Котлета с пюре

Дополнительно:
  Фокачча x1 — 50 ₽

Итого: 600 ₽
```

### 3.3 Главная страница (page.tsx)

#### 3.3.1 State

```typescript
const [selectedCafe, setSelectedCafe] = useState<Cafe | null>(null);
const [selectedComboId, setSelectedComboId] = useState<number | null>(null);
const [comboItems, setComboItems] = useState<{ [category: string]: number }>({});
const [extrasCart, setExtrasCart] = useState<{ [itemId: number]: number }>({});
const [isAuthenticated, setIsAuthenticated] = useState(false);
const [authToken, setAuthToken] = useState<string | null>(null);
```

#### 3.3.2 Data Fetching (SWR hooks)

```typescript
const { data: cafes } = useCafes(true);
const { data: combos } = useCombos(selectedCafe?.id ?? null);
const { data: menuItems } = useMenu(selectedCafe?.id ?? null);
const { data: extras } = useMenu(selectedCafe?.id ?? null, "extra");
```

#### 3.3.3 Computed Values

```typescript
const selectedCombo = combos?.find(c => c.id === selectedComboId) ?? null;
const comboPrice = selectedCombo?.price ?? 0;

const extrasTotal = Object.entries(extrasCart).reduce((sum, [id, qty]) => {
  const extra = extras?.find(e => e.id === +id);
  return sum + (extra?.price ?? 0) * qty;
}, 0);

const totalPrice = comboPrice + extrasTotal;

// Валидация: все категории комбо заполнены
const isOrderComplete = selectedCombo &&
  selectedCombo.categories.every(cat => comboItems[cat]);
```

#### 3.3.4 Flow авторизации

```typescript
useEffect(() => {
  const initData = getTelegramInitData();
  if (!initData) {
    console.error("Not in Telegram WebApp");
    return;
  }

  authenticateWithTelegram(initData)
    .then(({ access_token, user }) => {
      setAuthToken(access_token);
      setIsAuthenticated(true);
      localStorage.setItem("jwt_token", access_token);
    })
    .catch(err => {
      console.error("Auth failed:", err);
    });
}, []);
```

#### 3.3.5 Обработка отправки заказа

```typescript
const { createOrder, isLoading } = useCreateOrder();

const handleCheckout = async () => {
  if (!isOrderComplete || !selectedCafe || !selectedCombo) return;

  const orderData: CreateOrderRequest = {
    cafe_id: selectedCafe.id,
    order_date: new Date().toISOString().split("T")[0], // YYYY-MM-DD
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
    // Success feedback
    alert(`Заказ №${order.id} оформлен!`);
    closeTelegramWebApp();
  } catch (err) {
    // Error handling
    alert(`Ошибка: ${err.message}`);
  }
};
```

## 4. Декомпозиция на подзадачи для Coder

### Подзадача 1: Инфраструктура API клиента (можно параллельно)

**Файлы для создания:**
- `frontend_mini_app/src/lib/api/client.ts`
- `frontend_mini_app/src/lib/api/types.ts`
- `frontend_mini_app/src/lib/api/hooks.ts`

**Описание:**
1. Создать `client.ts` с функцией `apiRequest<T>(endpoint, options)`
2. Добавить функцию `authenticateWithTelegram(initData)` для `/auth/telegram`
3. Добавить хранение JWT токена в localStorage
4. Создать `types.ts` с TypeScript интерфейсами всех сущностей API
5. Создать `hooks.ts` с SWR хуками: `useCafes`, `useCombos`, `useMenu`, `useCreateOrder`

**Зависимости:**
- Установить `swr` через npm: `npm install swr`

**Приоритет:** Высокий (блокирует остальные подзадачи)

---

### Подзадача 2: Telegram WebApp SDK интеграция (можно параллельно)

**Файлы для создания:**
- `frontend_mini_app/src/lib/telegram/webapp.ts`

**Описание:**
1. Создать обёртку над `@twa-dev/sdk`
2. Реализовать функции: `initTelegramWebApp()`, `getTelegramInitData()`, `closeTelegramWebApp()`, `showMainButton()`, `hideMainButton()`
3. Обработать случай запуска вне Telegram (для разработки)

**Зависимости:**
- Пакет `@twa-dev/sdk` уже установлен

**Приоритет:** Высокий (нужен для авторизации)

---

### Подзадача 3: ComboSelector компонент (можно параллельно с 4, 5, 6)

**Файлы для создания:**
- `frontend_mini_app/src/components/ComboSelector/ComboSelector.tsx`

**Описание:**
1. Создать компонент с пропсами: `combos`, `selectedComboId`, `onComboSelect`
2. Отобразить карточки комбо с названием и ценой
3. Подсветить выбранное комбо градиентом (как в CafeSelector)
4. Использовать Tailwind стили в стиле проекта

**Зависимости:**
- `types.ts` (для типа `Combo`)

**Приоритет:** Средний

---

### Подзадача 4: MenuSection переделка (можно параллельно с 3, 5, 6)

**Файлы для изменения:**
- `frontend_mini_app/src/components/Menu/MenuSection.tsx`

**Описание:**
1. Изменить интерфейс пропсов на `{ category, categoryLabel, items, selectedItemId, onItemSelect }`
2. Заменить кнопки `+`/`-` на radio selection
3. Показывать заголовок категории (`categoryLabel`)
4. Подсветить выбранное блюдо

**Зависимости:**
- `types.ts` (для типа `MenuItem`)

**Приоритет:** Средний

---

### Подзадача 5: ExtrasSection компонент (можно параллельно с 3, 4, 6)

**Файлы для создания:**
- `frontend_mini_app/src/components/ExtrasSection/ExtrasSection.tsx`

**Описание:**
1. Создать компонент с пропсами: `extras`, `cart`, `addToCart`, `removeFromCart`
2. Отобразить карточки дополнительных товаров
3. Показать название, описание, цену
4. Кнопка "+ Добавить" или счётчик `[-] [qty] [+]`

**Зависимости:**
- `types.ts` (для типа `MenuItem`)

**Приоритет:** Средний

---

### Подзадача 6: OrderSummary компонент (можно параллельно с 3, 4, 5)

**Файлы для создания:**
- `frontend_mini_app/src/components/OrderSummary/OrderSummary.tsx`

**Описание:**
1. Создать компонент с пропсами: `combo`, `comboItems`, `extras`, `totalPrice`
2. Показать информацию о комбо и выбранных блюдах
3. Показать дополнительные товары с количеством
4. Показать итоговую сумму
5. Сохранить стиль существующего `CartSummary`

**Зависимости:**
- Нет (использует простые пропсы)

**Приоритет:** Средний

---

### Подзадача 7: Главная страница интеграция

**Файлы для изменения:**
- `frontend_mini_app/src/app/page.tsx`

**Описание:**
1. Заменить state на новый: `selectedCafe`, `selectedComboId`, `comboItems`, `extrasCart`
2. Добавить авторизацию через Telegram WebApp в `useEffect`
3. Использовать SWR хуки для загрузки данных: `useCafes`, `useCombos`, `useMenu`
4. Заменить `CategorySelector` на `ComboSelector`
5. Переделать отображение `MenuSection` для каждой категории выбранного комбо
6. Добавить `ExtrasSection`
7. Заменить `CartSummary` на `OrderSummary`
8. Реализовать `handleCheckout` с использованием `useCreateOrder`
9. Добавить валидацию: `isOrderComplete`
10. Удалить импорт и использование `CategorySelector`

**Зависимости:**
- Подзадачи 1, 2, 3, 4, 5, 6 должны быть завершены

**Приоритет:** Низкий (выполняется последней)

---

### Подзадача 8: Удаление устаревших компонентов

**Файлы для удаления:**
- `frontend_mini_app/src/components/CategorySelector/CategorySelector.tsx`
- `frontend_mini_app/src/components/Cart/CartSummary.tsx`

**Описание:**
1. Удалить компоненты, которые больше не используются
2. Проверить, что нет импортов этих компонентов

**Зависимости:**
- Подзадача 7 должна быть завершена

**Приоритет:** Низкий

---

## 5. Параллельное выполнение

### Группа 1 (критическая инфраструктура) — запустить последовательно:
1. **Подзадача 1** (API клиент) — блокирует всё
2. **Подзадача 2** (Telegram SDK) — блокирует авторизацию

### Группа 2 (UI компоненты) — запустить параллельно после Группы 1:
- **Подзадача 3** (ComboSelector) — независимая
- **Подзадача 4** (MenuSection переделка) — независимая
- **Подзадача 5** (ExtrasSection) — независимая
- **Подзадача 6** (OrderSummary) — независимая

### Группа 3 (интеграция) — после Группы 2:
- **Подзадача 7** (page.tsx) — зависит от всех предыдущих
- **Подзадача 8** (удаление) — после подзадачи 7

**Рекомендация для Supervisor:**
- Запустить подзадачи 1 и 2 последовательно
- Запустить подзадачи 3, 4, 5, 6 параллельно (4 Coder субагента одновременно)
- Запустить подзадачи 7 и 8 последовательно

## 6. Риски и ограничения

### 6.1 Риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Backend API недоступен | Средняя | Высокое | Mock server для разработки, обработка ошибок |
| Telegram WebApp initData невалиден | Низкая | Высокое | Fallback для разработки, логирование |
| SWR кэш конфликты | Низкая | Среднее | Правильные ключи кэша, revalidation |
| Большая задержка API | Средняя | Среднее | Loading states, skeleton loaders |

### 6.2 Ограничения

- Backend API должен быть запущен на `http://localhost:8000` (или другой URL для `apiRequest`)
- Telegram WebApp работает только внутри Telegram (для разработки нужен mock)
- JWT токен имеет expiration (нужен refresh механизм в будущем)

## 7. Следующие шаги

После завершения интеграции:
1. **Tester** — написать тесты для API клиента и компонентов
2. **DocWriter** — обновить документацию компонентов
3. **Reviewer** — проверить код на соответствие code-style

## 8. Acceptance Criteria

- [ ] Авторизация через Telegram WebApp работает
- [ ] Список кафе загружается из API через SWR
- [ ] Комбо-наборы отображаются с ценами
- [ ] Выбор блюд по категориям работает (radio)
- [ ] Дополнительные товары добавляются в заказ
- [ ] Итоговая сумма считается корректно
- [ ] Заказ отправляется на backend через `POST /orders`
- [ ] Обрабатываются ошибки API (deadline, access, validation)
- [ ] Код соответствует code-style (Next.js/React/Tailwind)
- [ ] Нет TypeScript ошибок
- [ ] UI соответствует дизайн-системе проекта (градиенты, цвета)
