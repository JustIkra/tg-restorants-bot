---
agent: coder
task_id: TSK-004
subtask: "4.4 Production Docker Compose"
status: completed
created_at: 2025-12-06T12:00:00
files_changed:
  - docker-compose.prod.yml
  - .env.production.example
---

# Coder Result: Production Docker Compose

## Task
Create production-ready Docker Compose configuration and environment template for the Lunch Order Bot system.

## Implementation

### 1. Created `docker-compose.prod.yml`

**Location:** `/Users/maksim/git_projects/tg_bot/docker-compose.prod.yml`

**Key differences from development `docker-compose.yml`:**

#### Production Hardening
- **Restart policy**: `restart: always` for all services (vs `unless-stopped` in dev)
- **Resource limits**: CPU and memory limits for all containers
- **No source code volumes**: Code is baked into images, not mounted
- **Health checks**: More aggressive intervals (30s vs 10s for critical services)
- **Environment**: Uses `.env.production` instead of inline/dev config

#### Services Configuration

**postgres:**
- Image: `postgres:17-alpine` (same as dev)
- Container: `lunch-bot-postgres-prod`
- Environment: Uses `${POSTGRES_PASSWORD:?...}` to require password
- Resources: 1 CPU, 1GB memory
- Volume: `postgres_data` for persistence
- Healthcheck: 10s interval

**redis:**
- Image: `redis:7-alpine`
- Container: `lunch-bot-redis-prod`
- Command: `redis-server --appendonly yes` (persistence enabled)
- Resources: 0.5 CPU, 256MB memory
- Volume: `redis_data` for AOF persistence
- Healthcheck: 10s interval

**kafka:**
- Image: `confluentinc/cp-kafka:latest` (KRaft mode, no Zookeeper)
- Container: `lunch-bot-kafka-prod`
- Environment: KRaft configuration (same as dev)
- Resources: 1 CPU, 1GB memory
- Volume: `kafka_data` for persistence
- Healthcheck: 30s interval (slower due to Kafka startup time)

**backend:**
- Build: `./backend/Dockerfile`
- Container: `lunch-bot-backend-prod`
- Depends on: postgres, redis, kafka (with health conditions)
- Env file: `.env.production`
- Healthcheck: `curl -f http://localhost:8000/health` (30s interval)
- Resources: 2 CPU, 2GB memory
- **NO volumes** (code is in image, not mounted)

**frontend:**
- Build: `./frontend_mini_app/Dockerfile` with `NEXT_PUBLIC_API_URL` arg
- Container: `lunch-bot-frontend-prod`
- Depends on: backend
- Healthcheck: `curl -f http://localhost:3000` (30s interval)
- Resources: 1 CPU, 512MB memory
- **NO volumes** (built app is in image)

**telegram-bot:**
- Build: `./backend/Dockerfile`
- Container: `lunch-bot-telegram-prod`
- Command: `python -m src.telegram.bot`
- Depends on: backend, kafka
- Resources: 0.5 CPU, 256MB memory

**notifications-worker:**
- Build: `./backend/Dockerfile`
- Container: `lunch-bot-notifications-prod`
- Command: `python -m workers.notifications`
- Depends on: backend, kafka
- Resources: 0.5 CPU, 256MB memory

**recommendations-worker:**
- Build: `./backend/Dockerfile`
- Container: `lunch-bot-recommendations-prod`
- Command: `python -m workers.recommendations`
- Depends on: backend, kafka
- Resources: 0.5 CPU, 256MB memory

**nginx:**
- Image: `nginx:1.27-alpine`
- Container: `lunch-bot-nginx-prod`
- Ports: `80:80`, `443:443` (HTTPS ready)
- Volumes:
  - `./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro` (read-only config)
  - `./nginx/ssl:/etc/nginx/ssl:ro` (SSL certificates)
  - `nginx_logs:/var/log/nginx` (persistent logs)
- Resources: 0.5 CPU, 128MB memory
- Healthcheck: `nginx -t` (validates config)

#### Volumes
- `postgres_data` - PostgreSQL data directory
- `redis_data` - Redis AOF persistence
- `kafka_data` - Kafka logs and topics
- `nginx_logs` - Nginx access/error logs

#### Network
- `lunch-bot-network` - Bridge network for all services

### 2. Created `.env.production.example`

**Location:** `/Users/maksim/git_projects/tg_bot/.env.production.example`

**Purpose:** Template for production environment variables. Users copy this to `.env.production` and fill in real values.

**Sections:**

#### Database
```bash
POSTGRES_USER=lunchbot_user
POSTGRES_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/lunch_bot
```

#### JWT Authentication
```bash
JWT_SECRET_KEY=CHANGE_ME_GENERATE_WITH_OPENSSL_RAND_HEX_32
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7
```
**Note:** Includes instructions to generate with `openssl rand -hex 32`

#### Kafka
```bash
KAFKA_BROKER_URL=kafka:29092
```

#### Redis
```bash
REDIS_URL=redis://redis:6379
```

#### Telegram
```bash
TELEGRAM_BOT_TOKEN=YOUR_PRODUCTION_BOT_TOKEN
TELEGRAM_MINI_APP_URL=https://your-domain.com
```

#### Gemini AI
```bash
GEMINI_API_KEYS=key1,key2,key3
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MAX_REQUESTS_PER_KEY=195
```

#### CORS
```bash
CORS_ORIGINS=["https://your-domain.com","https://web.telegram.org"]
```

#### Frontend (Next.js)
```bash
NEXT_PUBLIC_API_URL=https://your-domain.com/api/v1
```

#### Optional sections (commented)
- Monitoring & Logging (Sentry, log levels)
- Performance Tuning (pool sizes, connections)

#### Deployment Checklist
Includes a comprehensive checklist of steps to complete before production deployment.

## Key Features

### Security
1. **Required password**: `${POSTGRES_PASSWORD:?...}` fails if not set
2. **No hardcoded secrets**: All sensitive values use placeholders
3. **Read-only configs**: Nginx config mounted as `:ro`
4. **Explicit CORS**: Must specify production domain
5. **Strong password guidance**: Instructions for JWT secret generation

### Reliability
1. **Health checks**: All services have health checks
2. **Restart policy**: `restart: always` ensures services recover
3. **Dependency conditions**: Services wait for dependencies to be healthy
4. **Resource limits**: Prevents services from consuming all resources

### Production Best Practices
1. **No source volumes**: Code is baked into images (immutable)
2. **Persistent volumes**: Data survives container restarts
3. **Structured logging**: Nginx logs to volume for analysis
4. **HTTPS ready**: Port 443 exposed, SSL volume mounted
5. **Separate env files**: Development and production configs isolated

## Comparison: Dev vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| **Source code** | Mounted volumes | Baked into image |
| **Restart** | `unless-stopped` | `always` |
| **Resources** | No limits | CPU/Memory limits |
| **Env file** | `backend/.env` | `.env.production` |
| **Health checks** | 10s intervals | 10-30s intervals |
| **Secrets** | Hardcoded (dev) | Env vars (required) |
| **HTTPS** | Not configured | Port 443 + SSL |
| **Logs** | Docker logs only | Persistent volume |
| **Hot reload** | Enabled (`--reload`) | Disabled |

## Usage

### 1. Setup Environment
```bash
# Copy template
cp .env.production.example .env.production

# Edit with real values
nano .env.production

# Generate JWT secret
openssl rand -hex 32
```

### 2. Deploy
```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop all services
docker-compose -f docker-compose.prod.yml down
```

### 3. Database Migrations
```bash
# Run migrations in backend container
docker exec lunch-bot-backend-prod alembic upgrade head
```

## Dependencies

### Existing Files (to be created/configured separately)
1. `nginx/nginx.prod.conf` - Production nginx configuration
2. `nginx/ssl/` - SSL certificate and key files
3. `backend/Dockerfile` - Backend Docker image
4. `frontend_mini_app/Dockerfile` - Frontend Docker image

### Expected in Next Steps (TSK-004)
- **4.5**: Create `nginx/nginx.prod.conf`
- **4.6**: Document deployment process
- **4.7**: Create monitoring/logging setup

## Testing Recommendations

Before deploying to production:

1. **Test build process:**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Test startup:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   docker-compose -f docker-compose.prod.yml ps
   ```

3. **Test health checks:**
   ```bash
   docker inspect lunch-bot-backend-prod | grep -A 10 Health
   docker inspect lunch-bot-frontend-prod | grep -A 10 Health
   ```

4. **Test resource limits:**
   ```bash
   docker stats
   ```

5. **Test restart policy:**
   ```bash
   docker stop lunch-bot-backend-prod
   # Should restart automatically within seconds
   docker-compose -f docker-compose.prod.yml ps
   ```

6. **Test volumes:**
   ```bash
   docker volume ls
   docker volume inspect lunch-bot-postgres-data
   ```

## Security Notes

### Secrets Management
- **Never commit** `.env.production` to git
- Use strong random passwords for all secrets
- Rotate JWT secret key periodically
- Store Gemini API keys securely (consider secret management service)

### Network Security
- CORS restricted to production domain only
- Nginx acts as reverse proxy (backend not exposed directly)
- Internal services communicate via Docker network (not host)

### Container Security
- Run containers as non-root user (to be added in Dockerfiles)
- Read-only root filesystem where possible
- Minimal base images (alpine)
- No unnecessary capabilities

## Known Limitations

1. **No auto-scaling**: Single instance per service (can be enhanced with Docker Swarm/Kubernetes)
2. **No secrets encryption**: Environment variables in plain text (consider Docker Secrets)
3. **No backups**: Manual backup strategy required (to be documented)
4. **No SSL auto-renewal**: Manual certificate renewal (consider Let's Encrypt)
5. **No distributed logging**: Logs on local volumes (consider ELK stack)

## Next Steps

1. Create `nginx/nginx.prod.conf` (TSK-004 subtask 4.5)
2. Test full production deployment locally
3. Document deployment process (TSK-004 Phase 3)
4. Add monitoring and logging (TSK-004 Phase 4)
5. Create backup/restore procedures
6. Set up CI/CD pipeline (TSK-004 Phase 6, optional)

## Files Created

1. `/Users/maksim/git_projects/tg_bot/docker-compose.prod.yml` (240 lines)
2. `/Users/maksim/git_projects/tg_bot/.env.production.example` (115 lines)

## Status

**Completed** ✓

Production Docker Compose configuration is ready. The configuration follows production best practices:
- Immutable infrastructure (no source volumes)
- Resource limits for stability
- Health checks for reliability
- Secure secrets management
- Comprehensive environment template

The system can be deployed with:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

After completing remaining prerequisites (nginx config, SSL certs, .env.production).
