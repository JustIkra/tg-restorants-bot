from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Deadline


class DeadlineRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_cafe(self, cafe_id: int) -> list[Deadline]:
        result = await self.session.execute(
            select(Deadline).where(Deadline.cafe_id == cafe_id)
        )
        return list(result.scalars().all())

    async def get_for_weekday(self, cafe_id: int, weekday: int) -> Deadline | None:
        result = await self.session.execute(
            select(Deadline)
            .where(Deadline.cafe_id == cafe_id)
            .where(Deadline.weekday == weekday)
        )
        return result.scalar_one_or_none()

    async def delete_for_cafe(self, cafe_id: int) -> None:
        await self.session.execute(
            delete(Deadline).where(Deadline.cafe_id == cafe_id)
        )
        await self.session.flush()

    async def create(self, cafe_id: int, **kwargs) -> Deadline:
        deadline = Deadline(cafe_id=cafe_id, **kwargs)
        self.session.add(deadline)
        await self.session.flush()
        return deadline

    async def bulk_create(self, cafe_id: int, items: list[dict]) -> list[Deadline]:
        deadlines = []
        for item in items:
            deadline = Deadline(cafe_id=cafe_id, **item)
            self.session.add(deadline)
            deadlines.append(deadline)
        await self.session.flush()
        return deadlines
