# Lunch Order Bot - Backend API

## Overview
Backend API для Telegram-бота заказа обедов. Предоставляет REST API для управления кафе, меню, заказами и пользователями.

## Tech Stack
- Python 3.13+
- FastAPI 0.115+
- PostgreSQL 17
- SQLAlchemy 2.0+ (async)
- Alembic (migrations)
- JWT authentication
- Telegram WebApp validation

## Requirements
- Python >= 3.13
- PostgreSQL >= 17
- pip

## Installation

1. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. For development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

## Running

Development server (with auto-reload):
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Production server:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

After starting the server, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing

Run all tests:
```bash
pytest tests/ -v
```

With coverage report:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

Run specific test suite:
```bash
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests only
```

Current coverage: **78%** (60 tests)

## Project Structure

```
backend/
├── src/
│   ├── auth/              # Authentication (Telegram, JWT)
│   │   ├── dependencies.py   # Auth dependencies (CurrentUser, ManagerUser)
│   │   ├── jwt.py            # JWT token creation/validation
│   │   ├── schemas.py        # Auth request/response schemas
│   │   └── telegram.py       # Telegram WebApp validation
│   ├── models/            # SQLAlchemy models
│   │   ├── cafe.py
│   │   ├── deadline.py
│   │   ├── menu_item.py
│   │   ├── order.py
│   │   └── user.py
│   ├── repositories/      # Database operations (CRUD)
│   │   ├── cafe.py
│   │   ├── deadline.py
│   │   ├── menu_item.py
│   │   ├── order.py
│   │   └── user.py
│   ├── routers/          # API endpoints
│   │   ├── auth.py
│   │   ├── cafes.py
│   │   ├── deadlines.py
│   │   ├── menu.py
│   │   ├── orders.py
│   │   ├── summaries.py
│   │   └── users.py
│   ├── schemas/          # Pydantic schemas (validation)
│   │   ├── cafe.py
│   │   ├── deadline.py
│   │   ├── menu_item.py
│   │   ├── order.py
│   │   └── user.py
│   ├── services/         # Business logic
│   │   ├── cafe.py
│   │   ├── deadline.py
│   │   ├── menu_item.py
│   │   ├── order.py
│   │   ├── summary.py
│   │   └── user.py
│   ├── config.py         # Configuration (env vars)
│   ├── database.py       # Database connection & session
│   └── main.py           # FastAPI application
├── tests/                # Test suite
│   ├── conftest.py          # Shared fixtures
│   ├── unit/                # Unit tests (services, auth)
│   └── integration/         # Integration tests (API endpoints)
├── alembic/              # Database migrations
├── .env.example          # Environment variables template
└── pyproject.toml        # Project configuration & dependencies
```

## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/telegram` | Authenticate via Telegram WebApp | - |

### Users
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/users` | List all users | Manager |
| GET | `/api/v1/users/me` | Get current user | User |
| PATCH | `/api/v1/users/{id}` | Update user | Manager |
| DELETE | `/api/v1/users/{id}` | Delete user | Manager |

### Cafes
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/cafes` | List cafes | User |
| POST | `/api/v1/cafes` | Create cafe | Manager |
| GET | `/api/v1/cafes/{id}` | Get cafe by ID | User |
| PATCH | `/api/v1/cafes/{id}` | Update cafe | Manager |
| DELETE | `/api/v1/cafes/{id}` | Delete cafe | Manager |
| PATCH | `/api/v1/cafes/{id}/status` | Update cafe status | Manager |

### Menu Items
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/menu` | List menu items | User |
| POST | `/api/v1/menu` | Create menu item | Manager |
| GET | `/api/v1/menu/{id}` | Get menu item | User |
| PATCH | `/api/v1/menu/{id}` | Update menu item | Manager |
| DELETE | `/api/v1/menu/{id}` | Delete menu item | Manager |
| PATCH | `/api/v1/menu/{id}/status` | Update menu item status | Manager |

### Deadlines
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/deadlines` | List deadlines | User |
| POST | `/api/v1/deadlines` | Create deadline | Manager |
| GET | `/api/v1/deadlines/{id}` | Get deadline | User |
| PATCH | `/api/v1/deadlines/{id}` | Update deadline | Manager |
| DELETE | `/api/v1/deadlines/{id}` | Delete deadline | Manager |

### Orders
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/orders` | List orders (own or all for manager) | User |
| POST | `/api/v1/orders` | Create order | User |
| GET | `/api/v1/orders/{id}` | Get order by ID | User/Manager |
| PATCH | `/api/v1/orders/{id}` | Update order (before deadline) | User/Manager |
| DELETE | `/api/v1/orders/{id}` | Delete order (before deadline) | User/Manager |
| GET | `/api/v1/orders/availability/week` | Get 7-day availability | User |
| GET | `/api/v1/orders/availability/{date}` | Check availability for date | User |

### Summaries
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/summaries` | List order summaries | Manager |

### Health Check
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check endpoint | - |

See full API documentation with request/response schemas at `/docs` after starting the server.

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Yes | - |
| `JWT_SECRET_KEY` | JWT signing key (min 32 chars) | Yes | - |
| `JWT_ALGORITHM` | JWT algorithm | No | HS256 |
| `JWT_EXPIRE_DAYS` | Token expiration in days | No | 7 |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | No | ["http://localhost:3000"] |

Example `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/lunch_bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
JWT_SECRET_KEY=your-very-long-secret-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:3000"]
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback last migration:
```bash
alembic downgrade -1
```

## Development Tools

Linting:
```bash
ruff check src/ tests/
```

Type checking:
```bash
mypy src/
```

Format code:
```bash
ruff format src/ tests/
```

## Architecture

### Layered Architecture
1. **Routers** (`src/routers/`) - HTTP layer, request validation, response formatting
2. **Services** (`src/services/`) - Business logic, orchestration
3. **Repositories** (`src/repositories/`) - Database operations (CRUD)
4. **Models** (`src/models/`) - SQLAlchemy ORM models
5. **Schemas** (`src/schemas/`) - Pydantic models for validation

### Authentication Flow
1. Frontend sends Telegram WebApp `initData` to `/api/v1/auth/telegram`
2. Backend validates `initData` using HMAC-SHA256 with bot token
3. User is created/updated in database
4. JWT token is generated and returned
5. Frontend includes JWT in `Authorization: Bearer <token>` header

### Authorization
- **User role**: Can manage own orders, view cafes/menu
- **Manager role**: Full access to all resources (users, cafes, menu, orders)

## License

Proprietary
