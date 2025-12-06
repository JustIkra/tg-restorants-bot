---
id: TSK-009
title: Отдельная команда и UI для функционала менеджера
pipeline: feature
status: pending
created_at: 2025-12-06T21:30:00+03:00
related_files:
  - frontend_mini_app/src/app/page.tsx
  - frontend_mini_app/src/app/layout.tsx
  - frontend_mini_app/src/lib/api/client.ts
  - frontend_mini_app/src/lib/api/types.ts
  - frontend_mini_app/src/lib/api/hooks.ts
  - backend/src/auth/dependencies.py
  - backend/src/routers/users.py
  - backend/src/routers/cafes.py
  - backend/src/routers/menu.py
  - backend/src/routers/summaries.py
  - backend/src/routers/cafe_links.py
impact:
  api: нет
  db: нет
  frontend: да
  services: нет
---

## Описание

Создать отдельную команду бота и UI-интерфейс для менеджера, который позволит выполнять административные задачи без использования основного интерфейса для сотрудников.

## Бизнес-контекст

Сейчас существует два типа пользователей:
1. **Сотрудник** (role: "user") — делает заказы через Telegram Mini App
2. **Менеджер** (role: "manager") — управляет меню, пользователями, получает отчёты

### Текущая проблема

- Менеджер использует тот же UI что и обычные сотрудники (главная страница `page.tsx`)
- Административные функции недоступны через UI (только через API)
- Нет отдельной команды бота для быстрого доступа к менеджерской панели

### Требуемое решение

1. **Отдельная команда бота** — `/manager` или кнопка "Панель менеджера"
2. **Отдельный UI-роут** — `/manager` с административным интерфейсом
3. **Разделение интерфейсов** — обычные пользователи не должны видеть менеджерские функции

## Acceptance Criteria

### Backend (минимально)
- [ ] Проверить, что все необходимые API endpoints уже реализованы (они уже есть)
- [ ] Убедиться, что роль пользователя передаётся в JWT и доступна на frontend

### Frontend
- [ ] Создать новую страницу `/manager` (app/manager/page.tsx)
- [ ] Добавить проверку роли пользователя при авторизации
- [ ] Реализовать редирект: user → `/` (главная), manager → `/manager` (панель)
- [ ] Создать менеджерский UI с разделами:
  - **Управление пользователями** — список, добавление, блокировка/разблокировка
  - **Управление кафе** — список, добавление, активация/деактивация
  - **Управление меню** — выбор кафе, список комбо/блюд, добавление, редактирование, доступность
  - **Запросы на подключение** — список запросов от кафе, approve/reject
  - **Отчёты** — просмотр отчётов по кафе и датам
- [ ] Добавить навигацию между разделами (вкладки или боковое меню)
- [ ] Использовать дизайн-систему проекта (purple градиенты, blur backgrounds)
- [ ] Добавить loading states и error handling
- [ ] Мобильная адаптивность (приложение работает в Telegram)

### API Integration
- [ ] Создать хуки для менеджерских операций:
  - `useUsers()`, `useCreateUser()`, `useUpdateUserAccess()`
  - `useCreateCafe()`, `useUpdateCafeStatus()`
  - `useCreateCombo()`, `useUpdateCombo()`, `useCreateMenuItem()`, `useUpdateMenuItem()`
  - `useCafeRequests()`, `useApproveCafeRequest()`, `useRejectCafeRequest()`
  - `useSummaries()`, `useCreateSummary()`
- [ ] Обработать 403 ошибку (недостаточно прав) → показать сообщение и редирект

### User Flow
```
1. Менеджер открывает бот
2. Авторизация через Telegram
3. Backend возвращает user.role = "manager"
4. Редирект на /manager
5. Менеджер видит панель с разделами
6. Выбирает раздел (например, "Управление меню")
7. Выполняет операции (добавляет блюдо, меняет цену, деактивирует)
8. Изменения сразу применяются и видны через SWR revalidation
```

## Контекст кодовой базы

### API Endpoints для менеджера (уже реализованы)

**Пользователи:**
- `GET /users` — список пользователей (manager only)
- `POST /users` — создать пользователя (manager only)
- `POST /users/managers` — создать менеджера (manager only)
- `PATCH /users/{tgid}/access` — блокировать/разблокировать (manager only)
- `DELETE /users/{tgid}` — удалить пользователя (manager only)

**Кафе:**
- `GET /cafes` — список кафе (user + manager)
- `POST /cafes` — создать кафе (manager only)
- `PATCH /cafes/{cafe_id}` — редактировать кафе (manager only)
- `DELETE /cafes/{cafe_id}` — удалить кафе (manager only)
- `PATCH /cafes/{cafe_id}/status` — активировать/деактивировать (manager only)

**Меню:**
- `GET /cafes/{cafe_id}/combos` — список комбо (user + manager)
- `POST /cafes/{cafe_id}/combos` — создать комбо (manager only)
- `PATCH /cafes/{cafe_id}/combos/{combo_id}` — редактировать комбо (manager only)
- `DELETE /cafes/{cafe_id}/combos/{combo_id}` — удалить комбо (manager only)
- `GET /cafes/{cafe_id}/menu` — список блюд (user + manager)
- `POST /cafes/{cafe_id}/menu` — создать блюдо (manager only)
- `PATCH /cafes/{cafe_id}/menu/{item_id}` — редактировать блюдо (manager only)
- `DELETE /cafes/{cafe_id}/menu/{item_id}` — удалить блюдо (manager only)

**Запросы на подключение:**
- `GET /cafe-requests` — список запросов (manager only)
- `POST /cafe-requests/{request_id}/approve` — одобрить (manager only)
- `POST /cafe-requests/{request_id}/reject` — отклонить (manager only)

**Отчёты:**
- `GET /summaries` — список отчётов (manager only)
- `POST /summaries` — создать отчёт (manager only)
- `GET /summaries/{summary_id}` — детали отчёта (manager only)
- `DELETE /summaries/{summary_id}` — удалить отчёт (manager only)

### Авторизация

- Backend возвращает `User` объект с полем `role: "user" | "manager"`
- JWT токен содержит `tgid`, по которому backend определяет роль
- Frontend проверяет роль после авторизации и делает редирект

**Существующие файлы:**
- `backend/src/auth/dependencies.py` — `require_manager()` dependency
- `frontend_mini_app/src/lib/api/client.ts` — `authenticateWithTelegram()` функция
- `frontend_mini_app/src/lib/api/types.ts` — `User` interface

### Текущая структура frontend

```
frontend_mini_app/src/app/
├── page.tsx              # Главная страница (для users)
├── layout.tsx            # Root layout
├── order/page.tsx        # Страница оформления заказа
└── FortuneWheel/page.tsx # Колесо фортуны
```

**Добавить:**
```
frontend_mini_app/src/app/
└── manager/
    ├── page.tsx          # Главная панель менеджера с навигацией
    ├── users/page.tsx    # Управление пользователями
    ├── cafes/page.tsx    # Управление кафе
    ├── menu/page.tsx     # Управление меню
    ├── requests/page.tsx # Запросы на подключение
    └── reports/page.tsx  # Отчёты
```

**ИЛИ использовать одностраничный подход:**
```
frontend_mini_app/src/app/manager/
└── page.tsx              # Вся функциональность на одной странице с вкладками
```

### Дизайн-система

**Цвета:**
- Background: `#130F30`
- Purple accent: `#A020F0`, `#8B23CB`
- Cards: `rgba(255, 255, 255, 0.05)` + `backdrop-blur-md`
- Text: `white`, `gray-300`

**Компоненты стиля:**
- Gradient buttons: `from-[#8B23CB] to-[#A020F0]`
- Blur backgrounds: `backdrop-blur-md` + `bg-white/5`
- Borders: `border-white/10`

**Анимации:**
- Gradient shift на активных элементах
- Hover effects на кнопках

### TypeScript типы

Все типы уже определены в `frontend_mini_app/src/lib/api/types.ts`:
- `User`, `Cafe`, `Combo`, `MenuItem`, `Order`
- `ListResponse<T>`
- Request/response schemas

## Технические детали

### Роутинг и редирект

```typescript
// app/page.tsx (главная страница для users)
useEffect(() => {
  const initData = getTelegramInitData();
  if (initData) {
    authenticateWithTelegram(initData)
      .then((response) => {
        setIsAuthenticated(true);
        // Редирект для менеджера
        if (response.user.role === "manager") {
          router.push("/manager");
        }
      })
      .catch(err => setAuthError(err.message));
  }
}, []);
```

```typescript
// app/manager/page.tsx (панель менеджера)
useEffect(() => {
  const initData = getTelegramInitData();
  if (initData) {
    authenticateWithTelegram(initData)
      .then((response) => {
        if (response.user.role !== "manager") {
          // Обычный пользователь пытается зайти — редирект на главную
          router.push("/");
        }
        setIsAuthenticated(true);
      })
      .catch(err => setAuthError(err.message));
  }
}, []);
```

### Примеры UI компонентов

**Список пользователей:**
```typescript
const { data: users, error, isLoading } = useUsers();

return (
  <div className="space-y-4">
    {users?.map(user => (
      <div key={user.tgid} className="bg-white/5 p-4 rounded-lg border border-white/10">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-white font-semibold">{user.name}</p>
            <p className="text-gray-400 text-sm">@{user.tgid}</p>
            <p className="text-gray-400 text-sm">{user.office}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => toggleUserAccess(user.tgid, !user.is_active)}
              className={user.is_active ? "bg-red-500" : "bg-green-500"}
            >
              {user.is_active ? "Заблокировать" : "Разблокировать"}
            </button>
          </div>
        </div>
      </div>
    ))}
  </div>
);
```

**Управление меню:**
```typescript
const [selectedCafe, setSelectedCafe] = useState<number | null>(null);
const { data: menuItems } = useMenu(selectedCafe);

return (
  <div>
    <CafeSelector cafes={cafes} activeCafeId={selectedCafe} onCafeClick={setSelectedCafe} />

    {selectedCafe && (
      <div className="mt-6">
        <button onClick={() => setShowAddForm(true)}>Добавить блюдо</button>

        {menuItems?.map(item => (
          <div key={item.id} className="flex justify-between items-center p-4">
            <div>
              <p className="text-white">{item.name}</p>
              <p className="text-gray-400">{item.category}</p>
              <p className="text-gray-400">{item.price} ₽</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => editItem(item)}>Редактировать</button>
              <button onClick={() => deleteItem(item.id)}>Удалить</button>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);
```

## Архитектурные решения

1. **Разделение интерфейсов на уровне роутинга:**
   - `/` — для users
   - `/manager` — для managers
   - Редирект на основе `user.role` после авторизации

2. **Переиспользование компонентов:**
   - `CafeSelector`, `CategorySelector` можно использовать в менеджерском UI
   - Создать новые компоненты для CRUD операций (UserList, MenuItemForm, etc.)

3. **State management:**
   - SWR для автоматической синхронизации данных
   - При создании/обновлении — вызывать `mutate()` для обновления списков

4. **Error handling:**
   - 403 Forbidden → показать "У вас нет доступа" и редирект
   - 401 Unauthorized → удалить токен и предложить перезайти
   - Остальные ошибки → показать toast или alert

5. **Мобильная оптимизация:**
   - Использовать вкладки вместо бокового меню
   - Адаптивные формы (stackable inputs)
   - Touch-friendly кнопки (min 44px height)

## Примечания

- API для менеджера уже реализовано, нужна только frontend интеграция
- Можно использовать готовые компоненты из существующего UI (CafeSelector, категории, кнопки)
- Telegram Mini App работает только в мобильном разрешении, учесть это в дизайне
- Все операции должны быть доступны без выхода из приложения

## Дополнительные возможности (опционально)

- [ ] Поиск пользователей/кафе/блюд
- [ ] Фильтры (активные/неактивные, по ролям)
- [ ] Массовые операции (выбрать несколько → деактивировать)
- [ ] Экспорт отчётов в CSV/PDF
- [ ] История изменений (кто и когда изменил меню)
- [ ] Dashboard с статистикой (количество заказов, активных пользователей, etc.)

## Риски

- **Нет UX-дизайна:** придётся придумывать UI самостоятельно, ориентируясь на текущий стиль
- **Мобильное разрешение:** сложно уместить много информации на маленьком экране
- **Производительность:** большие списки пользователей/блюд могут тормозить — нужна пагинация

## Решения для рисков

- Использовать минималистичный дизайн с иконками
- Реализовать виртуальную прокрутку или пагинацию для больших списков
- Добавить скелетоны (loading skeletons) вместо спиннеров
