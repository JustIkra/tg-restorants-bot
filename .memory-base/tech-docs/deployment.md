# Deployment Guide

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
     build:
       args:
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
