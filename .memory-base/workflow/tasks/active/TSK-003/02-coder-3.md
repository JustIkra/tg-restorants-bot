---
agent: coder
task_id: TSK-003
subtask: 3
subtask_name: "Kafka Producer Setup"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/src/kafka/__init__.py
    action: created
  - path: backend/src/kafka/producer.py
    action: created
  - path: backend/src/kafka/events.py
    action: created
  - path: backend/src/config.py
    action: modified
---

# Coder Report: Kafka Producer Setup (Subtask 1.3)

## Summary

Successfully implemented Kafka producer setup for TSK-003 using FastStream library. Created event schemas, producer functions, and integrated with application configuration.

## Files Created

### 1. `backend/src/kafka/__init__.py`
- Exports key functions and schemas from the kafka module
- Provides clean public API: `get_kafka_broker()`, `publish_deadline_passed()`, `publish_daily_task()`
- Exports event schemas: `DeadlinePassedEvent`, `DailyTaskEvent`

### 2. `backend/src/kafka/events.py`
- **`DeadlinePassedEvent`**: Pydantic schema for deadline.passed events
  - Fields: `type` (fixed as "deadline.passed"), `cafe_id`, `date`, `timestamp`
  - Used when order deadline passes to trigger notifications worker

- **`DailyTaskEvent`**: Pydantic schema for scheduled daily tasks
  - Fields: `type` (task type string), `timestamp`
  - Used for batch operations like recommendations generation

### 3. `backend/src/kafka/producer.py`
- **`get_kafka_broker()`**: Singleton pattern for KafkaBroker instance
  - Lazy initialization from `settings.KAFKA_BROKER_URL`
  - Configured with FastStream's KafkaBroker
  - Logging on initialization

- **`publish_deadline_passed(cafe_id, date)`**: Publishes to `lunch-bot.deadlines` topic
  - Creates DeadlinePassedEvent
  - Publishes to Kafka using broker.publish()
  - Structured logging (info level on success, error level on failure)
  - Raises exception on failure for proper error handling

- **`publish_daily_task(task_type)`**: Publishes to `lunch-bot.daily-tasks` topic
  - Creates DailyTaskEvent with specified task type
  - Publishes to Kafka
  - Structured logging with task metadata
  - Exception handling with detailed error logs

### 4. `backend/src/config.py` (Modified)
- Added `KAFKA_BROKER_URL: str = "localhost:9092"` to Settings class
- Default value points to local Kafka instance
- Can be overridden via environment variable

## Implementation Details

### FastStream Integration
- Used `faststream.kafka.KafkaBroker` as recommended in documentation
- Broker initialized with connection string from settings
- Simple publish pattern without decorators (workers will use subscribers)

### Topics
1. **`lunch-bot.deadlines`** - for deadline.passed events
2. **`lunch-bot.daily-tasks`** - for scheduled batch tasks

### Logging Strategy
- Used Python's built-in `logging` module
- Structured logs with `extra` dict containing event metadata
- Info level for successful publishes
- Error level with `exc_info=True` for failures
- Fields logged: cafe_id, date, task_type, topic, timestamp, error

### Event Schemas (Pydantic)
Both event classes:
- Use Pydantic BaseModel for validation
- Include `timestamp` field with automatic UTC datetime
- Serialize to dict using `model_dump()` before publishing
- Field descriptions for documentation

### Error Handling
- Try-except blocks around publish operations
- Errors logged with context before re-raising
- Allows caller to handle failures appropriately

## Design Decisions

1. **Singleton Broker**: Global `_broker` instance to avoid creating multiple connections

2. **Separate Event Schemas**: Clean separation between different event types with explicit fields

3. **Topic Naming**: Prefixed with `lunch-bot.` for namespace isolation in shared Kafka clusters

4. **No Async Context Manager**: Broker lifecycle will be managed by FastStream application startup/shutdown hooks (to be implemented by workers)

5. **Python 3.13 Syntax**: Used modern type hints (`int | None` instead of `Optional[int]`)

## Dependencies

This implementation requires:
- `faststream[kafka] >= 0.6.3` (from tech stack)
- Pydantic >= 2.12.0 (already in project)

## Integration Points

### For Workers (Future Implementation)
Workers will use this producer by:
```python
from backend.src.kafka.producer import publish_deadline_passed

# After deadline detection
await publish_deadline_passed(cafe_id=123, date="2025-12-08")
```

### For API (Future Implementation)
Backend API can trigger events:
```python
from backend.src.kafka.producer import publish_daily_task

# Trigger recommendations generation
await publish_daily_task("generate_recommendations")
```

## Testing Considerations

For future Tester agent:
- Mock `KafkaBroker.publish()` method
- Verify event schema validation (valid/invalid data)
- Test error handling when Kafka is unavailable
- Verify structured logging output
- Test singleton pattern (multiple calls to `get_kafka_broker()` return same instance)

## Compliance

✅ **Code Style**: Follows code-style.md guidelines
- Python 3.13 type hints (`|` instead of `Optional`)
- Double quotes for strings
- snake_case naming
- Line length < 100 characters
- Pydantic 2.x best practices

✅ **Architecture**: Matches architect design (01-architect.md)
- FastStream Kafka integration
- Event schemas as specified
- Topic names as specified
- Producer functions with correct signatures

✅ **Boundaries**: Only touched specified files
- Did NOT modify docker-compose.yml
- Did NOT create Redis client
- Did NOT create workers

## Status

**Completed**: All requirements for Subtask 1.3 fulfilled.

## Next Steps

This producer is ready for integration with:
- Subtask 2.4: Notifications Worker (will subscribe to `lunch-bot.deadlines`)
- Subtask 3.5: Recommendations Worker (will subscribe to `lunch-bot.daily-tasks`)
- Backend API endpoints (will call `publish_deadline_passed()` after deadline detection)
