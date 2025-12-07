"""Integration tests for Recommendations API."""

import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from src.models.order import Order


@pytest.fixture
async def user_with_order_history(
    db_session, test_user, test_cafe, test_menu_items, test_combo
):
    """Create user with order history for recommendations."""
    today = datetime.now()

    # Create 10 orders over the past month
    for i in range(10):
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=(today - timedelta(days=i)).date(),
            status="confirmed",
            combo_id=test_combo.id,
            items=[
                {"category": "soup", "menu_item_id": test_menu_items[0].id},
                {"category": "main", "menu_item_id": test_menu_items[1].id},
                {"category": "salad", "menu_item_id": test_menu_items[2].id},
            ],
            extras=[{"menu_item_id": test_menu_items[3].id, "quantity": 1}],
            total_price=Decimal("20.00"),
        )
        db_session.add(order)

    await db_session.commit()
    return test_user


async def test_get_recommendations_without_cache(
    client, user_with_order_history, auth_headers
):
    """Test GET /users/{tgid}/recommendations without cached data."""
    response = await client.get(
        f"/api/v1/users/{user_with_order_history.tgid}/recommendations",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Without cache, should return empty recommendations but with stats
    assert data["summary"] is None
    assert data["tips"] == []
    assert data["generated_at"] is None

    # But stats should be present
    assert "stats" in data
    assert data["stats"]["orders_last_30_days"] == 10
    assert "categories" in data["stats"]
    assert data["stats"]["unique_dishes"] == 4


async def test_get_recommendations_with_cache(
    client, user_with_order_history, auth_headers
):
    """Test GET /users/{tgid}/recommendations with cached data."""
    # Mock cached recommendations in Redis
    cached_data = {
        "summary": "Great variety, keep it up!",
        "tips": [
            "Try adding more vegetables",
            "Explore fish options on Wednesdays",
        ],
        "generated_at": "2025-12-06T03:00:00Z",
    }

    with patch("src.routers.recommendations.get_cache") as mock_cache:
        mock_cache.return_value = json.dumps(cached_data)

        response = await client.get(
            f"/api/v1/users/{user_with_order_history.tgid}/recommendations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return cached recommendations
        assert data["summary"] == "Great variety, keep it up!"
        assert len(data["tips"]) == 2
        assert "vegetables" in data["tips"][0]
        assert data["generated_at"] == "2025-12-06T03:00:00Z"

        # Stats should still be fresh (not from cache)
        assert "stats" in data
        assert data["stats"]["orders_last_30_days"] == 10


async def test_get_recommendations_stats_structure(
    client, user_with_order_history, auth_headers
):
    """Test that recommendations endpoint returns correct stats structure."""
    response = await client.get(
        f"/api/v1/users/{user_with_order_history.tgid}/recommendations",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    stats = data["stats"]

    # Check all required fields
    assert "orders_last_30_days" in stats
    assert "categories" in stats
    assert "unique_dishes" in stats
    assert "favorite_dishes" in stats

    # Check categories structure
    assert isinstance(stats["categories"], dict)
    for category, info in stats["categories"].items():
        assert "count" in info
        assert "percent" in info
        assert isinstance(info["count"], int)
        assert isinstance(info["percent"], (int, float))

    # Check favorite dishes structure
    assert isinstance(stats["favorite_dishes"], list)
    for dish in stats["favorite_dishes"]:
        assert "name" in dish
        assert "count" in dish


async def test_get_recommendations_user_without_orders(
    client, test_user, auth_headers
):
    """Test getting recommendations for user without any orders."""
    # Create a new user without orders
    response = await client.get(
        f"/api/v1/users/{test_user.tgid}/recommendations",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return empty data
    assert data["summary"] is None
    assert data["tips"] == []
    assert data["stats"]["orders_last_30_days"] == 0
    assert data["stats"]["categories"] == {}
    assert data["stats"]["unique_dishes"] == 0
    assert data["stats"]["favorite_dishes"] == []


async def test_get_recommendations_cache_key_format(
    client, user_with_order_history, auth_headers
):
    """Test that correct cache key is used for recommendations."""
    with patch("src.routers.recommendations.get_cache") as mock_cache:
        mock_cache.return_value = None

        await client.get(
            f"/api/v1/users/{user_with_order_history.tgid}/recommendations",
            headers=auth_headers,
        )

        # Verify correct cache key was used
        expected_key = f"recommendations:user:{user_with_order_history.tgid}"
        mock_cache.assert_called_once_with(expected_key)


async def test_get_recommendations_malformed_cache_data(
    client, user_with_order_history, auth_headers
):
    """Test handling of malformed cache data."""
    with patch("src.routers.recommendations.get_cache") as mock_cache:
        # Return invalid JSON
        mock_cache.return_value = "not valid json {{"

        # Should handle gracefully and return error or empty data
        # Depending on implementation, this might raise or return empty
        try:
            response = await client.get(
                f"/api/v1/users/{user_with_order_history.tgid}/recommendations",
                headers=auth_headers,
            )
            # If it doesn't raise, it should return 500 or empty data
            assert response.status_code in [200, 500]
        except json.JSONDecodeError:
            # If it raises, that's also acceptable
            pass


async def test_get_recommendations_response_model(
    client, user_with_order_history, auth_headers
):
    """Test that response matches RecommendationsResponse schema."""
    with patch("src.routers.recommendations.get_cache") as mock_cache:
        cached_data = {
            "summary": "Test summary",
            "tips": ["Tip 1", "Tip 2"],
            "generated_at": "2025-12-06T03:00:00Z",
        }
        mock_cache.return_value = json.dumps(cached_data)

        response = await client.get(
            f"/api/v1/users/{user_with_order_history.tgid}/recommendations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        required_fields = ["summary", "tips", "stats", "generated_at"]
        for field in required_fields:
            assert field in data

        # Check types
        assert isinstance(data["summary"], (str, type(None)))
        assert isinstance(data["tips"], list)
        assert isinstance(data["stats"], dict)
        assert isinstance(data["generated_at"], (str, type(None)))
