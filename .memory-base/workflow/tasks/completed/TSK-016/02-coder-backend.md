---
agent: coder
task_id: TSK-016
subtask: backend (1-6)
status: completed
next: coder (frontend)
created_at: 2025-12-07T02:15:00Z
files_changed:
  - path: backend/src/models/user.py
    action: modified
  - path: backend/src/models/__init__.py
    action: modified
  - path: backend/alembic/versions/005_user_access_requests.py
    action: created
  - path: backend/src/repositories/user_request.py
    action: created
  - path: backend/src/services/user_request.py
    action: created
  - path: backend/src/schemas/user_request.py
    action: created
  - path: backend/src/schemas/user.py
    action: modified
  - path: backend/src/routers/user_requests.py
    action: created
  - path: backend/src/routers/__init__.py
    action: modified
  - path: backend/src/main.py
    action: modified
  - path: backend/src/routers/auth.py
    action: modified
  - path: backend/src/routers/users.py
    action: modified
---

## Реализация

Реализованы все 6 подзадач для backend части TSK-016 (User Access Request Approval System):

1. Модель и миграция БД
2. Repository и Service для UserAccessRequest
3. Schemas для UserAccessRequest
4. Router для user-requests
5. Изменение логики авторизации
6. Добавление PATCH /users/{tgid}

Все изменения следуют существующим паттернам проекта, особенно паттерну `CafeLinkRequest`.

## Изменения

### 1. Модель и миграция БД

#### `backend/src/models/user.py`
- Добавлен enum `UserAccessRequestStatus` с вариантами: pending, approved, rejected
- Добавлена модель `UserAccessRequest` с полями:
  - `id` (PK, autoincrement)
  - `tgid` (BigInteger, unique) — Telegram ID
  - `name` (String) — имя пользователя
  - `office` (String) — офис
  - `username` (String, nullable) — Telegram username
  - `status` (Enum) — статус запроса
  - `processed_at` (DateTime, nullable) — время обработки
  - Наследует `TimestampMixin` (created_at, updated_at)

#### `backend/src/models/__init__.py`
- Добавлен экспорт `UserAccessRequest`

#### `backend/alembic/versions/005_user_access_requests.py`
- Создана миграция для таблицы `user_access_requests`
- Добавлен unique constraint на `tgid`
- Создан индекс на `status` для фильтрации

### 2. Repository и Service

#### `backend/src/repositories/user_request.py`
Создан repository с методами:
- `get_request(request_id)` — получить запрос по ID
- `get_by_tgid(tgid)` — получить запрос по Telegram ID
- `list_requests(skip, limit, status)` — список с пагинацией и фильтрацией
- `create_request(tgid, name, office, username)` — создать новый запрос
- `update_request(request, **kwargs)` — обновить запрос

Использует whitelist для обновляемых полей: `status`, `processed_at`

#### `backend/src/services/user_request.py`
Создан service с методами:
- `list_requests(skip, limit, status)` — список запросов с метаданными (total, skip, limit)
- `get_request(request_id)` — получить запрос с проверкой существования
- `approve_request(request_id)` — одобрить запрос:
  - Проверяет статус (должен быть pending)
  - Создаёт пользователя (`User`) с данными из запроса
  - Обновляет статус запроса на approved
  - Устанавливает `processed_at`
- `reject_request(request_id)` — отклонить запрос:
  - Проверяет статус (должен быть pending)
  - Обновляет статус на rejected
  - Устанавливает `processed_at`

### 3. Schemas

#### `backend/src/schemas/user_request.py`
Созданы схемы:
- `UserAccessRequestSchema` — ответ с данными запроса
- `UserAccessRequestListSchema` — пагинированный список запросов

#### `backend/src/schemas/user.py`
- Добавлено поле `role` в схему `UserUpdate` для обновления роли пользователя

### 4. Router для user-requests

#### `backend/src/routers/user_requests.py`
Создан router с endpoints:
- `GET /user-requests` — список запросов (manager only)
  - Поддерживает пагинацию (skip, limit)
  - Фильтрацию по статусу
- `POST /user-requests/{request_id}/approve` — одобрить запрос (manager only)
- `POST /user-requests/{request_id}/reject` — отклонить запрос (manager only)

#### `backend/src/routers/__init__.py`
- Добавлен экспорт `user_requests_router`

#### `backend/src/main.py`
- Подключён router с prefix `/api/v1`

### 5. Изменение логики авторизации

#### `backend/src/routers/auth.py`
Изменена логика `POST /auth/telegram`:

**Для существующих пользователей:**
- Нормальная авторизация с выдачей JWT token
- Обновление имени и офиса при изменении
- Проверка `is_active`

**Для новых пользователей:**
1. Проверка существующего запроса по `tgid`
2. Если запрос существует:
   - `pending` → 403 "Access request pending approval"
   - `rejected` → 403 "Access request rejected"
   - `approved` (но user не существует) → 500 "Data inconsistency"
3. Если запроса нет:
   - Создаётся новый `UserAccessRequest` со статусом `pending`
   - Возвращается 403 "Access request created. Please wait for manager approval."

### 6. Добавление PATCH /users/{tgid}

#### `backend/src/routers/users.py`
- Добавлен endpoint `PATCH /users/{tgid}` для обновления пользователя (manager only)
- Принимает `UserUpdate` schema с полями: `name`, `office`, `role` (все опциональные)
- Использует существующий `UserService.update_user()` метод

## Примечания

### Архитектурные решения
1. **Паттерн CafeLinkRequest:** Все реализовано по аналогии с существующим approval workflow для кафе
2. **Unique constraint на tgid:** Предотвращает дублирование запросов от одного пользователя
3. **Индекс на status:** Оптимизирует фильтрацию запросов по статусу
4. **Whitelist полей в repository:** Защита от случайного изменения критичных полей

### Backward Compatibility
- Существующие пользователи в БД продолжат работать без изменений
- Только новые пользователи проходят через approval workflow
- Миграция не требует изменений существующих данных

### Security
- Все endpoints управления запросами защищены `ManagerUser` dependency
- Проверка статуса запроса перед approve/reject
- Проверка `is_active` перед выдачей token

### Зависимости для frontend
Frontend потребуется:
- Типы для `UserAccessRequest`
- API hooks для endpoints:
  - `GET /api/v1/user-requests`
  - `POST /api/v1/user-requests/{id}/approve`
  - `POST /api/v1/user-requests/{id}/reject`
  - `PATCH /api/v1/users/{tgid}` (для редактирования пользователя)
- UI компоненты для отображения и управления запросами
