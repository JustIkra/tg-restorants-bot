"""Integration tests for MenuItemOption CRUD API."""

from decimal import Decimal

import pytest


@pytest.mark.asyncio
async def test_create_menu_item_option_as_manager(
    client, manager_auth_headers, test_cafe, test_menu_items
):
    """Test creating a menu item option as manager."""
    menu_item = test_menu_items[0]

    option_data = {
        "name": "Размер порции",
        "values": ["Стандарт", "Большая", "XL"],
        "is_required": True
    }

    response = await client.post(
        f"/api/v1/cafes/{test_cafe.id}/menu/{menu_item.id}/options",
        headers=manager_auth_headers,
        json=option_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Размер порции"
    assert data["values"] == ["Стандарт", "Большая", "XL"]
    assert data["is_required"] is True
    assert data["menu_item_id"] == menu_item.id


@pytest.mark.asyncio
async def test_create_menu_item_option_as_user_forbidden(
    client, auth_headers, test_cafe, test_menu_items
):
    """Test that regular users cannot create menu item options."""
    menu_item = test_menu_items[0]

    option_data = {
        "name": "Размер порции",
        "values": ["Стандарт", "Большая"],
        "is_required": True
    }

    response = await client.post(
        f"/api/v1/cafes/{test_cafe.id}/menu/{menu_item.id}/options",
        headers=auth_headers,
        json=option_data
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_menu_item_options(
    client, auth_headers, manager_auth_headers, test_cafe, test_menu_items, db_session
):
    """Test listing menu item options (accessible to all users)."""
    from src.models.cafe import MenuItemOption

    menu_item = test_menu_items[0]

    # Create options as manager
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

    # Regular user can list options
    response = await client.get(
        f"/api/v1/cafes/{test_cafe.id}/menu/{menu_item.id}/options",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any(opt["name"] == "Размер" for opt in data)
    assert any(opt["name"] == "Острота" for opt in data)


@pytest.mark.asyncio
async def test_update_menu_item_option(
    client, manager_auth_headers, test_cafe, test_menu_items, db_session
):
    """Test updating a menu item option."""
    from src.models.cafe import MenuItemOption

    menu_item = test_menu_items[0]

    option = MenuItemOption(
        menu_item_id=menu_item.id,
        name="Размер",
        values=["Стандарт", "Большая"],
        is_required=True
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)

    update_data = {
        "values": ["Стандарт", "Большая", "XL", "XXL"],
        "is_required": False
    }

    response = await client.patch(
        f"/api/v1/cafes/{test_cafe.id}/menu/{menu_item.id}/options/{option.id}",
        headers=manager_auth_headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["values"]) == 4
    assert "XXL" in data["values"]
    assert data["is_required"] is False


@pytest.mark.asyncio
async def test_delete_menu_item_option(
    client, manager_auth_headers, test_cafe, test_menu_items, db_session
):
    """Test deleting a menu item option."""
    from src.models.cafe import MenuItemOption

    menu_item = test_menu_items[0]

    option = MenuItemOption(
        menu_item_id=menu_item.id,
        name="Размер",
        values=["Стандарт", "Большая"],
        is_required=False
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)

    response = await client.delete(
        f"/api/v1/cafes/{test_cafe.id}/menu/{menu_item.id}/options/{option.id}",
        headers=manager_auth_headers
    )

    assert response.status_code == 204

    # Verify option is deleted
    from sqlalchemy import select
    result = await db_session.execute(
        select(MenuItemOption).where(MenuItemOption.id == option.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cascade_delete_options_when_menu_item_deleted(
    client, manager_auth_headers, test_cafe, test_menu_items, db_session
):
    """Test that options are cascade deleted when menu item is deleted."""
    from src.models.cafe import MenuItem, MenuItemOption

    # Create a menu item with options
    menu_item = MenuItem(
        cafe_id=test_cafe.id,
        name="Test Item",
        category="main",
        price=Decimal("10.00"),
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
    await db_session.refresh(option)
    option_id = option.id

    # Delete menu item
    response = await client.delete(
        f"/api/v1/cafes/{test_cafe.id}/menu/{menu_item.id}",
        headers=manager_auth_headers
    )

    assert response.status_code == 204

    # Verify option is cascade deleted
    from sqlalchemy import select
    result = await db_session.execute(
        select(MenuItemOption).where(MenuItemOption.id == option_id)
    )
    assert result.scalar_one_or_none() is None
