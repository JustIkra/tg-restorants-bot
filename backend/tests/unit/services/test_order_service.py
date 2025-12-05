"""Tests for OrderService."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from src.models.order import Order
from src.schemas.order import OrderCreate, OrderUpdate
from src.services.order import OrderService


@pytest.mark.asyncio
async def test_list_orders_user(db_session, test_user, test_order):
    """Test user can list their own orders."""
    service = OrderService(db_session)

    orders = await service.list_orders(user_tgid=test_user.tgid, is_manager=False)

    assert len(orders) == 1
    assert orders[0].id == test_order.id
    assert orders[0].user_tgid == test_user.tgid


@pytest.mark.asyncio
async def test_list_orders_manager_all(db_session, test_manager, test_order):
    """Test manager can list all orders."""
    service = OrderService(db_session)

    orders = await service.list_orders(is_manager=True)

    assert len(orders) == 1
    assert orders[0].id == test_order.id


@pytest.mark.asyncio
async def test_get_order_success(db_session, test_order):
    """Test getting an order by ID."""
    service = OrderService(db_session)

    order = await service.get_order(test_order.id)

    assert order.id == test_order.id
    assert order.total_price == test_order.total_price


@pytest.mark.asyncio
async def test_get_order_not_found(db_session):
    """Test getting non-existent order raises 404."""
    service = OrderService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_order(999999)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_order_success(
    db_session,
    test_user,
    test_cafe,
    test_combo,
    test_menu_items,
    test_deadline,
):
    """Test creating an order successfully."""
    service = OrderService(db_session)

    # Create order for tomorrow (within deadline)
    order_date = date.today() + timedelta(days=2)

    order_data = OrderCreate(
        cafe_id=test_cafe.id,
        order_date=order_date,
        combo_id=test_combo.id,
        combo_items=[
            {"category": "soup", "menu_item_id": test_menu_items[0].id},
            {"category": "main", "menu_item_id": test_menu_items[1].id},
            {"category": "salad", "menu_item_id": test_menu_items[2].id},
        ],
        extras=[{"menu_item_id": test_menu_items[3].id, "quantity": 1}],
        notes="Test order",
    )

    order = await service.create_order(test_user.tgid, order_data)

    assert order.user_tgid == test_user.tgid
    assert order.cafe_id == test_cafe.id
    assert order.combo_id == test_combo.id
    assert order.total_price == Decimal("17.50")  # 15.00 + 2.50
    assert order.notes == "Test order"


@pytest.mark.asyncio
async def test_update_order_success(db_session, test_user, test_order, test_deadline):
    """Test updating an order."""
    service = OrderService(db_session)

    update_data = OrderUpdate(notes="Updated notes")

    updated_order = await service.update_order(
        test_order.id,
        test_user.tgid,
        is_manager=False,
        data=update_data,
    )

    assert updated_order.notes == "Updated notes"


@pytest.mark.asyncio
async def test_update_order_not_owner_forbidden(
    db_session, test_manager, test_order
):
    """Test non-owner cannot update order."""
    service = OrderService(db_session)

    update_data = OrderUpdate(notes="Hacked notes")

    # test_manager trying to update test_order (owned by test_user)
    with pytest.raises(HTTPException) as exc_info:
        await service.update_order(
            test_order.id,
            test_manager.tgid,  # Different user
            is_manager=False,
            data=update_data,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_order_success(db_session, test_user, test_order, test_deadline):
    """Test deleting an order."""
    service = OrderService(db_session)

    await service.delete_order(
        test_order.id,
        test_user.tgid,
        is_manager=False,
    )

    # Verify order is deleted
    with pytest.raises(HTTPException):
        await service.get_order(test_order.id)


@pytest.mark.asyncio
async def test_delete_order_not_owner_forbidden(
    db_session, test_manager, test_order
):
    """Test non-owner cannot delete order."""
    service = OrderService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_order(
            test_order.id,
            test_manager.tgid,  # Different user
            is_manager=False,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_manager_can_delete_any_order(
    db_session, test_manager, test_order
):
    """Test manager can delete any order."""
    service = OrderService(db_session)

    # Manager can delete order owned by test_user
    await service.delete_order(
        test_order.id,
        test_manager.tgid,
        is_manager=True,
    )

    # Verify order is deleted
    with pytest.raises(HTTPException):
        await service.get_order(test_order.id)
