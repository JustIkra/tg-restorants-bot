"""Integration tests for Orders API."""

from datetime import date, timedelta

import pytest


@pytest.mark.asyncio
async def test_get_orders_list(client, auth_headers, test_order):
    """Test getting list of orders."""
    response = await client.get("/api/v1/orders", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == test_order.id


@pytest.mark.asyncio
async def test_get_order_by_id(client, auth_headers, test_order):
    """Test getting a specific order."""
    response = await client.get(f"/api/v1/orders/{test_order.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_order.id
    assert data["user_tgid"] == test_order.user_tgid
    assert float(data["total_price"]) == float(test_order.total_price)


@pytest.mark.asyncio
async def test_create_order(
    client,
    auth_headers,
    test_cafe,
    test_combo,
    test_menu_items,
    test_deadline,
):
    """Test creating a new order."""
    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": test_combo.id,
        "combo_items": [
            {"category": "soup", "menu_item_id": test_menu_items[0].id},
            {"category": "main", "menu_item_id": test_menu_items[1].id},
            {"category": "salad", "menu_item_id": test_menu_items[2].id},
        ],
        "extras": [{"menu_item_id": test_menu_items[3].id, "quantity": 1}],
        "notes": "API test order",
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert data["cafe_id"] == test_cafe.id
    assert data["combo_id"] == test_combo.id
    assert data["notes"] == "API test order"
    assert float(data["total_price"]) == 17.50


@pytest.mark.asyncio
async def test_update_order(client, auth_headers, test_order, test_deadline):
    """Test updating an order."""
    update_data = {"notes": "Updated via API"}

    response = await client.patch(
        f"/api/v1/orders/{test_order.id}", headers=auth_headers, json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Updated via API"


@pytest.mark.asyncio
async def test_delete_order(client, auth_headers, test_order, test_deadline):
    """Test deleting an order."""
    response = await client.delete(
        f"/api/v1/orders/{test_order.id}", headers=auth_headers
    )

    assert response.status_code == 204

    # Verify order is deleted
    response = await client.get(f"/api/v1/orders/{test_order.id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_order_unauthorized(client, test_order):
    """Test getting order without auth fails."""
    response = await client.get(f"/api/v1/orders/{test_order.id}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_check_availability(client, auth_headers, test_cafe, test_deadline):
    """Test checking order availability."""
    order_date = date.today() + timedelta(days=2)

    response = await client.get(
        f"/api/v1/orders/availability/{order_date}?cafe_id={test_cafe.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "can_order" in data
    assert "date" in data


@pytest.mark.asyncio
async def test_get_week_availability(client, auth_headers, test_cafe, test_deadline):
    """Test getting week availability."""
    response = await client.get(
        f"/api/v1/orders/availability/week?cafe_id={test_cafe.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "cafe_id" in data
    assert "availability" in data
    assert len(data["availability"]) == 7
