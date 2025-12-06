"""Unit tests for Order Statistics Service."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.models.cafe import Cafe
from src.models.order import Order
from src.models.user import User
from src.models.cafe import MenuItem
from src.services.order_stats import OrderStatsService


@pytest.fixture
async def stats_service(db_session):
    """Create OrderStatsService instance."""
    return OrderStatsService(db_session)


@pytest.fixture
async def test_user_with_orders(db_session, test_user, test_cafe, test_menu_items, test_combo):
    """Create a user with multiple orders for stats testing."""
    # Create orders over the past 30 days
    today = datetime.now()
    orders = []

    for i in range(10):
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=(today - timedelta(days=i)).date(),
            status="confirmed",
            combo_id=test_combo.id,
            combo_items=[
                {"category": "soup", "menu_item_id": test_menu_items[0].id},
                {"category": "main", "menu_item_id": test_menu_items[1].id},
                {"category": "salad", "menu_item_id": test_menu_items[2].id},
            ],
            extras=[{"menu_item_id": test_menu_items[3].id, "quantity": 1}],
            total_price=Decimal("20.00"),
        )
        db_session.add(order)
        orders.append(order)

    await db_session.commit()
    return test_user, orders


async def test_get_user_stats_returns_correct_format(
    stats_service, test_user_with_orders
):
    """Test that get_user_stats returns the correct format."""
    user, orders = test_user_with_orders

    stats = await stats_service.get_user_stats(user.tgid, days=30)

    assert "orders_count" in stats
    assert "categories" in stats
    assert "unique_dishes" in stats
    assert "total_dishes_available" in stats
    assert "favorite_dishes" in stats
    assert "last_order_date" in stats

    assert stats["orders_count"] == 10
    assert isinstance(stats["categories"], dict)
    assert isinstance(stats["unique_dishes"], int)


async def test_get_user_stats_counts_orders_correctly(
    stats_service, test_user_with_orders
):
    """Test that orders are counted correctly."""
    user, orders = test_user_with_orders

    stats = await stats_service.get_user_stats(user.tgid, days=30)

    assert stats["orders_count"] == 10


async def test_get_user_stats_categories_distribution(
    stats_service, test_user_with_orders
):
    """Test category distribution calculation."""
    user, orders = test_user_with_orders

    stats = await stats_service.get_user_stats(user.tgid, days=30)

    categories = stats["categories"]

    # Each order has soup, main, salad (3 categories)
    # 10 orders = 10 of each category
    assert "soup" in categories
    assert "main" in categories
    assert "salad" in categories

    assert categories["soup"]["count"] == 10
    assert categories["main"]["count"] == 10
    assert categories["salad"]["count"] == 10

    # Each should be 33.3% (1/3 of total)
    assert abs(categories["soup"]["percent"] - 33.3) < 0.1
    assert abs(categories["main"]["percent"] - 33.3) < 0.1
    assert abs(categories["salad"]["percent"] - 33.3) < 0.1


async def test_get_user_stats_unique_dishes(
    stats_service, test_user_with_orders, test_menu_items
):
    """Test unique dishes counting."""
    user, orders = test_user_with_orders

    stats = await stats_service.get_user_stats(user.tgid, days=30)

    # User ordered 4 different items (3 combo + 1 extra)
    assert stats["unique_dishes"] == 4


async def test_get_active_users_filters_by_min_orders(
    stats_service, db_session, test_cafe, test_combo
):
    """Test that get_active_users filters by minimum orders."""
    # Create users with different order counts
    today = datetime.now()

    # User 1: 6 orders (should be included with min_orders=5)
    user1 = User(
        tgid=111111,
        name="User 1",
        office="Office A",
        role="user",
        is_active=True,
        weekly_limit=Decimal("1000.00"),
    )
    db_session.add(user1)

    for i in range(6):
        order = Order(
            user_tgid=user1.tgid,
            cafe_id=test_cafe.id,
            order_date=(today - timedelta(days=i)).date(),
            status="confirmed",
            combo_id=test_combo.id,
            combo_items=[],
            extras=[],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)

    # User 2: 3 orders (should be excluded with min_orders=5)
    user2 = User(
        tgid=222222,
        name="User 2",
        office="Office A",
        role="user",
        is_active=True,
        weekly_limit=Decimal("1000.00"),
    )
    db_session.add(user2)

    for i in range(3):
        order = Order(
            user_tgid=user2.tgid,
            cafe_id=test_cafe.id,
            order_date=(today - timedelta(days=i)).date(),
            status="confirmed",
            combo_id=test_combo.id,
            combo_items=[],
            extras=[],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)

    await db_session.commit()

    # Get active users with min_orders=5
    active_users = await stats_service.get_active_users(min_orders=5, days=30)

    assert user1.tgid in active_users
    assert user2.tgid not in active_users


async def test_get_user_stats_favorite_dishes(
    db_session, stats_service, test_user, test_cafe, test_menu_items, test_combo
):
    """Test favorite dishes calculation."""
    today = datetime.now()

    # Create orders with repeated dishes
    # Item 0: ordered 5 times
    # Item 1: ordered 3 times
    # Item 2: ordered 2 times
    for i in range(5):
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=(today - timedelta(days=i)).date(),
            status="confirmed",
            combo_id=test_combo.id,
            combo_items=[{"category": "soup", "menu_item_id": test_menu_items[0].id}],
            extras=[],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)

    for i in range(3):
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=(today - timedelta(days=i + 5)).date(),
            status="confirmed",
            combo_id=test_combo.id,
            combo_items=[{"category": "main", "menu_item_id": test_menu_items[1].id}],
            extras=[],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)

    for i in range(2):
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=(today - timedelta(days=i + 8)).date(),
            status="confirmed",
            combo_id=test_combo.id,
            combo_items=[{"category": "salad", "menu_item_id": test_menu_items[2].id}],
            extras=[],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)

    await db_session.commit()

    stats = await stats_service.get_user_stats(test_user.tgid, days=30)

    favorite_dishes = stats["favorite_dishes"]

    # Should be sorted by count descending
    assert len(favorite_dishes) == 3
    assert favorite_dishes[0]["name"] == "Tomato Soup"
    assert favorite_dishes[0]["count"] == 5
    assert favorite_dishes[1]["name"] == "Grilled Chicken"
    assert favorite_dishes[1]["count"] == 3
    assert favorite_dishes[2]["name"] == "Caesar Salad"
    assert favorite_dishes[2]["count"] == 2
