"""
Redis caching module for lunch bot.

Provides async Redis client wrapper with common caching operations.
"""

from .redis_client import (
    close_redis_client,
    delete_cache,
    get_cache,
    get_int,
    get_redis_client,
    increment,
    set_cache,
)

__all__ = [
    "get_redis_client",
    "get_cache",
    "set_cache",
    "delete_cache",
    "increment",
    "get_int",
    "close_redis_client",
]
