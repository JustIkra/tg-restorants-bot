---
agent: coder
task_id: TSK-013
subtask: 1
subtask_name: "API Layer"
status: completed
next: null
created_at: 2025-12-07T12:00:00
files_changed:
  - path: frontend_mini_app/src/lib/api/types.ts
    action: modified
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
---

## Реализация

Реализован API Layer для страницы профиля пользователя - добавлены необходимые типы TypeScript и SWR hooks для работы с балансами и рекомендациями.

### Изменения

#### `frontend_mini_app/src/lib/api/types.ts`

1. **Обновлён `BalanceResponse` интерфейс** (заменён устаревший):
   - Добавлено поле `tgid: number`
   - Изменён тип `weekly_limit` на `number | null` (вместо обязательного `number`)
   - Добавлено поле `remaining: number | null`
   - Удалено поле `balance` (заменено на `spent_this_week`)

2. **Добавлен `OrderStats` интерфейс**:
   - `orders_last_30_days: number` - количество заказов за последние 30 дней
   - `categories: { [category: string]: { count: number; percent: number } }` - статистика по категориям
   - `unique_dishes: number` - количество уникальных блюд
   - `favorite_dishes: { name: string; count: number }[]` - любимые блюда с частотой заказа

3. **Добавлен `RecommendationsResponse` интерфейс**:
   - `summary: string | null` - текстовое резюме рекомендаций (null если < 5 заказов)
   - `tips: string[]` - массив советов от AI
   - `stats: OrderStats` - статистика заказов
   - `generated_at: string | null` - дата генерации рекомендаций

#### `frontend_mini_app/src/lib/api/hooks.ts`

1. **Обновлены импорты**:
   - Добавлены типы `BalanceResponse` и `RecommendationsResponse`

2. **Добавлена секция "User Profile Hooks"** с тремя новыми hooks:

   **`useUserRecommendations(tgid: number | null)`**:
   - Endpoint: `GET /users/{tgid}/recommendations`
   - Conditional fetching: запрос выполняется только если `tgid !== null`
   - Возвращает: `{ data, error, isLoading, mutate }`
   - Тип данных: `RecommendationsResponse`

   **`useUserBalance(tgid: number | null)`**:
   - Endpoint: `GET /users/{tgid}/balance`
   - Conditional fetching: запрос выполняется только если `tgid !== null`
   - Возвращает: `{ data, error, isLoading, mutate }`
   - Тип данных: `BalanceResponse`

   **`useUpdateBalanceLimit()`**:
   - Endpoint: `PATCH /users/{tgid}/balance/limit`
   - Mutation hook для обновления недельного лимита
   - Возвращает: `{ updateLimit: (tgid, weekly_limit) => Promise<User> }`
   - Параметры: `tgid: number`, `weekly_limit: number | null`
   - Автоматическая инвалидация кэша:
     - `/users/${tgid}/balance` - для обновления данных баланса пользователя
     - `/users` - для обновления списка всех пользователей в менеджере

## Примечания

### Архитектурные решения

1. **Conditional fetching** во всех read-hooks:
   - Используется паттерн `tgid ? endpoint : null`
   - Позволяет безопасно использовать hooks до получения user.tgid из localStorage
   - Предотвращает лишние запросы с null/undefined параметрами

2. **Nullable типы**:
   - `weekly_limit: number | null` - лимит может отсутствовать (не установлен менеджером)
   - `remaining: number | null` - остаток считается только при наличии лимита
   - `summary: string | null` - рекомендации отсутствуют при < 5 заказах
   - Компоненты должны обрабатывать эти случаи через empty states

3. **Mutation с двойной инвалидацией**:
   - `useUpdateBalanceLimit` инвалидирует два endpoints
   - `/users/${tgid}/balance` - для немедленного обновления ProfileBalance компонента
   - `/users` - для обновления BalanceManager в панели менеджера
   - Обеспечивает консистентность данных во всех компонентах

### Соответствие backend schemas

Все типы точно соответствуют backend API:
- Backend `Decimal` → Frontend `number` (автоматическая конвертация через JSON)
- Backend `datetime` → Frontend `string` (ISO format)
- Nullable поля корректно отражены через `| null`

### Готовность для следующих подзадач

API Layer готов для использования в:
- Подзадача 2: Profile Components (ProfileStats, ProfileRecommendations, ProfileBalance)
- Подзадача 3: Profile Page (/profile)
- Подзадача 4: Balance Manager (панель менеджера)

Все hooks следуют существующим паттернам проекта и готовы к использованию.
