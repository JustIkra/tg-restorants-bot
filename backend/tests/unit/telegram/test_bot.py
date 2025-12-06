"""Tests for Telegram bot initialization and menu button setup."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.exceptions import TelegramAPIError

from src.config import settings


class TestSetupMenuButton:
    """Tests for setup_menu_button function."""

    @patch("src.telegram.bot.bot")
    async def test_setup_menu_button_success(self, mock_bot):
        """Test menu button setup succeeds."""
        # Import after patching
        from src.telegram.bot import setup_menu_button

        mock_bot.set_chat_menu_button = AsyncMock()

        await setup_menu_button()

        # Should call set_chat_menu_button once
        mock_bot.set_chat_menu_button.assert_called_once()

        # Check the menu button configuration
        call_args = mock_bot.set_chat_menu_button.call_args
        menu_button = call_args[1]["menu_button"]

        assert menu_button.text == "Заказать обед"
        assert menu_button.web_app.url == settings.TELEGRAM_MINI_APP_URL

    @patch("src.telegram.bot.bot")
    @patch("src.telegram.bot.logger")
    async def test_setup_menu_button_logs_success(self, mock_logger, mock_bot):
        """Test menu button setup logs success message."""
        from src.telegram.bot import setup_menu_button

        mock_bot.set_chat_menu_button = AsyncMock()

        await setup_menu_button()

        # Should log success
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        log_message = call_args[0][0]

        assert "Menu button configured" in log_message

    @patch("src.telegram.bot.bot")
    @patch("src.telegram.bot.logger")
    async def test_setup_menu_button_telegram_api_error(self, mock_logger, mock_bot):
        """Test menu button setup handles TelegramAPIError gracefully."""
        from src.telegram.bot import setup_menu_button

        # Mock TelegramAPIError
        error = TelegramAPIError(method="setChatMenuButton", message="Invalid token")
        mock_bot.set_chat_menu_button = AsyncMock(side_effect=error)

        # Should not raise exception (bot can work without menu button)
        await setup_menu_button()

        # Should log error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        log_message = call_args[0][0]

        assert "Failed to setup menu button" in log_message
        assert "Telegram API error" in log_message

        # Should log with exc_info=True for traceback
        assert call_args[1]["exc_info"] is True

    @patch("src.telegram.bot.bot")
    @patch("src.telegram.bot.logger")
    async def test_setup_menu_button_unexpected_error(self, mock_logger, mock_bot):
        """Test menu button setup propagates unexpected errors."""
        from src.telegram.bot import setup_menu_button

        # Mock unexpected error (not TelegramAPIError)
        error = RuntimeError("Unexpected error")
        mock_bot.set_chat_menu_button = AsyncMock(side_effect=error)

        # Should raise exception for unexpected errors
        with pytest.raises(RuntimeError, match="Unexpected error"):
            await setup_menu_button()

        # Should log error before raising
        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args
        log_message = call_args[0][0]

        assert "Unexpected error during menu button setup" in log_message
        assert call_args[1]["exc_info"] is True

    @patch("src.telegram.bot.bot")
    async def test_setup_menu_button_uses_correct_url(self, mock_bot):
        """Test menu button setup uses TELEGRAM_MINI_APP_URL from settings."""
        from src.telegram.bot import setup_menu_button

        mock_bot.set_chat_menu_button = AsyncMock()

        await setup_menu_button()

        call_args = mock_bot.set_chat_menu_button.call_args
        menu_button = call_args[1]["menu_button"]

        # Should use URL from settings (default: http://localhost)
        assert menu_button.web_app.url == settings.TELEGRAM_MINI_APP_URL


class TestBotInitialization:
    """Tests for bot initialization."""

    def test_bot_token_from_settings(self):
        """Test bot is initialized with token from settings."""
        # Bot should be created (we can't easily test the token value
        # without exposing it, but we can verify bot exists and is initialized)
        from src.telegram.bot import bot

        assert bot is not None
        # Bot should have a session (indicates proper initialization)
        assert bot.session is not None

    def test_dispatcher_created(self):
        """Test dispatcher is created during initialization."""
        from src.telegram.bot import dp

        assert dp is not None


class TestMainFunction:
    """Tests for main entrypoint function."""

    @patch("src.telegram.bot.dp")
    @patch("src.telegram.bot.setup_menu_button")
    async def test_main_includes_router(self, mock_setup_menu, mock_dp):
        """Test main function includes handlers router."""
        from src.telegram.bot import main

        mock_dp.include_router = MagicMock()
        mock_dp.start_polling = AsyncMock()

        await main()

        # Should include router
        mock_dp.include_router.assert_called_once()

    @patch("src.telegram.bot.dp")
    @patch("src.telegram.bot.setup_menu_button")
    async def test_main_calls_setup_menu_button(self, mock_setup_menu, mock_dp):
        """Test main function calls setup_menu_button before polling."""
        from src.telegram.bot import main

        mock_dp.include_router = MagicMock()
        mock_dp.start_polling = AsyncMock()

        await main()

        # Should call setup_menu_button
        mock_setup_menu.assert_called_once()

    @patch("src.telegram.bot.dp")
    @patch("src.telegram.bot.setup_menu_button")
    @patch("src.telegram.bot.bot")
    async def test_main_starts_polling(self, mock_bot, mock_setup_menu, mock_dp):
        """Test main function starts polling after setup."""
        from src.telegram.bot import main

        mock_dp.include_router = MagicMock()
        mock_dp.start_polling = AsyncMock()

        await main()

        # Should start polling with bot instance
        mock_dp.start_polling.assert_called_once_with(mock_bot)

    @patch("src.telegram.bot.dp")
    @patch("src.telegram.bot.setup_menu_button")
    async def test_main_order_of_operations(self, mock_setup_menu, mock_dp):
        """Test main function calls operations in correct order."""
        from src.telegram.bot import main

        mock_dp.include_router = MagicMock()
        mock_dp.start_polling = AsyncMock()

        call_order = []

        def track_include_router(*args):
            call_order.append("include_router")

        async def track_setup_menu():
            call_order.append("setup_menu_button")

        async def track_start_polling(*args):
            call_order.append("start_polling")

        mock_dp.include_router = track_include_router
        mock_setup_menu.side_effect = track_setup_menu
        mock_dp.start_polling = track_start_polling

        await main()

        # Should be called in correct order
        assert call_order == ["include_router", "setup_menu_button", "start_polling"]
