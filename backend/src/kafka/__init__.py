"""Kafka integration module for event-driven architecture."""

from backend.src.kafka.events import DailyTaskEvent, DeadlinePassedEvent
from backend.src.kafka.producer import get_kafka_broker, publish_daily_task, publish_deadline_passed

__all__ = [
    "get_kafka_broker",
    "publish_deadline_passed",
    "publish_daily_task",
    "DeadlinePassedEvent",
    "DailyTaskEvent",
]
