from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser
from ..database import get_db
from ..schemas.deadline import AvailabilityResponse, WeekAvailabilityResponse
from ..schemas.order import OrderCreate, OrderResponse, OrderUpdate
from ..services.order import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(db: Annotated[AsyncSession, Depends(get_db)]) -> OrderService:
    return OrderService(db)


@router.get("/availability/{order_date}", response_model=AvailabilityResponse)
async def check_availability(
    order_date: date,
    cafe_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Check if ordering is available for a specific date."""
    return await service.check_availability(cafe_id, order_date)


@router.get("/availability/week", response_model=WeekAvailabilityResponse)
async def get_week_availability(
    cafe_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Get availability for the next 7 days."""
    return await service.get_week_availability(cafe_id)


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    cafe_id: int | None = None,
    order_date: date | None = None,
):
    """List orders (own orders for users, all orders for managers)."""
    is_manager = current_user.role == "manager"
    return await service.list_orders(
        user_tgid=current_user.tgid,
        is_manager=is_manager,
        skip=skip,
        limit=limit,
        cafe_id=cafe_id,
        order_date=order_date,
    )


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Create a new order."""
    return await service.create_order(current_user.tgid, data)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Get order by ID (owner or manager)."""
    order = await service.get_order(order_id)

    if current_user.role != "manager" and order.user_tgid != current_user.tgid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Update order (owner before deadline, or manager)."""
    return await service.update_order(
        order_id=order_id,
        user_tgid=current_user.tgid,
        is_manager=current_user.role == "manager",
        data=data,
    )


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: int,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Delete order (owner before deadline, or manager)."""
    await service.delete_order(
        order_id=order_id,
        user_tgid=current_user.tgid,
        is_manager=current_user.role == "manager",
    )
