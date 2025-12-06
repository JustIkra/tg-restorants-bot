# Kafka Architecture

Event-driven architecture for Telegram notifications and batch job scheduling.

## Overview

The system uses Apache Kafka as a message broker for asynchronous event processing. Two main topics handle different types of events:

1. **lunch-bot.deadlines** - Deadline-passed notifications
2. **lunch-bot.daily-tasks** - Scheduled batch jobs

## Infrastructure

### Kafka Setup (Docker Compose)

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"      # External access
      - "29092:29092"    # Internal Docker network
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

**Connection:**
- External: `localhost:9092`
- Docker network: `kafka:29092`

## Topics

### 1. lunch-bot.deadlines

**Purpose:** Trigger notifications to cafes after order deadline passes

**Producer:** Backend API (scheduled job or manual trigger)

**Consumer:** Notifications Worker

**Event Schema:**
```python
class DeadlinePassedEvent(BaseModel):
    type: Literal["deadline.passed"] = "deadline.passed"
    cafe_id: int
    date: str  # YYYY-MM-DD format
    timestamp: datetime
```

**Example Event:**
```json
{
  "type": "deadline.passed",
  "cafe_id": 123,
  "date": "2025-12-08",
  "timestamp": "2025-12-07T10:00:00Z"
}
```

**Flow:**
1. Deadline passes (10:00 AM for lunch orders)
2. Backend publishes event to `lunch-bot.deadlines`
3. Notifications Worker receives event
4. Worker queries orders for cafe + date
5. Worker formats message and sends via Telegram Bot

### 2. lunch-bot.daily-tasks

**Purpose:** Trigger scheduled batch operations

**Producer:** External scheduler or APScheduler in worker

**Consumer:** Recommendations Worker

**Event Schema:**
```python
class DailyTaskEvent(BaseModel):
    type: str  # e.g., "generate_recommendations"
    timestamp: datetime
```

**Example Event:**
```json
{
  "type": "generate_recommendations",
  "timestamp": "2025-12-06T03:00:00Z"
}
```

**Flow:**
1. APScheduler triggers at 03:00 AM daily
2. Publishes event to `lunch-bot.daily-tasks` (optional, currently uses direct scheduler)
3. Worker starts batch recommendation generation
4. Worker processes active users sequentially
5. Results cached in Redis

## Workers

### Notifications Worker

**Location:** `backend/workers/notifications.py`

**Purpose:** Send aggregated order notifications to cafes via Telegram

**Kafka Configuration:**
```python
broker = KafkaBroker(settings.KAFKA_BROKER_URL)

@broker.subscriber("lunch-bot.deadlines")
async def handle_deadline_passed(event: dict):
    # Process deadline passed event
    ...
```

**Process:**
1. Receive `deadline.passed` event
2. Query orders from PostgreSQL for cafe + date
3. Format notification message (Markdown)
4. Send via Telegram Bot API
5. Log success/failure

**Message Format:**
```
📋 Столовая №1 — Заказ на 2025-12-08
━━━━━━━━━━━━━━━━━━━━━

👤 Иван Петров:
  • Салат + Суп + Основное блюдо (550₽)
    - Салат с курицей (салат)
    - Борщ с курицей (суп)
    - Котлета с пюре (основное)
  • Фокачча с пряным маслом ×1 (50₽)
  📝 Доставить к 12:30

━━━━━━━━━━━━━━━━━━━━━
Итого: 15 заказов, 8750₽
```

**Error Handling:**
- Network errors → retry with exponential backoff
- Telegram rate limits → throttle (30 msg/sec)
- Failed notifications → log to PostgreSQL

### Recommendations Worker

**Location:** `backend/workers/recommendations.py`

**Purpose:** Generate AI-powered food recommendations using Gemini API

**Scheduling:** APScheduler (runs at 03:00 AM daily)

**Configuration:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    generate_recommendations_batch,
    trigger='cron',
    hour=3,
    minute=0
)
```

**Batch Process:**
1. Query active users (>= 5 orders in last 30 days)
2. For each user:
   - Collect order statistics
   - Generate recommendations via Gemini API
   - Cache in Redis (TTL: 24 hours)
3. Log progress and errors

**Gemini API Integration:**
- Uses API key pool with automatic rotation
- Handles rate limits (429) → switch to next key
- Handles invalid keys (401) → skip key
- Exponential backoff on network errors

## Event Publishing

### From Backend API

**Producer Setup:**
```python
from kafka.producer import publish_deadline_passed

# After deadline check
if datetime.now() > deadline:
    await publish_deadline_passed(cafe_id=123, date="2025-12-08")
```

**Implementation:** `backend/src/kafka/producer.py`

## Monitoring

### Metrics to Track

**Kafka:**
- Events published per topic
- Consumer lag
- Failed event count

**Workers:**
- Processing time per event
- Success/failure rate
- Retry count

**Redis:**
- Cache hit/miss ratio
- Memory usage
- Key expiration rate

### Logging

Structured logs with JSON format:

```python
logger.info(
    "Notification sent",
    extra={
        "cafe_id": 123,
        "date": "2025-12-08",
        "orders_count": 15,
        "telegram_chat_id": 456789
    }
)
```

## Configuration

### Environment Variables

```bash
# Kafka
KAFKA_BROKER_URL=localhost:9092  # or kafka:29092 for Docker

# Workers need both Kafka and database access
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEYS=key1,key2,key3
```

## Scaling Considerations

### Horizontal Scaling

**Workers:**
- Run multiple instances of each worker
- Kafka automatically balances partitions
- Use consumer groups for fault tolerance

**Kafka:**
- Increase topic partitions for parallelism
- Add more brokers for high availability

### Performance

**Throughput:**
- Notifications: ~30 messages/sec (Telegram limit)
- Recommendations: Limited by Gemini API (195 req/key/day)

**Latency:**
- Deadline notifications: < 1 minute after event
- Recommendations: Batch processing overnight

## Troubleshooting

### Common Issues

**Workers not receiving events:**
- Check Kafka connection
- Verify topic names match
- Check consumer group status

**Notification delivery failures:**
- Check Telegram Bot token
- Verify cafe Telegram link
- Review rate limiting logs

**Recommendation generation errors:**
- Check Gemini API key pool
- Verify Redis connectivity
- Review key rotation logs

### Debug Commands

```bash
# List topics
kafka-topics --list --bootstrap-server localhost:9092

# Consume events (debug)
kafka-console-consumer --topic lunch-bot.deadlines \
  --bootstrap-server localhost:9092 --from-beginning

# Check consumer groups
kafka-consumer-groups --list --bootstrap-server localhost:9092
```

## References

- [FastStream Documentation](https://faststream.airt.ai/)
- [Confluent Kafka Docker](https://docs.confluent.io/platform/current/installation/docker/image-reference.html)
- [Telegram Bot API Rate Limits](https://core.telegram.org/bots/faq#broadcasting-to-users)
