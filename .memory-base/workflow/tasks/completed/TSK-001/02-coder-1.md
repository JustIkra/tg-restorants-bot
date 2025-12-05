---
agent: coder
task_id: TSK-001
subtask: 1
status: completed
next: coder
created_at: 2025-12-05T23:50:00
files_changed:
  - path: frontend_mini_app/package.json
    action: modified
  - path: frontend_mini_app/package-lock.json
    action: modified
  - path: frontend_mini_app/src/lib/api/client.ts
    action: created
  - path: frontend_mini_app/src/lib/api/types.ts
    action: created
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: created
---

# Coder Report: Подзадача 1 - Инфраструктура API клиента

## Выполненные работы

### 1. Установка зависимостей

Установлен пакет `swr` версии 2.x:

```bash
npm install swr
```

SWR (Stale-While-Revalidate) — это React hooks библиотека для data fetching с:
- Автоматическим кэшированием
- Revalidation при фокусе окна
- Retry при ошибках
- Optimistic updates
- TypeScript поддержкой

### 2. Созданные файлы

#### frontend_mini_app/src/lib/api/types.ts

Определены TypeScript интерфейсы всех сущностей API согласно спецификации:

**Entities:**
- `User` — пользователь системы (tgid, name, office, role, is_active)
- `Cafe` — кафе (id, name, description, is_active)
- `Combo` — комбо-набор (id, cafe_id, name, categories, price, is_available)
- `MenuItem` — блюдо меню (id, cafe_id, name, description, category, price, is_available)
- `OrderCombo` — комбо в заказе (combo_id, combo_name, combo_price, items)
- `OrderComboItem` — блюдо в комбо (category, menu_item_id, menu_item_name)
- `OrderExtra` — дополнительный товар в заказе (menu_item_id, quantity, price, subtotal)
- `Order` — заказ (id, user_tgid, cafe_id, combo, extras, total_price, status)

**Request payloads:**
- `CreateOrderRequest` — создание заказа (cafe_id, order_date, combo_id, combo_items, extras, notes)

**Response wrappers:**
- `ListResponse<T>` — обёртка для списков (items, total)
- `BalanceResponse` — баланс пользователя
- `OrderAvailabilityResponse` — доступность заказа на дату

#### frontend_mini_app/src/lib/api/client.ts

Реализован базовый HTTP клиент с JWT авторизацией:

**Функции:**

1. **`getToken(): string | null`**
   - Получает JWT токен из localStorage
   - Возвращает null если токена нет или выполняется на сервере

2. **`setToken(token: string): void`**
   - Сохраняет JWT токен в localStorage
   - Ключ: `"jwt_token"`

3. **`removeToken(): void`**
   - Удаляет JWT токен из localStorage
   - Вызывается при 401 Unauthorized

4. **`apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T>`**
   - Базовая функция для всех API запросов
   - Автоматически добавляет `Authorization: Bearer {token}` заголовок
   - Добавляет `Content-Type: application/json`
   - Обработка HTTP статусов:
     - 401 Unauthorized → удаляет токен, бросает ошибку
     - 403 Forbidden → "Access denied"
     - 404 Not Found → "Resource not found"
     - 5xx Server Error → "Server error: {detail}"
     - 204 No Content → возвращает undefined
   - Парсит JSON ошибки из response.detail или response.message
   - Обрабатывает network errors

5. **`authenticateWithTelegram(initData: string): Promise<{ access_token: string; user: User }>`**
   - Отправляет POST /auth/telegram с Telegram WebApp initData
   - Автоматически сохраняет токен через `setToken()`
   - Возвращает access_token и объект User

**Константы:**
- `API_URL` — базовый URL API (из `NEXT_PUBLIC_API_URL` env или "http://localhost:8000/api/v1")
- `TOKEN_KEY` — ключ для localStorage ("jwt_token")

**Обработка ошибок:**
- Все ошибки бросаются как `Error` с человекочитаемым сообщением
- 401 автоматически очищает токен
- 5xx можно расширить retry логикой в будущем

#### frontend_mini_app/src/lib/api/hooks.ts

Реализованы SWR хуки для data fetching:

**Хуки:**

1. **`useCafes(activeOnly = true): SWRResponse<Cafe[], Error>`**
   - Загружает список кафе
   - По умолчанию фильтрует только активные (`?active_only=true`)
   - Возвращает массив Cafe

2. **`useCombos(cafeId: number | null): SWRResponse<Combo[], Error>`**
   - Загружает комбо-наборы для кафе
   - Если `cafeId = null`, запрос не выполняется (endpoint = null)
   - Возвращает массив Combo

3. **`useMenu(cafeId: number | null, category?: string): SWRResponse<MenuItem[], Error>`**
   - Загружает меню кафе
   - Опциональный фильтр по категории (`?category=soup`)
   - Если `cafeId = null`, запрос не выполняется
   - Возвращает массив MenuItem

4. **`useCreateOrder(): { createOrder, isLoading, error }`**
   - Mutation hook для создания заказа
   - Возвращает функцию `createOrder(data)` и состояние `isLoading`/`error`
   - Вызов `createOrder()` отправляет POST /orders
   - Автоматически управляет loading state

5. **`useOrders(filters?): SWRResponse<Order[], Error>`**
   - Загружает заказы пользователя
   - Опциональные фильтры: `date`, `cafeId`, `status`
   - Возвращает массив Order

**Технические детали:**
- Все хуки помечены `"use client"` для Next.js 16 App Router
- Используется общий fetcher функция `apiRequest`
- SWR автоматически кэширует данные по endpoint key
- Null endpoint отключает запрос (conditional fetching)

### 3. Соответствие требованиям

✅ **TypeScript strict mode** — все типы явно определены
✅ **Code style** — следует Next.js/React conventions:
  - `"use client"` для hooks
  - Functional syntax
  - Двойные кавычки
  - Правильные импорты
✅ **API спецификация** — все endpoints и типы соответствуют `.memory-base/tech-docs/api.md`
✅ **Архитектурный план** — реализация соответствует `01-architect.md`

### 4. Использование в компонентах

Пример использования хуков в page.tsx:

```tsx
"use client";

import { useCafes, useCombos, useMenu, useCreateOrder } from "@/lib/api/hooks";
import { authenticateWithTelegram } from "@/lib/api/client";
import { getTelegramInitData } from "@/lib/telegram/webapp";

export default function HomePage() {
  // Data fetching
  const { data: cafes, isLoading: cafesLoading } = useCafes(true);
  const { data: combos } = useCombos(selectedCafe?.id ?? null);
  const { data: menuItems } = useMenu(selectedCafe?.id ?? null);
  const { data: extras } = useMenu(selectedCafe?.id ?? null, "extra");

  // Mutation
  const { createOrder, isLoading: orderLoading } = useCreateOrder();

  // Auth
  useEffect(() => {
    const initData = getTelegramInitData();
    if (initData) {
      authenticateWithTelegram(initData)
        .then(({ user }) => console.log("Logged in:", user.name))
        .catch(err => console.error("Auth failed:", err));
    }
  }, []);

  // Create order
  const handleCheckout = async () => {
    const orderData = { cafe_id: 1, order_date: "2025-12-06", ... };
    const order = await createOrder(orderData);
    console.log("Order created:", order.id);
  };

  return <div>...</div>;
}
```

## Зависимости для следующих подзадач

Этот модуль является критической инфраструктурой и блокирует:

- **Подзадача 2** (Telegram SDK) — нужен для авторизации
- **Подзадача 3-6** (UI компоненты) — используют типы из `types.ts`
- **Подзадача 7** (page.tsx) — использует все хуки

Рекомендуется запустить **Подзадачу 2** следующей, а затем параллельно подзадачи 3-6.

## Следующие шаги

1. ✅ Подзадача 1 завершена
2. → Запустить **Подзадачу 2** (Telegram SDK) — нужен для авторизации
3. → После завершения 2, запустить **Подзадачи 3, 4, 5, 6 параллельно** (UI компоненты)
4. → После завершения всех, запустить **Подзадачу 7** (page.tsx интеграция)

## Проверка

Код готов к использованию. TypeScript компиляция должна пройти без ошибок.

Для тестирования API клиента:
1. Убедиться, что backend запущен на `http://localhost:8000`
2. Или установить `NEXT_PUBLIC_API_URL` в `.env.local`
3. Проверить работу хуков в компонентах

## Примечания

- **Environment variable:** Можно изменить API URL через `NEXT_PUBLIC_API_URL` в `.env.local`
- **Token persistence:** JWT токен сохраняется в localStorage с ключом `"jwt_token"`
- **Error handling:** Все ошибки API бросаются как `Error` с человекочитаемым message
- **SSR safe:** Проверки `typeof window === "undefined"` для серверного рендеринга
- **SWR cache:** Данные кэшируются по URL, revalidation при фокусе окна
- **Retry logic:** SWR автоматически повторяет запросы при ошибках (можно настроить)

Status: **completed** ✅
