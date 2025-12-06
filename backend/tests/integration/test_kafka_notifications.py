"""Integration tests for Kafka notifications worker."""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from backend.src.kafka.events import DeadlinePassedEvent
from backend.src.models.cafe import Cafe
from backend.src.models.order import Order


class TestKafkaNotificationsWorker:
    """Test suite for notifications worker."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx.AsyncClient for Telegram API calls."""
        with patch("backend.workers.notifications.httpx.AsyncClient") as mock_client:
            # Create mock context manager
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__.return_value = None

            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)

            yield mock_instance

    @pytest.mark.asyncio
    async def test_handle_deadline_passed_with_orders(
        self,
        db_session,
        test_cafe,
        test_user,
        test_combo,
        test_menu_items,
        mock_httpx_client,
    ):
        """Test processing deadline notification event with orders."""
        # Arrange: Update cafe with Telegram chat ID
        test_cafe.tg_chat_id = 123456789
        test_cafe.notifications_enabled = True
        await db_session.commit()

        # Create order for today
        order_date = date.today()
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=order_date,
            status="pending",
            combo_id=test_combo.id,
            combo_items=[
                {"category": "soup", "menu_item_id": test_menu_items[0].id},
                {"category": "main", "menu_item_id": test_menu_items[1].id},
                {"category": "salad", "menu_item_id": test_menu_items[2].id},
            ],
            extras=[{"menu_item_id": test_menu_items[3].id, "quantity": 1}],
            notes="No onions please",
            total_price=Decimal("17.50"),
        )
        db_session.add(order)
        await db_session.commit()

        # Create event
        event = DeadlinePassedEvent(
            cafe_id=test_cafe.id,
            date=order_date.isoformat(),
        )

        # Act: Import and call handler directly
        from backend.workers.notifications import handle_deadline_passed

        await handle_deadline_passed(event)

        # Assert: Verify Telegram API was called
        assert mock_httpx_client.post.called
        call_args = mock_httpx_client.post.call_args

        # Verify URL contains bot token
        assert "https://api.telegram.org/bot" in call_args[0][0]

        # Verify payload structure
        payload = call_args[1]["json"]
        assert payload["chat_id"] == test_cafe.tg_chat_id
        assert payload["parse_mode"] == "Markdown"
        assert "text" in payload

        # Verify message content
        message = payload["text"]
        assert test_cafe.name in message
        assert test_user.name in message
        assert test_combo.name in message
        assert test_menu_items[0].name in message  # soup
        assert test_menu_items[3].name in message  # extra
        assert "No onions please" in message
        assert "17.50" in message or "17,50" in message

    @pytest.mark.asyncio
    async def test_handle_deadline_passed_no_orders(
        self,
        db_session,
        test_cafe,
        mock_httpx_client,
    ):
        """Test that no notification is sent when there are no orders."""
        # Arrange: Cafe with Telegram enabled but no orders
        test_cafe.tg_chat_id = 123456789
        test_cafe.notifications_enabled = True
        await db_session.commit()

        order_date = date.today()
        event = DeadlinePassedEvent(
            cafe_id=test_cafe.id,
            date=order_date.isoformat(),
        )

        # Act
        from backend.workers.notifications import handle_deadline_passed

        await handle_deadline_passed(event)

        # Assert: No Telegram API call should be made
        assert not mock_httpx_client.post.called

    @pytest.mark.asyncio
    async def test_handle_deadline_passed_no_chat_id(
        self,
        db_session,
        test_cafe,
        test_user,
        test_combo,
        test_menu_items,
        mock_httpx_client,
    ):
        """Test graceful handling when cafe has no tg_chat_id."""
        # Arrange: Cafe without Telegram chat ID
        test_cafe.tg_chat_id = None
        test_cafe.notifications_enabled = True
        await db_session.commit()

        # Create order
        order_date = date.today()
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=order_date,
            status="pending",
            combo_id=test_combo.id,
            combo_items=[
                {"category": "soup", "menu_item_id": test_menu_items[0].id},
            ],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)
        await db_session.commit()

        event = DeadlinePassedEvent(
            cafe_id=test_cafe.id,
            date=order_date.isoformat(),
        )

        # Act
        from backend.workers.notifications import handle_deadline_passed

        await handle_deadline_passed(event)

        # Assert: No notification should be sent
        assert not mock_httpx_client.post.called

    @pytest.mark.asyncio
    async def test_handle_deadline_passed_notifications_disabled(
        self,
        db_session,
        test_cafe,
        test_user,
        test_combo,
        test_menu_items,
        mock_httpx_client,
    ):
        """Test that notifications are skipped when disabled for cafe."""
        # Arrange: Cafe with notifications disabled
        test_cafe.tg_chat_id = 123456789
        test_cafe.notifications_enabled = False
        await db_session.commit()

        # Create order
        order_date = date.today()
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=order_date,
            status="pending",
            combo_id=test_combo.id,
            combo_items=[
                {"category": "soup", "menu_item_id": test_menu_items[0].id},
            ],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)
        await db_session.commit()

        event = DeadlinePassedEvent(
            cafe_id=test_cafe.id,
            date=order_date.isoformat(),
        )

        # Act
        from backend.workers.notifications import handle_deadline_passed

        await handle_deadline_passed(event)

        # Assert: No notification should be sent
        assert not mock_httpx_client.post.called

    @pytest.mark.asyncio
    async def test_handle_deadline_passed_cafe_not_found(
        self,
        db_session,
        mock_httpx_client,
    ):
        """Test graceful handling when cafe does not exist."""
        # Arrange: Non-existent cafe ID
        event = DeadlinePassedEvent(
            cafe_id=99999,
            date=date.today().isoformat(),
        )

        # Act
        from backend.workers.notifications import handle_deadline_passed

        await handle_deadline_passed(event)

        # Assert: No error raised, no notification sent
        assert not mock_httpx_client.post.called

    @pytest.mark.asyncio
    async def test_notification_format_multiple_orders(
        self,
        db_session,
        test_cafe,
        test_user,
        test_manager,
        test_combo,
        test_menu_items,
        mock_httpx_client,
    ):
        """Test notification message format with multiple orders."""
        # Arrange: Cafe with notifications enabled
        test_cafe.tg_chat_id = 123456789
        test_cafe.notifications_enabled = True
        await db_session.commit()

        order_date = date.today()

        # Create two orders from different users
        order1 = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=order_date,
            status="pending",
            combo_id=test_combo.id,
            combo_items=[
                {"category": "soup", "menu_item_id": test_menu_items[0].id},
            ],
            total_price=Decimal("15.00"),
        )
        order2 = Order(
            user_tgid=test_manager.tgid,
            cafe_id=test_cafe.id,
            order_date=order_date,
            status="pending",
            combo_id=test_combo.id,
            combo_items=[
                {"category": "main", "menu_item_id": test_menu_items[1].id},
            ],
            total_price=Decimal("20.00"),
        )
        db_session.add(order1)
        db_session.add(order2)
        await db_session.commit()

        event = DeadlinePassedEvent(
            cafe_id=test_cafe.id,
            date=order_date.isoformat(),
        )

        # Act
        from backend.workers.notifications import handle_deadline_passed

        await handle_deadline_passed(event)

        # Assert: Verify message contains both users and correct total
        payload = mock_httpx_client.post.call_args[1]["json"]
        message = payload["text"]

        assert test_user.name in message
        assert test_manager.name in message
        assert "2 заказов" in message or "2 заказа" in message
        assert "35" in message  # Total price

    @pytest.mark.asyncio
    async def test_telegram_api_retry_on_rate_limit(
        self,
        db_session,
        test_cafe,
        test_user,
        test_combo,
        test_menu_items,
    ):
        """Test retry logic when Telegram API returns 429 (rate limit)."""
        # Arrange: Setup cafe and order
        test_cafe.tg_chat_id = 123456789
        test_cafe.notifications_enabled = True
        await db_session.commit()

        order_date = date.today()
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=order_date,
            status="pending",
            combo_id=test_combo.id,
            combo_items=[
                {"category": "soup", "menu_item_id": test_menu_items[0].id},
            ],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)
        await db_session.commit()

        # Mock 429 response then success
        with patch("backend.workers.notifications.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # First call: 429 error
            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {"Retry-After": "1"}
            rate_limit_response.text = "Rate limit exceeded"

            # Second call: success
            success_response = MagicMock()
            success_response.status_code = 200
            success_response.raise_for_status = MagicMock()

            mock_instance.post = AsyncMock(
                side_effect=[
                    rate_limit_response,  # First call fails
                    success_response,     # Second call succeeds
                ]
            )

            # Mock raise_for_status to raise HTTPStatusError on first call
            import httpx
            rate_limit_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "Rate limit",
                    request=MagicMock(),
                    response=rate_limit_response,
                )
            )

            event = DeadlinePassedEvent(
                cafe_id=test_cafe.id,
                date=order_date.isoformat(),
            )

            # Act
            from backend.workers.notifications import handle_deadline_passed

            await handle_deadline_passed(event)

            # Assert: Should have retried and succeeded
            assert mock_instance.post.call_count == 2

    @pytest.mark.asyncio
    async def test_telegram_api_client_error_no_retry(
        self,
        db_session,
        test_cafe,
        test_user,
        test_combo,
        test_menu_items,
    ):
        """Test that 4xx errors don't trigger retries."""
        # Arrange: Setup cafe and order
        test_cafe.tg_chat_id = 123456789
        test_cafe.notifications_enabled = True
        await db_session.commit()

        order_date = date.today()
        order = Order(
            user_tgid=test_user.tgid,
            cafe_id=test_cafe.id,
            order_date=order_date,
            status="pending",
            combo_id=test_combo.id,
            combo_items=[
                {"category": "soup", "menu_item_id": test_menu_items[0].id},
            ],
            total_price=Decimal("10.00"),
        )
        db_session.add(order)
        await db_session.commit()

        # Mock 403 Forbidden response (e.g., bot blocked by user)
        with patch("backend.workers.notifications.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            error_response = MagicMock()
            error_response.status_code = 403
            error_response.text = "Forbidden: bot was blocked by the user"

            mock_instance.post = AsyncMock(return_value=error_response)

            # Mock raise_for_status to raise HTTPStatusError
            import httpx
            error_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "Forbidden",
                    request=MagicMock(),
                    response=error_response,
                )
            )

            event = DeadlinePassedEvent(
                cafe_id=test_cafe.id,
                date=order_date.isoformat(),
            )

            # Act
            from backend.workers.notifications import handle_deadline_passed

            await handle_deadline_passed(event)

            # Assert: Should NOT retry on 403
            assert mock_instance.post.call_count == 1
