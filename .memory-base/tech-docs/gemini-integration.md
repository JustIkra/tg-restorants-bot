# Gemini API Integration

Personalized food recommendations powered by Google Gemini AI with API key pool management.

## Overview

The system uses Google's Gemini API (via `google-genai` SDK) to generate personalized nutrition recommendations based on user order history. To handle API rate limits, we implement an API key pool with automatic rotation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Recommendations Worker                       │
│                  (Nightly Batch Job)                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│              OrderStatsService                               │
│         (Collect user statistics)                            │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│          GeminiRecommendationService                         │
│              (API client wrapper)                            │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│              GeminiAPIKeyPool                                │
│         (Key rotation & management)                          │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Redis                                      │
│   (Persistent counters & cache)                              │
│                                                              │
│   gemini:current_key_index → "0"                            │
│   gemini:usage:0 → "187"  (TTL 24h)                         │
│   gemini:usage:1 → "45"                                     │
│   gemini:invalid:2 → "1"                                    │
│   recommendations:user:123 → {...}  (TTL 24h)               │
└─────────────────────────────────────────────────────────────┘
```

## API Key Pool Management

### Why Key Pooling?

**Problem:** Gemini API free tier has rate limits:
- 195 requests per key per day
- HTTP 429 error when limit exceeded

**Solution:** Maintain a pool of API keys and rotate automatically when limits are reached.

### Implementation

**Location:** `backend/src/gemini/key_pool.py`

```python
class GeminiAPIKeyPool:
    """
    Manages a pool of Gemini API keys with automatic rotation.

    Features:
    - Automatic rotation when key reaches request limit (195 requests)
    - Persistent usage counters in Redis (TTL: 24 hours)
    - Fallback to next key on errors
    - Invalid key tracking
    """

    def __init__(self, keys: list[str], max_requests_per_key: int = 195):
        self.keys = keys
        self.max_requests = max_requests_per_key
```

### Redis Schema

```
# Current active key index
gemini:current_key_index → "0"

# Usage counters (TTL: 24 hours, auto-reset daily)
gemini:usage:0 → "187"   # Key at index 0: 187 requests used
gemini:usage:1 → "45"    # Key at index 1: 45 requests used
gemini:usage:2 → "0"     # Key at index 2: unused

# Invalid key flags (no TTL)
gemini:invalid:2 → "1"   # Key at index 2 is invalid (401 error)

# Rotation history (for monitoring)
gemini:rotation_log → ["2025-12-06T03:15:00 0→1", "2025-12-06T04:30:00 1→2"]
```

### Key Rotation Logic

```python
async def get_api_key(self) -> str:
    """
    Get current active API key with automatic rotation.

    Flow:
    1. Get current key index from Redis
    2. Check usage count
    3. If usage >= max_requests → rotate to next key
    4. Skip invalid keys
    5. Increment usage counter
    6. Return key
    """
    current_index = await self._get_current_key_index()
    usage_count = await self._get_usage_count(current_index)

    if usage_count >= self.max_requests:
        current_index = await self._rotate_key()

    await self._increment_usage(current_index)
    return self.keys[current_index]
```

### Error Handling

**HTTP 429 (Rate Limit Exceeded):**
```python
except genai_errors.APIError as e:
    if e.code == 429:
        logger.warning("Rate limit hit, rotating key")
        await key_pool._rotate_key()
        continue  # Retry with new key
```

**HTTP 401 (Invalid Key):**
```python
except genai_errors.APIError as e:
    if e.code == 401:
        logger.error("Invalid API key, skipping")
        await key_pool._mark_key_invalid(current_index)
        continue  # Try next key
```

**All Keys Exhausted:**
```python
raise AllKeysExhaustedException(
    "All API keys are exhausted or invalid. Please wait for daily reset."
)
```

## Gemini Recommendation Service

**Location:** `backend/src/gemini/client.py`

### Generation Flow

```python
async def generate_recommendations(user_stats: dict) -> dict:
    """
    Generate recommendations with retry logic.

    Process:
    1. Get API key from pool
    2. Create Gemini client
    3. Format prompt with user data
    4. Call API with timeout (30s)
    5. Parse JSON response
    6. Handle errors and retry
    """
    max_retries = len(self.key_pool.keys)

    for attempt in range(max_retries):
        try:
            api_key = await self.key_pool.get_api_key()
            client = genai.Client(api_key=api_key)

            response = await asyncio.wait_for(
                client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt
                ),
                timeout=30.0
            )

            return self._parse_response(response.text)

        except genai_errors.APIError as e:
            # Handle rate limits, invalid keys
            ...
```

### Prompt Engineering

**Location:** `backend/src/gemini/prompts.py`

```python
RECOMMENDATION_PROMPT = """
Проанализируй привычки питания пользователя и дай персональные рекомендации.

Статистика за 30 дней:
- Всего заказов: {orders_count}
- Распределение по категориям:
  * Супы: {soup_percentage}%
  * Салаты: {salad_percentage}%
  * Основные блюда: {main_percentage}%
  * Дополнительно: {extra_percentage}%
- Уникальных блюд заказано: {unique_dishes} из {total_available}
- Топ-5 любимых блюд: {favorite_dishes}

Дай краткое резюме (1 предложение) и 2-3 совета:
1. По сбалансированности питания
2. По разнообразию рациона
3. Новые блюда для пробы (из доступного меню)

Формат ответа СТРОГО JSON:
{{
    "summary": "краткое резюме привычек питания",
    "tips": ["совет 1", "совет 2", "совет 3"]
}}
"""
```

**Example User Stats Input:**
```json
{
  "orders_count": 18,
  "categories": {
    "soup": 0.35,      // 35% супов
    "salad": 0.25,     // 25% салатов
    "main": 0.30,      // 30% основных блюд
    "extra": 0.10      // 10% дополнительно
  },
  "unique_dishes": 8,
  "total_dishes_available": 45,
  "favorite_dishes": [
    {"name": "Борщ с курицей", "count": 6},
    {"name": "Салат Цезарь", "count": 5},
    {"name": "Котлета с пюре", "count": 4}
  ]
}
```

**Example Gemini Response:**
```json
{
  "summary": "80% горячего, мало овощей и разнообразия блюд",
  "tips": [
    "Попробуйте добавить салат к обеду — в меню есть Греческий и Оливье",
    "Вы заказываете одни и те же 8 блюд — попробуйте рыбные дни по средам",
    "Добавьте больше разнообразия: супы с овощами, легкие гарниры"
  ]
}
```

## Order Statistics Service

**Location:** `backend/src/services/order_stats.py`

### User Stats Collection

```python
async def get_user_stats(user_tgid: int, days: int = 30) -> dict:
    """
    Collect user order statistics for recommendation generation.

    Returns:
    {
        "orders_count": int,
        "categories": {"soup": 0.35, "salad": 0.25, ...},
        "unique_dishes": int,
        "total_dishes_available": int,
        "favorite_dishes": [{"name": str, "count": int}, ...]
    }
    """
```

**SQL Queries:**
1. Count orders in last N days
2. Aggregate by category (percentage distribution)
3. Count unique menu items ordered
4. Rank top 5 most ordered dishes
5. Count total dishes available in active cafes

### Active Users Query

```python
async def get_active_users(min_orders: int = 5, days: int = 30) -> list[int]:
    """
    Get list of active user TGIDs for batch recommendation generation.

    Criteria:
    - At least {min_orders} orders in last {days} days
    - User is active (is_active=true)
    """
```

## Caching Strategy

### Redis Keys

```
# User recommendations (TTL: 24 hours)
recommendations:user:{tgid} → JSON {
    "summary": "...",
    "tips": ["...", "..."],
    "stats": {...},
    "generated_at": "2025-12-06T03:15:00Z"
}
```

### Cache Flow

**Write (Worker):**
```python
# Generate recommendations
result = await gemini_service.generate_recommendations(user_stats)

# Cache in Redis
cache_data = {
    "summary": result["summary"],
    "tips": result["tips"],
    "stats": user_stats,
    "generated_at": datetime.now(timezone.utc).isoformat()
}

await set_cache(
    key=f"recommendations:user:{tgid}",
    value=json.dumps(cache_data),
    ttl=86400  # 24 hours
)
```

**Read (API):**
```python
# Try to get from cache
cache_key = f"recommendations:user:{tgid}"
cached = await get_cache(cache_key)

if cached:
    return json.loads(cached)
else:
    # Return empty recommendations with current stats
    return {
        "summary": None,
        "tips": [],
        "stats": await stats_service.get_user_stats(tgid),
        "generated_at": None
    }
```

## Batch Generation Workflow

**Location:** `backend/workers/recommendations.py`

### Nightly Job (03:00 AM)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    generate_recommendations_batch,
    trigger='cron',
    hour=3,
    minute=0
)

async def generate_recommendations_batch():
    """
    Batch process:
    1. Get active users (>= 5 orders in 30 days)
    2. For each user:
       - Collect stats
       - Generate via Gemini (with key rotation)
       - Cache in Redis
    3. Log progress
    """
    active_users = await stats_service.get_active_users(min_orders=5)

    for tgid in active_users:
        try:
            user_stats = await stats_service.get_user_stats(tgid)
            result = await gemini_service.generate_recommendations(user_stats)
            await cache_result(tgid, result, user_stats)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed for user {tgid}", exc_info=True)
            error_count += 1
```

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEYS=AIzaSyA...key1,AIzaSyB...key2,AIzaSyC...key3

# Optional (defaults)
GEMINI_MAX_REQUESTS_PER_KEY=195  # Daily limit per key
GEMINI_MODEL=gemini-2.0-flash-exp  # Model to use
```

### Settings Class

```python
class Settings(BaseSettings):
    GEMINI_API_KEYS: str
    GEMINI_MAX_REQUESTS_PER_KEY: int = 195
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"

    @property
    def gemini_keys_list(self) -> list[str]:
        return [k.strip() for k in self.GEMINI_API_KEYS.split(',')]
```

## Monitoring & Observability

### Metrics

**Key Pool:**
- Current active key index
- Usage count per key
- Rotation events count
- Invalid keys count

**Generation:**
- Recommendations generated (success/failure)
- Average generation time
- API errors by type (429, 401, timeout)

### Logging

```python
logger.info(
    "Recommendation generated",
    extra={
        "user_tgid": tgid,
        "key_index": current_key_index,
        "usage_count": usage_count,
        "generation_time_ms": elapsed_ms
    }
)
```

## Troubleshooting

### Common Issues

**All keys exhausted:**
- Wait for daily reset (24h TTL on counters)
- Add more API keys to pool
- Reduce batch size

**Invalid key errors:**
- Check API key validity in Google AI Studio
- Remove invalid keys from config
- Monitor `gemini:invalid:{index}` flags in Redis

**Slow generation:**
- Check Gemini API latency
- Increase timeout from 30s
- Monitor network connectivity

### Debug Commands

```bash
# Check Redis counters
redis-cli GET gemini:current_key_index
redis-cli GET gemini:usage:0
redis-cli GET gemini:usage:1

# Check cached recommendations
redis-cli GET "recommendations:user:123"

# View rotation log
redis-cli LRANGE gemini:rotation_log 0 -1
```

## References

- [Google Generative AI Python SDK](https://github.com/googleapis/python-genai)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Gemini Pricing & Limits](https://ai.google.dev/pricing)
