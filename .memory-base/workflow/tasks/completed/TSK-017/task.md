---
id: TSK-017
title: Исправить загрузку данных в панели менеджера
pipeline: bugfix
status: completed
created_at: 2025-12-06T22:54:52Z
related_files:
  - frontend_mini_app/src/components/Manager/CafeList.tsx
  - frontend_mini_app/src/lib/api/hooks.ts
impact:
  - api: no
  - db: no
  - frontend: yes
  - services: no
---

## Описание
В панели менеджера (/manager) не отображаются кафе и пользователи.
На скриншотах видно:
- Вкладка "Кафе" показывает "Кафе не найдены"
- Вкладка "Пользователи" показывает "Нет пользователей"

**Root Cause:**
В компоненте `CafeList.tsx` (строка 14) используется `useCafes(false)`, где первый параметр `shouldFetch` установлен в `false`. Это означает, что SWR хук **не выполняет запрос** к API.

```tsx
// frontend_mini_app/src/components/Manager/CafeList.tsx:14
const { data: cafes, error, isLoading } = useCafes(false); // ❌ shouldFetch=false
```

Аналогично, `useUsers()` используется корректно в `manager/page.tsx` (строка 70), но возможна проблема с авторизацией или API.

## Acceptance Criteria
- [ ] Компонент `CafeList` загружает и отображает список всех кафе (активных и неактивных)
- [ ] Компонент `UserList` получает данные пользователей через props из `manager/page.tsx`
- [ ] При успешной загрузке данные отображаются на вкладках "Кафе" и "Пользователи"
- [ ] При ошибке загрузки отображается сообщение об ошибке с деталями
- [ ] Backend API endpoints `/cafes` и `/users` корректно возвращают данные

## Контекст

### Компоненты
1. **CafeList.tsx** (`frontend_mini_app/src/components/Manager/CafeList.tsx`)
   - Использует хук `useCafes(false)` — **shouldFetch=false** блокирует запрос
   - Должен использовать `useCafes(true, false)` для загрузки всех кафе (не только активных)

2. **UserList.tsx** (`frontend_mini_app/src/components/Manager/UserList.tsx`)
   - Получает данные через props (users, isLoading, error) из родителя
   - Родитель `manager/page.tsx` использует `useUsers()` корректно

3. **manager/page.tsx** (`frontend_mini_app/src/app/manager/page.tsx`)
   - Строка 70: `const { data: users, error: usersError, isLoading: usersLoading } = useUsers();`
   - Авторизация проходит успешно (пользователь — менеджер)
   - Передаёт props в UserList

### API хуки

**useCafes** (`frontend_mini_app/src/lib/api/hooks.ts:39`)
```tsx
export function useCafes(shouldFetch = true, activeOnly = true): UseDataResult<Cafe> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<Cafe>>(
    shouldFetch ? `/cafes${activeOnly ? "?active_only=true" : ""}` : null,
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}
```
- `shouldFetch=false` → SWR ключ = `null` → **запрос не выполняется**

**useUsers** (`frontend_mini_app/src/lib/api/hooks.ts:339`)
```tsx
export function useUsers(): UseDataResult<User> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<User>>(
    "/users",
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}
```
- Всегда делает запрос к `/users`

### API endpoints

**Backend API** (`/api/v1/`)
- `GET /cafes?active_only=true` — список кафе (только активных)
- `GET /cafes` — список всех кафе
- `GET /users` — список пользователей (manager only)

### Найденные использования

**useCafes с shouldFetch=false:**
- `CafeList.tsx:14` — ❌ **проблема здесь**
- `ReportsList.tsx:14` — может быть проблема
- `MenuManager.tsx:24` — может быть проблема

**useCafes с динамическим shouldFetch:**
- `page.tsx:59` — `useCafes(isAuthenticated, true)` — ✅ корректно

## Решение

### 1. CafeList.tsx
Изменить строку 14:
```tsx
// До:
const { data: cafes, error, isLoading } = useCafes(false);

// После:
const { data: cafes, error, isLoading } = useCafes(true, false);
```
Параметры:
- `shouldFetch=true` — выполнять запрос
- `activeOnly=false` — получить все кафе (активные и неактивные)

### 2. Проверить другие компоненты
- `ReportsList.tsx` и `MenuManager.tsx` — аналогичная проблема?

### 3. Проверить backend
Если после исправления фронтенда данные не загружаются:
- Проверить, что API endpoint `/cafes` и `/users` возвращают данные
- Проверить авторизацию (JWT token)
- Проверить CORS и Network в DevTools

## Файлы для изменения
- `frontend_mini_app/src/components/Manager/CafeList.tsx` — исправить `useCafes(false)` → `useCafes(true, false)`
- Возможно: `frontend_mini_app/src/components/Manager/ReportsList.tsx`
- Возможно: `frontend_mini_app/src/components/Manager/MenuManager.tsx`

## Тестирование
1. Открыть панель менеджера `/manager`
2. Перейти на вкладку "Кафе" — должен отобразиться список кафе
3. Перейти на вкладку "Пользователи" — должен отобразиться список пользователей
4. Проверить консоль браузера на наличие ошибок
5. Проверить Network tab — должны быть успешные запросы к `/cafes` и `/users`
