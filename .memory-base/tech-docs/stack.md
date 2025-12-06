# Tech Stack

## Backend

### Core
- Python >= 3.13
- PostgreSQL 17
- Kafka
- Redis

### Frameworks & Libraries

**Production:**
- faststream >= 0.6.3 — async message broker (Kafka integration)
- fastapi >= 0.120.0 — web framework
- uvicorn >= 0.38.0 — ASGI server
- pydantic >= 2.12.0 — data validation
- sqlalchemy >= 2.0.44 — ORM (async)
- asyncpg >= 0.31.0 — async PostgreSQL driver
- alembic >= 1.17.0 — database migrations
- redis >= 5.0.0 — async Redis client for caching
- aiogram >= 3.0.0 — Telegram Bot API framework
- google-genai >= 1.0.0 — Google Generative AI (Gemini API)
- apscheduler >= 3.10.0 — task scheduler for batch jobs
- structlog — structured logging

**Development:**
- mypy >= 1.19.0 — static type checker
- ruff >= 0.14.0 — linter & formatter
- pytest >= 8.0.0 — testing framework

---

## Frontend (Telegram Mini App)

**Location:** `frontend_mini_app/`

### Core
- Next.js 16.0.7 — React framework (App Router)
- React 19.2.0
- TypeScript 5

### Styling
- Tailwind CSS 4 — utility-first CSS
- PostCSS

### Libraries
- react-icons 5.5.0 — icon library (Font Awesome 6)

### Development
- ESLint 9 + eslint-config-next

### Scripts
```bash
npm run dev      # development server (localhost:3000)
npm run build    # production build
npm run start    # production server
npm run lint     # eslint check
```

---

## Sources

### Backend
- https://pypi.org/project/faststream/
- https://pypi.org/project/fastapi/
- https://pypi.org/project/uvicorn/
- https://pypi.org/project/pydantic/
- https://pypi.org/project/SQLAlchemy/
- https://pypi.org/project/asyncpg/
- https://pypi.org/project/alembic/
- https://pypi.org/project/mypy/
- https://pypi.org/project/ruff/

### Frontend
- https://nextjs.org/docs
- https://react.dev/
- https://tailwindcss.com/docs
- https://react-icons.github.io/react-icons/
