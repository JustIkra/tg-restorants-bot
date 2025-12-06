import json
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..cache.redis_client import get_cache
from ..database import get_db
from ..schemas.recommendations import OrderStats, RecommendationsResponse
from ..services.order_stats import OrderStatsService

router = APIRouter(prefix="/users", tags=["recommendations"])


def get_order_stats_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OrderStatsService:
    return OrderStatsService(db)


@router.get("/{tgid}/recommendations", response_model=RecommendationsResponse)
async def get_user_recommendations(
    tgid: int,
    service: Annotated[OrderStatsService, Depends(get_order_stats_service)],
) -> RecommendationsResponse:
    """
    Получение рекомендаций для пользователя.

    Логика работы:
    1. Проверить кэш Redis: recommendations:user:{tgid}
    2. Если есть - вернуть кэшированные данные
    3. Если нет - вернуть пустые рекомендации + текущую статистику

    Рекомендации генерируются в batch режиме ночью (worker),
    этот endpoint только читает из кэша.

    Args:
        tgid: Telegram ID пользователя
        service: Сервис статистики заказов

    Returns:
        RecommendationsResponse с рекомендациями или пустыми данными
    """
    # Redis key для рекомендаций пользователя
    cache_key = f"recommendations:user:{tgid}"

    # Попытка получить из кэша
    cached = await get_cache(cache_key)

    # Получить текущую статистику (всегда свежие данные)
    stats = await service.get_user_stats(tgid)

    if cached:
        # Парсим кэшированные рекомендации
        data = json.loads(cached)
        return RecommendationsResponse(
            summary=data.get("summary"),
            tips=data.get("tips", []),
            stats=OrderStats(
                orders_last_30_days=stats["orders_count"],
                categories=stats["categories"],
                unique_dishes=stats["unique_dishes"],
                favorite_dishes=stats["favorite_dishes"],
            ),
            generated_at=data.get("generated_at"),
        )

    # Нет кэша - возвращаем пустые рекомендации + статистику
    return RecommendationsResponse(
        summary=None,
        tips=[],
        stats=OrderStats(
            orders_last_30_days=stats["orders_count"],
            categories=stats["categories"],
            unique_dishes=stats["unique_dishes"],
            favorite_dishes=stats["favorite_dishes"],
        ),
        generated_at=None,
    )
