---
id: TSK-002
title: "Реализация Backend API для Lunch Order Bot"
pipeline: feature
status: completed
created_at: 2025-12-06T00:00:00
related_files:
  - backend/
  - .memory-base/tech-docs/api.md
  - .memory-base/tech-docs/stack.md
impact:
  api: true
  db: true
  frontend: false
  services: true
---

## Описание

Реализовать полноценный backend для Telegram-бота заказа обедов. В настоящее время фронтенд (Telegram Mini App) полностью реализован и протестирован (TSK-001), но backend API отсутствует. Необходимо создать все API endpoints согласно спецификации в `.memory-base/tech-docs/api.md`.

## Анализ текущего состояния

### Что уже сделано:
- ✅ Frontend (Telegram Mini App) полностью реализован
- ✅ API Client и интеграция с Telegram WebApp SDK
- ✅ UI компоненты: CafeSelector, ComboSelector, MenuSection, ExtrasSection
- ✅ Тесты фронтенда (66 тестов, все проходят)
- ✅ Документация API (`.memory-base/tech-docs/api.md`)
- ✅ Техническая спецификация

### Что нужно сделать:
- ❌ Backend API endpoints (Python, FastAPI)
- ❌ База данных PostgreSQL + миграции (Alembic)
- ❌ Модели SQLAlchemy
- ❌ Авторизация через Telegram WebApp initData
- ❌ JWT токены
- ❌ Бизнес-логика (deadline checks, order validation)

### Связанные файлы:

| Файл | Назначение |
|------|------------|
| `.memory-base/tech-docs/api.md` | Полная спецификация API |
| `.memory-base/tech-docs/stack.md` | Стек технологий |
| `.memory-base/busness-logic/technical_requirements.md` | Бизнес-требования |
| `frontend_mini_app/` | Готовый фронтенд (для понимания контекста) |

## Acceptance Criteria

### Инфраструктура
- [ ] Создана структура backend проекта (FastAPI, SQLAlchemy, Alembic)
- [ ] Настроено подключение к PostgreSQL
- [ ] Настроена система миграций (Alembic)
- [ ] Добавлены зависимости в pyproject.toml

### База данных
- [ ] Созданы таблицы: users, cafes, combos, menu_items, orders, deadlines, summaries
- [ ] Настроены связи между таблицами
- [ ] Добавлены индексы для оптимизации запросов
- [ ] Созданы миграции

### Модели и схемы
- [ ] SQLAlchemy модели для всех сущностей
- [ ] Pydantic схемы для валидации запросов/ответов
- [ ] TypeScript типы соответствуют API схемам

### Авторизация
- [ ] Endpoint `POST /auth/telegram` работает
- [ ] Валидация Telegram WebApp initData
- [ ] Генерация и проверка JWT токенов
- [ ] Middleware для авторизации
- [ ] Role-based access control (user, manager)

### API Endpoints - Users
- [ ] `GET /users` - список пользователей (manager)
- [ ] `POST /users` - создание пользователя (manager)
- [ ] `POST /users/managers` - создание менеджера (manager)
- [ ] `GET /users/{tgid}` - получение пользователя
- [ ] `DELETE /users/{tgid}` - удаление пользователя (manager)
- [ ] `PATCH /users/{tgid}/access` - управление доступом (manager)
- [ ] `GET /users/{tgid}/balance` - баланс пользователя
- [ ] `PATCH /users/{tgid}/balance/limit` - лимит баланса (manager)

### API Endpoints - Cafes
- [ ] `GET /cafes` - список кафе
- [ ] `POST /cafes` - создание кафе (manager)
- [ ] `GET /cafes/{cafe_id}` - получение кафе
- [ ] `PATCH /cafes/{cafe_id}` - обновление кафе (manager)
- [ ] `DELETE /cafes/{cafe_id}` - удаление кафе (manager)
- [ ] `PATCH /cafes/{cafe_id}/status` - изменение статуса (manager)

### API Endpoints - Menu (Combos & Items)
- [ ] `GET /cafes/{cafe_id}/combos` - список комбо
- [ ] `POST /cafes/{cafe_id}/combos` - создание комбо (manager)
- [ ] `PATCH /cafes/{cafe_id}/combos/{combo_id}` - обновление комбо (manager)
- [ ] `DELETE /cafes/{cafe_id}/combos/{combo_id}` - удаление комбо (manager)
- [ ] `GET /cafes/{cafe_id}/menu` - список блюд
- [ ] `POST /cafes/{cafe_id}/menu` - создание блюда (manager)
- [ ] `GET /cafes/{cafe_id}/menu/{item_id}` - получение блюда
- [ ] `PATCH /cafes/{cafe_id}/menu/{item_id}` - обновление блюда (manager)
- [ ] `DELETE /cafes/{cafe_id}/menu/{item_id}` - удаление блюда (manager)

### API Endpoints - Deadlines
- [ ] `GET /cafes/{cafe_id}/deadlines` - расписание дедлайнов (manager)
- [ ] `PUT /cafes/{cafe_id}/deadlines` - обновление расписания (manager)

### API Endpoints - Orders
- [ ] `GET /orders/availability/{date}` - проверка возможности заказа
- [ ] `GET /orders/availability/week` - доступность на неделю
- [ ] `GET /orders` - список заказов (self/all)
- [ ] `POST /orders` - создание заказа
- [ ] `GET /orders/{order_id}` - получение заказа
- [ ] `PATCH /orders/{order_id}` - обновление заказа (до дедлайна)
- [ ] `DELETE /orders/{order_id}` - удаление заказа (до дедлайна)

### API Endpoints - Summaries (Reports)
- [ ] `GET /summaries` - список отчётов (manager)
- [ ] `POST /summaries` - создание отчёта (manager)
- [ ] `GET /summaries/{summary_id}` - получение отчёта (json/csv/pdf)
- [ ] `DELETE /summaries/{summary_id}` - удаление отчёта (manager)

### Бизнес-логика
- [ ] Проверка deadline перед созданием/изменением заказа
- [ ] Валидация комбо (все категории заполнены)
- [ ] Расчёт total_price (combo + extras)
- [ ] Валидация доступа (owner, manager)
- [ ] Агрегация данных для отчётов

### Тестирование
- [ ] Unit тесты для моделей
- [ ] Integration тесты для API endpoints
- [ ] Тесты авторизации и RBAC
- [ ] Тесты бизнес-логики (deadlines, validation)
- [ ] Coverage >= 80%

### Документация
- [ ] README для backend
- [ ] Инструкции по развёртыванию
- [ ] Конфигурация окружения (.env.example)
- [ ] OpenAPI (Swagger) автодокументация

### Интеграция с фронтендом
- [ ] Backend запускается и отвечает на запросы
- [ ] Frontend может авторизоваться
- [ ] Frontend может создать заказ
- [ ] CORS настроен правильно
- [ ] Все endpoints совместимы с frontend API client

## Контекст

### Стек технологий (Backend)
- Python >= 3.13
- FastAPI >= 0.120.0
- PostgreSQL 17
- SQLAlchemy >= 2.0.44 (async)
- Alembic >= 1.17.0
- Pydantic >= 2.12.0
- asyncpg >= 0.31.0
- uvicorn >= 0.38.0

### Структура базы данных

```
users
  - tgid (PK)
  - name
  - office
  - role (user|manager)
  - is_active
  - weekly_limit
  - created_at

cafes
  - id (PK)
  - name
  - description
  - is_active
  - created_at

combos
  - id (PK)
  - cafe_id (FK)
  - name
  - categories (JSON: ["salad", "soup", "main"])
  - price
  - is_available

menu_items
  - id (PK)
  - cafe_id (FK)
  - name
  - description
  - category (soup|salad|main|extra)
  - price (nullable, только для extra)
  - is_available

deadlines
  - id (PK)
  - cafe_id (FK)
  - weekday (0-6)
  - deadline_time
  - is_enabled
  - advance_days

orders
  - id (PK)
  - user_tgid (FK)
  - cafe_id (FK)
  - order_date
  - status (pending|confirmed|cancelled)
  - combo_id (FK)
  - combo_items (JSON)
  - extras (JSON)
  - notes
  - total_price
  - created_at
  - updated_at

summaries
  - id (PK)
  - cafe_id (FK)
  - date
  - total_orders
  - total_amount
  - breakdown (JSON)
  - created_at
```

## Подзадачи для Architect

Architect должен будет разбить эту задачу на модули:
1. Инфраструктура и подключение к БД
2. Модели и миграции
3. Авторизация (Telegram + JWT)
4. API: Users
5. API: Cafes
6. API: Menu (Combos + Items)
7. API: Deadlines
8. API: Orders
9. API: Summaries
10. Бизнес-логика (deadline checks, validation)
11. Тестирование
12. Документация

Рекомендуется параллельный запуск Coder субагентов для независимых API модулей (Users, Cafes, Menu, Deadlines, Orders, Summaries).

## Ожидаемый результат

Полностью рабочий backend API, который:
- Соответствует спецификации в `.memory-base/tech-docs/api.md`
- Интегрируется с готовым фронтендом без изменений
- Имеет все необходимые endpoints
- Проходит тесты
- Документирован
