"""Telegram bot command handlers for cafe linking and Mini App."""

import logging
import re

import httpx
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from ..config import settings

router = Router()
logger = logging.getLogger(__name__)

# Base URL for backend API (use Docker hostname for inter-container communication)
API_BASE_URL = settings.BACKEND_API_URL


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handle /start command.

    Sends welcome message with Mini App button and instructions.
    """
    webapp = WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Заказать обед", web_app=webapp)],
        ]
    )
    await message.answer(
        "👋 Привет! Это бот для заказа обедов.\n\n"
        "Нажмите кнопку ниже, чтобы открыть меню и сделать заказ.\n\n"
        "📌 Для менеджеров кафе: /link <cafe_id> - привязать кафе к чату",
        reply_markup=keyboard,
    )


@router.message(Command("order"))
async def cmd_order(message: Message):
    """
    Handle /order command - launch Mini App for ordering.

    Sends inline keyboard with web_app button to open the Mini App.
    """
    webapp = WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Заказать обед", web_app=webapp)],
        ]
    )
    await message.answer(
        "Откройте приложение для заказа обеда:",
        reply_markup=keyboard,
    )


@router.message(Command("link"))
async def cmd_link(message: Message):
    """
    Handle /link command to create cafe link request.

    Format: /link <cafe_id>

    Steps:
    1. Parse cafe_id from command
    2. Extract chat_id and username from message
    3. Send POST request to backend API
    4. Notify user of the result
    """
    # Extract cafe_id from command text
    command_text = message.text or ""
    match = re.match(r"/link\s+(\d+)", command_text.strip())

    if not match:
        await message.answer(
            "❌ Неверный формат команды.\n\n"
            "Используйте: /link <cafe_id>\n"
            "Например: /link 1"
        )
        return

    cafe_id = int(match.group(1))
    chat_id = message.chat.id
    username = message.from_user.username if message.from_user else None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/cafes/{cafe_id}/link-request",
                json={"tg_chat_id": chat_id, "tg_username": username},
            )

            if response.status_code == 201:
                # Successfully created link request
                data = response.json()
                await message.answer(
                    f"✅ Заявка на привязку кафе #{cafe_id} успешно создана!\n\n"
                    f"ID заявки: {data['id']}\n"
                    f"Статус: {data['status']}\n\n"
                    "Ожидайте одобрения от менеджера."
                )
                logger.info(
                    "Link request created",
                    extra={
                        "cafe_id": cafe_id,
                        "chat_id": chat_id,
                        "request_id": data["id"],
                    },
                )

            elif response.status_code == 404:
                # Cafe not found
                await message.answer(
                    f"❌ Кафе с ID {cafe_id} не найдено.\n\n" "Проверьте правильность ID."
                )

            elif response.status_code == 400:
                # Bad request (e.g., already has pending request)
                error_detail = response.json().get("detail", "Неизвестная ошибка")
                await message.answer(
                    f"❌ Не удалось создать заявку:\n\n{error_detail}"
                )

            else:
                # Unexpected error
                await message.answer(
                    "❌ Произошла ошибка при создании заявки.\n\n"
                    "Попробуйте позже или обратитесь к администратору."
                )
                logger.error(
                    "Unexpected API response",
                    extra={"status_code": response.status_code, "body": response.text},
                )

    except httpx.TimeoutException:
        await message.answer(
            "⏱️ Превышено время ожидания ответа от сервера.\n\n"
            "Попробуйте позже."
        )
        logger.error("API request timeout", extra={"cafe_id": cafe_id})

    except httpx.RequestError as e:
        await message.answer(
            "❌ Ошибка подключения к серверу.\n\n"
            "Попробуйте позже или обратитесь к администратору."
        )
        logger.error(
            "API request failed", extra={"cafe_id": cafe_id, "error": str(e)}
        )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """
    Handle /status command to show link status.

    Shows current link status for this chat (if linked to a cafe).
    """
    await message.answer(
        "ℹ️ Статус привязки:\n\n"
        "Эта функция в разработке. Используйте /link для привязки кафе."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handle /help command.

    Shows available commands and their descriptions.
    """
    await message.answer(
        "📖 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/order - Открыть меню для заказа обеда\n"
        "/link <cafe_id> - Привязать кафе к чату (для менеджеров)\n"
        "/status - Проверить статус привязки\n"
        "/help - Показать эту справку\n\n"
        "💡 Для заказа обеда нажмите кнопку Menu или используйте /order"
    )
