---
agent: architect
task_id: TSK-004
status: completed
next: coder
created_at: 2025-12-06T14:00:00
---

## Анализ

TSK-004 — финальная задача проекта, которая интегрирует все ранее реализованные компоненты в единую работающую систему, проводит комплексное E2E тестирование и готовит проект к production deployment.

### Текущее состояние компонентов

**Backend (TSK-002, TSK-003) - Полностью реализован:**
- ✅ FastAPI REST API с 9 роутерами
- ✅ PostgreSQL 17 + SQLAlchemy (async) + Alembic миграции
- ✅ JWT авторизация через Telegram WebApp
- ✅ RBAC (user, manager)
- ✅ Все endpoints согласно API spec (`.memory-base/tech-docs/api.md`)
- ✅ Kafka integration (FastStream)
- ✅ Redis caching
- ✅ Gemini API с пулом ключей (до 195 req/key с ротацией)
- ✅ Telegram Bot для приема заявок от кафе
- ✅ Workers: notifications, recommendations
- ✅ Unit тесты (pytest) с покрытием

**Frontend (TSK-001) - Полностью реализован:**
- ✅ Next.js 16 + React 19 + Tailwind CSS 4
- ✅ Telegram WebApp SDK интеграция
- ✅ API client (`src/lib/api/client.ts`) с JWT
- ✅ SWR hooks для data fetching
- ✅ Компоненты: CafeSelector, ComboSelector, MenuSection, ExtrasSection
- ✅ Unit тесты (Jest + React Testing Library) - 66 тестов

**Infrastructure (TSK-003) - Реализован:**
- ✅ Docker Compose с сервисами: PostgreSQL, Kafka, Redis, Backend, Telegram Bot, Workers
- ✅ Health checks для всех сервисов
- ✅ Environment variables настроены

### Выявленные проблемы интеграции

#### 1. Frontend ↔ Backend разрыв
**Проблема:** Frontend использует **mock данные** в `page.tsx`:
```typescript
const cafes = Array.from({ length: 12 }).map((_, i) => ({ id: i + 1, name: `кафе ${i + 1}` }));
const dishes = [/* hardcoded */];
```

**Решение:**
- Заменить mock данные на реальные API calls
- Использовать SWR hooks (`useCafes`, `useCombos`, `useMenu`)
- Настроить `NEXT_PUBLIC_API_URL` в `.env`
- Проверить CORS в backend (`CORS_ORIGINS`)

#### 2. Frontend не включен в Docker Compose
**Проблема:** Docker Compose содержит только backend сервисы. Frontend отсутствует.

**Решение:**
- Добавить `frontend` service в `docker-compose.yml`
- Настроить build из `frontend_mini_app/`
- Настроить environment variables (`NEXT_PUBLIC_API_URL`)
- Настроить port mapping (3000:3000)

#### 3. CORS конфигурация
**Проблема:** Backend CORS настроен только на `http://localhost:3000`.

**Решение:**
- Для development: добавить Docker hostname (например, `http://frontend:3000`)
- Для production: настроить домен через `.env`

#### 4. Отсутствует E2E тестирование
**Проблема:** Нет E2E тестов для проверки полного user flow.

**Решение:**
- Использовать Playwright MCP tools
- Создать test plan через `playwright-test-planner` агента
- Сгенерировать автотесты через `playwright-test-generator` агента
- Настроить Playwright config (`playwright.config.ts`)

#### 5. Нет production-ready конфигурации
**Проблема:** `.env.example` содержит dev defaults, нет production guide.

**Решение:**
- Создать production `.env` пример
- Документировать secrets management
- Настроить multi-stage Dockerfile для оптимизации
- Добавить health check endpoints

#### 6. Отсутствует документация по deployment
**Проблема:** Нет инструкций для деплоя системы.

**Решение:**
- Создать deployment guide
- Документировать Docker Compose setup
- Описать database migrations
- Troubleshooting guide

## Архитектурное решение

### Принцип интеграции

Используем **поэтапный подход** с постепенной интеграцией и тестированием каждого слоя:

```
Фаза 1: Frontend ↔ Backend Integration
  ├─> Замена mock данных на API calls
  ├─> CORS настройка
  ├─> Docker Compose для frontend
  └─> Проверка базового флоу (авторизация → заказ)

Фаза 2: E2E Testing (Playwright)
  ├─> Test planning (через MCP tool)
  ├─> Test generation (через MCP tool)
  ├─> Test execution
  └─> Test healing (фикс падающих тестов)

Фаза 3: Integration Testing
  ├─> Kafka workers тестирование
  ├─> Gemini API key pool в реальных условиях
  └─> Полный флоу: заказ → deadline → уведомление

Фаза 4: Production Configuration
  ├─> Environment variables для production
  ├─> Multi-stage Dockerfiles
  ├─> Health checks и monitoring
  └─> Security hardening

Фаза 5: Documentation
  ├─> User guides (сотрудники, менеджеры, кафе)
  ├─> Deployment guide
  ├─> API documentation
  └─> Troubleshooting guide

Фаза 6: Final Acceptance Testing
  ├─> Manual testing checklist
  ├─> Performance testing
  └─> User acceptance criteria
```

### Изменения в данных

**Не требуется.** Все таблицы и схемы уже реализованы в TSK-002 и TSK-003.

### API изменения

**Не требуется.** Все endpoints уже реализованы. Необходимо только:
- Проверить Swagger документацию (`/docs`)
- Добавить health check endpoints (если отсутствуют)

### Новые компоненты

1. **Playwright Test Suite** (E2E)
   - Location: `frontend_mini_app/tests/e2e/`
   - Config: `frontend_mini_app/playwright.config.ts`

2. **Production Docker Compose**
   - Location: `docker-compose.prod.yml`
   - Отличия от dev: без volumes для кода, оптимизированные образы

3. **Deployment Documentation**
   - Location: `.memory-base/docs/deployment/`
   - User guides, admin guides, troubleshooting

## Подзадачи для Coder

### Фаза 1: Frontend ↔ Backend Integration

#### 1.1 Подключение Frontend к Backend API
**Файлы для изменения:**
- `frontend_mini_app/src/app/page.tsx`
- `frontend_mini_app/.env.example`

**Действия:**
1. Удалить mock данные (`cafes`, `categories`, `dishes`)
2. Использовать SWR hooks:
   - `useCafes(true)` → получить список кафе
   - `useCombos(selectedCafe?.id)` → получить комбо для кафе
   - `useMenu(selectedCafe?.id)` → получить menu items
   - `useMenu(selectedCafe?.id, "extra")` → получить extras
3. Обновить state management для работы с реальными данными
4. Добавить loading states и error handling
5. Настроить `.env.example`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

**Зависимости:** Backend API должен быть запущен и доступен

#### 1.2 CORS Configuration
**Файлы для изменения:**
- `backend/.env.example`
- `backend/src/config.py` (если CORS origins hardcoded)

**Действия:**
1. Обновить `CORS_ORIGINS` в `.env.example`:
   ```
   # Development
   CORS_ORIGINS=["http://localhost:3000","http://frontend:3000"]

   # Production (example)
   CORS_ORIGINS=["https://yourdomain.com"]
   ```
2. Проверить что backend читает CORS_ORIGINS из env
3. Добавить комментарии с примерами

**Зависимости:** Нет

#### 1.3 Docker Compose для Frontend
**Файлы для изменения:**
- `docker-compose.yml`
- `frontend_mini_app/Dockerfile` (создать)
- `frontend_mini_app/.dockerignore` (создать)

**Действия:**
1. Создать `frontend_mini_app/Dockerfile`:
   ```dockerfile
   FROM node:20-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   ARG NEXT_PUBLIC_API_URL
   ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
   RUN npm run build

   FROM node:20-alpine
   WORKDIR /app
   COPY --from=builder /app/.next ./.next
   COPY --from=builder /app/node_modules ./node_modules
   COPY --from=builder /app/package.json ./package.json
   EXPOSE 3000
   CMD ["npm", "start"]
   ```

2. Создать `frontend_mini_app/.dockerignore`:
   ```
   node_modules
   .next
   .git
   .env.local
   ```

3. Добавить `frontend` service в `docker-compose.yml`:
   ```yaml
   frontend:
     build:
       context: ./frontend_mini_app
       dockerfile: Dockerfile
       args:
         NEXT_PUBLIC_API_URL: http://backend:8000/api/v1
     container_name: lunch-bot-frontend
     depends_on:
       - backend
     ports:
       - "3000:3000"
     environment:
       NEXT_PUBLIC_API_URL: http://backend:8000/api/v1
     volumes:
       - ./frontend_mini_app:/app  # dev mode only
       - /app/node_modules
   ```

**Зависимости:** 1.2 (CORS)

#### 1.4 Интеграционный тест: полный флоу заказа
**Файлы для изменения:**
- `backend/tests/integration/test_full_order_flow.py` (создать)

**Действия:**
1. Создать тест, который проверяет:
   - Авторизация через Telegram initData
   - Получение списка кафе
   - Получение комбо и меню для кафе
   - Создание заказа
   - Проверка что заказ сохранен в БД
2. Использовать pytest fixtures для тестовых данных
3. Проверить error cases (deadline passed, invalid combo)

**Зависимости:** 1.1, 1.2, 1.3

### Фаза 2: E2E Testing (Playwright)

#### 2.1 Настройка Playwright
**Файлы для создания:**
- `frontend_mini_app/playwright.config.ts`
- `frontend_mini_app/tests/e2e/.gitkeep`
- `frontend_mini_app/package.json` (update)

**Действия:**
1. Добавить зависимости в `package.json`:
   ```json
   "devDependencies": {
     "@playwright/test": "^1.40.0"
   }
   ```

2. Создать `playwright.config.ts`:
   ```typescript
   import { defineConfig, devices } from '@playwright/test';

   export default defineConfig({
     testDir: './tests/e2e',
     fullyParallel: true,
     forbidOnly: !!process.env.CI,
     retries: process.env.CI ? 2 : 0,
     workers: process.env.CI ? 1 : undefined,
     reporter: 'html',
     use: {
       baseURL: 'http://localhost:3000',
       trace: 'on-first-retry',
     },
     projects: [
       {
         name: 'chromium',
         use: { ...devices['Desktop Chrome'] },
       },
     ],
     webServer: {
       command: 'npm run dev',
       url: 'http://localhost:3000',
       reuseExistingServer: !process.env.CI,
     },
   });
   ```

3. Добавить scripts в `package.json`:
   ```json
   "scripts": {
     "test:e2e": "playwright test",
     "test:e2e:ui": "playwright test --ui",
     "test:e2e:report": "playwright show-report"
   }
   ```

**Зависимости:** Нет

#### 2.2 E2E Test Planning (через Playwright MCP Agent)
**Используемый агент:** `playwright-test-planner`

**Действия:**
1. Supervisor запускает playwright-test-planner субагент через Task tool
2. Субагент использует Playwright MCP tools:
   - `mcp__playwright-test__planner_setup_page` - настройка страницы
   - `mcp__playwright-test__browser_snapshot` - исследование интерфейса
   - `mcp__playwright-test__planner_submit_plan` - создание test plan
3. Результат: comprehensive test plan в формате markdown

**Test scenarios (примеры):**
- User authentication via Telegram WebApp
- Cafe selection
- Combo selection
- Menu item selection for each category
- Extras addition
- Order submission
- Order history view
- Manager: approve cafe request
- Manager: create summary report

**Зависимости:** 2.1, Frontend и Backend должны быть запущены

#### 2.3 E2E Test Generation (через Playwright MCP Agent)
**Используемый агент:** `playwright-test-generator`

**Действия:**
1. Supervisor запускает playwright-test-generator субагент через Task tool
2. Субагент читает test plan из 2.2
3. Субагент использует Playwright MCP tools для генерации тестов:
   - `mcp__playwright-test__generator_setup_page` - настройка страницы
   - `mcp__playwright-test__browser_navigate` - навигация
   - `mcp__playwright-test__browser_click` - клики
   - `mcp__playwright-test__browser_fill_form` - заполнение форм
   - `mcp__playwright-test__browser_verify_*` - assertions
   - `mcp__playwright-test__generator_write_test` - сохранение теста
4. Результат: автоматически сгенерированные test specs в `tests/e2e/*.spec.ts`

**Зависимости:** 2.2

#### 2.4 E2E Test Execution & Healing
**Используемый агент (при необходимости):** `playwright-test-healer`

**Действия:**
1. Запустить тесты: `npm run test:e2e`
2. Если тесты падают:
   - Supervisor запускает playwright-test-healer субагент
   - Субагент анализирует failures через `mcp__playwright-test__test_debug`
   - Субагент исправляет селекторы, timing, assertions
   - Субагент обновляет test files
3. Повторить до 100% pass rate

**Результат:**
- Все E2E тесты проходят
- Test report сгенерирован
- Coverage основных user flows

**Зависимости:** 2.3

### Фаза 3: Integration Testing

#### 3.1 Kafka Workers Integration Test
**Файлы для создания:**
- `backend/tests/integration/test_kafka_notifications.py`
- `backend/tests/integration/test_kafka_recommendations.py`

**Действия:**
1. **Notifications Worker Test:**
   - Создать тестовые данные: кафе, заказы, deadline прошел
   - Отправить Kafka event `deadline.passed`
   - Проверить что worker обработал событие
   - Проверить что уведомление отправлено (mock Telegram Bot API)

2. **Recommendations Worker Test:**
   - Создать тестового пользователя с историей заказов
   - Запустить recommendations worker вручную
   - Проверить что данные отправлены в Gemini API (mock)
   - Проверить что результат сохранен в Redis
   - Проверить TTL = 24h

**Зависимости:** Kafka и Redis должны быть запущены

#### 3.2 Gemini API Key Pool Test
**Файлы для изменения:**
- `backend/tests/unit/gemini/test_key_pool.py` (уже существует, расширить)

**Действия:**
1. Расширить существующие unit тесты для проверки:
   - Ротация после 195 запросов
   - Fallback при rate limit (429)
   - Пропуск invalid keys (401)
   - Персистентность счетчиков в Redis
2. Создать integration test:
   - Сделать 200 реальных запросов к Gemini API
   - Проверить автоматическую ротацию ключей
   - Проверить что счетчики обновляются в Redis

**Зависимости:** Redis, реальные Gemini API keys (для integration теста)

#### 3.3 End-to-End Flow Test
**Файлы для создания:**
- `backend/tests/integration/test_e2e_order_flow.py`

**Действия:**
1. Создать комплексный тест полного цикла:
   ```
   User создает заказ
     → Заказ сохраняется в PostgreSQL
     → Deadline наступает
     → Kafka event генерируется
     → Notifications worker обрабатывает
     → Уведомление отправляется в Telegram (mock)
   ```

2. Проверить:
   - Все промежуточные состояния
   - Error handling на каждом этапе
   - Rollback при ошибках

**Зависимости:** 3.1, Kafka, PostgreSQL

### Фаза 4: Production Configuration

#### 4.1 Environment Variables для Production
**Файлы для изменения:**
- `backend/.env.example`
- `frontend_mini_app/.env.example`
- `.memory-base/docs/deployment/environment.md` (создать)

**Действия:**
1. Обновить `backend/.env.example` с production примерами:
   ```bash
   # Production PostgreSQL
   DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/lunch_bot

   # Production JWT (MUST CHANGE!)
   JWT_SECRET_KEY=CHANGE_THIS_IN_PRODUCTION_TO_RANDOM_STRING

   # Production CORS
   CORS_ORIGINS=["https://yourdomain.com"]

   # Gemini API Keys (comma-separated)
   GEMINI_API_KEYS=key1,key2,key3

   # Telegram Bot
   TELEGRAM_BOT_TOKEN=your_production_token
   ```

2. Создать документацию по secrets management
3. Добавить предупреждения о безопасности

**Зависимости:** Нет

#### 4.2 Multi-Stage Dockerfiles
**Файлы для создания/изменения:**
- `backend/Dockerfile` (проверить что уже multi-stage)
- `frontend_mini_app/Dockerfile` (уже создан в 1.3, оптимизировать)

**Действия:**
1. Проверить `backend/Dockerfile`:
   - Builder stage (установка зависимостей)
   - Runtime stage (только необходимое)
   - Минимизация размера образа

2. Оптимизировать `frontend_mini_app/Dockerfile`:
   - Использовать `.next/standalone` для меньшего размера
   - Удалить dev dependencies
   - Настроить caching слоев

**Зависимости:** Нет

#### 4.3 Health Check Endpoints
**Файлы для изменения:**
- `backend/src/main.py`

**Действия:**
1. Добавить health check endpoints (если отсутствуют):
   ```python
   @app.get("/health")
   async def health():
       return {"status": "ok"}

   @app.get("/health/db")
   async def health_db():
       # Check PostgreSQL connection
       ...

   @app.get("/health/redis")
   async def health_redis():
       # Check Redis connection
       ...

   @app.get("/health/kafka")
   async def health_kafka():
       # Check Kafka connection
       ...
   ```

2. Обновить Docker Compose health checks для использования этих endpoints

**Зависимости:** Нет

#### 4.4 Production Docker Compose
**Файлы для создания:**
- `docker-compose.prod.yml`

**Действия:**
1. Создать production версию Docker Compose:
   - Без volumes для кода (используется image)
   - Resource limits (CPU, memory)
   - Restart policies: always
   - Networks для изоляции
   - Secrets через environment files

2. Пример структуры:
   ```yaml
   services:
     postgres:
       image: postgres:17-alpine
       restart: always
       deploy:
         resources:
           limits:
             cpus: '1'
             memory: 1G

     backend:
       build: ./backend
       restart: always
       depends_on:
         - postgres
       env_file:
         - .env.production
       # NO volumes for code
   ```

**Зависимости:** 4.1, 4.2

#### 4.5 Security Hardening
**Файлы для изменения:**
- `backend/src/main.py`
- `backend/src/config.py`

**Действия:**
1. Добавить rate limiting для API endpoints:
   - Использовать `slowapi` или custom middleware
   - Лимиты: 100 req/min для authenticated, 10 req/min для auth endpoint

2. Проверить input validation:
   - Все Pydantic схемы имеют правильные constraints
   - SQL injection защита (SQLAlchemy ORM)

3. Проверить secrets:
   - Нет hardcoded токенов/ключей
   - `.env` в `.gitignore`

4. Настроить HTTPS (документация):
   - Reverse proxy (nginx/traefik)
   - SSL certificates (Let's Encrypt)

**Зависимости:** Нет

#### 4.6 Performance Optimization
**Файлы для изменения:**
- Backend migration files (добавить индексы)
- `backend/src/database.py` (connection pooling)

**Действия:**
1. Добавить database индексы (если отсутствуют):
   ```sql
   CREATE INDEX idx_orders_user_date ON orders(user_tgid, order_date);
   CREATE INDEX idx_orders_cafe_date ON orders(cafe_id, order_date);
   CREATE INDEX idx_menu_items_cafe_category ON menu_items(cafe_id, category);
   ```

2. Проверить connection pooling настроен:
   ```python
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=10,
       max_overflow=20
   )
   ```

3. Настроить Redis TTL для кэширования (уже должно быть в TSK-003)

**Зависимости:** Нет

### Фаза 5: Documentation

#### 5.1 User Guides
**Файлы для создания:**
- `.memory-base/docs/user-guides/employee.md`
- `.memory-base/docs/user-guides/cafe.md`
- `.memory-base/docs/user-guides/manager.md`

**Действия:**
1. **Employee Guide** (для сотрудников):
   - Как открыть Telegram Mini App
   - Как выбрать кафе и сделать заказ
   - Как изменить заказ (до дедлайна)
   - Как посмотреть историю заказов
   - Как посмотреть рекомендации
   - FAQ (частые вопросы)

2. **Cafe Guide** (для кафе):
   - Как подключить кафе через Telegram бота
   - Формат уведомлений
   - Что делать при проблемах
   - Контакты для поддержки

3. **Manager Guide** (для менеджеров):
   - Как добавить пользователей
   - Как управлять меню кафе
   - Как настроить deadlines
   - Как получить отчет
   - Как одобрить заявку от кафе
   - Как настроить уведомления

**Зависимости:** Нет

#### 5.2 Deployment Guide
**Файлы для создания:**
- `.memory-base/docs/deployment/quick-start.md`
- `.memory-base/docs/deployment/production.md`
- `.memory-base/docs/deployment/environment.md` (уже в 4.1)

**Действия:**
1. **Quick Start Guide:**
   ```markdown
   # Quick Start

   ## Prerequisites
   - Docker & Docker Compose
   - Node.js 20+ (for local frontend development)
   - Python 3.13+ (for local backend development)

   ## Development Setup
   1. Clone repository
   2. Copy .env.example to .env
   3. Run `docker-compose up -d`
   4. Run migrations: `docker exec backend alembic upgrade head`
   5. Access frontend: http://localhost:3000

   ## Production Setup
   See production.md
   ```

2. **Production Guide:**
   - Server requirements
   - Docker Compose production setup
   - Database migrations
   - SSL/HTTPS setup (nginx example)
   - Backup strategy
   - Monitoring setup

**Зависимости:** 4.4 (Production Docker Compose)

#### 5.3 API Documentation
**Файлы для проверки/обновления:**
- `.memory-base/tech-docs/api.md` (уже существует)
- Backend Swagger (`/docs` endpoint)

**Действия:**
1. Проверить что все endpoints в Swagger имеют:
   - Описание
   - Примеры request/response
   - Коды ошибок

2. Обновить `.memory-base/tech-docs/api.md` если были изменения

3. Добавить примеры curl запросов для каждого endpoint

**Зависимости:** Нет

#### 5.4 Troubleshooting Guide
**Файлы для создания:**
- `.memory-base/docs/troubleshooting.md`

**Действия:**
1. Создать guide с разделами:
   - **Common Issues:**
     - Frontend не подключается к backend (CORS)
     - Database connection failed
     - Kafka worker не запускается
     - Gemini API key exhausted
   - **Debug Commands:**
     - Проверка логов: `docker logs <container>`
     - Проверка health: `curl http://localhost:8000/health`
     - Проверка Redis: `redis-cli ping`
     - Проверка Kafka topics
   - **Monitoring:**
     - Kafka consumer lag
     - Redis memory usage
     - API response time
     - Gemini API key usage

**Зависимости:** Нет

#### 5.5 README Update
**Файлы для изменения:**
- `README.md` (корень проекта, создать если отсутствует)

**Действия:**
1. Создать comprehensive README:
   ```markdown
   # Lunch Order Telegram Bot

   ## Overview
   Telegram Mini App для предварительного заказа обедов в офисе.

   ## Features
   - Telegram WebApp авторизация
   - Заказ комбо-наборов обедов
   - Telegram уведомления для кафе
   - AI рекомендации (Gemini API)
   - Отчеты для менеджеров

   ## Tech Stack
   - Backend: Python 3.13, FastAPI, PostgreSQL 17
   - Frontend: Next.js 16, React 19, Tailwind CSS 4
   - Messaging: Kafka
   - Caching: Redis
   - AI: Google Gemini API

   ## Architecture
   [Diagram from .memory-base/tech-docs/image.png]

   ## Quick Start
   See docs/deployment/quick-start.md

   ## Documentation
   - [API Specification](.memory-base/tech-docs/api.md)
   - [User Guides](.memory-base/docs/user-guides/)
   - [Deployment](.memory-base/docs/deployment/)
   - [Troubleshooting](.memory-base/docs/troubleshooting.md)

   ## Testing
   - Backend: `pytest`
   - Frontend: `npm test`
   - E2E: `npm run test:e2e`

   ## License
   ...
   ```

**Зависимости:** 5.1, 5.2, 5.4

### Фаза 6: Final Acceptance Testing

#### 6.1 Manual Testing Checklist
**Файлы для создания:**
- `.memory-base/docs/testing/manual-checklist.md`

**Действия:**
1. Создать comprehensive manual testing checklist:
   - [ ] Создать тестовых пользователей (user, manager)
   - [ ] Создать тестовое кафе с меню и комбо
   - [ ] Настроить deadlines
   - [ ] Сделать заказ через Telegram Mini App
   - [ ] Проверить что заказ сохранен в БД
   - [ ] Изменить заказ до дедлайна
   - [ ] Попробовать изменить после дедлайна (должна быть ошибка)
   - [ ] Дождаться deadline → проверить Kafka event
   - [ ] Проверить что кафе получило уведомление
   - [ ] Проверить генерацию рекомендаций (запустить worker)
   - [ ] Проверить отображение рекомендаций в профиле
   - [ ] Создать отчет через manager API
   - [ ] Экспортировать отчет (JSON, CSV)
   - [ ] Проверить cafe link request flow (бот → API → approval)

**Зависимости:** Все компоненты должны быть интегрированы

#### 6.2 Performance Testing
**Файлы для создания:**
- `backend/tests/performance/test_load.py` (опционально)

**Действия:**
1. Создать простой load test (опционально, можно использовать `locust` или `k6`):
   - Симулировать 100 одновременных пользователей
   - Создание заказов
   - Получение меню
   - Проверить response time < 500ms
   - Проверить нет errors

2. Проверить Gemini API key pool под нагрузкой:
   - 300 запросов подряд
   - Проверить автоматическую ротацию ключей
   - Проверить нет fallback errors

**Зависимости:** 3.2, все компоненты интегрированы

#### 6.3 User Acceptance Testing
**Файлы для создания:**
- `.memory-base/docs/testing/acceptance-report.md`

**Действия:**
1. Пройти все User Acceptance Criteria из task.md:
   - Сотрудник: авторизация, просмотр меню, заказ, управление заказом
   - Менеджер: загрузка пользователей, управление меню/сроками, отчеты
   - Необязательные: баланс, выгрузка форматов, уведомления кафе, рекомендации

2. Создать acceptance report с результатами

**Зависимости:** 6.1 (Manual Testing)

## Риски и зависимости

### Риски

1. **E2E тесты могут быть нестабильными (flaky)**
   - Решение: Использовать Playwright MCP tools для генерации и healing
   - Решение: Добавить retry logic в playwright.config.ts

2. **Frontend может не работать в Docker из-за SSR/Telegram SDK**
   - Решение: Проверить что Telegram SDK работает корректно в production build
   - Решение: Добавить fallback для development mode

3. **Kafka/Redis могут не стартовать вовремя в Docker Compose**
   - Решение: Используются health checks и `depends_on` с `condition: service_healthy`

4. **Gemini API keys могут быстро исчерпаться при testing**
   - Решение: Использовать mock для большинства тестов
   - Решение: Integration тесты только с реальными ключами

### Зависимости между подзадачами

**Критический путь (последовательные задачи):**
```
1.1 → 1.2 → 1.3 → 1.4 (Frontend Integration)
  ↓
2.1 → 2.2 → 2.3 → 2.4 (E2E Testing)
  ↓
3.1, 3.2, 3.3 (Integration Testing) — можно параллельно
  ↓
6.1 → 6.2 → 6.3 (Acceptance Testing)
```

**Параллельные задачи:**
- Фаза 4 (Production Config) — можно делать параллельно с Фазой 2-3
- Фаза 5 (Documentation) — можно делать параллельно с Фазой 3-4

### Рекомендация по параллельному выполнению

**Параллелизация для Coder субагентов:**

**Batch 1 (Frontend Integration):**
- Coder 1: Frontend API integration (1.1)
- Coder 2: CORS config (1.2)
- Coder 3: Docker Compose frontend (1.3)

**Batch 2 (Production Config — параллельно с Batch 3):**
- Coder 1: Environment variables + security (4.1, 4.5)
- Coder 2: Dockerfiles optimization (4.2)
- Coder 3: Health checks + performance (4.3, 4.6)

**Batch 3 (Integration Testing):**
- Coder 1: Kafka workers tests (3.1)
- Coder 2: Gemini key pool tests (3.2)
- Coder 3: E2E flow test (3.3)

**Batch 4 (Documentation):**
- Coder 1: User guides (5.1)
- Coder 2: Deployment guides (5.2)
- Coder 3: API docs + troubleshooting (5.3, 5.4, 5.5)

## Итоговая архитектура после интеграции

```
┌─────────────────────────────────────────────────────────────────┐
│                  Telegram Mini App (Frontend)                    │
│                 Next.js 16 + React 19 (Port 3000)                │
│                                                                   │
│  Components:                                                      │
│  - CafeSelector (real API data)                                  │
│  - ComboSelector (real API data)                                 │
│  - MenuSection (real API data)                                   │
│  - ExtrasSection (real API data)                                 │
│  - RecommendationsCard (Gemini AI)                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST (CORS configured)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│                         Port 8000                                │
│                                                                   │
│  Routers:                                                         │
│  - /auth/telegram → JWT                                          │
│  - /cafes, /menu, /combos → CRUD                                 │
│  - /orders → Create/Update/Delete (deadline check)               │
│  - /users/{tgid}/recommendations → Redis cache                   │
│  - /cafe-requests → Manager approval                             │
│  - /summaries → Reports (JSON/CSV export)                        │
│                                                                   │
│  Health Checks:                                                   │
│  - /health, /health/db, /health/redis, /health/kafka            │
└───────┬──────────────┬──────────────────┬─────────────┬─────────┘
        │              │                  │             │
        ▼              ▼                  ▼             ▼
   ┌────────┐   ┌───────────┐      ┌─────────┐   ┌─────────┐
   │Postgre │   │  Kafka    │      │  Redis  │   │ Telegram│
   │SQL 17  │   │  (Events) │      │ (Cache) │   │   Bot   │
   └────────┘   └─────┬─────┘      └─────────┘   └─────────┘
                      │                  ▲             ▲
                      │                  │             │
        ┌─────────────┴────────┐         │             │
        ▼                      ▼         │             │
   ┌────────────┐        ┌───────────────┴──┐          │
   │Notifications│        │Recommendations   │          │
   │  Worker    │        │   Worker         │          │
   │(after      │        │(nightly 03:00)   │          │
   │ deadline)  │        │                  │          │
   └──────┬─────┘        └────────┬─────────┘          │
          │                       │                    │
          │                       ▼                    │
          │                  ┌──────────────┐          │
          │                  │ Gemini API   │          │
          │                  │ Key Pool     │          │
          │                  │ (195 req/key)│          │
          │                  └──────────────┘          │
          │                                            │
          └────────────────────────────────────────────┘
                     (Telegram Bot API)
```

## Следующие шаги

После завершения архитектурного проектирования, Supervisor должен запустить Coder субагенты для выполнения подзадач.

**Рекомендуемый порядок:**
1. Начать с Batch 1 (Frontend Integration) — критический путь
2. После завершения Batch 1 → запустить 2.1 (Playwright Setup)
3. Параллельно с E2E Testing (2.2-2.4) → запустить Batch 2 (Production Config)
4. После E2E Tests → запустить Batch 3 (Integration Testing)
5. Параллельно с Integration Testing → запустить Batch 4 (Documentation)
6. Финал: Manual Testing → Performance Testing → Acceptance Testing

**Критичные подзадачи (блокируют другие):**
- 1.1 Frontend API Integration — без этого нет смысла в E2E тестах
- 2.1 Playwright Setup — без этого нельзя запустить test generation
- 4.1 Environment Variables — нужно для production deployment

**Можно отложить на потом (post-MVP):**
- 6.2 Performance Testing — nice to have, но не критично
- Некоторые части документации (можно дописать после acceptance testing)
