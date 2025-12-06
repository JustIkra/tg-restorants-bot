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
- Server: `user@172.25.0.200:22`
- External Nginx Proxy Manager (on separate server) for HTTPS termination
- Docker Compose for service orchestration
- Internal nginx for routing between frontend and backend

### Architecture

```
Internet
    ↓
Nginx Proxy Manager (external server, HTTPS)
    ↓
172.25.0.200:80 (production server)
    ↓
docker nginx (lunch-bot-nginx container)
    ↓
    ┌────────┴─────────┐
    │                  │
    ▼                  ▼
frontend:3000     backend:8000
```

### Deployment Steps

**1. SSH to production server:**

```bash
ssh user@172.25.0.200
```

**2. Clone or update repository:**

```bash
# First time
git clone <repository-url> /path/to/tg_bot
cd /path/to/tg_bot

# Updates
cd /path/to/tg_bot
git pull origin main
```

**3. Configure environment variables:**

Edit `backend/.env`:
```bash
# Database (production credentials)
DATABASE_URL=postgresql+asyncpg://postgres:secure_password@postgres:5432/lunch_bot

# Telegram
TELEGRAM_BOT_TOKEN=your_production_bot_token
TELEGRAM_MINI_APP_URL=https://lunchbot.vibe-labs.ru

# CORS (production domains)
CORS_ORIGINS=["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]

# JWT (generate secure key)
JWT_SECRET_KEY=your_very_secure_secret_key_here

# Gemini API
GEMINI_API_KEYS=key1,key2,key3
```

Edit `frontend_mini_app/.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://lunchbot.vibe-labs.ru/api/v1
```

**4. Update docker-compose.yml (if needed):**

Ensure CORS is correctly set:
```yaml
backend:
  environment:
    CORS_ORIGINS: '["https://lunchbot.vibe-labs.ru","https://web.telegram.org"]'
```

**5. Build and start services:**

```bash
docker-compose up --build -d
```

**6. Check service status:**

```bash
docker-compose ps
```

All services should show "Up" status.

**7. Verify health check:**

```bash
curl http://localhost/health
```

Should return: `{"status":"ok"}`

### Nginx Proxy Manager Configuration

Configure external Nginx Proxy Manager to forward traffic to production server:

**Proxy Host settings:**
- Domain Names: `lunchbot.vibe-labs.ru`
- Scheme: `http`
- Forward Hostname/IP: `172.25.0.200`
- Forward Port: `80`
- Cache Assets: Yes
- Block Common Exploits: Yes
- Websockets Support: Yes

**SSL settings:**
- SSL Certificate: Let's Encrypt or custom
- Force SSL: Yes
- HTTP/2 Support: Yes
- HSTS Enabled: Yes

### Post-Deployment Verification

**1. Check frontend:**
```bash
curl https://lunchbot.vibe-labs.ru
```

**2. Check backend API:**
```bash
curl https://lunchbot.vibe-labs.ru/api/v1/health
```

**3. Check API docs:**
```bash
curl https://lunchbot.vibe-labs.ru/docs
```

**4. Test Telegram Mini App:**
- Open bot in Telegram
- Send `/order` or click Menu Button
- Mini App should open and load successfully
- Check authentication works
- Test creating an order

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
