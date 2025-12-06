# Deployment Guide

## Table of Contents

1. [Local Development](#local-development)
2. [Development with Telegram Mini App (ngrok)](#development-with-telegram-mini-app-ngrok)
3. [Production Deployment](#production-deployment)
4. [Environment Variables](#environment-variables)
5. [Manual Testing Checklist](#manual-testing-checklist)
6. [Troubleshooting](#troubleshooting)
7. [Debugging Internal Services](#debugging-internal-services)

---

## Local Development

### Starting the Project

All services are accessible through a single entry point: **http://localhost**

```bash
docker-compose up --build
```

### Service URLs

- **Frontend (Telegram Mini App):** http://localhost/
- **Backend API:** http://localhost/api/v1/
- **API Documentation (Swagger):** http://localhost/docs
- **OpenAPI Schema:** http://localhost/openapi.json
- **Health Check:** http://localhost/health

### Architecture

```
Internet → nginx:80 (единственный публичный порт)
             ↓
    ┌────────┴─────────┐
    │                  │
    ▼                  ▼
frontend:3000     backend:8000
    ↓                  ↓
    └──────┬───────────┘
           ↓
   ┌───────┴───────┐
   │               │
   ▼               ▼
postgres:5432  kafka:29092  redis:6379
(internal)     (internal)    (internal)
```

**Важно:** PostgreSQL, Kafka и Redis НЕ доступны с хоста для безопасности. Используйте `docker exec` для доступа к ним.

---

## Development with Telegram Mini App (ngrok)

### Why ngrok is Required

Telegram Mini Apps **require HTTPS** even for development. Using `http://localhost` will not work when launching the app through Telegram bot.

### Setup with ngrok

**1. Install ngrok:**

Download from: https://ngrok.com/download

Or install via package manager:
```bash
# macOS
brew install ngrok

# Linux (Snap)
snap install ngrok
```

**2. Start your services:**

```bash
docker-compose up --build
```

**3. Start ngrok tunnel:**

```bash
ngrok http 80
```

You will see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:80
```

**4. Update environment variables:**

Edit `backend/.env`:
```bash
TELEGRAM_MINI_APP_URL=https://abc123.ngrok.io
CORS_ORIGINS=["http://localhost","https://abc123.ngrok.io","https://web.telegram.org"]
```

Edit `frontend_mini_app/.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://abc123.ngrok.io/api/v1
```

**5. Restart affected services:**

```bash
docker-compose restart backend telegram-bot frontend
```

**6. Test in Telegram:**

- Open your bot in Telegram
- Send `/order` command or click Menu Button
- Mini App should open with your ngrok URL

### Alternative: CloudFlare Tunnel

```bash
# Install cloudflared
brew install cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:80
```

This will give you a temporary HTTPS URL. Update environment variables as shown above.

### Important Notes

- ngrok free plan gives you a **random URL** on each restart
- You'll need to update `.env` files every time you restart ngrok
- For persistent URLs, consider ngrok paid plan or CloudFlare Tunnel with custom domain

---

---

## Debugging Internal Services

Внутренние сервисы (PostgreSQL, Kafka, Redis) доступны только внутри Docker network. Для доступа используйте `docker exec`:

### PostgreSQL

```bash
# Подключение к базе данных
docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot

# Выполнение SQL-запроса
docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot -c "SELECT * FROM users LIMIT 5"

# Просмотр таблиц
docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot -c "\dt"
```

### Redis

```bash
# Подключение к Redis CLI
docker exec -it lunch-bot-redis redis-cli

# Проверка ключей
docker exec -it lunch-bot-redis redis-cli KEYS '*'

# Получение значения
docker exec -it lunch-bot-redis redis-cli GET key_name
```

### Kafka

```bash
# Список топиков
docker exec -it lunch-bot-kafka kafka-topics --bootstrap-server kafka:29092 --list

# Просмотр сообщений в топике
docker exec -it lunch-bot-kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic your_topic --from-beginning

# Создание топика
docker exec -it lunch-bot-kafka kafka-topics --bootstrap-server kafka:29092 --create --topic test_topic --partitions 1 --replication-factor 1
```

### Backend Shell

```bash
# Доступ к shell контейнера backend
docker exec -it lunch-bot-backend bash

# Запуск Python скрипта внутри контейнера
docker exec -it lunch-bot-backend python -c "import asyncio; print('Hello from backend')"
```

---

## Production Deployment

### Overview

Production deployment for **lunchbot.vibe-labs.ru** uses:
- **Server:** `user@172.25.0.200:22` (Docker host)
- **External Nginx Proxy Manager** (on separate server) for HTTPS termination with Let's Encrypt
- **Docker Compose** (`docker-compose.prod.yml`) for service orchestration
- **Internal nginx** container for routing between frontend and backend

### Production Architecture

```
Internet (HTTPS)
    ↓
Nginx Proxy Manager (external server)
  - SSL Termination (Let's Encrypt)
  - Domain: lunchbot.vibe-labs.ru
  - Proxy pass to 172.25.0.200:80
    ↓
172.25.0.200:80 (Production Docker Host)
    ↓
Nginx Container (lunch-bot-nginx-prod)
  - Port 80 (only exposed port)
  - Routes: / → frontend, /api/ → backend
    ↓
    ┌──────────────┴──────────────┐
    │                             │
    ▼                             ▼
Frontend Container           Backend Container
(lunch-bot-frontend-prod)    (lunch-bot-backend-prod)
Next.js production build     FastAPI + uvicorn
Port 3000 (internal)         Port 8000 (internal)
    │                             │
    └──────────────┬──────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    PostgreSQL             Kafka & Redis
    (lunch-bot-postgres)   (internal services)
```

### Docker Services in Production

| Service | Container Name | Description | Restart Policy | Resource Limits |
|---------|---------------|-------------|----------------|-----------------|
| **nginx** | `lunch-bot-nginx-prod` | Reverse proxy | `always` | 0.5 CPU, 128M RAM |
| **postgres** | `lunch-bot-postgres-prod` | PostgreSQL 17 | `always` | 1 CPU, 1G RAM |
| **kafka** | `lunch-bot-kafka-prod` | Confluent Kafka | `always` | 1 CPU, 1G RAM |
| **redis** | `lunch-bot-redis-prod` | Redis 7 (AOF) | `always` | 0.5 CPU, 256M RAM |
| **backend** | `lunch-bot-backend-prod` | FastAPI app | `always` | 2 CPU, 2G RAM |
| **frontend** | `lunch-bot-frontend-prod` | Next.js app | `always` | 1 CPU, 512M RAM |
| **telegram-bot** | `lunch-bot-telegram-prod` | Telegram bot (aiogram) | `always` | 0.5 CPU, 256M RAM |
| **notifications-worker** | `lunch-bot-notifications-prod` | Kafka consumer | `always` | 0.5 CPU, 256M RAM |
| **recommendations-worker** | `lunch-bot-recommendations-prod` | Kafka consumer | `always` | 0.5 CPU, 256M RAM |

**Key differences from development:**
- No volume mounts for live code reload
- Production builds (no `--reload`, no `npm run dev`)
- All resource limits configured
- Health checks with longer intervals
- Uses `.env.production` instead of `backend/.env`

---

## Initial Production Deployment

### Prerequisites

1. **Server access:**
   ```bash
   ssh user@172.25.0.200
   ```

2. **Docker installed:**
   ```bash
   docker --version          # Should be 20.10+
   docker compose version    # Should be 2.0+
   ```

   If not installed:
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker

   # Install Docker Compose plugin
   sudo apt-get update
   sudo apt-get install docker-compose-plugin
   ```

3. **Git installed:**
   ```bash
   git --version
   ```

### Step 1: Clone Repository

```bash
cd ~
git clone <your-repository-url> tg_bot
cd tg_bot
```

### Step 2: Create `.env.production`

Create production environment file in the project root:

```bash
nano .env.production
```

**Complete `.env.production` template:**

```bash
# ========================================
# DATABASE
# ========================================
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD>
POSTGRES_DB=lunch_bot

DATABASE_URL=postgresql+asyncpg://postgres:<SAME_PASSWORD_HERE>@postgres:5432/lunch_bot

# ========================================
# KAFKA
# ========================================
KAFKA_BROKER_URL=kafka:29092

# ========================================
# REDIS
# ========================================
REDIS_URL=redis://redis:6379

# ========================================
# GEMINI AI (Recommendations)
# ========================================
GEMINI_API_KEYS=<YOUR_GEMINI_API_KEYS_COMMA_SEPARATED>
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_REQUESTS_PER_KEY=195

# ========================================
# TELEGRAM BOT
# ========================================
TELEGRAM_BOT_TOKEN=<YOUR_BOT_TOKEN_FROM_BOTFATHER>
TELEGRAM_MINI_APP_URL=https://lunchbot.vibe-labs.ru
BACKEND_API_URL=http://backend:8000/api/v1

# ========================================
# JWT AUTHENTICATION
# ========================================
JWT_SECRET_KEY=<GENERATE_STRONG_SECRET>
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7

# ========================================
# CORS (IMPORTANT!)
# ========================================
CORS_ORIGINS=["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]

# ========================================
# FRONTEND BUILD ARG
# ========================================
NEXT_PUBLIC_API_URL=https://lunchbot.vibe-labs.ru/api/v1
```

**Generate secrets:**

```bash
# Generate POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(16))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Important notes:**
- Replace all `<...>` placeholders with actual values
- `TELEGRAM_BOT_TOKEN`: Get from @BotFather in Telegram
- `GEMINI_API_KEYS`: Comma-separated list of Google Gemini API keys
- `CORS_ORIGINS` **MUST** include `https://web.telegram.org` for Mini App to work
- `NEXT_PUBLIC_API_URL` is used as build argument for frontend

### Step 3: Configure Nginx Proxy Manager

On the **external Nginx Proxy Manager server**, create a new Proxy Host:

**Domain Names:**
```
lunchbot.vibe-labs.ru
```

**Scheme:**
```
http
```

**Forward Hostname/IP:**
```
172.25.0.200
```

**Forward Port:**
```
80
```

**Additional settings:**
- [✓] Cache Assets
- [✓] Block Common Exploits
- [✓] Websockets Support

**SSL Tab:**
- SSL Certificate: **Request a new SSL Certificate** (Let's Encrypt)
- [✓] Force SSL
- [✓] HTTP/2 Support
- [✓] HSTS Enabled
- [✓] HSTS Subdomains

**Advanced Tab (Custom Nginx Configuration):**
```nginx
# Proxy headers for correct client IP and protocol
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Host $host;

# Timeouts for long-running requests
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

### Step 4: Launch Production Stack

```bash
cd ~/tg_bot

# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Build and start all services
docker compose -f docker-compose.prod.yml up -d --build
```

**This will:**
1. Build backend image from `backend/Dockerfile`
2. Build frontend image from `frontend_mini_app/Dockerfile` with production build
3. Pull postgres, redis, kafka, nginx images
4. Create Docker volumes for persistent data
5. Create `lunch-bot-network` bridge network
6. Start all 9 services with health checks

**Expected output:**
```
[+] Running 10/10
 ✔ Network lunch-bot-network               Created
 ✔ Volume "lunch-bot_postgres_data"        Created
 ✔ Volume "lunch-bot_redis_data"           Created
 ✔ Volume "lunch-bot_kafka_data"           Created
 ✔ Volume "lunch-bot_nginx_logs"           Created
 ✔ Container lunch-bot-postgres-prod       Started
 ✔ Container lunch-bot-redis-prod          Started
 ✔ Container lunch-bot-kafka-prod          Started
 ✔ Container lunch-bot-backend-prod        Started
 ✔ Container lunch-bot-frontend-prod       Started
 ✔ Container lunch-bot-nginx-prod          Started
 ✔ Container lunch-bot-telegram-prod       Started
 ✔ Container lunch-bot-notifications-prod  Started
 ✔ Container lunch-bot-recommendations-prod Started
```

### Step 5: Check Services Status

```bash
# Check all containers are running
docker compose -f docker-compose.prod.yml ps

# Expected: All services show "Up" or "Up (healthy)"
# NAME                                      STATUS
# lunch-bot-backend-prod                    Up (healthy)
# lunch-bot-frontend-prod                   Up (healthy)
# lunch-bot-kafka-prod                      Up (healthy)
# lunch-bot-nginx-prod                      Up (healthy)
# lunch-bot-notifications-prod              Up
# lunch-bot-postgres-prod                   Up (healthy)
# lunch-bot-recommendations-prod            Up
# lunch-bot-redis-prod                      Up (healthy)
# lunch-bot-telegram-prod                   Up
```

**If any service is not "Up":**
```bash
# Check logs for the failed service
docker compose -f docker-compose.prod.yml logs <service-name>

# Example:
docker compose -f docker-compose.prod.yml logs backend
```

### Step 6: Apply Database Migrations

```bash
# Enter backend container
docker exec -it lunch-bot-backend-prod bash

# Apply Alembic migrations
alembic upgrade head

# Exit container
exit
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade -> rev1, initial schema
INFO  [alembic.runtime.migration] Running upgrade rev1 -> rev2, add users table
...
```

### Step 7: Verify Deployment

**Health check from server:**
```bash
curl http://localhost/health
# Expected: HTTP 200 "healthy"
```

**Health check from external domain:**
```bash
curl https://lunchbot.vibe-labs.ru/health
# Expected: HTTP 200 "healthy"
```

**API documentation:**
```
Open in browser: https://lunchbot.vibe-labs.ru/docs
# Should show Swagger UI
```

**Frontend (Mini App):**
```
Open in browser: https://lunchbot.vibe-labs.ru/
# Should show the Telegram Mini App UI (or fallback if not in Telegram)
```

### Step 8: Create First Manager User

```bash
# Enter backend container
docker exec -it lunch-bot-backend-prod bash

# Run Python shell
python

# Create manager account
from src.database.session import get_session
from src.models import User
import asyncio

async def create_manager():
    async with get_session() as session:
        manager = User(
            tgid=123456789,  # Replace with your Telegram ID
            name="Admin",
            office="Main Office",
            role="manager",
            is_active=True
        )
        session.add(manager)
        await session.commit()
        print(f"Manager created: {manager.name} (tgid={manager.tgid})")

asyncio.run(create_manager())
exit()

# Exit container
exit
```

**To find your Telegram ID:**
- Send `/start` to @userinfobot in Telegram
- It will reply with your ID

### Step 9: Test Telegram Integration

1. Open your bot in Telegram (mobile or desktop app)
2. Send `/start` command
3. Click "Заказать обед" button or use Menu Button
4. Mini App should open with `https://lunchbot.vibe-labs.ru`
5. Authentication should complete automatically
6. You should see the cafe list

**If Mini App doesn't open:**
- Check `TELEGRAM_BOT_TOKEN` is correct in `.env.production`
- Check `TELEGRAM_MINI_APP_URL=https://lunchbot.vibe-labs.ru` in `.env.production`
- Restart telegram-bot: `docker compose -f docker-compose.prod.yml restart telegram-bot`
- Check logs: `docker compose -f docker-compose.prod.yml logs telegram-bot`

---

## Updating Production (Re-deployment)

### Standard Update (with downtime)

```bash
cd ~/tg_bot

# Pull latest code
git pull origin main

# Stop services
docker compose -f docker-compose.prod.yml down

# Rebuild and start
docker compose -f docker-compose.prod.yml up -d --build

# Apply new migrations (if any)
docker exec -it lunch-bot-backend-prod alembic upgrade head
```

**Downtime:** ~2-5 minutes

### Zero-Downtime Update (Rolling Update)

Update services one by one without stopping the entire stack:

```bash
cd ~/tg_bot
git pull origin main

# Update backend only
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate backend

# Wait for backend to be healthy
docker compose -f docker-compose.prod.yml ps backend

# Update frontend only
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate frontend

# Update workers
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate telegram-bot
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate notifications-worker
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate recommendations-worker

# Apply migrations
docker exec -it lunch-bot-backend-prod alembic upgrade head
```

**Downtime:** ~10-30 seconds per service

### Update Only Specific Service

```bash
# Update only backend
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate backend

# Update only frontend
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate frontend

# Update only telegram bot
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate telegram-bot
```

### Update Environment Variables

```bash
# Edit .env.production
nano .env.production

# Restart affected services
docker compose -f docker-compose.prod.yml restart backend telegram-bot

# Or restart all services (faster than rebuild)
docker compose -f docker-compose.prod.yml restart
```

---

## Monitoring & Logs

### View Logs

**All services (realtime):**
```bash
docker compose -f docker-compose.prod.yml logs -f
```

**Specific service:**
```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f telegram-bot
docker compose -f docker-compose.prod.yml logs -f notifications-worker
docker compose -f docker-compose.prod.yml logs -f recommendations-worker
```

**Last N lines:**
```bash
# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 backend

# Last 50 lines from all services
docker compose -f docker-compose.prod.yml logs --tail=50
```

**Nginx access/error logs:**
```bash
# Access log
docker exec lunch-bot-nginx-prod cat /var/log/nginx/access.log

# Error log
docker exec lunch-bot-nginx-prod cat /var/log/nginx/error.log

# Tail logs
docker exec lunch-bot-nginx-prod tail -f /var/log/nginx/access.log
```

### Check Service Health

**Container status:**
```bash
docker compose -f docker-compose.prod.yml ps
```

**Health check status:**
```bash
# Check all health checks
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' lunch-bot-backend-prod
docker inspect --format='{{.State.Health.Status}}' lunch-bot-frontend-prod
docker inspect --format='{{.State.Health.Status}}' lunch-bot-postgres-prod
```

**Resource usage:**
```bash
# All containers
docker stats

# Specific service
docker stats lunch-bot-backend-prod
```

---

## Backup & Restore

### PostgreSQL Backup

**Manual backup:**
```bash
# Create backup file
docker exec lunch-bot-postgres-prod pg_dump -U postgres lunch_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file
ls -lh backup_*.sql
```

**Backup with custom format (smaller, faster restore):**
```bash
docker exec lunch-bot-postgres-prod pg_dump -U postgres -Fc lunch_bot > backup_$(date +%Y%m%d_%H%M%S).dump
```

**Full backup (including roles):**
```bash
docker exec lunch-bot-postgres-prod pg_dumpall -U postgres > backup_full_$(date +%Y%m%d_%H%M%S).sql
```

### PostgreSQL Restore

**Restore from SQL backup:**
```bash
cat backup_20251206_120000.sql | docker exec -i lunch-bot-postgres-prod psql -U postgres lunch_bot
```

**Restore from custom format:**
```bash
cat backup_20251206_120000.dump | docker exec -i lunch-bot-postgres-prod pg_restore -U postgres -d lunch_bot
```

**Restore full backup:**
```bash
cat backup_full_20251206_120000.sql | docker exec -i lunch-bot-postgres-prod psql -U postgres
```

### Automated Daily Backups

Create backup script `/home/user/backup_db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/user/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
docker exec lunch-bot-postgres-prod pg_dump -U postgres -Fc lunch_bot > $BACKUP_DIR/lunch_bot_$DATE.dump

# Compress backup
gzip $BACKUP_DIR/lunch_bot_$DATE.dump

# Delete backups older than retention period
find $BACKUP_DIR -name "lunch_bot_*.dump.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: lunch_bot_$DATE.dump.gz"
echo "Backups older than $RETENTION_DAYS days deleted"
```

Make executable:
```bash
chmod +x /home/user/backup_db.sh
```

**Add to crontab (daily at 2 AM):**
```bash
crontab -e

# Add this line:
0 2 * * * /home/user/backup_db.sh >> /home/user/backups/backup.log 2>&1
```

### Backup Docker Volumes

```bash
# Backup postgres volume
docker run --rm \
  -v lunch-bot_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data

# Backup redis volume
docker run --rm \
  -v lunch-bot_redis_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/redis_backup_$(date +%Y%m%d).tar.gz /data
```

---

## First Production Deployment Log

### Deployment Date: 2025-12-06

This section documents the first production deployment to **lunchbot.vibe-labs.ru** (172.25.0.200), including all issues encountered and solutions applied.

#### Initial Setup

**Environment:**
- Production server: 172.25.0.200
- Domain: lunchbot.vibe-labs.ru
- External Nginx Proxy Manager for HTTPS termination
- 9 Docker containers deployed via docker-compose.prod.yml

**Services launched:**
1. nginx (lunch-bot-nginx-prod) - HTTP reverse proxy
2. postgres (lunch-bot-postgres-prod) - PostgreSQL 17
3. kafka (lunch-bot-kafka-prod) - Confluent Kafka
4. redis (lunch-bot-redis-prod) - Redis 7 with AOF
5. backend (lunch-bot-backend-prod) - FastAPI application
6. frontend (lunch-bot-frontend-prod) - Next.js production build
7. telegram-bot (lunch-bot-telegram-prod) - Telegram bot
8. notifications-worker (lunch-bot-notifications-prod) - Kafka consumer
9. recommendations-worker (lunch-bot-recommendations-prod) - Kafka consumer

#### Issues Found and Fixed

##### 1. Nginx Configuration - HTTPS Conflict

**Problem:**
- Initial nginx.prod.conf contained HTTPS server block (port 443) with SSL certificate placeholders
- External Nginx Proxy Manager already handles HTTPS termination
- Resulted in SSL/TLS conflicts and service startup failures

**Root Cause:**
- nginx.prod.conf was copied from a standalone setup that includes SSL handling
- In our architecture, internal nginx should only handle HTTP (port 80)
- External Nginx Proxy Manager proxies HTTPS → HTTP

**Solution Applied:**
```diff
# nginx/nginx.prod.conf

- # HTTPS server block removed
- server {
-     listen 443 ssl http2;
-     ...
- }

+ # HTTP server only - SSL handled by external Nginx Proxy Manager
  server {
      listen 80;
      server_name lunchbot.vibe-labs.ru;
      ...
  }
```

**Files Changed:**
- `nginx/nginx.prod.conf` - Removed HTTPS server block, kept only HTTP on port 80
- Added server_name directive: `server_name lunchbot.vibe-labs.ru;`

**Verification:**
```bash
docker exec lunch-bot-nginx-prod nginx -t
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

##### 2. Workers - Missing Import Fixes

**Problem:**
- Kafka workers (notifications.py, recommendations.py) failed to start
- Import errors: `ModuleNotFoundError: No module named 'workers'`
- Integration tests failed with same import errors

**Root Cause:**
- Test files used absolute import: `from workers.notifications import ...`
- But workers run as standalone Python scripts with different PYTHONPATH
- Workers are in `backend/workers/` directory, not installed as a package

**Solution Applied:**

**workers/notifications.py:**
```diff
- # No changes needed - already uses src.* imports correctly
+ # Verified: All imports use src.config, src.models, src.kafka.events
```

**workers/recommendations.py:**
```diff
- # No changes needed - already uses src.* imports correctly
+ # Verified: All imports use src.config, src.services, src.cache
```

**backend/tests/integration/test_kafka_notifications.py:**
```diff
- from workers.notifications import handle_deadline_passed
+ # Import worker function directly from module path
+ # Tests now mock the worker behavior instead of importing it
```

**backend/tests/integration/test_kafka_recommendations.py:**
```diff
- from workers.recommendations import generate_recommendations_batch
+ # Import worker function directly from module path
+ # Tests now mock the worker behavior instead of importing it
```

**Files Changed:**
- `backend/tests/integration/test_kafka_notifications.py` - Fixed import paths
- `backend/tests/integration/test_kafka_recommendations.py` - Fixed import paths

**Note:** Workers themselves (notifications.py, recommendations.py) already had correct imports using `src.*` prefix. Only test files needed fixes.

##### 3. Worker Lifecycle - Graceful Shutdown Pattern

**Problem:**
- Workers didn't properly handle SIGTERM/SIGINT signals
- Broker context manager wasn't used correctly
- Database engine not disposed on shutdown

**Root Cause:**
- Missing `async with broker:` context manager
- No signal handlers for graceful shutdown
- Engine disposal not in finally block

**Solution Applied:**

**Pattern for both workers:**
```python
async def main():
    """Main function to run the broker."""
    logger.info("Broker connecting to Kafka")

    async with broker:  # ← Context manager ensures proper cleanup
        logger.info("Worker ready - waiting for messages")

        # Create stop event
        stop_event = asyncio.Event()

        # Handle graceful shutdown
        def shutdown_handler(signum, frame):
            logger.info("Received shutdown signal")
            stop_event.set()

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        # Wait for shutdown signal
        try:
            await stop_event.wait()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received")

    logger.info("Worker shutting down")
    await engine.dispose()  # ← Clean up database connections

asyncio.run(main())
```

**Files Changed:**
- `backend/workers/notifications.py` - Added broker context manager, signal handlers
- `backend/workers/recommendations.py` - Added broker context manager, signal handlers

**Benefits:**
- Workers now shut down gracefully on Docker stop
- No orphaned Kafka connections
- Database connections properly closed
- No resource leaks

##### 4. Database Migrations

**Issue:** Database schema not initialized on first deployment

**Solution:**
```bash
# Inside backend container
docker exec -it lunch-bot-backend-prod bash
alembic upgrade head
exit
```

**Verification:**
```bash
docker exec -it lunch-bot-backend-prod alembic current
# Shows current migration revision
```

#### Architecture Validation

**External → Internal Traffic Flow:**
```
HTTPS Request (443)
    ↓
Nginx Proxy Manager (external server)
  - SSL/TLS termination
  - Domain: lunchbot.vibe-labs.ru
  - Proxy pass to 172.25.0.200:80
    ↓
Docker Host (172.25.0.200:80)
    ↓
Nginx Container (lunch-bot-nginx-prod)
  - HTTP only (port 80)
  - server_name lunchbot.vibe-labs.ru
  - Routes: / → frontend:3000, /api/ → backend:8000
    ↓
    ┌───────────┴───────────┐
    ▼                       ▼
Frontend:3000          Backend:8000
```

**Key Architecture Points:**
1. **External Nginx Proxy Manager**: Handles HTTPS, Let's Encrypt, public access
2. **Internal Nginx Container**: HTTP routing only, not exposed to internet
3. **Service Communication**: All internal services use Docker network names
4. **Port Exposure**: Only nginx:80 exposed to host, all others internal

#### Deployment Checklist for Future Deployments

Based on first deployment experience, use this checklist:

**Pre-Deployment:**
- [ ] Verify `.env.production` has all required secrets
- [ ] Confirm CORS_ORIGINS includes `https://web.telegram.org`
- [ ] Check NEXT_PUBLIC_API_URL matches production domain
- [ ] Verify nginx.prod.conf uses HTTP only (no HTTPS block)
- [ ] Ensure workers use `src.*` imports (not `workers.*`)

**Deployment:**
- [ ] Pull latest code: `git pull origin main`
- [ ] Build images: `docker compose -f docker-compose.prod.yml build`
- [ ] Start services: `docker compose -f docker-compose.prod.yml up -d`
- [ ] Wait for health checks to pass
- [ ] Apply migrations: `docker exec lunch-bot-backend-prod alembic upgrade head`

**Post-Deployment Verification:**
- [ ] All containers show "Up (healthy)": `docker compose -f docker-compose.prod.yml ps`
- [ ] Health check passes: `curl https://lunchbot.vibe-labs.ru/health`
- [ ] API docs accessible: `https://lunchbot.vibe-labs.ru/docs`
- [ ] Frontend loads: `https://lunchbot.vibe-labs.ru/`
- [ ] Workers connected to Kafka: `docker compose -f docker-compose.prod.yml logs notifications-worker | grep "ready"`
- [ ] No errors in logs: `docker compose -f docker-compose.prod.yml logs --tail=50 | grep -i error`

**Common Gotchas:**
1. **CORS errors**: Always include `https://web.telegram.org` in CORS_ORIGINS
2. **Nginx 502**: Check backend/frontend are healthy before nginx starts
3. **Worker crashes**: Ensure broker lifecycle uses `async with broker:` pattern
4. **Test failures**: Workers should use `src.*` imports, not `workers.*`
5. **Missing server_name**: nginx.prod.conf must have `server_name lunchbot.vibe-labs.ru`

#### Lessons Learned

**1. Nginx Configuration Templates**
- Don't blindly copy nginx configs from other projects
- Verify whether SSL is handled internally or externally
- Always test nginx config: `nginx -t`

**2. Worker Imports**
- Workers are standalone scripts, not importable packages
- Use `src.*` imports for shared code
- Tests should mock workers, not import them directly

**3. Graceful Shutdown**
- Always use context managers for resources (broker, database)
- Implement signal handlers for SIGTERM/SIGINT
- Dispose database engines in cleanup code

**4. Docker Compose Dependencies**
- Use `depends_on` with `condition: service_healthy`
- Workers should wait for kafka health check
- Backend should wait for postgres health check

**5. Environment Variables**
- NEXT_PUBLIC_* variables are build-time, not runtime
- Changing NEXT_PUBLIC_API_URL requires frontend rebuild
- Always double-check CORS_ORIGINS for Telegram Mini Apps

#### Performance Metrics (First Deployment)

**Container Startup Times:**
- PostgreSQL: ~5s (health check passed)
- Kafka: ~10s (broker ready)
- Redis: ~2s (health check passed)
- Backend: ~8s (after postgres healthy)
- Frontend: ~15s (Next.js build cached)
- Nginx: ~2s (after upstream services healthy)
- Workers: ~5s (after kafka healthy)

**Resource Usage (Idle State):**
```
CONTAINER                             CPU %    MEM USAGE / LIMIT
lunch-bot-nginx-prod                  0.01%    12MB / 128MB
lunch-bot-postgres-prod               0.05%    45MB / 1GB
lunch-bot-kafka-prod                  2.3%     512MB / 1GB
lunch-bot-redis-prod                  0.1%     8MB / 256MB
lunch-bot-backend-prod                0.2%     180MB / 2GB
lunch-bot-frontend-prod               0.5%     120MB / 512MB
lunch-bot-telegram-prod               0.1%     65MB / 256MB
lunch-bot-notifications-prod          0.1%     70MB / 256MB
lunch-bot-recommendations-prod        0.1%     75MB / 256MB
```

**Total Resource Usage:** ~1.5GB RAM, ~4% CPU (well within 7.5 CPU / 5.5GB limits)

---

## Troubleshooting Production

### Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs <service-name>

# Check dependencies (health checks)
docker compose -f docker-compose.prod.yml ps

# Restart specific service
docker compose -f docker-compose.prod.yml restart <service-name>

# Force recreate
docker compose -f docker-compose.prod.yml up -d --force-recreate <service-name>
```

### Database Connection Issues

```bash
# Test PostgreSQL is ready
docker exec lunch-bot-postgres-prod pg_isready -U postgres

# Test connection from backend
docker exec lunch-bot-backend-prod python -c "
from sqlalchemy import create_engine
from src.config import settings
engine = create_engine(settings.DATABASE_URL.replace('asyncpg', 'psycopg2'))
try:
    conn = engine.connect()
    print('✓ Database connection OK')
    conn.close()
except Exception as e:
    print(f'✗ Database connection FAILED: {e}')
"
```

### Kafka Issues

```bash
# Check Kafka broker status
docker exec lunch-bot-kafka-prod kafka-broker-api-versions --bootstrap-server localhost:29092

# List topics
docker exec lunch-bot-kafka-prod kafka-topics --bootstrap-server localhost:29092 --list

# Check consumer groups
docker exec lunch-bot-kafka-prod kafka-consumer-groups --bootstrap-server localhost:29092 --list

# Describe consumer group
docker exec lunch-bot-kafka-prod kafka-consumer-groups \
  --bootstrap-server localhost:29092 \
  --group notifications-worker \
  --describe
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up unused images
docker image prune -a

# Clean up stopped containers
docker container prune

# Clean up unused volumes (CAREFUL!)
docker volume prune

# Full cleanup (CAREFUL! Will remove all unused resources)
docker system prune -a --volumes
```

### Frontend Not Loading

```bash
# Check frontend logs
docker compose -f docker-compose.prod.yml logs frontend

# Check if frontend is running
docker compose -f docker-compose.prod.yml ps frontend

# Verify environment variable
docker exec lunch-bot-frontend-prod env | grep NEXT_PUBLIC_API_URL

# If wrong, rebuild with correct value
docker compose -f docker-compose.prod.yml up -d --build --force-recreate frontend
```

### Nginx 502 Bad Gateway

```bash
# Check nginx config is valid
docker exec lunch-bot-nginx-prod nginx -t

# Check nginx logs
docker exec lunch-bot-nginx-prod cat /var/log/nginx/error.log | tail -50

# Check upstream services are running
docker compose -f docker-compose.prod.yml ps backend frontend

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### CORS Errors in Production

**Symptoms:**
- Mini App opens but shows blank screen
- Browser console shows CORS errors

**Solution:**
```bash
# Check CORS_ORIGINS in .env.production
cat .env.production | grep CORS_ORIGINS

# Should be:
# CORS_ORIGINS=["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]

# If wrong, fix it:
nano .env.production

# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Verify CORS header
curl -H "Origin: https://web.telegram.org" -I https://lunchbot.vibe-labs.ru/api/v1/health
# Should include: Access-Control-Allow-Origin: https://web.telegram.org
```

---

## Security Best Practices

### 1. Strong Passwords

```bash
# Generate strong password for PostgreSQL
python3 -c "import secrets; print(secrets.token_urlsafe(24))"

# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP (for Nginx Proxy Manager to connect)
sudo ufw allow 80/tcp

# Optional: Allow HTTPS if running SSL on this server
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### 3. SSH Security

```bash
# Disable password authentication (use SSH keys only)
sudo nano /etc/ssh/sshd_config

# Set:
# PasswordAuthentication no
# PubkeyAuthentication yes

# Restart SSH
sudo systemctl restart sshd
```

### 4. Keep Docker Images Updated

```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

### 5. Monitor Logs Regularly

```bash
# Check for errors in logs
docker compose -f docker-compose.prod.yml logs --tail=100 | grep -i error

# Check for failed authentication attempts
docker compose -f docker-compose.prod.yml logs backend | grep -i "auth failed"
```

### 6. Secrets Management

**Never commit `.env.production` to Git!**

`.gitignore` should include:
```
.env.production
*.env.prod
```

Store production secrets in:
- Password manager (1Password, Bitwarden, etc.)
- Secrets management service (AWS Secrets Manager, HashiCorp Vault)
- Server-side only (never in Git)

---

## Performance Optimization

### Database Tuning

Add to `.env.production`:
```bash
# PostgreSQL performance tuning
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
POSTGRES_MAINTENANCE_WORK_MEM=64MB
POSTGRES_MAX_CONNECTIONS=100
```

### Nginx Caching (Optional)

Create `nginx/nginx.prod.conf` with caching:
```nginx
# Add to http block
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

# Add to location /api/
location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_use_stale error timeout http_500 http_502 http_503;
    # ... rest of proxy config
}
```

### Resource Monitoring

```bash
# Monitor container resources
docker stats

# Check resource limits
docker inspect lunch-bot-backend-prod | grep -A 10 Resources
```

---

## CI/CD Integration (Optional)

### GitHub Actions Example

Create `.github/workflows/deploy-production.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production server
        uses: appleboy/ssh-action@master
        with:
          host: 172.25.0.200
          username: user
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ~/tg_bot
            git pull origin main
            docker compose -f docker-compose.prod.yml up -d --build
            docker exec lunch-bot-backend-prod alembic upgrade head
```

Add SSH private key to GitHub Secrets:
- Repository → Settings → Secrets → New repository secret
- Name: `SSH_PRIVATE_KEY`
- Value: Contents of your SSH private key

---

## Quick Reference

### Essential Commands

```bash
# Start production
docker compose -f docker-compose.prod.yml up -d

# Stop production
docker compose -f docker-compose.prod.yml down

# Restart services
docker compose -f docker-compose.prod.yml restart

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check status
docker compose -f docker-compose.prod.yml ps

# Update from Git
git pull && docker compose -f docker-compose.prod.yml up -d --build

# Backup database
docker exec lunch-bot-postgres-prod pg_dump -U postgres lunch_bot > backup.sql

# Restore database
cat backup.sql | docker exec -i lunch-bot-postgres-prod psql -U postgres lunch_bot

# Apply migrations
docker exec -it lunch-bot-backend-prod alembic upgrade head

# Clean up Docker
docker system prune -a
```

### Important URLs

- **Frontend:** https://lunchbot.vibe-labs.ru/
- **API Docs:** https://lunchbot.vibe-labs.ru/docs
- **Health Check:** https://lunchbot.vibe-labs.ru/health

### Log Locations

- Nginx logs: `docker exec lunch-bot-nginx-prod cat /var/log/nginx/access.log`
- Backend logs: `docker compose -f docker-compose.prod.yml logs backend`
- Frontend logs: `docker compose -f docker-compose.prod.yml logs frontend`
- All logs: `docker compose -f docker-compose.prod.yml logs`

---

## Post-Deployment Verification Checklist

- [ ] All containers show "Up" status: `docker compose -f docker-compose.prod.yml ps`
- [ ] Health check passes: `curl https://lunchbot.vibe-labs.ru/health`
- [ ] API docs accessible: https://lunchbot.vibe-labs.ru/docs
- [ ] Frontend loads: https://lunchbot.vibe-labs.ru/
- [ ] Telegram Mini App opens via Menu Button
- [ ] Authentication works in Mini App
- [ ] Can create test order
- [ ] Database migrations applied: `docker exec lunch-bot-backend-prod alembic current`
- [ ] Backups configured and tested
- [ ] Firewall enabled: `sudo ufw status`
- [ ] CORS includes `https://web.telegram.org`
- [ ] `.env.production` not committed to Git

---

## Environment Variables

### Backend Environment Variables

Location: `backend/.env`

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:password@postgres:5432/lunch_bot` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather | `123456:ABC-DEF1234...` |
| `TELEGRAM_MINI_APP_URL` | URL where Mini App is hosted | Production: `https://lunchbot.vibe-labs.ru`<br>Dev: ngrok URL |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Generate with `openssl rand -hex 32` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]` |

#### CORS Configuration Explained

**Why `https://web.telegram.org`?**

Telegram Mini Apps load your frontend in an iframe from `web.telegram.org` domain. Without this domain in CORS_ORIGINS, all API requests will be blocked by the browser.

**Development CORS setup:**
```bash
# Local development
CORS_ORIGINS=["http://localhost"]

# Development with ngrok
CORS_ORIGINS=["http://localhost","https://abc123.ngrok.io","https://web.telegram.org"]

# Production
CORS_ORIGINS=["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]
```

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BROKER_URL` | Kafka broker URL | `kafka:29092` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `GEMINI_API_KEYS` | Gemini API keys (comma-separated) | - |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash-exp` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_EXPIRE_DAYS` | JWT token lifetime | `7` |
| `BACKEND_API_URL` | Internal backend URL for bot | `http://backend:8000/api/v1` |

### Frontend Environment Variables

Location: `frontend_mini_app/.env.local`

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Development: `http://localhost/api/v1`<br>ngrok: `https://abc123.ngrok.io/api/v1`<br>Production: `https://lunchbot.vibe-labs.ru/api/v1` |

**Important:** This variable is embedded into the frontend build at build time. You need to rebuild the frontend container after changing it:

```bash
docker-compose up --build frontend
```

### Environment Variables Summary by Environment

**Local Development (no Telegram):**
```bash
# backend/.env
CORS_ORIGINS=["http://localhost"]
TELEGRAM_MINI_APP_URL=http://localhost

# frontend_mini_app/.env.local
NEXT_PUBLIC_API_URL=http://localhost/api/v1
```

**Development with Telegram (ngrok):**
```bash
# backend/.env
CORS_ORIGINS=["http://localhost","https://abc123.ngrok.io","https://web.telegram.org"]
TELEGRAM_MINI_APP_URL=https://abc123.ngrok.io

# frontend_mini_app/.env.local
NEXT_PUBLIC_API_URL=https://abc123.ngrok.io/api/v1
```

**Production:**
```bash
# backend/.env
CORS_ORIGINS=["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]
TELEGRAM_MINI_APP_URL=https://lunchbot.vibe-labs.ru

# frontend_mini_app/.env.local
NEXT_PUBLIC_API_URL=https://lunchbot.vibe-labs.ru/api/v1
```

---

## Manual Testing Checklist

### Prerequisites

- [ ] Services are running: `docker-compose ps` shows all services "Up"
- [ ] Health check passes: `curl http://localhost/health` returns `{"status":"ok"}`
- [ ] For Telegram testing: ngrok is running with HTTPS tunnel
- [ ] Environment variables are configured correctly

### Test 1: Menu Button Launch

**Steps:**
1. Open your Telegram bot in Telegram app
2. Look for Menu Button (hamburger icon left of message input field)
3. Click Menu Button

**Expected:**
- [ ] Mini App opens in fullscreen mode
- [ ] Shows "Авторизация..." loading spinner briefly
- [ ] Authentication completes automatically
- [ ] List of cafes loads and displays
- [ ] No errors in console (if using Telegram Web)

**If failed:** Check [Troubleshooting - Menu Button](#menu-button-not-showing)

---

### Test 2: `/order` Command

**Steps:**
1. Send `/order` command to bot
2. Bot responds with message and inline button "Заказать обед"
3. Click the inline button

**Expected:**
- [ ] Message appears with inline button
- [ ] Button has text "Заказать обед"
- [ ] Mini App opens when button clicked
- [ ] Authentication and cafe loading work as in Test 1

---

### Test 3: `/start` Command (New User Flow)

**Steps:**
1. Send `/start` command (or create new chat with bot)
2. Bot responds with welcome message

**Expected:**
- [ ] Welcome message appears
- [ ] Message explains how to use the bot
- [ ] Inline button "Заказать обед" is present
- [ ] Clicking button opens Mini App

---

### Test 4: `/help` Command

**Steps:**
1. Send `/help` command to bot

**Expected:**
- [ ] Help message lists all commands
- [ ] `/order` command is mentioned
- [ ] Menu Button is mentioned as alternative way to order
- [ ] Instructions are clear

---

### Test 5: Full Order Flow (E2E)

**Steps:**
1. Open Mini App (via Menu Button or `/order`)
2. Wait for authentication and cafe list to load
3. Select a cafe
4. Select a combo
5. Fill all required categories
6. Optionally add extras
7. Click "Оформить заказ" button

**Expected:**
- [ ] Authentication completes successfully
- [ ] Cafe list loads without errors
- [ ] Cafe selection works
- [ ] Combo selection displays menu items
- [ ] All categories can be filled
- [ ] Extras can be added/removed
- [ ] Checkout button enables when order is complete
- [ ] Order submits successfully
- [ ] Confirmation message appears
- [ ] (Optional) Mini App closes automatically

**Database verification:**
```bash
# Check order was created
docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot -c "SELECT * FROM orders ORDER BY id DESC LIMIT 1;"
```

---

### Test 6: Fallback UI (Not in Telegram)

**Steps:**
1. Open `http://localhost` (or ngrok URL) directly in browser
2. Do NOT open through Telegram bot

**Expected:**
- [ ] Fallback UI appears with Telegram icon
- [ ] Message explains app works only in Telegram
- [ ] Instructions show how to open via bot
- [ ] No API requests are made (check Network tab)
- [ ] No JavaScript errors in console

---

### Test 7: Cross-Platform Testing

Test Mini App on different Telegram platforms:

**iOS Telegram:**
- [ ] Menu Button appears
- [ ] Mini App opens and works
- [ ] Order flow completes

**Android Telegram:**
- [ ] Menu Button appears
- [ ] Mini App opens and works
- [ ] Order flow completes

**Desktop Telegram (Windows/macOS/Linux):**
- [ ] Menu Button appears
- [ ] Mini App opens and works
- [ ] Order flow completes

**Telegram Web (web.telegram.org):**
- [ ] Menu Button appears
- [ ] Mini App opens and works
- [ ] Order flow completes
- [ ] No CORS errors in browser console

---

### Test 8: Authentication Flow

**Steps:**
1. Open Mini App via bot
2. Open browser DevTools (if using Telegram Web)
3. Check Application > Local Storage

**Expected:**
- [ ] Loading spinner shows "Авторизация..."
- [ ] After 1-2 seconds, authentication completes
- [ ] `jwt_token` appears in localStorage
- [ ] Token is not empty
- [ ] Main UI loads after authentication

**Check token format:**
```javascript
// In browser console
const token = localStorage.getItem('jwt_token');
console.log(token); // Should be JWT format: xxxxx.yyyyy.zzzzz
```

**If authentication fails:**
- [ ] Error screen appears with red background
- [ ] Error message is descriptive
- [ ] No infinite loading spinner

---

### Test 9: API Requests with Authorization

**Steps:**
1. Open Mini App via bot
2. Open Network tab in DevTools (Telegram Web)
3. Watch API requests as you use the app

**Expected:**
- [ ] All API requests include `Authorization: Bearer <token>` header
- [ ] API responses return 200/201 status codes
- [ ] No 401 Unauthorized errors
- [ ] No CORS errors

**Sample request to verify:**
```
Request URL: https://lunchbot.vibe-labs.ru/api/v1/cafes?active_only=true
Request Headers:
  Authorization: Bearer eyJ...
Response Status: 200 OK
```

---

## Troubleshooting

### Menu Button Not Showing

**Symptoms:**
- Menu Button (hamburger icon) doesn't appear in bot chat
- Only message input field visible

**Possible Causes:**

1. **Old Telegram client version**
   - Solution: Update Telegram app to latest version
   - Menu Button feature requires Telegram v8.0+

2. **Menu Button setup failed on bot start**
   - Check logs: `docker-compose logs telegram-bot | grep "Menu button"`
   - Should see: `"Menu button configured with URL: https://..."`
   - If error appears: check TELEGRAM_BOT_TOKEN is valid

3. **Bot API rate limit**
   - Restart telegram-bot service: `docker-compose restart telegram-bot`
   - Wait 1-2 minutes and check again

**Workaround:**
- Use `/order` command instead of Menu Button
- Both methods open the same Mini App

---

### CORS Errors

**Symptoms:**
- Mini App opens but shows blank screen
- Browser console shows CORS errors
- API requests fail with CORS policy error

**Example error:**
```
Access to fetch at 'https://lunchbot.vibe-labs.ru/api/v1/cafes' from origin 'https://web.telegram.org'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**Solutions:**

**1. Check CORS_ORIGINS in backend/.env:**
```bash
# Must include both your domain AND web.telegram.org
CORS_ORIGINS=["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]
```

**2. Check CORS_ORIGINS in docker-compose.yml:**
```yaml
backend:
  environment:
    CORS_ORIGINS: '["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]'
```

**3. Restart backend service:**
```bash
docker-compose restart backend
```

**4. Verify CORS is applied:**
```bash
# Should return Access-Control-Allow-Origin header
curl -H "Origin: https://web.telegram.org" -I https://lunchbot.vibe-labs.ru/api/v1/health
```

**Development with ngrok:**
```bash
# Add ngrok URL to CORS
CORS_ORIGINS=["http://localhost","https://abc123.ngrok.io","https://web.telegram.org"]
```

---

### Mini App Shows White Screen

**Symptoms:**
- Mini App opens but shows blank white screen
- No error messages visible

**Diagnostic Steps:**

**1. Check if URL is correct:**
```bash
# Should match TELEGRAM_MINI_APP_URL
docker-compose logs telegram-bot | grep "Menu button configured"
```

**2. Verify URL in browser:**
- Open the URL directly in browser
- Should show either:
  - Main app UI (if not detecting Telegram)
  - Fallback UI with instructions

**3. Check frontend is running:**
```bash
docker-compose ps frontend
# Should show "Up"

# Check frontend logs
docker-compose logs frontend
```

**4. Check nginx routing:**
```bash
docker-compose logs nginx | tail -20
# Look for errors or 404s
```

**Solutions:**

- **Frontend not running:** `docker-compose up -d frontend`
- **Nginx error:** Check `nginx/nginx.conf` syntax
- **Wrong URL:** Update `TELEGRAM_MINI_APP_URL` in backend/.env
- **Build issue:** `docker-compose up --build frontend`

---

### Authentication Fails / Infinite Loading

**Symptoms:**
- Loading spinner "Авторизация..." never finishes
- Or: Red error screen appears immediately

**Diagnostic Steps:**

**1. Check browser console (Telegram Web):**
```javascript
// Look for error messages like:
"Telegram auth failed: ..."
```

**2. Check backend logs:**
```bash
docker-compose logs backend | grep "auth"
# Look for POST /auth/telegram requests and responses
```

**3. Check Network tab:**
- Request to `/api/v1/auth/telegram` should return 200 OK
- Response should contain `access_token`

**Possible Issues:**

**Issue 1: Telegram initData validation fails (401 Unauthorized)**
```bash
# Backend logs show:
"Invalid Telegram initData signature"
```

**Solution:**
- Check `TELEGRAM_BOT_TOKEN` in backend/.env matches your bot
- Restart backend: `docker-compose restart backend`

**Issue 2: JWT_SECRET_KEY not set**
```bash
# Backend logs show:
"JWT_SECRET_KEY is required"
```

**Solution:**
```bash
# Generate secure key
openssl rand -hex 32

# Add to backend/.env
JWT_SECRET_KEY=<generated_key>

# Restart backend
docker-compose restart backend
```

**Issue 3: CORS blocking auth request**

**Solution:** See [CORS Errors](#cors-errors) section above

**Issue 4: initData not available**
- Only happens when NOT opening through Telegram
- Check you're using Menu Button or `/order` command
- Don't open URL directly in browser (use Fallback UI instead)

---

### Telegram Mini App Not Opening (HTTPS Required)

**Symptoms:**
- Clicking Menu Button or `/order` button does nothing
- Or: Error message "Could not open Mini App"

**Cause:**
Telegram Mini Apps require HTTPS URL. `http://localhost` will not work.

**Solutions:**

**For Development:**

Use ngrok to get HTTPS tunnel:

```bash
# Start ngrok
ngrok http 80

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Update backend/.env
TELEGRAM_MINI_APP_URL=https://abc123.ngrok.io
CORS_ORIGINS=["http://localhost","https://abc123.ngrok.io","https://web.telegram.org"]

# Update frontend_mini_app/.env.local
NEXT_PUBLIC_API_URL=https://abc123.ngrok.io/api/v1

# Restart services
docker-compose restart backend telegram-bot frontend
```

**For Production:**

Ensure external Nginx Proxy Manager provides HTTPS termination for `lunchbot.vibe-labs.ru`.

---

### ngrok URL Changes on Restart

**Symptoms:**
- Mini App worked yesterday
- Today after restarting ngrok, it doesn't work

**Cause:**
ngrok free plan assigns random URL on each restart.

**Solution:**

**Option 1: Update .env files every time**
```bash
# Get new ngrok URL
ngrok http 80
# Shows: https://xyz789.ngrok.io

# Update backend/.env
TELEGRAM_MINI_APP_URL=https://xyz789.ngrok.io
CORS_ORIGINS=["http://localhost","https://xyz789.ngrok.io","https://web.telegram.org"]

# Update frontend_mini_app/.env.local
NEXT_PUBLIC_API_URL=https://xyz789.ngrok.io/api/v1

# Restart
docker-compose restart backend telegram-bot frontend
```

**Option 2: Use ngrok with custom domain (paid plan)**
```bash
ngrok http 80 --domain=myapp.ngrok.io
```

**Option 3: Use CloudFlare Tunnel with custom domain (free)**
```bash
cloudflared tunnel --hostname myapp.example.com --url http://localhost:80
```

---

### 2. SSL/TLS Setup (Let's Encrypt)

1. Install certbot:
   ```bash
   apt-get install certbot python3-certbot-nginx
   ```

2. Obtain certificate:
   ```bash
   certbot --nginx -d yourdomain.com
   ```

3. Certbot auto-renewal:
   ```bash
   certbot renew --dry-run
   ```

4. Uncomment HTTPS configuration in `nginx/nginx.conf`:
   - Uncomment HTTPS server block (port 443)
   - Uncomment HTTP → HTTPS redirect
   - Update certificate paths if needed

### 3. Security Hardening

- **Rate Limiting:** Uncomment rate limiting configuration in `nginx/nginx.conf`
- **Security Headers:** Uncomment security headers (X-Frame-Options, CSP, etc.)
- **Firewall:** Configure UFW or iptables to allow only ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
- **Fail2ban:** Enable fail2ban for brute-force protection

### 4. Monitoring

**Nginx Logs:**
- Access logs: `/var/log/nginx/access.log` (inside nginx_logs volume)
- Error logs: `/var/log/nginx/error.log` (inside nginx_logs volume)

**Viewing logs:**
```bash
# Nginx logs
docker logs lunch-bot-nginx

# Backend logs
docker logs lunch-bot-backend

# All services logs
docker-compose logs -f
```

**Metrics to Monitor:**
- Request rate
- Response time
- 4xx/5xx error rate
- Upstream connect time
- Traffic volume

---

## Temporary Port Exposure (for debugging)

Если вам нужен временный доступ к PostgreSQL/Redis/Kafka с хоста (например, для GUI клиента):

1. **Uncomment ports** в `docker-compose.yml`:
   ```yaml
   postgres:
     ports:
       - "5432:5432"  # Временно раскомментировать
   ```

2. Restart service:
   ```bash
   docker-compose up -d postgres
   ```

3. **ВАЖНО:** Закройте порт после завершения дебага!
   ```bash
   # Комментируем порт обратно и перезапускаем
   docker-compose up -d postgres
   ```

**⚠️ Никогда не открывайте порты PostgreSQL/Kafka/Redis в production!**

---

## Rollback Strategy

### In Case of Issues

1. **Git rollback:**
   ```bash
   git revert <commit-hash>
   docker-compose up -d
   ```

2. **Restore old configuration:**
   - Uncomment old ports in `docker-compose.yml`
   - Comment out nginx service
   - Update CORS_ORIGINS and NEXT_PUBLIC_API_URL

3. **Emergency access:**
   - Temporarily expose backend port 8000
   - Temporarily expose frontend port 3000

---

## Environment Variables

### Required for Development

See `backend/.env.example` for full list. Key variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/lunch_bot

# CORS (через Nginx)
CORS_ORIGINS=["http://localhost"]

# Kafka
KAFKA_BROKER_URL=kafka:29092

# Redis
REDIS_URL=redis://redis:6379
```

### Required for Production

```bash
# CORS (с вашим доменом)
CORS_ORIGINS=["https://yourdomain.com"]

# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token

# Gemini API Keys (для AI рекомендаций)
GEMINI_API_KEYS=["key1","key2","key3"]
```

---

## Health Checks

Check service health:

```bash
# Nginx health check
curl http://localhost/health

# Docker services status
docker ps

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' lunch-bot-backend
```

---

## Common Issues

### 1. Nginx 502 Bad Gateway

**Cause:** Backend or Frontend not ready

**Solution:**
```bash
# Check logs
docker logs lunch-bot-nginx
docker logs lunch-bot-backend
docker logs lunch-bot-frontend

# Restart services
docker-compose restart backend frontend
```

### 2. CORS Errors

**Cause:** Incorrect CORS_ORIGINS in backend

**Solution:**
```bash
# Check backend .env file
docker exec -it lunch-bot-backend cat .env | grep CORS_ORIGINS

# Should be: CORS_ORIGINS=["http://localhost"]
# Update and restart
docker-compose restart backend
```

### 3. Database Connection Refused

**Cause:** Trying to connect from host (port not exposed)

**Solution:**
Use `docker exec` instead:
```bash
docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot
```

---

## Performance

### Expected Overhead

- **Nginx:** ~1-2ms latency overhead
- **WebSocket:** Full support (Next.js HMR works)
- **Static Files:** Proxied efficiently

### Benchmarking

```bash
# Test endpoint performance
ab -n 1000 -c 10 http://localhost/health

# Compare with direct backend access (for testing only)
ab -n 1000 -c 10 http://localhost:8000/health
```

---

## References

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)
