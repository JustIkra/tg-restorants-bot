"""Kafka integration module for event-driven architecture."""

from .events import DailyTaskEvent, DeadlinePassedEvent
from .producer import get_kafka_broker, publish_daily_task, publish_deadline_passed

__all__ = [
    "get_kafka_broker",
    "publish_deadline_passed",
    "publish_daily_task",
    "DeadlinePassedEvent",
    "DailyTaskEvent",
]
