---
id: TSK-018
title: Исправить баг создания сущностей в менеджерской панели
pipeline: bugfix
status: completed
created_at: 2025-12-07T02:30:00Z
related_files:
  - frontend_mini_app/src/components/Manager/MenuManager.tsx
  - frontend_mini_app/src/components/Manager/ComboForm.tsx
  - frontend_mini_app/src/components/Manager/MenuItemForm.tsx
  - frontend_mini_app/src/components/Manager/CafeForm.tsx
  - frontend_mini_app/src/components/Manager/UserForm.tsx
  - frontend_mini_app/src/lib/api/hooks.ts
  - frontend_mini_app/src/lib/api/client.ts
  - backend/src/routers/menu.py
  - backend/src/services/menu.py
  - backend/src/repositories/menu.py
impact:
  api: да
  db: да
  frontend: да
  services: да
---

## Описание

Пользователь сообщает: "при нажатии кнопки создать никаких новых записей ни где не появляется"

Проблема возникает в менеджерской панели (`/manager`). Пользователь не указал конкретную кнопку, но в панели есть несколько форм создания:
- Создание пользователя (UserForm)
- Создание кафе (CafeForm)
- Создание комбо-набора (ComboForm)
- Создание блюда (MenuItemForm)

## Acceptance Criteria

- [ ] Определить конкретную форму, в которой не работает создание
- [ ] Проверить все формы создания в менеджерской панели
- [ ] Проверить отправку запросов на backend (network logs)
- [ ] Проверить обработку ответов и обновление UI
- [ ] Проверить мутацию SWR кэша после создания
- [ ] Исправить найденные баги
- [ ] Убедиться что после создания записи появляются в списке

## Контекст

### Frontend формы создания

1. **UserForm** (`frontend_mini_app/src/components/Manager/UserForm.tsx`)
   - Вызывается из `manager/page.tsx` (строка 310-319)
   - Использует hook `useCreateUser()` из `lib/api/hooks.ts` (строка 355-363)
   - API endpoint: `POST /users`
   - После успеха: `mutate("/users")`

2. **CafeForm** (`frontend_mini_app/src/components/Manager/CafeForm.tsx`)
   - Вызывается из `manager/page.tsx` (строка 369-380)
   - Прямой вызов `apiRequest("/cafes", { method: "POST", body })` (строка 52-55)
   - После успеха: `mutate("/cafes")` (строка 64)
   - API endpoint: `POST /cafes`

3. **ComboForm** (`frontend_mini_app/src/components/Manager/ComboForm.tsx`)
   - Вызывается из `MenuManager.tsx` (строка 324-330)
   - Handler: `handleCreateCombo` (строка 36-46)
   - Использует hook `useCreateCombo()` (строка 458-465)
   - API endpoint: `POST /cafes/{cafe_id}/combos`
   - После успеха: `mutate(/cafes/{cafeId}/combos)` и `setShowComboForm(false)`

4. **MenuItemForm** (`frontend_mini_app/src/components/Manager/MenuItemForm.tsx`)
   - Вызывается из `MenuManager.tsx` (строка 343-349)
   - Handler: `handleCreateMenuItem` (строка 84-100)
   - Использует hook `useCreateMenuItem()` (строка 500-507)
   - API endpoint: `POST /cafes/{cafe_id}/menu`
   - После успеха: `mutate(/cafes/{cafeId}/menu)` и `setShowMenuItemForm(false)`

### Backend endpoints

Все endpoints определены в `backend/src/routers/menu.py`:

- `POST /cafes/{cafe_id}/combos` (строка 34-39) → `MenuService.create_combo()`
- `POST /cafes/{cafe_id}/menu` (строка 71-76) → `MenuService.create_menu_item()`

Backend использует:
- `MenuService` (`backend/src/services/menu.py`)
- `ComboRepository.create()` (строка 33-37 в `repositories/menu.py`)
- `MenuItemRepository.create()` (строка 77-81 в `repositories/menu.py`)

### Возможные причины бага

1. **Запрос не отправляется**
   - Форма не вызывает onSubmit
   - Валидация блокирует отправку
   - Ошибка в handleSubmit

2. **Запрос отправляется, но backend возвращает ошибку**
   - 400 (валидация)
   - 401/403 (авторизация)
   - 404 (cafe не найдено)
   - 500 (серверная ошибка)

3. **Backend создаёт запись, но frontend не обновляется**
   - `mutate()` не вызывается
   - SWR cache не обновляется
   - Неправильный ключ для mutate()

4. **UI состояние некорректное**
   - Форма не закрывается после создания
   - Список не перезагружается
   - Модальное окно не закрывается

### Логи и отладка

Все формы имеют `console.error()` при ошибках:
- MenuManager.tsx: строки 44, 56, 68, 79, 98, 116, 128, 139
- CafeForm.tsx: строка 75
- UserForm.tsx: строка 72-74

### План отладки (для Debugger agent)

1. Воспроизвести баг в конкретной форме
2. Проверить network tab:
   - Отправляется ли POST запрос?
   - Какой статус ответа?
   - Какое тело ответа?
3. Проверить console:
   - Есть ли ошибки?
   - Вызывается ли console.error?
4. Проверить SWR cache:
   - Вызывается ли mutate()?
   - Обновляется ли ключ?
5. Проверить backend logs:
   - Приходит ли запрос?
   - Есть ли ошибки в обработке?
6. Проверить БД:
   - Создаётся ли запись?

### Потенциальные фиксы

1. Если запрос не отправляется → проверить форму и валидацию
2. Если backend ошибка → исправить backend или frontend данные
3. Если mutate не работает → проверить ключи SWR и вызовы mutate()
4. Если UI не обновляется → добавить revalidate или оптимистичное обновление

## Шаги для Debugger

1. Определить проблемную форму (попросить пользователя уточнить или проверить все)
2. Добавить логирование в handleSubmit для отладки
3. Проверить network запросы
4. Проверить response от backend
5. Проверить вызовы mutate()
6. Создать минимальный воспроизводимый пример

## Шаги для Coder

После того как Debugger найдёт root cause, Coder исправит баг:
1. Исправить найденную проблему
2. Убедиться что mutate() вызывается правильно
3. Добавить better error handling если нужно
4. Проверить что UI state корректный после создания
