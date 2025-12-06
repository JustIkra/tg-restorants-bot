---
agent: architect
task_id: TSK-002
status: completed
next: coder
created_at: 2025-12-06T00:45:00Z
files_changed: []
---

## Анализ задачи

### Контекст

Frontend (Telegram Mini App) полностью реализован и протестирован (66 тестов):
- ✅ API Client с JWT авторизацией
- ✅ Telegram WebApp SDK интеграция
- ✅ UI компоненты (CafeSelector, ComboSelector, MenuSection, ExtrasSection)
- ✅ SWR hooks для data fetching
- ✅ TypeScript типы для всех API entities

Backend API **полностью отсутствует**. Необходимо создать все ~35 endpoints согласно спецификации.

### Основные требования

1. **База данных:** PostgreSQL 17 с 7 таблицами (users, cafes, combos, menu_items, deadlines, orders, summaries)
2. **API:** ~35 REST endpoints с JWT авторизацией и RBAC (user/manager)
3. **Бизнес-логика:**
   - Проверка deadlines перед создание/изменением заказа
   - Валидация комбо (все категории заполнены)
   - Расчёт total_price (combo + extras)
   - Агрегация данных для отчётов
4. **Авторизация:** Telegram WebApp initData → JWT token
5. **Async:** Все DB операции асинхронные (SQLAlchemy 2.0 + asyncpg)

### Затронутые компоненты

- **Новые:** backend/ (директория не существует)
- **Зависимости:** PostgreSQL, asyncpg, SQLAlchemy, Alembic
- **Интеграция:** Frontend уже готов и ожидает API endpoints

### Риски

1. **Telegram Auth:** Валидация initData требует правильного HMAC-SHA256 алгоритма с bot token
2. **Deadline Logic:** Расчёт времени с учётом advance_days и weekday требует точности
3. **Parallel Merge:** При параллельном выполнении возможны конфликты в импортах/зависимостях
4. **Database Schema:** Неправильные foreign keys/индексы могут снизить производительность

---

## Архитектурное решение

### Подход

**Clean Architecture + Dependency Injection:**

```
┌─────────────────────────────────────────────┐
│ Routers (FastAPI)                           │  ← API layer
├─────────────────────────────────────────────┤
│ Services (Business Logic)                   │  ← Application layer
├─────────────────────────────────────────────┤
│ Repositories (Database Access)              │  ← Data layer
├─────────────────────────────────────────────┤
│ Models (SQLAlchemy) + Schemas (Pydantic)    │  ← Domain layer
└─────────────────────────────────────────────┘
```

**Преимущества:**
- Слои разделены, тестируются независимо
- Services содержат бизнес-логику (deadline checks, validation)
- Repositories инкапсулируют DB queries
- Routers — тонкий слой, только HTTP handling

### Структура проекта

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, startup/shutdown
│   ├── config.py                  # Settings (Pydantic BaseSettings)
│   │
│   ├── auth/                      # Authentication & Authorization
│   │   ├── __init__.py
│   │   ├── telegram.py            # Validate Telegram initData
│   │   ├── jwt.py                 # Generate/verify JWT tokens
│   │   ├── dependencies.py        # FastAPI Depends (get_current_user, require_manager)
│   │   └── schemas.py             # LoginRequest, TokenResponse
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py                # Base class, metadata
│   │   ├── user.py                # User model
│   │   ├── cafe.py                # Cafe, Combo, MenuItem models
│   │   ├── deadline.py            # Deadline model
│   │   ├── order.py               # Order model
│   │   └── summary.py             # Summary model
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py                # UserResponse, UserCreate, UserUpdate
│   │   ├── cafe.py                # CafeResponse, ComboResponse, MenuItemResponse
│   │   ├── deadline.py            # DeadlineSchedule
│   │   ├── order.py               # OrderResponse, OrderCreate, OrderCombo, OrderExtra
│   │   └── summary.py             # SummaryResponse, SummaryCreate
│   │
│   ├── repositories/              # Database access layer
│   │   ├── __init__.py
│   │   ├── base.py                # BaseRepository[T]
│   │   ├── user.py                # UserRepository
│   │   ├── cafe.py                # CafeRepository, ComboRepository, MenuItemRepository
│   │   ├── deadline.py            # DeadlineRepository
│   │   ├── order.py               # OrderRepository
│   │   └── summary.py             # SummaryRepository
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── user.py                # UserService
│   │   ├── cafe.py                # CafeService, MenuService
│   │   ├── deadline.py            # DeadlineService (availability checks)
│   │   ├── order.py               # OrderService (validation, pricing)
│   │   └── summary.py             # SummaryService (aggregation)
│   │
│   ├── routers/                   # FastAPI routers
│   │   ├── __init__.py
│   │   ├── auth.py                # POST /auth/telegram
│   │   ├── users.py               # 8 endpoints
│   │   ├── cafes.py               # 6 endpoints
│   │   ├── menu.py                # 9 endpoints (combos + items)
│   │   ├── deadlines.py           # 2 endpoints
│   │   ├── orders.py              # 7 endpoints
│   │   └── summaries.py           # 4 endpoints
│   │
│   └── database.py                # AsyncEngine, SessionLocal, get_db dependency
│
├── alembic/                       # Database migrations
│   ├── versions/
│   │   └── 001_initial_schema.py
│   ├── env.py
│   └── script.py.mako
│
├── tests/                         # Tests
│   ├── conftest.py                # Fixtures (async_client, db_session)
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_cafes.py
│   ├── test_menu.py
│   ├── test_deadlines.py
│   ├── test_orders.py
│   └── test_summaries.py
│
├── pyproject.toml                 # Dependencies
├── alembic.ini                    # Alembic config
├── .env.example                   # Example environment variables
└── README.md                      # Setup instructions
```

### Слои приложения

#### 1. Models (SQLAlchemy 2.0, async)

**Ответственность:** Определение структуры таблиц БД

**Пример (User):**
```python
from sqlalchemy import Boolean, String, Integer, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    tgid: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    office: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_limit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Связи:**
- User → Orders (one-to-many)
- Cafe → Combos, MenuItems, Deadlines (one-to-many)
- Order → User, Cafe (many-to-one)
- Combo → Cafe (many-to-one)

**Индексы:**
- `users.tgid` (PK, unique)
- `orders.user_tgid, order_date` (composite, для быстрого поиска заказов пользователя)
- `orders.cafe_id, order_date` (composite, для отчётов кафе)
- `menu_items.cafe_id, category` (composite, для фильтрации по категории)

#### 2. Schemas (Pydantic 2.x)

**Ответственность:** Валидация входных/выходных данных API

**Request schemas:**
- `UserCreate`, `UserUpdate`
- `CafeCreate`, `CafeUpdate`
- `ComboCreate`, `ComboUpdate`
- `MenuItemCreate`, `MenuItemUpdate`
- `OrderCreate`, `OrderUpdate`

**Response schemas:**
- `UserResponse`, `CafeResponse`, `ComboResponse`, `MenuItemResponse`, `OrderResponse`
- `model_config = {"from_attributes": True}` для конвертации из SQLAlchemy models

**Пример (OrderCreate):**
```python
class OrderCreate(BaseModel):
    cafe_id: int
    order_date: date
    combo_id: int
    combo_items: list[ComboItemInput]  # [{ category: str, menu_item_id: int }]
    extras: list[ExtraInput] = []      # [{ menu_item_id: int, quantity: int }]
    notes: str | None = None
```

#### 3. Repositories

**Ответственность:** CRUD операции, DB queries

**BaseRepository:**
```python
class BaseRepository[T]:
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get(self, id: int) -> T | None: ...
    async def list(self, filters: dict) -> list[T]: ...
    async def create(self, data: dict) -> T: ...
    async def update(self, id: int, data: dict) -> T: ...
    async def delete(self, id: int) -> None: ...
```

**Специализированные методы:**
- `OrderRepository.get_by_user_and_date(tgid, date)`
- `DeadlineRepository.get_for_cafe(cafe_id)`
- `SummaryRepository.aggregate_orders(cafe_id, date)`

#### 4. Services

**Ответственность:** Бизнес-логика, валидация, координация

**UserService:**
- `create_user(data)` → проверка дубликатов
- `update_access(tgid, enabled)` → деактивация пользователя
- `get_balance(tgid)` → расчёт баланса и spent_this_week

**OrderService:**
- `create_order(user_tgid, data)` → проверка deadline, валидация combo, расчёт total_price
- `update_order(order_id, user_tgid, data)` → проверка owner, deadline
- `delete_order(order_id, user_tgid, role)` → проверка прав

**DeadlineService:**
- `check_availability(cafe_id, order_date)` → расчёт deadline с учётом advance_days
- `get_week_availability(cafe_id)` → доступность на 7 дней вперёд

**MenuService:**
- `validate_combo(combo_id, combo_items)` → проверка категорий
- `calculate_total_price(combo_id, extras)` → сумма комбо + доп. товары

#### 5. Routers (FastAPI)

**Ответственность:** HTTP handling, авторизация, сериализация

**Пример (orders.py):**
```python
router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> Order:
    return await service.create_order(user.tgid, data)
```

**Dependency Injection:**
- `get_current_user` → JWT validation, User object
- `require_manager` → Role check
- `get_db` → AsyncSession
- `get_*_service` → Service instances

### Telegram Authentication Flow

```
1. Frontend (Telegram Mini App)
   ├─> Получает initData от Telegram WebApp SDK
   └─> POST /auth/telegram { init_data: string }

2. Backend
   ├─> Парсит initData (query string)
   ├─> Проверяет hash через HMAC-SHA256 с bot token
   ├─> Извлекает user { id, first_name, ... }
   ├─> Ищет User по tgid или создаёт нового
   ├─> Генерирует JWT token (payload: { tgid, role })
   └─> Возвращает { access_token, user }

3. Frontend
   ├─> Сохраняет token в localStorage
   └─> Добавляет header "Authorization: Bearer {token}" ко всем запросам
```

**Важно:**
- initData валидируется по алгоритму из документации Telegram
- Bot token берётся из environment variable `TELEGRAM_BOT_TOKEN`
- JWT expires через 7 дней (configurable)

### Database Migrations (Alembic)

**Первая миграция:** `001_initial_schema.py`

**Таблицы (в порядке создания):**
1. `users` (no foreign keys)
2. `cafes` (no foreign keys)
3. `combos` (FK: cafe_id)
4. `menu_items` (FK: cafe_id)
5. `deadlines` (FK: cafe_id)
6. `orders` (FK: user_tgid, cafe_id, combo_id)
7. `summaries` (FK: cafe_id)

**JSON columns:**
- `combos.categories` → PostgreSQL JSONB
- `orders.combo_items` → PostgreSQL JSONB
- `orders.extras` → PostgreSQL JSONB
- `summaries.breakdown` → PostgreSQL JSONB

**Команды:**
```bash
alembic upgrade head   # Применить все миграции
alembic downgrade -1   # Откатить последнюю миграцию
alembic revision --autogenerate -m "description"  # Создать новую миграцию
```

### Configuration (Pydantic Settings)

**config.py:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/lunch_bot"
    TELEGRAM_BOT_TOKEN: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env"}

settings = Settings()
```

**.env.example:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/lunch_bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
```

### Error Handling

**Единый формат ошибок:**
```python
# HTTPException с detail
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Deadline has passed"
)

# Response:
{
  "detail": "Deadline has passed"
}
```

**Коды ошибок:**
- 400 Bad Request → validation errors, deadline passed
- 401 Unauthorized → invalid/missing token
- 403 Forbidden → access denied (role mismatch, not owner)
- 404 Not Found → resource not found
- 409 Conflict → duplicate (e.g., user already exists)
- 500 Internal Server Error → unexpected errors

---

## Декомпозиция на подзадачи

### Фаза 1: Инфраструктура (последовательно, сначала)

Подзадачи выполняются **последовательно**, так как каждая зависит от предыдущей.

#### 1.1 Инициализация проекта и конфигурация

**Действия:**
- Создать структуру директорий `backend/src/`, `backend/alembic/`, `backend/tests/`
- Создать `pyproject.toml` с зависимостями
- Создать `backend/src/config.py` (Pydantic Settings)
- Создать `.env.example`
- Создать `backend/README.md` с инструкциями по запуску

**Файлы:**
```
backend/
├── src/
│   ├── __init__.py
│   └── config.py
├── alembic/
├── tests/
├── pyproject.toml
├── .env.example
└── README.md
```

**Зависимости (pyproject.toml):**
```toml
[project]
name = "lunch-bot-backend"
version = "0.1.0"
requires-python = ">=3.13"

dependencies = [
    "fastapi>=0.120.0",
    "uvicorn>=0.38.0",
    "pydantic>=2.12.0",
    "pydantic-settings>=2.7.0",
    "sqlalchemy>=2.0.44",
    "asyncpg>=0.31.0",
    "alembic>=1.17.0",
    "python-jose[cryptography]>=3.3.0",  # JWT
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.20",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",  # For TestClient
    "mypy>=1.19.0",
    "ruff>=0.14.0",
]
```

**Критерий готовности:** `pyproject.toml` создан, структура директорий создана, config.py работает

---

#### 1.2 Database setup и модели SQLAlchemy

**Действия:**
- Создать `backend/src/database.py` (AsyncEngine, SessionLocal, get_db)
- Создать базовый класс `backend/src/models/base.py`
- Создать модели SQLAlchemy:
  - `backend/src/models/user.py` → User
  - `backend/src/models/cafe.py` → Cafe, Combo, MenuItem
  - `backend/src/models/deadline.py` → Deadline
  - `backend/src/models/order.py` → Order
  - `backend/src/models/summary.py` → Summary
- Настроить Alembic (`alembic init alembic`, `alembic.ini`, `env.py`)
- Создать первую миграцию `001_initial_schema.py`

**Файлы:**
```
backend/src/
├── database.py
└── models/
    ├── __init__.py
    ├── base.py
    ├── user.py
    ├── cafe.py
    ├── deadline.py
    ├── order.py
    └── summary.py

backend/alembic/
├── versions/
│   └── 001_initial_schema.py
├── env.py
└── script.py.mako
```

**Связи между моделями:**
- User.orders → relationship("Order")
- Cafe.combos → relationship("Combo")
- Cafe.menu_items → relationship("MenuItem")
- Cafe.deadlines → relationship("Deadline")
- Order.user → relationship("User")
- Order.cafe → relationship("Cafe")
- Order.combo → relationship("Combo")

**Критерий готовности:** `alembic upgrade head` успешно создаёт все таблицы в PostgreSQL

---

#### 1.3 Авторизация (Telegram + JWT)

**Действия:**
- Создать `backend/src/auth/telegram.py` → validate_telegram_init_data()
- Создать `backend/src/auth/jwt.py` → create_access_token(), verify_token()
- Создать `backend/src/auth/dependencies.py` → get_current_user(), require_manager()
- Создать `backend/src/auth/schemas.py` → TelegramAuthRequest, TokenResponse
- Создать `backend/src/routers/auth.py` → POST /auth/telegram
- Добавить в `backend/src/main.py` → router включение

**Файлы:**
```
backend/src/auth/
├── __init__.py
├── telegram.py        # validate_telegram_init_data(init_data: str, bot_token: str) -> dict
├── jwt.py             # create_access_token(data: dict) -> str
├── dependencies.py    # get_current_user(token: str) -> User
└── schemas.py         # TelegramAuthRequest, TokenResponse

backend/src/routers/
├── __init__.py
└── auth.py            # POST /auth/telegram
```

**Telegram validation алгоритм:**
1. Parse initData (query string)
2. Extract hash
3. Create data_check_string (sorted key=value pairs, except hash)
4. Generate secret_key = HMAC-SHA256(bot_token, "WebAppData")
5. Compute hash = HMAC-SHA256(secret_key, data_check_string)
6. Compare with provided hash

**JWT payload:**
```json
{
  "tgid": 123456789,
  "role": "user",
  "exp": 1234567890
}
```

**Критерий готовности:** POST /auth/telegram возвращает JWT token, get_current_user извлекает User из token

---

### Фаза 2: API Modules (параллельно)

Подзадачи **независимы** и могут выполняться **параллельно**. Каждая работает со своими файлами.

#### 2.1 Users API (8 endpoints)

**Действия:**
- Создать `backend/src/schemas/user.py` → UserResponse, UserCreate, UserUpdate
- Создать `backend/src/repositories/user.py` → UserRepository
- Создать `backend/src/services/user.py` → UserService
- Создать `backend/src/routers/users.py` → 8 endpoints

**Endpoints:**
1. `GET /users` (manager) → list users with search
2. `POST /users` (manager) → create user
3. `POST /users/managers` (manager) → create manager
4. `GET /users/{tgid}` (self | manager) → get user
5. `DELETE /users/{tgid}` (manager) → delete user
6. `PATCH /users/{tgid}/access` (manager) → enable/disable user
7. `GET /users/{tgid}/balance` (self | manager) → get balance
8. `PATCH /users/{tgid}/balance/limit` (manager) → set weekly limit

**Файлы:**
```
backend/src/schemas/user.py
backend/src/repositories/user.py
backend/src/services/user.py
backend/src/routers/users.py
```

**Зависимости:** models.user, auth.dependencies

**Критерий готовности:** 8 endpoints работают, тесты проходят

**Может выполняться параллельно с:** 2.2, 2.3, 2.4, 2.5, 2.6

---

#### 2.2 Cafes API (6 endpoints)

**Действия:**
- Создать `backend/src/schemas/cafe.py` → CafeResponse, CafeCreate, CafeUpdate
- Создать `backend/src/repositories/cafe.py` → CafeRepository
- Создать `backend/src/services/cafe.py` → CafeService
- Создать `backend/src/routers/cafes.py` → 6 endpoints

**Endpoints:**
1. `GET /cafes` (user | manager) → list cafes
2. `POST /cafes` (manager) → create cafe
3. `GET /cafes/{cafe_id}` (user | manager) → get cafe
4. `PATCH /cafes/{cafe_id}` (manager) → update cafe
5. `DELETE /cafes/{cafe_id}` (manager) → delete cafe
6. `PATCH /cafes/{cafe_id}/status` (manager) → set is_active

**Файлы:**
```
backend/src/schemas/cafe.py
backend/src/repositories/cafe.py
backend/src/services/cafe.py
backend/src/routers/cafes.py
```

**Зависимости:** models.cafe, auth.dependencies

**Критерий готовности:** 6 endpoints работают, тесты проходят

**Может выполняться параллельно с:** 2.1, 2.3, 2.4, 2.5, 2.6

---

#### 2.3 Menu API (9 endpoints: Combos + Items)

**Действия:**
- Обновить `backend/src/schemas/cafe.py` → ComboResponse, ComboCreate, MenuItemResponse, MenuItemCreate
- Создать `backend/src/repositories/menu.py` → ComboRepository, MenuItemRepository
- Создать `backend/src/services/menu.py` → MenuService (validate_combo, calculate_price)
- Создать `backend/src/routers/menu.py` → 9 endpoints

**Endpoints:**

**Combos:**
1. `GET /cafes/{cafe_id}/combos` → list combos
2. `POST /cafes/{cafe_id}/combos` (manager) → create combo
3. `PATCH /cafes/{cafe_id}/combos/{combo_id}` (manager) → update combo
4. `DELETE /cafes/{cafe_id}/combos/{combo_id}` (manager) → delete combo

**Menu Items:**
5. `GET /cafes/{cafe_id}/menu` → list menu items (filter by category)
6. `POST /cafes/{cafe_id}/menu` (manager) → create menu item
7. `GET /cafes/{cafe_id}/menu/{item_id}` → get menu item
8. `PATCH /cafes/{cafe_id}/menu/{item_id}` (manager) → update menu item
9. `DELETE /cafes/{cafe_id}/menu/{item_id}` (manager) → delete menu item

**Файлы:**
```
backend/src/schemas/cafe.py  (обновить: добавить Combo, MenuItem schemas)
backend/src/repositories/menu.py
backend/src/services/menu.py
backend/src/routers/menu.py
```

**Зависимости:** models.cafe (Combo, MenuItem), auth.dependencies

**Критерий готовности:** 9 endpoints работают, validate_combo() корректно проверяет категории

**Может выполняться параллельно с:** 2.1, 2.2, 2.4, 2.5, 2.6

---

#### 2.4 Deadlines API (2 endpoints)

**Действия:**
- Создать `backend/src/schemas/deadline.py` → DeadlineSchedule, DeadlineScheduleInput
- Создать `backend/src/repositories/deadline.py` → DeadlineRepository
- Создать `backend/src/services/deadline.py` → DeadlineService (check_availability, get_week_availability)
- Создать `backend/src/routers/deadlines.py` → 2 endpoints

**Endpoints:**
1. `GET /cafes/{cafe_id}/deadlines` (manager) → get schedule
2. `PUT /cafes/{cafe_id}/deadlines` (manager) → update schedule

**Файлы:**
```
backend/src/schemas/deadline.py
backend/src/repositories/deadline.py
backend/src/services/deadline.py
backend/src/routers/deadlines.py
```

**Бизнес-логика:**
- `check_availability(cafe_id, order_date)` → проверяет:
  - Есть ли deadline для weekday
  - Не прошёл ли deadline (с учётом advance_days)
  - Возвращает `{ can_order: bool, deadline: datetime, reason: str }`

**Зависимости:** models.deadline, auth.dependencies

**Критерий готовности:** check_availability() корректно вычисляет deadline с advance_days

**Может выполняться параллельно с:** 2.1, 2.2, 2.3, 2.5, 2.6

---

#### 2.5 Orders API (7 endpoints)

**Действия:**
- Создать `backend/src/schemas/order.py` → OrderResponse, OrderCreate, OrderUpdate, OrderCombo, OrderExtra
- Создать `backend/src/repositories/order.py` → OrderRepository
- Создать `backend/src/services/order.py` → OrderService (create_order, update_order с deadline check)
- Создать `backend/src/routers/orders.py` → 7 endpoints

**Endpoints:**
1. `GET /orders/availability/{date}` → check if can order
2. `GET /orders/availability/week` → availability for 7 days
3. `GET /orders` (self | manager) → list orders
4. `POST /orders` → create order
5. `GET /orders/{order_id}` (owner | manager) → get order
6. `PATCH /orders/{order_id}` (owner, before deadline) → update order
7. `DELETE /orders/{order_id}` (owner, before deadline | manager) → delete order

**Файлы:**
```
backend/src/schemas/order.py
backend/src/repositories/order.py
backend/src/services/order.py
backend/src/routers/orders.py
```

**Бизнес-логика:**
- `create_order()`:
  1. Check deadline via DeadlineService
  2. Validate combo via MenuService
  3. Calculate total_price (combo.price + sum(extras))
  4. Create order
- `update_order()`, `delete_order()`:
  1. Check deadline
  2. Check ownership (owner or manager)
  3. Update/delete

**Зависимости:** models.order, services.deadline, services.menu, auth.dependencies

**Критерий готовности:** Все 7 endpoints работают, deadline проверяется корректно

**Может выполняться параллельно с:** 2.1, 2.2, 2.3, 2.4, 2.6

---

#### 2.6 Summaries API (4 endpoints)

**Действия:**
- Создать `backend/src/schemas/summary.py` → SummaryResponse, SummaryCreate
- Создать `backend/src/repositories/summary.py` → SummaryRepository (aggregate_orders)
- Создать `backend/src/services/summary.py` → SummaryService (generate report)
- Создать `backend/src/routers/summaries.py` → 4 endpoints

**Endpoints:**
1. `GET /summaries` (manager) → list summaries
2. `POST /summaries` (manager) → create summary
3. `GET /summaries/{summary_id}` (manager) → get summary (format: json|csv|pdf)
4. `DELETE /summaries/{summary_id}` (manager) → delete summary

**Файлы:**
```
backend/src/schemas/summary.py
backend/src/repositories/summary.py
backend/src/services/summary.py
backend/src/routers/summaries.py
```

**Aggregation logic:**
- Группировка заказов по комбо, блюдам, extras
- Подсчёт количества и суммы
- Выгрузка в CSV/PDF (optional, может быть в следующей итерации)

**Зависимости:** models.summary, models.order, auth.dependencies

**Критерий готовности:** Отчёт корректно агрегирует данные, JSON формат работает

**Может выполняться параллельно с:** 2.1, 2.2, 2.3, 2.4, 2.5

---

### Фаза 3: Интеграция и тестирование (последовательно, после Фазы 2)

Выполняется **после завершения всех параллельных подзадач** Фазы 2.

#### 3.1 Main app и CORS

**Действия:**
- Создать `backend/src/main.py` (FastAPI app)
- Подключить все routers
- Настроить CORS
- Настроить exception handlers
- Добавить startup/shutdown events (database connection)

**Файлы:**
```
backend/src/main.py
```

**Структура main.py:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, users, cafes, menu, deadlines, orders, summaries

app = FastAPI(title="Lunch Order Bot API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(cafes.router, prefix="/api/v1")
app.include_router(menu.router, prefix="/api/v1")
app.include_router(deadlines.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(summaries.router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Критерий готовности:** `uvicorn src.main:app --reload` запускается без ошибок, `/health` отвечает 200

---

#### 3.2 Integration тесты

**Действия:**
- Создать `backend/tests/conftest.py` (fixtures: async_client, test_db)
- Написать тесты для каждого модуля:
  - `tests/test_auth.py` → Telegram auth, JWT validation
  - `tests/test_users.py` → 8 endpoints
  - `tests/test_cafes.py` → 6 endpoints
  - `tests/test_menu.py` → 9 endpoints
  - `tests/test_deadlines.py` → deadline logic
  - `tests/test_orders.py` → order creation, deadline checks
  - `tests/test_summaries.py` → report generation

**Файлы:**
```
backend/tests/
├── conftest.py
├── test_auth.py
├── test_users.py
├── test_cafes.py
├── test_menu.py
├── test_deadlines.py
├── test_orders.py
└── test_summaries.py
```

**Coverage target:** >= 80%

**Критерий готовности:** `pytest` проходит все тесты, coverage >= 80%

---

#### 3.3 Документация и deployment инструкции

**Действия:**
- Обновить `backend/README.md`:
  - Setup инструкции (database, migrations, env variables)
  - Запуск приложения (`uvicorn src.main:app`)
  - Запуск тестов (`pytest`)
- Создать `backend/.env.example` с примером переменных
- Проверить OpenAPI документацию (`/docs`)

**Файлы:**
```
backend/README.md
backend/.env.example
```

**Критерий готовности:** README содержит полные инструкции, `/docs` работает

---

### Фаза 4: Frontend Integration (последовательно, после Фазы 3)

#### 4.1 End-to-End тестирование с фронтендом

**Действия:**
- Запустить backend (`uvicorn src.main:app`)
- Запустить frontend (`npm run dev` в frontend_mini_app/)
- Проверить:
  1. Авторизация через Telegram WebApp initData
  2. Получение списка кафе
  3. Создание заказа
  4. CORS работает корректно
- Исправить найденные несоответствия

**Критерий готовности:** Frontend успешно взаимодействует с backend, заказ создаётся

---

## Параллельное выполнение

### Фаза 2: Рекомендация для Supervisor

Запусти **6 Coder субагентов параллельно** в одном сообщении:

```
Task(coder, subtask=2.1, "Users API: 8 endpoints")
Task(coder, subtask=2.2, "Cafes API: 6 endpoints")
Task(coder, subtask=2.3, "Menu API: 9 endpoints")
Task(coder, subtask=2.4, "Deadlines API: 2 endpoints")
Task(coder, subtask=2.5, "Orders API: 7 endpoints")
Task(coder, subtask=2.6, "Summaries API: 4 endpoints")
```

**Результаты:**
```
02-coder-1.md  (Users API)
02-coder-2.md  (Cafes API)
02-coder-3.md  (Menu API)
02-coder-4.md  (Deadlines API)
02-coder-5.md  (Orders API)
02-coder-6.md  (Summaries API)
```

**Проверка конфликтов после завершения:**
- Каждый модуль работает со своими файлами (schemas, repositories, services, routers)
- Единственный общий файл — `main.py` (обновляется в Фазе 3)
- Импорты между модулями минимальны (только auth.dependencies)

---

## Риски и зависимости

### Риски

| Риск | Вероятность | Mitigation |
|------|-------------|------------|
| Неправильная валидация Telegram initData | Средняя | Использовать проверенный алгоритм из официальной документации, тесты |
| Ошибки в deadline logic (advance_days) | Средняя | Unit тесты с различными сценариями (weekday, advance_days) |
| Конфликты при merge параллельных подзадач | Низкая | Чёткое разделение файлов, проверка после Фазы 2 |
| Несовместимость с frontend API | Низкая | Frontend уже имеет TypeScript типы, следовать спецификации |
| Проблемы с производительностью (N+1 queries) | Средняя | Использовать `selectinload()` для relationships, индексы в БД |

### Зависимости между фазами

```
Фаза 1.1 (init)
    ↓
Фаза 1.2 (models + migrations)
    ↓
Фаза 1.3 (auth)
    ↓
Фаза 2 (parallel API modules) — 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
    ↓
Фаза 3.1 (main app integration)
    ↓
Фаза 3.2 (tests)
    ↓
Фаза 3.3 (docs)
    ↓
Фаза 4 (frontend integration)
```

### Зависимости между модулями

- **Orders** зависит от **Deadlines** (check availability) и **Menu** (validate combo)
- Все модули зависят от **Auth** (get_current_user, require_manager)
- Все модули зависят от **Models** (SQLAlchemy)

**Важно:** В Фазе 2 Orders (2.5) может разрабатываться параллельно, так как зависимости — это только импорты функций. Deadlines и Menu будут готовы к моменту интеграции в Фазе 3.

---

## Summary

### Архитектура

- **Clean Architecture** с 4 слоями (Models, Repositories, Services, Routers)
- **Async** SQLAlchemy 2.0 + asyncpg
- **Telegram WebApp Auth** → JWT tokens
- **PostgreSQL 17** с JSONB columns
- **Alembic** для миграций
- **Pydantic** для валидации
- **FastAPI** с Dependency Injection

### Подзадачи для Coder

**Последовательно (Фаза 1):**
1. 1.1 Инициализация проекта
2. 1.2 Database + Models
3. 1.3 Авторизация

**Параллельно (Фаза 2):**
4. 2.1 Users API
5. 2.2 Cafes API
6. 2.3 Menu API
7. 2.4 Deadlines API
8. 2.5 Orders API
9. 2.6 Summaries API

**Последовательно (Фаза 3):**
10. 3.1 Main app + CORS
11. 3.2 Integration тесты
12. 3.3 Документация

**Последовательно (Фаза 4):**
13. 4.1 Frontend integration

### Метрики

- **~35 endpoints** (8+6+9+2+7+4 = 36)
- **7 таблиц** в БД
- **6 параллельных подзадач** (Фаза 2)
- **Coverage target:** >= 80%

### Следующий шаг

Запустить **Coder субагент** для подзадачи **1.1** (Инициализация проекта).
