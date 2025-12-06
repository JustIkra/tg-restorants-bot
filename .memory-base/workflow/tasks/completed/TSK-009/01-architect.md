---
agent: architect
task_id: TSK-009
status: completed
next: coder
created_at: 2025-12-06T21:45:00+03:00
files_changed: []
---

# Архитектурное решение: UI для менеджера

## Анализ текущей системы

### Существующая структура

**Frontend:**
- `frontend_mini_app/src/app/page.tsx` — главная страница для обычных пользователей (выбор кафе, меню, заказ)
- `frontend_mini_app/src/app/layout.tsx` — root layout
- `frontend_mini_app/src/app/order/page.tsx` — страница оформления заказа
- `frontend_mini_app/src/app/FortuneWheel/page.tsx` — колесо фортуны

**API Client:**
- `frontend_mini_app/src/lib/api/client.ts` — JWT аутентификация через `authenticateWithTelegram()`
- `frontend_mini_app/src/lib/api/types.ts` — TypeScript типы (User с полем `role: "user" | "manager"`)
- `frontend_mini_app/src/lib/api/hooks.ts` — SWR hooks для кафе, меню, комбо, заказов

**Компоненты:**
- `CafeSelector` — выбор кафе (переиспользуемый)
- `CategorySelector` — выбор категории (переиспользуемый)
- `MenuSection` — отображение списка блюд
- `DishModal` — модальное окно с деталями блюда

### Проблемы

1. **Нет разделения интерфейсов** — менеджер видит тот же UI что и обычный пользователь
2. **Нет административных операций** — создание/редактирование кафе, меню, пользователей доступно только через API
3. **Нет редиректа на основе роли** — после авторизации все идут на `/`

### Backend API для менеджера

Все необходимые endpoints уже реализованы:

**Пользователи** (manager only):
- GET /users — список
- POST /users — создать
- PATCH /users/{tgid}/access — блокировка/разблокировка
- DELETE /users/{tgid} — удалить

**Кафе** (manager only):
- POST /cafes — создать
- PATCH /cafes/{cafe_id} — редактировать
- DELETE /cafes/{cafe_id} — удалить
- PATCH /cafes/{cafe_id}/status — активация/деактивация

**Меню** (manager only):
- POST /cafes/{cafe_id}/combos — создать комбо
- PATCH /cafes/{cafe_id}/combos/{combo_id} — редактировать
- DELETE /cafes/{cafe_id}/combos/{combo_id} — удалить
- POST /cafes/{cafe_id}/menu — создать блюдо
- PATCH /cafes/{cafe_id}/menu/{item_id} — редактировать
- DELETE /cafes/{cafe_id}/menu/{item_id} — удалить

**Запросы на подключение** (manager only):
- GET /cafe-requests — список
- POST /cafe-requests/{request_id}/approve — одобрить
- POST /cafe-requests/{request_id}/reject — отклонить

**Отчёты** (manager only):
- GET /summaries — список
- POST /summaries — создать
- GET /summaries/{summary_id} — детали
- DELETE /summaries/{summary_id} — удалить

---

## Архитектурное решение

### 1. Разделение на уровне роутинга

**Пользовательский интерфейс:**
- `/` — главная страница (выбор кафе, меню, заказ)
- `/order` — оформление заказа
- `/FortuneWheel` — колесо фортуны

**Менеджерский интерфейс:**
- `/manager` — панель управления с табами для разных секций

### 2. Редирект на основе роли

После успешной аутентификации через Telegram:
1. Получить `user.role` из ответа `/auth/telegram`
2. Если `role === "manager"` → редирект на `/manager`
3. Если `role === "user"` → остаться на `/`

**Защита роутов:**
- `/manager` — проверка роли при загрузке, если `role !== "manager"` → редирект на `/`
- `/` — проверка роли, если `role === "manager"` → редирект на `/manager`

### 3. Одностраничный подход с табами

Вместо создания множества отдельных страниц (`/manager/users`, `/manager/cafes`, etc.) используем одностраничное приложение с табами (вкладками). Это оптимально для мобильного разрешения Telegram Mini App.

**Структура:**
```
/manager
  └── page.tsx (панель с табами)
```

**Табы:**
1. **Пользователи** — список, добавление, блокировка/разблокировка
2. **Кафе** — список, добавление, редактирование, активация/деактивация
3. **Меню** — выбор кафе → управление комбо и блюдами
4. **Запросы** — список запросов на подключение кафе, approve/reject
5. **Отчёты** — просмотр отчётов по кафе и датам

### 4. Переиспользование компонентов

**Существующие компоненты:**
- `CafeSelector` — можно использовать в разделе "Меню" для выбора кафе
- Дизайн-система (purple gradients, blur backgrounds, button styles) — применить ко всем менеджерским компонентам

**Новые компоненты:**
- `ManagerLayout` — wrapper с навигацией по табам
- `UserList` — таблица пользователей с действиями
- `UserForm` — форма создания пользователя
- `CafeList` — таблица кафе с действиями
- `CafeForm` — форма создания/редактирования кафе
- `MenuManager` — управление меню (комбо + блюда) для выбранного кафе
- `ComboForm` — форма создания/редактирования комбо
- `MenuItemForm` — форма создания/редактирования блюда
- `RequestsList` — список запросов на подключение
- `ReportsList` — список отчётов

### 5. State management

**SWR для автоматической синхронизации:**
- При создании/обновлении/удалении → вызывать `mutate()` для обновления списков
- Кеширование через SWR — не нужно перезагружать данные при переключении табов

**Новые hooks:**
```typescript
// Пользователи
useUsers() → GET /users
useCreateUser() → POST /users
useUpdateUserAccess() → PATCH /users/{tgid}/access
useDeleteUser() → DELETE /users/{tgid}

// Кафе
useCreateCafe() → POST /cafes
useUpdateCafe() → PATCH /cafes/{cafe_id}
useDeleteCafe() → DELETE /cafes/{cafe_id}
useUpdateCafeStatus() → PATCH /cafes/{cafe_id}/status

// Меню
useCreateCombo() → POST /cafes/{cafe_id}/combos
useUpdateCombo() → PATCH /cafes/{cafe_id}/combos/{combo_id}
useDeleteCombo() → DELETE /cafes/{cafe_id}/combos/{combo_id}
useCreateMenuItem() → POST /cafes/{cafe_id}/menu
useUpdateMenuItem() → PATCH /cafes/{cafe_id}/menu/{item_id}
useDeleteMenuItem() → DELETE /cafes/{cafe_id}/menu/{item_id}

// Запросы на подключение
useCafeRequests() → GET /cafe-requests
useApproveCafeRequest() → POST /cafe-requests/{request_id}/approve
useRejectCafeRequest() → POST /cafe-requests/{request_id}/reject

// Отчёты
useSummaries() → GET /summaries
useCreateSummary() → POST /summaries
useDeleteSummary() → DELETE /summaries/{summary_id}
```

### 6. UI/UX дизайн

**Дизайн-система:**
- Background: `#130F30`
- Purple gradient: `from-[#8B23CB] to-[#A020F0]`
- Cards: `bg-white/5 backdrop-blur-md border border-white/10`
- Active states: gradient shift animation
- Hover: `opacity` и `scale` transitions

**Навигация (табы):**
- Горизонтальный scroll для табов (для мобильного разрешения)
- Активный таб — gradient background + white text
- Неактивный таб — gray text + transparent background

**Таблицы:**
- Карточки вместо таблиц (лучше для мобильного)
- Каждая строка — отдельная карточка с `bg-white/5`
- Действия (редактировать, удалить, блокировать) — кнопки справа

**Формы:**
- Модальные окна или inline формы (зависит от раздела)
- Input fields: `bg-white/10 border border-white/20 text-white`
- Submit button: gradient `from-[#8B23CB] to-[#A020F0]`

**Loading states:**
- Skeleton loaders вместо спиннеров (где возможно)
- Spinner + текст для критических операций

**Error handling:**
- Toast notifications для успеха/ошибки
- 403 Forbidden → показать alert + редирект на `/`
- 401 Unauthorized → удалить токен + перезагрузка

### 7. Мобильная оптимизация

Telegram Mini App работает только в мобильном разрешении:
- Минимальная ширина кнопок: 44px
- Touch-friendly элементы (не слишком маленькие)
- Использовать вертикальный scroll вместо горизонтального (кроме табов)
- Формы — stackable inputs (один под другим)
- Модальные окна — на весь экран (для форм создания/редактирования)

---

## Подзадачи для Coder

Разбиваем реализацию на **7 параллельных подзадач** для ускорения разработки. Все подзадачи работают с разными файлами и не имеют конфликтов.

### Подзадача 1: Обновление авторизации с редиректом по ролям

**Файлы:**
- `frontend_mini_app/src/app/page.tsx`

**Действия:**
1. Модифицировать `useEffect` с авторизацией:
   - После успешного `authenticateWithTelegram()` проверить `response.user.role`
   - Если `role === "manager"` → `router.push("/manager")`
   - Иначе — остаться на `/`
2. Сохранить `user` объект в localStorage или Context для доступа на других страницах

**Результат:**
- Менеджер автоматически редиректится на `/manager` после авторизации

---

### Подзадача 2: Создание страницы `/manager` с табами

**Файлы:**
- `frontend_mini_app/src/app/manager/page.tsx` (создать)

**Действия:**
1. Создать компонент `ManagerPage` с авторизацией:
   - Проверка роли: если `role !== "manager"` → редирект на `/`
   - Показывать loading state во время авторизации
2. Реализовать табы (state: `activeTab: "users" | "cafes" | "menu" | "requests" | "reports"`)
3. Навигация табов — горизонтальный scroll с gradient кнопками
4. Рендерить контент в зависимости от `activeTab`
5. Placeholder контент для каждого таба (заполнят другие подзадачи)

**Результат:**
- Страница `/manager` с переключением между табами

---

### Подзадача 3: API hooks для менеджера

**Файлы:**
- `frontend_mini_app/src/lib/api/hooks.ts` (дополнить)
- `frontend_mini_app/src/lib/api/types.ts` (дополнить при необходимости)

**Действия:**
1. Создать hooks для управления пользователями:
   - `useUsers()` → GET /users
   - `useCreateUser()` → POST /users
   - `useUpdateUserAccess()` → PATCH /users/{tgid}/access
   - `useDeleteUser()` → DELETE /users/{tgid}

2. Создать hooks для управления кафе:
   - `useCreateCafe()` → POST /cafes
   - `useUpdateCafe()` → PATCH /cafes/{cafe_id}
   - `useDeleteCafe()` → DELETE /cafes/{cafe_id}
   - `useUpdateCafeStatus()` → PATCH /cafes/{cafe_id}/status

3. Создать hooks для управления меню:
   - `useCreateCombo()` → POST /cafes/{cafe_id}/combos
   - `useUpdateCombo()` → PATCH /cafes/{cafe_id}/combos/{combo_id}
   - `useDeleteCombo()` → DELETE /cafes/{cafe_id}/combos/{combo_id}
   - `useCreateMenuItem()` → POST /cafes/{cafe_id}/menu
   - `useUpdateMenuItem()` → PATCH /cafes/{cafe_id}/menu/{item_id}
   - `useDeleteMenuItem()` → DELETE /cafes/{cafe_id}/menu/{item_id}

4. Создать hooks для запросов на подключение:
   - `useCafeRequests()` → GET /cafe-requests
   - `useApproveCafeRequest()` → POST /cafe-requests/{request_id}/approve
   - `useRejectCafeRequest()` → POST /cafe-requests/{request_id}/reject

5. Создать hooks для отчётов:
   - `useSummaries()` → GET /summaries
   - `useCreateSummary()` → POST /summaries
   - `useDeleteSummary()` → DELETE /summaries/{summary_id}

**Результат:**
- Полный набор hooks для менеджерских операций

---

### Подзадача 4: Компоненты для управления пользователями

**Файлы:**
- `frontend_mini_app/src/components/Manager/UserList.tsx` (создать)
- `frontend_mini_app/src/components/Manager/UserForm.tsx` (создать)

**Действия:**
1. `UserList` компонент:
   - Использовать `useUsers()` hook
   - Отобразить список пользователей в виде карточек
   - Каждая карточка: имя, tgid, office, статус (active/blocked)
   - Кнопки: "Заблокировать"/"Разблокировать", "Удалить"
   - Loading state, error handling

2. `UserForm` компонент:
   - Форма создания пользователя: tgid, name, office
   - Submit → `useCreateUser()`
   - Валидация (tgid обязателен, name обязателен)
   - После успеха — обновить список (`mutate()`)

**Результат:**
- Готовые компоненты для управления пользователями
- Интегрировать в `/manager` → таб "Пользователи"

---

### Подзадача 5: Компоненты для управления кафе

**Файлы:**
- `frontend_mini_app/src/components/Manager/CafeList.tsx` (создать)
- `frontend_mini_app/src/components/Manager/CafeForm.tsx` (создать)

**Действия:**
1. `CafeList` компонент:
   - Использовать `useCafes(false)` hook (все кафе, не только активные)
   - Отобразить список кафе в виде карточек
   - Каждая карточка: название, описание, статус (active/inactive)
   - Кнопки: "Редактировать", "Активировать"/"Деактивировать", "Удалить"

2. `CafeForm` компонент:
   - Форма создания/редактирования: name, description
   - Поддержка двух режимов: create (POST /cafes) и edit (PATCH /cafes/{id})
   - Валидация (name обязателен)
   - После успеха — обновить список

**Результат:**
- Готовые компоненты для управления кафе
- Интегрировать в `/manager` → таб "Кафе"

---

### Подзадача 6: Компоненты для управления меню

**Файлы:**
- `frontend_mini_app/src/components/Manager/MenuManager.tsx` (создать)
- `frontend_mini_app/src/components/Manager/ComboForm.tsx` (создать)
- `frontend_mini_app/src/components/Manager/MenuItemForm.tsx` (создать)

**Действия:**
1. `MenuManager` компонент:
   - Выбор кафе через `CafeSelector` (переиспользовать существующий)
   - После выбора кафе → показать две секции:
     - **Комбо-наборы**: список комбо с кнопками "Редактировать", "Удалить", "Доступность"
     - **Блюда**: список блюд с кнопками "Редактировать", "Удалить", "Доступность"
   - Кнопка "Добавить комбо" → открыть `ComboForm`
   - Кнопка "Добавить блюдо" → открыть `MenuItemForm`

2. `ComboForm` компонент:
   - Форма: name, categories (multiselect), price
   - Режимы: create / edit
   - Валидация

3. `MenuItemForm` компонент:
   - Форма: name, description, category (select), price
   - Режимы: create / edit
   - Валидация

**Результат:**
- Готовые компоненты для управления меню
- Интегрировать в `/manager` → таб "Меню"

---

### Подзадача 7: Компоненты для запросов и отчётов

**Файлы:**
- `frontend_mini_app/src/components/Manager/RequestsList.tsx` (создать)
- `frontend_mini_app/src/components/Manager/ReportsList.tsx` (создать)

**Действия:**
1. `RequestsList` компонент:
   - Использовать `useCafeRequests()` hook
   - Отобразить список запросов на подключение
   - Каждая карточка: название кафе, статус (pending/approved/rejected)
   - Кнопки: "Одобрить", "Отклонить" (для pending запросов)

2. `ReportsList` компонент:
   - Использовать `useSummaries()` hook
   - Отобразить список отчётов
   - Каждая карточка: дата, кафе, ссылка на детали
   - Кнопка "Создать отчёт" → форма выбора даты и кафе
   - Кнопка "Удалить" для каждого отчёта

**Результат:**
- Готовые компоненты для запросов и отчётов
- Интегрировать в `/manager` → табы "Запросы" и "Отчёты"

---

## Порядок выполнения

**Параллельные подзадачи** (можно выполнять одновременно):
- Подзадача 3 (API hooks)
- Подзадача 4 (Пользователи)
- Подзадача 5 (Кафе)
- Подзадача 6 (Меню)
- Подзадача 7 (Запросы и отчёты)

**Последовательные подзадачи** (зависимости):
1. Подзадача 1 (Авторизация с редиректом) — **первая**
2. Подзадача 2 (Страница /manager) — после подзадачи 1
3. Подзадачи 4-7 интегрируются в подзадачу 2 (заполняют табы)

**Финальная интеграция:**
- После завершения всех подзадач — объединить компоненты в `/manager/page.tsx`
- Тестирование всех операций

---

## Риски и зависимости

### Риски

1. **Конфликт стилей** — новые компоненты могут не совпадать с дизайн-системой
   - **Митигация:** использовать существующие стили из `CafeSelector`, `CategorySelector`

2. **Производительность с большими списками** — медленная прокрутка при 1000+ пользователей/блюд
   - **Митигация:** добавить пагинацию или виртуальный scroll (в будущем)

3. **Сложность форм** — создание комбо требует выбора категорий (multiselect)
   - **Митигация:** использовать простой UI с чекбоксами для категорий

4. **Error handling** — 403 ошибка должна корректно обрабатываться
   - **Митигация:** централизованный обработчик ошибок в `apiRequest()`

### Зависимости

- **Backend API** — все endpoints уже реализованы, нет блокеров
- **Авторизация** — JWT токен уже работает, нужно только добавить проверку роли
- **SWR** — уже используется в проекте, можно расширить hooks

---

## Дополнительные возможности (не в текущем scope)

Эти возможности можно добавить в будущем:
- Поиск по пользователям/кафе/блюдам
- Фильтры (активные/неактивные, по ролям)
- Массовые операции (выбрать несколько → деактивировать)
- Экспорт отчётов в CSV/PDF
- История изменений (audit log)
- Dashboard с аналитикой

---

## Итоговая структура файлов

```
frontend_mini_app/src/
├── app/
│   ├── page.tsx (обновлён: редирект для менеджера)
│   ├── manager/
│   │   └── page.tsx (новый: панель менеджера с табами)
│   └── ...
├── components/
│   ├── Manager/
│   │   ├── UserList.tsx (новый)
│   │   ├── UserForm.tsx (новый)
│   │   ├── CafeList.tsx (новый)
│   │   ├── CafeForm.tsx (новый)
│   │   ├── MenuManager.tsx (новый)
│   │   ├── ComboForm.tsx (новый)
│   │   ├── MenuItemForm.tsx (новый)
│   │   ├── RequestsList.tsx (новый)
│   │   └── ReportsList.tsx (новый)
│   └── ...
└── lib/
    └── api/
        └── hooks.ts (дополнен: новые hooks для менеджера)
```

---

## Заключение

Архитектурное решение использует одностраничный подход с табами для оптимального UX на мобильных устройствах. Все административные операции будут доступны через понятный интерфейс с переиспользованием существующих компонентов и дизайн-системы.

Разбивка на 7 параллельных подзадач позволит быстро реализовать функционал без конфликтов в коде.
