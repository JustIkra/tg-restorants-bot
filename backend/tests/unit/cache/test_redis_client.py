"""Unit tests for Redis client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.cache import redis_client


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return AsyncMock()


@pytest.fixture
def mock_connection_pool():
    """Mock Redis connection pool."""
    return MagicMock()


@pytest.fixture(autouse=True)
def reset_redis_client():
    """Reset global Redis client before each test."""
    redis_client._redis_client = None
    redis_client._redis_pool = None
    yield
    redis_client._redis_client = None
    redis_client._redis_pool = None


async def test_set_and_get_cache(mock_redis, mock_connection_pool):
    """Test setting and getting cache values."""
    with patch("src.cache.redis_client.ConnectionPool") as pool_mock:
        pool_mock.from_url.return_value = mock_connection_pool
        with patch("src.cache.redis_client.Redis") as redis_mock:
            redis_mock.return_value = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.get.return_value = "test_value"
            mock_redis.set.return_value = True

            # Set cache
            await redis_client.set_cache("test_key", "test_value")
            mock_redis.set.assert_called_once_with("test_key", "test_value")

            # Get cache
            value = await redis_client.get_cache("test_key")
            assert value == "test_value"
            mock_redis.get.assert_called_once_with("test_key")


async def test_set_cache_with_ttl(mock_redis, mock_connection_pool):
    """Test setting cache with TTL."""
    with patch("src.cache.redis_client.ConnectionPool") as pool_mock:
        pool_mock.from_url.return_value = mock_connection_pool
        with patch("src.cache.redis_client.Redis") as redis_mock:
            redis_mock.return_value = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.setex.return_value = True

            await redis_client.set_cache("test_key", "test_value", ttl=3600)

            mock_redis.setex.assert_called_once_with("test_key", 3600, "test_value")


async def test_increment(mock_redis, mock_connection_pool):
    """Test incrementing a value."""
    with patch("src.cache.redis_client.ConnectionPool") as pool_mock:
        pool_mock.from_url.return_value = mock_connection_pool
        with patch("src.cache.redis_client.Redis") as redis_mock:
            redis_mock.return_value = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.incrby.return_value = 5

            result = await redis_client.increment("counter", 5)

            assert result == 5
            mock_redis.incrby.assert_called_once_with("counter", 5)


async def test_get_int(mock_redis, mock_connection_pool):
    """Test getting integer value from cache."""
    with patch("src.cache.redis_client.ConnectionPool") as pool_mock:
        pool_mock.from_url.return_value = mock_connection_pool
        with patch("src.cache.redis_client.Redis") as redis_mock:
            redis_mock.return_value = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.get.return_value = "42"

            result = await redis_client.get_int("test_key")

            assert result == 42


async def test_get_int_returns_none_for_invalid_value(mock_redis, mock_connection_pool):
    """Test that get_int returns None for invalid integer values."""
    with patch("src.cache.redis_client.ConnectionPool") as pool_mock:
        pool_mock.from_url.return_value = mock_connection_pool
        with patch("src.cache.redis_client.Redis") as redis_mock:
            redis_mock.return_value = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.get.return_value = "not_an_int"

            result = await redis_client.get_int("test_key")

            assert result is None


async def test_get_int_returns_none_for_missing_key(mock_redis, mock_connection_pool):
    """Test that get_int returns None for missing keys."""
    with patch("src.cache.redis_client.ConnectionPool") as pool_mock:
        pool_mock.from_url.return_value = mock_connection_pool
        with patch("src.cache.redis_client.Redis") as redis_mock:
            redis_mock.return_value = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.get.return_value = None

            result = await redis_client.get_int("missing_key")

            assert result is None


async def test_delete_cache(mock_redis, mock_connection_pool):
    """Test deleting cache key."""
    with patch("src.cache.redis_client.ConnectionPool") as pool_mock:
        pool_mock.from_url.return_value = mock_connection_pool
        with patch("src.cache.redis_client.Redis") as redis_mock:
            redis_mock.return_value = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.delete.return_value = 1  # 1 key deleted

            await redis_client.delete_cache("test_key")

            mock_redis.delete.assert_called_once_with("test_key")


async def test_close_redis_client(mock_redis, mock_connection_pool):
    """Test closing Redis client gracefully."""
    with patch("src.cache.redis_client.ConnectionPool") as pool_mock:
        pool_mock.from_url.return_value = mock_connection_pool
        with patch("src.cache.redis_client.Redis") as redis_mock:
            redis_mock.return_value = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.aclose = AsyncMock()
            mock_connection_pool.aclose = AsyncMock()

            # Initialize client
            await redis_client.get_redis_client()

            # Close client
            await redis_client.close_redis_client()

            mock_redis.aclose.assert_called_once()
            mock_connection_pool.aclose.assert_called_once()

            # Verify globals are reset
            assert redis_client._redis_client is None
            assert redis_client._redis_pool is None
