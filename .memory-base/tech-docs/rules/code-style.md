# Code Style

Стек проекта: @.memory-base/tech-docs/stack.md

## Python (>= 3.13)

### Форматирование
- **Formatter/Linter:** Ruff >= 0.14.0
- **Line length:** 100 символов
- **Quotes:** двойные `"`
- **Imports:** сортировка через Ruff (isort совместимый)

### Именование
- `snake_case` — переменные, функции, методы
- `PascalCase` — классы, Pydantic модели
- `UPPER_CASE` — константы
- `_private` — приватные атрибуты

### Type Hints (Python 3.13+)

```python
# Используй встроенный синтаксис, не typing модуль
def get_user(tgid: int) -> User | None:
    ...

# Generics с новым синтаксом (PEP 695)
def first[T](items: list[T]) -> T:
    return items[0]

# Bounded type variables
class Repository[T: BaseModel]:
    async def get(self, id: int) -> T | None: ...

# Для сложных случаев
from typing import Annotated
UserId = Annotated[int, "Telegram user ID"]
```

### Pydantic Models (>= 2.12)

```python
from pydantic import BaseModel, Field

class OrderCreate(BaseModel):
    cafe_id: int
    order_date: date
    items: list[OrderItemCreate]
    notes: str | None = None

class OrderResponse(BaseModel):
    id: int
    status: str
    total_price: Decimal = Field(decimal_places=2)

    model_config = {"from_attributes": True}
```

### SQLAlchemy (>= 2.0, async)

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_tgid: Mapped[int] = mapped_column(ForeignKey("users.tgid"))
    status: Mapped[str] = mapped_column(default="pending")

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
```

### FastAPI (>= 0.120)

```python
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Order:
    ...
```

### FastStream (Kafka, >= 0.6.3)

```python
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")

@broker.subscriber("deadline.passed")
async def handle_deadline(event: DeadlineEvent) -> None:
    ...
```

### Docstrings
- Только для сложной бизнес-логики
- Google style формат
- Не добавлять к очевидным методам

---

## TypeScript/React (Next.js 16 + Tailwind CSS 4)

**Location:** `frontend_mini_app/`

### Форматирование
- **Linter:** ESLint 9 + eslint-config-next
- **Framework:** Next.js 16 (App Router)
- **Styling:** Tailwind CSS 4 (utility classes)

### Структура проекта

```
frontend_mini_app/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   └── globals.css   # Global styles + Tailwind
│   └── components/       # React components
│       ├── CafeSelector/
│       ├── CategorySelector/
│       ├── Menu/
│       └── Cart/
├── public/               # Static assets
└── package.json
```

### Компоненты

```tsx
import React from "react";

// TypeScript интерфейсы для props
interface DishCardProps {
  dish: Dish;
  quantity: number;
  onAdd: (id: number) => void;
  onRemove: (id: number) => void;
}

// Functional component с React.FC
const DishCard: React.FC<DishCardProps> = ({ dish, quantity, onAdd, onRemove }) => (
  <div className="bg-[#7B6F9C]/20 rounded-[12px] p-4">
    <h4 className="text-white font-medium">{dish.name}</h4>
    <p className="text-gray-300 text-sm">{dish.description}</p>
    <span className="text-white font-bold">{dish.price} ₽</span>
  </div>
);

export default DishCard;
```

### Client Components

```tsx
"use client";  // Обязательно для useState, useEffect, event handlers

import { useState } from "react";

export default function InteractiveComponent() {
  const [state, setState] = useState<number>(0);
  return <button onClick={() => setState(s => s + 1)}>{state}</button>;
}
```

### Импорты

```tsx
// React и hooks
import { useState, useEffect } from "react";

// Next.js
import type { Metadata } from "next";
import { Geist } from "next/font/google";

// Иконки
import { FaCartShopping, FaBowlFood } from "react-icons/fa6";

// Компоненты (@ = src/)
import CafeSelector from "@/components/CafeSelector/CafeSelector";
```

### Tailwind CSS

```tsx
// Цветовая схема проекта
const colors = {
  background: "#130F30",        // темный фон
  accent: "#A020F0",            // фиолетовый акцент
  accentDark: "#8B23CB",        // темный акцент
  card: "#7B6F9C",              // карточки (с opacity)
  text: "white",
  textMuted: "gray-300",
};

// Пример компонента
<div className="bg-[#130F30] min-h-screen">
  <div className="bg-[#7B6F9C]/20 backdrop-blur-sm rounded-xl p-4">
    <h1 className="text-white font-bold text-2xl">Title</h1>
    <p className="text-gray-300 text-sm">Description</p>
  </div>
</div>

// Градиенты
<button className="bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white">
  Action
</button>
```

### Типы

```tsx
// Определение типов рядом с компонентом или в отдельном файле
type Cafe = { id: number; name: string };
type Category = { id: number; name: string; icon: React.ReactNode };
type Dish = {
  id: number;
  name: string;
  description: string;
  price: number;
  categoryId: number;
};

// Cart как Record
type Cart = { [dishId: number]: number };
```

### State Management

```tsx
// Локальный state для UI
const [activeCafeId, setActiveCafeId] = useState<number>(1);
const [cart, setCart] = useState<Cart>({});

// Handlers
const addToCart = (dishId: number) =>
  setCart(prev => ({ ...prev, [dishId]: (prev[dishId] || 0) + 1 }));

const removeFromCart = (dishId: number) =>
  setCart(prev => {
    const copy = { ...prev };
    if (copy[dishId] > 1) copy[dishId]--;
    else delete copy[dishId];
    return copy;
  });
```
