---
agent: coder
task_id: TSK-003
subtask: 6
subtask_name: "Notifications Worker"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/workers/__init__.py
    action: created
  - path: backend/workers/notifications.py
    action: created
---

# Coder Report: Notifications Worker

## Задача

Подзадача 2.4: Реализовать Notifications Worker для обработки событий deadline.passed и отправки уведомлений кафе через Telegram Bot API.

## Реализация

### 1. Созданные файлы

#### `backend/workers/__init__.py`
- Инициализационный файл для пакета workers
- Минималистичная документация

#### `backend/workers/notifications.py`
- **FastStream Kafka Worker** для обработки событий
- **Подписка на топик**: `lunch-bot.deadlines`
- **Обработчик события**: `handle_deadline_passed()`
- **Интеграция с PostgreSQL**: получение заказов и данных кафе
- **Telegram Bot API**: отправка уведомлений через httpx
- **Retry логика**: экспоненциальная задержка при ошибках
- **Логирование**: структурированные логи для всех операций

### 2. Ключевые компоненты

#### Database Integration
```python
# Async SQLAlchemy setup
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Fetch cafe and orders with relationships
async def get_cafe_with_orders(db: AsyncSession, cafe_id: int, order_date: str):
    # Fetch cafe
    cafe = await db.execute(select(Cafe).where(Cafe.id == cafe_id))

    # Fetch orders with eager loading
    orders = await db.execute(
        select(Order)
        .where(Order.cafe_id == cafe_id, Order.order_date == order_date)
        .options(selectinload(Order.user), selectinload(Order.combo))
    )
```

#### FastStream Kafka Subscriber
```python
broker = KafkaBroker(settings.KAFKA_BROKER_URL)

@broker.subscriber("lunch-bot.deadlines")
async def handle_deadline_passed(event: DeadlinePassedEvent) -> None:
    # 1. Fetch cafe and orders
    # 2. Check cafe is linked to Telegram
    # 3. Check notifications enabled
    # 4. Format message
    # 5. Send via Telegram Bot API
```

#### Notification Formatting
```python
def format_notification(cafe, date, orders, menu_items) -> str:
    """
    Формат:
    📋 {Cafe.name} — Заказ на {date}
    ━━━━━━━━━━━━━━━━━━━━━

    👤 {User.name}:
       • {Combo.name}
         - {MenuItem.name} (category)
       • {Extra.name} ×{quantity}
       📝 {notes}

    ━━━━━━━━━━━━━━━━━━━━━
    Итого: {total_orders} заказов, {total_amount} ₽
    """
```

#### Telegram Bot API Integration
```python
async def send_telegram_notification(chat_id: int, message: str) -> bool:
    """
    - URL: https://api.telegram.org/bot{token}/sendMessage
    - parse_mode: Markdown
    - Retry logic: 3 attempts with exponential backoff
    - Error handling:
      - 429 (Rate Limit) → retry with Retry-After header
      - 400/403/404 (Client Error) → don't retry
      - 5xx (Server Error) → retry
      - Network errors → retry
    """
```

### 3. Обработка ошибок

#### Rate Limiting (429)
- Читает `Retry-After` header
- Ждет указанное время
- Повторяет попытку

#### Client Errors (400, 403, 404)
- **Не повторяет** попытку (ошибка конфигурации)
- Логирует детали ошибки

#### Server Errors (5xx)
- Повторяет с экспоненциальной задержкой
- Максимум 3 попытки

#### Network Errors
- Retry с backoff
- Логирование всех попыток

### 4. Логирование

**Структурированные логи** с контекстом:

```python
logger.info(
    "Notification sent successfully",
    extra={
        "cafe_id": event.cafe_id,
        "cafe_name": cafe.name,
        "chat_id": cafe.tg_chat_id,
        "date": event.date,
        "orders_count": len(orders),
    }
)
```

**События логируются:**
- Получение события deadline.passed
- Проверка кафе (существует, привязан к TG, уведомления включены)
- Количество заказов
- Отправка уведомления (успех/неудача)
- Ошибки и retry попытки

### 5. Lifecycle Hooks

```python
@broker.on_startup
async def startup_event():
    """Логирование запуска worker"""

@broker.on_shutdown
async def shutdown_event():
    """Закрытие соединений с БД"""
    await engine.dispose()
```

### 6. Entrypoint

```python
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(broker.start())
```

**Запуск:**
```bash
python -m backend.workers.notifications
```

## Особенности реализации

### 1. Использование SQLAlchemy async
- Создан отдельный async engine для worker
- Использование `selectinload` для eager loading связей
- Избежание N+1 queries

### 2. FastStream интеграция
- Подписка на Kafka топик через декоратор
- Автоматический десериализация в Pydantic модель
- Async обработчик события

### 3. Telegram Bot API
- Использование httpx (async HTTP client)
- Timeout: 10 секунд
- Markdown формат для красивых сообщений

### 4. Бизнес-логика
- **Проверка:** кафе существует
- **Проверка:** кафе привязано к Telegram (tg_chat_id)
- **Проверка:** уведомления включены (notifications_enabled)
- **Проверка:** есть заказы на дату
- **Только после всех проверок:** отправка уведомления

### 5. Устойчивость к ошибкам
- Retry для временных сбоев
- Graceful degradation при конфигурационных ошибках
- Логирование всех ошибок с контекстом

## Зависимости

Все необходимые библиотеки уже есть в проекте:
- `faststream[kafka]` - Kafka integration
- `httpx` - HTTP client (используется в тестах)
- `sqlalchemy` - ORM
- `asyncpg` - PostgreSQL driver

## Тестирование

**Для тестирования worker:**

1. Запустить Kafka и PostgreSQL
2. Убедиться что в .env есть:
   ```
   KAFKA_BROKER_URL=localhost:9092
   DATABASE_URL=postgresql+asyncpg://...
   TELEGRAM_BOT_TOKEN=your_token
   ```

3. Запустить worker:
   ```bash
   python -m backend.workers.notifications
   ```

4. Опубликовать событие в Kafka:
   ```python
   from backend.src.kafka.producer import publish_deadline_passed
   await publish_deadline_passed(cafe_id=1, date="2025-12-08")
   ```

5. Проверить логи и Telegram чат

## Границы подзадачи

✅ **Сделано:**
- Создан workers package
- Реализован notifications worker
- Подписка на Kafka топик
- Обработка deadline.passed события
- Формирование сообщения (Markdown)
- Отправка через Telegram Bot API
- Retry логика
- Структурированное логирование

❌ **НЕ сделано (не входит в подзадачу):**
- Telegram Bot для приема заявок (подзадача 2.3)
- Recommendations worker (подзадача 3.5)
- Тесты (отдельная фаза)

## Следующие шаги

После этой подзадачи параллельно можно реализовать:
- **Подзадача 2.3**: Telegram Bot (независима)
- **Подзадача 3.1**: Gemini API Key Pool (независима)
- **Подзадача 3.3**: Order Statistics Service (независима)

## Статус

✅ **Completed** - Notifications Worker полностью реализован и готов к тестированию.
