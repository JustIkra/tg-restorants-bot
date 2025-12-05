from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Combo, MenuItem

# Whitelists of fields that can be updated via repository
ALLOWED_COMBO_UPDATE_FIELDS = {"name", "categories", "price", "is_available"}
ALLOWED_MENU_ITEM_UPDATE_FIELDS = {"name", "description", "category", "price", "is_available"}


class ComboRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, combo_id: int) -> Combo | None:
        result = await self.session.execute(
            select(Combo).where(Combo.id == combo_id)
        )
        return result.scalar_one_or_none()

    async def list_by_cafe(
        self,
        cafe_id: int,
        available_only: bool = False,
    ) -> list[Combo]:
        query = select(Combo).where(Combo.cafe_id == cafe_id)
        if available_only:
            query = query.where(Combo.is_available == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, cafe_id: int, **kwargs) -> Combo:
        combo = Combo(cafe_id=cafe_id, **kwargs)
        self.session.add(combo)
        await self.session.flush()
        return combo

    async def update(self, combo: Combo, **kwargs) -> Combo:
        for key, value in kwargs.items():
            if key not in ALLOWED_COMBO_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            if value is not None:
                setattr(combo, key, value)
        await self.session.flush()
        return combo

    async def delete(self, combo: Combo) -> None:
        await self.session.delete(combo)
        await self.session.flush()


class MenuItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, item_id: int) -> MenuItem | None:
        result = await self.session.execute(
            select(MenuItem).where(MenuItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def list_by_cafe(
        self,
        cafe_id: int,
        category: str | None = None,
        available_only: bool = False,
    ) -> list[MenuItem]:
        query = select(MenuItem).where(MenuItem.cafe_id == cafe_id)
        if category:
            query = query.where(MenuItem.category == category)
        if available_only:
            query = query.where(MenuItem.is_available == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, cafe_id: int, **kwargs) -> MenuItem:
        item = MenuItem(cafe_id=cafe_id, **kwargs)
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(self, item: MenuItem, **kwargs) -> MenuItem:
        for key, value in kwargs.items():
            if key not in ALLOWED_MENU_ITEM_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            if value is not None:
                setattr(item, key, value)
        await self.session.flush()
        return item

    async def delete(self, item: MenuItem) -> None:
        await self.session.delete(item)
        await self.session.flush()
