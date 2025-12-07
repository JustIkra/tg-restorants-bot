from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.order import OrderRepository
from ..schemas.order import OrderCreate, OrderUpdate
from .deadline import DeadlineService
from .menu import MenuService


class OrderService:
    def __init__(self, session: AsyncSession):
        self.repo = OrderRepository(session)
        self.deadline_service = DeadlineService(session)
        self.menu_service = MenuService(session)

    async def list_orders(
        self,
        user_tgid: int | None = None,
        is_manager: bool = False,
        skip: int = 0,
        limit: int = 100,
        cafe_id: int | None = None,
        order_date: date | None = None,
    ):
        if is_manager:
            return await self.repo.list_all(
                skip=skip, limit=limit, cafe_id=cafe_id, order_date=order_date
            )
        else:
            return await self.repo.list_by_user(user_tgid, skip=skip, limit=limit)

    async def get_order(self, order_id: int):
        order = await self.repo.get(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return order

    async def create_order(self, user_tgid: int, data: OrderCreate):
        # 1. Validate deadline
        await self.deadline_service.validate_order_deadline(data.cafe_id, data.order_date)

        items_dict = [item.model_dump() for item in data.items]
        extras_dict = [extra.model_dump() for extra in data.extras]

        # 2. Validate items based on combo_id
        if data.combo_id:
            # Combo order - validate combo items
            combo_items = [item for item in items_dict if item.get("type") == "combo"]
            if not combo_items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Combo order requires at least one combo item"
                )
            await self.menu_service.validate_combo_items(data.combo_id, combo_items)

            # Also validate any standalone items
            standalone_items = [item for item in items_dict if item.get("type") == "standalone"]
            if standalone_items:
                await self.menu_service.validate_standalone_items(standalone_items)
        else:
            # Standalone order - all items must be standalone
            for item in items_dict:
                if item.get("type") == "combo":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Combo items require combo_id to be set"
                    )
            await self.menu_service.validate_standalone_items(items_dict)

        # 3. Calculate total price
        combo_price = Decimal("0")
        if data.combo_id:
            combo = await self.menu_service.get_combo(data.combo_id)
            combo_price = combo.price

        standalone_items = [item for item in items_dict if item.get("type") == "standalone"]
        standalone_price = await self.menu_service.calculate_standalone_price(standalone_items)

        extras_price = await self.menu_service.calculate_extras_price(extras_dict)
        total_price = combo_price + standalone_price + extras_price

        # 4. Create order
        return await self.repo.create(
            user_tgid=user_tgid,
            cafe_id=data.cafe_id,
            order_date=data.order_date,
            combo_id=data.combo_id,
            items=items_dict,  # Используем items вместо combo_items
            extras=extras_dict,
            notes=data.notes,
            total_price=total_price,
        )

    async def update_order(
        self,
        order_id: int,
        user_tgid: int,
        is_manager: bool,
        data: OrderUpdate,
    ):
        order = await self.get_order(order_id)

        # Check ownership
        if not is_manager and order.user_tgid != user_tgid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Check deadline (unless manager)
        if not is_manager:
            await self.deadline_service.validate_order_deadline(
                order.cafe_id, order.order_date
            )

        update_data = {}

        # Update combo if changed
        if data.combo_id is not None:
            update_data["combo_id"] = data.combo_id

        # Update items if changed
        if data.items is not None:
            combo_id = data.combo_id if data.combo_id is not None else order.combo_id
            items_dict = [item.model_dump() for item in data.items]

            # Validate items based on combo_id
            if combo_id:
                # Combo order - validate combo items
                combo_items = [item for item in items_dict if item.get("type") == "combo"]
                await self.menu_service.validate_combo_items(combo_id, combo_items)

                # Also validate any standalone items
                standalone_items = [item for item in items_dict if item.get("type") == "standalone"]
                if standalone_items:
                    await self.menu_service.validate_standalone_items(standalone_items)
            else:
                # Standalone order - all items must be standalone
                for item in items_dict:
                    if item.get("type") == "combo":
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Combo items require combo_id to be set"
                        )
                await self.menu_service.validate_standalone_items(items_dict)

            update_data["items"] = items_dict

        # Update extras if changed
        if data.extras is not None:
            extras_dict = [extra.model_dump() for extra in data.extras]
            update_data["extras"] = extras_dict

        # Update notes if changed
        if data.notes is not None:
            update_data["notes"] = data.notes

        # Recalculate total price if needed
        if data.combo_id is not None or data.items is not None or data.extras is not None:
            combo_id = update_data.get("combo_id") if "combo_id" in update_data else order.combo_id
            items = update_data.get("items", order.items)
            extras = update_data.get("extras", order.extras)

            # Calculate combo price
            combo_price = Decimal("0")
            if combo_id:
                combo = await self.menu_service.get_combo(combo_id)
                combo_price = combo.price

            # Calculate standalone price
            standalone_items = [item for item in items if item.get("type") == "standalone"]
            standalone_price = await self.menu_service.calculate_standalone_price(standalone_items)

            # Calculate extras price
            extras_price = await self.menu_service.calculate_extras_price(extras)

            update_data["total_price"] = combo_price + standalone_price + extras_price

        return await self.repo.update(order, **update_data)

    async def delete_order(
        self,
        order_id: int,
        user_tgid: int,
        is_manager: bool,
    ):
        order = await self.get_order(order_id)

        # Check ownership (manager can delete any)
        if not is_manager and order.user_tgid != user_tgid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Check deadline (unless manager)
        if not is_manager:
            await self.deadline_service.validate_order_deadline(
                order.cafe_id, order.order_date
            )

        await self.repo.delete(order)

    async def check_availability(self, cafe_id: int, order_date: date):
        return await self.deadline_service.check_availability(cafe_id, order_date)

    async def get_week_availability(self, cafe_id: int):
        return await self.deadline_service.get_week_availability(cafe_id)
