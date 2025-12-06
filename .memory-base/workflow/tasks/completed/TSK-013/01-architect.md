---
agent: architect
task_id: TSK-013
status: completed
next: coder
created_at: 2025-12-07T12:30:00
---

## Анализ

Задача требует создать страницу профиля пользователя и добавить управление балансами в панель менеджера. Backend API уже полностью готов, задача исключительно frontend.

**Существующая инфраструктура:**
- Backend endpoints готовы: `/users/{tgid}/recommendations`, `/users/{tgid}/balance`, `PATCH /users/{tgid}/balance/limit`
- Frontend API client и SWR hooks готовы для расширения
- Дизайн-система и компоненты менеджера готовы для повторного использования
- Навигация между страницами уже реализована (кнопки в header)

**Ключевые решения:**
1. Создать новую страницу `/profile` для всех пользователей (user и manager)
2. Разбить профиль на 3 независимых компонента (Stats, Recommendations, Balance)
3. Добавить вкладку "Балансы" в панель менеджера (6-я вкладка)
4. Использовать существующие паттерны: SWR hooks, loading states, error handling, дизайн-система

## Архитектурное решение

### Подход

**Routing:**
- Новая страница: `frontend_mini_app/src/app/profile/page.tsx`
- Навигация: кнопка профиля в header главной страницы (FaUser icon)
- Back navigation: кнопка возврата на главную страницу

**Component Architecture:**
```
ProfilePage
├── ProfileStats (статистика заказов)
├── ProfileRecommendations (AI рекомендации)
└── ProfileBalance (корпоративный баланс)

ManagerPage (existing)
└── New Tab: "Балансы"
    └── BalanceManager (управление лимитами)
```

**Data Flow:**
- Profile page получает `user.tgid` из localStorage (уже сохраняется при авторизации)
- Три SWR hooks загружают данные параллельно: `useUserRecommendations`, `useUserBalance`, `useUsers` (для менеджера)
- Loading/error states управляются внутри каждого компонента
- BalanceManager использует список пользователей + балансы

### Изменения в данных

**Backend schemas (уже существуют):**
```python
# BalanceResponse
{
  "tgid": int,
  "weekly_limit": Decimal | None,
  "spent_this_week": Decimal,
  "remaining": Decimal | None
}

# RecommendationsResponse
{
  "summary": str | None,
  "tips": list[str],
  "stats": OrderStats,
  "generated_at": datetime | None
}

# OrderStats
{
  "orders_last_30_days": int,
  "categories": {"soup": {"count": 10, "percent": 40.0}},
  "unique_dishes": int,
  "favorite_dishes": [{"name": "Борщ", "count": 5}]
}
```

**Frontend types to add (types.ts):**
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
  weekly_limit: number | null;  // Decimal → number
  spent_this_week: number;      // Decimal → number
  remaining: number | null;      // Decimal → number
}
```

**Note:** Existing `BalanceResponse` type is outdated and needs to be replaced.

### API изменения

**New SWR hooks (hooks.ts):**

1. **useUserRecommendations(tgid: number | null)**
   - Endpoint: `GET /users/{tgid}/recommendations`
   - Returns: `{ data, error, isLoading, mutate }`
   - Conditional fetching: skip if tgid is null

2. **useUserBalance(tgid: number | null)**
   - Endpoint: `GET /users/{tgid}/balance`
   - Returns: `{ data, error, isLoading, mutate }`
   - Conditional fetching: skip if tgid is null

3. **useUpdateBalanceLimit()**
   - Endpoint: `PATCH /users/{tgid}/balance/limit`
   - Returns: `{ updateLimit: (tgid, weekly_limit) => Promise<User> }`
   - Mutation hook with SWR revalidation
   - Revalidates: `/users/${tgid}/balance` and `/users`

**Pattern:**
```typescript
// Read hook
export function useUserRecommendations(tgid: number | null) {
  const { data, error, isLoading, mutate } = useSWR<RecommendationsResponse>(
    tgid ? `/users/${tgid}/recommendations` : null,
    fetcher
  );
  return { data, error, isLoading, mutate };
}

// Mutation hook
export function useUpdateBalanceLimit() {
  const { mutate } = useSWRConfig();
  const updateLimit = async (tgid: number, weekly_limit: number | null) => {
    const result = await apiRequest<User>(`/users/${tgid}/balance/limit`, {
      method: "PATCH",
      body: JSON.stringify({ weekly_limit })
    });
    mutate(`/users/${tgid}/balance`);
    mutate("/users");
    return result;
  };
  return { updateLimit };
}
```

## Подзадачи для Coder

### Независимые подзадачи (можно выполнять параллельно)

#### 1. API Layer: Types and Hooks
**Файлы:**
- `frontend_mini_app/src/lib/api/types.ts`
- `frontend_mini_app/src/lib/api/hooks.ts`

**Действия:**
- Обновить `BalanceResponse` интерфейс (заменить устаревший)
- Добавить `OrderStats` интерфейс
- Добавить `RecommendationsResponse` интерфейс
- Добавить hook `useUserRecommendations(tgid: number | null)`
- Добавить hook `useUserBalance(tgid: number | null)`
- Добавить hook `useUpdateBalanceLimit()`

**Validation:**
- Типы соответствуют backend schemas
- Hooks используют conditional fetching (null check)
- Mutation hook корректно инвалидирует кэш

#### 2. Profile Components (3 компонента)
**Файлы:**
- `frontend_mini_app/src/components/Profile/ProfileStats.tsx`
- `frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx`
- `frontend_mini_app/src/components/Profile/ProfileBalance.tsx`

**Действия:**

**ProfileStats:**
- Props: `{ stats: OrderStats }`
- Отображение:
  - Заголовок "Статистика заказов" + иконка FaChartLine
  - Заказов за 30 дней: `stats.orders_last_30_days`
  - Категории: loop через `stats.categories` → "Супы: 40% (10 заказов)"
  - Уникальных блюд: `stats.unique_dishes`
  - Топ-5 любимых: loop через `stats.favorite_dishes.slice(0, 5)` → "1. Борщ (5 раз)"
- Стили: semi-transparent card, purple gradient header, white text
- Empty state: если `orders_last_30_days === 0` → "Пока нет заказов"

**ProfileRecommendations:**
- Props: `{ recommendations: RecommendationsResponse }`
- Отображение:
  - Заголовок "AI-рекомендации" + иконка FaLightbulb
  - Summary (если есть): `recommendations.summary`
  - Tips: loop через `recommendations.tips` → список с bullet points
  - Дата генерации: `recommendations.generated_at` форматировать как "DD.MM.YYYY"
- Empty state: если `recommendations.summary === null` → "Сделайте минимум 5 заказов для получения рекомендаций"
- Стили: semi-transparent card, purple gradient header

**ProfileBalance:**
- Props: `{ balance: BalanceResponse }`
- Отображение:
  - Заголовок "Корпоративный баланс" + иконка FaWallet
  - Недельный лимит: `balance.weekly_limit` или "Не установлен"
  - Потрачено: `balance.spent_this_week` → форматировать "XXX ₽"
  - Остаток: `balance.remaining` или "—"
  - Progress bar: `(spent_this_week / weekly_limit) * 100`
    - Цвет: зеленый < 70%, желтый 70-90%, красный > 90%
- Стили: semi-transparent card, purple gradient header
- Decimal formatting: `.toFixed(2)` для всех чисел

**Validation для всех компонентов:**
- Loading state: skeleton placeholders
- Error handling: red error banner
- Responsive design: mobile-first
- Icons from `react-icons/fa6`
- Дизайн-система: purple gradient, dark background, white text

#### 3. Profile Page
**Файлы:**
- `frontend_mini_app/src/app/profile/page.tsx`

**Действия:**
- Создать новую страницу `/profile`
- Получить `user.tgid` из localStorage
- Использовать 3 SWR hooks параллельно:
  ```typescript
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const { data: recommendations, isLoading: recLoading, error: recError } = useUserRecommendations(user.tgid);
  const { data: balance, isLoading: balLoading, error: balError } = useUserBalance(user.tgid);
  ```
- Layout:
  - Header: "Мой профиль" + кнопка назад (FaArrowLeft → `/`)
  - ProfileStats (передать `recommendations.stats`)
  - ProfileRecommendations (передать `recommendations`)
  - ProfileBalance (передать `balance`)
- Стили: dark background, gradient blurs, responsive layout
- Authentication: check `isTelegramWebApp()`, redirect if not authenticated

**Validation:**
- Обработка null/undefined данных
- Loading states для каждой секции
- Error states для каждой секции
- Кнопка назад работает корректно

#### 4. Balance Manager Component
**Файлы:**
- `frontend_mini_app/src/components/Manager/BalanceManager.tsx`

**Действия:**
- Self-contained компонент (no props)
- Использовать hooks:
  ```typescript
  const { data: users, isLoading, error } = useUsers();
  const { updateLimit } = useUpdateBalanceLimit();
  ```
- Для каждого пользователя загружать баланс:
  ```typescript
  const { data: balance } = useUserBalance(user.tgid);
  ```
- Отображение таблицы/списка:
  - Columns: Имя, Office, Telegram ID, Лимит, Потрачено, Остаток, Действия
  - Кнопка "Редактировать" → открывает форму/modal
- Форма редактирования:
  - Input для `weekly_limit` (number, nullable)
  - Кнопка "Сохранить" → вызывает `updateLimit(tgid, value)`
  - Кнопка "Снять лимит" → вызывает `updateLimit(tgid, null)`
  - Validation: positive number or null
- Стили: таблица с semi-transparent rows, purple gradient buttons
- Loading: skeleton placeholders
- Error handling: red error banner

**Validation:**
- Обработка decimal чисел (форматирование `.toFixed(2)`)
- Корректная работа с `null` лимитами
- SWR revalidation после изменений
- Confirm dialog перед снятием лимита

#### 5. Navigation Integration
**Файлы:**
- `frontend_mini_app/src/app/page.tsx` (главная страница)
- `frontend_mini_app/src/app/manager/page.tsx` (панель менеджера)

**Действия:**

**page.tsx (главная страница):**
- Добавить кнопку профиля в header рядом с кнопкой менеджера/колеса:
  ```tsx
  <button
    onClick={() => router.push("/profile")}
    className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B23CB]/50 to-[#A020F0]/50 border border-white/20 backdrop-blur-md shadow-lg"
    aria-label="Профиль"
  >
    <FaUser className="text-white text-xl" />
  </button>
  ```
- Расположение: в существующем блоке кнопок (строки 327-344)
- Порядок: FaUser (profile) → FaUserShield (manager, if manager) → Fortune Wheel

**manager/page.tsx (панель менеджера):**
- Добавить новую вкладку "Балансы" в массив `tabs` после "Users":
  ```typescript
  { id: "balances", name: "Балансы", icon: <FaWallet /> }
  ```
- Добавить рендеринг в `{activeTab === "balances" && ...}`:
  ```tsx
  {activeTab === "balances" && (
    <div className="text-white">
      <BalanceManager />
    </div>
  )}
  ```

**Validation:**
- Кнопка профиля видна для всех пользователей (user и manager)
- Responsive design: кнопка сохраняет размеры на мобильных
- Вкладка "Балансы" появляется после "Users" в менеджере
- Tab navigation работает корректно

### Порядок выполнения подзадач

**Рекомендуемый порядок (с учетом зависимостей):**

1. **Сначала (обязательно):** Подзадача 1 (API Layer)
   - Причина: все остальные подзадачи зависят от типов и hooks

2. **Параллельно (после подзадачи 1):**
   - Подзадача 2 (Profile Components)
   - Подзадача 3 (Profile Page)
   - Подзадача 4 (Balance Manager)

3. **Последними (после всех компонентов):**
   - Подзадача 5 (Navigation Integration)

**Note для Coder:** Подзадачи 2, 3, 4 независимы друг от друга после завершения подзадачи 1. Можно выполнять параллельно для ускорения.

## Риски и зависимости

### Риски

1. **Decimal → Number конвертация**
   - Backend использует `Decimal` для точности финансовых операций
   - Frontend получает числа как `number` через JSON
   - Риск: потеря точности при больших суммах
   - Митигация: использовать `.toFixed(2)` для отображения, backend контролирует точность

2. **Рекомендации могут отсутствовать**
   - Endpoint возвращает `summary: null` если < 5 заказов
   - Риск: пустой экран или ошибка
   - Митигация: empty state "Сделайте минимум 5 заказов..."

3. **Формат categories в OrderStats**
   - Backend: `{"soup": {"count": 10, "percent": 40.0}}`
   - Нужно точно понять структуру для корректного отображения
   - Митигация: использовать `Object.entries(categories).map(...)`

4. **localStorage user object может отсутствовать**
   - Если пользователь очистил localStorage или зашел напрямую на `/profile`
   - Риск: crash или некорректная работа
   - Митигация: проверка на null, redirect на `/` если нет user

5. **Balance loading для каждого пользователя**
   - BalanceManager загружает баланс для КАЖДОГО пользователя отдельно
   - Риск: множественные запросы, медленная загрузка
   - Митигация: использовать SWR кэширование, показывать loading states

### Зависимости

1. **Backend API готов** ✓
   - Endpoints работают
   - Schemas определены
   - Authorization настроена

2. **Frontend инфраструктура готова** ✓
   - SWR hooks pattern
   - API client с JWT auth
   - Дизайн-система
   - Manager components pattern

3. **User object в localStorage** ✓
   - Сохраняется при авторизации в `page.tsx`
   - Содержит `tgid` для запросов

4. **Icons from react-icons/fa6** ✓
   - Библиотека уже используется
   - Нужные иконки: FaUser, FaChartLine, FaLightbulb, FaWallet, FaArrowLeft

### Вопросы для уточнения

1. **Pagination для BalanceManager?**
   - Если пользователей > 100, нужна пагинация?
   - Предложение: использовать существующий `useUsers()` hook с limit=100

2. **Search/Filter в BalanceManager?**
   - Task mentions "опционально"
   - Предложение: пропустить в первой итерации, добавить позже если нужно

3. **Chart для категорий в ProfileStats?**
   - Текст или круговая диаграмма?
   - Предложение: простой текстовый список "Супы: 40% (10 заказов)" для MVP

4. **Формат даты для generated_at?**
   - Backend: ISO datetime string
   - Предложение: форматировать как "DD.MM.YYYY" через `new Date().toLocaleDateString('ru-RU')`

## Acceptance Criteria Checklist

### Страница профиля (/profile)
- [ ] Новая страница `/profile` доступна для всех пользователей
- [ ] Кнопка профиля в header главной страницы (FaUser icon)
- [ ] ProfileStats отображает статистику корректно
- [ ] ProfileRecommendations показывает AI-рекомендации или placeholder
- [ ] ProfileBalance отображает баланс с прогресс-баром
- [ ] Кнопка возврата на главную работает

### Управление балансами в панели менеджера
- [ ] Новая вкладка "Балансы" в `/manager` после "Users"
- [ ] BalanceManager отображает список пользователей с балансами
- [ ] Форма редактирования лимита работает корректно
- [ ] Кнопка "Снять лимит" устанавливает weekly_limit = null
- [ ] Обновление данных после изменения (SWR mutate)

### API интеграция
- [ ] GET /users/{tgid}/recommendations работает
- [ ] GET /users/{tgid}/balance работает
- [ ] PATCH /users/{tgid}/balance/limit работает

### Дизайн и UX
- [ ] Purple gradient для активных элементов
- [ ] Dark background (#130F30)
- [ ] Responsive design для мобильных
- [ ] Loading states (skeleton placeholders)
- [ ] Error handling с информативными сообщениями
- [ ] Empty states для отсутствия данных

## Технические детали

### Дизайн-система (существующая)

**Colors:**
```typescript
background: "#130F30"
gradient: "linear-gradient(to right, #8B23CB, #A020F0)"
card: "bg-white/5 backdrop-blur-md border border-white/10"
text: "text-white"
textMuted: "text-gray-300"
```

**Icons:**
- FaUser - профиль
- FaChartLine - статистика
- FaLightbulb - рекомендации
- FaWallet - баланс
- FaArrowLeft - назад

**Layout patterns:**
```tsx
// Card
<div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
  {/* content */}
</div>

// Gradient header
<div className="flex items-center gap-3 mb-4">
  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
    <FaChartLine className="text-white text-lg" />
  </div>
  <h2 className="text-white text-xl font-bold">Статистика заказов</h2>
</div>

// Button
<button className="px-4 py-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-lg text-white font-medium hover:opacity-90 transition-opacity">
  Сохранить
</button>
```

### Progress Bar для баланса

```typescript
const getProgressColor = (percent: number) => {
  if (percent < 70) return "bg-green-500";
  if (percent < 90) return "bg-yellow-500";
  return "bg-red-500";
};

const percent = balance.weekly_limit
  ? (balance.spent_this_week / balance.weekly_limit) * 100
  : 0;

// JSX
<div className="w-full bg-gray-700 rounded-full h-2">
  <div
    className={`h-2 rounded-full transition-all ${getProgressColor(percent)}`}
    style={{ width: `${Math.min(percent, 100)}%` }}
  />
</div>
```

### Category labels mapping

```typescript
const categoryLabels: { [key: string]: string } = {
  soup: "Супы",
  salad: "Салаты",
  main: "Основное",
  extra: "Дополнительно",
  side: "Гарниры",
  drink: "Напитки",
  dessert: "Десерты"
};
```

### Date formatting

```typescript
const formatDate = (isoString: string | null) => {
  if (!isoString) return null;
  return new Date(isoString).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};
```

## Summary

**Задача:** Frontend-only реализация профиля пользователя и управления балансами.

**Подзадачи:**
1. API Layer (types.ts, hooks.ts) - **обязательно первым**
2. Profile Components (3 компонента) - **параллельно после 1**
3. Profile Page (/profile) - **параллельно после 1**
4. Balance Manager (менеджер) - **параллельно после 1**
5. Navigation Integration (кнопки) - **последним**

**Complexity:** Medium
- Много компонентов, но все по существующим паттернам
- Backend готов
- Дизайн-система готова
- Основная работа: CRUD UI + data binding

**Estimated effort:** ~4-6 hours для Coder
- API Layer: 30 min
- Profile Components: 2 hours
- Profile Page: 1 hour
- Balance Manager: 1.5 hours
- Navigation: 30 min
- Testing & fixes: 1 hour

**Next:** Передать подзадачи Coder для реализации.
