---
id: TSK-011
title: Интеграция компонентов менеджера в панель управления
pipeline: feature
status: completed
created_at: 2025-12-07T15:00:00+03:00
related_files:
  - frontend_mini_app/src/app/manager/page.tsx
  - frontend_mini_app/src/components/Manager/UserList.tsx
  - frontend_mini_app/src/components/Manager/UserForm.tsx
  - frontend_mini_app/src/components/Manager/CafeList.tsx
  - frontend_mini_app/src/components/Manager/CafeForm.tsx
  - frontend_mini_app/src/components/Manager/MenuManager.tsx
  - frontend_mini_app/src/components/Manager/ComboForm.tsx
  - frontend_mini_app/src/components/Manager/MenuItemForm.tsx
  - frontend_mini_app/src/components/Manager/RequestsList.tsx
  - frontend_mini_app/src/components/Manager/ReportsList.tsx
  - frontend_mini_app/src/lib/api/hooks.ts
impact:
  api: нет
  db: нет
  frontend: да
  services: нет
---

## Описание

Интегрировать все уже созданные компоненты менеджера в панель управления `/manager`, заменив placeholder тексты на функциональные компоненты с полной CRUD-функциональностью.

## Бизнес-контекст

### Текущее состояние

Панель менеджера (`/app/manager/page.tsx`) уже создана с табами:
- Пользователи
- Кафе
- Меню
- Запросы
- Отчёты

Но каждый таб показывает placeholder текст вместо реальных компонентов.

### Найденные компоненты

Все необходимые компоненты уже существуют в `components/Manager/`:
1. **UserList.tsx** — список пользователей с блокировкой/разблокировкой и удалением
2. **UserForm.tsx** — форма создания пользователя (предположительно существует)
3. **CafeList.tsx** — список кафе с редактированием, активацией/деактивацией и удалением
4. **CafeForm.tsx** — форма создания/редактирования кафе (предположительно существует)
5. **MenuManager.tsx** — полный менеджер меню с комбо и блюдами
6. **ComboForm.tsx** — форма комбо-набора
7. **MenuItemForm.tsx** — форма блюда
8. **RequestsList.tsx** — список запросов на подключение с approve/reject
9. **ReportsList.tsx** — список отчётов (предположительно существует)

### API хуки

Все необходимые хуки уже реализованы в `lib/api/hooks.ts`:

**Пользователи:**
- `useUsers()` — GET /users
- `useCreateUser()` — POST /users
- `useUpdateUserAccess()` — PATCH /users/{tgid}/access
- `useDeleteUser()` — DELETE /users/{tgid}

**Кафе:**
- `useCafes(shouldFetch, activeOnly)` — GET /cafes
- `useCreateCafe()` — POST /cafes
- `useUpdateCafe()` — PATCH /cafes/{id}
- `useUpdateCafeStatus()` — PATCH /cafes/{id}/status
- `useDeleteCafe()` — DELETE /cafes/{id}

**Меню:**
- `useCombos(cafeId)` — GET /cafes/{id}/combos
- `useMenu(cafeId, category?)` — GET /cafes/{id}/menu
- `useCreateCombo()`, `useUpdateCombo()`, `useDeleteCombo()`
- `useCreateMenuItem()`, `useUpdateMenuItem()`, `useDeleteMenuItem()`

**Запросы:**
- `useCafeRequests()` — GET /cafe-requests
- `useApproveCafeRequest()` — POST /cafe-requests/{id}/approve
- `useRejectCafeRequest()` — POST /cafe-requests/{id}/reject

**Отчёты:**
- `useSummaries()` — GET /summaries
- `useCreateSummary()` — POST /summaries
- `useDeleteSummary()` — DELETE /summaries/{id}

## Acceptance Criteria

### Таб "Пользователи"
- [ ] Заменить placeholder на компонент UserList
- [ ] Добавить кнопку "Добавить пользователя" над списком
- [ ] Интегрировать UserForm для создания нового пользователя (modal или inline)
- [ ] Проверить работу блокировки/разблокировки через useUpdateUserAccess
- [ ] Проверить работу удаления через useDeleteUser
- [ ] Убедиться, что после операций список обновляется (SWR mutate)

### Таб "Кафе"
- [ ] Заменить placeholder на компонент CafeList
- [ ] Добавить кнопку "Добавить кафе" над списком
- [ ] Интегрировать CafeForm для создания нового кафе (modal или inline)
- [ ] Реализовать редактирование: клик на "Редактировать" → открывает CafeForm с initialData
- [ ] Проверить работу активации/деактивации через useUpdateCafeStatus
- [ ] Проверить работу удаления через useDeleteCafe
- [ ] Убедиться, что после операций список обновляется

### Таб "Меню"
- [ ] Заменить placeholder на компонент MenuManager
- [ ] MenuManager уже содержит всю логику (комбо + блюда + формы)
- [ ] Убедиться, что выбор кафе работает корректно
- [ ] Проверить создание/редактирование/удаление комбо
- [ ] Проверить создание/редактирование/удаление блюд
- [ ] Проверить переключение доступности (is_available)

### Таб "Запросы"
- [ ] Заменить placeholder на компонент RequestsList
- [ ] RequestsList уже содержит логику approve/reject
- [ ] Убедиться, что список обновляется после approve/reject
- [ ] Проверить отображение статусов (pending, approved, rejected)
- [ ] Проверить форматирование дат

### Таб "Отчёты"
- [ ] Заменить placeholder на компонент ReportsList
- [ ] Если ReportsList не существует — создать базовый компонент
- [ ] Добавить кнопку "Создать отчёт" с формой выбора кафе и даты
- [ ] Отобразить список существующих отчётов
- [ ] Добавить кнопку удаления отчётов
- [ ] Показать детали отчёта (total_orders, total_amount, breakdowns)

### UI/UX требования
- [ ] Все компоненты используют дизайн-систему проекта (purple gradients, blur backgrounds)
- [ ] Loading states показывают skeleton placeholders или spinners
- [ ] Error states показывают red banners с текстом ошибки
- [ ] Empty states показывают серый текст "Нет данных"
- [ ] Кнопки имеют hover effects и disabled states
- [ ] Формы валидируют данные перед отправкой
- [ ] После успешных операций обновляется UI через SWR mutate

### Технические требования
- [ ] Использовать существующие компоненты из `components/Manager/`
- [ ] Использовать существующие хуки из `lib/api/hooks.ts`
- [ ] Не дублировать логику — все операции через хуки
- [ ] Сохранить текущий стиль и структуру manager/page.tsx
- [ ] Мобильная адаптивность (работает в Telegram Mini App)

## Контекст кодовой базы

### Структура manager/page.tsx

```tsx
<div className="px-4 md:px-6 py-6">
  {activeTab === "users" && (
    <div className="text-white">
      <h2 className="text-xl font-bold mb-4">Управление пользователями</h2>
      {/* СЮДА КОМПОНЕНТЫ */}
    </div>
  )}

  {activeTab === "cafes" && (
    <div className="text-white">
      <h2 className="text-xl font-bold mb-4">Управление кафе</h2>
      {/* СЮДА КОМПОНЕНТЫ */}
    </div>
  )}

  {/* ... остальные табы */}
</div>
```

### Примеры интеграции компонентов

Найденные компоненты уже правильно структурированы:

**UserList** принимает props:
```tsx
interface UserListProps {
  users: User[] | undefined;
  isLoading: boolean;
  error: Error | undefined;
  onToggleAccess: (tgid: number, newStatus: boolean) => Promise<void>;
  onDelete: (tgid: number) => Promise<void>;
}
```

**CafeList** принимает props:
```tsx
interface CafeListProps {
  onEdit?: (cafe: Cafe) => void;
}
```
И внутри использует:
```tsx
const { data: cafes, error, isLoading } = useCafes(false);
```

**MenuManager** — self-contained, не требует props:
```tsx
export default function MenuManager() {
  // Вся логика внутри
}
```

**RequestsList** — self-contained:
```tsx
const RequestsList: React.FC = () => {
  // Вся логика внутри
}
```

## Подзадачи

### Подзадача 1: Интеграция UserList + UserForm
**Файлы:** `app/manager/page.tsx`, `components/Manager/UserList.tsx`, `components/Manager/UserForm.tsx`

**Действия:**
1. Импортировать UserList и UserForm в manager/page.tsx
2. В табе "users" добавить:
   - Кнопку "Добавить пользователя"
   - State для показа/скрытия формы создания
   - Вызов хуков useUsers, useCreateUser, useUpdateUserAccess, useDeleteUser
   - Передать данные в UserList как props
3. Реализовать логику создания пользователя через UserForm
4. Проверить mutate после всех операций

**Пример кода:**
```tsx
const { data: users, error, isLoading, mutate: mutateUsers } = useUsers();
const { createUser } = useCreateUser();
const { updateAccess } = useUpdateUserAccess();
const { deleteUser } = useDeleteUser();
const [showUserForm, setShowUserForm] = useState(false);

const handleCreateUser = async (data: { tgid: number; name: string; office: string }) => {
  await createUser(data);
  mutateUsers();
  setShowUserForm(false);
};

const handleToggleAccess = async (tgid: number, newStatus: boolean) => {
  await updateAccess(tgid, newStatus);
  mutateUsers();
};

const handleDeleteUser = async (tgid: number) => {
  await deleteUser(tgid);
  mutateUsers();
};

// В JSX
<button onClick={() => setShowUserForm(true)}>Добавить пользователя</button>
{showUserForm && <UserForm onSubmit={handleCreateUser} onCancel={() => setShowUserForm(false)} />}
<UserList
  users={users}
  isLoading={isLoading}
  error={error}
  onToggleAccess={handleToggleAccess}
  onDelete={handleDeleteUser}
/>
```

### Подзадача 2: Интеграция CafeList + CafeForm
**Файлы:** `app/manager/page.tsx`, `components/Manager/CafeList.tsx`, `components/Manager/CafeForm.tsx`

**Действия:**
1. Импортировать CafeList и CafeForm
2. В табе "cafes" добавить:
   - Кнопку "Добавить кафе"
   - State для показа формы создания и редактирования
   - State для хранения редактируемого кафе
   - Вызов хуков useCreateCafe, useUpdateCafe
3. CafeList уже использует useCafes внутри, но нужно обработать callback onEdit
4. Проверить mutate после операций

**Пример кода:**
```tsx
const [showCafeForm, setShowCafeForm] = useState(false);
const [editingCafe, setEditingCafe] = useState<Cafe | null>(null);
const { createCafe } = useCreateCafe();
const { updateCafe } = useUpdateCafe();

const handleCreateCafe = async (data: { name: string; description?: string }) => {
  await createCafe(data);
  setShowCafeForm(false);
};

const handleUpdateCafe = async (data: { name: string; description?: string }) => {
  if (!editingCafe) return;
  await updateCafe(editingCafe.id, data);
  setEditingCafe(null);
};

// В JSX
<button onClick={() => setShowCafeForm(true)}>Добавить кафе</button>
{showCafeForm && <CafeForm mode="create" onSubmit={handleCreateCafe} onCancel={() => setShowCafeForm(false)} />}
{editingCafe && <CafeForm mode="edit" initialData={editingCafe} onSubmit={handleUpdateCafe} onCancel={() => setEditingCafe(null)} />}
<CafeList onEdit={(cafe) => setEditingCafe(cafe)} />
```

### Подзадача 3: Интеграция MenuManager
**Файлы:** `app/manager/page.tsx`, `components/Manager/MenuManager.tsx`

**Действия:**
1. Импортировать MenuManager
2. В табе "menu" заменить placeholder на `<MenuManager />`
3. Компонент полностью self-contained, не требует props
4. Проверить, что все формы (ComboForm, MenuItemForm) работают

**Пример кода:**
```tsx
{activeTab === "menu" && (
  <div className="text-white">
    <h2 className="text-xl font-bold mb-4">Управление меню</h2>
    <MenuManager />
  </div>
)}
```

### Подзадача 4: Интеграция RequestsList
**Файлы:** `app/manager/page.tsx`, `components/Manager/RequestsList.tsx`

**Действия:**
1. Импортировать RequestsList
2. В табе "requests" заменить placeholder на `<RequestsList />`
3. Компонент self-contained
4. Проверить работу approve/reject

**Пример кода:**
```tsx
{activeTab === "requests" && (
  <div className="text-white">
    <h2 className="text-xl font-bold mb-4">Запросы на подключение</h2>
    <RequestsList />
  </div>
)}
```

### Подзадача 5: Создание/интеграция ReportsList
**Файлы:** `app/manager/page.tsx`, `components/Manager/ReportsList.tsx`

**Действия:**
1. Проверить существование ReportsList.tsx
2. Если компонент не существует — создать его по аналогии с другими списками
3. Использовать хуки useSummaries, useCreateSummary, useDeleteSummary
4. Добавить форму создания отчёта (выбор кафе + дата)
5. Отобразить детали отчёта

**Структура компонента (если нужно создать):**
```tsx
const ReportsList: React.FC = () => {
  const { data: summaries, error, isLoading } = useSummaries();
  const { createSummary } = useCreateSummary();
  const { deleteSummary } = useDeleteSummary();
  const [showForm, setShowForm] = useState(false);

  const handleCreate = async (cafeId: number, date: string) => {
    await createSummary(cafeId, date);
    mutate("/summaries");
    setShowForm(false);
  };

  const handleDelete = async (summaryId: number) => {
    if (!confirm("Удалить отчёт?")) return;
    await deleteSummary(summaryId);
    mutate("/summaries");
  };

  return (
    <div>
      <button onClick={() => setShowForm(true)}>Создать отчёт</button>
      {/* Форма создания */}
      {/* Список отчётов с деталями */}
    </div>
  );
};
```

## Технические детали

### Дизайн-система

Все компоненты уже используют правильные стили:
- Background: `bg-white/5 backdrop-blur-md`
- Borders: `border border-white/10`
- Buttons: `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- Hover: `hover:bg-white/10`
- Text: `text-white`, `text-gray-300`, `text-gray-400`

### State Management

Все данные управляются через SWR:
- Автоматический кэш
- Revalidation on focus
- Ручное обновление через `mutate()`

### Error Handling

Уже реализовано в компонентах:
```tsx
if (error) {
  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
      <p className="text-red-400 text-sm">Ошибка: {error.message}</p>
    </div>
  );
}
```

### Loading States

Уже реализовано:
```tsx
if (isLoading) {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white/5 p-4 rounded-lg animate-pulse">
          <div className="h-5 bg-white/10 rounded w-1/3"></div>
        </div>
      ))}
    </div>
  );
}
```

## Архитектурные решения

1. **Компоненты уже созданы** — задача только интегрировать их
2. **Self-contained компоненты** — MenuManager, RequestsList не требуют props
3. **Props-based компоненты** — UserList требует передачи данных
4. **Формы как модалы** — можно использовать conditional rendering (показывать/скрывать)
5. **SWR для синхронизации** — после операций вызывать mutate()

## Риски и решения

### Риск: Компонент ReportsList не существует
**Решение:** Создать базовый компонент по аналогии с другими списками

### Риск: Формы (UserForm, CafeForm) могут не существовать
**Решение:** Проверить наличие, если нет — создать inline формы в manager/page.tsx или использовать простые prompt/confirm

### Риск: Конфликты стилей
**Решение:** Все компоненты уже используют одинаковую дизайн-систему

### Риск: Производительность на больших списках
**Решение:** SWR кэширует данные, skeleton loading улучшает UX

## Примечания

- Все API endpoints уже реализованы и работают
- Все хуки уже созданы и протестированы
- Компоненты следуют единой дизайн-системе
- Telegram Mini App работает только в мобильном разрешении
- Менеджер может переключаться между `/manager` и `/` (пользовательский интерфейс)

## Дополнительные возможности (опционально)

- [ ] Поиск пользователей (фильтр по имени/tgid)
- [ ] Пагинация для больших списков
- [ ] Экспорт отчётов в CSV/PDF
- [ ] Подтверждающие toast уведомления вместо alert()
- [ ] Анимации при добавлении/удалении элементов списка
