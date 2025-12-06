---
id: TSK-008
title: Production Deployment via SSH
pipeline: hotfix
status: pending
created_at: 2025-12-06T13:22:10Z
related_files:
  - docker-compose.prod.yml
  - .env.production.example
  - nginx/nginx.prod.conf
  - backend/Dockerfile
  - frontend_mini_app/Dockerfile
  - .memory-base/tech-docs/deployment.md
impact:
  api: true
  db: true
  frontend: true
  services: true
  docs: false
---

## Описание

Задеплоить проект Telegram-бота заказа обедов на production сервер через SSH.

**Production сервер:**
- IP: 172.25.0.200
- SSH: user@172.25.0.200:22
- Домен: lunchbot.vibe-labs.ru
- Внешний Nginx Proxy Manager (отдельный сервер) — HTTPS termination с Let's Encrypt

**Архитектура production:**
```
Internet (HTTPS)
    ↓
Nginx Proxy Manager (external server)
  - SSL/TLS termination (Let's Encrypt)
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
(Next.js production build)   (FastAPI + uvicorn)
    │                             │
    └──────────────┬──────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    PostgreSQL             Kafka & Redis
```

**Docker сервисы (9 сервисов):**
1. nginx — reverse proxy (port 80)
2. postgres — PostgreSQL 17
3. kafka — Confluent Kafka
4. redis — Redis 7 (AOF)
5. backend — FastAPI app
6. frontend — Next.js app (production build)
7. telegram-bot — Telegram bot (aiogram)
8. notifications-worker — Kafka consumer
9. recommendations-worker — Kafka consumer

## Acceptance Criteria

- [ ] SSH доступ к серверу проверен
- [ ] Docker и Docker Compose установлены на сервере
- [ ] Git репозиторий склонирован на сервер
- [ ] Создан `.env.production` с production секретами
- [ ] Nginx Proxy Manager настроен для домена lunchbot.vibe-labs.ru
- [ ] Все 9 Docker контейнеров запущены и healthy
- [ ] Применены database migrations
- [ ] Health check проходит: curl https://lunchbot.vibe-labs.ru/health
- [ ] API documentation доступна: https://lunchbot.vibe-labs.ru/docs
- [ ] Frontend загружается: https://lunchbot.vibe-labs.ru/
- [ ] Telegram Mini App открывается через Menu Button
- [ ] Создан первый manager user через psql
- [ ] Настроены автоматические backups PostgreSQL
- [ ] Firewall настроен (UFW)
- [ ] `.env.production` НЕ коммитится в git

## Контекст

### Найденные файлы

**Docker Compose:**
- `docker-compose.prod.yml` — production конфигурация с resource limits

**Environment variables:**
- `.env.production.example` — template для production env vars
- Требует обязательные секреты:
  - POSTGRES_PASSWORD (strong random password)
  - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
  - TELEGRAM_BOT_TOKEN (from @BotFather)
  - GEMINI_API_KEYS (comma-separated)
  - CORS_ORIGINS (must include https://web.telegram.org)
  - NEXT_PUBLIC_API_URL (https://lunchbot.vibe-labs.ru/api/v1)

**Nginx:**
- `nginx/nginx.prod.conf` — production nginx config
- HTTP → HTTPS redirect
- HTTPS server block (port 443) для lunchbot.vibe-labs.ru
- Rate limiting configured
- Security headers configured

**Dockerfiles:**
- `backend/Dockerfile` — FastAPI production image
- `frontend_mini_app/Dockerfile` — Next.js production build

**Документация:**
- `.memory-base/tech-docs/deployment.md` — полная инструкция по deployment
  - Prerequisites (Docker, Git)
  - Step-by-step deployment guide
  - Environment variables setup
  - Nginx Proxy Manager configuration
  - Database migrations
  - Health checks
  - Backup strategy
  - Troubleshooting

### Стек технологий

**Backend:**
- Python 3.13
- FastAPI, uvicorn
- PostgreSQL 17 (asyncpg)
- Kafka (faststream)
- Redis
- Alembic migrations
- Telegram bot (aiogram)
- Gemini AI (google-genai)

**Frontend:**
- Next.js 16.0.7
- React 19.2.0
- Tailwind CSS 4
- TypeScript 5

**Infrastructure:**
- Nginx 1.27-alpine
- Docker Compose
- Docker volumes для persistent data

### Resource Limits (Production)

| Service | CPU | Memory |
|---------|-----|--------|
| nginx | 0.5 | 128M |
| postgres | 1 | 1G |
| kafka | 1 | 1G |
| redis | 0.5 | 256M |
| backend | 2 | 2G |
| frontend | 1 | 512M |
| telegram-bot | 0.5 | 256M |
| notifications-worker | 0.5 | 256M |
| recommendations-worker | 0.5 | 256M |

**Total:** ~7.5 CPU, ~5.5GB RAM

### Volumes (Persistent Data)

- postgres_data — PostgreSQL database
- redis_data — Redis AOF
- kafka_data — Kafka logs
- nginx_logs — Nginx access/error logs

### Health Checks

Все критичные сервисы имеют health checks:
- postgres: pg_isready
- redis: redis-cli ping
- kafka: kafka-broker-api-versions
- backend: curl http://localhost:8000/health
- frontend: curl http://localhost:3000
- nginx: nginx -t

### CORS Configuration (CRITICAL!)

`CORS_ORIGINS` MUST include:
1. Production domain: https://lunchbot.vibe-labs.ru
2. Telegram Web App: https://web.telegram.org

Example:
```
CORS_ORIGINS=["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]
```

Without `https://web.telegram.org`, Telegram Mini App will fail with CORS errors.

### Deployment Steps (from deployment.md)

1. SSH to server: `ssh user@172.25.0.200`
2. Install Docker & Docker Compose (if not installed)
3. Clone repository: `git clone <repo-url> tg_bot && cd tg_bot`
4. Create `.env.production` from `.env.production.example`
5. Generate secrets (POSTGRES_PASSWORD, JWT_SECRET_KEY)
6. Configure Nginx Proxy Manager for lunchbot.vibe-labs.ru
7. Launch stack: `docker compose -f docker-compose.prod.yml up -d --build`
8. Check services: `docker compose -f docker-compose.prod.yml ps`
9. Apply migrations: `docker exec -it lunch-bot-backend-prod alembic upgrade head`
10. Verify health: `curl https://lunchbot.vibe-labs.ru/health`
11. Create first manager user via psql
12. Test Telegram integration

### Security Checklist

- [ ] Strong POSTGRES_PASSWORD generated
- [ ] JWT_SECRET_KEY generated with openssl
- [ ] `.env.production` in .gitignore
- [ ] Firewall enabled (UFW)
- [ ] Only ports 22 (SSH), 80 (HTTP) exposed
- [ ] Internal services (postgres, kafka, redis) NOT exposed
- [ ] HTTPS enforced via Nginx Proxy Manager
- [ ] Security headers configured in nginx

### Monitoring

**View logs:**
```bash
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f telegram-bot
```

**Check status:**
```bash
docker compose -f docker-compose.prod.yml ps
docker stats
```

**Nginx logs:**
```bash
docker exec lunch-bot-nginx-prod cat /var/log/nginx/access.log
docker exec lunch-bot-nginx-prod cat /var/log/nginx/error.log
```

### Backup Strategy

**PostgreSQL backup:**
```bash
docker exec lunch-bot-postgres-prod pg_dump -U postgres -Fc lunch_bot > backup_$(date +%Y%m%d).dump
```

**Automated daily backups:**
- Create backup script: `/home/user/backup_db.sh`
- Add to crontab: `0 2 * * * /home/user/backup_db.sh`
- Retention: 7 days

### Re-deployment (Updates)

**Standard update (with downtime ~2-5 min):**
```bash
cd ~/tg_bot
git pull origin main
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
docker exec -it lunch-bot-backend-prod alembic upgrade head
```

**Zero-downtime update (rolling):**
```bash
cd ~/tg_bot
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate backend
docker compose -f docker-compose.prod.yml up -d --build --no-deps --force-recreate frontend
# ... (see deployment.md for full sequence)
```

### Troubleshooting

See `.memory-base/tech-docs/deployment.md` section "Troubleshooting Production":
- Container won't start
- Database connection issues
- Kafka issues
- Out of disk space
- Frontend not loading
- Nginx 502 Bad Gateway
- CORS errors in production

### Post-Deployment Verification Checklist

- [ ] All containers show "Up": `docker compose -f docker-compose.prod.yml ps`
- [ ] Health check passes: `curl https://lunchbot.vibe-labs.ru/health`
- [ ] API docs accessible: https://lunchbot.vibe-labs.ru/docs
- [ ] Frontend loads: https://lunchbot.vibe-labs.ru/
- [ ] Telegram Mini App opens via Menu Button
- [ ] Authentication works in Mini App
- [ ] Can create test order
- [ ] Database migrations applied: `docker exec lunch-bot-backend-prod alembic current`
- [ ] Backups configured and tested
- [ ] Firewall enabled: `sudo ufw status`
- [ ] CORS includes https://web.telegram.org
- [ ] `.env.production` not committed to Git

## Notes

- Это первый production deployment (initial deployment)
- Документация deployment.md содержит детальные инструкции
- Используется внешний Nginx Proxy Manager для SSL/TLS
- Внутренний nginx контейнер работает на HTTP (port 80)
- Все internal services (postgres, kafka, redis) доступны только внутри Docker network
- Frontend использует build argument NEXT_PUBLIC_API_URL
- Production builds БЕЗ volume mounts (no live reload)
- Resource limits настроены для всех сервисов
