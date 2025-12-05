from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Order, User

# Whitelist of fields that can be updated via repository
ALLOWED_UPDATE_FIELDS = {"name", "office", "role", "is_active", "weekly_limit"}


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tgid(self, tgid: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.tgid == tgid)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        role: str | None = None,
    ) -> list[User]:
        query = select(User)

        if search:
            query = query.where(
                User.name.ilike(f"%{search}%") | User.office.ilike(f"%{search}%")
            )

        if role:
            query = query.where(User.role == role)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if key not in ALLOWED_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            if value is not None:
                setattr(user, key, value)
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()

    async def get_spent_this_week(self, tgid: int) -> Decimal:
        """Calculate total spent by user this week (Monday to Sunday)."""
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        result = await self.session.execute(
            select(func.coalesce(func.sum(Order.total_price), 0))
            .where(Order.user_tgid == tgid)
            .where(Order.order_date >= monday)
            .where(Order.order_date <= sunday)
            .where(Order.status != "cancelled")
        )
        return Decimal(str(result.scalar_one()))
