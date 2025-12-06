"""Notifications worker for sending aggregated orders to cafes via Telegram."""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

import httpx
from faststream.kafka import KafkaBroker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker

from backend.src.config import settings
from backend.src.kafka.events import DeadlinePassedEvent
from backend.src.models.cafe import Cafe, Combo, MenuItem
from backend.src.models.order import Order
from backend.src.models.user import User

logger = logging.getLogger(__name__)

# Database setup
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Kafka broker
broker = KafkaBroker(settings.KAFKA_BROKER_URL)


async def get_cafe_with_orders(
    db: AsyncSession, cafe_id: int, order_date: str
) -> tuple[Cafe | None, list[Order]]:
    """Fetch cafe and orders for the given date.

    Args:
        db: Database session
        cafe_id: ID of the cafe
        order_date: Date in YYYY-MM-DD format

    Returns:
        Tuple of (Cafe, list of Orders) or (None, []) if cafe not found
    """
    # Fetch cafe
    cafe_result = await db.execute(select(Cafe).where(Cafe.id == cafe_id))
    cafe = cafe_result.scalar_one_or_none()

    if not cafe:
        logger.warning(f"Cafe not found", extra={"cafe_id": cafe_id})
        return None, []

    # Fetch orders for this cafe and date
    orders_result = await db.execute(
        select(Order)
        .where(Order.cafe_id == cafe_id, Order.order_date == order_date)
        .options(
            selectinload(Order.user),
            selectinload(Order.combo),
        )
    )
    orders = list(orders_result.scalars().all())

    return cafe, orders


async def get_menu_items(db: AsyncSession, cafe_id: int) -> dict[int, MenuItem]:
    """Fetch all menu items for a cafe.

    Args:
        db: Database session
        cafe_id: ID of the cafe

    Returns:
        Dictionary mapping menu_item_id to MenuItem
    """
    result = await db.execute(select(MenuItem).where(MenuItem.cafe_id == cafe_id))
    items = result.scalars().all()
    return {item.id: item for item in items}


def format_notification(
    cafe: Cafe, date: str, orders: list[Order], menu_items: dict[int, MenuItem]
) -> str:
    """Format notification message for Telegram.

    Args:
        cafe: Cafe object
        date: Order date (YYYY-MM-DD)
        orders: List of orders
        menu_items: Dictionary of menu items by ID

    Returns:
        Formatted message in Markdown
    """
    if not orders:
        return ""

    lines = [
        f"📋 *{cafe.name}* — Заказ на {date}",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    total_amount = Decimal("0")

    for order in orders:
        # User info
        lines.append(f"👤 *{order.user.name}*:")

        # Combo info
        combo = order.combo
        lines.append(f"   • {combo.name}")

        # Combo items
        for combo_item in order.combo_items:
            menu_item_id = combo_item.get("menu_item_id")
            category = combo_item.get("category", "unknown")

            if menu_item_id and menu_item_id in menu_items:
                menu_item = menu_items[menu_item_id]
                lines.append(f"     - {menu_item.name} ({category})")

        # Extras
        for extra in order.extras:
            menu_item_id = extra.get("menu_item_id")
            quantity = extra.get("quantity", 1)

            if menu_item_id and menu_item_id in menu_items:
                extra_item = menu_items[menu_item_id]
                lines.append(f"   • {extra_item.name} ×{quantity}")

        # Notes
        if order.notes:
            lines.append(f"   📝 {order.notes}")

        lines.append("")  # Empty line between orders
        total_amount += order.total_price

    # Summary
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"Итого: {len(orders)} заказов, {total_amount} ₽")

    return "\n".join(lines)


async def send_telegram_notification(chat_id: int, message: str) -> bool:
    """Send notification via Telegram Bot API.

    Args:
        chat_id: Telegram chat ID
        message: Message text in Markdown format

    Returns:
        True if sent successfully, False otherwise
    """
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    max_retries = 3
    backoff = 1  # seconds

    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                logger.info(
                    "Telegram notification sent successfully",
                    extra={
                        "chat_id": chat_id,
                        "attempt": attempt + 1,
                    },
                )
                return True

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limit hit - wait and retry
                    retry_after = int(e.response.headers.get("Retry-After", backoff))
                    logger.warning(
                        f"Rate limit hit, retrying after {retry_after}s",
                        extra={
                            "chat_id": chat_id,
                            "attempt": attempt + 1,
                            "retry_after": retry_after,
                        },
                    )
                    await asyncio.sleep(retry_after)
                    backoff *= 2
                elif e.response.status_code in (400, 403, 404):
                    # Client error - don't retry
                    logger.error(
                        f"Telegram API client error: {e.response.status_code}",
                        extra={
                            "chat_id": chat_id,
                            "status_code": e.response.status_code,
                            "response": e.response.text,
                        },
                    )
                    return False
                else:
                    # Server error - retry
                    logger.warning(
                        f"Telegram API server error: {e.response.status_code}",
                        extra={
                            "chat_id": chat_id,
                            "attempt": attempt + 1,
                            "status_code": e.response.status_code,
                        },
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2

            except httpx.RequestError as e:
                logger.warning(
                    f"Network error sending notification",
                    extra={
                        "chat_id": chat_id,
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2

    logger.error(
        "Failed to send notification after all retries",
        extra={"chat_id": chat_id, "max_retries": max_retries},
    )
    return False


@broker.subscriber("lunch-bot.deadlines")
async def handle_deadline_passed(event: DeadlinePassedEvent) -> None:
    """Handle deadline.passed event and send notifications to cafes.

    Args:
        event: DeadlinePassedEvent with cafe_id and date
    """
    logger.info(
        "Processing deadline.passed event",
        extra={
            "cafe_id": event.cafe_id,
            "date": event.date,
            "timestamp": event.timestamp.isoformat(),
        },
    )

    async with async_session_factory() as db:
        try:
            # Fetch cafe and orders
            cafe, orders = await get_cafe_with_orders(db, event.cafe_id, event.date)

            if not cafe:
                logger.warning(
                    "Cafe not found for deadline event",
                    extra={"cafe_id": event.cafe_id, "date": event.date},
                )
                return

            # Check if cafe is linked to Telegram and notifications are enabled
            if not cafe.tg_chat_id:
                logger.info(
                    "Cafe not linked to Telegram, skipping notification",
                    extra={"cafe_id": event.cafe_id, "cafe_name": cafe.name},
                )
                return

            if not cafe.notifications_enabled:
                logger.info(
                    "Notifications disabled for cafe, skipping",
                    extra={"cafe_id": event.cafe_id, "cafe_name": cafe.name},
                )
                return

            # If no orders, skip notification
            if not orders:
                logger.info(
                    "No orders for cafe on this date, skipping notification",
                    extra={
                        "cafe_id": event.cafe_id,
                        "cafe_name": cafe.name,
                        "date": event.date,
                    },
                )
                return

            # Fetch menu items
            menu_items = await get_menu_items(db, event.cafe_id)

            # Format notification message
            message = format_notification(cafe, event.date, orders, menu_items)

            if not message:
                logger.warning(
                    "Empty notification message generated",
                    extra={"cafe_id": event.cafe_id, "date": event.date},
                )
                return

            # Send notification via Telegram
            success = await send_telegram_notification(cafe.tg_chat_id, message)

            if success:
                logger.info(
                    "Notification sent successfully",
                    extra={
                        "cafe_id": event.cafe_id,
                        "cafe_name": cafe.name,
                        "chat_id": cafe.tg_chat_id,
                        "date": event.date,
                        "orders_count": len(orders),
                    },
                )
            else:
                logger.error(
                    "Failed to send notification",
                    extra={
                        "cafe_id": event.cafe_id,
                        "cafe_name": cafe.name,
                        "chat_id": cafe.tg_chat_id,
                        "date": event.date,
                    },
                )

        except Exception as e:
            logger.error(
                "Error processing deadline.passed event",
                extra={
                    "cafe_id": event.cafe_id,
                    "date": event.date,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise


@broker.on_startup
async def startup_event():
    """Log startup of notifications worker."""
    logger.info(
        "Notifications worker started",
        extra={
            "kafka_broker": settings.KAFKA_BROKER_URL,
            "topic": "lunch-bot.deadlines",
        },
    )


@broker.on_shutdown
async def shutdown_event():
    """Log shutdown of notifications worker."""
    logger.info("Notifications worker shutting down")
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(broker.start())
