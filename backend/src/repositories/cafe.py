from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Cafe

# Whitelist of fields that can be updated via repository
ALLOWED_UPDATE_FIELDS = {"name", "description", "is_active"}


class CafeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, cafe_id: int) -> Cafe | None:
        result = await self.session.execute(
            select(Cafe).where(Cafe.id == cafe_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Cafe]:
        query = select(Cafe)

        if active_only:
            query = query.where(Cafe.is_active == True)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Cafe:
        cafe = Cafe(**kwargs)
        self.session.add(cafe)
        await self.session.flush()
        return cafe

    async def update(self, cafe: Cafe, **kwargs) -> Cafe:
        for key, value in kwargs.items():
            if key not in ALLOWED_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            if value is not None:
                setattr(cafe, key, value)
        await self.session.flush()
        return cafe

    async def delete(self, cafe: Cafe) -> None:
        await self.session.delete(cafe)
        await self.session.flush()
