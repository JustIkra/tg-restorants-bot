"""Telegram bot command handlers for cafe linking."""

import logging
import re

import httpx
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from ..config import settings

router = Router()
logger = logging.getLogger(__name__)

# Base URL for backend API
API_BASE_URL = "http://localhost:8000/api/v1"


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handle /start command.

    Sends welcome message with instructions on how to link cafe.
    """
    await message.answer(
        "👋 Привет! Это бот для уведомлений о заказах.\n\n"
        "Для привязки кафе к этому чату используйте команду:\n"
        "/link <cafe_id>\n\n"
        "Например: /link 1"
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
        "/link <cafe_id> - Привязать кафе к этому чату\n"
        "/status - Проверить статус привязки\n"
        "/help - Показать эту справку\n\n"
        "Пример использования:\n"
        "/link 1 - Привязать кафе с ID 1"
    )
