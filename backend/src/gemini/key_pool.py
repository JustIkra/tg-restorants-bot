"""
Gemini API Key Pool management.

Manages a pool of Gemini API keys with automatic rotation when rate limits
are reached. Persists usage counters in Redis for reliability across restarts.
"""

import structlog

from backend.src.cache.redis_client import get_int, get_redis_client, increment, set_cache

logger = structlog.get_logger(__name__)


class AllKeysExhaustedException(Exception):
    """Raised when all API keys in the pool are exhausted or invalid."""

    pass


class GeminiAPIKeyPool:
    """
    Manages a pool of Gemini API keys with automatic rotation.

    Features:
    - Automatic rotation when key reaches request limit (default: 195 requests)
    - Persistent usage counters in Redis (TTL: 24 hours)
    - Fallback to next key on errors
    - Usage monitoring and rotation history

    Redis Schema:
    - gemini:current_key_index → "0" (current active key index)
    - gemini:usage:{key_index} → "187" (usage count, TTL 24h)
    - gemini:invalid:{key_index} → "1" (invalid key flag)
    - gemini:rotation_log → list (rotation history for monitoring)
    """

    def __init__(self, keys: list[str], max_requests_per_key: int = 195):
        """
        Initialize API key pool.

        Args:
            keys: List of Gemini API keys
            max_requests_per_key: Maximum requests per key before rotation (default: 195)

        Raises:
            ValueError: If keys list is empty
        """
        if not keys:
            raise ValueError("API keys list cannot be empty")

        self.keys = keys
        self.max_requests = max_requests_per_key

        logger.info(
            "Gemini API key pool initialized",
            keys_count=len(keys),
            max_requests_per_key=max_requests_per_key,
        )

    async def get_api_key(self) -> str:
        """
        Get the current active API key.

        Automatically rotates to the next key if the current one has reached
        its request limit.

        Returns:
            Active API key string

        Raises:
            AllKeysExhaustedException: If all keys are exhausted or invalid
        """
        current_index = await self._get_current_key_index()
        usage_count = await self._get_usage_count(current_index)

        # Check if current key needs rotation
        if usage_count >= self.max_requests:
            logger.info(
                "Key usage limit reached, rotating",
                current_index=current_index,
                usage_count=usage_count,
                max_requests=self.max_requests,
            )
            current_index = await self._rotate_to_next_available_key()

        # Check if key is valid
        is_invalid = await self._is_key_invalid(current_index)
        if is_invalid:
            logger.warning(
                "Current key is marked invalid, rotating",
                current_index=current_index,
            )
            current_index = await self._rotate_to_next_available_key()

        # Increment usage counter
        await self._increment_usage(current_index)

        return self.keys[current_index]

    async def rotate_key(self) -> str:
        """
        Manually rotate to the next available key.

        Returns:
            New active API key

        Raises:
            AllKeysExhaustedException: If no valid keys available
        """
        new_index = await self._rotate_to_next_available_key()
        return self.keys[new_index]

    async def mark_key_invalid(self, key_index: int) -> None:
        """
        Mark a specific key as invalid.

        Args:
            key_index: Index of the key to mark as invalid
        """
        redis = await get_redis_client()
        await redis.set(f"gemini:invalid:{key_index}", "1")

        logger.warning("Key marked as invalid", key_index=key_index)

    async def get_pool_status(self) -> dict:
        """
        Get current status of the key pool.

        Returns:
            Dictionary with pool status:
            - current_key_index: Index of active key
            - usage_counts: Usage count for each key
            - invalid_keys: List of invalid key indices
        """
        current_index = await self._get_current_key_index()

        usage_counts = {}
        invalid_keys = []

        for i in range(len(self.keys)):
            usage = await self._get_usage_count(i)
            usage_counts[i] = usage

            if await self._is_key_invalid(i):
                invalid_keys.append(i)

        status = {
            "current_key_index": current_index,
            "usage_counts": usage_counts,
            "invalid_keys": invalid_keys,
            "total_keys": len(self.keys),
            "max_requests_per_key": self.max_requests,
        }

        logger.debug("Pool status retrieved", status=status)

        return status

    # Private methods

    async def _get_current_key_index(self) -> int:
        """
        Get the current active key index from Redis.

        Returns:
            Current key index (defaults to 0 if not set)
        """
        index = await get_int("gemini:current_key_index")
        return index if index is not None else 0

    async def _get_usage_count(self, key_index: int) -> int:
        """
        Get usage count for a specific key.

        Args:
            key_index: Index of the key

        Returns:
            Usage count (0 if not set)
        """
        count = await get_int(f"gemini:usage:{key_index}")
        return count if count is not None else 0

    async def _increment_usage(self, key_index: int) -> None:
        """
        Increment usage counter for a specific key.

        Sets TTL to 24 hours on first increment.

        Args:
            key_index: Index of the key
        """
        redis = await get_redis_client()
        key = f"gemini:usage:{key_index}"

        # Increment and set TTL (24 hours)
        new_count = await increment(key, 1)

        # Set TTL only if this is the first increment or TTL is not set
        ttl = await redis.ttl(key)
        if ttl == -1:  # No TTL set
            await redis.expire(key, 86400)  # 24 hours

        logger.debug(
            "Key usage incremented",
            key_index=key_index,
            new_count=new_count,
        )

    async def _rotate_to_next_available_key(self) -> int:
        """
        Rotate to the next available (not exhausted, not invalid) key.

        Returns:
            Index of the new active key

        Raises:
            AllKeysExhaustedException: If no valid keys available
        """
        current_index = await self._get_current_key_index()

        # Try each key in sequence
        for offset in range(1, len(self.keys) + 1):
            candidate_index = (current_index + offset) % len(self.keys)

            # Check if key is valid and not exhausted
            if await self._is_key_invalid(candidate_index):
                logger.debug(
                    "Skipping invalid key",
                    key_index=candidate_index,
                )
                continue

            usage = await self._get_usage_count(candidate_index)
            if usage >= self.max_requests:
                logger.debug(
                    "Skipping exhausted key",
                    key_index=candidate_index,
                    usage=usage,
                )
                continue

            # Found a valid key
            await self._set_current_key_index(candidate_index)
            await self._log_rotation(current_index, candidate_index)

            logger.info(
                "Key rotated",
                from_index=current_index,
                to_index=candidate_index,
                usage=usage,
            )

            return candidate_index

        # No valid keys found
        logger.error("All API keys exhausted or invalid")
        raise AllKeysExhaustedException(
            "All API keys have been exhausted or marked invalid. "
            "Please wait for counters to reset or add new keys."
        )

    async def _set_current_key_index(self, key_index: int) -> None:
        """
        Set the current active key index in Redis.

        Args:
            key_index: Index to set as current
        """
        await set_cache("gemini:current_key_index", str(key_index))

    async def _is_key_invalid(self, key_index: int) -> bool:
        """
        Check if a key is marked as invalid.

        Args:
            key_index: Index of the key to check

        Returns:
            True if key is invalid, False otherwise
        """
        redis = await get_redis_client()
        invalid = await redis.get(f"gemini:invalid:{key_index}")
        return invalid == "1"

    async def _log_rotation(self, from_index: int, to_index: int) -> None:
        """
        Log key rotation event to Redis for monitoring.

        Args:
            from_index: Previous key index
            to_index: New key index
        """
        from datetime import datetime, timezone

        redis = await get_redis_client()
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"{timestamp} key{from_index}->key{to_index}"

        await redis.lpush("gemini:rotation_log", log_entry)

        # Keep only last 100 rotation events
        await redis.ltrim("gemini:rotation_log", 0, 99)


# Singleton instance
_key_pool: GeminiAPIKeyPool | None = None


def get_key_pool() -> GeminiAPIKeyPool:
    """
    Get singleton instance of the Gemini API key pool.

    Initializes the pool from settings on first call.

    Returns:
        GeminiAPIKeyPool instance

    Raises:
        RuntimeError: If settings are not properly configured
    """
    global _key_pool

    if _key_pool is None:
        from backend.src.config import settings

        if not settings.gemini_keys_list:
            raise RuntimeError(
                "GEMINI_API_KEYS not configured. "
                "Please set the environment variable with comma-separated keys."
            )

        _key_pool = GeminiAPIKeyPool(
            keys=settings.gemini_keys_list,
            max_requests_per_key=settings.GEMINI_MAX_REQUESTS_PER_KEY,
        )

    return _key_pool
