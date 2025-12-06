"""
Recommendations worker for batch generation of Gemini-based food recommendations.

Runs scheduled batch job at 03:00 AM daily to generate personalized
recommendations for active users. Uses APScheduler for scheduling.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from faststream.kafka import KafkaBroker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.cache.redis_client import set_cache
from src.config import settings
from src.gemini import AllKeysExhaustedException, get_key_pool
from src.services.order_stats import OrderStatsService

logger = logging.getLogger(__name__)

# Database setup
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Kafka broker
broker = KafkaBroker(settings.KAFKA_BROKER_URL)

# APScheduler for nightly batch job
scheduler = AsyncIOScheduler()


async def generate_recommendations_batch():
    """
    Batch-generate recommendations for active users.

    Process:
    1. Get active users with >= 5 orders in last 30 days
    2. For each user:
       a. Collect order statistics
       b. Send to Gemini API (via key pool with rotation)
       c. Cache result in Redis with TTL 24h
    3. Log progress and errors

    If all API keys are exhausted, stops batch and logs error.
    Individual user errors are logged but don't stop the batch.
    """
    logger.info("Starting recommendations batch generation")

    async with async_session_factory() as session:
        stats_service = OrderStatsService(session)

        try:
            # Get active users (>= 5 orders in last 30 days)
            active_users = await stats_service.get_active_users(min_orders=5, days=30)
            logger.info(f"Found {len(active_users)} active users for recommendations")

            if not active_users:
                logger.info("No active users found, skipping batch")
                return

            success_count = 0
            error_count = 0
            key_pool = get_key_pool()

            for tgid in active_users:
                try:
                    # Get user statistics
                    user_stats = await stats_service.get_user_stats(tgid, days=30)

                    logger.debug(
                        "Generating recommendations",
                        extra={
                            "user_tgid": tgid,
                            "orders_count": user_stats["orders_count"],
                        },
                    )

                    # Generate recommendations via Gemini API
                    # Note: This assumes GeminiRecommendationService exists (subtask 3.2)
                    # For now, create a mock structure until client.py is implemented
                    try:
                        from src.gemini.client import (
                            get_recommendation_service,
                        )

                        recommendation_service = get_recommendation_service()
                        recommendations = await recommendation_service.generate_recommendations(
                            user_stats
                        )
                    except ImportError:
                        # Fallback if client not implemented yet
                        logger.warning(
                            "GeminiRecommendationService not available, skipping user",
                            extra={"user_tgid": tgid},
                        )
                        error_count += 1
                        continue

                    # Cache in Redis (TTL 24 hours)
                    cache_key = f"recommendations:user:{tgid}"
                    cache_data = {
                        "summary": recommendations.get("summary"),
                        "tips": recommendations.get("tips", []),
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    }

                    await set_cache(cache_key, json.dumps(cache_data), ttl=86400)

                    success_count += 1
                    logger.info(
                        "Generated recommendations for user",
                        extra={
                            "user_tgid": tgid,
                            "summary_length": len(recommendations.get("summary", "")),
                            "tips_count": len(recommendations.get("tips", [])),
                        },
                    )

                except AllKeysExhaustedException:
                    logger.error(
                        "All Gemini API keys exhausted, stopping batch",
                        extra={
                            "processed_users": success_count + error_count,
                            "total_users": len(active_users),
                            "success_count": success_count,
                            "error_count": error_count,
                        },
                    )
                    break

                except Exception as e:
                    error_count += 1
                    logger.error(
                        "Failed to generate recommendations for user",
                        extra={
                            "user_tgid": tgid,
                            "error": str(e),
                        },
                        exc_info=True,
                    )

            logger.info(
                "Batch generation completed",
                extra={
                    "total_users": len(active_users),
                    "success_count": success_count,
                    "error_count": error_count,
                    "success_rate": f"{success_count / len(active_users) * 100:.1f}%"
                    if active_users
                    else "0%",
                },
            )

        except Exception as e:
            logger.error(
                "Critical error in batch generation",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise


@broker.subscriber("lunch-bot.daily-tasks")
async def handle_daily_task(event: dict):
    """
    Alternative trigger: manual batch generation via Kafka event.

    This allows manual triggering of recommendation generation
    without waiting for the scheduled time.

    Args:
        event: Kafka event with type field
    """
    if event.get("type") == "generate_recommendations":
        logger.info(
            "Manual recommendations generation triggered via Kafka",
            extra={"event": event},
        )
        await generate_recommendations_batch()


if __name__ == "__main__":
    import signal

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info(
        "Starting recommendations worker",
        extra={
            "kafka_broker": settings.KAFKA_BROKER_URL,
            "database_url": settings.DATABASE_URL.split("@")[-1],  # Hide credentials
        },
    )

    async def main():
        """Main function to run the broker with scheduler."""
        # Start scheduler in async context
        scheduler.add_job(
            generate_recommendations_batch,
            trigger="cron",
            hour=3,
            minute=0,
            id="daily_recommendations",
            replace_existing=True,
        )
        scheduler.start()

        logger.info(
            "Recommendations scheduler started",
            extra={
                "schedule": "03:00 daily",
                "kafka_broker": settings.KAFKA_BROKER_URL,
            },
        )

        logger.info("Broker connecting to Kafka")

        async with broker:
            logger.info("Recommendations worker ready - waiting for messages")

            # Create stop event
            stop_event = asyncio.Event()

            # Handle graceful shutdown
            def shutdown_handler(signum, frame):
                logger.info("Received shutdown signal")
                stop_event.set()

            signal.signal(signal.SIGINT, shutdown_handler)
            signal.signal(signal.SIGTERM, shutdown_handler)

            # Wait for shutdown signal
            try:
                await stop_event.wait()
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received")

        logger.info("Recommendations worker shutting down")
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await engine.dispose()

    asyncio.run(main())
