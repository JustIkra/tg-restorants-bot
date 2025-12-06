from datetime import datetime

from pydantic import BaseModel


class OrderStats(BaseModel):
    """Статистика заказов пользователя."""

    orders_last_30_days: int
    categories: dict[str, dict]  # {"soup": {"count": 10, "percent": 40.0}}
    unique_dishes: int
    favorite_dishes: list[dict]  # [{"name": "Борщ", "count": 5}]


class RecommendationsResponse(BaseModel):
    """Ответ endpoint рекомендаций."""

    summary: str | None
    tips: list[str]
    stats: OrderStats
    generated_at: datetime | None
