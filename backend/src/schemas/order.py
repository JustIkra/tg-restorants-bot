from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ComboItemInput(BaseModel):
    category: str = Field(..., pattern="^(soup|salad|main)$")
    menu_item_id: int = Field(..., gt=0)


class ExtraInput(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)


class OrderCreate(BaseModel):
    cafe_id: int
    order_date: date
    combo_id: int
    combo_items: list[ComboItemInput]
    extras: list[ExtraInput] = []
    notes: str | None = None


class OrderUpdate(BaseModel):
    combo_id: int | None = None
    combo_items: list[ComboItemInput] | None = None
    extras: list[ExtraInput] | None = None
    notes: str | None = None


class OrderResponse(BaseModel):
    id: int
    user_tgid: int
    cafe_id: int
    order_date: date
    status: str
    combo_id: int
    combo_items: list[dict]
    extras: list[dict]
    notes: str | None
    total_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
