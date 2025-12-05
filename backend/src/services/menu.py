from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.menu import ComboRepository, MenuItemRepository
from ..schemas.menu import ComboCreate, ComboUpdate, MenuItemCreate, MenuItemUpdate


class MenuService:
    def __init__(self, session: AsyncSession):
        self.combo_repo = ComboRepository(session)
        self.item_repo = MenuItemRepository(session)

    async def list_combos(self, cafe_id: int, available_only: bool = False):
        return await self.combo_repo.list_by_cafe(cafe_id, available_only=available_only)

    async def get_combo(self, combo_id: int):
        combo = await self.combo_repo.get(combo_id)
        if not combo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Combo not found")
        return combo

    async def create_combo(self, cafe_id: int, data: ComboCreate):
        return await self.combo_repo.create(
            cafe_id=cafe_id, name=data.name, categories=data.categories, price=data.price
        )

    async def update_combo(self, cafe_id: int, combo_id: int, data: ComboUpdate):
        combo = await self.get_combo(combo_id)
        if combo.cafe_id != cafe_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Combo not found in this cafe")
        return await self.combo_repo.update(combo, **data.model_dump(exclude_unset=True))

    async def delete_combo(self, cafe_id: int, combo_id: int):
        combo = await self.get_combo(combo_id)
        if combo.cafe_id != cafe_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Combo not found in this cafe")
        await self.combo_repo.delete(combo)

    async def list_menu_items(self, cafe_id: int, category: str | None = None, available_only: bool = False):
        return await self.item_repo.list_by_cafe(cafe_id, category=category, available_only=available_only)

    async def get_menu_item(self, item_id: int):
        item = await self.item_repo.get(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        return item

    async def create_menu_item(self, cafe_id: int, data: MenuItemCreate):
        return await self.item_repo.create(
            cafe_id=cafe_id, name=data.name, description=data.description,
            category=data.category, price=data.price
        )

    async def update_menu_item(self, cafe_id: int, item_id: int, data: MenuItemUpdate):
        item = await self.get_menu_item(item_id)
        if item.cafe_id != cafe_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found in this cafe")
        return await self.item_repo.update(item, **data.model_dump(exclude_unset=True))

    async def delete_menu_item(self, cafe_id: int, item_id: int):
        item = await self.get_menu_item(item_id)
        if item.cafe_id != cafe_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found in this cafe")
        await self.item_repo.delete(item)

    async def validate_combo_items(self, combo_id: int, combo_items: list[dict]) -> bool:
        combo = await self.get_combo(combo_id)
        required = set(combo.categories)
        provided = {item["category"] for item in combo_items}
        if required != provided:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Combo requires categories: {combo.categories}")
        for item in combo_items:
            menu_item = await self.item_repo.get(item["menu_item_id"])
            if not menu_item:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item {item['menu_item_id']} not found")
            if menu_item.category != item["category"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {item['menu_item_id']} is not in category {item['category']}")
        return True

    async def calculate_extras_price(self, extras: list[dict]) -> Decimal:
        total = Decimal("0")
        for extra in extras:
            item = await self.item_repo.get(extra["menu_item_id"])
            if not item:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Extra {extra['menu_item_id']} not found")
            if item.category != "extra":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {extra['menu_item_id']} is not an extra")
            if item.price:
                total += item.price * extra["quantity"]
        return total
