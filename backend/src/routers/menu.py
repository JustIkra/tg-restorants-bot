from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser, ManagerUser
from ..database import get_db
from ..schemas.menu import (
    ComboCreate, ComboResponse, ComboUpdate,
    MenuItemCreate, MenuItemResponse, MenuItemUpdate,
)
from ..services.menu import MenuService

router = APIRouter(tags=["menu"])


def get_menu_service(db: Annotated[AsyncSession, Depends(get_db)]) -> MenuService:
    return MenuService(db)


@router.get("/cafes/{cafe_id}/combos", response_model=list[ComboResponse])
async def list_combos(
    cafe_id: int,
    current_user: CurrentUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
    available_only: bool = Query(True),
):
    if current_user.role != "manager":
        available_only = True
    return await service.list_combos(cafe_id, available_only=available_only)


@router.post("/cafes/{cafe_id}/combos", response_model=ComboResponse, status_code=201)
async def create_combo(
    cafe_id: int, data: ComboCreate, manager: ManagerUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
):
    return await service.create_combo(cafe_id, data)


@router.patch("/cafes/{cafe_id}/combos/{combo_id}", response_model=ComboResponse)
async def update_combo(
    cafe_id: int, combo_id: int, data: ComboUpdate, manager: ManagerUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
):
    return await service.update_combo(cafe_id, combo_id, data)


@router.delete("/cafes/{cafe_id}/combos/{combo_id}", status_code=204)
async def delete_combo(
    cafe_id: int, combo_id: int, manager: ManagerUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
):
    await service.delete_combo(cafe_id, combo_id)


@router.get("/cafes/{cafe_id}/menu", response_model=list[MenuItemResponse])
async def list_menu_items(
    cafe_id: int,
    current_user: CurrentUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
    category: str | None = None,
    available_only: bool = Query(True),
):
    if current_user.role != "manager":
        available_only = True
    return await service.list_menu_items(cafe_id, category=category, available_only=available_only)


@router.post("/cafes/{cafe_id}/menu", response_model=MenuItemResponse, status_code=201)
async def create_menu_item(
    cafe_id: int, data: MenuItemCreate, manager: ManagerUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
):
    return await service.create_menu_item(cafe_id, data)


@router.get("/cafes/{cafe_id}/menu/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    cafe_id: int, item_id: int, current_user: CurrentUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
):
    item = await service.get_menu_item(item_id)
    if item.cafe_id != cafe_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    return item


@router.patch("/cafes/{cafe_id}/menu/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    cafe_id: int, item_id: int, data: MenuItemUpdate, manager: ManagerUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
):
    return await service.update_menu_item(cafe_id, item_id, data)


@router.delete("/cafes/{cafe_id}/menu/{item_id}", status_code=204)
async def delete_menu_item(
    cafe_id: int, item_id: int, manager: ManagerUser,
    service: Annotated[MenuService, Depends(get_menu_service)],
):
    await service.delete_menu_item(cafe_id, item_id)
