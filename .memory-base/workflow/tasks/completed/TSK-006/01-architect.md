---
agent: architect
task_id: TSK-006
status: completed
next: coder
created_at: 2025-12-06T14:05:00
files_changed:
  - path: nginx/nginx.conf
    action: created
  - path: docker-compose.yml
    action: modified
  - path: backend/.env.example
    action: modified
---

# TSK-006: Nginx Reverse Proxy - Architectural Design

## Executive Summary

Спроектирована архитектура reverse proxy на базе Nginx для объединения всех публичных HTTP-сервисов под единым портом 80. Решение улучшает безопасность (закрывает прямой доступ к БД и Kafka), упрощает деплой (один DNS-запись, один публичный порт) и готовит инфраструктуру к production (готовность к SSL/TLS).

## Current State Analysis

### Текущие проблемы

1. **Безопасность:**
   - PostgreSQL:5432 открыт наружу — угроза SQL-инъекций, brute-force атак
   - Kafka:9092 открыт наружу — возможность перехвата сообщений, DDoS
   - Redis:6379 открыт наружу — риск утечки кэшированных данных

2. **Инфраструктура:**
   - 5 публичных портов (3000, 8000, 5432, 9092, 6379)
   - Сложная настройка DNS (нужны отдельные записи для каждого порта)
   - Невозможность централизованного логирования и мониторинга

3. **HTTPS/SSL:**
   - Для каждого порта нужен отдельный SSL-сертификат
   - Telegram Mini Apps требуют HTTPS в production

### Текущая маршрутизация

```
Internet → localhost:3000 (Frontend)
Internet → localhost:8000 (Backend API)
Internet → localhost:5432 (PostgreSQL) ❌
Internet → localhost:9092 (Kafka) ❌
Internet → localhost:6379 (Redis) ❌
```

### API Endpoints (из src/main.py)

Backend использует FastAPI с префиксом `/api/v1`:

- `/health` — health check (БЕЗ префикса!)
- `/api/v1/auth/*` — аутентификация
- `/api/v1/users/*` — пользователи
- `/api/v1/cafes/*` — кафе
- `/api/v1/cafe-links/*` — ссылки на кафе
- `/api/v1/menu/*` — меню
- `/api/v1/deadlines/*` — дедлайны
- `/api/v1/orders/*` — заказы
- `/api/v1/summaries/*` — сводки
- `/api/v1/recommendations/*` — рекомендации (Gemini AI)
- `/docs` — Swagger UI (БЕЗ префикса!)
- `/openapi.json` — OpenAPI schema (БЕЗ префикса!)

**ВАЖНО:** `/health`, `/docs`, `/openapi.json` НЕ имеют префикса `/api/v1`!

---

## Proposed Architecture

### Target State

```
Internet → nginx:80
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

### URL Routing Scheme

| Request | Nginx Routing | Target Service | Notes |
|---------|---------------|----------------|-------|
| `http://localhost/` | → `http://frontend:3000/` | Frontend (Next.js) | Root & все пути кроме `/api`, `/docs`, `/health` |
| `http://localhost/api/v1/*` | → `http://backend:8000/api/v1/*` | Backend API | Все API endpoints |
| `http://localhost/health` | → `http://backend:8000/health` | Backend health check | Monitoring |
| `http://localhost/docs` | → `http://backend:8000/docs` | Swagger UI | API documentation |
| `http://localhost/openapi.json` | → `http://backend:8000/openapi.json` | OpenAPI schema | API schema |
| `http://localhost/_next/*` | → `http://frontend:3000/_next/*` | Next.js static files | Build artifacts |

### Security Model

**Public Access (через nginx):**
- nginx:80 — единственный публичный порт

**Internal Access (только внутри Docker network `lunch-bot-network`):**
- frontend:3000 — доступен только через nginx
- backend:8000 — доступен только через nginx
- postgres:5432 — доступен только для backend, telegram-bot, workers
- kafka:29092 — доступен только для backend, workers
- redis:6379 — доступен только для backend, telegram-bot, workers

**Access Matrix:**

| Service | nginx | frontend | backend | telegram-bot | workers | Internet |
|---------|-------|----------|---------|--------------|---------|----------|
| nginx | - | ✓ | ✓ | ✗ | ✗ | ✓ |
| frontend | ✗ | - | ✓ | ✗ | ✗ | ✗ |
| backend | ✗ | ✗ | - | ✗ | ✗ | ✗ |
| postgres | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ |
| kafka | ✗ | ✗ | ✓ | ✗ | ✓ | ✗ |
| redis | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ |

---

## Technical Design

### 1. Nginx Configuration

**File:** `nginx/nginx.conf`

**Key Features:**

1. **Upstream Definitions:**
   ```nginx
   upstream frontend {
       server frontend:3000;
   }

   upstream backend {
       server backend:8000;
   }
   ```

2. **Location Priority (order matters!):**
   - `/health` — backend health check (exact match)
   - `/docs` — Swagger UI (exact match)
   - `/openapi.json` — OpenAPI schema (exact match)
   - `/api/` — backend API (prefix match)
   - `/_next/` — Next.js static files (prefix match)
   - `/` — frontend SPA (catch-all)

3. **Proxy Headers:**
   - `X-Real-IP` — original client IP
   - `X-Forwarded-For` — proxy chain
   - `X-Forwarded-Proto` — original protocol (http/https)
   - `Host` — original host header

4. **WebSocket Support:**
   - `Upgrade` и `Connection` headers для Next.js hot-reload
   - Nginx 1.3+ поддерживает WebSocket out-of-the-box

5. **File Upload:**
   - `client_max_body_size 10M` — max request body (для будущих загрузок)

6. **Logging:**
   - `access.log` — все входящие запросы
   - `error.log` — ошибки proxy

7. **HTTPS Preparation:**
   - Комментарии с примером SSL-конфигурации
   - Готовность к Let's Encrypt (комментарии для `certbot`)

**Critical Configuration Notes:**

- **Trailing slashes:** `/api/` vs `/api`
  - `location /api/` + `proxy_pass http://backend/api/` → rewrite работает
  - `location /api` + `proxy_pass http://backend/api` → НЕ работает для `/api/v1/*`

- **Location Order:**
  1. Exact matches (`= /health`)
  2. Prefix matches (`^~ /api/`)
  3. Regex matches (`~ \.jpg$`)
  4. Catch-all (`/`)

### 2. Docker Compose Changes

**Changes Required:**

#### A. Add Nginx Service

```yaml
nginx:
  image: nginx:1.27-alpine  # LTS version
  container_name: lunch-bot-nginx
  ports:
    - "80:80"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - nginx_logs:/var/log/nginx
  depends_on:
    - frontend
    - backend
  networks:
    - lunch-bot-network
  healthcheck:
    test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
    interval: 10s
    timeout: 5s
    retries: 3
  restart: unless-stopped
```

**Why `nginx:1.27-alpine`?**
- Alpine — минимальный образ (~10MB vs ~140MB для Debian)
- 1.27 — latest stable LTS (long-term support)
- Меньше attack surface, быстрый старт

#### B. Remove Public Ports

**Services to modify:**

1. **postgres:**
   ```yaml
   # REMOVE:
   ports:
     - "5432:5432"

   # KEEP:
   networks:
     - lunch-bot-network
   ```

2. **kafka:**
   ```yaml
   # REMOVE:
   ports:
     - "9092:9092"

   # UPDATE environment:
   KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092
   # (убрать PLAINTEXT_HOST://localhost:9092)
   ```

3. **redis:**
   ```yaml
   # REMOVE:
   ports:
     - "6379:6379"
   ```

4. **backend:**
   ```yaml
   # REMOVE:
   ports:
     - "8000:8000"

   # UPDATE environment:
   CORS_ORIGINS: '["http://localhost"]'
   # (вместо http://localhost:3000)
   ```

5. **frontend:**
   ```yaml
   # REMOVE:
   ports:
     - "3000:3000"

   # UPDATE environment:
   NEXT_PUBLIC_API_URL: http://localhost/api/v1
   # (вместо http://localhost:8000/api/v1)

   # UPDATE build args:
   build:
     args:
       NEXT_PUBLIC_API_URL: http://localhost/api/v1
   ```

#### C. Add Nginx Logs Volume

```yaml
volumes:
  postgres_data:
  redis_data:
  nginx_logs:  # NEW
```

### 3. Environment Variables Updates

**File:** `backend/.env.example`

**Changes:**

```bash
# CORS — UPDATE
# Old: CORS_ORIGINS=["http://localhost:3000","http://frontend:3000"]
# New: Только nginx URL
CORS_ORIGINS=["http://localhost"]

# Production example with HTTPS:
# CORS_ORIGINS=["https://yourdomain.com"]
```

**Frontend (docker-compose.yml):**

```yaml
# Old:
NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1

# New:
NEXT_PUBLIC_API_URL: http://localhost/api/v1
```

**Why?**
- Frontend теперь обращается к backend через nginx (`/api/v1`)
- CORS разрешён только для `http://localhost` (nginx URL)
- В production: `https://yourdomain.com`

### 4. Testing Strategy

**Test Cases:**

1. **Frontend Access:**
   ```bash
   curl -I http://localhost/
   # Expected: 200 OK (Next.js app)
   ```

2. **API Access:**
   ```bash
   curl http://localhost/api/v1/health
   # Expected: 404 (нет такого endpoint)

   curl http://localhost/health
   # Expected: {"status": "ok"}
   ```

3. **Swagger UI:**
   ```bash
   curl -I http://localhost/docs
   # Expected: 200 OK (HTML page)
   ```

4. **OpenAPI Schema:**
   ```bash
   curl http://localhost/openapi.json
   # Expected: 200 OK (JSON schema)
   ```

5. **Database Isolation:**
   ```bash
   psql -h localhost -p 5432 -U postgres -d lunch_bot
   # Expected: Connection refused (port not exposed)
   ```

6. **Kafka Isolation:**
   ```bash
   kafka-console-consumer --bootstrap-server localhost:9092 --topic test
   # Expected: Connection refused
   ```

7. **Redis Isolation:**
   ```bash
   redis-cli -h localhost -p 6379 ping
   # Expected: Connection refused
   ```

8. **Internal Access (from backend to postgres):**
   ```bash
   docker exec -it lunch-bot-backend psql postgresql://postgres:password@postgres:5432/lunch_bot -c "SELECT 1"
   # Expected: 1
   ```

9. **Frontend → Backend (через nginx):**
   - Открыть `http://localhost/` в браузере
   - Проверить DevTools → Network: запросы к `/api/v1/*` работают

10. **Next.js Hot Reload (WebSocket):**
    - Изменить `frontend_mini_app/src/app/page.tsx`
    - Проверить: страница обновилась без перезагрузки

---

## Implementation Plan

### Subtask 1: Create Nginx Configuration

**Goal:** Создать `nginx/nginx.conf` с маршрутизацией

**Files:**
- **Created:** `nginx/nginx.conf`

**Key Points:**
- Upstream definitions для frontend и backend
- Location blocks с правильным приоритетом
- Proxy headers для X-Real-IP, X-Forwarded-For
- WebSocket support (Upgrade, Connection headers)
- Client max body size 10M
- Logging to `/var/log/nginx/`
- Комментарии для HTTPS (Let's Encrypt)

**Acceptance:**
- ✅ Конфигурация проходит `nginx -t` (syntax check)
- ✅ Маршрутизация для `/`, `/api/`, `/health`, `/docs`, `/openapi.json`
- ✅ WebSocket headers для Next.js HMR

### Subtask 2: Update Docker Compose

**Goal:** Добавить nginx, убрать публичные порты, обновить зависимости

**Files:**
- **Modified:** `docker-compose.yml`

**Changes:**

1. **Add nginx service:**
   - Image: `nginx:1.27-alpine`
   - Ports: `80:80`
   - Volumes: `nginx.conf`, `nginx_logs`
   - Depends_on: frontend, backend
   - Health check: `wget http://localhost/health`

2. **Remove ports from:**
   - postgres (убрать `5432:5432`)
   - kafka (убрать `9092:9092`)
   - redis (убрать `6379:6379`)
   - backend (убрать `8000:8000`)
   - frontend (убрать `3000:3000`)

3. **Update Kafka environment:**
   - Убрать `PLAINTEXT_HOST://localhost:9092` из `KAFKA_ADVERTISED_LISTENERS`
   - Оставить только `PLAINTEXT://kafka:29092`

4. **Update backend environment:**
   - `CORS_ORIGINS: '["http://localhost"]'`

5. **Update frontend environment:**
   - `NEXT_PUBLIC_API_URL: http://localhost/api/v1`

6. **Update frontend build args:**
   - `NEXT_PUBLIC_API_URL: http://localhost/api/v1`

7. **Add nginx_logs volume:**
   ```yaml
   volumes:
     nginx_logs:
   ```

**Acceptance:**
- ✅ `docker-compose config` проходит без ошибок
- ✅ Все сервисы имеют `networks: - lunch-bot-network`
- ✅ Только nginx имеет публичный порт

### Subtask 3: Update Environment Variables

**Goal:** Обновить `.env.example` с новыми CORS origins

**Files:**
- **Modified:** `backend/.env.example`

**Changes:**
```bash
# Old:
CORS_ORIGINS=["http://localhost:3000","http://frontend:3000"]

# New:
CORS_ORIGINS=["http://localhost"]

# Add comment for production:
# Production example with HTTPS:
# CORS_ORIGINS=["https://yourdomain.com"]
```

**Acceptance:**
- ✅ `.env.example` содержит новый CORS_ORIGINS
- ✅ Добавлен комментарий для production

### Subtask 4: Testing & Validation

**Goal:** Убедиться, что всё работает

**Actions:**

1. **Start services:**
   ```bash
   docker-compose down -v
   docker-compose up --build
   ```

2. **Run test suite:**
   ```bash
   # Frontend
   curl -I http://localhost/

   # Health check
   curl http://localhost/health

   # API docs
   curl -I http://localhost/docs
   curl http://localhost/openapi.json

   # Database isolation
   psql -h localhost -p 5432 -U postgres  # должно fail

   # Internal access
   docker exec -it lunch-bot-backend python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; asyncio.run(create_async_engine('postgresql+asyncpg://postgres:password@postgres:5432/lunch_bot').connect())"
   ```

3. **Browser testing:**
   - Open `http://localhost/`
   - Check DevTools → Network: API calls to `/api/v1/*`
   - Check Console: no CORS errors

4. **WebSocket testing:**
   - Edit `frontend_mini_app/src/app/page.tsx`
   - Verify: page reloads automatically (HMR works)

**Acceptance:**
- ✅ Все curl тесты проходят
- ✅ Frontend отображается в браузере
- ✅ API вызовы работают без CORS ошибок
- ✅ PostgreSQL/Kafka/Redis недоступны извне
- ✅ WebSocket hot-reload работает

---

## Production Considerations

### 1. HTTPS/SSL Setup

**Current State:** HTTP only (port 80)

**Production Requirements:**
- Let's Encrypt SSL certificate
- Nginx конфигурация для HTTPS (port 443)
- HTTP → HTTPS redirect

**Nginx Config Extension (commented out):**

```nginx
# HTTPS server (uncomment for production)
# server {
#     listen 443 ssl http2;
#     server_name yourdomain.com;
#
#     ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
#     ssl_protocols TLSv1.2 TLSv1.3;
#     ssl_ciphers HIGH:!aNULL:!MD5;
#
#     # ... same location blocks as HTTP
# }
#
# # HTTP → HTTPS redirect
# server {
#     listen 80;
#     server_name yourdomain.com;
#     return 301 https://$server_name$request_uri;
# }
```

**Certbot Integration:**

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d yourdomain.com

# Auto-renewal
certbot renew --dry-run
```

### 2. Rate Limiting

**Risk:** DDoS attacks, API abuse

**Solution:** Nginx `limit_req` module

**Example (commented out in nginx.conf):**

```nginx
http {
    # Rate limiting zone (10MB = ~160k IP addresses)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            # ... proxy_pass
        }
    }
}
```

### 3. Monitoring

**Nginx Logs:**
- `/var/log/nginx/access.log` — все запросы
- `/var/log/nginx/error.log` — ошибки proxy

**Log Format:**

```nginx
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for" '
                'rt=$request_time uct="$upstream_connect_time" '
                'uht="$upstream_header_time" urt="$upstream_response_time"';

access_log /var/log/nginx/access.log main;
```

**Metrics to Monitor:**
- Request rate
- Response time (`$request_time`)
- Upstream connect time (`$upstream_connect_time`)
- 4xx/5xx error rate
- Traffic volume

**Integration with Prometheus:**
- nginx-prometheus-exporter
- Grafana dashboard

### 4. Security Headers

**Add to nginx.conf:**

```nginx
server {
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

**For Production (strict CSP):**

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.telegram.org;" always;
```

### 5. Caching

**Static Assets (Next.js):**

```nginx
location /_next/static/ {
    proxy_pass http://frontend;
    proxy_cache_valid 200 1y;
    add_header Cache-Control "public, immutable";
}
```

**API (conditional):**

```nginx
location /api/v1/menu/ {
    proxy_pass http://backend;
    proxy_cache_valid 200 5m;  # cache successful responses for 5 minutes
}
```

### 6. Backup Plan

**Rollback Strategy:**

1. **Keep old ports commented:**
   ```yaml
   # backend:
   #   ports:
   #     - "8000:8000"  # uncomment for rollback
   ```

2. **Git tag before deploy:**
   ```bash
   git tag -a v1.0-pre-nginx -m "Before nginx reverse proxy"
   ```

3. **Rollback command:**
   ```bash
   git revert <nginx-commit-hash>
   docker-compose up -d
   ```

---

## Risks & Mitigations

### Risk 1: CORS Issues

**Problem:** Frontend не может обращаться к backend через nginx

**Mitigation:**
- Тестировать CORS локально перед деплоем
- Проверить `CORS_ORIGINS` в backend
- Проверить `proxy_set_header Host` в nginx
- DevTools → Console: проверить ошибки CORS

**Fallback:**
- Временно вернуть `CORS_ORIGINS=["*"]` для дебага
- Проверить nginx logs: `docker logs lunch-bot-nginx`

### Risk 2: WebSocket не работает

**Problem:** Next.js hot-reload не работает (требует WebSocket)

**Mitigation:**
- Добавить `Upgrade` и `Connection` headers в nginx
- Проверить: `http_version 1.1` в proxy_pass

**Fallback:**
- Использовать `npm run build && npm run start` (production mode без HMR)

### Risk 3: Database недоступна для дебага

**Problem:** Нельзя подключиться к PostgreSQL с хоста

**Mitigation:**
- Использовать `docker exec` для доступа:
  ```bash
  docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot
  ```
- Альтернатива: временно открыть порт для дебага, закрыть после

**Documentation:**
- Добавить команды для дебага в README

### Risk 4: Nginx не стартует

**Problem:** Ошибка в `nginx.conf` (syntax error)

**Mitigation:**
- Валидация конфигурации перед docker-compose:
  ```bash
  docker run --rm -v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx:1.27-alpine nginx -t
  ```
- CI/CD: добавить тест конфигурации

**Fallback:**
- Откатить `docker-compose.yml` на старую версию

### Risk 5: Performance Degradation

**Problem:** Nginx добавляет latency

**Mitigation:**
- Nginx очень быстрый (~1-2ms overhead)
- Использовать `proxy_buffering off` для real-time API
- Monitoring: сравнить latency до/после nginx

**Benchmark:**
```bash
# Before nginx
ab -n 1000 -c 10 http://localhost:8000/health

# After nginx
ab -n 1000 -c 10 http://localhost/health
```

---

## Documentation Updates

### README.md

**Add Section: "Development Setup"**

```markdown
## Development Setup

### Running with Docker Compose

All services are accessible through a single entry point: `http://localhost`

- **Frontend (Telegram Mini App):** http://localhost/
- **Backend API:** http://localhost/api/v1/
- **API Documentation (Swagger):** http://localhost/docs
- **Health Check:** http://localhost/health

**Start services:**

```bash
docker-compose up --build
```

**Access internal services for debugging:**

```bash
# PostgreSQL
docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot

# Redis
docker exec -it lunch-bot-redis redis-cli

# Backend shell
docker exec -it lunch-bot-backend bash
```

**Note:** PostgreSQL, Kafka, and Redis are NOT exposed to the host for security reasons. Use `docker exec` to access them.
```

### backend/.env.example

**Add Comment:**

```bash
# CORS
# Development: Nginx reverse proxy
CORS_ORIGINS=["http://localhost"]

# Production example with HTTPS:
# CORS_ORIGINS=["https://yourdomain.com"]

# Why only http://localhost?
# - Frontend и Backend доступны через Nginx (единая точка входа)
# - Это упрощает HTTPS setup (один сертификат для всех сервисов)
```

### DEPLOYMENT.md (create if not exists)

**New File:** `DEPLOYMENT.md`

```markdown
# Deployment Guide

## Production Nginx Setup

### 1. Domain Configuration

1. Point your domain to the server IP:
   ```
   yourdomain.com → 123.45.67.89
   ```

2. Update `nginx/nginx.conf`:
   ```nginx
   server_name yourdomain.com;
   ```

3. Update `backend/.env`:
   ```bash
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

4. Update `docker-compose.yml`:
   ```yaml
   frontend:
     environment:
       NEXT_PUBLIC_API_URL: https://yourdomain.com/api/v1
   ```

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

### 3. Security Hardening

- Enable rate limiting (uncomment in nginx.conf)
- Add security headers (X-Frame-Options, CSP)
- Configure firewall (UFW, iptables)
- Enable fail2ban for brute-force protection

### 4. Monitoring

- Nginx access logs: `/var/log/nginx/access.log`
- Nginx error logs: `/var/log/nginx/error.log`
- Docker logs: `docker-compose logs -f`
```

---

## Success Criteria

### Must Have (Blocker)

- ✅ Nginx конфигурация проходит `nginx -t`
- ✅ `docker-compose up` стартует без ошибок
- ✅ Frontend доступен на `http://localhost/`
- ✅ Backend API доступен на `http://localhost/api/v1/*`
- ✅ Swagger UI доступен на `http://localhost/docs`
- ✅ PostgreSQL/Kafka/Redis недоступны извне (только internal network)
- ✅ Frontend может обращаться к Backend (CORS OK)

### Should Have (Important)

- ✅ WebSocket (Next.js HMR) работает
- ✅ Health check endpoint работает: `http://localhost/health`
- ✅ Nginx логи пишутся в `/var/log/nginx/`
- ✅ Команды для дебага в README (docker exec)
- ✅ `.env.example` обновлён

### Nice to Have (Optional)

- ✅ HTTPS конфигурация закомментирована (готово к production)
- ✅ Rate limiting закомментирован (готово к production)
- ✅ Security headers закомментированы
- ✅ DEPLOYMENT.md создан

---

## Summary

### Changes Overview

| Component | Change | Impact |
|-----------|--------|--------|
| **Nginx** | Added reverse proxy | Single entry point (port 80) |
| **PostgreSQL** | Removed public port 5432 | Security ✅ |
| **Kafka** | Removed public port 9092 | Security ✅ |
| **Redis** | Removed public port 6379 | Security ✅ |
| **Backend** | Removed public port 8000 | Access via nginx only |
| **Frontend** | Removed public port 3000 | Access via nginx only |
| **CORS** | Updated to `http://localhost` | Single origin |
| **API URL** | Updated to `/api/v1` | Nginx routing |

### Benefits

1. **Security:**
   - 80% reduction in attack surface (5 ports → 1 port)
   - Database isolation (no external access)
   - Centralized access control

2. **Operations:**
   - Single DNS entry
   - Single SSL certificate (for production)
   - Centralized logging and monitoring

3. **Developer Experience:**
   - Unified URL scheme (`http://localhost/`)
   - No port juggling
   - Easy transition to production

### Next Steps for Coder

1. Create `nginx/nginx.conf` (Subtask 1)
2. Update `docker-compose.yml` (Subtask 2)
3. Update `backend/.env.example` (Subtask 3)
4. Run tests (Subtask 4)

---

## References

- **Nginx Docs:** https://nginx.org/en/docs/
- **Docker Compose Networking:** https://docs.docker.com/compose/networking/
- **FastAPI CORS:** https://fastapi.tiangolo.com/tutorial/cors/
- **Next.js Deployment:** https://nextjs.org/docs/deployment
- **Let's Encrypt:** https://letsencrypt.org/getting-started/
