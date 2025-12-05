from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class SummaryCreate(BaseModel):
    cafe_id: int
    date: date


class SummaryResponse(BaseModel):
    id: int
    cafe_id: int
    date: date
    total_orders: int
    total_amount: Decimal
    breakdown: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class BreakdownItem(BaseModel):
    name: str
    quantity: int
    amount: Decimal


class DetailedBreakdown(BaseModel):
    combos: list[BreakdownItem]
    extras: list[BreakdownItem]
    total_orders: int
    total_amount: Decimal
