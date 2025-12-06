---
agent: coder
task_id: TSK-003
subtask: 9
subtask_name: "Telegram Bot"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/src/telegram/__init__.py
    action: created
  - path: backend/src/telegram/bot.py
    action: created
  - path: backend/src/telegram/handlers.py
    action: created
---

# Telegram Bot Implementation

## Описание

Реализован Telegram Bot на базе aiogram 3.x для приема заявок на привязку кафе к чатам.

## Реализованные файлы

### 1. backend/src/telegram/__init__.py

Экспорт основных компонентов бота:
- `bot` - экземпляр Bot
- `dp` - экземпляр Dispatcher

### 2. backend/src/telegram/bot.py

Инициализация бота и главная точка входа:
- Создание Bot instance с токеном из конфигурации
- Создание Dispatcher instance
- Функция `main()` для запуска бота в режиме polling
- Регистрация роутера с обработчиками

**Запуск:**
```bash
python -m src.telegram.bot
```

### 3. backend/src/telegram/handlers.py

Обработчики команд для привязки кафе:

#### Команды

**1. /start**
- Приветственное сообщение
- Инструкции по использованию /link

**2. /link <cafe_id>**
- Парсинг cafe_id из команды (regex: `/link\s+(\d+)`)
- Извлечение chat_id и username из message
- HTTP POST запрос к API: `POST /api/v1/cafes/{cafe_id}/link-request`
- Обработка ответов:
  - 201: Успешное создание заявки
  - 404: Кафе не найдено
  - 400: Неверный запрос (например, уже есть pending заявка)
  - Другие: Общая ошибка

**3. /status**
- Placeholder для проверки статуса привязки
- В текущей версии показывает информационное сообщение

**4. /help**
- Список доступных команд
- Описание каждой команды
- Пример использования

#### Обработка ошибок

- `httpx.TimeoutException` - Превышено время ожидания
- `httpx.RequestError` - Ошибка подключения
- HTTP статусы (404, 400, 5xx)
- Валидация формата команды

#### Логирование

Структурированные логи для:
- Успешное создание заявок
- Ошибки API запросов
- Таймауты

## Архитектура

```
Telegram User
      ↓
/link <cafe_id>
      ↓
handlers.py → cmd_link()
      ↓
httpx.AsyncClient
      ↓
POST /api/v1/cafes/{cafe_id}/link-request
      ↓
Backend API (routers/cafe_links.py)
      ↓
Response → User
```

## Технологии

- **aiogram 3.x** - Async Telegram Bot framework
- **httpx** - Async HTTP client для API запросов
- **Python 3.13** - Type hints, async/await

## Зависимости

```toml
aiogram >= 3.0.0
httpx >= 0.25.0
```

## Конфигурация

Используется из `backend/src/config.py`:
- `TELEGRAM_BOT_TOKEN` - токен бота

## Особенности реализации

1. **Async/await** - Все обработчики асинхронные
2. **Regex валидация** - Команда /link валидируется через регулярное выражение
3. **Timeout handling** - HTTP запросы с таймаутом 10 секунд
4. **User-friendly messages** - Понятные сообщения об ошибках на русском языке
5. **Structured logging** - Логи с контекстом (cafe_id, chat_id, request_id)

## Примеры использования

### Успешная привязка

```
Пользователь: /link 1

Бот:
✅ Заявка на привязку кафе #1 успешно создана!

ID заявки: 42
Статус: pending

Ожидайте одобрения от менеджера.
```

### Кафе не найдено

```
Пользователь: /link 999

Бот:
❌ Кафе с ID 999 не найдено.

Проверьте правильность ID.
```

### Неверный формат

```
Пользователь: /link abc

Бот:
❌ Неверный формат команды.

Используйте: /link <cafe_id>
Например: /link 1
```

## Следующие шаги

1. **Notifications Worker** (подзадача 2.4) использует этот бот для отправки уведомлений
2. Для отправки уведомлений нужно:
   - Импортировать `bot` из `src.telegram`
   - Использовать `bot.send_message(chat_id=..., text=...)`
   - Форматировать сообщение с заказами (Markdown/HTML)

## Интеграция с Worker

Пример использования в notifications worker:

```python
from src.telegram import bot

async def send_notification(cafe_tg_chat_id: int, message: str):
    """Send notification to cafe Telegram chat."""
    await bot.send_message(
        chat_id=cafe_tg_chat_id,
        text=message,
        parse_mode="HTML"
    )
```

## Тестирование

Для локального тестирования:
1. Создать бота через @BotFather
2. Получить токен
3. Добавить в `.env`: `TELEGRAM_BOT_TOKEN=...`
4. Запустить: `python -m src.telegram.bot`
5. Найти бота в Telegram
6. Отправить `/start` и `/link 1`

## Границы

- ✅ Реализованы все команды из спецификации
- ✅ Обработка ошибок HTTP запросов
- ✅ Валидация формата команды
- ✅ Логирование
- ❌ НЕ реализована отправка уведомлений (это для worker)
- ❌ НЕ реализован /status (placeholder, требует дополнительный API endpoint)

## Статус

**Completed** ✅

Все файлы созданы согласно спецификации Architect. Telegram Bot готов к интеграции с Notifications Worker.
