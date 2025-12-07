from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Combo, MenuItem, MenuItemOption

# Whitelists of fields that can be updated via repository
ALLOWED_COMBO_UPDATE_FIELDS: set[str] = {"name", "categories", "price", "is_available"}
ALLOWED_MENU_ITEM_UPDATE_FIELDS: set[str] = {"name", "description", "category", "price", "is_available"}
ALLOWED_MENU_ITEM_OPTION_UPDATE_FIELDS: set[str] = {"name", "values", "is_required"}


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
            select(MenuItem).options(selectinload(MenuItem.options)).where(MenuItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def list_by_cafe(
        self,
        cafe_id: int,
        category: str | None = None,
        available_only: bool = False,
    ) -> list[MenuItem]:
        query = select(MenuItem).options(selectinload(MenuItem.options)).where(MenuItem.cafe_id == cafe_id)
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
        await self.session.refresh(item, ["options"])
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


class MenuItemOptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, option_id: int) -> MenuItemOption | None:
        result = await self.session.execute(
            select(MenuItemOption).where(MenuItemOption.id == option_id)
        )
        return result.scalar_one_or_none()

    async def list_by_menu_item(self, menu_item_id: int) -> list[MenuItemOption]:
        result = await self.session.execute(
            select(MenuItemOption)
            .where(MenuItemOption.menu_item_id == menu_item_id)
            .order_by(MenuItemOption.id)
        )
        return list(result.scalars().all())

    async def create(self, menu_item_id: int, **kwargs) -> MenuItemOption:
        option = MenuItemOption(menu_item_id=menu_item_id, **kwargs)
        self.session.add(option)
        await self.session.flush()
        return option

    async def update(self, option: MenuItemOption, **kwargs) -> MenuItemOption:
        for key, value in kwargs.items():
            if key not in ALLOWED_MENU_ITEM_OPTION_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            if value is not None:
                setattr(option, key, value)
        await self.session.flush()
        return option

    async def delete(self, option: MenuItemOption) -> None:
        await self.session.delete(option)
        await self.session.flush()
