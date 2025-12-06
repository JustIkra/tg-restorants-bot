"""Integration test for full order flow: Auth -> Cafes -> Combos -> Menu -> Order."""

import hashlib
import hmac
import json
import time
from datetime import date, timedelta
from urllib.parse import urlencode

import pytest
from sqlalchemy import select

from src.models.order import Order


def generate_telegram_init_data(user_data: dict, bot_token: str) -> str:
    """Generate valid Telegram WebApp initData."""
    auth_date = int(time.time())

    data = {
        "auth_date": str(auth_date),
        "user": json.dumps(user_data),
    }

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    data["hash"] = calculated_hash
    return urlencode(data)


@pytest.mark.asyncio
async def test_full_order_flow(
    client,
    db_session,
    test_cafe,
    test_combo,
    test_menu_items,
    test_deadline,
):
    """
    Test complete user flow from authentication to order creation.

    Flow:
    1. Authenticate via Telegram initData (mock)
    2. Get list of cafes
    3. Get combos for selected cafe
    4. Get menu items for selected cafe
    5. Create order with combo and extras
    6. Verify order is saved in database
    """
    # Step 1: Authenticate via Telegram WebApp initData
    user_data = {
        "id": 999888777,
        "first_name": "Integration",
        "last_name": "Test",
        "username": "integrationtest",
        "language_code": "en",
    }

    init_data = generate_telegram_init_data(
        user_data, "test_bot_token_123456:ABCdefGHIjklMNOpqrsTUVwxyz"
    )

    auth_response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Test Office"},
    )

    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    assert "access_token" in auth_data
    assert auth_data["user"]["tgid"] == 999888777
    assert auth_data["user"]["name"] == "Integration Test"

    # Extract auth token for subsequent requests
    auth_token = auth_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # Step 2: Get list of cafes
    cafes_response = await client.get("/api/v1/cafes?active_only=true", headers=auth_headers)

    assert cafes_response.status_code == 200
    cafes_data = cafes_response.json()
    assert isinstance(cafes_data, list)
    assert len(cafes_data) >= 1

    # Verify our test cafe is in the list
    cafe_ids = [cafe["id"] for cafe in cafes_data]
    assert test_cafe.id in cafe_ids

    # Select the test cafe
    selected_cafe_id = test_cafe.id

    # Step 3: Get combos for selected cafe
    combos_response = await client.get(
        f"/api/v1/cafes/{selected_cafe_id}/combos",
        headers=auth_headers,
    )

    assert combos_response.status_code == 200
    combos_data = combos_response.json()
    assert isinstance(combos_data, list)
    assert len(combos_data) >= 1
    assert combos_data[0]["id"] == test_combo.id
    assert combos_data[0]["name"] == "Combo A"
    assert combos_data[0]["categories"] == ["soup", "main", "salad"]

    # Step 4: Get menu items for selected cafe
    menu_response = await client.get(
        f"/api/v1/cafes/{selected_cafe_id}/menu",
        headers=auth_headers,
    )

    assert menu_response.status_code == 200
    menu_data = menu_response.json()
    assert isinstance(menu_data, list)
    assert len(menu_data) >= 3  # At least soup, main, salad

    # Verify menu items are available
    menu_item_ids = [item["id"] for item in menu_data]
    assert test_menu_items[0].id in menu_item_ids  # soup
    assert test_menu_items[1].id in menu_item_ids  # main
    assert test_menu_items[2].id in menu_item_ids  # salad

    # Get extras
    extras_response = await client.get(
        f"/api/v1/cafes/{selected_cafe_id}/menu?category=extra",
        headers=auth_headers,
    )

    assert extras_response.status_code == 200
    extras_data = extras_response.json()
    assert isinstance(extras_data, list)
    assert len(extras_data) >= 1
    assert extras_data[0]["id"] == test_menu_items[3].id  # Coffee
    assert extras_data[0]["category"] == "extra"

    # Step 5: Create order with combo items and extras
    # Order for 2 days from now (should be before deadline)
    order_date = date.today() + timedelta(days=2)

    order_payload = {
        "cafe_id": selected_cafe_id,
        "order_date": str(order_date),
        "combo_id": test_combo.id,
        "combo_items": [
            {"category": "soup", "menu_item_id": test_menu_items[0].id},
            {"category": "main", "menu_item_id": test_menu_items[1].id},
            {"category": "salad", "menu_item_id": test_menu_items[2].id},
        ],
        "extras": [
            {"menu_item_id": test_menu_items[3].id, "quantity": 2}  # 2 coffees
        ],
        "notes": "Integration test order - no onions please",
    }

    order_response = await client.post(
        "/api/v1/orders",
        headers=auth_headers,
        json=order_payload,
    )

    assert order_response.status_code == 201
    order_data = order_response.json()

    # Verify order details
    assert order_data["cafe_id"] == selected_cafe_id
    assert order_data["user_tgid"] == 999888777
    assert order_data["combo_id"] == test_combo.id
    assert order_data["status"] == "pending"
    assert order_data["notes"] == "Integration test order - no onions please"

    # Verify combo items
    assert len(order_data["combo_items"]) == 3
    combo_categories = [item["category"] for item in order_data["combo_items"]]
    assert "soup" in combo_categories
    assert "main" in combo_categories
    assert "salad" in combo_categories

    # Verify extras
    assert len(order_data["extras"]) == 1
    assert order_data["extras"][0]["menu_item_id"] == test_menu_items[3].id
    assert order_data["extras"][0]["quantity"] == 2

    # Verify total price calculation
    # Combo A: 15.00, Coffee x2: 2.50 * 2 = 5.00, Total: 20.00
    expected_total = 20.00
    assert float(order_data["total_price"]) == expected_total

    # Step 6: Verify order is saved in database
    order_id = order_data["id"]

    # Query database directly to verify persistence
    result = await db_session.execute(
        select(Order).where(Order.id == order_id)
    )
    db_order = result.scalar_one_or_none()

    assert db_order is not None
    assert db_order.user_tgid == 999888777
    assert db_order.cafe_id == selected_cafe_id
    assert db_order.combo_id == test_combo.id
    assert db_order.status == "pending"
    assert db_order.notes == "Integration test order - no onions please"
    assert float(db_order.total_price) == expected_total

    # Verify combo items are stored correctly
    assert len(db_order.combo_items) == 3

    # Verify extras are stored correctly
    assert len(db_order.extras) == 1
    assert db_order.extras[0]["quantity"] == 2

    # Additional: Verify order appears in user's order list
    orders_list_response = await client.get(
        "/api/v1/orders",
        headers=auth_headers,
    )

    assert orders_list_response.status_code == 200
    orders_list = orders_list_response.json()
    assert isinstance(orders_list, list)
    assert len(orders_list) >= 1

    # Find our order in the list
    created_order = next((o for o in orders_list if o["id"] == order_id), None)
    assert created_order is not None
    assert float(created_order["total_price"]) == expected_total


@pytest.mark.asyncio
async def test_order_after_deadline_fails(
    client,
    db_session,
    test_cafe,
    test_combo,
    test_menu_items,
    test_deadline,
):
    """Test that creating order after deadline fails with 400 error."""
    # Create and authenticate user
    user_data = {
        "id": 111222333,
        "first_name": "Late",
        "last_name": "User",
        "username": "lateuser",
    }

    init_data = generate_telegram_init_data(
        user_data, "test_bot_token_123456:ABCdefGHIjklMNOpqrsTUVwxyz"
    )

    auth_response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Test Office"},
    )

    assert auth_response.status_code == 200
    auth_token = auth_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # Try to order for today (should fail - past deadline)
    order_date = date.today()

    order_payload = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": test_combo.id,
        "combo_items": [
            {"category": "soup", "menu_item_id": test_menu_items[0].id},
        ],
        "extras": [],
    }

    order_response = await client.post(
        "/api/v1/orders",
        headers=auth_headers,
        json=order_payload,
    )

    # Should fail with 400 (deadline passed or invalid order date)
    assert order_response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_order_with_invalid_combo_fails(
    client,
    db_session,
    test_cafe,
    test_combo,
    test_menu_items,
    test_deadline,
):
    """Test that creating order with invalid combo items fails."""
    # Create and authenticate user
    user_data = {
        "id": 444555666,
        "first_name": "Invalid",
        "last_name": "Order",
        "username": "invalidorder",
    }

    init_data = generate_telegram_init_data(
        user_data, "test_bot_token_123456:ABCdefGHIjklMNOpqrsTUVwxyz"
    )

    auth_response = await client.post(
        "/api/v1/auth/telegram",
        json={"init_data": init_data, "office": "Test Office"},
    )

    assert auth_response.status_code == 200
    auth_token = auth_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # Order for valid date
    order_date = date.today() + timedelta(days=2)

    # Invalid combo: missing "salad" category (Combo A requires soup, main, salad)
    order_payload = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": test_combo.id,
        "combo_items": [
            {"category": "soup", "menu_item_id": test_menu_items[0].id},
            {"category": "main", "menu_item_id": test_menu_items[1].id},
            # Missing salad
        ],
        "extras": [],
    }

    order_response = await client.post(
        "/api/v1/orders",
        headers=auth_headers,
        json=order_payload,
    )

    # Should fail with 400 or 422 (validation error)
    assert order_response.status_code in [400, 422]
