---
agent: coder
task_id: TSK-002
subtask: "1.3"
subtask_name: "Авторизация Telegram + JWT"
status: completed
next: coder
created_at: 2025-12-06T02:00:00Z
files_changed:
  - path: backend/src/auth/telegram.py
    action: created
  - path: backend/src/auth/jwt.py
    action: created
  - path: backend/src/auth/dependencies.py
    action: created
  - path: backend/src/auth/schemas.py
    action: created
  - path: backend/src/auth/__init__.py
    action: modified
  - path: backend/src/routers/auth.py
    action: created
  - path: backend/src/routers/__init__.py
    action: modified
---

## Реализация

Реализована полная система авторизации.

### Компоненты

1. **telegram.py** — валидация Telegram WebApp initData через HMAC-SHA256
2. **jwt.py** — создание и проверка JWT токенов
3. **dependencies.py** — FastAPI dependencies (get_current_user, require_manager)
4. **schemas.py** — Pydantic схемы для auth endpoints
5. **routers/auth.py** — POST /auth/telegram endpoint

### Auth Flow

1. Frontend получает initData от Telegram WebApp SDK
2. Frontend отправляет POST /auth/telegram { init_data: string }
3. Backend валидирует initData через HMAC-SHA256
4. Backend создаёт/обновляет User в БД
5. Backend возвращает JWT token + user info
6. Frontend использует token в Authorization header

### JWT Payload

{ tgid: int, role: str, exp: datetime }

## Следующий шаг

Phase 2: API модули (параллельное выполнение)
