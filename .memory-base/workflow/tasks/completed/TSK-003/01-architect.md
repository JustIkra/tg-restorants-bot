---
agent: architect
task_id: TSK-003
status: completed
next: coder
created_at: 2025-12-06T14:30:00Z
---

# Architectural Design: TSK-003
## Уведомления для кафе через Telegram и Gemini рекомендации

## Обзор

Эта задача добавляет две важные функции в систему:

1. **Уведомления для кафе через Telegram** - автоматическая отправка агрегированных заказов после дедлайна
2. **Умные рекомендации через Gemini API** - персональные советы по питанию на основе истории заказов

Обе функции используют event-driven архитектуру на базе Kafka и кэширование в Redis.

## Архитектурное решение

### Общая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    EXISTING COMPONENTS                       │
├─────────────────────────────────────────────────────────────┤
│ FastAPI Backend │ PostgreSQL │ Telegram Mini App             │
└────────┬────────────────┬───────────────────────────────────┘
         │                │
         ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                     NEW COMPONENTS                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐     │
│  │  Kafka   │◄────────│  Redis   │────────►│ Telegram │     │
│  │  Broker  │         │  Cache   │         │   Bot    │     │
│  └────┬─────┘         └────┬─────┘         └──────────┘     │
│       │                    │                                 │
│       ▼                    ▼                                 │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │ Notifications│    │Recommendations│                       │
│  │   Worker     │    │    Worker     │                       │
│  └──────┬───────┘    └──────┬───────┘                       │
│         │                    │                               │
│         │                    ▼                               │
│         │            ┌──────────────┐                        │
│         └───────────►│ Gemini API   │                        │
│                      │  Key Pool    │                        │
│                      └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Технологический стек (дополнения)

**Новые зависимости:**
- `faststream[kafka] >= 0.6.3` - Kafka integration для event-driven архитектуры
- `redis >= 5.0` - Кэширование рекомендаций и счетчиков API ключей
- `aiogram >= 3.0` - Telegram Bot API (современная async библиотека)
- `google-genai >= 1.0` - Google Generative AI Python SDK для Gemini API

**Инфраструктура:**
- Kafka (event broker)
- Redis (cache + key usage counters)
- Telegram Bot (для уведомлений кафе)

---

## 1. Уведомления для кафе через Telegram

### 1.1 Изменения в структуре данных

#### Обновление модели `Cafe`

**Файл:** `backend/src/models/cafe.py`

Добавить новые поля:
```python
tg_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
tg_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

#### Новая модель `CafeLinkRequest`

**Файл:** `backend/src/models/cafe.py`

```python
class CafeLinkRequest(Base, TimestampMixin):
    __tablename__ = "cafe_link_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"), nullable=False)
    tg_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tg_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, approved, rejected
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    cafe: Mapped["Cafe"] = relationship("Cafe")
```

#### Миграция Alembic

**Файл:** `backend/alembic/versions/002_add_cafe_notifications.py`

Новая миграция для:
- Добавления полей в таблицу `cafes`
- Создания таблицы `cafe_link_requests`

### 1.2 API Endpoints

**Файл:** `backend/src/routers/cafe_links.py` (новый)

```python
POST /api/v1/cafes/{cafe_id}/link-request
  - Auth: public (через Telegram бота)
  - Создание заявки на привязку кафе к Telegram

GET /api/v1/cafe-requests
  - Auth: manager
  - Список заявок на привязку

POST /api/v1/cafe-requests/{request_id}/approve
  - Auth: manager
  - Одобрение заявки

POST /api/v1/cafe-requests/{request_id}/reject
  - Auth: manager
  - Отклонение заявки

PATCH /api/v1/cafes/{cafe_id}/notifications
  - Auth: manager
  - Включение/выключение уведомлений

DELETE /api/v1/cafes/{cafe_id}/link
  - Auth: manager
  - Отвязка Telegram от кафе
```

**Файлы для создания:**
- `backend/src/routers/cafe_links.py` - роутер
- `backend/src/services/cafe_link.py` - бизнес-логика
- `backend/src/repositories/cafe_link.py` - работа с БД
- `backend/src/schemas/cafe_link.py` - Pydantic схемы

### 1.3 Telegram Bot

**Файл:** `backend/src/telegram/bot.py` (новый модуль)

Функциональность:
- Прием команд от представителей кафе
- Создание заявок через API
- Отправка уведомлений с форматированными заказами

Технология: **aiogram 3.x** (современный async фреймворк)

### 1.4 Kafka Event System

#### Event Producer

**Файл:** `backend/src/kafka/producer.py` (новый)

После наступления дедлайна заказа генерируется событие:
```python
event = {
    "type": "deadline.passed",
    "cafe_id": 123,
    "date": "2025-12-08"
}
```

Публикуется в топик: `lunch-bot.deadlines`

#### Notifications Worker

**Файл:** `backend/workers/notifications.py` (новый)

```python
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")

@broker.subscriber("lunch-bot.deadlines")
async def handle_deadline_passed(event: dict):
    """
    1. Получить заказы для cafe_id и date
    2. Если заказов нет - пропустить
    3. Сформировать сообщение
    4. Отправить через Telegram Bot API
    5. Залогировать результат
    """
    pass
```

**Формат уведомления:**
```
📋 {Cafe.name} — Заказ на {date}
━━━━━━━━━━━━━━━━━━━━━

👤 {User.name}:
   • {Combo.name}
     - {MenuItem.name} (категория)
     - {MenuItem.name} (категория)
   • {Extra.name} ×{quantity}
   📝 {notes}

━━━━━━━━━━━━━━━━━━━━━
Итого: {total_orders} заказов, {total_amount} ₽
```

---

## 2. Gemini рекомендации

### 2.1 Redis Кэширование

**Структура ключей:**
```
recommendations:user:{tgid}          # TTL 24h - рекомендации
gemini:current_key                   # текущий активный ключ
gemini:usage:key:{key_hash}          # счетчик использований (TTL 24h)
gemini:rotation_log                  # история ротаций (для мониторинга)
```

**Файл:** `backend/src/cache/redis_client.py` (новый)

Async Redis клиент на базе `redis.asyncio`

### 2.2 Gemini API Key Pool

**Файл:** `backend/src/gemini/key_pool.py` (новый)

```python
class GeminiAPIKeyPool:
    """
    Управление пулом API ключей для Gemini API.

    Особенности:
    - Автоматическая ротация при достижении лимита (195 запросов)
    - Персистентность счетчиков в Redis
    - Fallback на следующий ключ при ошибках
    - Мониторинг использования
    """

    def __init__(
        self,
        keys: list[str],
        redis_client: Redis,
        max_requests_per_key: int = 195
    ):
        self.keys = keys
        self.redis = redis_client
        self.max_requests = max_requests_per_key

    async def get_client(self) -> genai.Client:
        """
        Возвращает Gemini client с активным ключом.
        Автоматически ротирует при достижении лимита.
        """
        pass

    async def _get_current_key(self) -> str:
        """Получить текущий активный ключ из Redis."""
        pass

    async def _get_usage_count(self, key: str) -> int:
        """Получить количество использований ключа."""
        pass

    async def _increment_usage(self, key: str) -> None:
        """Увеличить счетчик использований."""
        pass

    async def _rotate_key(self) -> str:
        """Переключить на следующий доступный ключ."""
        pass

    async def _mark_key_invalid(self, key: str) -> None:
        """Отметить ключ как недействительный."""
        pass
```

### 2.3 Gemini API Integration

**Файл:** `backend/src/gemini/client.py` (новый)

```python
class GeminiRecommendationService:
    """
    Сервис для генерации рекомендаций через Gemini API.

    Обработка ошибок:
    - 429 (Rate Limit) → автоматическая ротация ключа
    - 401 (Invalid Key) → пропуск ключа, переход к следующему
    - Network errors → retry с экспоненциальной задержкой
    """

    def __init__(self, key_pool: GeminiAPIKeyPool):
        self.key_pool = key_pool

    async def generate_recommendations(
        self,
        user_stats: dict
    ) -> dict:
        """
        Генерация рекомендаций с обработкой ошибок.

        Retry логика:
        - Максимум попыток = количество ключей в пуле
        - При каждой ошибке 429/401 - ротация на следующий ключ
        - При исчерпании всех ключей - raise Exception
        """
        pass
```

**Промпт для Gemini:**
```python
RECOMMENDATION_PROMPT = """
Проанализируй привычки питания пользователя и дай персональные рекомендации.

Статистика за 30 дней:
- Всего заказов: {orders_count}
- Распределение по категориям: {categories}
- Уникальных блюд: {unique_dishes} из {total_available}

Дай краткое резюме (1 предложение) и 2-3 совета:
1. По сбалансированности питания
2. По разнообразию рациона
3. Новые блюда для пробы (из меню)

Формат ответа JSON:
{{
    "summary": "краткое резюме",
    "tips": ["совет 1", "совет 2", "совет 3"]
}}
"""
```

### 2.4 API Endpoint

**Файл:** `backend/src/routers/recommendations.py` (новый)

```python
GET /api/v1/users/{tgid}/recommendations
  - Auth: manager | self
  - Возвращает кэшированные рекомендации из Redis
  - Если кэш пуст - возвращает пустой ответ
```

**Схема ответа:**
```python
class RecommendationsResponse(BaseModel):
    summary: str | None
    tips: list[str]
    stats: OrderStats
    generated_at: datetime | None

class OrderStats(BaseModel):
    orders_last_30_days: int
    categories: dict[str, float]  # процентное распределение
    unique_dishes: int
```

### 2.5 Kafka Worker для Рекомендаций

**Файл:** `backend/workers/recommendations.py` (новый)

```python
from faststream.kafka import KafkaBroker
from apscheduler.schedulers.asyncio import AsyncIOScheduler

broker = KafkaBroker("localhost:9092")

@broker.on_startup
async def setup_scheduler():
    """
    Настройка планировщика для ночной генерации рекомендаций.
    Запуск: каждый день в 03:00
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        generate_recommendations_batch,
        trigger='cron',
        hour=3,
        minute=0
    )
    scheduler.start()

async def generate_recommendations_batch():
    """
    Batch-генерация рекомендаций:
    1. Получить активных пользователей с >= 5 заказами за 30 дней
    2. Для каждого:
       - Собрать статистику заказов
       - Отправить в Gemini API (через key pool)
       - Сохранить в Redis с TTL 24h
    3. Логирование прогресса и ошибок
    """
    pass
```

Альтернативный подход: использовать Kafka как триггер
```python
@broker.subscriber("lunch-bot.daily-tasks")
async def handle_daily_task(task: dict):
    """
    Слушает событие от внешнего cron job.
    """
    if task["type"] == "generate_recommendations":
        await generate_recommendations_batch()
```

### 2.6 Сервис статистики заказов

**Файл:** `backend/src/services/order_stats.py` (новый)

```python
class OrderStatsService:
    """
    Сбор и анализ статистики заказов для рекомендаций.
    """

    async def get_user_stats(self, user_tgid: int, days: int = 30) -> dict:
        """
        Собирает статистику:
        - orders_last_N_days: количество заказов
        - categories: распределение по категориям (%, абсолютные значения)
        - unique_dishes: количество уникальных блюд
        - total_dishes_available: общее количество блюд в меню
        """
        pass
```

---

## 3. Инфраструктура

### 3.1 Docker Compose

**Файл:** `docker-compose.yml` (обновление)

Добавить сервисы:
```yaml
services:
  # Existing: postgres, backend, frontend

  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      # KRaft mode configuration
    ports:
      - "9092:9092"

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes

  notifications-worker:
    build: ./backend
    command: python -m workers.notifications
    depends_on:
      - kafka
      - postgres
      - redis

  recommendations-worker:
    build: ./backend
    command: python -m workers.recommendations
    depends_on:
      - kafka
      - postgres
      - redis

  telegram-bot:
    build: ./backend
    command: python -m telegram.bot
    depends_on:
      - postgres
```

### 3.2 Environment Variables

**Файл:** `backend/.env.example` (обновление)

```bash
# Existing vars...

# Kafka
KAFKA_BROKER_URL=localhost:9092

# Redis
REDIS_URL=redis://localhost:6379

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Gemini API (пул ключей через запятую)
GEMINI_API_KEYS=AIzaSyA...key1,AIzaSyB...key2,AIzaSyC...key3
GEMINI_MAX_REQUESTS_PER_KEY=195
```

### 3.3 Configuration

**Файл:** `backend/src/config.py` (обновление)

```python
class Settings(BaseSettings):
    # Existing fields...

    # Kafka
    KAFKA_BROKER_URL: str

    # Redis
    REDIS_URL: str

    # Telegram
    TELEGRAM_BOT_TOKEN: str

    # Gemini
    GEMINI_API_KEYS: str  # comma-separated
    GEMINI_MAX_REQUESTS_PER_KEY: int = 195

    @property
    def gemini_keys_list(self) -> list[str]:
        return [k.strip() for k in self.GEMINI_API_KEYS.split(',')]
```

---

## 4. Декомпозиция на подзадачи для Coder

### Фаза 1: Инфраструктура (можно параллельно)

**Подзадача 1.1: Docker Compose и базовая настройка**
- **Файлы:** `docker-compose.yml`, `.env.example`, `backend/src/config.py`
- **Параллельно:** ✓ (независима)
- **Описание:** Добавить Kafka, Zookeeper, Redis в docker-compose

**Подзадача 1.2: Redis Client Setup**
- **Файлы:** `backend/src/cache/redis_client.py`, `backend/src/cache/__init__.py`
- **Параллельно:** ✓ (независима от 1.1)
- **Описание:** Async Redis client wrapper

**Подзадача 1.3: Kafka Producer Setup**
- **Файлы:** `backend/src/kafka/producer.py`, `backend/src/kafka/__init__.py`
- **Параллельно:** ✓ (независима)
- **Описание:** FastStream Kafka producer для событий

### Фаза 2: Уведомления для кафе

**Подзадача 2.1: Database Changes**
- **Файлы:**
  - `backend/src/models/cafe.py` (обновление)
  - `backend/alembic/versions/002_add_cafe_notifications.py` (новая миграция)
- **Параллельно:** ✗ (критическая, база для остальных)
- **Описание:** Обновить модель Cafe, создать CafeLinkRequest, миграция

**Подзадача 2.2: Cafe Link API Endpoints**
- **Файлы:**
  - `backend/src/routers/cafe_links.py`
  - `backend/src/services/cafe_link.py`
  - `backend/src/repositories/cafe_link.py`
  - `backend/src/schemas/cafe_link.py`
- **Параллельно:** ✗ (зависит от 2.1)
- **Описание:** CRUD для cafe link requests

**Подзадача 2.3: Telegram Bot**
- **Файлы:**
  - `backend/src/telegram/bot.py`
  - `backend/src/telegram/__init__.py`
  - `backend/src/telegram/handlers.py`
- **Параллельно:** ✓ (после 2.2, но можно параллельно с 2.4)
- **Описание:** Aiogram bot для приема заявок и отправки уведомлений

**Подзадача 2.4: Notifications Worker**
- **Файлы:**
  - `backend/workers/notifications.py`
  - `backend/workers/__init__.py`
- **Параллельно:** ✓ (после 2.1, параллельно с 2.3)
- **Описание:** Kafka worker для обработки deadline.passed событий

### Фаза 3: Gemini рекомендации (частично параллельно)

**Подзадача 3.1: Gemini API Key Pool**
- **Файлы:**
  - `backend/src/gemini/key_pool.py`
  - `backend/src/gemini/__init__.py`
- **Параллельно:** ✓ (после 1.2, независима от уведомлений)
- **Описание:** Класс управления пулом API ключей с ротацией

**Подзадача 3.2: Gemini Client и Recommendation Service**
- **Файлы:**
  - `backend/src/gemini/client.py`
  - `backend/src/gemini/prompts.py`
- **Параллельно:** ✗ (зависит от 3.1)
- **Описание:** Интеграция с Gemini API, обработка ошибок

**Подзадача 3.3: Order Statistics Service**
- **Файлы:**
  - `backend/src/services/order_stats.py`
- **Параллельно:** ✓ (после 2.1, параллельно с 3.1-3.2)
- **Описание:** Сбор статистики заказов для рекомендаций

**Подзадача 3.4: Recommendations API Endpoint**
- **Файлы:**
  - `backend/src/routers/recommendations.py`
  - `backend/src/schemas/recommendations.py`
- **Параллельно:** ✗ (зависит от 3.2, 3.3)
- **Описание:** GET endpoint для получения рекомендаций

**Подзадача 3.5: Recommendations Worker**
- **Файлы:**
  - `backend/workers/recommendations.py`
- **Параллельно:** ✗ (зависит от 3.2, 3.3)
- **Описание:** Kafka worker для batch-генерации рекомендаций

### Фаза 4: Frontend (опционально, можно отложить)

**Подзадача 4.1: Recommendations Component**
- **Файлы:**
  - `frontend_mini_app/src/components/RecommendationsCard.tsx`
  - `frontend_mini_app/src/components/RecommendationsCard.module.css`
- **Параллельно:** ✓ (независима от других)
- **Описание:** React компонент для отображения рекомендаций

**Подзадача 4.2: Profile Page Integration**
- **Файлы:**
  - `frontend_mini_app/src/app/profile/page.tsx` (обновление)
- **Параллельно:** ✗ (зависит от 4.1)
- **Описание:** Интеграция компонента рекомендаций в профиль

### Фаза 5: Тестирование

**Подзадача 5.1: Unit Tests**
- **Файлы:**
  - `backend/tests/unit/gemini/test_key_pool.py`
  - `backend/tests/unit/gemini/test_client.py`
  - `backend/tests/unit/services/test_order_stats.py`
  - `backend/tests/unit/services/test_cafe_link.py`
- **Параллельно:** ✓ (можно разделить между несколькими coder агентами)
- **Описание:** Unit тесты для ключевых компонентов

**Подзадача 5.2: Integration Tests**
- **Файлы:**
  - `backend/tests/integration/api/test_cafe_links.py`
  - `backend/tests/integration/api/test_recommendations.py`
  - `backend/tests/integration/test_gemini_pool.py`
- **Параллельно:** ✓ (после 5.1)
- **Описание:** Integration тесты для API и Gemini pool

**Подзадача 5.3: E2E Tests (Playwright)**
- **Файлы:**
  - `specs/recommendations.spec.ts`
  - `specs/test.plan.md`
- **Параллельно:** ✓ (независима, использует Playwright агенты)
- **Описание:** E2E тесты для фронтенда с рекомендациями

### Фаза 6: Документация

**Подзадача 6.1: Technical Documentation**
- **Файлы:**
  - `README.md` (обновление)
  - `.memory-base/tech-docs/kafka-architecture.md`
  - `.memory-base/tech-docs/gemini-integration.md`
- **Параллельно:** ✓
- **Описание:** Обновление документации

---

## 5. Параллельное выполнение - Рекомендации

### Группа 1 (Инфраструктура) - ПАРАЛЛЕЛЬНО
- Подзадача 1.1: Docker Compose
- Подзадача 1.2: Redis Client
- Подзадача 1.3: Kafka Producer

### Группа 2 (После 2.1) - ПАРАЛЛЕЛЬНО
- Подзадача 2.3: Telegram Bot
- Подзадача 2.4: Notifications Worker
- Подзадача 3.1: Gemini Key Pool
- Подзадача 3.3: Order Stats Service

### Группа 3 (После Группы 2) - ПАРАЛЛЕЛЬНО
- Подзадача 3.4: Recommendations API
- Подзадача 3.5: Recommendations Worker
- Подзадача 4.1: Frontend Component

### Критический путь (последовательно):
1. Подзадача 2.1: Database Changes
2. Подзадача 2.2: Cafe Link API
3. Подзадача 3.2: Gemini Client (зависит от 3.1)

---

## 6. Риски и соображения

### Технические риски

**1. Gemini API Rate Limits**
- **Риск:** Превышение лимитов даже с пулом ключей
- **Митигация:**
  - Мониторинг использования в Redis
  - Graceful degradation (возврат пустых рекомендаций)
  - Alert при исчерпании всех ключей

**2. Kafka Reliability**
- **Риск:** Потеря событий при сбое worker
- **Митигация:**
  - Consumer groups для fault tolerance
  - Dead letter queue для failed events
  - Логирование всех событий в PostgreSQL

**3. Redis Memory**
- **Риск:** OOM при большом количестве пользователей
- **Митигация:**
  - TTL на все ключи
  - Мониторинг memory usage
  - Eviction policy: allkeys-lru

**4. Telegram Bot Rate Limits**
- **Риск:** Ограничения Telegram API при массовой рассылке
- **Митигация:**
  - Rate limiting на стороне worker (30 msg/sec)
  - Retry с экспоненциальной задержкой
  - Batch отправка с паузами

### Архитектурные решения

**1. Event-Driven vs Direct Calls**
- **Выбор:** Event-driven через Kafka
- **Обоснование:**
  - Декаплинг компонентов
  - Fault tolerance
  - Масштабируемость

**2. Aiogram vs python-telegram-bot**
- **Выбор:** Aiogram 3.x
- **Обоснование:**
  - Современный async API
  - Лучшая интеграция с FastAPI
  - Активная разработка

**3. Scheduler: APScheduler vs Cron Job**
- **Выбор:** APScheduler в worker
- **Обоснование:**
  - Меньше зависимостей
  - Проще для разработки/тестирования
  - Можно легко перейти на Kafka events позже

**4. Gemini API: пул ключей vs квоты**
- **Выбор:** Пул ключей с ротацией
- **Обоснование:**
  - Обход лимитов бесплатного tier
  - Высокая доступность
  - Горизонтальное масштабирование

---

## 7. Зависимости библиотек

**Обновить `backend/pyproject.toml`:**

```toml
dependencies = [
    # Existing...
    "faststream[kafka]>=0.6.3",
    "redis>=5.0.0",
    "aiogram>=3.0.0",
    "google-genai>=1.0.0",
    "apscheduler>=3.10.0",
]
```

---

## 8. Мониторинг и наблюдаемость

### Метрики для сбора

**Kafka:**
- События в секунду (deadline.passed)
- Consumer lag
- Failed events count

**Redis:**
- Memory usage
- Hit/miss ratio для рекомендаций
- Key pool usage (current key, rotations count)

**Gemini API:**
- Requests per key
- Error rate по кодам (429, 401, 400)
- Rotation events

**Telegram:**
- Notifications sent/failed
- Average delivery time

### Логирование

Структурированные логи (JSON):
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

---

## 9. Миграция и развертывание

### Порядок развертывания

1. **Инфраструктура:**
   - Развернуть Kafka + Zookeeper
   - Развернуть Redis
   - Проверить подключение

2. **Database Migration:**
   - Применить миграцию 002
   - Проверить схему

3. **Backend Services:**
   - Развернуть обновленный API
   - Развернуть Telegram Bot
   - Развернуть Workers

4. **Тестирование:**
   - Создать тестовую заявку от кафе
   - Проверить уведомление
   - Запустить batch генерацию рекомендаций вручную

5. **Мониторинг:**
   - Настроить alerts
   - Проверить метрики

### Rollback Plan

При критических проблемах:
1. Откатить миграцию БД
2. Остановить workers
3. Откатить API на предыдущую версию
4. Сохранить логи для анализа

---

## 10. Следующие шаги

После завершения архитектурного дизайна:

1. **Coder агент** получит эту спецификацию для реализации
2. Рекомендуется начать с **Фазы 1** (инфраструктура) - параллельно
3. Затем **Фаза 2.1** (database changes) - критический путь
4. Далее **Группа 2** (уведомления + gemini key pool) - параллельно
5. **Reviewer** проверит качество кода
6. **Tester** напишет и запустит тесты
7. **DocWriter** обновит документацию

---

## Приложения

### A. Примеры событий Kafka

**deadline.passed:**
```json
{
  "type": "deadline.passed",
  "cafe_id": 123,
  "date": "2025-12-08",
  "timestamp": "2025-12-07T10:00:00Z"
}
```

**recommendation.generated:**
```json
{
  "type": "recommendation.generated",
  "user_tgid": 456789,
  "success": true,
  "timestamp": "2025-12-06T03:15:00Z"
}
```

### B. Redis Key Examples

```
recommendations:user:456789 = {
  "summary": "80% горячего, мало овощей",
  "tips": ["Добавь салат", "Попробуй рыбу"],
  "stats": {...},
  "generated_at": "2025-12-06T03:15:00Z"
}

gemini:current_key = "key1"
gemini:usage:key:abc123 = "187"
gemini:rotation_log = ["2025-12-06T03:15:00 key1->key2", ...]
```

### C. Gemini API Response Example

```json
{
  "summary": "80% горячего, мало овощей и клетчатки",
  "tips": [
    "Попробуйте добавить салат к обеду — в меню есть Греческий и Цезарь",
    "Вы заказываете одни и те же 8 блюд — попробуйте рыбные дни по средам",
    "Добавьте больше разнообразия: супы с овощами, легкие гарниры"
  ]
}
```

---

## Заключение

Архитектурный дизайн TSK-003 предоставляет полную спецификацию для реализации уведомлений для кафе и Gemini рекомендаций. Использование event-driven архитектуры на базе Kafka обеспечивает масштабируемость и отказоустойчивость. Пул API ключей для Gemini позволяет обойти лимиты бесплатного tier.

**Готово к передаче Coder агенту.**

**Статус:** completed
**Следующий агент:** coder
