"""Integration tests for backward compatibility of orders API."""

from datetime import date, timedelta

import pytest


@pytest.mark.asyncio
async def test_create_order_with_legacy_combo_items_field(
    client, auth_headers, test_cafe, test_combo, test_menu_items, test_deadline
):
    """Test that old combo_items field is still accepted and migrated to items."""
    order_date = date.today() + timedelta(days=2)

    # Using old field name 'combo_items' instead of 'items'
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
        "notes": "Legacy field test"
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert data["combo_id"] == test_combo.id
    assert data["notes"] == "Legacy field test"
    assert float(data["total_price"]) == 17.50
    # Verify items field is populated (migrated from combo_items)
    assert "items" in data
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_update_order_with_legacy_combo_items_field(
    client, auth_headers, test_order, test_menu_items, test_deadline
):
    """Test that old combo_items field works for order updates."""
    update_data = {
        "combo_items": [
            {"category": "soup", "menu_item_id": test_menu_items[0].id},
            {"category": "main", "menu_item_id": test_menu_items[1].id},
            {"category": "salad", "menu_item_id": test_menu_items[2].id},
        ],
        "notes": "Updated with legacy field"
    }

    response = await client.patch(
        f"/api/v1/orders/{test_order.id}",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Updated with legacy field"
    assert "items" in data
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_get_order_response_includes_items_field(
    client, auth_headers, test_order
):
    """Test that order response includes 'items' field (not just combo_items)."""
    response = await client.get(f"/api/v1/orders/{test_order.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    # Old orders should have items populated from combo_items
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_existing_order_with_combo_id_still_works(
    client, auth_headers, test_order
):
    """Test that existing orders with combo_id continue to work."""
    response = await client.get(f"/api/v1/orders/{test_order.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_order.id
    assert data["combo_id"] == test_order.combo_id
    assert data["combo_id"] is not None  # Old order has combo_id


@pytest.mark.asyncio
async def test_order_model_combo_items_property(test_order):
    """Test that Order model has combo_items property for backward compatibility."""
    # Access deprecated property
    combo_items = test_order.combo_items

    # Should return the same as items
    assert combo_items == test_order.items
    assert isinstance(combo_items, list)
    assert len(combo_items) > 0
