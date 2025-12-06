"""Tests for Telegram bot handlers."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from aiogram.types import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Message, User, WebAppInfo

from src.config import settings
from src.telegram.handlers import cmd_help, cmd_link, cmd_order, cmd_start


@pytest.fixture
def mock_message():
    """Create mock Telegram Message for testing."""
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 123456789
    message.from_user = MagicMock(spec=User)
    message.from_user.username = "testuser"
    return message


class TestCmdStart:
    """Tests for /start command handler."""

    async def test_cmd_start_sends_welcome_message(self, mock_message):
        """Test /start command sends welcome message with Mini App button."""
        await cmd_start(mock_message)

        # Should call answer once
        mock_message.answer.assert_called_once()

        # Check message text
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]
        assert "👋 Привет!" in message_text
        assert "бот для заказа обедов" in message_text
        assert "/link" in message_text

    async def test_cmd_start_includes_mini_app_button(self, mock_message):
        """Test /start command includes inline keyboard with Mini App button."""
        await cmd_start(mock_message)

        # Check keyboard
        call_args = mock_message.answer.call_args
        keyboard = call_args[1]["reply_markup"]

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 1

        # Check button
        button = keyboard.inline_keyboard[0][0]
        assert isinstance(button, InlineKeyboardButton)
        assert "Заказать обед" in button.text
        assert button.web_app is not None
        assert isinstance(button.web_app, WebAppInfo)
        assert button.web_app.url == settings.TELEGRAM_MINI_APP_URL


class TestCmdOrder:
    """Tests for /order command handler."""

    async def test_cmd_order_sends_message(self, mock_message):
        """Test /order command sends message with Mini App button."""
        await cmd_order(mock_message)

        # Should call answer once
        mock_message.answer.assert_called_once()

        # Check message text
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]
        assert "приложение для заказа" in message_text.lower()

    async def test_cmd_order_includes_mini_app_button(self, mock_message):
        """Test /order command includes inline keyboard with Mini App button."""
        await cmd_order(mock_message)

        # Check keyboard
        call_args = mock_message.answer.call_args
        keyboard = call_args[1]["reply_markup"]

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 1

        # Check button
        button = keyboard.inline_keyboard[0][0]
        assert isinstance(button, InlineKeyboardButton)
        assert "Заказать обед" in button.text
        assert button.web_app is not None
        assert isinstance(button.web_app, WebAppInfo)
        assert button.web_app.url == settings.TELEGRAM_MINI_APP_URL

    async def test_cmd_order_uses_correct_url(self, mock_message):
        """Test /order command uses TELEGRAM_MINI_APP_URL from settings."""
        await cmd_order(mock_message)

        call_args = mock_message.answer.call_args
        keyboard = call_args[1]["reply_markup"]
        button = keyboard.inline_keyboard[0][0]

        # Should use URL from settings (default: http://localhost)
        assert button.web_app.url == settings.TELEGRAM_MINI_APP_URL


class TestCmdHelp:
    """Tests for /help command handler."""

    async def test_cmd_help_lists_all_commands(self, mock_message):
        """Test /help command lists all available commands."""
        await cmd_help(mock_message)

        # Should call answer once
        mock_message.answer.assert_called_once()

        # Check message text includes all commands
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        assert "/start" in message_text
        assert "/order" in message_text
        assert "/link" in message_text
        assert "/status" in message_text
        assert "/help" in message_text

    async def test_cmd_help_mentions_mini_app(self, mock_message):
        """Test /help command mentions Mini App and Menu Button."""
        await cmd_help(mock_message)

        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        # Should mention Menu button or /order for Mini App
        assert "Menu" in message_text or "/order" in message_text


class TestCmdLink:
    """Tests for /link command handler."""

    async def test_cmd_link_invalid_format_no_cafe_id(self, mock_message):
        """Test /link command with invalid format (no cafe_id)."""
        mock_message.text = "/link"

        await cmd_link(mock_message)

        # Should send error message
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        assert "❌" in message_text
        assert "Неверный формат" in message_text
        assert "/link <cafe_id>" in message_text

    async def test_cmd_link_invalid_format_non_numeric(self, mock_message):
        """Test /link command with non-numeric cafe_id."""
        mock_message.text = "/link abc"

        await cmd_link(mock_message)

        # Should send error message
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        assert "❌" in message_text
        assert "Неверный формат" in message_text

    @patch("src.telegram.handlers.httpx.AsyncClient")
    async def test_cmd_link_success(self, mock_client_class, mock_message):
        """Test /link command successfully creates link request."""
        mock_message.text = "/link 1"

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "cafe_id": 1,
            "tg_chat_id": 123456789,
            "status": "pending",
        }

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        mock_client_class.return_value = mock_client

        await cmd_link(mock_message)

        # Should call API
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert f"{settings.BACKEND_API_URL}/cafes/1/link-request" in call_args[0][0]
        assert call_args[1]["json"]["tg_chat_id"] == 123456789
        assert call_args[1]["json"]["tg_username"] == "testuser"

        # Should send success message
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        assert "✅" in message_text
        assert "успешно создана" in message_text
        assert "ID заявки: 1" in message_text

    @patch("src.telegram.handlers.httpx.AsyncClient")
    async def test_cmd_link_cafe_not_found(self, mock_client_class, mock_message):
        """Test /link command with non-existent cafe."""
        mock_message.text = "/link 999"

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        mock_client_class.return_value = mock_client

        await cmd_link(mock_message)

        # Should send error message
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        assert "❌" in message_text
        assert "не найдено" in message_text

    @patch("src.telegram.handlers.httpx.AsyncClient")
    async def test_cmd_link_bad_request(self, mock_client_class, mock_message):
        """Test /link command with bad request (e.g., duplicate request)."""
        mock_message.text = "/link 1"

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "detail": "У этого чата уже есть активная заявка"
        }

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        mock_client_class.return_value = mock_client

        await cmd_link(mock_message)

        # Should send error message with detail
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        assert "❌" in message_text
        assert "уже есть активная заявка" in message_text

    @patch("src.telegram.handlers.httpx.AsyncClient")
    async def test_cmd_link_timeout(self, mock_client_class, mock_message):
        """Test /link command handles timeout errors."""
        mock_message.text = "/link 1"

        # Create async mock that raises timeout
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        # Mock the async context manager
        async_context_manager = MagicMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_client)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = async_context_manager

        await cmd_link(mock_message)

        # Should send timeout error message
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        assert "⏱️" in message_text
        assert "время ожидания" in message_text.lower()

    @patch("src.telegram.handlers.httpx.AsyncClient")
    async def test_cmd_link_request_error(self, mock_client_class, mock_message):
        """Test /link command handles connection errors."""
        mock_message.text = "/link 1"

        # httpx.RequestError requires a message parameter
        error = httpx.RequestError("Connection failed", request=MagicMock())

        # Create async mock that raises RequestError
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=error)

        # Mock the async context manager
        async_context_manager = MagicMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_client)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = async_context_manager

        await cmd_link(mock_message)

        # Should send connection error message
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]

        assert "❌" in message_text
        assert "подключения" in message_text.lower()

    @patch("src.telegram.handlers.httpx.AsyncClient")
    async def test_cmd_link_uses_backend_api_url(self, mock_client_class, mock_message):
        """Test /link command uses BACKEND_API_URL from settings."""
        mock_message.text = "/link 1"

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "status": "pending"}

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        mock_client_class.return_value = mock_client

        await cmd_link(mock_message)

        # Should use BACKEND_API_URL (default: http://backend:8000/api/v1)
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        url = call_args[0][0]

        assert settings.BACKEND_API_URL in url
        assert "http://backend:8000/api/v1" in url or settings.BACKEND_API_URL in url
