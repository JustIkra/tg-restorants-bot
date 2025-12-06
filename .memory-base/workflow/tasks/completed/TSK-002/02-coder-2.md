---
agent: coder
task_id: TSK-002
subtask: 2
subtask_name: "Cafes API"
status: completed
next: null
created_at: 2025-12-06T02:30:00Z
files_changed:
  - path: backend/src/schemas/cafe.py
    action: created
  - path: backend/src/repositories/cafe.py
    action: created
  - path: backend/src/services/cafe.py
    action: created
  - path: backend/src/routers/cafes.py
    action: created
---

## Реализация

Реализован Cafes API с 6 endpoints.

### Endpoints

1. GET /cafes — список кафе (user | manager)
2. POST /cafes — создание кафе (manager)
3. GET /cafes/{cafe_id} — получение кафе
4. PATCH /cafes/{cafe_id} — обновление кафе (manager)
5. DELETE /cafes/{cafe_id} — удаление кафе (manager)
6. PATCH /cafes/{cafe_id}/status — изменение статуса (manager)

### Компоненты

- schemas/cafe.py — Pydantic схемы
- repositories/cafe.py — CafeRepository
- services/cafe.py — CafeService
- routers/cafes.py — FastAPI router
