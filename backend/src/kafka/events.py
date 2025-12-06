"""Pydantic schemas for Kafka events."""

from datetime import datetime

from pydantic import BaseModel, Field


class DeadlinePassedEvent(BaseModel):
    """Event published when a cafe's order deadline has passed.

    Triggers the notifications worker to send aggregated orders
    to the cafe via Telegram.
    """

    type: str = Field(default="deadline.passed", frozen=True)
    cafe_id: int = Field(description="ID of the cafe")
    date: str = Field(description="Date of the orders (YYYY-MM-DD)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DailyTaskEvent(BaseModel):
    """Event published for scheduled daily tasks.

    Used for triggering batch operations like recommendations generation.
    """

    type: str = Field(description="Type of daily task (e.g., 'generate_recommendations')")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
