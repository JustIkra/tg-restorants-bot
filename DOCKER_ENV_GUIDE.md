# Docker & Environment Configuration Guide

This project uses separate configurations for local development and production environments.

## File Structure

```
.
├── docker-compose.yml              # Main compose (includes localdev)
├── docker-compose.localdev.yml     # Local development config
├── docker-compose.prod.yml         # Production config
├── .env.localdev.example           # Local development env template
├── .env.production.example         # Production env template
└── .env                            # Your actual env (git-ignored)
```

## Quick Start

### Local Development

1. **Create your environment file:**
   ```bash
   cp .env.localdev.example .env
   ```

2. **Edit `.env` and set required values:**
   - `TELEGRAM_BOT_TOKEN` - Get from @BotFather (create a test bot)
   - `GEMINI_API_KEYS` - Optional, get from https://aistudio.google.com/apikey

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Frontend: http://localhost
   - Backend API: http://localhost/api/v1
   - API Docs: http://localhost/api/v1/docs

5. **View logs:**
   ```bash
   # All services
   docker-compose logs -f

   # Specific service
   docker-compose logs -f backend
   ```

### Testing with Telegram Mini App

To test the Mini App in real Telegram:

1. **Install and run ngrok:**
   ```bash
   ngrok http 80
   ```

2. **Update your `.env`:**
   ```env
   TELEGRAM_MINI_APP_URL=https://your-ngrok-url.ngrok-free.app
   NEXT_PUBLIC_API_URL=https://your-ngrok-url.ngrok-free.app/api/v1
   ```

3. **Rebuild frontend:**
   ```bash
   docker-compose up -d --build frontend
   ```

4. **Set Mini App URL in Telegram:**
   - Open your test bot in Telegram
   - Go to @BotFather
   - Send `/setmenubutton`
   - Select your bot
   - Enter the ngrok URL

## Production Deployment

### Prerequisites

- Server with Docker and Docker Compose installed
- Domain name pointed to your server
- SSL certificates (Let's Encrypt recommended)

### Steps

1. **Copy production env template:**
   ```bash
   cp .env.production.example .env.production
   ```

2. **Edit `.env.production` with production values:**

   **CRITICAL - Must change:**
   ```env
   POSTGRES_PASSWORD=<strong-random-password>
   JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
   TELEGRAM_BOT_TOKEN=<your-production-bot-token>
   GEMINI_API_KEYS=<real-api-keys>
   NEXT_PUBLIC_API_URL=https://your-domain.com/api/v1
   CORS_ORIGINS=["https://your-domain.com","https://web.telegram.org"]
   ```

   **Generate secure secrets:**
   ```bash
   # Generate JWT secret
   openssl rand -hex 32

   # Generate strong password
   openssl rand -base64 32
   ```

3. **Configure nginx for HTTPS:**
   - Copy `nginx/nginx.conf` to `nginx/nginx.prod.conf`
   - Add SSL configuration
   - Place SSL certificates in `nginx/ssl/`

4. **Start production services:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Verify deployment:**
   ```bash
   # Check all services are running
   docker-compose -f docker-compose.prod.yml ps

   # Check logs
   docker-compose -f docker-compose.prod.yml logs -f

   # Test API
   curl https://your-domain.com/api/v1/health
   ```

## Environment Differences

| Aspect | Local Development | Production |
|--------|------------------|------------|
| **File** | `docker-compose.localdev.yml` | `docker-compose.prod.yml` |
| **Env** | `.env` | `.env.production` |
| **Hot Reload** | ✓ Enabled | ✗ Disabled |
| **Source Volumes** | ✓ Mounted | ✗ No volumes |
| **Resource Limits** | ✗ None | ✓ CPU/Memory limits |
| **Restart Policy** | `unless-stopped` | `always` |
| **Ports** | `80` | `80`, `443` |
| **Database Password** | `password` (simple) | Strong random |
| **JWT Secret** | `dev-secret-key` | Generated with openssl |
| **HTTPS** | ✗ HTTP only | ✓ HTTPS with SSL |

## Key Features by Environment

### Local Development (`docker-compose.localdev.yml`)

- **Hot Reload:** Code changes auto-reload without restart
- **Debug Friendly:** Detailed logs, DEBUG level
- **Simple Credentials:** Easy to remember (password/password)
- **Volume Mounts:** Source code mounted for live editing
- **Port 80 Only:** HTTP for local testing

### Production (`docker-compose.prod.yml`)

- **Optimized Builds:** No source volumes, built images only
- **Health Checks:** All services monitored
- **Resource Limits:** Prevents resource exhaustion
- **Auto Restart:** Services restart on failure
- **HTTPS Ready:** Nginx configured for SSL
- **Secure Credentials:** Strong passwords, rotated secrets

## Common Commands

### Local Development

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# View logs
docker-compose logs -f [service_name]

# Reset everything (deletes data!)
docker-compose down -v
docker-compose up -d --build

# Run backend shell
docker-compose exec backend bash

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### Production

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Update and restart
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f [service_name]

# Backup database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres lunch_bot > backup.sql
```

## Troubleshooting

### Ports Already in Use

If you get "port already allocated" errors:

```bash
# Check what's using the port
lsof -i :80
lsof -i :5432

# Stop conflicting services or change ports in docker-compose
```

### Database Connection Errors

```bash
# Check postgres is healthy
docker-compose ps postgres

# View postgres logs
docker-compose logs postgres

# Reset database (WARNING: deletes all data!)
docker-compose down -v
docker-compose up -d
```

### Frontend Not Updating

```bash
# Rebuild frontend with new env variables
docker-compose up -d --build frontend

# Check frontend logs
docker-compose logs -f frontend
```

### Kafka/Workers Not Starting

```bash
# Kafka needs time to initialize
docker-compose logs kafka

# Wait for healthy status
docker-compose ps kafka

# Restart workers after kafka is ready
docker-compose restart notifications-worker recommendations-worker
```

## Security Checklist

Before deploying to production:

- [ ] Changed `POSTGRES_PASSWORD` to strong random password
- [ ] Generated new `JWT_SECRET_KEY` with `openssl rand -hex 32`
- [ ] Using production `TELEGRAM_BOT_TOKEN` (not test bot)
- [ ] Added real `GEMINI_API_KEYS`
- [ ] Updated `CORS_ORIGINS` with production domain
- [ ] Set `NEXT_PUBLIC_API_URL` to production URL
- [ ] `.env.production` is in `.gitignore` (never commit!)
- [ ] SSL certificates installed and configured
- [ ] Nginx production config (`nginx.prod.conf`) tested
- [ ] Database backups configured
- [ ] Firewall rules configured (only 80/443 open)
- [ ] All secrets stored securely (not in git)
- [ ] Monitoring and logging configured

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt SSL](https://letsencrypt.org/)
- [PostgreSQL Backup](https://www.postgresql.org/docs/current/backup.html)
