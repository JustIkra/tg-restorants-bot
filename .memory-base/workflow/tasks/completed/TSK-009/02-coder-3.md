---
agent: coder
task_id: TSK-009
subtask: 3
subtask_name: "API hooks"
status: completed
next: null
created_at: 2025-12-06T22:00:00+03:00
files_changed:
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
---

## Реализация

Добавлены API hooks для менеджерских операций в `frontend_mini_app/src/lib/api/hooks.ts`.

### Что сделано

1. **Добавлен импорт `useSWRConfig`** для работы с глобальной мутацией кэша SWR
2. **Добавлен тип `User`** в импорты из types.ts

### Добавленные hooks

#### User Management (Управление пользователями)

- `useUsers()` - GET /users - получение всех пользователей
- `useCreateUser()` - POST /users - создание нового пользователя
- `useUpdateUserAccess()` - PATCH /users/{tgid}/access - обновление доступа пользователя
- `useDeleteUser()` - DELETE /users/{tgid} - удаление пользователя

#### Cafe Management (Управление кафе)

- `useCreateCafe()` - POST /cafes - создание нового кафе
- `useUpdateCafe()` - PATCH /cafes/{id} - обновление информации о кафе
- `useDeleteCafe()` - DELETE /cafes/{id} - удаление кафе
- `useUpdateCafeStatus()` - PATCH /cafes/{id}/status - активация/деактивация кафе

#### Combo Management (Управление комбо)

- `useCreateCombo()` - POST /cafes/{id}/combos - создание комбо
- `useUpdateCombo()` - PATCH /cafes/{id}/combos/{comboId} - обновление комбо
- `useDeleteCombo()` - DELETE /cafes/{id}/combos/{comboId} - удаление комбо

#### Menu Item Management (Управление блюдами)

- `useCreateMenuItem()` - POST /cafes/{id}/menu - создание блюда
- `useUpdateMenuItem()` - PATCH /cafes/{id}/menu/{itemId} - обновление блюда
- `useDeleteMenuItem()` - DELETE /cafes/{id}/menu/{itemId} - удаление блюда

### Технические детали

1. **Паттерн мутации**:
   - Все mutation hooks используют `useSWRConfig()` для доступа к глобальной функции `mutate`
   - После изменений автоматически обновляется кэш SWR

2. **Invalidation стратегии**:
   - User hooks: простая мутация по ключу `/users`
   - Cafe hooks: мутация всех ключей начинающихся с `/cafes` с использованием функции-предиката
   - Combo/MenuItem hooks: мутация конкретного endpoint'а кафе

3. **Типобезопасность**:
   - Все hooks типизированы через TypeScript
   - Используются типы из `api/types.ts`
   - Partial типы для update операций

4. **Консистентность с существующим кодом**:
   - Hooks следуют тому же паттерну, что и существующие (useCreateOrder, useCreateSummary и т.д.)
   - Используется функция `apiRequest` из `./client`
   - Автоматическая ревалидация кэша после мутаций

### Пример использования

```typescript
// В React компоненте
const { createUser } = useCreateUser();

const handleCreateUser = async () => {
  try {
    const newUser = await createUser({
      tgid: 123456789,
      name: "John Doe",
      office: "Moscow"
    });
    console.log("User created:", newUser);
    // Кэш /users автоматически обновится
  } catch (error) {
    console.error("Failed to create user:", error);
  }
};
```

### Преимущества

1. **Автоматическая синхронизация UI** - SWR автоматически обновляет все компоненты после мутаций
2. **Минимальная боилерплейт** - не нужно вручную управлять состоянием загрузки
3. **Оптимистичные обновления** - можно легко добавить optimistic UI при необходимости
4. **Централизованная логика** - вся работа с API в одном месте

## Файлы

- **frontend_mini_app/src/lib/api/hooks.ts** - добавлено 200+ строк с новыми hooks

## Статус

✅ Completed - все запрошенные hooks реализованы и готовы к использованию
