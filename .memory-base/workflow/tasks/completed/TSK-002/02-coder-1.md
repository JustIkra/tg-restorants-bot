---
agent: coder
task_id: TSK-002
subtask: 1
subtask_name: "Users API"
status: completed
next: null
created_at: 2025-12-06T02:30:00Z
files_changed:
  - path: backend/src/schemas/user.py
    action: created
  - path: backend/src/repositories/base.py
    action: created
  - path: backend/src/repositories/user.py
    action: created
  - path: backend/src/services/user.py
    action: created
  - path: backend/src/routers/users.py
    action: created
---

## Реализация

Реализован Users API с 8 endpoints.

### Endpoints

1. GET /users — список пользователей (manager)
2. POST /users — создание пользователя (manager)
3. POST /users/managers — создание менеджера (manager)
4. GET /users/{tgid} — получение пользователя (self | manager)
5. DELETE /users/{tgid} — удаление пользователя (manager)
6. PATCH /users/{tgid}/access — управление доступом (manager)
7. GET /users/{tgid}/balance — баланс пользователя (self | manager)
8. PATCH /users/{tgid}/balance/limit — лимит баланса (manager)

### Компоненты

- schemas/user.py — Pydantic схемы
- repositories/base.py — базовый репозиторий
- repositories/user.py — UserRepository
- services/user.py — UserService с бизнес-логикой
- routers/users.py — FastAPI router
