"""Telegram bot initialization and main entrypoint."""

from aiogram import Bot, Dispatcher

from ..config import settings

# Initialize bot instance
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

# Create dispatcher instance
dp = Dispatcher()


async def main():
    """Main entrypoint for running the bot."""
    # Import and register handlers
    from .handlers import router

    dp.include_router(router)

    # Start polling for updates
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
