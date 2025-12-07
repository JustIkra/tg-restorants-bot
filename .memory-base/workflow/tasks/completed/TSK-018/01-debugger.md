---
agent: debugger
task_id: TSK-018
status: completed
created_at: 2025-12-07T03:15:00Z
next: coder
files_analyzed:
  - frontend_mini_app/src/lib/api/hooks.ts
  - frontend_mini_app/src/lib/api/client.ts
  - frontend_mini_app/src/components/Manager/UserForm.tsx
  - frontend_mini_app/src/components/Manager/CafeForm.tsx
  - frontend_mini_app/src/components/Manager/ComboForm.tsx
  - frontend_mini_app/src/components/Manager/MenuItemForm.tsx
  - frontend_mini_app/src/components/Manager/MenuManager.tsx
  - frontend_mini_app/src/app/manager/page.tsx
  - backend/src/routers/users.py
  - backend/src/routers/cafes.py
  - backend/src/routers/menu.py
---

## Root Cause Analysis

### Проблема

**ОСНОВНАЯ ПРОБЛЕМА: `mutate()` вызывается без `await`, список не обновляется синхронно**

После создания сущности через формы в менеджерской панели вызывается `mutate()` для обновления SWR cache, но:

1. **`mutate()` возвращает Promise**, который НЕ ожидается
2. **Форма закрывается ДО того как список обновится**
3. **Пользователь НЕ видит новую запись**, потому что UI не перерендерился

### Доказательства

#### 1. CafeForm.tsx (строки 63-73)

```typescript
// Revalidate cafes list
mutate("/cafes");  // ❌ НЕТ await - mutate() возвращает Promise!

// Reset form
setName("");
setDescription("");

// Call onSubmit callback
if (onSubmit) {
  onSubmit();  // Форма закрывается СРАЗУ
}
```

**Проблема:** `mutate()` запускает revalidation асинхронно, но код не ждёт завершения. Форма сбрасывается и закрывается ДО того как SWR успел обновить cache.

#### 2. hooks.ts - все mutation hooks

```typescript
// useCreateUser (строки 355-363)
export function useCreateUser() {
  const { mutate } = useSWRConfig();
  const createUser = async (data: { tgid: number; name: string; office: string }) => {
    const result = await apiRequest<User>("/users", { method: "POST", body: JSON.stringify(data) });
    mutate("/users");  // ❌ НЕТ await
    return result;
  };
  return { createUser };
}

// useCreateCafe (строки 400-408)
export function useCreateCafe() {
  const { mutate } = useSWRConfig();
  const createCafe = async (data: { name: string; description?: string }) => {
    const result = await apiRequest<Cafe>("/cafes", { method: "POST", body: JSON.stringify(data) });
    mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });  // ❌ НЕТ await
    return result;
  };
  return { createCafe };
}

// useCreateCombo (строки 458-466)
export function useCreateCombo() {
  const { mutate } = useSWRConfig();
  const createCombo = async (cafeId: number, data: { name: string; categories: string[]; price: number }) => {
    const result = await apiRequest<Combo>(`/cafes/${cafeId}/combos`, { method: "POST", body: JSON.stringify(data) });
    mutate(`/cafes/${cafeId}/combos`);  // ❌ НЕТ await
    return result;
  };
  return { createCombo };
}

// useCreateMenuItem (строки 500-508)
export function useCreateMenuItem() {
  const { mutate } = useSWRConfig();
  const createMenuItem = async (cafeId: number, data: { name: string; description?: string; category: string; price?: number }) => {
    const result = await apiRequest<MenuItem>(`/cafes/${cafeId}/menu`, { method: "POST", body: JSON.stringify(data) });
    mutate(`/cafes/${cafeId}/menu`);  // ❌ НЕТ await
    return result;
  };
  return { createMenuItem };
}
```

**Все mutation hooks вызывают `mutate()` БЕЗ `await`!**

#### 3. MenuManager.tsx - ComboForm handler (строки 36-46)

```typescript
const handleCreateCombo = async (data: { name: string; categories: string[]; price: number }) => {
  if (!selectedCafeId) return;
  try {
    await createCombo(selectedCafeId, data);
    mutateCombos();  // ❌ НЕТ await - вызов из useCombos hook
    setShowComboForm(false);  // Форма закрывается СРАЗУ
  } catch (error) {
    alert("Ошибка при создании комбо");
    console.error(error);
  }
};
```

**Проблема:** `mutateCombos()` вернулся из `useCombos()` hook (строка 25), это `mutate` callback из SWR. Он тоже асинхронный, но не ожидается.

### Затронутые файлы

**Frontend hooks (нужно добавить await):**
- `frontend_mini_app/src/lib/api/hooks.ts` (строки 359, 404, 462, 504, 475, 488, 517, 530, 375, 418, 445, 573-574)

**Frontend компоненты (уже правильно обрабатывают, НО зависят от hooks):**
- `frontend_mini_app/src/components/Manager/CafeForm.tsx` (строка 64)
- `frontend_mini_app/src/components/Manager/MenuManager.tsx` (строки 40, 52, 65, 75, 94, 112, 125, 136)

**Backend endpoints (уже работают правильно):**
- `backend/src/routers/users.py` (строка 37-44) - `POST /users` ✅
- `backend/src/routers/cafes.py` (строка 33-40) - `POST /cafes` ✅
- `backend/src/routers/menu.py` (строка 34-39) - `POST /cafes/{cafe_id}/combos` ✅
- `backend/src/routers/menu.py` (строка 71-76) - `POST /cafes/{cafe_id}/menu` ✅

### Рекомендуемое исправление

#### Стратегия 1: Добавить `await` для всех `mutate()` в hooks.ts

**ПРОБЛЕМА:** `mutate()` из `useSWRConfig()` **НЕ возвращает Promise по умолчанию!**

Из [SWR документации](https://swr.vercel.app/docs/mutation):
- `mutate(key)` - **НЕ возвращает Promise** (просто помечает cache как stale)
- `mutate(key, data, { revalidate: true })` - **возвращает Promise** если `revalidate: true`

**Решение:**
1. Использовать `await mutate(key, undefined, { revalidate: true })`
2. Или использовать оптимистичное обновление (добавить новую запись в cache вручную)

#### Стратегия 2: Оптимистичное обновление

Добавить новую запись в cache СРАЗУ, не дожидаясь revalidation:

```typescript
export function useCreateUser() {
  const { mutate } = useSWRConfig();
  const createUser = async (data: { tgid: number; name: string; office: string }) => {
    const result = await apiRequest<User>("/users", { method: "POST", body: JSON.stringify(data) });

    // Оптимистичное обновление
    mutate("/users", (current: ListResponse<User> | undefined) => {
      if (!current) return current;
      return {
        ...current,
        items: [...current.items, result],
      };
    }, { revalidate: false });  // НЕ делаем revalidation, данные уже актуальные

    return result;
  };
  return { createUser };
}
```

#### Стратегия 3: Использовать `mutate()` из конкретного hook

Вместо `useSWRConfig().mutate()` использовать локальный `mutate` из `useSWR()`:

```typescript
const { data, mutate } = useSWR("/users", fetcher);
await mutate();  // Этот mutate() возвращает Promise!
```

НО это не подходит для mutation hooks, т.к. они не используют `useSWR()` напрямую.

### Для Coder агента

**ЗАДАЧА: Исправить все mutation hooks в `hooks.ts` для синхронного обновления UI**

#### Вариант 1: Добавить `revalidate: true` и `await`

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts`

Изменить все mutation hooks:

1. **useCreateUser** (строка 355-363):
```typescript
export function useCreateUser() {
  const { mutate } = useSWRConfig();
  const createUser = async (data: { tgid: number; name: string; office: string }) => {
    const result = await apiRequest<User>("/users", { method: "POST", body: JSON.stringify(data) });
    await mutate("/users", undefined, { revalidate: true });  // ✅ await + revalidate
    return result;
  };
  return { createUser };
}
```

2. **useCreateCafe** (строка 400-408):
```typescript
export function useCreateCafe() {
  const { mutate } = useSWRConfig();
  const createCafe = async (data: { name: string; description?: string }) => {
    const result = await apiRequest<Cafe>("/cafes", { method: "POST", body: JSON.stringify(data) });
    await mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });  // ✅ await + revalidate уже есть
    return result;
  };
  return { createCafe };
}
```

3. **useCreateCombo** (строка 458-466):
```typescript
export function useCreateCombo() {
  const { mutate } = useSWRConfig();
  const createCombo = async (cafeId: number, data: { name: string; categories: string[]; price: number }) => {
    const result = await apiRequest<Combo>(`/cafes/${cafeId}/combos`, { method: "POST", body: JSON.stringify(data) });
    await mutate(`/cafes/${cafeId}/combos`, undefined, { revalidate: true });  // ✅ await + revalidate
    return result;
  };
  return { createCombo };
}
```

4. **useCreateMenuItem** (строка 500-508):
```typescript
export function useCreateMenuItem() {
  const { mutate } = useSWRConfig();
  const createMenuItem = async (cafeId: number, data: { name: string; description?: string; category: string; price?: number }) => {
    const result = await apiRequest<MenuItem>(`/cafes/${cafeId}/menu`, { method: "POST", body: JSON.stringify(data) });
    await mutate(`/cafes/${cafeId}/menu`, undefined, { revalidate: true });  // ✅ await + revalidate
    return result;
  };
  return { createMenuItem };
}
```

**То же самое для update/delete hooks:**

5. **useUpdateUserAccess** (строка 368-379)
6. **useDeleteUser** (строка 384-391)
7. **useUpdateCafe** (строка 413-421)
8. **useDeleteCafe** (строка 426-433)
9. **useUpdateCafeStatus** (строка 438-449)
10. **useUpdateCombo** (строка 471-479)
11. **useDeleteCombo** (строка 484-491)
12. **useUpdateMenuItem** (строка 513-521)
13. **useDeleteMenuItem** (строка 526-533)
14. **useUpdateBalanceLimit** (строка 566-578)

**Все эти hooks должны:**
1. Добавить `await` перед `mutate()`
2. Добавить `{ revalidate: true }` если его нет
3. Проверить что async функция правильно возвращает результат

#### Вариант 2: Оптимистичное обновление (альтернативный подход)

Для `create` hooks можно добавить новую запись в cache вручную:

```typescript
export function useCreateUser() {
  const { mutate } = useSWRConfig();
  const createUser = async (data: { tgid: number; name: string; office: string }) => {
    const result = await apiRequest<User>("/users", { method: "POST", body: JSON.stringify(data) });

    // Оптимистичное обновление - добавляем новую запись сразу
    mutate("/users", (current: ListResponse<User> | undefined) => {
      if (!current) return current;
      return {
        ...current,
        items: [...current.items, result],
      };
    }, { revalidate: false });

    return result;
  };
  return { createUser };
}
```

**НО** этот подход сложнее и требует знания структуры `ListResponse<T>`. Проще использовать Вариант 1.

#### Также исправить CafeForm.tsx

**Файл:** `frontend_mini_app/src/components/Manager/CafeForm.tsx`

Строка 64:
```typescript
// Было:
mutate("/cafes");

// Стало:
await mutate("/cafes", undefined, { revalidate: true });
```

### Итого

**Root cause:** `mutate()` вызывается БЕЗ `await` и БЕЗ `{ revalidate: true }`, поэтому:
1. SWR НЕ делает revalidation (новый запрос к API)
2. Cache НЕ обновляется
3. UI НЕ показывает новую запись

**Решение:** Добавить `await mutate(key, undefined, { revalidate: true })` во ВСЕ mutation hooks.
