import json
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser, get_current_user
from ..cache.redis_client import get_cache, set_cache
from ..database import get_db
from ..gemini import AllKeysExhaustedException, get_recommendation_service
from ..schemas.recommendations import OrderStats, RecommendationsResponse
from ..services.order_stats import OrderStatsService

logger = structlog.get_logger(__name__)

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

        # Parse generated_at from ISO string to datetime (if exists)
        generated_at_str = data.get("generated_at")
        generated_at = (
            datetime.fromisoformat(generated_at_str)
            if generated_at_str
            else None
        )

        return RecommendationsResponse(
            summary=data.get("summary"),
            tips=data.get("tips", []),
            stats=OrderStats(
                orders_last_30_days=stats["orders_count"],
                categories=stats["categories"],
                unique_dishes=stats["unique_dishes"],
                favorite_dishes=stats["favorite_dishes"],
            ),
            generated_at=generated_at,
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


@router.post("/{tgid}/recommendations/generate", response_model=RecommendationsResponse)
async def generate_user_recommendations(
    tgid: int,
    current_user: CurrentUser,
    service: Annotated[OrderStatsService, Depends(get_order_stats_service)],
) -> RecommendationsResponse:
    """
    Force generate AI recommendations for user.

    Triggers immediate Gemini API generation instead of waiting for batch job.
    Requires minimum 5 orders in last 30 days.

    Auth: manager | self

    Args:
        tgid: Telegram ID of the user
        current_user: Current authenticated user
        service: Order statistics service

    Returns:
        RecommendationsResponse with generated recommendations

    Raises:
        HTTPException:
            - 403 Forbidden if not manager and not self
            - 400 Bad Request if less than 5 orders
            - 500 Internal Server Error if Gemini API fails
    """
    # Authorization check: manager or self
    if current_user.role != "manager" and current_user.tgid != tgid:
        logger.warning(
            "Unauthorized recommendation generation attempt",
            requester_tgid=current_user.tgid,
            target_tgid=tgid,
        )
        raise HTTPException(status_code=403, detail="Access denied")

    # Get user statistics for last 30 days
    stats = await service.get_user_stats(tgid, days=30)

    # Validate minimum orders requirement
    if stats["orders_count"] < 5:
        logger.info(
            "Insufficient orders for recommendation generation",
            tgid=tgid,
            orders_count=stats["orders_count"],
        )
        raise HTTPException(
            status_code=400,
            detail="Minimum 5 orders required for recommendations",
        )

    try:
        # Generate recommendations using Gemini API
        logger.info(
            "Starting manual recommendation generation",
            tgid=tgid,
            orders_count=stats["orders_count"],
        )

        gemini_service = get_recommendation_service()
        result = await gemini_service.generate_recommendations(stats)

        # Cache result (same as batch worker)
        cache_key = f"recommendations:user:{tgid}"
        generated_at = datetime.now(timezone.utc)
        cache_data = {
            "summary": result.get("summary"),
            "tips": result.get("tips", []),
            "generated_at": generated_at.isoformat(),
        }

        await set_cache(cache_key, json.dumps(cache_data), ttl=86400)

        logger.info(
            "Recommendations generated and cached successfully",
            tgid=tgid,
            has_summary=bool(result.get("summary")),
            tips_count=len(result.get("tips", [])),
        )

        # Return response
        return RecommendationsResponse(
            summary=result.get("summary"),
            tips=result.get("tips", []),
            stats=OrderStats(
                orders_last_30_days=stats["orders_count"],
                categories=stats["categories"],
                unique_dishes=stats["unique_dishes"],
                favorite_dishes=stats["favorite_dishes"],
            ),
            generated_at=generated_at,
        )

    except AllKeysExhaustedException as e:
        logger.error(
            "All Gemini API keys exhausted",
            tgid=tgid,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail="Service temporarily unavailable. Please try again later.",
        )
    except Exception as e:
        logger.error(
            "Failed to generate recommendations",
            tgid=tgid,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations",
        )
