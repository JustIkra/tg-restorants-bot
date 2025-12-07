---
agent: architect
task_id: TSK-016
status: completed
next: coder
created_at: 2025-12-07T01:10:00Z
---

## Анализ

Задача TSK-016 требует реализации системы контроля доступа с approval workflow для пользователей Telegram Mini App. Текущая реализация автоматически создаёт пользователя при первой авторизации, что недопустимо для production.

Решение в task.md уже содержит полноценную архитектуру, которая следует существующему паттерну `CafeLinkRequest`.

## Архитектурное решение

Использовать существующий паттерн approval workflow из `CafeLinkRequest`:
- Новая модель `UserAccessRequest` для хранения запросов на доступ
- Изменение логики `POST /auth/telegram` для создания request вместо user
- Новые endpoints для управления запросами (manager only)
- Frontend компоненты для approval UI

### Изменения в данных

**Новая таблица:** `user_access_requests`
- `id` (PK, autoincrement)
- `tgid` (BigInteger, unique) — Telegram ID
- `name` (String) — имя из Telegram
- `office` (String) — офис
- `username` (String, nullable) — Telegram username
- `status` (Enum: pending/approved/rejected)
- `processed_at` (DateTime, nullable)
- `created_at` (DateTime)

### API изменения

| Endpoint | Метод | Изменение |
|----------|-------|-----------|
| `/auth/telegram` | POST | Создаёт request вместо user для новых пользователей |
| `/user-requests` | GET | Список запросов (manager only) |
| `/user-requests/{id}/approve` | POST | Одобрить запрос (manager only) |
| `/user-requests/{id}/reject` | POST | Отклонить запрос (manager only) |
| `/users/{tgid}` | PATCH | Обновить пользователя (manager only) |

## Подзадачи для Coder

### 1. Модель и миграция БД
- Файлы:
  - `backend/src/models/user.py`
  - `backend/alembic/versions/005_user_access_requests.py`
- Действия:
  - Добавить `UserAccessRequestStatus` enum
  - Добавить модель `UserAccessRequest`
  - Создать миграцию для таблицы `user_access_requests`

### 2. Repository и Service для UserAccessRequest
- Файлы:
  - `backend/src/repositories/user_request.py` (новый)
  - `backend/src/services/user_request.py` (новый)
- Действия:
  - Создать repository с CRUD операциями
  - Создать service с логикой approve/reject

### 3. Schemas для UserAccessRequest
- Файлы:
  - `backend/src/schemas/user_request.py` (новый)
  - `backend/src/schemas/user.py`
- Действия:
  - Создать схемы `UserAccessRequestSchema`, `UserAccessRequestListSchema`
  - Добавить `UserUpdate` schema с полем `role`

### 4. Router для user-requests
- Файлы:
  - `backend/src/routers/user_requests.py` (новый)
  - `backend/src/main.py`
- Действия:
  - Создать router с endpoints GET, POST approve, POST reject
  - Подключить router в main.py

### 5. Изменение логики авторизации
- Файлы:
  - `backend/src/routers/auth.py`
- Действия:
  - Изменить `POST /auth/telegram` для создания request вместо user
  - Добавить проверку существующих requests

### 6. Добавить PATCH /users/{tgid}
- Файлы:
  - `backend/src/routers/users.py`
  - `backend/src/services/user.py`
- Действия:
  - Добавить endpoint для обновления пользователя
  - Обновить service

### 7. Frontend: API hooks и типы
- Файлы:
  - `frontend_mini_app/src/lib/api/types.ts`
  - `frontend_mini_app/src/lib/api/hooks.ts`
  - `frontend_mini_app/src/lib/api/client.ts`
- Действия:
  - Добавить типы для UserAccessRequest
  - Добавить hooks для user-requests API
  - Добавить API методы

### 8. Frontend: Компоненты для User Requests
- Файлы:
  - `frontend_mini_app/src/components/Manager/UserRequestCard.tsx` (новый)
  - `frontend_mini_app/src/components/Manager/UserRequestsList.tsx` (новый)
  - `frontend_mini_app/src/components/Manager/UserEditModal.tsx` (новый)
- Действия:
  - Создать карточку запроса с кнопками Approve/Reject
  - Создать список запросов с фильтрацией по статусу
  - Создать модалку редактирования пользователя

### 9. Frontend: Интеграция в Manager Page
- Файлы:
  - `frontend_mini_app/src/app/manager/page.tsx`
- Действия:
  - Добавить вкладку "User Requests"
  - Добавить секцию управления пользователями
  - Интегрировать новые компоненты

## Рекомендации по параллельному выполнению

**Можно выполнять параллельно:**
- Подзадачи 1-4 (backend base) — последовательно между собой
- Подзадачи 7-9 (frontend) — после 1-6, параллельно между собой

**Зависимости:**
- Подзадача 5 зависит от 1-4
- Подзадача 6 зависит от 3
- Frontend (7-9) зависит от backend (1-6) для типов и API

## Риски и зависимости

- **Миграция БД:** Требуется применить миграцию перед тестированием
- **Первый менеджер:** Seed script должен создать первого менеджера
- **Backward compatibility:** Существующие пользователи продолжат работать без изменений
