---
agent: coder
task_id: TSK-003
subtask: 12
subtask_name: "Recommendations Worker"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/workers/recommendations.py
    action: created
---

# Coder Report: TSK-003 Subtask 12 - Recommendations Worker

## Implementation Summary

Successfully created `backend/workers/recommendations.py` - a Kafka worker that performs batch generation of Gemini-based food recommendations for active users.

## Files Created

### `backend/workers/recommendations.py`

Kafka worker with the following features:

1. **Scheduled Batch Job (APScheduler)**
   - Runs daily at 03:00 AM
   - Automatically generates recommendations for all active users
   - Configured via `@broker.on_startup` hook

2. **Batch Generation Logic (`generate_recommendations_batch`)**
   - Fetches active users with >= 5 orders in last 30 days
   - For each user:
     - Collects order statistics via `OrderStatsService`
     - Sends to Gemini API (via `GeminiRecommendationService`)
     - Caches result in Redis with 24h TTL
   - Comprehensive error handling:
     - `AllKeysExhaustedException` → stops batch immediately
     - Individual user errors → logged, batch continues
   - Progress logging with success/error counts

3. **Alternative Kafka Trigger**
   - Listens to `lunch-bot.daily-tasks` topic
   - Allows manual triggering via Kafka event
   - Event format: `{"type": "generate_recommendations"}`

4. **Database Session Management**
   - Uses async context manager pattern
   - Follows same structure as `notifications.py`
   - Proper session cleanup

5. **Graceful Shutdown**
   - Stops scheduler
   - Disposes database engine
   - Clean resource cleanup

## Key Implementation Details

### APScheduler Configuration
```python
scheduler.add_job(
    generate_recommendations_batch,
    trigger="cron",
    hour=3,
    minute=0,
    id="daily_recommendations",
    replace_existing=True,
)
```

### Redis Caching
- Key format: `recommendations:user:{tgid}`
- TTL: 86400 seconds (24 hours)
- Data structure:
  ```json
  {
    "summary": "80% горячего, мало овощей",
    "tips": ["Добавь салат", "Попробуй рыбу"],
    "generated_at": "2025-12-06T03:15:00Z"
  }
  ```

### Error Handling Strategy
1. **AllKeysExhaustedException**: Critical error, stops entire batch
   - Logs processed count, success/error counts
   - Prevents wasting resources when API quota exhausted

2. **Individual User Errors**: Non-critical, batch continues
   - Logs error with user_tgid
   - Increments error_count
   - Other users still processed

3. **Import Error**: Graceful degradation
   - If `GeminiRecommendationService` not available yet (subtask 3.2)
   - Logs warning and skips user
   - Allows worker to run even if dependency incomplete

### Logging
Structured logging with context:
```python
logger.info(
    "Generated recommendations for user",
    extra={
        "user_tgid": tgid,
        "summary_length": len(recommendations.get("summary", "")),
        "tips_count": len(recommendations.get("tips", [])),
    },
)
```

## Dependencies

### External Services
- **Kafka**: Event broker for manual triggering
- **Redis**: Cache storage (via `redis_client.py`)
- **PostgreSQL**: User order data (via `OrderStatsService`)
- **Gemini API**: Recommendation generation (via `client.py` - subtask 3.2)

### Python Packages
- `faststream[kafka]` - Kafka integration
- `apscheduler` - Scheduled jobs
- `sqlalchemy` - Database ORM
- `redis.asyncio` - Redis client

### Internal Modules
- `backend.src.config.settings` - Configuration
- `backend.src.cache.redis_client` - Redis operations
- `backend.src.gemini.get_key_pool` - API key management
- `backend.src.gemini.AllKeysExhaustedException` - Exception handling
- `backend.src.services.order_stats.OrderStatsService` - Statistics collection
- `backend.src.gemini.client.get_recommendation_service` - Gemini client (NOT YET IMPLEMENTED)

## Integration Notes

### Dependency on Subtask 3.2
This worker expects `backend/src/gemini/client.py` to exist with:
```python
class GeminiRecommendationService:
    async def generate_recommendations(self, user_stats: dict) -> dict:
        """
        Returns:
            {
                "summary": str | None,
                "tips": list[str]
            }
        """
```

Current implementation has fallback for missing client:
- Catches `ImportError`
- Logs warning
- Skips user gracefully

Once subtask 3.2 is completed, remove the try/except fallback.

### Manual Triggering
To manually trigger batch generation via Kafka:
```bash
# Using kafka-console-producer
echo '{"type": "generate_recommendations"}' | kafka-console-producer \
  --broker-list localhost:9092 \
  --topic lunch-bot.daily-tasks
```

Or programmatically via FastStream producer.

## Testing Recommendations

### Unit Tests (for Tester)
- `test_generate_recommendations_batch` - mock all dependencies
- `test_handle_daily_task` - verify Kafka event handling
- `test_all_keys_exhausted` - verify batch stops correctly
- `test_individual_user_error` - verify batch continues

### Integration Tests
- End-to-end batch with real Redis
- Verify cache TTL
- Verify statistics collection

### Manual Testing
1. Set up environment:
   ```bash
   export KAFKA_BROKER_URL=localhost:9092
   export REDIS_URL=redis://localhost:6379
   export DATABASE_URL=postgresql+asyncpg://...
   export GEMINI_API_KEYS=key1,key2
   ```

2. Run worker:
   ```bash
   python -m backend.workers.recommendations
   ```

3. Trigger manually via Kafka event

4. Check Redis:
   ```bash
   redis-cli GET "recommendations:user:123456789"
   ```

## Code Style Compliance

- ✅ Python 3.13 type hints (builtin generics)
- ✅ Async/await throughout
- ✅ Structured logging with `extra` fields
- ✅ Google-style docstrings for complex logic
- ✅ Line length < 100 chars
- ✅ Proper error handling with specific exceptions
- ✅ Following patterns from `notifications.py`

## Blockers / Notes

**BLOCKER**: This worker depends on `backend/src/gemini/client.py` (subtask 3.2) which doesn't exist yet.

**Current State**: Worker has graceful fallback for missing client:
- Catches `ImportError`
- Logs warning
- Continues without crashing

**Next Steps**:
1. Wait for subtask 3.2 (Gemini Client) to be completed
2. Once client exists, remove the try/except ImportError block
3. Test full integration with real Gemini API

## Status

**Status**: `completed` (with dependency note)

The worker is fully implemented and follows all architectural requirements. It's ready to be integrated once the Gemini client (subtask 3.2) is available.

## Next Agent

No specific next agent required for this subtask. This completes subtask 3.5.

However, the overall TSK-003 pipeline continues with other subtasks as per the architect plan.
