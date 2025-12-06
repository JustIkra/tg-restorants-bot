# Quick Start Guide

Быстрый старт для локальной разработки Lunch Order Bot.

## Требования

- Docker & Docker Compose v2.20+
- Node.js 20+ (для локальной разработки frontend)
- Python 3.13+ (для локальной разработки backend)
- Git

## Быстрый старт (Docker)

### 1. Клонировать репозиторий

```bash
git clone <repository-url>
cd tg_bot
```

### 2. Настроить переменные окружения

```bash
# Backend
cp backend/.env.example backend/.env
# Отредактировать backend/.env - установить TELEGRAM_BOT_TOKEN и JWT_SECRET_KEY

# Frontend
cp frontend_mini_app/.env.example frontend_mini_app/.env
```

**Обязательные переменные в backend/.env:**
- `TELEGRAM_BOT_TOKEN` - получить от @BotFather
- `JWT_SECRET_KEY` - сгенерировать: `openssl rand -hex 32`

### 3. Запустить сервисы

```bash
docker-compose up -d
```

Это запустит все сервисы:
- PostgreSQL 17 (база данных)
- Kafka (message broker)
- Redis (кэш)
- Backend API (FastAPI)
- Frontend (Next.js)
- Telegram Bot (aiogram)
- Workers (notifications + recommendations)
- Nginx (reverse proxy)

### 4. Применить миграции БД

```bash
docker exec lunch-bot-backend alembic upgrade head
```

### 5. Проверить работоспособность

- Frontend: http://localhost:80
- Backend API: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 6. Создать тестовые данные (опционально)

```bash
# Войти в контейнер backend
docker exec -it lunch-bot-backend bash

# Запустить Python shell
python -c "
from src.database import get_session
from src.models import User, Cafe, MenuItem
# Создать тестовых пользователей, кафе, меню
"
```

## Локальная разработка (без Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Запустить только зависимости в Docker
docker-compose up -d postgres redis kafka

# Запустить сервер
uvicorn src.main:app --reload
```

Backend будет доступен на http://localhost:8000

### Frontend

```bash
cd frontend_mini_app
npm install
npm run dev
```

Frontend будет доступен на http://localhost:3000

### Telegram Bot

```bash
cd backend
source .venv/bin/activate
python -m src.telegram.bot
```

### Workers

```bash
# Notifications worker
cd backend
source .venv/bin/activate
python -m workers.notifications

# Recommendations worker (в отдельном терминале)
python -m workers.recommendations
```

## Остановка сервисов

```bash
# Остановить все контейнеры
docker-compose down

# Остановить и удалить volumes (БД, кэш)
docker-compose down -v
```

## Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker logs -f lunch-bot-backend
docker logs -f lunch-bot-frontend
docker logs -f lunch-bot-telegram
```

## Troubleshooting

### Backend не запускается
- Проверьте, что PostgreSQL, Kafka, Redis здоровы: `docker-compose ps`
- Проверьте логи: `docker logs lunch-bot-backend`
- Проверьте переменные окружения в `backend/.env`

### Frontend не подключается к Backend
- Проверьте `NEXT_PUBLIC_API_URL` в `frontend_mini_app/.env`
- Для Docker: должно быть `http://localhost/api/v1`
- Для локальной разработки: `http://localhost:8000/api/v1`

### Миграции не применяются
```bash
# Проверить статус миграций
docker exec lunch-bot-backend alembic current

# Применить миграции заново
docker exec lunch-bot-backend alembic upgrade head
```

### Kafka не стартует
- Kafka требует минимум 4GB RAM для Docker
- Проверьте: `docker stats lunch-bot-kafka`
- При необходимости увеличьте лимиты Docker

## Следующие шаги

- [Production Deployment](production.md) - развертывание в продакшн
- [Environment Variables](environment.md) - полный справочник переменных окружения
- [Troubleshooting](../troubleshooting.md) - решение проблем
