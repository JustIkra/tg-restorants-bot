---
agent: coder
task_id: TSK-009
subtask: 4
subtask_name: "Компоненты Users"
status: completed
next: null
created_at: 2025-12-06T22:00:00+03:00
files_changed:
  - path: frontend_mini_app/src/components/Manager/UserList.tsx
    action: created
  - path: frontend_mini_app/src/components/Manager/UserForm.tsx
    action: created
---

## Реализация

Созданы два компонента для управления пользователями в менеджерской панели:

### 1. UserList.tsx

**Функциональность:**
- Отображает список пользователей в виде карточек
- Показывает информацию: имя, Telegram ID, офис, роль, статус (активен/заблокирован)
- Кнопки управления:
  - "Заблокировать"/"Разблокировать" — переключение статуса `is_active`
  - "Удалить" — удаление пользователя с подтверждением
- Loading states:
  - Skeleton loader при первой загрузке (3 анимированных карточки)
  - Спиннеры на кнопках во время выполнения действий
- Error handling:
  - Показ ошибки загрузки в красной карточке
  - Обработка ошибок в колбэках `onToggleAccess` и `onDelete`
- Empty state: "Нет пользователей"

**Дизайн-система:**
- Cards: `bg-white/5 backdrop-blur-md border border-white/10` с hover эффектом
- Статусы:
  - Активен: `bg-green-500/20 text-green-400 border border-green-500/30`
  - Заблокирован: `bg-red-500/20 text-red-400 border border-red-500/30`
- Buttons:
  - Заблокировать: `bg-red-500/20 text-red-400 border border-red-500/30`
  - Разблокировать: `bg-green-500/20 text-green-400 border border-green-500/30`
  - Удалить: `bg-red-500/20 text-red-400 border border-red-500/30`
- Адаптивность: кнопки stackable на мобильных (`flex-col sm:flex-row`)

**Props Interface:**
```typescript
interface UserListProps {
  users: User[] | undefined;
  isLoading: boolean;
  error: Error | undefined;
  onToggleAccess: (tgid: number, newStatus: boolean) => Promise<void>;
  onDelete: (tgid: number) => Promise<void>;
}
```

**Использование:**
```tsx
import UserList from "@/components/Manager/UserList";
import { useUsers, useUpdateUserAccess, useDeleteUser } from "@/lib/api/hooks";

const { data: users, error, isLoading } = useUsers();
const { updateUserAccess } = useUpdateUserAccess();
const { deleteUser } = useDeleteUser();

<UserList
  users={users}
  isLoading={isLoading}
  error={error}
  onToggleAccess={updateUserAccess}
  onDelete={deleteUser}
/>
```

### 2. UserForm.tsx

**Функциональность:**
- Форма создания нового пользователя
- Поля:
  - **Telegram ID** (обязательно, число)
  - **Имя** (обязательно, минимум 2 символа)
  - **Офис** (обязательно)
- Валидация:
  - Проверка обязательных полей
  - Telegram ID должен быть числом (regex: `^\d+$`)
  - Имя минимум 2 символа
  - Показ ошибок под каждым полем
  - Очистка ошибки при изменении поля
- Submit:
  - Вызов `onSubmit` с валидированными данными
  - После успеха — очистка формы
  - При ошибке — показ общей ошибки сверху
- Loading state: disabled inputs и кнопка с spinner во время отправки
- Опциональная кнопка "Отмена" (`onCancel` prop)

**Дизайн-система:**
- Inputs: `bg-white/10 border border-white/20 text-white rounded-lg`
- Focus state: `focus:border-[#A020F0]`
- Error state: `border-red-500/50`
- Submit button: `bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white`
- Cancel button: `bg-white/10 text-white border border-white/20`
- Error message: `bg-red-500/10 border border-red-500/30 text-red-400`
- Required indicator: `<span className="text-red-400">*</span>`

**Props Interface:**
```typescript
interface UserFormProps {
  onSubmit: (data: { tgid: number; name: string; office: string }) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
}
```

**Использование:**
```tsx
import UserForm from "@/components/Manager/UserForm";
import { useCreateUser } from "@/lib/api/hooks";

const { createUser } = useCreateUser();

<UserForm
  onSubmit={createUser}
  onCancel={() => setShowForm(false)}
/>
```

### Интеграция в `/manager` страницу

Компоненты готовы к интеграции в таб "Пользователи":

```tsx
// app/manager/page.tsx (фрагмент для таба "users")
import UserList from "@/components/Manager/UserList";
import UserForm from "@/components/Manager/UserForm";

const [showUserForm, setShowUserForm] = useState(false);
const { data: users, error, isLoading, mutate } = useUsers();
const { updateUserAccess } = useUpdateUserAccess();
const { deleteUser } = useDeleteUser();
const { createUser } = useCreateUser();

const handleCreateUser = async (data) => {
  await createUser(data);
  mutate(); // Refresh list
  setShowUserForm(false);
};

const handleToggleAccess = async (tgid, newStatus) => {
  await updateUserAccess(tgid, newStatus);
  mutate(); // Refresh list
};

const handleDelete = async (tgid) => {
  await deleteUser(tgid);
  mutate(); // Refresh list
};

return (
  <div className="space-y-6">
    <div className="flex justify-between items-center">
      <h2 className="text-white text-xl font-semibold">Управление пользователями</h2>
      <button
        onClick={() => setShowUserForm(!showUserForm)}
        className="bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white px-4 py-2 rounded-lg"
      >
        {showUserForm ? "Закрыть форму" : "Добавить пользователя"}
      </button>
    </div>

    {showUserForm && (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
        <UserForm
          onSubmit={handleCreateUser}
          onCancel={() => setShowUserForm(false)}
        />
      </div>
    )}

    <UserList
      users={users}
      isLoading={isLoading}
      error={error}
      onToggleAccess={handleToggleAccess}
      onDelete={handleDelete}
    />
  </div>
);
```

## Технические детали

### TypeScript типы

Используется существующий интерфейс `User` из `@/lib/api/types`:
```typescript
interface User {
  tgid: number;
  name: string;
  office: string;
  role: "user" | "manager";
  is_active: boolean;
  created_at: string;
}
```

### Зависимости от других подзадач

**Зависимость от подзадачи 3 (API hooks):**
Компоненты ожидают следующие hooks:
- `useUsers()` → `GET /users`
- `useCreateUser()` → `POST /users`
- `useUpdateUserAccess(tgid, isActive)` → `PATCH /users/{tgid}/access`
- `useDeleteUser(tgid)` → `DELETE /users/{tgid}`

Эти hooks должны быть реализованы в `frontend_mini_app/src/lib/api/hooks.ts`.

### Мобильная оптимизация

- Кнопки в UserList: `flex-col sm:flex-row` для stack на мобильных
- Minimum touch target: 44px (кнопки имеют `py-2` + padding)
- Форма: полностью стэкуемая, все поля на 100% ширины
- Карточки: адаптивный gap и padding

### Accessibility

- Labels связаны с inputs через `htmlFor` и `id`
- Обязательные поля помечены `*`
- Disabled состояния для кнопок во время загрузки
- Confirm dialog перед удалением пользователя
- ARIA-friendly loading spinners

## Результат

Созданы готовые компоненты для управления пользователями:
- ✅ UserList — отображение, блокировка/разблокировка, удаление
- ✅ UserForm — создание нового пользователя с валидацией
- ✅ Loading states и error handling
- ✅ Дизайн соответствует проектной системе (purple gradients, blur backgrounds)
- ✅ Мобильная адаптивность
- ✅ TypeScript типизация

Компоненты готовы к интеграции в таб "Пользователи" на странице `/manager`.
