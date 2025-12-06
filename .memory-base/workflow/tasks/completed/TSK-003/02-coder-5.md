---
agent: coder
task_id: TSK-003
subtask: 5
subtask_name: "Cafe Link API Endpoints"
status: completed
next: null
created_at: 2025-12-06T15:00:00Z
files_changed:
  - path: backend/src/routers/cafe_links.py
    action: created
  - path: backend/src/services/cafe_link.py
    action: created
  - path: backend/src/repositories/cafe_link.py
    action: created
  - path: backend/src/schemas/cafe_link.py
    action: created
  - path: backend/src/routers/__init__.py
    action: modified
  - path: backend/src/main.py
    action: modified
---

# Coder Report: Cafe Link API Endpoints

## Задача
Подзадача 2.2: Реализация API endpoints для управления привязкой кафе к Telegram.

## Выполненная работа

### 1. Schemas (`backend/src/schemas/cafe_link.py`)

Созданы Pydantic схемы для валидации данных:

- **CreateLinkRequestSchema**: для создания заявки на привязку
  - `tg_chat_id: int` (обязательное)
  - `tg_username: str | None` (опциональное)

- **LinkRequestSchema**: для ответов API
  - Все поля модели CafeLinkRequest
  - Конфигурация `from_attributes=True` для ORM

- **LinkRequestListSchema**: для пагинированного списка
  - `items: list[LinkRequestSchema]`
  - `total: int` - общее количество
  - `skip: int`, `limit: int` - параметры пагинации

- **UpdateNotificationsSchema**: для включения/выключения уведомлений
  - `enabled: bool`

### 2. Repository (`backend/src/repositories/cafe_link.py`)

Реализован слой работы с БД с использованием async SQLAlchemy:

**Методы для CafeLinkRequest:**
- `get_request(request_id)` - получение заявки по ID
- `list_requests(skip, limit, status)` - список заявок с пагинацией и фильтром по статусу
- `create_request(cafe_id, tg_chat_id, tg_username)` - создание новой заявки
- `update_request(request, **kwargs)` - обновление заявки (с whitelist полей)

**Методы для Cafe:**
- `get_cafe(cafe_id)` - получение кафе по ID
- `update_cafe_telegram(cafe, **kwargs)` - обновление Telegram полей (с whitelist)
- `clear_cafe_link(cafe)` - очистка привязки к Telegram

**Безопасность:**
- Whitelist для обновляемых полей:
  - `ALLOWED_UPDATE_FIELDS` для CafeLinkRequest: `status`, `processed_at`
  - `ALLOWED_CAFE_TELEGRAM_FIELDS` для Cafe: `tg_chat_id`, `tg_username`, `linked_at`, `notifications_enabled`

**Пагинация:**
- Используется `func.count()` для получения общего количества записей
- Сортировка по дате создания (DESC) для показа новых заявок сверху

### 3. Service (`backend/src/services/cafe_link.py`)

Реализована бизнес-логика с валидацией:

**Методы:**

1. **create_link_request(cafe_id, data)**
   - Проверка существования кафе
   - Проверка, что кафе не привязано к другому аккаунту
   - Проверка отсутствия pending заявок для этого кафе
   - Создание новой заявки со статусом "pending"

2. **list_requests(skip, limit, status)**
   - Список заявок с пагинацией
   - Фильтрация по статусу (опционально)

3. **get_request(request_id)**
   - Получение заявки с проверкой существования
   - Raise HTTPException 404 если не найдена

4. **approve_request(request_id)**
   - Проверка статуса заявки (должна быть "pending")
   - Проверка, что кафе не привязано к другому аккаунту
   - Обновление Cafe с данными из request:
     - `tg_chat_id`, `tg_username` - из заявки
     - `linked_at` - текущая дата/время
     - `notifications_enabled` - True по умолчанию
   - Обновление статуса заявки на "approved"
   - Установка `processed_at`

5. **reject_request(request_id)**
   - Проверка статуса заявки (должна быть "pending")
   - Обновление статуса на "rejected"
   - Установка `processed_at`

6. **update_notifications(cafe_id, enabled)**
   - Проверка существования кафе
   - Проверка, что кафе привязано к Telegram
   - Обновление флага `notifications_enabled`

7. **unlink_cafe(cafe_id)**
   - Проверка существования кафе
   - Проверка, что кафе привязано к Telegram
   - Очистка всех Telegram полей:
     - `tg_chat_id = None`
     - `tg_username = None`
     - `linked_at = None`
     - `notifications_enabled = True` (сброс на default)

**Обработка ошибок:**
- HTTPException 404 - кафе/заявка не найдена
- HTTPException 400 - некорректное состояние (уже привязано, неверный статус и т.д.)

### 4. Router (`backend/src/routers/cafe_links.py`)

Реализованы FastAPI endpoints согласно спецификации:

**POST /api/v1/cafes/{cafe_id}/link-request**
- **Auth:** Public (для Telegram бота)
- **Body:** CreateLinkRequestSchema
- **Response:** LinkRequestSchema (201)
- Создание заявки на привязку кафе

**GET /api/v1/cafes/cafe-requests**
- **Auth:** Manager
- **Query params:**
  - `skip: int` (default: 0)
  - `limit: int` (default: 100, max: 1000)
  - `status: str | None` (regex: pending|approved|rejected)
- **Response:** LinkRequestListSchema
- Список всех заявок с пагинацией и фильтром

**POST /api/v1/cafes/cafe-requests/{request_id}/approve**
- **Auth:** Manager
- **Response:** LinkRequestSchema
- Одобрение заявки (обновляет Cafe)

**POST /api/v1/cafes/cafe-requests/{request_id}/reject**
- **Auth:** Manager
- **Response:** LinkRequestSchema
- Отклонение заявки

**PATCH /api/v1/cafes/{cafe_id}/notifications**
- **Auth:** Manager
- **Body:** UpdateNotificationsSchema
- **Response:** CafeResponse
- Включение/выключение уведомлений

**DELETE /api/v1/cafes/{cafe_id}/link**
- **Auth:** Manager
- **Response:** CafeResponse
- Отвязка Telegram от кафе

**Паттерны:**
- Dependency Injection для сервиса (`get_cafe_link_service`)
- Использование `Annotated` для типизации зависимостей
- Авторизация через `ManagerUser` dependency для защищенных endpoints
- Query параметры с валидацией (regex для status)
- Подробные docstrings для автогенерации OpenAPI документации

### 5. Интеграция в приложение

**backend/src/routers/__init__.py:**
- Добавлен импорт `cafe_links_router`
- Добавлен в `__all__`

**backend/src/main.py:**
- Зарегистрирован роутер: `app.include_router(cafe_links_router, prefix="/api/v1")`
- Порядок: после `cafes_router`, перед `menu_router`

## Соответствие требованиям

### API Endpoints (из архитектуры) ✅

- ✅ POST /api/v1/cafes/{cafe_id}/link-request
- ✅ GET /api/v1/cafes/cafe-requests (с пагинацией и фильтром)
- ✅ POST /api/v1/cafes/cafe-requests/{request_id}/approve
- ✅ POST /api/v1/cafes/cafe-requests/{request_id}/reject
- ✅ PATCH /api/v1/cafes/{cafe_id}/notifications
- ✅ DELETE /api/v1/cafes/{cafe_id}/link

### Паттерны проекта ✅

- ✅ Async SQLAlchemy в репозитории
- ✅ Repository → Service → Router архитектура
- ✅ Pydantic схемы с `from_attributes=True`
- ✅ Dependency Injection (`Depends`)
- ✅ FastAPI роутер с `Annotated` типами
- ✅ Авторизация через существующие механизмы (`ManagerUser`, `CurrentUser`)
- ✅ HTTPException для ошибок
- ✅ Whitelist для обновляемых полей (безопасность)

### Бизнес-логика ✅

- ✅ Проверка существования кафе
- ✅ Проверка дубликатов pending заявок
- ✅ Проверка статуса перед approve/reject
- ✅ Обновление Cafe при approve с данными из request
- ✅ Валидация привязки при update_notifications и unlink
- ✅ Установка `processed_at` при approve/reject
- ✅ Установка `linked_at` при approve
- ✅ Очистка всех Telegram полей при unlink

## Технические детали

### Использованные технологии
- Python 3.13+ (type hints с `|` для unions)
- FastAPI (роутер, зависимости, валидация)
- Pydantic v2 (схемы, `model_config`)
- SQLAlchemy 2.0 (async, mapped_column, select)

### Code Style
- Следование существующим паттернам проекта
- Docstrings для всех публичных методов
- Type hints везде
- Meaningful variable names
- DRY принцип (переиспользование существующих паттернов)

### Безопасность
- Whitelist для обновляемых полей (защита от mass assignment)
- Авторизация на уровне роутера
- Валидация входных данных (Pydantic, Query regex)
- Проверки бизнес-правил в сервисе

## Границы задачи

**Выполнено:**
- ✅ API endpoints для cafe link requests
- ✅ Бизнес-логика для управления заявками
- ✅ Пагинация и фильтрация
- ✅ Интеграция в main.py

**НЕ выполнено (согласно инструкции):**
- ❌ Telegram Bot реализация (подзадача 2.3)
- ❌ Kafka workers (подзадача 2.4)
- ❌ Тесты (будет в подзадаче 5.x)

## Следующие шаги

После этой подзадачи можно переходить к:
1. **Подзадача 2.3:** Telegram Bot для приема заявок и отправки уведомлений
2. **Подзадача 2.4:** Notifications Worker (Kafka)

Эти подзадачи могут быть реализованы **параллельно**, так как не зависят друг от друга.

## Статус

**Completed** - все файлы созданы, роутер зарегистрирован, API готов к использованию.

---

**Готово к передаче следующему агенту.**
