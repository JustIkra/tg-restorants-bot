---
id: TSK-004
title: "Полная интеграция, E2E тестирование и деплой системы"
pipeline: feature
status: completed
created_at: 2025-12-06T11:30:00
related_files:
  - backend/
  - frontend_mini_app/
  - docker-compose.yml
  - .memory-base/busness-logic/technical_requirements.md
impact:
  api: true
  db: false
  frontend: true
  services: true
  testing: true
  deployment: true
---

## Описание

Завершить разработку проекта Telegram-бота заказа обедов путем полной интеграции всех компонентов, комплексного тестирования и подготовки к продакшн деплою.

На данный момент все основные компоненты реализованы технически:
- Backend API (TSK-002)
- Frontend Telegram Mini App (TSK-001)
- Kafka workers, Redis кэширование, Gemini API (TSK-003)
- Telegram Bot для кафе
- Docker инфраструктура

Однако система не протестирована как единое целое и не готова к реальному использованию.

## Анализ текущего состояния

### Что уже реализовано:

**Backend (TSK-002, TSK-003):**
- ✅ FastAPI REST API
- ✅ PostgreSQL 17 + SQLAlchemy + Alembic
- ✅ JWT авторизация через Telegram WebApp
- ✅ RBAC (user, manager)
- ✅ API endpoints: users, cafes, menu, orders, summaries, cafe-requests, recommendations
- ✅ Kafka integration (FastStream)
- ✅ Redis caching
- ✅ Gemini API с пулом ключей (195 req/key)
- ✅ Telegram Bot для приема заявок от кафе
- ✅ Workers: notifications, recommendations
- ✅ Unit тесты (pytest)

**Frontend (TSK-001):**
- ✅ Next.js 16 + React 19 + Tailwind CSS 4
- ✅ Telegram WebApp SDK интеграция
- ✅ Компоненты: CafeSelector, ComboSelector, MenuSection, ExtrasSection
- ✅ API client с JWT
- ✅ Unit тесты (Jest + React Testing Library)

**Infrastructure (TSK-003):**
- ✅ Docker Compose
- ✅ Services: PostgreSQL, Kafka, Zookeeper, Redis, Backend, Telegram Bot, Workers
- ✅ Health checks
- ✅ Environment variables

### Что НЕ сделано:

**Интеграция:**
- ❌ Frontend не подключен к реальному backend (использует mock данные?)
- ❌ Telegram Bot не протестирован с реальными кафе
- ❌ Workers не протестированы в связке с Telegram
- ❌ Полный флоу от заказа до уведомления кафе не проверен

**Тестирование:**
- ❌ E2E тесты для фронтенда (Playwright)
- ❌ Integration тесты для полного флоу (заказ → deadline → уведомление)
- ❌ Тесты Gemini API key pool в реальных условиях
- ❌ Нагрузочные тесты

**Документация:**
- ❌ Инструкции по деплою
- ❌ Руководство пользователя
- ❌ Руководство администратора
- ❌ API документация (Swagger/OpenAPI) не проверена
- ❌ Troubleshooting guide

**Deployment:**
- ❌ Production-ready конфигурация
- ❌ CI/CD pipeline (GitHub Actions?)
- ❌ Мониторинг и логирование
- ❌ Backup стратегия

## Acceptance Criteria

### 1. Интеграция компонентов

#### Frontend ↔ Backend
- [ ] Frontend подключен к backend API (не mock)
- [ ] Авторизация через Telegram WebApp работает end-to-end
- [ ] Создание заказа через UI → сохранение в PostgreSQL
- [ ] Получение меню и комбо из backend
- [ ] CORS настроен корректно
- [ ] Error handling работает на всех уровнях

#### Telegram Bot ↔ Backend
- [ ] Бот принимает заявки от кафе
- [ ] Заявки создаются в БД через API
- [ ] Менеджер может одобрять/отклонять заявки
- [ ] После одобрения кафе получает тестовое уведомление
- [ ] Форматирование уведомлений корректное (Markdown)

#### Workers ↔ Kafka ↔ Backend
- [ ] После дедлайна генерируется Kafka событие
- [ ] Notifications worker обрабатывает событие
- [ ] Worker получает заказы из PostgreSQL
- [ ] Worker отправляет уведомление через Telegram Bot API
- [ ] Recommendations worker генерирует рекомендации ночью
- [ ] Рекомендации кэшируются в Redis (TTL 24h)
- [ ] API endpoint возвращает кэшированные рекомендации

#### Gemini API Key Pool
- [ ] Пул из нескольких ключей настроен
- [ ] Автоматическая ротация после 195 запросов
- [ ] Счетчики в Redis работают корректно
- [ ] Обработка rate limits (429) → переключение на следующий ключ
- [ ] Обработка invalid key (401) → пропуск ключа
- [ ] Fallback при исчерпании всех ключей

### 2. End-to-End тестирование

#### E2E тесты (Playwright)
- [ ] **Использовать Playwright MCP tools** и агенты из `.claude/agents/`:
  - `playwright-test-planner` - создание test plan
  - `playwright-test-generator` - генерация автотестов
  - `playwright-test-healer` - фикс падающих тестов
- [ ] Тест: Авторизация пользователя через Telegram WebApp
- [ ] Тест: Выбор кафе и комбо-набора
- [ ] Тест: Заполнение заказа (выбор блюд по категориям)
- [ ] Тест: Добавление extras
- [ ] Тест: Подтверждение заказа
- [ ] Тест: Просмотр истории заказов
- [ ] Тест: Просмотр рекомендаций в профиле
- [ ] Тест: Менеджер одобряет заявку от кафе
- [ ] Тест: Менеджер создает отчет

#### Integration тесты
- [ ] Полный флоу: заказ → deadline → Kafka event → worker → Telegram notification
- [ ] Gemini API: генерация рекомендаций → кэш в Redis → API endpoint
- [ ] Cafe link request: bot → API → manager approval → notification enabled
- [ ] Deadline validation: попытка заказать после дедлайна → 400 error
- [ ] Balance check: превышение лимита → ошибка (если реализовано)

#### Manual Testing Checklist
- [ ] Создать тестовых пользователей (user, manager)
- [ ] Создать тестовые кафе с меню
- [ ] Настроить deadlines
- [ ] Сделать несколько заказов через UI
- [ ] Проверить уведомление кафе после дедлайна
- [ ] Проверить генерацию рекомендаций
- [ ] Проверить экспорт отчета (JSON, CSV)

### 3. Документация

#### User Guides
- [ ] README в корне проекта:
  - Описание системы
  - Архитектурная диаграмма
  - Инструкции по запуску
- [ ] Руководство пользователя (для сотрудников):
  - Как сделать заказ
  - Как изменить заказ
  - Как посмотреть историю
- [ ] Руководство для кафе:
  - Как подключить кафе через бота
  - Формат уведомлений
  - Что делать при проблемах
- [ ] Руководство менеджера:
  - Управление пользователями
  - Управление меню
  - Настройка deadlines
  - Получение отчетов

#### Technical Documentation
- [ ] API документация (Swagger UI):
  - Все endpoints задокументированы
  - Примеры запросов/ответов
  - Error codes
- [ ] Architecture документация:
  - Схема компонентов
  - Kafka topics и events
  - Redis ключи и TTL
  - Gemini API key pool
- [ ] Deployment guide:
  - Production конфигурация
  - Environment variables
  - Docker deployment
  - Database migrations
- [ ] Troubleshooting guide:
  - Частые проблемы и решения
  - Debug commands
  - Логи и мониторинг

### 4. Production-Ready Deployment

#### Configuration
- [ ] `.env.example` с описанием всех переменных
- [ ] Production vs Development конфигурации
- [ ] Secrets management (не коммитить токены/ключи)
- [ ] CORS для production домена
- [ ] HTTPS настроен (или инструкции)

#### Docker & Infrastructure
- [ ] Multi-stage Dockerfile для оптимизации размера
- [ ] Docker Compose для production (без volumes для кода)
- [ ] Health checks для всех сервисов
- [ ] Resource limits (CPU, memory)
- [ ] Restart policies

#### Database
- [ ] Миграции готовы к продакшн
- [ ] Backup стратегия (pg_dump)
- [ ] Индексы для производительности
- [ ] Connection pooling настроен

#### Monitoring & Logging
- [ ] Structured logging (JSON format)
- [ ] Логи доступны через `docker logs`
- [ ] Метрики:
  - Kafka consumer lag
  - Redis memory usage
  - API response time
  - Gemini API key usage
- [ ] Health check endpoints:
  - `/health` - API статус
  - `/health/db` - PostgreSQL connection
  - `/health/redis` - Redis connection
  - `/health/kafka` - Kafka connection

#### CI/CD (опционально, можно отложить)
- [ ] GitHub Actions workflow:
  - Lint и type check
  - Run tests
  - Build Docker images
  - Deploy to staging/production
- [ ] Automated database migrations

### 5. Security & Performance

#### Security
- [ ] JWT секрет изменен на production
- [ ] Rate limiting для API endpoints
- [ ] Input validation (Pydantic)
- [ ] SQL injection защита (SQLAlchemy ORM)
- [ ] XSS защита (React)
- [ ] CORS ограничен production доменом
- [ ] Secrets не в git (`.env` в `.gitignore`)

#### Performance
- [ ] Database индексы:
  - `orders(user_tgid, order_date)`
  - `orders(cafe_id, order_date)`
  - `menu_items(cafe_id, category)`
- [ ] Redis кэширование работает (TTL 24h)
- [ ] Connection pooling для PostgreSQL
- [ ] Kafka partitioning для масштабирования
- [ ] Frontend оптимизация:
  - Production build (`npm run build`)
  - Минификация
  - Code splitting

### 6. Acceptance Testing

#### User Acceptance Criteria (из technical_requirements.md)

**Для сотрудника:**
- [ ] Авторизация в боте по Telegram-ID ✓
- [ ] Просмотр меню ✓
- [ ] Оформление заказа ✓
- [ ] Управление заказом (изменение до дедлайна) ✓

**Для менеджера:**
- [ ] Загрузка сотрудников (Telegram-ID, имя, офис) ✓
- [ ] Управление сроками, меню, доступными кафе ✓
- [ ] Просмотр заказов ✓
- [ ] Получение агрегированного отчёта по кафе ✓
- [ ] Запрет изменений заказов после дедлайна ✓

**Необязательные (реализовано в TSK-003):**
- [ ] Личный баланс/статистика сотрудника ✓
- [ ] Возможность выгрузки в различных форматах (JSON, CSV) ✓
- [ ] Отправка заказов напрямую в кафе (через Telegram) ✓
- [ ] Умные подсказки и рекомендации (Gemini API) ✓

## Контекст

### Стек технологий

**Backend:**
- Python 3.13, FastAPI, PostgreSQL 17, SQLAlchemy (async)
- Kafka (FastStream), Redis
- Gemini API (google-genai), Telegram Bot API (aiogram)

**Frontend:**
- Next.js 16, React 19, Tailwind CSS 4, TypeScript

**Testing:**
- pytest (backend unit/integration)
- Jest + React Testing Library (frontend unit)
- Playwright (E2E) с MCP tools

**Infrastructure:**
- Docker Compose
- PostgreSQL, Kafka, Zookeeper, Redis

### Playwright MCP Tools

Используются специализированные MCP tools для Playwright тестирования:

**Доступные tools:**
- `mcp__playwright-test__planner_setup_page` - Setup page for test planning
- `mcp__playwright-test__planner_save_plan` - Save test plan
- `mcp__playwright-test__planner_submit_plan` - Submit test plan
- `mcp__playwright-test__generator_setup_page` - Setup page for test generation
- `mcp__playwright-test__generator_write_test` - Write generated test to file
- `mcp__playwright-test__test_run` - Run Playwright tests
- `mcp__playwright-test__test_debug` - Debug single test
- `mcp__playwright-test__browser_*` - Browser automation (navigate, click, fill, verify, etc.)

**Playwright Агенты:**
Используй агенты из `.claude/agents/`:
1. `playwright-test-planner.md` - создание comprehensive test plan
2. `playwright-test-generator.md` - генерация автотестов
3. `playwright-test-healer.md` - дебаг и фикс падающих тестов

### Архитектура системы

```
┌─────────────────────────────────────────────────────────────────┐
│                      Telegram Mini App                           │
│                  (Next.js 16 + React 19)                          │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTPS/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API                                 │
│                  (FastAPI + PostgreSQL)                           │
│                                                                   │
│  /auth/telegram → JWT                                            │
│  /cafes, /menu, /orders → CRUD                                   │
│  /users/{tgid}/recommendations → Redis cache                     │
│  /cafe-requests → Manager approval                               │
└─────┬───────────────────────┬──────────────────────┬────────────┘
      │                       │                      │
      ▼                       ▼                      ▼
┌──────────┐          ┌──────────────┐      ┌──────────────┐
│PostgreSQL│          │  Kafka       │      │  Redis       │
│  17      │          │  (Events)    │      │  (Cache)     │
└──────────┘          └──────┬───────┘      └──────────────┘
                             │
                   ┌─────────┴──────────┐
                   ▼                    ▼
         ┌──────────────────┐   ┌──────────────────┐
         │ Notifications    │   │ Recommendations  │
         │ Worker           │   │ Worker           │
         │ (Telegram Bot)   │   │ (Gemini API)     │
         └─────────┬────────┘   └────────┬─────────┘
                   │                     │
                   ▼                     ▼
         ┌──────────────────┐   ┌──────────────────┐
         │ Cafe Telegram    │   │ Gemini API       │
         │ Chats            │   │ Key Pool (1-N)   │
         └──────────────────┘   └──────────────────┘
```

## Подзадачи для Architect

Architect должен разбить эту задачу на модули:

### Фаза 1: Интеграция
1. Frontend → Backend подключение (замена mock на реальные API)
2. Telegram Bot → Backend (заявки от кафе)
3. Workers → Kafka → Backend (полный цикл уведомлений)
4. Gemini API key pool тестирование

### Фаза 2: E2E тестирование
5. **Playwright test planning** (через MCP tool: planner_setup_page + planner_submit_plan)
6. **Playwright test generation** (через MCP tool: generator_setup_page + generator_write_test)
7. **Playwright test execution** (test_run)
8. **Test healing** (test_debug + фиксы)
9. Integration тесты (полный флоу)

### Фаза 3: Документация
10. User guides (сотрудники, кафе, менеджеры)
11. Technical docs (API, Architecture, Deployment)
12. Troubleshooting guide

### Фаза 4: Production Deployment
13. Production конфигурация (.env, Docker)
14. Monitoring и logging
15. Security hardening
16. Performance optimization

### Фаза 5: Acceptance Testing
17. Manual testing checklist
18. User acceptance testing
19. Performance testing (load/stress)

### Фаза 6: CI/CD (опционально)
20. GitHub Actions setup
21. Automated deployment

**Рекомендация:**
- Фазы 1-2 критичны, выполнять последовательно
- Фаза 3 можно параллелить (разные документы)
- Фазы 4-5 зависят от результатов тестирования
- Фаза 6 опциональна (можно отложить на потом)

## Ожидаемый результат

Полностью функциональная, протестированная и готовая к деплою система:

1. **Работает end-to-end:**
   - Пользователь создает заказ через Telegram Mini App
   - Заказ сохраняется в PostgreSQL
   - После дедлайна кафе получает уведомление в Telegram
   - Ночью генерируются рекомендации для активных пользователей
   - Рекомендации отображаются в профиле

2. **Протестирована:**
   - E2E тесты (Playwright) покрывают основные user flows
   - Integration тесты проверяют взаимодействие компонентов
   - Manual testing подтверждает работоспособность

3. **Задокументирована:**
   - Понятные инструкции для пользователей всех ролей
   - Техническая документация для разработчиков
   - Troubleshooting guide для админов

4. **Готова к деплою:**
   - Production конфигурация
   - Docker Compose для простого разворачивания
   - Мониторинг и логирование
   - Backup стратегия

5. **Все бизнес-требования выполнены:**
   - Обязательные функции для сотрудников ✓
   - Обязательные функции для менеджеров ✓
   - Необязательные функции ✓

## Связь с другими задачами

- **TSK-001**: Frontend готов, будет интегрирован с backend
- **TSK-002**: Backend API готов, будет протестирован end-to-end
- **TSK-003**: Kafka/Redis/Gemini готовы, будут протестированы в связке
- **Зависимости**: TSK-004 требует завершения TSK-001, TSK-002, TSK-003

## Примечания

- Это финальная задача проекта, после которой система будет готова к использованию
- Основной фокус - интеграция и тестирование, а не новые функции
- Критично использовать Playwright MCP tools для E2E тестов (не писать тесты вручную)
- Документация должна быть понятна как техническим, так и нетехническим пользователям
- Production деплой должен быть максимально простым (Docker Compose + .env)
- После завершения TSK-004 проект считается MVP (Minimum Viable Product)

## Приоритет

**Critical:**
- Frontend ↔ Backend интеграция
- E2E тестирование (Playwright)
- Production конфигурация

**High:**
- Workers тестирование
- User documentation
- Deployment guide

**Medium:**
- Monitoring и logging
- Performance optimization
- Technical documentation

**Low:**
- CI/CD pipeline (можно отложить на post-MVP)
- Advanced monitoring (можно добавить позже)
