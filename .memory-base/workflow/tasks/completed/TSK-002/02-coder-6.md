---
agent: coder
task_id: TSK-002
subtask: 6
subtask_name: "Summaries API"
status: completed
next: null
created_at: 2025-12-06T02:30:00Z
files_changed:
  - path: backend/src/schemas/summary.py
    action: created
  - path: backend/src/repositories/summary.py
    action: created
  - path: backend/src/services/summary.py
    action: created
  - path: backend/src/routers/summaries.py
    action: created
---

## Реализация

Реализован Summaries API с 4 endpoints.

### Endpoints

1. GET /summaries — список отчётов (manager)
2. POST /summaries — создание отчёта (manager)
3. GET /summaries/{summary_id} — получение отчёта, format=json|csv (manager)
4. DELETE /summaries/{summary_id} — удаление отчёта (manager)

### Aggregation Logic

- Группировка заказов по комбо и extras
- Подсчёт количества и суммы
- Генерация breakdown: { combos: [...], extras: [...] }
- Экспорт в CSV
