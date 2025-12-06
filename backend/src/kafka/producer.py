"""Kafka producer for publishing events."""

import logging
from datetime import datetime

from faststream.kafka import KafkaBroker

from backend.src.config import settings
from backend.src.kafka.events import DailyTaskEvent, DeadlinePassedEvent

logger = logging.getLogger(__name__)

# Global Kafka broker instance
_broker: KafkaBroker | None = None


def get_kafka_broker() -> KafkaBroker:
    """Get or create the Kafka broker instance.

    Returns:
        KafkaBroker: Configured Kafka broker for publishing events.
    """
    global _broker
    if _broker is None:
        _broker = KafkaBroker(settings.KAFKA_BROKER_URL)
        logger.info(f"Kafka broker initialized: {settings.KAFKA_BROKER_URL}")
    return _broker


async def publish_deadline_passed(cafe_id: int, date: str) -> None:
    """Publish a deadline.passed event to Kafka.

    This event triggers the notifications worker to send aggregated
    orders to the cafe via Telegram.

    Args:
        cafe_id: ID of the cafe
        date: Date of the orders (YYYY-MM-DD format)
    """
    broker = get_kafka_broker()
    event = DeadlinePassedEvent(cafe_id=cafe_id, date=date)

    try:
        await broker.publish(
            event.model_dump(),
            topic="lunch-bot.deadlines",
        )
        logger.info(
            f"Published deadline.passed event",
            extra={
                "cafe_id": cafe_id,
                "date": date,
                "topic": "lunch-bot.deadlines",
                "timestamp": event.timestamp.isoformat(),
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to publish deadline.passed event",
            extra={
                "cafe_id": cafe_id,
                "date": date,
                "error": str(e),
            },
            exc_info=True,
        )
        raise


async def publish_daily_task(task_type: str) -> None:
    """Publish a daily task event to Kafka.

    Used for triggering scheduled batch operations like
    recommendations generation.

    Args:
        task_type: Type of daily task (e.g., 'generate_recommendations')
    """
    broker = get_kafka_broker()
    event = DailyTaskEvent(type=task_type)

    try:
        await broker.publish(
            event.model_dump(),
            topic="lunch-bot.daily-tasks",
        )
        logger.info(
            f"Published daily task event",
            extra={
                "task_type": task_type,
                "topic": "lunch-bot.daily-tasks",
                "timestamp": event.timestamp.isoformat(),
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to publish daily task event",
            extra={
                "task_type": task_type,
                "error": str(e),
            },
            exc_info=True,
        )
        raise
