---
agent: reviewer
task_id: TSK-008
status: completed
next: tester
created_at: 2025-12-06T14:35:00Z
---

## Review Result: CHANGES_REQUESTED

### Проверено

- [x] nginx/nginx.prod.conf
- [x] backend/workers/notifications.py
- [x] backend/workers/recommendations.py

### Critical Issues

#### 1. Integration Tests Have Broken Imports

**File:** `backend/tests/integration/test_kafka_notifications.py` and `backend/tests/integration/test_kafka_recommendations.py`

**Issue:** These test files still use old import pattern `from backend.src.*` which will fail:

```python
# test_kafka_notifications.py
from backend.src.kafka.events import DeadlinePassedEvent
from backend.src.models.cafe import Cafe
from backend.src.models.order import Order

# test_kafka_recommendations.py
from backend.src.gemini import AllKeysExhaustedException
from backend.src.models.order import Order
```

**Impact:** Integration tests for Kafka workers will fail when executed.

**Recommendation:** Update test imports to match worker imports:
- `from backend.src.kafka.events` → `from src.kafka.events`
- `from backend.src.models.cafe` → `from src.models.cafe`
- `from backend.src.models.order` → `from src.models.order`
- `from backend.src.gemini` → `from src.gemini`

---

#### 2. Nginx Server Name Configuration

**File:** `nginx/nginx.prod.conf`

**Issue:** Server name is set to wildcard `server_name _;` instead of actual domain.

```nginx
server {
    listen 80;
    server_name _;  # ← Should be specific domain
```

**Security Concern:**
- Accepts requests for any hostname
- No host header validation
- Potential for host header injection attacks
- Not following security best practices

**Recommendation:** Change to specific domain:
```nginx
server {
    listen 80;
    server_name lunchbot.vibe-labs.ru;
```

This ensures nginx only responds to requests for the correct domain.

---

### Important Issues

#### 3. Worker Error Handling Could Be More Robust

**File:** `backend/workers/notifications.py`, line 333-343

**Issue:** Exception handling in `handle_deadline_passed` catches all exceptions but re-raises them, which will cause worker to crash.

```python
except Exception as e:
    logger.error(
        "Error processing deadline.passed event",
        extra={"cafe_id": event.cafe_id, "date": event.date, "error": str(e)},
        exc_info=True,
    )
    raise  # ← Worker will crash and restart
```

**Concern:** While restart loop is acceptable, consider if certain errors should be caught without crashing (e.g., database connection temporary failures).

**Recommendation:** Consider differentiating between:
- **Fatal errors** (re-raise) → invalid data, programming errors
- **Transient errors** (log and continue) → network timeouts, temporary DB issues

Current approach is acceptable but could be improved for production stability.

---

#### 4. Recommendations Worker Missing Import Error Handling

**File:** `backend/workers/recommendations.py`, line 94-101

**Issue:** ImportError fallback logs warning but continues processing, which will waste resources on users that can't be processed.

```python
except ImportError:
    logger.warning(
        "GeminiRecommendationService not available, skipping user",
        extra={"user_tgid": tgid},
    )
    error_count += 1
    continue
```

**Concern:** If `GeminiRecommendationService` is not available, this error will occur for EVERY user in the batch, creating noise in logs.

**Recommendation:** Check import availability once at startup, not in the loop:
```python
try:
    from src.gemini.client import get_recommendation_service
    recommendation_service = get_recommendation_service()
except ImportError:
    logger.error("GeminiRecommendationService not available, exiting")
    return
```

Move the import check outside the user loop.

---

#### 5. Scheduler Shutdown Sequence

**File:** `backend/workers/recommendations.py`, line 246-247

**Issue:** Scheduler shutdown happens after broker closes, but scheduler might still try to run jobs.

```python
logger.info("Recommendations worker shutting down")
if scheduler.running:
    scheduler.shutdown(wait=False)  # ← Should shutdown before broker closes
await engine.dispose()
```

**Concern:** Race condition if scheduler fires job during broker shutdown.

**Recommendation:** Shutdown scheduler before exiting broker context:
```python
async with broker:
    # ... wait for shutdown signal ...

    # Shutdown scheduler first
    if scheduler.running:
        logger.info("Shutting down scheduler")
        scheduler.shutdown(wait=False)

# Then broker closes automatically
logger.info("Recommendations worker shutting down")
await engine.dispose()
```

---

### Code Style & Quality

#### ✅ Positive Observations

1. **Import fixes are correct** - All `from backend.src.*` → `from src.*` changes align with Docker container structure
2. **Broker lifecycle properly implemented** - Signal handlers, stop event, graceful shutdown all correct
3. **Logging is comprehensive** - Good use of structured logging with `extra` fields
4. **Error handling in Telegram API** - Proper retry logic with exponential backoff
5. **Type hints present** - Good use of type annotations (Python 3.13+)
6. **Docstrings for complex functions** - Following Google style format
7. **Line length adheres to standard** - All lines under 100 characters

#### ✅ Security Headers (nginx)

Nginx configuration includes proper security headers:
- `X-Frame-Options: SAMEORIGIN` ✓
- `X-Content-Type-Options: nosniff` ✓
- `X-XSS-Protection: 1; mode=block` ✓
- `Referrer-Policy: no-referrer-when-downgrade` ✓

#### ✅ Rate Limiting Configured

- API endpoints: 10 req/s with burst 20
- General traffic: 30 req/s with burst 50

---

### Suggestions (Non-blocking)

#### 1. Add Health Check Endpoints to Workers

**Current:** Workers have no health check mechanism.

**Suggestion:** Add HTTP health check endpoint or readiness probe for Docker:
```python
# Could add simple HTTP server on different port
# Or use file-based health check: touch /tmp/worker_healthy
```

This would help docker-compose health checks verify worker status.

---

#### 2. Validate Event Schema Before Processing

**File:** `backend/workers/notifications.py`, line 241

**Current:** Event is deserialized but not validated for required fields before usage.

**Suggestion:** Add explicit validation:
```python
@broker.subscriber("lunch-bot.deadlines")
async def handle_deadline_passed(event: DeadlinePassedEvent) -> None:
    # Pydantic already validates, but add defensive check
    if not event.cafe_id or not event.date:
        logger.error("Invalid event received", extra={"event": event})
        return
    # ... continue processing
```

Though Pydantic should handle this, explicit checks improve robustness.

---

#### 3. Consider Adding Metrics/Observability

**Suggestion:** Add prometheus metrics or simple counters:
- Notifications sent (success/failure)
- Recommendations generated
- API key pool exhaustion events
- Processing time per event

This would help with production monitoring.

---

### Architecture Review

#### ✅ Nginx Configuration Aligned with Production Architecture

The removal of HTTPS server block is **correct**:
- External Nginx Proxy Manager handles SSL/TLS termination
- Internal nginx only needs HTTP on port 80
- Clean separation of concerns
- Follows reverse proxy best practices

**Architecture flow:**
```
Internet (HTTPS)
  → External Nginx Proxy Manager (SSL termination)
    → Internal nginx:80 (routing)
      → backend:8000 / frontend:3000
```

#### ✅ Worker Isolation

Workers properly isolated in Docker network:
- No external ports exposed
- Communication only via Kafka
- Database access via internal network
- Proper service discovery via Docker DNS

---

### Testing Requirements

Before marking as APPROVED, Tester agent must verify:

1. **Integration tests pass** after fixing imports
2. **Workers start successfully** and connect to Kafka
3. **Notifications sent** when deadline event published
4. **Scheduler fires** at correct time (can test with manual trigger)
5. **Graceful shutdown** works with SIGTERM
6. **Nginx routes correctly** to backend/frontend on port 80
7. **No import errors** in production Docker environment

---

## Summary

The code changes correctly fix the production deployment issues:
- ✅ Nginx SSL configuration removed (correct for architecture)
- ✅ Worker imports fixed for Docker environment
- ✅ Broker lifecycle properly implemented

However, **CHANGES_REQUESTED** due to:
1. **Critical:** Integration test imports still broken
2. **Critical:** Nginx server_name should be specific domain, not wildcard

After fixing these two issues, the code will be ready for production deployment.

---

## Files Requiring Changes

1. **backend/tests/integration/test_kafka_notifications.py**
   - Change `from backend.src.*` → `from src.*`

2. **backend/tests/integration/test_kafka_recommendations.py**
   - Change `from backend.src.*` → `from src.*`

3. **nginx/nginx.prod.conf**
   - Change `server_name _;` → `server_name lunchbot.vibe-labs.ru;`

The other suggestions are improvements but not blocking for deployment.

---

## Next Steps

1. Coder fixes the 2 critical issues above
2. Reviewer re-reviews the fixes
3. If approved → Tester runs integration tests and deployment verification
4. If tests pass → Task moves to completed
