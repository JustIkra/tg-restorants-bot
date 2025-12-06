# Environment Variables Reference

Полный справочник переменных окружения для Lunch Order Bot.

## Backend (.env)

### Database

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string | `postgresql+asyncpg://postgres:password@localhost:5432/lunch_bot` |

**Notes:**
- Формат: `postgresql+asyncpg://user:password@host:port/dbname`
- Используйте `asyncpg` драйвер для async SQLAlchemy
- В production используйте сильный пароль

### JWT Authentication

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `JWT_SECRET_KEY` | Yes | - | Secret key for signing JWT tokens | `a1b2c3d4...` (64 chars) |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm | `HS256` |
| `JWT_EXPIRE_DAYS` | No | `7` | Token expiration in days | `7` |

**Notes:**
- Генерируйте `JWT_SECRET_KEY`: `openssl rand -hex 32`
- **Критично**: Используйте разные ключи для dev/production
- Никогда не коммитьте реальный ключ в git

### Telegram Bot

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Bot token from @BotFather | `123456:ABC-DEF...` |
| `TELEGRAM_MINI_APP_URL` | Yes | - | URL where Mini App is hosted | `https://lunchbot.vibe-labs.ru` |

**Notes:**
- Получите токен у @BotFather в Telegram
- `TELEGRAM_MINI_APP_URL` должен быть HTTPS в production
- Используйте ngrok для локального тестирования Mini App

### Kafka

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `KAFKA_BROKER_URL` | Yes | `localhost:9092` | Kafka broker address | `kafka:29092` (Docker), `localhost:9092` (local) |

**Notes:**
- В Docker используйте имя сервиса: `kafka:29092`
- Локально: `localhost:9092`
- Kafka требует минимум 4GB RAM

### Redis

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `REDIS_URL` | Yes | `redis://localhost:6379` | Redis connection URL | `redis://redis:6379` (Docker) |

**Notes:**
- Формат: `redis://host:port/db`
- В Docker используйте имя сервиса: `redis:6379`
- TTL для рекомендаций: 24 часа

### Gemini AI (Optional)

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `GEMINI_API_KEYS` | No | - | Comma-separated Gemini API keys | `key1,key2,key3` |
| `GEMINI_MODEL` | No | `gemini-2.0-flash-exp` | Gemini model name | `gemini-2.0-flash-exp` |
| `GEMINI_MAX_REQUESTS_PER_KEY` | No | `195` | Requests before key rotation | `195` |

**Notes:**
- Получите API ключи: https://aistudio.google.com/
- Используйте несколько ключей для масштабирования (каждый ключ = 200 req/day)
- Без ключей рекомендации будут отключены
- Free tier: 200 запросов в день на ключ
- Автоматическая ротация после 195 запросов (резерв 5 для safety)

### CORS

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `CORS_ORIGINS` | Yes | - | JSON array of allowed origins | `["http://localhost","https://web.telegram.org"]` |

**Notes:**
- Формат: JSON array строк
- Development: `["http://localhost","https://web.telegram.org"]`
- Production: `["https://your-domain.com","https://web.telegram.org"]`
- `https://web.telegram.org` нужен для Telegram WebApp iframe

## Frontend (.env)

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Yes | - | Backend API URL | `http://localhost:8000/api/v1` |

**Notes:**
- `NEXT_PUBLIC_` префикс обязателен для Next.js (доступно в браузере)
- Development (локально): `http://localhost:8000/api/v1`
- Development (Docker): `http://localhost/api/v1` (через nginx)
- Development (ngrok): `https://your-ngrok-url/api/v1`
- Production: `https://your-domain.com/api/v1`

## Production Secrets

### Docker Compose (.env)

Для `docker-compose.prod.yml` создайте корневой `.env`:

```bash
# PostgreSQL password
POSTGRES_PASSWORD=strong_password_here

# Backend environment file
BACKEND_ENV_FILE=./backend/.env.production

# Frontend environment file
FRONTEND_ENV_FILE=./frontend_mini_app/.env.production
```

## Полный пример (Development)

### backend/.env

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/lunch_bot

# Kafka
KAFKA_BROKER_URL=localhost:9092

# Redis
REDIS_URL=redis://localhost:6379

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_MINI_APP_URL=http://localhost

# Gemini API (optional)
GEMINI_API_KEYS=AIzaSyA...key1,AIzaSyB...key2
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MAX_REQUESTS_PER_KEY=195

# JWT
JWT_SECRET_KEY=dev_secret_key_replace_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost","https://web.telegram.org"]
```

### frontend_mini_app/.env

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Полный пример (Production)

### backend/.env.production

```bash
# Database (strong password!)
DATABASE_URL=postgresql+asyncpg://postgres:Xk9#mP2$vL8@qR5&postgres:5432/lunch_bot

# Kafka
KAFKA_BROKER_URL=kafka:29092

# Redis
REDIS_URL=redis://redis:6379

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_MINI_APP_URL=https://lunchbot.vibe-labs.ru

# Gemini API
GEMINI_API_KEYS=AIzaSyA...key1,AIzaSyB...key2,AIzaSyC...key3
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MAX_REQUESTS_PER_KEY=195

# JWT (generate new key!)
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7

# CORS (production domain!)
CORS_ORIGINS=["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]
```

### frontend_mini_app/.env.production

```bash
NEXT_PUBLIC_API_URL=https://lunchbot.vibe-labs.ru/api/v1
```

## Security Best Practices

### 1. Secrets Management

**НИКОГДА не коммитьте в git:**
- `.env`
- `.env.production`
- `.env.local`
- Любые файлы с реальными токенами/паролями

**Проверьте .gitignore:**
```bash
# .gitignore
.env
.env.*
!.env.example
```

### 2. Strong Passwords

```bash
# Генерация сильных паролей
openssl rand -base64 32  # PostgreSQL password
openssl rand -hex 32     # JWT secret key
```

### 3. Key Rotation

Регулярно меняйте:
- `JWT_SECRET_KEY` (раз в год или при утечке)
- `POSTGRES_PASSWORD` (раз в год)
- `TELEGRAM_BOT_TOKEN` (при компрометации)
- `GEMINI_API_KEYS` (при превышении лимитов)

### 4. Environment Separation

Используйте **разные** ключи/пароли для:
- Development
- Staging
- Production

### 5. Access Control

```bash
# Ограничьте доступ к .env файлам
chmod 600 backend/.env.production
chmod 600 frontend_mini_app/.env.production

# Только владелец может читать/писать
ls -la backend/.env.production
# -rw------- 1 user group ... backend/.env.production
```

## Troubleshooting

### Backend не может подключиться к PostgreSQL

**Проблема:** `connection refused` или `timeout`

**Решение:**
1. Проверьте `DATABASE_URL`:
   - Docker: `postgres:5432` (имя сервиса)
   - Локально: `localhost:5432`
2. Проверьте PostgreSQL запущен: `docker ps | grep postgres`
3. Проверьте пароль совпадает с `POSTGRES_PASSWORD` в docker-compose

### Frontend не может достучаться до Backend API

**Проблема:** CORS errors или 404

**Решение:**
1. Проверьте `NEXT_PUBLIC_API_URL`:
   - Локально: `http://localhost:8000/api/v1`
   - Docker: `http://localhost/api/v1` (через nginx)
2. Проверьте Backend `CORS_ORIGINS` включает frontend URL
3. Убедитесь nginx проксирует `/api/v1/` на backend

### JWT токены не работают

**Проблема:** 401 Unauthorized

**Решение:**
1. Проверьте `JWT_SECRET_KEY` одинаковый на всех сервисах
2. Проверьте `JWT_ALGORITHM=HS256`
3. Проверьте токен не истек (`JWT_EXPIRE_DAYS`)
4. Проверьте Telegram WebApp инициализирован корректно

### Gemini API ключи не работают

**Проблема:** 401 или 429 ошибки

**Решение:**
1. Проверьте ключи валидны: https://aistudio.google.com/
2. Проверьте формат: `GEMINI_API_KEYS=key1,key2,key3` (без пробелов)
3. Проверьте квоты не исчерпаны (200 req/day на ключ)
4. Добавьте больше ключей для масштабирования

### Redis кэш не работает

**Проблема:** Рекомендации не кэшируются

**Решение:**
1. Проверьте `REDIS_URL`:
   - Docker: `redis://redis:6379`
   - Локально: `redis://localhost:6379`
2. Проверьте Redis запущен: `docker ps | grep redis`
3. Проверьте TTL: `docker exec lunch-bot-redis redis-cli TTL recommendations:*`

## Дополнительные ресурсы

- [Quick Start Guide](quick-start.md) - локальная разработка
- [Production Deployment](production.md) - развертывание в продакшн
- [Troubleshooting](../troubleshooting.md) - решение проблем
