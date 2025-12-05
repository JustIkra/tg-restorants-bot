---
agent: coder
task_id: TSK-002
subtask: 5
subtask_name: "Orders API"
status: completed
next: null
created_at: 2025-12-06T02:30:00Z
files_changed:
  - path: backend/src/schemas/deadline.py
    action: created
  - path: backend/src/schemas/order.py
    action: created
  - path: backend/src/repositories/order.py
    action: created
  - path: backend/src/services/order.py
    action: created
  - path: backend/src/routers/orders.py
    action: created
---

## Реализация

Реализован Orders API с 7 endpoints.

### Endpoints

1. GET /orders/availability/{date} — проверка доступности
2. GET /orders/availability/week — доступность на неделю
3. GET /orders — список заказов (self | all для manager)
4. POST /orders — создание заказа
5. GET /orders/{order_id} — получение заказа (owner | manager)
6. PATCH /orders/{order_id} — обновление (owner до deadline | manager)
7. DELETE /orders/{order_id} — удаление (owner до deadline | manager)

### Business Logic

- Проверка deadline перед созданием/обновлением/удалением
- Валидация combo items (все категории заполнены)
- Расчёт total_price (combo + extras)
- RBAC: owner может менять до deadline, manager — всегда

### Зависимости

Orders API использует:
- `DeadlineService.validate_order_deadline()` — проверка deadline
- `DeadlineService.check_availability()` — availability endpoint
- `DeadlineService.get_week_availability()` — week availability endpoint
- `MenuService.validate_combo_items()` — валидация состава комбо
- `MenuService.calculate_extras_price()` — расчёт стоимости extras
- `MenuService.get_combo()` — получение комбо для price calculation

Эти сервисы создаются параллельно в других Coder субагентах.

### Структура

```
backend/src/
├── schemas/
│   ├── deadline.py         # AvailabilityResponse, WeekAvailabilityResponse
│   └── order.py            # OrderCreate, OrderUpdate, OrderResponse
├── repositories/
│   └── order.py            # OrderRepository (CRUD + list queries)
├── services/
│   └── order.py            # OrderService (business logic + validation)
└── routers/
    └── orders.py           # 7 REST endpoints
```

### Ключевые особенности

1. **RBAC Authorization:**
   - Users can only see/modify own orders before deadline
   - Managers can see/modify any orders at any time

2. **Deadline Validation:**
   - Checked before create/update/delete for non-managers
   - Uses `DeadlineService` for consistency

3. **Combo Validation:**
   - Ensures all combo categories are filled
   - Validates menu item IDs exist and belong to correct categories

4. **Price Calculation:**
   - `total_price = combo.price + sum(extra.price * extra.quantity)`
   - Recalculated on update if combo or extras changed

5. **Query Optimization:**
   - Supports filtering by cafe_id and order_date
   - Pagination with skip/limit
   - Ordered by order_date DESC for recent first
