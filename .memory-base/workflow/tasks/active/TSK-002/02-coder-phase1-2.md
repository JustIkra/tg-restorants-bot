---
agent: coder
task_id: TSK-002
subtask: "1.2"
subtask_name: "Database setup и модели"
status: completed
next: coder
created_at: 2025-12-06T01:30:00Z
files_changed:
  - path: backend/src/database.py
    action: created
  - path: backend/src/models/base.py
    action: created
  - path: backend/src/models/user.py
    action: created
  - path: backend/src/models/cafe.py
    action: created
  - path: backend/src/models/deadline.py
    action: created
  - path: backend/src/models/order.py
    action: created
  - path: backend/src/models/summary.py
    action: created
  - path: backend/src/models/__init__.py
    action: modified
  - path: backend/alembic.ini
    action: created
  - path: backend/alembic/env.py
    action: created
  - path: backend/alembic/script.py.mako
    action: created
  - path: backend/alembic/versions/.gitkeep
    action: created
  - path: backend/alembic/versions/001_initial_schema.py
    action: created
---

## Реализация

Созданы SQLAlchemy модели и настроен Alembic.

### Модели (7 таблиц)

1. **User** - пользователи (tgid, name, office, role, is_active, weekly_limit)
2. **Cafe** - кафе (id, name, description, is_active)
3. **Combo** - комбо-наборы (id, cafe_id, name, categories, price)
4. **MenuItem** - блюда меню (id, cafe_id, name, category, price)
5. **Deadline** - дедлайны заказов (id, cafe_id, weekday, deadline_time, advance_days)
6. **Order** - заказы (id, user_tgid, cafe_id, combo_id, combo_items, extras, total_price)
7. **Summary** - отчёты (id, cafe_id, date, total_orders, total_amount, breakdown)

### Alembic

- Настроен async Alembic
- Создана миграция 001_initial_schema.py
- Добавлены индексы для оптимизации

## Следующий шаг

Phase 1.3: Авторизация (Telegram + JWT)
