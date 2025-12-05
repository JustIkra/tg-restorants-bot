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

## TypeScript/React

Стек: Vite + React + TypeScript

### Форматирование
- **Formatter:** Prettier
- **Linter:** ESLint

### Компоненты

```tsx
interface UserCardProps {
  user: User;
  onSelect: (id: number) => void;
}

export function UserCard({ user, onSelect }: UserCardProps) {
  return ...
}
```

### Импорты

```tsx
import { useState } from 'react';
import { Button } from '@telegram-apps/telegram-ui';
import { useUser } from '@/hooks/useUser';
import styles from './UserCard.module.css';
```
