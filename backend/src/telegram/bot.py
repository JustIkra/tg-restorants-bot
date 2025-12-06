"""Telegram bot initialization and main entrypoint."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.types import MenuButtonWebApp, WebAppInfo

from ..config import settings

logger = logging.getLogger(__name__)

# Initialize bot instance
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

# Create dispatcher instance
dp = Dispatcher()


async def setup_menu_button():
    """Configure Menu Button for Mini App launch."""
    try:
        webapp = WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL)
        menu_button = MenuButtonWebApp(text="Заказать обед", web_app=webapp)
        await bot.set_chat_menu_button(menu_button=menu_button)
        logger.info(
            "Menu button configured with URL: %s",
            settings.TELEGRAM_MINI_APP_URL
        )
    except TelegramAPIError as e:
        logger.error(
            "Failed to setup menu button (Telegram API error): %s",
            e,
            exc_info=True
        )
        # Don't re-raise - bot can work without Menu Button (there is /order command)
    except Exception as e:
        logger.error(
            "Unexpected error during menu button setup: %s",
            e,
            exc_info=True
        )
        # Critical error - propagate
        raise


async def main():
    """Main entrypoint for running the bot."""
    # Import and register handlers
    from .handlers import router

    dp.include_router(router)

    # Setup Menu Button for Mini App
    await setup_menu_button()

    # Start polling for updates
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
