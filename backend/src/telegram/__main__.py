"""Entry point for python -m src.telegram."""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main entrypoint for running the bot."""
    from .bot import bot, dp
    from .handlers import router

    dp.include_router(router)

    # Setup Menu Button
    from .bot import setup_menu_button
    await setup_menu_button()

    logger.info("Starting Telegram bot polling...")

    # Start polling
    await dp.start_polling(bot)


# Always run when executed as module
asyncio.run(main())
