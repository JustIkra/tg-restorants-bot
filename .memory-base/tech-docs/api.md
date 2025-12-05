# API Specification

Base URL: `/api/v1`

Auth: JWT token с `tgid` в payload

---

## Auth

```
POST /auth/telegram
  Auth: public
  Body: { init_data: string }  # Telegram WebApp initData
  Response: { access_token: string, user: User }
```

---

## Users

```
GET /users
  Auth: manager
  Query: ?search={name|tgid}&limit=50&offset=0
  Response: { items: User[], total: int }

POST /users
  Auth: manager
  Body: { tgid: int, name: string, office: string }
  Response: User
  Errors: 409 (already exists)

POST /users/managers
  Auth: manager
  Body: { tgid: int, name: string }
  Response: User

GET /users/{tgid}
  Auth: manager | self
  Response: User

DELETE /users/{tgid}
  Auth: manager
  Response: 204

PATCH /users/{tgid}/access
  Auth: manager
  Body: { enabled: bool }
  Response: User

GET /users/{tgid}/balance
  Auth: manager | self
  Response: { balance: decimal, weekly_limit: decimal, spent_this_week: decimal }

PATCH /users/{tgid}/balance/limit
  Auth: manager
  Body: { weekly_limit: decimal }
  Response: { weekly_limit: decimal }
```

**User schema:**
```
User {
  tgid: int
  name: string
  office: string
  role: "user" | "manager"
  is_active: bool
  created_at: datetime
}
```

---

## Cafes

```
GET /cafes
  Auth: user | manager
  Query: ?active_only=true
  Response: { items: Cafe[] }

POST /cafes
  Auth: manager
  Body: { name: string, description?: string }
  Response: Cafe

GET /cafes/{cafe_id}
  Auth: user | manager
  Response: Cafe

PATCH /cafes/{cafe_id}
  Auth: manager
  Body: { name?: string, description?: string }
  Response: Cafe

DELETE /cafes/{cafe_id}
  Auth: manager
  Response: 204

PATCH /cafes/{cafe_id}/status
  Auth: manager
  Body: { is_active: bool }
  Response: Cafe
```

**Cafe schema:**
```
Cafe {
  id: int
  name: string
  description: string | null
  is_active: bool
  created_at: datetime
}
```

---

## Menu

```
GET /cafes/{cafe_id}/menu
  Auth: user | manager
  Query: ?category={string}
  Response: { items: MenuItem[] }

POST /cafes/{cafe_id}/menu
  Auth: manager
  Body: {
    name: string,
    description?: string,
    category?: string,
    portion_type: "single" | "sized",
    portion_sizes?: [{ size: string, price: decimal }],  # если sized
    price?: decimal  # если single
  }
  Response: MenuItem

GET /cafes/{cafe_id}/menu/{item_id}
  Auth: user | manager
  Response: MenuItem

PATCH /cafes/{cafe_id}/menu/{item_id}
  Auth: manager
  Body: { name?, description?, category?, portion_sizes?, is_available? }
  Response: MenuItem

DELETE /cafes/{cafe_id}/menu/{item_id}
  Auth: manager
  Response: 204
```

**MenuItem schema:**
```
MenuItem {
  id: int
  cafe_id: int
  name: string
  description: string | null
  category: string | null
  portion_type: "single" | "sized"
  portion_sizes: PortionSize[] | null  # если sized
  price: decimal | null                 # если single
  is_available: bool
}

PortionSize {
  size: string      # "small" | "standard" | "large" или custom
  label: string     # "Маленькая" | "Стандартная" | "Большая"
  price: decimal
}
```

**Примеры:**
```json
// Единичный товар (напиток, десерт)
{
  "id": 1,
  "name": "Американо",
  "portion_type": "single",
  "price": 150.00,
  "portion_sizes": null
}

// Товар с размерами порций
{
  "id": 2,
  "name": "Борщ",
  "portion_type": "sized",
  "price": null,
  "portion_sizes": [
    { "size": "small", "label": "Маленькая", "price": 180.00 },
    { "size": "standard", "label": "Стандартная", "price": 250.00 },
    { "size": "large", "label": "Большая", "price": 320.00 }
  ]
}
```

---

## Deadlines

```
GET /cafes/{cafe_id}/deadlines
  Auth: manager
  Response: { schedules: DeadlineSchedule[] }

PUT /cafes/{cafe_id}/deadlines
  Auth: manager
  Body: { schedules: DeadlineScheduleInput[] }
  Response: { schedules: DeadlineSchedule[] }
```

**DeadlineSchedule schema:**
```
DeadlineSchedule {
  weekday: int          # 0=Пн, 1=Вт, ..., 6=Вс
  weekday_name: string  # "Понедельник", "Вторник", ...
  deadline_time: time   # "10:00"
  is_enabled: bool
  advance_days: int     # за сколько дней можно заказать (default: 1)
}

DeadlineScheduleInput {
  weekday: int
  deadline_time?: time
  is_enabled: bool
  advance_days?: int
}
```

---

## Orders

```
GET /orders/availability/{date}
  Auth: user | manager
  Query: ?cafe_id={int}
  Response: {
    can_order: bool,
    deadline: datetime | null,
    time_remaining: string | null,
    reason: string | null
  }

GET /orders/availability/week
  Auth: user | manager
  Query: ?cafe_id={int}
  Response: {
    days: [{
      date: date,
      weekday: string,
      can_order: bool,
      deadline: time | null,
      reason: string | null
    }]
  }

GET /orders
  Auth: user (self) | manager (all)
  Query: ?date={date}&cafe_id={int}&status={pending|confirmed|cancelled}
  Response: { items: Order[], total: int }

POST /orders
  Auth: user
  Body: {
    cafe_id: int,
    order_date: date,
    items: [{
      menu_item_id: int,
      portion_size?: string,  # "small"|"standard"|"large" для sized
      quantity: int,
      notes?: string          # пожелания к блюду
    }],
    notes?: string            # общие пожелания к заказу
  }
  Response: Order
  Errors: 400 (deadline passed), 403 (access denied)

GET /orders/{order_id}
  Auth: user (owner) | manager
  Response: Order

PATCH /orders/{order_id}
  Auth: user (owner, before deadline)
  Body: {
    items?: [{ menu_item_id, portion_size?, quantity, notes? }],
    notes?: string
  }
  Response: Order
  Errors: 400 (deadline passed)

DELETE /orders/{order_id}
  Auth: user (owner, before deadline) | manager
  Response: 204
  Errors: 400 (deadline passed)

POST /orders/{order_id}/items
  Auth: user (owner, before deadline)
  Body: { menu_item_id: int, portion_size?: string, quantity: int, notes?: string }
  Response: Order
  Errors: 400 (deadline passed)
```

**Order schema:**
```
Order {
  id: int
  user_tgid: int
  user_name: string
  cafe_id: int
  cafe_name: string
  order_date: date
  status: "pending" | "confirmed" | "cancelled"
  items: OrderItem[]
  notes: string | null        # общие пожелания к заказу
  total_price: decimal
  created_at: datetime
  updated_at: datetime
}

OrderItem {
  id: int
  menu_item_id: int
  menu_item_name: string
  portion_size: string | null   # null для single, "small"|"standard"|"large" для sized
  portion_label: string | null  # "Маленькая" и т.д.
  quantity: int
  price: decimal
  subtotal: decimal
  notes: string | null          # пожелания к конкретному блюду ("без лука", "острее")
}
```

**Пример заказа:**
```json
{
  "id": 123,
  "user_name": "Иван Петров",
  "cafe_name": "Столовая №1",
  "order_date": "2025-12-08",
  "status": "pending",
  "notes": "Доставить к 12:30",
  "items": [
    {
      "menu_item_name": "Борщ",
      "portion_size": "large",
      "portion_label": "Большая",
      "quantity": 1,
      "price": 320.00,
      "subtotal": 320.00,
      "notes": "без сметаны"
    },
    {
      "menu_item_name": "Американо",
      "portion_size": null,
      "quantity": 2,
      "price": 150.00,
      "subtotal": 300.00,
      "notes": null
    }
  ],
  "total_price": 620.00
}
```

---

## Summary (Reports)

```
GET /summaries
  Auth: manager
  Query: ?cafe_id={int}&date_from={date}&date_to={date}
  Response: { items: Summary[] }

POST /summaries
  Auth: manager
  Body: { cafe_id: int, date: date }
  Response: Summary

GET /summaries/{summary_id}
  Auth: manager
  Query: ?format=json|csv|pdf
  Response: Summary | file

DELETE /summaries/{summary_id}
  Auth: manager
  Response: 204
```

**Summary schema:**
```
Summary {
  id: int
  cafe_id: int
  cafe_name: string
  date: date
  total_orders: int
  total_items: int
  total_amount: decimal
  items_breakdown: [{
    menu_item_name: string,
    portion_size: string | null,
    quantity: int,
    total: decimal
  }]
  orders_with_notes: [{       # заказы с пожеланиями
    user_name: string,
    item_name: string,
    notes: string
  }]
  created_at: datetime
}
```

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK |
| 201 | Created |
| 204 | No Content (delete) |
| 400 | Bad Request (validation, deadline passed) |
| 401 | Unauthorized |
| 403 | Forbidden (no access) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 500 | Internal Server Error |
