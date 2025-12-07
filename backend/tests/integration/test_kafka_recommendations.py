"""Integration tests for Kafka recommendations worker."""

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.gemini import AllKeysExhaustedException
from src.models.order import Order


class TestKafkaRecommendationsWorker:
    """Test suite for recommendations worker."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for caching."""
        with patch("workers.recommendations.set_cache") as mock_set_cache:
            mock_set_cache.return_value = AsyncMock()
            yield mock_set_cache

    @pytest.fixture
    def mock_recommendation_service(self):
        """Mock GeminiRecommendationService."""
        with patch(
            "workers.recommendations.get_recommendation_service"
        ) as mock_service:
            service_instance = AsyncMock()
            service_instance.generate_recommendations = AsyncMock(
                return_value={
                    "summary": "Вы предпочитаете супы и салаты. Рекомендуем попробовать новые комбинации.",
                    "tips": [
                        "Попробуйте борщ с чесночными гренками",
                        "Салат Цезарь отлично сочетается с курицей гриль",
                    ],
                }
            )
            mock_service.return_value = service_instance
            yield service_instance

    @pytest.fixture
    def mock_key_pool(self):
        """Mock Gemini API key pool."""
        with patch("workers.recommendations.get_key_pool") as mock_pool:
            pool_instance = MagicMock()
            mock_pool.return_value = pool_instance
            yield pool_instance

    @pytest.mark.asyncio
    async def test_generate_recommendations_for_active_user(
        self,
        db_session,
        test_user,
        test_cafe,
        test_combo,
        test_menu_items,
        mock_redis_client,
        mock_recommendation_service,
        mock_key_pool,
    ):
        """Test generating recommendations for an active user."""
        # Arrange: Create 5+ orders for the user (to be considered active)
        from datetime import date, timedelta

        for i in range(6):
            order_date = date.today() - timedelta(days=i)
            order = Order(
                user_tgid=test_user.tgid,
                cafe_id=test_cafe.id,
                order_date=order_date,
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "soup", "menu_item_id": test_menu_items[0].id},
                    {"category": "main", "menu_item_id": test_menu_items[1].id},
                ],
                total_price=Decimal("15.00"),
            )
            db_session.add(order)
        await db_session.commit()

        # Act: Run batch generation
        from workers.recommendations import generate_recommendations_batch

        await generate_recommendations_batch()

        # Assert: Verify recommendations were generated and cached
        assert mock_recommendation_service.generate_recommendations.called
        assert mock_redis_client.called

        # Verify cache key format
        call_args = mock_redis_client.call_args
        cache_key = call_args[0][0]
        assert cache_key == f"recommendations:user:{test_user.tgid}"

        # Verify cached data structure
        cached_data = json.loads(call_args[0][1])
        assert "summary" in cached_data
        assert "tips" in cached_data
        assert "generated_at" in cached_data

        # Verify TTL is 24 hours (86400 seconds)
        assert call_args[1]["ttl"] == 86400

    @pytest.mark.asyncio
    async def test_recommendations_cached_with_correct_ttl(
        self,
        db_session,
        test_user,
        test_cafe,
        test_combo,
        test_menu_items,
        mock_redis_client,
        mock_recommendation_service,
        mock_key_pool,
    ):
        """Test that recommendations are stored in Redis with 24h TTL."""
        # Arrange: Create active user with orders
        from datetime import date, timedelta

        for i in range(5):
            order = Order(
                user_tgid=test_user.tgid,
                cafe_id=test_cafe.id,
                order_date=date.today() - timedelta(days=i),
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "soup", "menu_item_id": test_menu_items[0].id},
                ],
                total_price=Decimal("10.00"),
            )
            db_session.add(order)
        await db_session.commit()

        # Act
        from workers.recommendations import generate_recommendations_batch

        await generate_recommendations_batch()

        # Assert: Verify TTL is set to 24 hours
        call_args = mock_redis_client.call_args
        assert call_args[1]["ttl"] == 86400  # 24 hours in seconds

    @pytest.mark.asyncio
    async def test_handles_gemini_api_error(
        self,
        db_session,
        test_user,
        test_cafe,
        test_combo,
        test_menu_items,
        mock_redis_client,
        mock_key_pool,
    ):
        """Test graceful handling of Gemini API errors."""
        # Arrange: Create active user
        from datetime import date, timedelta

        for i in range(5):
            order = Order(
                user_tgid=test_user.tgid,
                cafe_id=test_cafe.id,
                order_date=date.today() - timedelta(days=i),
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "soup", "menu_item_id": test_menu_items[0].id},
                ],
                total_price=Decimal("10.00"),
            )
            db_session.add(order)
        await db_session.commit()

        # Mock service to raise error
        with patch(
            "workers.recommendations.get_recommendation_service"
        ) as mock_service:
            service_instance = AsyncMock()
            service_instance.generate_recommendations = AsyncMock(
                side_effect=Exception("Gemini API error")
            )
            mock_service.return_value = service_instance

            # Act: Should not raise exception
            from workers.recommendations import (
                generate_recommendations_batch,
            )

            await generate_recommendations_batch()

            # Assert: Redis should not be called (no cache on error)
            assert not mock_redis_client.called

    @pytest.mark.asyncio
    async def test_handles_all_keys_exhausted(
        self,
        db_session,
        test_user,
        test_manager,
        test_cafe,
        test_combo,
        test_menu_items,
        mock_redis_client,
        mock_key_pool,
    ):
        """Test that batch stops when all Gemini API keys are exhausted."""
        # Arrange: Create two active users
        from datetime import date, timedelta

        # User 1: orders
        for i in range(5):
            order = Order(
                user_tgid=test_user.tgid,
                cafe_id=test_cafe.id,
                order_date=date.today() - timedelta(days=i),
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "soup", "menu_item_id": test_menu_items[0].id},
                ],
                total_price=Decimal("10.00"),
            )
            db_session.add(order)

        # User 2: orders
        for i in range(5):
            order = Order(
                user_tgid=test_manager.tgid,
                cafe_id=test_cafe.id,
                order_date=date.today() - timedelta(days=i),
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "main", "menu_item_id": test_menu_items[1].id},
                ],
                total_price=Decimal("12.00"),
            )
            db_session.add(order)

        await db_session.commit()

        # Mock service: first user succeeds, second raises AllKeysExhaustedException
        with patch(
            "workers.recommendations.get_recommendation_service"
        ) as mock_service:
            service_instance = AsyncMock()

            # First call succeeds, second raises exhausted exception
            service_instance.generate_recommendations = AsyncMock(
                side_effect=[
                    {
                        "summary": "First user recommendations",
                        "tips": ["Tip 1"],
                    },
                    AllKeysExhaustedException("All API keys exhausted"),
                ]
            )
            mock_service.return_value = service_instance

            # Act
            from workers.recommendations import (
                generate_recommendations_batch,
            )

            await generate_recommendations_batch()

            # Assert: Should have processed first user only
            assert service_instance.generate_recommendations.call_count == 2
            # Redis should be called only once (for first user)
            assert mock_redis_client.call_count == 1

    @pytest.mark.asyncio
    async def test_no_active_users_skips_generation(
        self,
        db_session,
        mock_redis_client,
        mock_recommendation_service,
    ):
        """Test that batch is skipped when no active users exist."""
        # Arrange: No orders in database

        # Act
        from workers.recommendations import generate_recommendations_batch

        await generate_recommendations_batch()

        # Assert: No recommendations generated
        assert not mock_recommendation_service.generate_recommendations.called
        assert not mock_redis_client.called

    @pytest.mark.asyncio
    async def test_only_users_with_min_orders_get_recommendations(
        self,
        db_session,
        test_user,
        test_manager,
        test_cafe,
        test_combo,
        test_menu_items,
        mock_redis_client,
        mock_recommendation_service,
        mock_key_pool,
    ):
        """Test that only users with >= 5 orders get recommendations."""
        # Arrange: User with 5 orders, manager with only 2
        from datetime import date, timedelta

        # test_user: 5 orders (active)
        for i in range(5):
            order = Order(
                user_tgid=test_user.tgid,
                cafe_id=test_cafe.id,
                order_date=date.today() - timedelta(days=i),
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "soup", "menu_item_id": test_menu_items[0].id},
                ],
                total_price=Decimal("10.00"),
            )
            db_session.add(order)

        # test_manager: only 2 orders (not active)
        for i in range(2):
            order = Order(
                user_tgid=test_manager.tgid,
                cafe_id=test_cafe.id,
                order_date=date.today() - timedelta(days=i),
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "main", "menu_item_id": test_menu_items[1].id},
                ],
                total_price=Decimal("12.00"),
            )
            db_session.add(order)

        await db_session.commit()

        # Act
        from workers.recommendations import generate_recommendations_batch

        await generate_recommendations_batch()

        # Assert: Only test_user should get recommendations
        assert mock_recommendation_service.generate_recommendations.call_count == 1

        # Verify it was called for test_user
        call_args = mock_recommendation_service.generate_recommendations.call_args[0][0]
        assert call_args["orders_count"] >= 5

    @pytest.mark.asyncio
    async def test_cached_data_structure(
        self,
        db_session,
        test_user,
        test_cafe,
        test_combo,
        test_menu_items,
        mock_redis_client,
        mock_recommendation_service,
        mock_key_pool,
    ):
        """Test that cached data has correct structure."""
        # Arrange: Create active user
        from datetime import date, timedelta

        for i in range(5):
            order = Order(
                user_tgid=test_user.tgid,
                cafe_id=test_cafe.id,
                order_date=date.today() - timedelta(days=i),
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "soup", "menu_item_id": test_menu_items[0].id},
                ],
                total_price=Decimal("10.00"),
            )
            db_session.add(order)
        await db_session.commit()

        # Act
        from workers.recommendations import generate_recommendations_batch

        await generate_recommendations_batch()

        # Assert: Verify cached data structure
        cached_json = mock_redis_client.call_args[0][1]
        cached_data = json.loads(cached_json)

        assert "summary" in cached_data
        assert "tips" in cached_data
        assert "generated_at" in cached_data

        # Verify generated_at is valid ISO timestamp
        generated_at = datetime.fromisoformat(cached_data["generated_at"])
        assert generated_at.tzinfo is not None  # Should have timezone

        # Verify recommendations content
        assert isinstance(cached_data["summary"], str)
        assert isinstance(cached_data["tips"], list)
        assert len(cached_data["tips"]) > 0

    @pytest.mark.asyncio
    async def test_manual_trigger_via_kafka_event(
        self,
        db_session,
        test_user,
        test_cafe,
        test_combo,
        test_menu_items,
        mock_redis_client,
        mock_recommendation_service,
        mock_key_pool,
    ):
        """Test manual triggering of recommendations via Kafka event."""
        # Arrange: Create active user
        from datetime import date, timedelta

        for i in range(5):
            order = Order(
                user_tgid=test_user.tgid,
                cafe_id=test_cafe.id,
                order_date=date.today() - timedelta(days=i),
                status="completed",
                combo_id=test_combo.id,
                items=[
                    {"category": "soup", "menu_item_id": test_menu_items[0].id},
                ],
                total_price=Decimal("10.00"),
            )
            db_session.add(order)
        await db_session.commit()

        # Create Kafka event
        event = {"type": "generate_recommendations", "timestamp": datetime.now(timezone.utc)}

        # Act: Call event handler
        from workers.recommendations import handle_daily_task

        await handle_daily_task(event)

        # Assert: Recommendations should be generated
        assert mock_recommendation_service.generate_recommendations.called
        assert mock_redis_client.called

    @pytest.mark.asyncio
    async def test_ignores_non_recommendation_events(
        self,
        db_session,
        mock_redis_client,
        mock_recommendation_service,
    ):
        """Test that non-recommendation events are ignored."""
        # Arrange: Event with different type
        event = {"type": "some_other_task", "timestamp": datetime.now(timezone.utc)}

        # Act
        from workers.recommendations import handle_daily_task

        await handle_daily_task(event)

        # Assert: No recommendations generated
        assert not mock_recommendation_service.generate_recommendations.called
        assert not mock_redis_client.called

    @pytest.mark.asyncio
    async def test_batch_progress_logging(
        self,
        db_session,
        test_user,
        test_manager,
        test_cafe,
        test_combo,
        test_menu_items,
        mock_redis_client,
        mock_recommendation_service,
        mock_key_pool,
    ):
        """Test that batch generation logs progress correctly."""
        # Arrange: Create two active users
        from datetime import date, timedelta

        for tgid in [test_user.tgid, test_manager.tgid]:
            for i in range(5):
                order = Order(
                    user_tgid=tgid,
                    cafe_id=test_cafe.id,
                    order_date=date.today() - timedelta(days=i),
                    status="completed",
                    combo_id=test_combo.id,
                    items=[
                        {"category": "soup", "menu_item_id": test_menu_items[0].id},
                    ],
                    total_price=Decimal("10.00"),
                )
                db_session.add(order)
        await db_session.commit()

        # Act
        from workers.recommendations import generate_recommendations_batch

        await generate_recommendations_batch()

        # Assert: Both users should get recommendations
        assert mock_recommendation_service.generate_recommendations.call_count == 2
        assert mock_redis_client.call_count == 2
