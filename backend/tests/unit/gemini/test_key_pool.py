"""Unit tests for Gemini API Key Pool."""

import pytest
from unittest.mock import AsyncMock, patch

from src.gemini.key_pool import AllKeysExhaustedException, GeminiAPIKeyPool


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch("src.gemini.key_pool.get_redis_client") as mock:
        redis_mock = AsyncMock()
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture
def mock_get_int():
    """Mock get_int function."""
    with patch("src.gemini.key_pool.get_int") as mock:
        yield mock


@pytest.fixture
def mock_increment():
    """Mock increment function."""
    with patch("src.gemini.key_pool.increment") as mock:
        yield mock


@pytest.fixture
def mock_set_cache():
    """Mock set_cache function."""
    with patch("src.gemini.key_pool.set_cache") as mock:
        yield mock


@pytest.fixture
def key_pool():
    """Create a key pool with test keys."""
    return GeminiAPIKeyPool(
        keys=["test_key_1", "test_key_2", "test_key_3"],
        max_requests_per_key=195,
    )


async def test_get_api_key_returns_key(key_pool, mock_redis, mock_get_int, mock_increment):
    """Test that get_api_key returns a valid key."""
    # Setup mocks
    mock_get_int.side_effect = [0, 50]  # current_index=0, usage_count=50
    mock_redis.get.return_value = None  # key is not invalid
    mock_increment.return_value = 51

    key = await key_pool.get_api_key()

    assert key == "test_key_1"
    mock_increment.assert_called_once()


async def test_rotate_key_switches_to_next(
    key_pool, mock_redis, mock_get_int, mock_set_cache
):
    """Test that rotate_key switches to the next available key."""
    # Current index is 0, next is 1
    mock_get_int.side_effect = [0, 10]  # current_index=0, usage_count=10
    mock_redis.get.return_value = None  # key is not invalid

    new_key = await key_pool.rotate_key()

    assert new_key == "test_key_2"
    mock_set_cache.assert_called_once_with("gemini:current_key_index", "1")


async def test_all_keys_exhausted_raises_exception(
    key_pool, mock_redis, mock_get_int
):
    """Test that AllKeysExhaustedException is raised when all keys are exhausted."""
    # Current index is 0, all keys have usage >= 195
    mock_get_int.side_effect = [
        0,          # current_index
        195,        # key 0 usage
        195,        # key 1 usage
        195,        # key 2 usage
    ]
    mock_redis.get.return_value = None  # no keys are invalid

    with pytest.raises(AllKeysExhaustedException):
        await key_pool.rotate_key()


async def test_mark_key_invalid(key_pool, mock_redis):
    """Test marking a key as invalid."""
    await key_pool.mark_key_invalid(1)

    mock_redis.set.assert_called_once_with("gemini:invalid:1", "1")


async def test_get_api_key_rotates_when_limit_reached(
    key_pool, mock_redis, mock_get_int, mock_increment, mock_set_cache
):
    """Test that get_api_key automatically rotates when usage limit is reached."""
    # Current key has 195 requests (limit reached), should rotate to next
    mock_get_int.side_effect = [
        0,      # current_index (initial)
        195,    # usage_count (limit reached, triggers rotation)
        0,      # current_index (for rotation)
        10,     # usage for next key (key 1) - available
    ]
    mock_redis.get.return_value = None  # no keys are invalid
    mock_increment.return_value = 11

    key = await key_pool.get_api_key()

    # Should have rotated to key 2 (index 1)
    assert key == "test_key_2"
    # Check that set_cache was called to update the index
    assert any(call[0][0] == "gemini:current_key_index" and call[0][1] == "1"
               for call in mock_set_cache.call_args_list)


async def test_get_api_key_skips_invalid_keys(
    key_pool, mock_redis, mock_get_int, mock_increment, mock_set_cache
):
    """Test that get_api_key skips keys marked as invalid."""
    # Current key (0) is marked invalid, should rotate to next
    mock_get_int.side_effect = [
        0,      # current_index (initial)
        50,     # usage_count (not at limit)
        0,      # current_index (for rotation when invalid)
        10,     # usage for next valid key (key 1)
    ]
    # First call: key 0 is invalid, second call: key 1 is invalid, third call: key 2 is valid
    mock_redis.get.side_effect = ["1", "1", None, None]
    mock_increment.return_value = 11

    key = await key_pool.get_api_key()

    # Should have rotated to key 3 (index 2) (skipping invalid keys 0 and 1)
    assert key == "test_key_3"


async def test_get_pool_status(key_pool, mock_redis, mock_get_int):
    """Test getting pool status."""
    mock_get_int.side_effect = [
        0,      # current_index
        50,     # usage key 0
        100,    # usage key 1
        10,     # usage key 2
    ]
    mock_redis.get.side_effect = [None, "1", None]  # key 1 is invalid

    status = await key_pool.get_pool_status()

    assert status["current_key_index"] == 0
    assert status["total_keys"] == 3
    assert status["max_requests_per_key"] == 195
    assert status["usage_counts"] == {0: 50, 1: 100, 2: 10}
    assert status["invalid_keys"] == [1]


def test_key_pool_requires_non_empty_keys():
    """Test that GeminiAPIKeyPool raises ValueError with empty keys."""
    with pytest.raises(ValueError, match="API keys list cannot be empty"):
        GeminiAPIKeyPool(keys=[])
