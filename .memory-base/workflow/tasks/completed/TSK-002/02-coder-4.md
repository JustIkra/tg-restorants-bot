---
agent: coder
task_id: TSK-002
subtask: 4
subtask_name: "Deadlines API"
status: completed
next: null
created_at: 2025-12-06T02:30:00Z
files_changed:
  - path: backend/src/schemas/deadline.py
    action: created
  - path: backend/src/repositories/deadline.py
    action: created
  - path: backend/src/services/deadline.py
    action: created
  - path: backend/src/routers/deadlines.py
    action: created
---

## Реализация

Реализован Deadlines API с 2 endpoints + availability logic.

### Endpoints

1. GET /cafes/{cafe_id}/deadlines (manager)
2. PUT /cafes/{cafe_id}/deadlines (manager)

### Business Logic

- check_availability(cafe_id, date) — проверка возможности заказа
- get_week_availability(cafe_id) — доступность на неделю
- validate_order_deadline() — валидация для Orders API

### Алгоритм проверки deadline

1. Найти deadline для weekday заказа
2. Вычислить actual deadline = order_date - advance_days + deadline_time
3. Сравнить с текущим временем
