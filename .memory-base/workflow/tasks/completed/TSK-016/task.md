---
id: TSK-016
title: Implement user access request approval system
pipeline: feature
status: completed
created_at: 2025-12-07T01:05:00Z
related_files:
  - backend/src/models/user.py
  - backend/src/routers/auth.py
  - backend/src/routers/users.py
  - backend/src/auth/dependencies.py
  - backend/src/services/user.py
  - backend/src/repositories/user.py
  - backend/src/schemas/user.py
  - backend/alembic/versions/
  - backend/tests/integration/api/test_auth_api.py
  - backend/tests/integration/api/test_users_api.py
  - frontend_mini_app/src/app/manager/page.tsx
impact:
  - api: yes
  - db: yes
  - frontend: yes
  - services: yes
---

## Описание

Реализовать систему контроля доступа с approval workflow для пользователей:
- Пользователи отправляют запрос на доступ при первой авторизации через Telegram
- Менеджеры принимают/отклоняют запросы, добавляют/удаляют пользователей вручную
- Менеджеры могут редактировать роли, имена и офисы пользователей
- Только одобренные пользователи могут создавать заказы

## Проблема

**Текущая реализация:** Любой пользователь с валидным Telegram initData автоматически создаётся в БД и получает доступ к системе (`POST /auth/telegram` создаёт нового пользователя автоматически).

**Требуемое поведение:**
1. **Approval Workflow:**
   - Новый пользователь отправляет запрос на доступ через `POST /auth/telegram`
   - Менеджер видит запросы в Manager Panel
   - Менеджер принимает (approve) или отклоняет (reject) запрос
   - После одобрения пользователь получает доступ к системе

2. **Manual Management:**
   - Менеджер может добавить пользователя вручную через `POST /users`
   - Менеджер может редактировать роль пользователя (`user` ↔ `manager`)
   - Менеджер может редактировать имя и офис пользователя
   - Менеджер может удалить пользователя
   - Менеджер может деактивировать (`is_active = false`)

## Acceptance Criteria

### Approval Workflow

- [ ] `POST /auth/telegram` создаёт `UserAccessRequest` для новых пользователей со статусом `pending`
- [ ] `POST /auth/telegram` возвращает 403 с message "Access request pending approval" для пользователей с pending request
- [ ] `POST /auth/telegram` возвращает 403 с message "Access request rejected" для пользователей с rejected request
- [ ] `POST /auth/telegram` возвращает 200 + JWT token для одобренных пользователей
- [ ] `GET /api/v1/user-requests` возвращает список запросов (manager only)
- [ ] `POST /api/v1/user-requests/{id}/approve` одобряет запрос и создаёт пользователя (manager only)
- [ ] `POST /api/v1/user-requests/{id}/reject` отклоняет запрос (manager only)

### Manual User Management

- [ ] `POST /users` создаёт пользователя вручную (manager only) — уже реализовано
- [ ] `POST /users/managers` создаёт менеджера вручную (manager only) — уже реализовано
- [ ] `PATCH /users/{tgid}` обновляет имя, офис и роль пользователя (manager only)
- [ ] `DELETE /users/{tgid}` удаляет пользователя (manager only) — уже реализовано
- [ ] `PATCH /users/{tgid}/access` блокирует/разблокирует пользователя (manager only) — уже реализовано

### Security

- [ ] Деактивированные пользователи (`is_active = false`) не могут авторизоваться
- [ ] Только менеджеры видят и управляют запросами
- [ ] Пользователи не могут изменять свою роль самостоятельно

### Frontend

- [ ] Manager Panel показывает список pending user requests
- [ ] Менеджер может принять/отклонить запрос одним кликом
- [ ] Менеджер может редактировать пользователей (имя, офис, роль)
- [ ] UI показывает статус запроса пользователя при попытке авторизации

### Tests

- [ ] Тесты для approval workflow (create request, approve, reject)
- [ ] Тесты для manual user management (update role, name, office)
- [ ] Тесты для security checks (pending/rejected users cannot auth)

## Контекст

### Существующий паттерн: CafeLinkRequest

Система уже использует approval workflow для подключения кафе к Telegram через `CafeLinkRequest`:

**Модель:** `backend/src/models/cafe.py`
```python
class LinkRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class CafeLinkRequest(Base, TimestampMixin):
    id: Mapped[int]
    cafe_id: Mapped[int]
    tg_chat_id: Mapped[int]
    tg_username: Mapped[str | None]
    status: Mapped[LinkRequestStatus]
    processed_at: Mapped[datetime | None]
```

**API Endpoints:**
- `POST /cafes/{cafe_id}/link-request` — создать запрос (public)
- `GET /cafe-requests` — список запросов (manager only)
- `POST /cafe-requests/{id}/approve` — одобрить (manager only)
- `POST /cafe-requests/{id}/reject` — отклонить (manager only)

**Использовать этот паттерн для UserAccessRequest.**

### Текущие эндпоинты управления пользователями

**Файл:** `backend/src/routers/users.py`

```python
# Уже реализовано (manager only):
POST /users                       # Создать пользователя
POST /users/managers               # Создать менеджера
DELETE /users/{tgid}              # Удалить пользователя
PATCH /users/{tgid}/access        # Блокировать/разблокировать

# Требуется добавить:
PATCH /users/{tgid}               # Обновить имя, офис, роль
```

### Модель User

**Файл:** `backend/src/models/user.py`

```python
class User(Base, TimestampMixin):
    tgid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str]
    office: Mapped[str]
    role: Mapped[str] = "user"  # "user" | "manager"
    is_active: Mapped[bool] = True
    weekly_limit: Mapped[Decimal | None]
```

**Дополнение:** Не требуется изменять модель User. Добавляем новую модель `UserAccessRequest`.

## Решение

### 1. Добавить модель UserAccessRequest

**Файл:** `backend/src/models/user.py`

```python
from enum import StrEnum

class UserAccessRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class UserAccessRequest(Base, TimestampMixin):
    __tablename__ = "user_access_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tgid: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    office: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[UserAccessRequestStatus] = mapped_column(String(20), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Поля:**
- `tgid` — Telegram ID (unique, чтобы один пользователь не отправил несколько запросов)
- `name` — имя из Telegram
- `office` — офис, указанный при запросе
- `username` — Telegram username (опционально)
- `status` — pending/approved/rejected
- `processed_at` — когда запрос был обработан

### 2. Миграция БД

**Файл:** `backend/alembic/versions/004_user_access_requests.py`

```python
def upgrade() -> None:
    op.create_table(
        "user_access_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tgid", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("office", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tgid"),
    )
    op.create_index("ix_user_access_requests_status", "user_access_requests", ["status"])
```

### 3. Изменить логику авторизации

**Файл:** `backend/src/routers/auth.py`

```python
@router.post("/telegram", response_model=AuthResponse)
async def authenticate_telegram(...):
    # 1. Validate Telegram initData
    tg_user = validate_telegram_init_data(...)
    tgid = tg_user["id"]

    # 2. Check if user exists
    user = await db.execute(select(User).where(User.tgid == tgid))
    user = user.scalar_one_or_none()

    if user:
        # User exists → normal auth
        if not user.is_active:
            raise HTTPException(403, "User is deactivated")

        # Create JWT token
        access_token = create_access_token({"tgid": user.tgid, "role": user.role})
        return AuthResponse(access_token=access_token, user=user)

    # 3. User doesn't exist → check for access request
    request = await db.execute(
        select(UserAccessRequest).where(UserAccessRequest.tgid == tgid)
    )
    request = request.scalar_one_or_none()

    if request:
        # Request exists
        if request.status == "pending":
            raise HTTPException(403, "Access request pending approval")
        elif request.status == "rejected":
            raise HTTPException(403, "Access request rejected")
        # If approved but user doesn't exist → data inconsistency
        raise HTTPException(500, "Data inconsistency. Contact administrator.")

    # 4. No request → create new request
    name = f"{tg_user['first_name']} {tg_user.get('last_name', '')}".strip()
    new_request = UserAccessRequest(
        tgid=tgid,
        name=name or f"User {tgid}",
        office=request.office,
        username=tg_user.get("username"),
        status="pending",
    )
    db.add(new_request)
    await db.commit()

    raise HTTPException(
        403,
        "Access request created. Please wait for manager approval.",
    )
```

### 4. API для управления запросами

**Файл:** `backend/src/routers/user_requests.py` (новый)

```python
from fastapi import APIRouter, Depends, Query
from ..auth.dependencies import ManagerUser
from ..services.user_request import UserRequestService

router = APIRouter(prefix="/user-requests", tags=["user-requests"])

@router.get("", response_model=UserRequestListSchema)
async def list_user_requests(
    manager: ManagerUser,
    service: UserRequestService,
    skip: int = 0,
    limit: int = 100,
    status: UserAccessRequestStatus | None = None,
):
    """List all user access requests (manager only)."""
    return await service.list_requests(skip, limit, status)

@router.post("/{request_id}/approve", response_model=UserRequestSchema)
async def approve_user_request(
    request_id: int,
    manager: ManagerUser,
    service: UserRequestService,
):
    """Approve user access request (manager only)."""
    return await service.approve_request(request_id)

@router.post("/{request_id}/reject", response_model=UserRequestSchema)
async def reject_user_request(
    request_id: int,
    manager: ManagerUser,
    service: UserRequestService,
):
    """Reject user access request (manager only)."""
    return await service.reject_request(request_id)
```

### 5. Service для обработки запросов

**Файл:** `backend/src/services/user_request.py` (новый)

```python
from datetime import datetime

class UserRequestService:
    async def approve_request(self, request_id: int):
        # 1. Get request
        request = await self.repo.get_request(request_id)
        if not request:
            raise HTTPException(404, "Request not found")
        if request.status != "pending":
            raise HTTPException(400, "Request already processed")

        # 2. Create user
        user = User(
            tgid=request.tgid,
            name=request.name,
            office=request.office,
            role="user",
            is_active=True,
        )
        db.add(user)

        # 3. Update request
        request.status = "approved"
        request.processed_at = datetime.utcnow()

        await db.commit()
        return request

    async def reject_request(self, request_id: int):
        request = await self.repo.get_request(request_id)
        if not request:
            raise HTTPException(404, "Request not found")
        if request.status != "pending":
            raise HTTPException(400, "Request already processed")

        request.status = "rejected"
        request.processed_at = datetime.utcnow()

        await db.commit()
        return request
```

### 6. Добавить PATCH /users/{tgid}

**Файл:** `backend/src/routers/users.py`

```python
@router.patch("/{tgid}", response_model=UserResponse)
async def update_user(
    tgid: int,
    data: UserUpdate,  # name, office, role (опционально)
    manager: ManagerUser,
    service: UserService,
):
    """Update user (manager only)."""
    return await service.update_user(tgid, data)
```

**Schema:** `backend/src/schemas/user.py`
```python
class UserUpdate(BaseModel):
    name: str | None = None
    office: str | None = None
    role: str | None = None  # "user" | "manager"
```

### 7. Frontend: Manager Panel

**Файл:** `frontend_mini_app/src/app/manager/page.tsx`

Добавить вкладку "User Requests":
- Список pending/approved/rejected requests
- Кнопки "Approve" / "Reject" для pending requests
- Список пользователей с возможностью редактирования (имя, офис, роль)

**UI Mockup:**
```
┌─────────────────────────────────────┐
│ User Access Requests                │
├─────────────────────────────────────┤
│ [Pending] [Approved] [Rejected]     │
├─────────────────────────────────────┤
│ ✓ Ivan Petrov (@ivanpetrov)         │
│   Office A                           │
│   [Approve] [Reject]                │
├─────────────────────────────────────┤
│ ✓ Maria Sidorova                    │
│   Office B                           │
│   [Approve] [Reject]                │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ User Management                      │
├─────────────────────────────────────┤
│ ✓ Alice Smith (Manager)             │
│   Office A | Active                 │
│   [Edit] [Deactivate] [Delete]      │
├─────────────────────────────────────┤
│ ✓ Bob Johnson (User)                │
│   Office B | Active                 │
│   [Edit] [Deactivate] [Delete]      │
└─────────────────────────────────────┘
```

### 8. Тесты

**Файл:** `backend/tests/integration/api/test_user_requests_api.py` (новый)

```python
async def test_create_access_request_on_first_auth(client):
    """Test access request is created for new user."""
    init_data = generate_telegram_init_data({"id": 999888777, ...})
    response = await client.post("/api/v1/auth/telegram", json={"init_data": init_data})

    assert response.status_code == 403
    assert "pending approval" in response.json()["detail"]

async def test_approve_access_request(client, manager_auth_headers):
    """Test manager can approve access request."""
    # 1. Create request
    init_data = generate_telegram_init_data({"id": 999888777, ...})
    await client.post("/api/v1/auth/telegram", json={"init_data": init_data})

    # 2. Get requests
    response = await client.get("/api/v1/user-requests", headers=manager_auth_headers)
    requests = response.json()["items"]
    request_id = requests[0]["id"]

    # 3. Approve
    response = await client.post(
        f"/api/v1/user-requests/{request_id}/approve",
        headers=manager_auth_headers,
    )
    assert response.status_code == 200

    # 4. Verify user can now auth
    response = await client.post("/api/v1/auth/telegram", json={"init_data": init_data})
    assert response.status_code == 200
    assert "access_token" in response.json()

async def test_reject_access_request(client, manager_auth_headers):
    """Test manager can reject access request."""
    # Similar to approve, but reject

async def test_update_user_role(client, manager_auth_headers, test_user):
    """Test manager can change user role."""
    response = await client.patch(
        f"/api/v1/users/{test_user.tgid}",
        headers=manager_auth_headers,
        json={"role": "manager"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "manager"
```

**Обновить:** `backend/tests/integration/api/test_auth_api.py`
```python
async def test_telegram_auth_success(client, manager_auth_headers):
    """Test successful auth for approved user."""
    # 1. Manager creates user manually
    await client.post(
        "/api/v1/users",
        headers=manager_auth_headers,
        json={"tgid": 111222333, "name": "Alice", "office": "Office A"},
    )

    # 2. User can now auth
    init_data = generate_telegram_init_data({"id": 111222333, ...})
    response = await client.post("/api/v1/auth/telegram", json={"init_data": init_data})

    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Затронутые файлы

### Backend

| Файл | Действие |
|------|----------|
| `backend/src/models/user.py` | Добавить: `UserAccessRequest`, `UserAccessRequestStatus` |
| `backend/src/routers/auth.py` | Изменить: создавать request вместо user для новых пользователей |
| `backend/src/routers/users.py` | Добавить: `PATCH /users/{tgid}` для обновления роли/имени/офиса |
| `backend/src/routers/user_requests.py` | Создать: API для управления access requests |
| `backend/src/services/user_request.py` | Создать: логика approve/reject requests |
| `backend/src/repositories/user_request.py` | Создать: БД операции для requests |
| `backend/src/schemas/user.py` | Обновить: `UserUpdate` с полем `role` |
| `backend/src/schemas/user_request.py` | Создать: схемы для requests |
| `backend/alembic/versions/004_user_access_requests.py` | Создать: миграция для новой таблицы |
| `backend/tests/integration/api/test_user_requests_api.py` | Создать: тесты для approval workflow |
| `backend/tests/integration/api/test_auth_api.py` | Обновить: тесты для новой логики auth |
| `backend/tests/integration/api/test_users_api.py` | Добавить: тесты для `PATCH /users/{tgid}` |

### Frontend

| Файл | Действие |
|------|----------|
| `frontend_mini_app/src/app/manager/page.tsx` | Добавить: вкладку User Requests |
| `frontend_mini_app/src/lib/api/hooks.ts` | Добавить: hooks для user requests API |
| `frontend_mini_app/src/components/UserRequestCard.tsx` | Создать: карточка запроса с кнопками Approve/Reject |
| `frontend_mini_app/src/components/UserEditModal.tsx` | Создать: модалка редактирования пользователя |

### Документация

| Файл | Действие |
|------|----------|
| `.memory-base/tech-docs/api.md` | Обновить: добавить `/user-requests` endpoints |
| `.memory-base/tech-docs/roles.md` | Обновить: добавить примечание о approval workflow |

## Альтернативные решения

### 1. Без approval workflow (только ручное добавление)

**Плюсы:**
- Проще реализация
- Менеджер полностью контролирует доступ

**Минусы:**
- Менеджер должен знать Telegram ID каждого пользователя заранее
- Неудобно для пользователей (нужно вручную сообщать tgid)

**Решение:** Не подходит. Approval workflow удобнее для пользователей.

### 2. Автоматическое одобрение для домена email

**Плюсы:**
- Автоматизация для корпоративных пользователей

**Минусы:**
- Telegram не предоставляет email в initData
- Требует дополнительную интеграцию (OAuth)

**Решение:** Не подходит. Telegram Mini App не имеет доступа к email.

### 3. Использовать Telegram Bot Commands вместо Mini App

**Плюсы:**
- Нативный Telegram flow (`/start`, `/request_access`)

**Минусы:**
- Требует переписать весь frontend
- Теряем преимущества Mini App (rich UI)

**Решение:** Не подходит. Архитектура уже построена на Mini App.

## Риски и вопросы

### Риск: Первый менеджер

**Проблема:** Кто одобрит первого менеджера?

**Решение:**
- Seed script создаёт первого менеджера при развёртывании
- Либо административный endpoint (защищённый API ключом)

**Рекомендация:** Использовать seed script (расширить `backend/tests/e2e_seed.py`).

### Риск: Дублирование запросов

**Проблема:** Пользователь отправляет несколько запросов.

**Решение:**
- `UserAccessRequest.tgid` уникальный (unique constraint)
- При повторном `POST /auth/telegram` возвращаем существующий request

### Риск: Миграция существующих пользователей

**Проблема:** Пользователи, созданные до изменений, не имеют request.

**Решение:**
- Существующие пользователи в БД → авторизуются нормально (через `user = await db.execute(...)`)
- Только новые пользователи проходят через approval workflow

**Рекомендация:** Не требуется миграция существующих пользователей.

### Вопрос: Менеджер может добавить пользователя напрямую минуя запрос?

**Ответ:** Да. `POST /users` позволяет менеджеру создать пользователя вручную без запроса. Это полезно когда менеджер знает tgid заранее или хочет предоставить доступ до получения запроса.

### Вопрос: Что делать с rejected запросами?

**Ответ:** Пользователь получает сообщение "Access request rejected. Contact your manager." Менеджер может удалить rejected request или изменить статус обратно на pending (опционально).

## Примерные flows

### Flow 1: Новый пользователь запрашивает доступ

1. Пользователь открывает Telegram Mini App → `POST /auth/telegram`
2. Backend: user не найден, request не найден → создаёт `UserAccessRequest` со статусом `pending`
3. Backend: возвращает `403 "Access request created. Please wait for manager approval."`
4. Frontend: показывает сообщение "Ваш запрос на доступ отправлен. Ожидайте одобрения менеджера."

### Flow 2: Менеджер одобряет запрос

1. Менеджер открывает Manager Panel → вкладка "User Requests"
2. Frontend: `GET /user-requests?status=pending` → показывает список pending requests
3. Менеджер нажимает "Approve" на запросе
4. Frontend: `POST /user-requests/{id}/approve`
5. Backend: создаёт `User` с `role="user"`, `is_active=true`, обновляет request `status="approved"`
6. Frontend: обновляет список, показывает успешное сообщение

### Flow 3: Одобренный пользователь авторизуется

1. Пользователь открывает Telegram Mini App → `POST /auth/telegram`
2. Backend: находит `User` по tgid → `is_active=true`
3. Backend: создаёт JWT token, возвращает `200 OK` + token + user
4. Frontend: сохраняет token, переходит на главную страницу

### Flow 4: Менеджер добавляет пользователя вручную

1. Менеджер открывает Manager Panel → вкладка "Users"
2. Менеджер нажимает "Add User", заполняет форму (tgid, name, office)
3. Frontend: `POST /users` с данными
4. Backend: создаёт `User` напрямую (без request)
5. Frontend: обновляет список пользователей

### Flow 5: Менеджер меняет роль пользователя

1. Менеджер открывает Manager Panel → список пользователей
2. Менеджер нажимает "Edit" на пользователе → модалка
3. Менеджер меняет роль на "Manager"
4. Frontend: `PATCH /users/{tgid}` с `{"role": "manager"}`
5. Backend: обновляет `user.role = "manager"`
6. Frontend: обновляет список, показывает badge "Manager"

### Flow 6: Менеджер отклоняет запрос

1. Менеджер открывает Manager Panel → вкладка "User Requests"
2. Менеджер нажимает "Reject" на запросе
3. Frontend: `POST /user-requests/{id}/reject`
4. Backend: обновляет request `status="rejected"`, `processed_at=now()`
5. Frontend: убирает запрос из pending списка

### Flow 7: Пользователь с rejected запросом пытается войти

1. Пользователь открывает Telegram Mini App → `POST /auth/telegram`
2. Backend: user не найден, находит request с `status="rejected"`
3. Backend: возвращает `403 "Access request rejected. Contact your manager."`
4. Frontend: показывает сообщение "Ваш запрос был отклонён. Обратитесь к менеджеру."

## Приоритет

**High** — критичная функциональность для безопасности и управления доступом.

## Оценка сложности

**Medium:**
- Новая модель + миграция БД
- Новые endpoints (3-4 endpoint'а)
- Service + repository для requests
- Обновление логики auth
- Frontend: новые компоненты (UserRequestCard, UserEditModal)
- Обновление существующих тестов + новые тесты

**Ориентировочное время:** 4-6 часов (включая тесты, frontend и документацию).
