"""
Redis client wrapper for async operations.

Provides singleton Redis client and common caching functions.
Uses redis.asyncio for async support.
"""

import structlog
from redis.asyncio import ConnectionPool, Redis

from backend.src.config import settings

logger = structlog.get_logger(__name__)

_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    """
    Get singleton Redis client instance.

    Creates connection pool on first call and reuses it.
    Configured from settings.REDIS_URL.

    Returns:
        Redis: Async Redis client instance
    """
    global _redis_pool, _redis_client

    if _redis_client is None:
        logger.info("Initializing Redis connection pool", redis_url=settings.REDIS_URL)

        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )

        _redis_client = Redis(connection_pool=_redis_pool)

        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection established")

    return _redis_client


async def get_cache(key: str) -> str | None:
    """
    Get value from Redis cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    client = await get_redis_client()
    value = await client.get(key)

    if value is not None:
        logger.debug("Cache hit", key=key)
    else:
        logger.debug("Cache miss", key=key)

    return value


async def set_cache(key: str, value: str, ttl: int | None = None) -> None:
    """
    Set value in Redis cache.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (optional)
    """
    client = await get_redis_client()

    if ttl is not None:
        await client.setex(key, ttl, value)
        logger.debug("Cache set with TTL", key=key, ttl=ttl)
    else:
        await client.set(key, value)
        logger.debug("Cache set", key=key)


async def delete_cache(key: str) -> None:
    """
    Delete key from Redis cache.

    Args:
        key: Cache key to delete
    """
    client = await get_redis_client()
    deleted = await client.delete(key)

    if deleted:
        logger.debug("Cache deleted", key=key)
    else:
        logger.debug("Cache key not found for deletion", key=key)


async def increment(key: str, amount: int = 1) -> int:
    """
    Increment integer value in Redis.

    If key does not exist, it is set to 0 before incrementing.

    Args:
        key: Cache key
        amount: Amount to increment by (default: 1)

    Returns:
        New value after increment
    """
    client = await get_redis_client()
    new_value = await client.incrby(key, amount)

    logger.debug("Cache incremented", key=key, amount=amount, new_value=new_value)

    return new_value


async def get_int(key: str) -> int | None:
    """
    Get integer value from Redis cache.

    Args:
        key: Cache key

    Returns:
        Integer value or None if not found or not a valid integer
    """
    value = await get_cache(key)

    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid integer value in cache", key=key, value=value)
        return None


async def close_redis_client() -> None:
    """
    Close Redis connection pool gracefully.

    Should be called during application shutdown to properly close connections.
    """
    global _redis_pool, _redis_client

    if _redis_client:
        logger.info("Closing Redis client")
        await _redis_client.aclose()
        _redis_client = None

    if _redis_pool:
        logger.info("Closing Redis connection pool")
        await _redis_pool.aclose()
        _redis_pool = None
