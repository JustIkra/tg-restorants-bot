from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ComboItemInput(BaseModel):
    category: str = Field(..., pattern="^(soup|salad|main)$")
    menu_item_id: int = Field(..., gt=0)


class ExtraInput(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)


# New types for order items (combo vs standalone)
class ComboItem(BaseModel):
    type: Literal["combo"] = "combo"
    category: str = Field(..., pattern="^(soup|salad|main)$")
    menu_item_id: int = Field(..., gt=0)


class StandaloneItem(BaseModel):
    type: Literal["standalone"] = "standalone"
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)
    options: dict[str, str] = {}


# Union for discriminated union
OrderItem = ComboItem | StandaloneItem


class OrderCreate(BaseModel):
    cafe_id: int
    order_date: date
    combo_id: int | None = None
    items: list[OrderItem]
    extras: list[ExtraInput] = []
    notes: str | None = None

    @model_validator(mode='before')
    @classmethod
    def migrate_combo_items(cls, data):
        """Migrate old combo_items field to items for backward compatibility."""
        if isinstance(data, dict) and 'combo_items' in data and 'items' not in data:
            # Convert combo_items to items with type="combo"
            data['items'] = [
                {'type': 'combo', **item} for item in data['combo_items']
            ]
        return data


class OrderUpdate(BaseModel):
    combo_id: int | None = None
    items: list[OrderItem] | None = None
    extras: list[ExtraInput] | None = None
    notes: str | None = None

    @model_validator(mode='before')
    @classmethod
    def migrate_combo_items(cls, data):
        """Migrate old combo_items field to items for backward compatibility."""
        if isinstance(data, dict) and 'combo_items' in data and 'items' not in data:
            # Convert combo_items to items with type="combo"
            data['items'] = [
                {'type': 'combo', **item} for item in data['combo_items']
            ]
        return data


class OrderResponse(BaseModel):
    id: int
    user_tgid: int
    cafe_id: int
    order_date: date
    status: str
    combo_id: int | None
    items: list[dict]
    extras: list[dict]
    notes: str | None
    total_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
