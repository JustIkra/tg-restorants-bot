from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Combo, MenuItem, Order, Summary


class SummaryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, summary_id: int) -> Summary | None:
        result = await self.session.execute(
            select(Summary).where(Summary.id == summary_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        cafe_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Summary]:
        query = select(Summary)

        if cafe_id:
            query = query.where(Summary.cafe_id == cafe_id)

        query = query.order_by(Summary.date.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Summary:
        summary = Summary(**kwargs)
        self.session.add(summary)
        await self.session.flush()
        return summary

    async def delete(self, summary: Summary) -> None:
        await self.session.delete(summary)
        await self.session.flush()

    async def get_orders_for_date(
        self, cafe_id: int, order_date: date
    ) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.cafe_id == cafe_id)
            .where(Order.order_date == order_date)
            .where(Order.status != "cancelled")
        )
        return list(result.scalars().all())

    async def get_combo(self, combo_id: int) -> Combo | None:
        result = await self.session.execute(
            select(Combo).where(Combo.id == combo_id)
        )
        return result.scalar_one_or_none()

    async def get_menu_item(self, item_id: int) -> MenuItem | None:
        result = await self.session.execute(
            select(MenuItem).where(MenuItem.id == item_id)
        )
        return result.scalar_one_or_none()
