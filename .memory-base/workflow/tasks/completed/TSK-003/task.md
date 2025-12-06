---
id: TSK-003
title: "Уведомления для кафе через Telegram и Gemini рекомендации"
pipeline: feature
status: pending
created_at: 2025-12-06T12:00:00
related_files:
  - .memory-base/busness-logic/new_features_design.md
  - backend/
  - .memory-base/tech-docs/stack.md
impact:
  api: true
  db: true
  frontend: true
  services: true
  kafka: true
  redis: true
---

## Описание

Реализовать две дополнительные функции из необязательных бизнес-требований:

1. **Уведомления для кафе через Telegram**
   - Привязка кафе к Telegram-чату
   - Автоматическая отправка агрегированных заказов после дедлайна
   - Kafka worker для асинхронной отправки уведомлений

2. **Умные рекомендации через Gemini API**
   - Анализ истории заказов пользователя (30 дней)
   - Генерация персональных советов по питанию
   - Кэширование рекомендаций в Redis (24 часа)
   - Kafka worker для batch-генерации рекомендаций (ночью)
   - **Управление пулом API ключей**: до 195 запросов на ключ с автоматической ротацией

## Анализ текущего состояния

### Что уже реализовано:
- ✅ Backend API (TSK-002)
- ✅ Frontend Telegram Mini App (TSK-001)
- ✅ Базовая архитектура с PostgreSQL, FastAPI
- ✅ Модели: Users, Cafes, Orders, Summaries
- ✅ Авторизация через Telegram WebApp

### Что нужно добавить:
- ❌ Kafka integration (FastStream)
- ❌ Redis для кэширования
- ❌ Telegram Bot API для отправки уведомлений
- ❌ Gemini API integration с пулом ключей
- ❌ Новые модели: CafeLinkRequest
- ❌ Обновление модели Cafe (поля для Telegram)
- ❌ Новые API endpoints (cafe requests, recommendations)
- ❌ Kafka workers: notifications, recommendations
- ❌ Расширение фронтенда (отображение рекомендаций)

## Acceptance Criteria

### 1. Уведомления для кафе

#### База данных
- [ ] Обновлена модель `Cafe`:
  - `tg_chat_id: int | null`
  - `tg_username: string | null`
  - `notifications_enabled: bool`
  - `linked_at: datetime | null`
- [ ] Создана таблица `cafe_link_requests`:
  - id, cafe_id, tg_chat_id, tg_username, status, created_at, processed_at
- [ ] Миграция для обновления схемы

#### API Endpoints (Backend)
- [ ] `POST /cafes/{cafe_id}/link-request` - создание заявки на привязку
- [ ] `GET /cafe-requests` - список заявок (manager)
- [ ] `POST /cafe-requests/{request_id}/approve` - одобрить заявку (manager)
- [ ] `POST /cafe-requests/{request_id}/reject` - отклонить заявку (manager)
- [ ] `PATCH /cafes/{cafe_id}/notifications` - вкл/выкл уведомления (manager)
- [ ] `DELETE /cafes/{cafe_id}/link` - отвязать Telegram (manager)

#### Kafka & Workers
- [ ] Настроен Kafka (docker-compose или cloud)
- [ ] Worker `notifications` слушает событие `deadline.passed`
- [ ] После дедлайна генерируется событие в Kafka
- [ ] Worker формирует сообщение с агрегированными заказами
- [ ] Worker отправляет уведомление через Telegram Bot API
- [ ] Логирование успешных/неудачных отправок

#### Telegram Bot
- [ ] Бот принимает команду от кафе для привязки
- [ ] Бот создает заявку через API
- [ ] Бот отправляет уведомления с форматированным списком заказов

#### Формат уведомления
- [ ] Красивое форматирование (Markdown/HTML)
- [ ] Структура: название кафе, дата, список заказов по людям, итоги
- [ ] Пример: см. `.memory-base/busness-logic/new_features_design.md`

### 2. Gemini рекомендации

#### Redis
- [ ] Настроен Redis (docker-compose или cloud)
- [ ] TTL для кэша рекомендаций: 24 часа
- [ ] Ключ: `recommendations:user:{tgid}`

#### API Endpoint
- [ ] `GET /users/{tgid}/recommendations` - получение рекомендаций
  - Возвращает кэш из Redis если есть
  - Если нет — возвращает `summary: null, tips: []`
  - Показывает статистику заказов (последние 30 дней)

#### Gemini API Key Pool Management
- [ ] **Пул API ключей**: хранение списка ключей в конфигурации
- [ ] **Счетчик запросов**: трекинг количества запросов для каждого ключа
- [ ] **Автоматическая ротация**: переключение на следующий ключ после 195 запросов
- [ ] **Хранилище счетчиков**: Redis для персистентности между перезапусками
- [ ] **Fallback**: если все ключи исчерпаны — ошибка с retry через N минут
- [ ] **Мониторинг**: логирование текущего ключа и количества использований

#### Kafka Worker
- [ ] Worker `recommendations` запускается по расписанию (cron/schedule)
- [ ] Время запуска: ночью (03:00)
- [ ] Логика:
  1. Берет активных пользователей с >= 5 заказами за 30 дней
  2. Собирает статистику по категориям и блюдам
  3. Отправляет в Gemini API (с ротацией ключей)
  4. Сохраняет результат в Redis

#### Gemini API Integration
- [ ] Конфигурация пула API keys в `.env` (GEMINI_API_KEYS=key1,key2,key3,...)
- [ ] Класс `GeminiAPIKeyPool` для управления ротацией
- [ ] Промпт для анализа питания (на основе категорий и разнообразия)
- [ ] Обработка ошибок:
  - Rate limits (429) → автоматический переход на следующий ключ
  - Network issues → retry с экспоненциальной задержкой
  - Invalid key → пропуск ключа, переход к следующему
- [ ] Fallback если все ключи недоступны или исчерпаны

#### Модели данных
- [ ] Pydantic схема для ответа Gemini:
  ```python
  class Recommendations:
      summary: str | None
      tips: list[str]
      stats: dict
      generated_at: datetime | None
  ```
- [ ] Модель для управления ключами:
  ```python
  class APIKeyUsage:
      key_id: str
      usage_count: int
      max_requests: int = 195
      reset_at: datetime
  ```

#### Frontend (опционально, можно отложить)
- [ ] Компонент `RecommendationsCard` для профиля
- [ ] Отображение статистики и советов
- [ ] Placeholder если рекомендаций нет

### 3. Инфраструктура

#### Docker Compose
- [ ] Kafka + Zookeeper (или Kafka KRaft mode)
- [ ] Redis
- [ ] PostgreSQL (уже есть)
- [ ] Backend API (уже есть)
- [ ] Workers (notifications, recommendations)

#### Environment Variables
- [ ] `KAFKA_BROKER_URL`
- [ ] `REDIS_URL`
- [ ] `TELEGRAM_BOT_TOKEN`
- [ ] `GEMINI_API_KEYS` - список ключей через запятую
- [ ] `GEMINI_MAX_REQUESTS_PER_KEY` - лимит запросов на ключ (default: 195)
- [ ] Обновлен `.env.example`

#### Dependencies
- [ ] `faststream[kafka]` - Kafka integration
- [ ] `redis` - Redis client
- [ ] `aiogram` или `python-telegram-bot` - Telegram Bot API
- [ ] `google-genai` - Gemini API SDK (googleapis/python-genai)
- [ ] Обновлен `pyproject.toml`

### 4. Тестирование

#### Unit Tests
- [ ] Тесты для Gemini API wrapper (mocked)
- [ ] Тесты для `GeminiAPIKeyPool` (ротация, счетчики)
- [ ] Тесты для формирования уведомлений
- [ ] Тесты для статистики заказов
- [ ] Тесты для Redis кэша

#### Integration Tests
- [ ] API: создание/одобрение cafe link requests
- [ ] API: получение рекомендаций
- [ ] API: управление уведомлениями (enable/disable)
- [ ] Gemini pool: переключение ключей после 195 запросов

#### E2E Tests (Playwright)
- [ ] **Использовать Playwright агенты** из `.claude/agents/`:
  - `playwright-test-planner` - создание тест-плана
  - `playwright-test-generator` - генерация автотестов
  - `playwright-test-healer` - дебаг и фикс падающих тестов
- [ ] E2E тесты для фронтенда:
  - Отображение рекомендаций в профиле
  - Интеграция с API
  - Пользовательские сценарии
- [ ] Mocked backend для независимого тестирования фронтенда

#### Coverage
- [ ] Coverage >= 80%

### 5. Документация

- [ ] README обновлен (новые endpoints, workers, инфраструктура)
- [ ] Описание архитектуры Kafka workers
- [ ] Инструкции по настройке Kafka и Redis
- [ ] Примеры конфигурации `.env` (включая пул API ключей)
- [ ] Документация Gemini API integration и ротации ключей
- [ ] OpenAPI (Swagger) автодокументация для новых endpoints
- [ ] Описание логики управления пулом API ключей
- [ ] Инструкции по запуску E2E тестов (Playwright)

## Контекст

### Полный дизайн

См. `.memory-base/busness-logic/new_features_design.md` для полной спецификации:
- Схемы моделей (Cafe, CafeLinkRequest)
- Формат уведомлений
- Структура данных для Gemini
- API endpoints
- Архитектура Kafka workers

### Playwright Агенты

Для E2E тестирования используются специализированные агенты в `.claude/agents/`:

1. **playwright-test-planner** (`playwright-test-planner.md`)
   - Создает comprehensive test plan для веб-приложения
   - Исследует интерфейс, определяет user flows
   - Генерирует сценарии (happy path, edge cases, error handling)

2. **playwright-test-generator** (`playwright-test-generator.md`)
   - Генерирует автоматические тесты на Playwright
   - Выполняет steps из test plan в реальном времени
   - Создает test specs с правильной структурой

3. **playwright-test-healer** (`playwright-test-healer.md`)
   - Дебагит и исправляет падающие тесты
   - Систематический подход: run → debug → fix → verify
   - Обновляет селекторы, assertions, timing

### Стек технологий

**Backend (уже используется):**
- Python >= 3.13
- FastAPI >= 0.120.0
- PostgreSQL 17
- SQLAlchemy >= 2.0.44 (async)

**Новые зависимости:**
- FastStream >= 0.6.3 (Kafka)
- Redis >= 5.0
- python-telegram-bot или aiogram
- google-genai (googleapis/python-genai)

**Тестирование:**
- pytest (unit/integration)
- Playwright (E2E для фронтенда)
- Playwright MCP tools (через агенты)

**Инфраструктура:**
- Kafka (для event-driven архитектуры)
- Redis (для кэширования и хранения счетчиков API ключей)
- Docker Compose (для оркестрации)

### Архитектура

```
┌─────────────┐
│ Telegram    │
│ Mini App    │ ← пользователь делает заказ
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Backend API │ → сохраняет заказ в PostgreSQL
└──────┬──────┘
       │
       ▼ (после дедлайна)
┌─────────────┐
│ Kafka Event │ → deadline.passed {cafe_id, date}
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Worker:     │ → читает заказы из PostgreSQL
│notifications│ → формирует уведомление
└──────┬──────┘ → отправляет через Telegram Bot API
       │
       ▼
┌─────────────┐
│ Cafe        │ ← получает уведомление в Telegram
│ Telegram    │
└─────────────┘

┌─────────────┐
│ Cron Job    │ → запускает в 03:00
│ (scheduler) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Worker:     │ → читает историю заказов
│recommenda-  │ → отправляет в Gemini API (с ротацией ключей)
│tions        │ → кэширует в Redis
└──────┬──────┘
       │
       ▼ (Gemini API)
┌─────────────┐
│ API Key     │ → key1 (195 req) → key2 (195 req) → key3 ...
│ Pool        │ → счетчики в Redis
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Redis Cache │ → recommendations + key usage counters (TTL 24h)
└──────┬──────┘
       │
       ▼ (когда пользователь открывает профиль)
┌─────────────┐
│ Backend API │ → GET /users/{tgid}/recommendations
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Frontend    │ ← отображает рекомендации
└─────────────┘
```

### Gemini API Key Pool - Детальная спецификация

#### Структура конфигурации
```bash
# .env
GEMINI_API_KEYS=AIzaSyA...key1,AIzaSyB...key2,AIzaSyC...key3
GEMINI_MAX_REQUESTS_PER_KEY=195
```

#### Архитектура пула ключей

```python
class GeminiAPIKeyPool:
    """
    Управление пулом API ключей для Gemini API.

    Функции:
    - Хранение списка ключей
    - Трекинг количества использований каждого ключа
    - Автоматическая ротация при достижении лимита
    - Персистентность счетчиков в Redis
    """

    def __init__(self, keys: list[str], max_requests: int = 195):
        self.keys = keys
        self.max_requests = max_requests
        self.redis_client = redis.Redis(...)

    async def get_client(self) -> genai.Client:
        """
        Возвращает Gemini client с текущим активным ключом.
        Автоматически переключает на следующий ключ если лимит достигнут.
        """
        current_key = await self._get_current_key()
        usage_count = await self._get_usage_count(current_key)

        if usage_count >= self.max_requests:
            current_key = await self._rotate_key()

        await self._increment_usage(current_key)
        return genai.Client(api_key=current_key)

    async def _get_current_key(self) -> str:
        """Получить текущий активный ключ из Redis."""
        ...

    async def _get_usage_count(self, key: str) -> int:
        """Получить количество использований ключа из Redis."""
        ...

    async def _increment_usage(self, key: str) -> None:
        """Увеличить счетчик использований ключа в Redis."""
        ...

    async def _rotate_key(self) -> str:
        """Переключить на следующий доступный ключ."""
        ...
```

#### Redis схема для хранения счетчиков

```
# Текущий активный ключ
gemini:current_key → "key1"

# Счетчики использований (TTL 24 часа)
gemini:usage:key1 → 187
gemini:usage:key2 → 45
gemini:usage:key3 → 0

# История ротации (для мониторинга)
gemini:rotation_log → ["2025-12-06T03:15:00 key1->key2", ...]
```

#### Обработка ошибок API

```python
async def generate_recommendations(user_stats: dict) -> dict:
    """
    Генерация рекомендаций с обработкой ошибок и ротацией ключей.
    """
    max_retries = len(api_key_pool.keys)

    for attempt in range(max_retries):
        try:
            client = await api_key_pool.get_client()
            response = await client.models.generate_content(
                model='gemini-2.5-flash',
                contents=format_prompt(user_stats)
            )
            return parse_response(response)

        except errors.APIError as e:
            if e.code == 429:  # Rate limit
                logger.warning(f"Rate limit hit, rotating key (attempt {attempt+1})")
                await api_key_pool._rotate_key()
                continue
            elif e.code == 401:  # Invalid key
                logger.error(f"Invalid API key, skipping")
                await api_key_pool._mark_key_invalid()
                continue
            else:
                raise

    raise Exception("All API keys exhausted")
```

## Подзадачи для Architect

Architect должен будет разбить эту задачу на модули:

### Фаза 1: Инфраструктура
1. Docker Compose (Kafka, Redis)
2. Kafka integration (FastStream)
3. Redis client setup

### Фаза 2: Уведомления для кафе
4. Обновление модели Cafe (миграция)
5. Модель CafeLinkRequest
6. API endpoints: cafe link requests
7. Telegram Bot (прием заявок)
8. Kafka Worker: notifications
9. Интеграция с Telegram Bot API

### Фаза 3: Gemini рекомендации
10. Класс GeminiAPIKeyPool (управление пулом ключей)
11. Gemini API wrapper с обработкой ошибок
12. Сервис статистики заказов
13. Kafka Worker: recommendations (batch job)
14. API endpoint: GET /users/{tgid}/recommendations
15. Redis кэширование (рекомендации + счетчики ключей)

### Фаза 4: Frontend
16. Компонент RecommendationsCard
17. Интеграция с API

### Фаза 5: Тестирование
18. Unit/Integration тесты (pytest)
19. **E2E тесты (Playwright):**
    - Запуск playwright-test-planner для создания test plan
    - Запуск playwright-test-generator для генерации автотестов
    - Запуск playwright-test-healer для исправления падающих тестов

### Фаза 6: Документация
20. Обновление README и документации

Рекомендуется параллельный запуск Coder субагентов для независимых модулей (например, Kafka setup, Redis setup, Gemini wrapper + Key Pool могут разрабатываться параллельно).

## Ожидаемый результат

Полнофункциональная система с:
1. Автоматическими уведомлениями для кафе после дедлайна заказов
2. Персональными рекомендациями по питанию для пользователей
3. Event-driven архитектурой на Kafka
4. Кэшированием в Redis
5. Интеграцией с Gemini API с автоматической ротацией ключей (до 195 запросов на ключ)
6. Мониторингом использования API ключей
7. Покрытием тестами >= 80% (включая E2E Playwright тесты)
8. Полной документацией

Все обязательные бизнес-требования уже реализованы в TSK-002. Эта задача добавляет необязательные функции, которые делают проект значительно более полезным и интересным.

## Связь с другими задачами

- **TSK-001**: Frontend готов, будет расширен для отображения рекомендаций
- **TSK-002**: Backend API готов, будет расширен новыми endpoints
- **Зависимости**: TSK-003 зависит от завершения TSK-002 (backend должен быть рабочим)

## Примечания

- Эта задача более сложная, чем TSK-001 и TSK-002, так как вводит новые технологии (Kafka, Redis, Gemini API с пулом ключей)
- Рекомендуется начать с инфраструктуры (Docker Compose) и базовой интеграции
- Можно реализовать функции поэтапно: сначала уведомления, потом рекомендации
- **Критично**: правильная реализация управления пулом API ключей для соблюдения лимитов Gemini API
- **E2E тесты**: обязательно использовать Playwright агенты из `.claude/agents/` для генерации и поддержки тестов

## Приоритет функций

**High Priority:**
- Уведомления для кафе (критично для бизнес-процесса)
- Kafka + Redis инфраструктура
- Gemini API Key Pool (критично для масштабирования)

**Medium Priority:**
- Gemini рекомендации (nice to have, но не блокирует основной функционал)
- E2E тесты (Playwright)

**Low Priority:**
- Frontend для рекомендаций (можно реализовать позже)

## Ограничения Gemini API

**Важно:** Согласно документации Google Generative AI Python SDK:
- Лимит запросов на API ключ может различаться в зависимости от тарифного плана
- Рекомендуется использовать пул из нескольких ключей для высоконагруженных приложений
- При превышении лимита (HTTP 429) необходимо автоматически переключаться на следующий ключ
- Для продакшн окружения необходим мониторинг использования ключей
