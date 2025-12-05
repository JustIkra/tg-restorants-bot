from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Order

# Whitelist of fields that can be updated via repository
ALLOWED_UPDATE_FIELDS = {"combo_id", "combo_items", "extras", "notes", "total_price", "status"}


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_tgid: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.user_tgid == user_tgid)
            .order_by(Order.order_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_cafe_and_date(
        self,
        cafe_id: int,
        order_date: date,
    ) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.cafe_id == cafe_id)
            .where(Order.order_date == order_date)
        )
        return list(result.scalars().all())

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        cafe_id: int | None = None,
        order_date: date | None = None,
    ) -> list[Order]:
        query = select(Order)

        if cafe_id:
            query = query.where(Order.cafe_id == cafe_id)

        if order_date:
            query = query.where(Order.order_date == order_date)

        query = query.order_by(Order.order_date.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Order:
        order = Order(**kwargs)
        self.session.add(order)
        await self.session.flush()
        return order

    async def update(self, order: Order, **kwargs) -> Order:
        for key, value in kwargs.items():
            if key not in ALLOWED_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            if value is not None:
                setattr(order, key, value)
        await self.session.flush()
        return order

    async def delete(self, order: Order) -> None:
        await self.session.delete(order)
        await self.session.flush()
