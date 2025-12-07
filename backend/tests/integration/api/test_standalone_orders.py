"""Integration tests for standalone orders (without combo)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest


@pytest.mark.asyncio
async def test_create_standalone_order_with_price(
    client, auth_headers, test_cafe, test_menu_items, test_deadline, db_session
):
    """Test creating a standalone order (combo_id=null) with priced items."""
    from src.models.cafe import MenuItem

    # Create menu items with prices for standalone orders
    standalone_item1 = MenuItem(
        cafe_id=test_cafe.id,
        name="Борщ большой",
        category="soup",
        price=Decimal("5.00"),
        is_available=True
    )
    standalone_item2 = MenuItem(
        cafe_id=test_cafe.id,
        name="Котлета с пюре",
        category="main",
        price=Decimal("8.00"),
        is_available=True
    )
    db_session.add_all([standalone_item1, standalone_item2])
    await db_session.commit()
    await db_session.refresh(standalone_item1)
    await db_session.refresh(standalone_item2)

    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": None,
        "items": [
            {
                "type": "standalone",
                "menu_item_id": standalone_item1.id,
                "quantity": 1,
                "options": {}
            },
            {
                "type": "standalone",
                "menu_item_id": standalone_item2.id,
                "quantity": 2,
                "options": {}
            }
        ],
        "extras": [],
        "notes": "Standalone order test"
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert data["combo_id"] is None
    # 5.00 + 8.00*2 = 21.00
    assert float(data["total_price"]) == 21.00
    assert len(data["items"]) == 2
    assert data["notes"] == "Standalone order test"


@pytest.mark.asyncio
async def test_create_standalone_order_without_price_fails(
    client, auth_headers, test_cafe, test_menu_items, test_deadline
):
    """Test that standalone order fails if menu item has no price."""
    # test_menu_items[0] (soup) has no price by default
    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": None,
        "items": [
            {
                "type": "standalone",
                "menu_item_id": test_menu_items[0].id,
                "quantity": 1,
                "options": {}
            }
        ],
        "extras": [],
        "notes": None
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 400
    assert "price" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_standalone_order_unavailable_item_fails(
    client, auth_headers, test_cafe, test_deadline, db_session
):
    """Test that standalone order fails if menu item is unavailable."""
    from src.models.cafe import MenuItem

    unavailable_item = MenuItem(
        cafe_id=test_cafe.id,
        name="Недоступное блюдо",
        category="main",
        price=Decimal("10.00"),
        is_available=False
    )
    db_session.add(unavailable_item)
    await db_session.commit()
    await db_session.refresh(unavailable_item)

    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": None,
        "items": [
            {
                "type": "standalone",
                "menu_item_id": unavailable_item.id,
                "quantity": 1,
                "options": {}
            }
        ],
        "extras": []
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 400
    assert "available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_standalone_order_with_required_option_missing_fails(
    client, auth_headers, test_cafe, test_deadline, db_session
):
    """Test that standalone order fails if required option is not provided."""
    from src.models.cafe import MenuItem, MenuItemOption

    menu_item = MenuItem(
        cafe_id=test_cafe.id,
        name="Пицца",
        category="main",
        price=Decimal("12.00"),
        is_available=True
    )
    db_session.add(menu_item)
    await db_session.commit()
    await db_session.refresh(menu_item)

    option = MenuItemOption(
        menu_item_id=menu_item.id,
        name="Размер",
        values=["Стандарт", "Большая"],
        is_required=True
    )
    db_session.add(option)
    await db_session.commit()

    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": None,
        "items": [
            {
                "type": "standalone",
                "menu_item_id": menu_item.id,
                "quantity": 1,
                "options": {}  # Missing required option
            }
        ],
        "extras": []
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_standalone_order_with_invalid_option_value_fails(
    client, auth_headers, test_cafe, test_deadline, db_session
):
    """Test that standalone order fails if option value is invalid."""
    from src.models.cafe import MenuItem, MenuItemOption

    menu_item = MenuItem(
        cafe_id=test_cafe.id,
        name="Пицца с сыром",  # Unique name to avoid conflict with other tests
        category="main",
        price=Decimal("12.00"),
        is_available=True
    )
    db_session.add(menu_item)
    await db_session.commit()
    await db_session.refresh(menu_item)

    # Create one required option and one non-required option
    option_required = MenuItemOption(
        menu_item_id=menu_item.id,
        name="Размер порции",
        values=["Стандарт", "Большая"],
        is_required=True
    )
    option_optional = MenuItemOption(
        menu_item_id=menu_item.id,
        name="Дополнительный сыр",
        values=["Да", "Нет"],
        is_required=False
    )
    db_session.add_all([option_required, option_optional])
    await db_session.commit()

    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": None,
        "items": [
            {
                "type": "standalone",
                "menu_item_id": menu_item.id,
                "quantity": 1,
                "options": {
                    "Размер порции": "Стандарт",  # Valid required option
                    "Дополнительный сыр": "Много"  # Invalid value for optional
                }
            }
        ],
        "extras": []
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower() or "value" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_standalone_order_with_empty_required_option_fails(
    client, auth_headers, test_cafe, test_deadline, db_session
):
    """Test that standalone order fails if required option has empty value."""
    from src.models.cafe import MenuItem, MenuItemOption

    menu_item = MenuItem(
        cafe_id=test_cafe.id,
        name="Салат",
        category="salad",
        price=Decimal("6.00"),
        is_available=True
    )
    db_session.add(menu_item)
    await db_session.commit()
    await db_session.refresh(menu_item)

    option = MenuItemOption(
        menu_item_id=menu_item.id,
        name="Заправка",
        values=["Масло", "Майонез", "Без заправки"],
        is_required=True
    )
    db_session.add(option)
    await db_session.commit()

    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": None,
        "items": [
            {
                "type": "standalone",
                "menu_item_id": menu_item.id,
                "quantity": 1,
                "options": {"Заправка": ""}  # Empty value for required option
            }
        ],
        "extras": []
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_standalone_order_with_valid_options(
    client, auth_headers, test_cafe, test_deadline, db_session
):
    """Test creating standalone order with valid options."""
    from src.models.cafe import MenuItem, MenuItemOption

    menu_item = MenuItem(
        cafe_id=test_cafe.id,
        name="Бургер",
        category="main",
        price=Decimal("10.00"),
        is_available=True
    )
    db_session.add(menu_item)
    await db_session.commit()
    await db_session.refresh(menu_item)

    option1 = MenuItemOption(
        menu_item_id=menu_item.id,
        name="Размер",
        values=["Стандарт", "Большая"],
        is_required=True
    )
    option2 = MenuItemOption(
        menu_item_id=menu_item.id,
        name="Острота",
        values=["Без остроты", "Слабая", "Средняя", "Острая"],
        is_required=False
    )
    db_session.add_all([option1, option2])
    await db_session.commit()

    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": None,
        "items": [
            {
                "type": "standalone",
                "menu_item_id": menu_item.id,
                "quantity": 2,
                "options": {
                    "Размер": "Большая",
                    "Острота": "Средняя"
                }
            }
        ],
        "extras": []
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert float(data["total_price"]) == 20.00  # 10.00 * 2
    assert data["items"][0]["options"]["Размер"] == "Большая"
    assert data["items"][0]["options"]["Острота"] == "Средняя"


@pytest.mark.asyncio
async def test_create_combo_order_with_combo_items_fails(
    client, auth_headers, test_cafe, test_combo, test_menu_items, test_deadline
):
    """Test that combo_id=null with type='combo' items fails."""
    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": None,  # No combo
        "items": [
            {
                "type": "combo",  # But trying to use combo type
                "category": "soup",
                "menu_item_id": test_menu_items[0].id
            }
        ],
        "extras": []
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 400
    assert "combo" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_combo_order_without_combo_items_fails(
    client, auth_headers, test_cafe, test_combo, test_deadline, db_session
):
    """Test that combo_id specified but no combo items fails."""
    from src.models.cafe import MenuItem

    # Create standalone item with price
    standalone_item = MenuItem(
        cafe_id=test_cafe.id,
        name="Standalone",
        category="main",
        price=Decimal("10.00"),
        is_available=True
    )
    db_session.add(standalone_item)
    await db_session.commit()
    await db_session.refresh(standalone_item)

    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": test_combo.id,  # Combo specified
        "items": [
            {
                "type": "standalone",  # But only standalone items
                "menu_item_id": standalone_item.id,
                "quantity": 1,
                "options": {}
            }
        ],
        "extras": []
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    # This should fail if validation requires combo items when combo_id is set
    # If the implementation allows mixing, adjust the assertion
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_mixed_order_combo_and_standalone(
    client, auth_headers, test_cafe, test_combo, test_menu_items, test_deadline, db_session
):
    """Test creating order with both combo and standalone items."""
    from src.models.cafe import MenuItem

    # Create standalone item with price
    standalone_item = MenuItem(
        cafe_id=test_cafe.id,
        name="Дополнительный гарнир",
        category="main",
        price=Decimal("5.00"),
        is_available=True
    )
    db_session.add(standalone_item)
    await db_session.commit()
    await db_session.refresh(standalone_item)

    order_date = date.today() + timedelta(days=2)

    order_data = {
        "cafe_id": test_cafe.id,
        "order_date": str(order_date),
        "combo_id": test_combo.id,
        "items": [
            # Combo items
            {"type": "combo", "category": "soup", "menu_item_id": test_menu_items[0].id},
            {"type": "combo", "category": "main", "menu_item_id": test_menu_items[1].id},
            {"type": "combo", "category": "salad", "menu_item_id": test_menu_items[2].id},
            # Standalone item
            {
                "type": "standalone",
                "menu_item_id": standalone_item.id,
                "quantity": 1,
                "options": {}
            }
        ],
        "extras": [{"menu_item_id": test_menu_items[3].id, "quantity": 1}]
    }

    response = await client.post("/api/v1/orders", headers=auth_headers, json=order_data)

    assert response.status_code == 201
    data = response.json()
    # total = combo(15.00) + standalone(5.00) + extra(2.50) = 22.50
    assert float(data["total_price"]) == 22.50
    assert len(data["items"]) == 4
    assert data["combo_id"] == test_combo.id
