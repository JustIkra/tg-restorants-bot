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

Меню состоит из комбо-наборов и отдельных блюд по категориям.

### Комбо-наборы

```
GET /cafes/{cafe_id}/combos
  Auth: user | manager
  Response: { items: Combo[] }

POST /cafes/{cafe_id}/combos
  Auth: manager
  Body: {
    name: string,
    categories: string[],  # ["salad", "soup"] или ["salad", "soup", "main"]
    price: decimal
  }
  Response: Combo

PATCH /cafes/{cafe_id}/combos/{combo_id}
  Auth: manager
  Body: { name?, categories?, price?, is_available? }
  Response: Combo

DELETE /cafes/{cafe_id}/combos/{combo_id}
  Auth: manager
  Response: 204
```

**Combo schema:**
```
Combo {
  id: int
  cafe_id: int
  name: string               # "Салат + Суп", "Салат + Суп + Основное блюдо"
  categories: string[]       # ["salad", "soup", "main"]
  price: decimal
  is_available: bool
}
```

### Блюда меню

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
    category: string,   # "soup" | "salad" | "main" | "extra"
    price?: decimal     # только для категории "extra"
  }
  Response: MenuItem

GET /cafes/{cafe_id}/menu/{item_id}
  Auth: user | manager
  Response: MenuItem

PATCH /cafes/{cafe_id}/menu/{item_id}
  Auth: manager
  Body: { name?, description?, category?, price?, is_available? }
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
  category: string           # "soup" | "salad" | "main" | "extra"
  price: decimal | null      # цена только для "extra", остальные входят в комбо
  is_available: bool
}
```

**Категории:**
- `soup` — Супы (входят в комбо)
- `salad` — Салаты (входят в комбо)
- `main` — Основные блюда (входят в комбо)
- `extra` — Дополнительно (продаётся отдельно, имеет цену)

**Примеры:**
```json
// Комбо-набор
{
  "id": 1,
  "name": "Салат + Суп",
  "categories": ["salad", "soup"],
  "price": 450.00,
  "is_available": true
}

// Блюдо в комбо (без цены)
{
  "id": 10,
  "name": "Борщ с курицей",
  "category": "soup",
  "price": null,
  "is_available": true
}

// Дополнительный товар (с ценой)
{
  "id": 20,
  "name": "Фокачча с пряным маслом",
  "description": "60 г.",
  "category": "extra",
  "price": 50.00,
  "is_available": true
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

Заказ состоит из комбо-набора (с выбранными блюдами) и опциональных дополнительных товаров.

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
    combo_id: int,
    combo_items: [{
      category: string,       # "soup" | "salad" | "main"
      menu_item_id: int
    }],
    extras?: [{
      menu_item_id: int,
      quantity: int
    }],
    notes?: string
  }
  Response: Order
  Errors: 400 (deadline passed, invalid combo), 403 (access denied)

GET /orders/{order_id}
  Auth: user (owner) | manager
  Response: Order

PATCH /orders/{order_id}
  Auth: user (owner, before deadline)
  Body: {
    combo_items?: [{ category, menu_item_id }],
    extras?: [{ menu_item_id, quantity }],
    notes?: string
  }
  Response: Order
  Errors: 400 (deadline passed)

DELETE /orders/{order_id}
  Auth: user (owner, before deadline) | manager
  Response: 204
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
  combo: OrderCombo
  extras: OrderExtra[]
  notes: string | null
  total_price: decimal
  created_at: datetime
  updated_at: datetime
}

OrderCombo {
  combo_id: int
  combo_name: string          # "Салат + Суп + Основное блюдо"
  combo_price: decimal
  items: [{
    category: string          # "soup" | "salad" | "main"
    menu_item_id: int
    menu_item_name: string
  }]
}

OrderExtra {
  menu_item_id: int
  menu_item_name: string
  quantity: int
  price: decimal
  subtotal: decimal
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
  "combo": {
    "combo_id": 2,
    "combo_name": "Салат + Суп + Основное блюдо",
    "combo_price": 550.00,
    "items": [
      { "category": "salad", "menu_item_id": 10, "menu_item_name": "Салат с курицей" },
      { "category": "soup", "menu_item_id": 11, "menu_item_name": "Борщ с курицей" },
      { "category": "main", "menu_item_id": 12, "menu_item_name": "Котлета с пюре" }
    ]
  },
  "extras": [
    {
      "menu_item_id": 20,
      "menu_item_name": "Фокачча с пряным маслом",
      "quantity": 1,
      "price": 50.00,
      "subtotal": 50.00
    }
  ],
  "total_price": 600.00
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
  total_amount: decimal
  combos_breakdown: [{
    combo_name: string,
    quantity: int,
    total: decimal
  }]
  items_breakdown: [{
    category: string,
    menu_item_name: string,
    quantity: int
  }]
  extras_breakdown: [{
    menu_item_name: string,
    quantity: int,
    total: decimal
  }]
  orders_with_notes: [{
    user_name: string,
    notes: string
  }]
  created_at: datetime
}
```

---

## Cafe Link Management

### POST /api/v1/cafes/{cafe_id}/link-request
Create a cafe link request (public endpoint for Telegram bot)

```
POST /api/v1/cafes/{cafe_id}/link-request
  Auth: public (через Telegram бота)
  Body: {
    tg_chat_id: int,
    tg_username: string | null
  }
  Response: LinkRequest
  Status: 201 Created
```

**LinkRequest schema:**
```
LinkRequest {
  id: int
  cafe_id: int
  cafe_name: string
  tg_chat_id: int
  tg_username: string | null
  status: "pending" | "approved" | "rejected"
  created_at: datetime
  processed_at: datetime | null
}
```

### GET /api/v1/cafe-requests
List all cafe link requests (manager only)

```
GET /api/v1/cafe-requests
  Auth: manager
  Query: ?status={pending|approved|rejected}&skip=0&limit=100
  Response: {
    items: LinkRequest[],
    total: int
  }
```

### POST /api/v1/cafe-requests/{request_id}/approve
Approve a cafe link request (manager only)

```
POST /api/v1/cafe-requests/{request_id}/approve
  Auth: manager
  Response: LinkRequest
  Status: 200 OK
```

Links the cafe to the Telegram chat and enables notifications.

### POST /api/v1/cafe-requests/{request_id}/reject
Reject a cafe link request (manager only)

```
POST /api/v1/cafe-requests/{request_id}/reject
  Auth: manager
  Response: LinkRequest
  Status: 200 OK
```

### PATCH /api/v1/cafes/{cafe_id}/notifications
Enable/disable notifications for a cafe (manager only)

```
PATCH /api/v1/cafes/{cafe_id}/notifications
  Auth: manager
  Body: {
    enabled: bool
  }
  Response: Cafe
```

### DELETE /api/v1/cafes/{cafe_id}/link
Unlink Telegram from cafe (manager only)

```
DELETE /api/v1/cafes/{cafe_id}/link
  Auth: manager
  Response: 204 No Content
```

Removes Telegram link and disables notifications.

---

## Recommendations

### GET /api/v1/users/{tgid}/recommendations
Get personalized food recommendations for a user

```
GET /api/v1/users/{tgid}/recommendations
  Auth: manager | self
  Response: RecommendationsResponse
```

**RecommendationsResponse schema:**
```
RecommendationsResponse {
  summary: string | null            # AI-generated summary of eating habits
  tips: string[]                    # Personalized recommendations
  stats: OrderStats                 # Current order statistics
  generated_at: datetime | null     # When recommendations were generated
}

OrderStats {
  orders_count: int                    # Number of orders in last 30 days
  categories: {                        # Category distribution (percentages)
    "soup": float,
    "salad": float,
    "main": float,
    "extra": float
  }
  unique_dishes: int                   # Number of unique dishes ordered
  total_dishes_available: int          # Total dishes available in menu
  favorite_dishes: [{                  # Top 5 most ordered dishes
    name: string,
    count: int
  }]
}
```

**Notes:**
- Recommendations are generated nightly by a batch worker
- Returns cached data from Redis (TTL: 24 hours)
- If no recommendations available, returns empty `summary` and `tips` with current stats
- Requires minimum 5 orders in last 30 days for generation

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
