"""Health check endpoints for monitoring system status."""

from fastapi import APIRouter, HTTPException
from redis.asyncio import Redis
from sqlalchemy import text

from ..config import settings
from ..database import async_session_maker

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health():
    """Basic health check - always returns ok if service is running."""
    return {"status": "ok"}


@router.get("/db")
async def health_db():
    """Check PostgreSQL database connection."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        return {"status": "ok", "service": "postgresql"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "service": "postgresql", "error": str(e)}
        )


@router.get("/redis")
async def health_redis():
    """Check Redis connection."""
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.close()
        return {"status": "ok", "service": "redis"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "service": "redis", "error": str(e)}
        )


@router.get("/all")
async def health_all():
    """Check all dependencies at once."""
    results = {
        "status": "ok",
        "services": {}
    }

    # Check PostgreSQL
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        results["services"]["postgresql"] = "ok"
    except Exception as e:
        results["status"] = "degraded"
        results["services"]["postgresql"] = f"error: {str(e)}"

    # Check Redis
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.close()
        results["services"]["redis"] = "ok"
    except Exception as e:
        results["status"] = "degraded"
        results["services"]["redis"] = f"error: {str(e)}"

    if results["status"] == "degraded":
        raise HTTPException(status_code=503, detail=results)

    return results
