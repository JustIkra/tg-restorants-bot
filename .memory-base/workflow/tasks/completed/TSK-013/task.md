---
id: TSK-013
title: "Страница профиля пользователя и управление балансами менеджером"
pipeline: feature
status: pending
created_at: 2025-12-07T00:30:00+00:00
related_files:
  # Backend - существующие файлы с балансом и рекомендациями
  - backend/src/routers/users.py
  - backend/src/routers/recommendations.py
  - backend/src/services/user.py
  - backend/src/services/order_stats.py
  - backend/src/schemas/user.py
  - backend/src/schemas/recommendations.py
  - backend/src/models/user.py
  - backend/src/repositories/user.py

  # Frontend - новые компоненты
  - frontend_mini_app/src/app/profile/page.tsx
  - frontend_mini_app/src/components/Profile/ProfileStats.tsx
  - frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx
  - frontend_mini_app/src/components/Profile/ProfileBalance.tsx
  - frontend_mini_app/src/components/Manager/BalanceManager.tsx

  # Frontend - обновляемые файлы
  - frontend_mini_app/src/lib/api/hooks.ts
  - frontend_mini_app/src/lib/api/types.ts
  - frontend_mini_app/src/app/manager/page.tsx
  - frontend_mini_app/src/app/page.tsx

impact:
  api: нет (используются существующие endpoints)
  db: нет (модель User уже содержит weekly_limit)
  frontend: да (новая страница /profile, компоненты профиля, вкладка в менеджере)
  services: нет (все сервисы уже реализованы)
---

## Описание

Создать страницу профиля пользователя с отображением статистики заказов, AI-рекомендаций и корпоративного баланса. Добавить в панель менеджера вкладку для управления балансами (weekly_limit) пользователей.

## Acceptance Criteria

### Страница профиля (/profile)
- [ ] Новая страница `/profile` доступная для всех пользователей (user и manager)
- [ ] Кнопка перехода на профиль в главной странице (/) - иконка профиля в шапке
- [ ] Три секции на странице профиля:
  - [ ] **Статистика заказов** (ProfileStats):
    - Количество заказов за последние 30 дней
    - Распределение по категориям (soup, salad, main, extra) в процентах
    - Количество уникальных блюд
    - Топ-5 любимых блюд с количеством заказов
  - [ ] **AI-рекомендации** (ProfileRecommendations):
    - Персональный саммари привычек питания (summary)
    - Список рекомендаций (tips)
    - Дата генерации рекомендаций (generated_at)
    - Плейсхолдер если нет рекомендаций (< 5 заказов)
  - [ ] **Корпоративный баланс** (ProfileBalance):
    - Недельный лимит (weekly_limit)
    - Потрачено на этой неделе (spent_this_week)
    - Остаток (remaining)
    - Индикатор прогресса использования баланса
- [ ] Кнопка возврата на главную страницу

### Управление балансами в панели менеджера
- [ ] Новая вкладка "Балансы" в `/manager` после вкладки "Users"
- [ ] Компонент `BalanceManager` отображает список пользователей с балансами:
  - [ ] Имя пользователя, office, telegram ID
  - [ ] Текущий лимит (weekly_limit)
  - [ ] Потрачено на этой неделе (spent_this_week)
  - [ ] Остаток (remaining)
  - [ ] Кнопка редактирования лимита для каждого пользователя
- [ ] Форма редактирования лимита:
  - [ ] Поле ввода для weekly_limit (decimal, nullable)
  - [ ] Кнопка "Сохранить" - вызывает PATCH /users/{tgid}/balance/limit
  - [ ] Кнопка "Снять лимит" - устанавливает weekly_limit = null
- [ ] Поиск/фильтрация пользователей (опционально)
- [ ] Обновление данных после изменения лимита (SWR mutate)

### API интеграция (уже существует)
- [ ] GET /users/{tgid}/recommendations - получить рекомендации
- [ ] GET /users/{tgid}/balance - получить баланс
- [ ] PATCH /users/{tgid}/balance/limit - установить лимит (manager only)

### Дизайн и UX
- [ ] Использовать существующий дизайн-систему проекта:
  - Purple gradient для активных элементов (#8B23CB - #A020F0)
  - Dark background (#130F30)
  - Semi-transparent cards
  - Tailwind CSS 4 стили
- [ ] Responsive design для мобильных устройств
- [ ] Loading states (skeleton placeholders)
- [ ] Error handling с информативными сообщениями
- [ ] Empty states для отсутствия данных

### Тесты
- [ ] Unit тесты для новых SWR hooks:
  - useUserRecommendations
  - useUserBalance
  - useUpdateBalanceLimit
- [ ] Component тесты для:
  - ProfileStats
  - ProfileRecommendations
  - ProfileBalance
  - BalanceManager
- [ ] E2E тест для сценария просмотра профиля
- [ ] E2E тест для сценария управления балансами менеджером

## Контекст

### Backend (уже реализовано)

**Модель User** (`backend/src/models/user.py`):
- Поле `weekly_limit: Decimal | None` - недельный лимит расходов
- Relationships с Order для расчёта статистики

**Endpoints:**
- `GET /users/{tgid}/recommendations` - возвращает `RecommendationsResponse`:
  ```python
  class RecommendationsResponse(BaseModel):
      summary: str | None           # AI-generated summary
      tips: list[str]                # Personalized recommendations
      stats: OrderStats              # Current order statistics
      generated_at: datetime | None  # When generated

  class OrderStats(BaseModel):
      orders_last_30_days: int
      categories: dict[str, dict]    # {"soup": {"count": 10, "percent": 40.0}}
      unique_dishes: int
      favorite_dishes: list[dict]    # [{"name": "Борщ", "count": 5}]
  ```
- `GET /users/{tgid}/balance` - возвращает `BalanceResponse`:
  ```python
  class BalanceResponse(BaseModel):
      tgid: int
      weekly_limit: Decimal | None
      spent_this_week: Decimal
      remaining: Decimal | None
  ```
- `PATCH /users/{tgid}/balance/limit` - устанавливает лимит (manager only):
  ```python
  class BalanceLimitUpdate(BaseModel):
      weekly_limit: Decimal | None
  ```

**Сервисы:**
- `UserService.get_balance(tgid)` - получает баланс пользователя
- `UserService.update_balance_limit(tgid, weekly_limit)` - обновляет лимит
- `OrderStatsService.get_user_stats(tgid)` - статистика заказов

**Рекомендации генерируются batch worker'ом ночью**, эндпоинт только читает из Redis кэша.

### Frontend

**Существующие hooks** (`frontend_mini_app/src/lib/api/hooks.ts`):
- `useUsers()` - список пользователей для менеджера
- `useCreateUser()`, `useUpdateUserAccess()`, `useDeleteUser()`

**Новые hooks (нужно добавить):**
- `useUserRecommendations(tgid: number)` - GET /users/{tgid}/recommendations
- `useUserBalance(tgid: number)` - GET /users/{tgid}/balance
- `useUpdateBalanceLimit()` - PATCH /users/{tgid}/balance/limit

**Существующие типы** (`frontend_mini_app/src/lib/api/types.ts`):
- `User` - интерфейс пользователя
- `BalanceResponse` - интерфейс баланса (УСТАРЕЛ, нужно обновить)

**Новые типы (нужно добавить):**
```typescript
export interface OrderStats {
  orders_last_30_days: number;
  categories: { [category: string]: { count: number; percent: number } };
  unique_dishes: number;
  favorite_dishes: { name: string; count: number }[];
}

export interface RecommendationsResponse {
  summary: string | null;
  tips: string[];
  stats: OrderStats;
  generated_at: string | null;
}

export interface BalanceResponse {
  tgid: number;
  weekly_limit: number | null;
  spent_this_week: number;
  remaining: number | null;
}
```

**Существующие Manager компоненты:**
- `UserList.tsx` - список пользователей
- `UserForm.tsx` - создание пользователя
- Layout: manager page с табами (Users, Cafes, Menu, Requests, Reports)

**Дизайн система:**
- Purple gradient: `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- Dark background: `bg-[#130F30]`
- Semi-transparent cards: `bg-white/10` или `bg-[#7B6F9C]/20`
- Icons: `react-icons/fa6` (FaUser, FaChartLine, FaLightbulb, FaWallet)

### Структура компонентов

**Profile Page** (`frontend_mini_app/src/app/profile/page.tsx`):
```tsx
- Заголовок "Мой профиль"
- ProfileStats компонент (статистика)
- ProfileRecommendations компонент (рекомендации)
- ProfileBalance компонент (баланс)
- Кнопка назад на главную (FaArrowLeft)
```

**ProfileStats** (`frontend_mini_app/src/components/Profile/ProfileStats.tsx`):
```tsx
Props: stats: OrderStats
Display:
- Карточка "Статистика заказов"
- Иконка FaChartLine
- Заказов за 30 дней: stats.orders_last_30_days
- Категории (круговая диаграмма или список):
  - Супы: X% (Y заказов)
  - Салаты: X% (Y заказов)
  - Основное: X% (Y заказов)
  - Дополнительно: X% (Y заказов)
- Уникальных блюд: stats.unique_dishes
- Топ-5 любимых:
  - 1. Борщ украинский (5 раз)
  - 2. Салат Цезарь (4 раза)
  ...
```

**ProfileRecommendations** (`frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx`):
```tsx
Props: recommendations: RecommendationsResponse
Display:
- Карточка "AI-рекомендации"
- Иконка FaLightbulb
- Summary (если есть): recommendations.summary
- Tips (список):
  - Попробуйте новые супы - вы пробовали только 3 из 10
  - Добавьте больше овощей в рацион
  ...
- Дата генерации: recommendations.generated_at
- Плейсхолдер если нет: "Сделайте минимум 5 заказов для получения рекомендаций"
```

**ProfileBalance** (`frontend_mini_app/src/components/Profile/ProfileBalance.tsx`):
```tsx
Props: balance: BalanceResponse
Display:
- Карточка "Корпоративный баланс"
- Иконка FaWallet
- Недельный лимит: balance.weekly_limit (или "Не установлен")
- Потрачено: balance.spent_this_week
- Остаток: balance.remaining
- Прогресс-бар: spent / limit (если лимит установлен)
- Цвет прогресса: зеленый < 70%, желтый 70-90%, красный > 90%
```

**BalanceManager** (`frontend_mini_app/src/components/Manager/BalanceManager.tsx`):
```tsx
Display:
- Заголовок "Управление балансами"
- Таблица/список пользователей:
  Columns:
  - Пользователь (имя + office)
  - Telegram ID
  - Лимит (weekly_limit или "—")
  - Потрачено (spent_this_week)
  - Остаток (remaining или "—")
  - Действия (кнопка редактировать)
- Modal/форма редактирования:
  - Поле ввода weekly_limit (number, nullable)
  - Кнопка "Сохранить"
  - Кнопка "Снять лимит" (weekly_limit = null)
```

### Навигация

**Главная страница** (`frontend_mini_app/src/app/page.tsx`):
- Добавить кнопку профиля в шапку (FaUser icon)
- Кнопка ведет на `/profile`

**Manager page** (`frontend_mini_app/src/app/manager/page.tsx`):
- Добавить новый таб "Балансы" после "Users"
- При клике показывать BalanceManager компонент

### Возможные проблемы

1. **weekly_limit nullable** - нужно корректно обрабатывать null значения
2. **Рекомендации могут отсутствовать** - показывать плейсхолдер
3. **Статистика за 0 заказов** - empty state "Пока нет заказов"
4. **Auth**: доступ к /users/{tgid}/balance разрешен только self или manager
5. **Decimal числа в балансе** - форматировать с 2 знаками после запятой

### План реализации

#### 1. Backend (проверка готовности)
- ✓ Endpoints уже есть
- ✓ Модели уже есть
- ✓ Сервисы уже есть
- Нужно: убедиться что все работает

#### 2. Frontend - API Layer
- Обновить типы (types.ts): OrderStats, RecommendationsResponse, BalanceResponse
- Добавить hooks (hooks.ts):
  - useUserRecommendations
  - useUserBalance
  - useUpdateBalanceLimit

#### 3. Frontend - Profile Components
- Создать Profile/ProfileStats.tsx
- Создать Profile/ProfileRecommendations.tsx
- Создать Profile/ProfileBalance.tsx
- Создать app/profile/page.tsx (использует 3 компонента выше)

#### 4. Frontend - Manager Components
- Создать Manager/BalanceManager.tsx
- Обновить app/manager/page.tsx - добавить таб "Балансы"

#### 5. Frontend - Navigation
- Обновить app/page.tsx - добавить кнопку профиля в header
- Добавить роутинг для /profile

#### 6. Тесты
- Unit тесты для hooks
- Component тесты для Profile компонентов
- Component тест для BalanceManager
- E2E тесты для профиля и управления балансами

#### 7. Документация
- Обновить frontend-components.md
- Описать новые компоненты и hooks
- Примеры использования

## Технические детали

### SWR Hooks Pattern

```typescript
export function useUserRecommendations(tgid: number | null): {
  data: RecommendationsResponse | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
} {
  const { data, error, isLoading, mutate } = useSWR<RecommendationsResponse>(
    tgid ? `/users/${tgid}/recommendations` : null,
    fetcher
  );
  return { data, error, isLoading, mutate };
}
```

### Balance Limit Update Hook

```typescript
export function useUpdateBalanceLimit() {
  const { mutate } = useSWRConfig();
  const updateLimit = async (tgid: number, weekly_limit: number | null) => {
    const result = await apiRequest<User>(`/users/${tgid}/balance/limit`, {
      method: "PATCH",
      body: JSON.stringify({ weekly_limit })
    });
    // Revalidate balance and users list
    mutate(`/users/${tgid}/balance`);
    mutate("/users");
    return result;
  };
  return { updateLimit };
}
```

### Balance Progress Bar

```typescript
const getProgressColor = (percent: number) => {
  if (percent < 70) return "bg-green-500";
  if (percent < 90) return "bg-yellow-500";
  return "bg-red-500";
};

const percent = balance.weekly_limit
  ? (balance.spent_this_week / balance.weekly_limit) * 100
  : 0;
```

### Responsive Design

- Mobile-first подход
- Профиль: одна колонка на мобильном, две на десктопе
- Менеджер балансов: scrollable table на мобильном
- Touch-friendly button sizes (минимум 44px)

## Зависимости

- Нет новых зависимостей
- Используется существующий стек: Next.js 16, React 19, Tailwind CSS 4
- SWR для кэширования
- react-icons для иконок

## Риски и вопросы

1. **Формат данных categories в OrderStats** - уточнить точную структуру из backend
2. **Decimal vs Float в балансе** - убедиться в правильном форматировании
3. **Кэширование рекомендаций** - понять TTL Redis кэша (документация говорит 24ч)
4. **Авторизация на фронте** - проверить что user.tgid доступен для запросов
