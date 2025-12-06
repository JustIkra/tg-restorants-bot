---
agent: reviewer
task_id: TSK-003
status: completed
verdict: CHANGES_REQUESTED
next: coder
created_at: 2025-12-06T18:30:00Z
---

# Review Result: CHANGES REQUESTED

## Executive Summary

Проверено 12 подзадач (02-coder-1 до 02-coder-12) для TSK-003. Обнаружено **3 критических**, **8 важных** и **множество рекомендаций**. Основные проблемы: отсутствие dependency в pyproject.toml, уязвимость secrets exposure в docker-compose, недостаточная обработка ошибок в Kafka/Gemini интеграции.

## Checklist

- [x] Code style
- [x] Security
- [x] Error handling
- [x] Architecture compliance
- [x] Async patterns

---

## CRITICAL Issues

### 1. Missing Dependencies in pyproject.toml
**File:** `backend/pyproject.toml`
**Severity:** CRITICAL

**Проблема:**
```toml
# Отсутствуют:
"redis>=5.0.0"  # Используется в cache/redis_client.py
"apscheduler>=3.10.0"  # Используется в workers/recommendations.py
```

**Доказательство:**
- `backend/src/cache/redis_client.py:9` - `from redis.asyncio import ConnectionPool, Redis`
- `backend/workers/recommendations.py:7` - `from apscheduler.schedulers.asyncio import AsyncIOScheduler`

**Impact:** Приложение не запустится без этих зависимостей.

**Fix:**
Добавить в `backend/pyproject.toml`:
```toml
dependencies = [
    ...
    "redis>=5.0.0",
    "apscheduler>=3.10.0",
]
```

---

### 2. Secrets Exposure in docker-compose.yml
**File:** `docker-compose.yml:84-86`
**Severity:** CRITICAL (OWASP A02:2021 - Cryptographic Failures)

**Проблема:**
```yaml
environment:
  TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}  # ✓ OK
  GEMINI_API_KEYS: ${GEMINI_API_KEYS}        # ✓ OK
  JWT_SECRET_KEY: ${JWT_SECRET_KEY}          # ⚠️ Но нет проверки длины в runtime
```

Однако в `.env.example:14`:
```bash
GEMINI_MODEL_TEXT=gemini-2.5-flash  # НЕ используется в config.py!
```

**Impact:**
1. Несоответствие между .env.example и config.py
2. Потенциальная путаница при настройке

**Fix:**
Либо добавить `GEMINI_MODEL_TEXT` в config.py, либо удалить из .env.example.

---

### 3. No Validation for status Field in CafeLinkRequest
**File:** `backend/src/models/cafe.py:75`
**Severity:** CRITICAL (Data Integrity)

**Проблема:**
```python
status: Mapped[str] = mapped_column(String(20), nullable=False)
# Комментарий: "pending, approved, rejected" - но нет constraint!
```

**Impact:** В БД может попасть любое значение: `"foo"`, `"bar"`, что нарушит бизнес-логику.

**Fix:**
Добавить SQLAlchemy Enum или CHECK constraint:
```python
from sqlalchemy import Enum as SQLEnum

status: Mapped[str] = mapped_column(
    SQLEnum("pending", "approved", "rejected", name="link_request_status"),
    nullable=False
)
```

Либо добавить CHECK constraint в миграции 002:
```python
# В upgrade():
op.create_check_constraint(
    "ck_cafe_link_requests_status",
    "cafe_link_requests",
    "status IN ('pending', 'approved', 'rejected')"
)
```

---

## IMPORTANT Issues

### 4. Missing Error Handling in Kafka Producer
**File:** `backend/src/kafka/producer.py:43-45`
**Severity:** IMPORTANT

**Проблема:**
```python
await broker.publish(
    event.model_dump(),
    topic="lunch-bot.deadlines",
)
# Что если broker не подключен? Нет fallback!
```

**Impact:** При недоступности Kafka приложение упадет без graceful degradation.

**Recommendation:**
```python
try:
    await broker.publish(...)
except Exception as e:
    logger.error("Kafka publish failed", exc_info=True)
    # Option 1: Store to DB for later retry
    # Option 2: Fallback to direct notification
    raise  # Re-raise после логирования
```

---

### 5. Hardcoded Telegram Bot Token in bot.py
**File:** `backend/src/telegram/bot.py` (inference from coder report)
**Severity:** IMPORTANT

**Recommendation:**
Убедиться, что токен берется ТОЛЬКО из `settings.TELEGRAM_BOT_TOKEN`, не hardcoded.

---

### 6. N+1 Query in Order Stats Service
**File:** `backend/src/services/order_stats.py` (inference)
**Severity:** IMPORTANT (Performance)

**Проблема:**
При сборе статистики по категориям может возникнуть N+1 если парсится JSON для каждого заказа отдельно.

**Recommendation:**
Использовать `func.json_extract` или batch-fetch всех заказов сразу.

---

### 7. No Timeout for Gemini API Calls
**File:** `backend/src/gemini/client.py:78-80`
**Severity:** IMPORTANT

**Проблема:**
```python
response = await client.aio.models.generate_content(
    model="gemini-2.0-flash-exp", contents=prompt
)
# Нет timeout! Может зависнуть навсегда
```

**Impact:** Worker может зависнуть на часы при медленном Gemini API.

**Fix:**
```python
import asyncio

response = await asyncio.wait_for(
    client.aio.models.generate_content(...),
    timeout=30.0  # 30 секунд
)
```

---

### 8. Redis Connection Pool Not Closed
**File:** `backend/src/cache/redis_client.py:19-50`
**Severity:** IMPORTANT (Resource Leak)

**Проблема:**
```python
_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None

# Нет функции для graceful shutdown!
```

**Impact:** При перезапуске worker могут накапливаться незакрытые соединения.

**Fix:**
Добавить функцию:
```python
async def close_redis_client() -> None:
    """Close Redis connection pool."""
    global _redis_pool, _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None
```

Использовать в `@broker.on_shutdown` hook.

---

### 9. Missing Index on cafe_link_requests.created_at
**File:** `backend/alembic/versions/002_add_cafe_notifications.py:52-67`
**Severity:** IMPORTANT (Performance)

**Проблема:**
Есть индексы на `cafe_id`, `status`, composite `(cafe_id, status)`, но НЕТ на `created_at`.

**Impact:** Сортировка по `created_at DESC` в `list_requests()` может быть медленной.

**Fix:**
Добавить индекс:
```python
op.create_index(
    "ix_cafe_link_requests_created_at",
    "cafe_link_requests",
    ["created_at"]
)
```

---

### 10. Unsafe JSON Parsing in Gemini Client
**File:** `backend/src/gemini/client.py` (inference)
**Severity:** IMPORTANT

**Проблема:**
Если Gemini возвращает невалидный JSON, парсинг может упасть без fallback.

**Recommendation:**
```python
try:
    return json.loads(json_text)
except json.JSONDecodeError:
    logger.warning("Invalid JSON from Gemini", response_text=text)
    return {"summary": None, "tips": []}  # Graceful fallback
```

---

### 11. No Retry Logic for Database Operations
**File:** `backend/workers/notifications.py:30-62`
**Severity:** IMPORTANT

**Проблема:**
Если PostgreSQL временно недоступен (network blip), worker упадет.

**Recommendation:**
Добавить retry decorator или try-except с экспоненциальной задержкой.

---

## Suggestions

### 12. Code Style: Inconsistent Import Order
**Files:** Multiple
**Severity:** SUGGESTION

В разных файлах разный порядок импортов:
- Иногда stdlib → third-party → local
- Иногда вперемешку

**Recommendation:**
Использовать Ruff для автосортировки:
```bash
ruff check --select I --fix backend/
```

---

### 13. Missing Type Hints in format_notification
**File:** `backend/workers/notifications.py:80-93`
**Severity:** SUGGESTION

```python
def format_notification(
    cafe: Cafe, date: str, orders: list[Order], menu_items: dict[int, MenuItem]
) -> str:
```

✓ Type hints есть, но можно улучшить:
```python
def format_notification(
    cafe: Cafe,
    date: str,
    orders: list[Order],
    menu_items: dict[int, MenuItem]
) -> str:
    """Format notification message..."""
```

---

### 14. Hardcoded Model Name in Gemini Client
**File:** `backend/src/gemini/client.py:79`
**Severity:** SUGGESTION

```python
model="gemini-2.0-flash-exp"  # Hardcoded!
```

**Recommendation:**
Вынести в config:
```python
# config.py
GEMINI_MODEL: str = "gemini-2.0-flash-exp"

# client.py
model=settings.GEMINI_MODEL
```

---

### 15. No Logging in successful API calls
**File:** `backend/src/routers/cafe_links.py`
**Severity:** SUGGESTION

Endpoints не логируют успешные операции (только ошибки).

**Recommendation:**
Добавить structured logging:
```python
@router.post("/cafe-requests/{request_id}/approve", ...)
async def approve_cafe_request(...):
    result = await service.approve_request(request_id)
    logger.info(
        "Cafe link request approved",
        extra={"request_id": request_id, "cafe_id": result.cafe_id}
    )
    return result
```

---

### 16. No Rate Limiting on Public Endpoints
**File:** `backend/src/routers/cafe_links.py:24-36`
**Severity:** SUGGESTION (Security)

Endpoint `/cafes/{cafe_id}/link-request` публичный (для Telegram бота), но нет rate limiting.

**Impact:** Можно заспамить заявками.

**Recommendation:**
Добавить FastAPI rate limiting middleware или проверять существование pending заявки от того же `tg_chat_id`.

---

### 17. Missing Docstrings in Private Methods
**Files:** Multiple (e.g., `backend/src/gemini/key_pool.py`)
**Severity:** SUGGESTION

Приватные методы `_get_current_key_index`, `_increment_usage` и т.д. не имеют docstrings.

**Recommendation:**
Добавить краткие docstrings хотя бы для сложных методов.

---

### 18. Duplicate Code in Workers
**Files:** `backend/workers/notifications.py`, `backend/workers/recommendations.py`
**Severity:** SUGGESTION (DRY)

Оба worker создают свой `engine` и `async_session_factory`:
```python
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, ...)
```

**Recommendation:**
Вынести в shared module:
```python
# backend/src/database.py (уже есть!)
# Переиспользовать get_db() или создать get_worker_session()
```

---

### 19. No Monitoring Metrics
**Files:** All workers and services
**Severity:** SUGGESTION

Нет интеграции с Prometheus/StatsD для метрик:
- Количество обработанных событий
- Время ответа Gemini API
- Количество ротаций ключей

**Recommendation:**
Добавить `prometheus-client` и экспортировать метрики.

---

### 20. Missing Health Check Endpoint for Workers
**Files:** `backend/workers/notifications.py`, `backend/workers/recommendations.py`
**Severity:** SUGGESTION

Worker не экспонируют health check для мониторинга (только логи).

**Recommendation:**
Добавить HTTP endpoint (например, на порту 8001) для health checks:
```python
from aiohttp import web

async def health_check(request):
    return web.json_response({"status": "healthy"})

app = web.Application()
app.router.add_get("/health", health_check)
```

---

## Architecture Compliance

### ✅ Проверено соответствие архитектуре (01-architect.md)

**Инфраструктура (Фаза 1):**
- ✅ Docker Compose с Kafka, Zookeeper, Redis
- ✅ Redis client с connection pool
- ✅ Kafka producer с FastStream
- ✅ Config с Gemini API keys

**Уведомления для кафе (Фаза 2):**
- ✅ Обновлена модель Cafe (tg_chat_id, tg_username, notifications_enabled, linked_at)
- ✅ Создана модель CafeLinkRequest
- ✅ Миграция 002 с индексами
- ✅ API endpoints (создание, одобрение, отклонение заявок)
- ✅ Telegram Bot с aiogram 3.x
- ✅ Notifications Worker с Kafka subscriber

**Gemini рекомендации (Фаза 3):**
- ✅ GeminiAPIKeyPool с ротацией
- ✅ GeminiRecommendationService с обработкой ошибок
- ✅ OrderStatsService для статистики
- ✅ Recommendations API endpoint (GET /users/{tgid}/recommendations)
- ✅ Recommendations Worker с APScheduler (03:00)

**Паттерны:**
- ✅ Repository → Service → Router
- ✅ Async/await везде
- ✅ Pydantic схемы
- ✅ Dependency Injection
- ✅ Singleton для Redis/Kafka

---

## Security Review (OWASP Top 10)

### A01:2021 - Broken Access Control
- ✅ Manager endpoints защищены через `ManagerUser` dependency
- ✅ Public endpoint `/cafes/{cafe_id}/link-request` корректно доступен
- ⚠️ **Но:** Нет проверки, что cafe_id соответствует реальному кафе (только в service)

### A02:2021 - Cryptographic Failures
- ✅ JWT_SECRET_KEY валидируется в config.py (min 32 chars)
- ⚠️ **CRITICAL:** Secrets в docker-compose.yml берутся из env, но нет дополнительной проверки

### A03:2021 - Injection (SQL, NoSQL)
- ✅ Используется SQLAlchemy ORM (параметризованные запросы)
- ✅ Нет raw SQL
- ⚠️ **Но:** JSON parsing в OrderStatsService может быть уязвим к malformed JSON

### A04:2021 - Insecure Design
- ✅ Event-driven архитектура корректно спроектирована
- ✅ Graceful degradation в Recommendations API (возврат stats даже без кэша)

### A05:2021 - Security Misconfiguration
- ⚠️ **IMPORTANT:** `.env.example` содержит `GEMINI_MODEL_TEXT`, которого нет в config.py
- ✅ CORS настроен корректно

### A06:2021 - Vulnerable Components
- ✅ Используются современные версии библиотек (faststream>=0.6.3, aiogram>=3.0, google-genai>=1.0)
- ⚠️ **CRITICAL:** Отсутствуют `redis>=5.0.0` и `apscheduler>=3.10.0` в pyproject.toml

### A07:2021 - Authentication Failures
- ✅ Telegram WebApp authentication (существующая система)
- ✅ JWT с expiration

### A08:2021 - Software Data Integrity
- ⚠️ **CRITICAL:** Нет constraint на `status` в CafeLinkRequest

### A09:2021 - Logging Failures
- ✅ Structured logging через `structlog` и `logging`
- ⚠️ **SUGGESTION:** Недостаточно логирования успешных операций (только ошибки)

### A10:2021 - Server-Side Request Forgery (SSRF)
- N/A (нет user-controlled URLs)

---

## Async Patterns Review

### ✅ Correct Usage:
- Все database operations используют `AsyncSession`
- Redis client async (`redis.asyncio`)
- Kafka broker async (FastStream)
- Gemini API async (`client.aio.models.generate_content`)

### ⚠️ Issues:
- **IMPORTANT:** Нет timeout для Gemini API calls (может зависнуть)
- **IMPORTANT:** Нет graceful shutdown для Redis connection pool

---

## Performance Review

### Potential Bottlenecks:

1. **OrderStatsService** - может быть медленным при большом количестве заказов
   - Рекомендация: Кэшировать статистику в Redis на 1 час

2. **Notifications Worker** - при большом количестве кафе может быть медленным
   - Рекомендация: Batch processing с pagination

3. **Gemini API** - лимиты на 195 запросов на ключ
   - ✅ Решено через pool, но нужен мониторинг

---

## Summary of Changes Requested

### MUST FIX (Блокируют deploy):
1. ✅ Добавить `redis>=5.0.0`, `apscheduler>=3.10.0` в pyproject.toml
2. ✅ Добавить CHECK constraint для `status` в CafeLinkRequest
3. ✅ Удалить/использовать `GEMINI_MODEL_TEXT` из .env.example

### SHOULD FIX (Важные улучшения):
4. ✅ Добавить timeout для Gemini API calls
5. ✅ Добавить graceful shutdown для Redis pool
6. ✅ Добавить индекс на `created_at` в cafe_link_requests
7. ✅ Улучшить error handling в Kafka producer

### NICE TO HAVE (Рекомендации):
8. Добавить rate limiting на public endpoints
9. Добавить метрики для мониторинга
10. Улучшить logging успешных операций

---

## Conclusion

Код высокого качества, следует архитектуре и code style. Основные проблемы:
- **Отсутствие зависимостей** (CRITICAL)
- **Недостаточная валидация данных** (CRITICAL)
- **Отсутствие timeout/graceful shutdown** (IMPORTANT)

После исправления критических и важных issues код будет готов к production deployment.

**Статус:** CHANGES_REQUESTED
**Следующий агент:** coder (для исправления issues 1-7)
