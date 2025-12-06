---
agent: reviewer
task_id: TSK-004
status: CHANGES_REQUESTED
created_at: 2025-12-06
commit: f9c0da5
---

# Code Review: Docker Configuration Split

## Overview

Reviewed commit: `f9c0da5` - "feat(docker): split configs into localdev and production environments"

**Overall Assessment:** Code quality is good, but there are **critical security issues** that must be addressed before production deployment.

---

## Summary

The commit introduces a clean separation between local development and production Docker configurations, which is a solid architectural decision. However, several security and configuration issues were identified that require immediate attention.

---

## Critical Issues (MUST FIX)

### 1. Security: Hardcoded Credentials in docker-compose.localdev.yml

**Location:** `docker-compose.localdev.yml:28-29`

```yaml
environment:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: password  # ← CRITICAL
```

**Issue:** While this is intended for local development, hardcoded credentials in committed files create a security risk. Developers might accidentally deploy this configuration to production.

**Recommendation:**
- Even for local development, credentials should come from `.env` files
- Update to use environment variables:
  ```yaml
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-postgres}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
  ```

---

### 2. Security: .env.production Not Properly Gitignored

**Location:** `.gitignore:2`

```gitignore
.env
```

**Issue:** The `.gitignore` only covers `.env`, but not `.env.production`. This means if someone creates `.env.production` file, it could be accidentally committed with real production secrets.

**Recommendation:**
Add to `.gitignore`:
```gitignore
.env
.env.*
!.env.*.example
```

This will ignore all `.env.*` files except the example templates.

---

### 3. Configuration: Missing nginx.prod.conf

**Location:** `docker-compose.prod.yml:211`

```yaml
volumes:
  - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
```

**Issue:** The production docker-compose references `nginx/nginx.prod.conf`, but this file doesn't exist in the repository. Only `nginx/nginx.conf` exists.

**Impact:** Production deployment will fail due to missing file.

**Recommendation:**
Either:
1. Create `nginx/nginx.prod.conf` with production-specific settings (HTTPS, rate limiting, security headers)
2. Update `docker-compose.prod.yml` to use `./nginx/nginx.conf` (if same config is acceptable)

**Suggested nginx.prod.conf features:**
- HTTPS/TLS configuration
- Security headers (CSP, X-Frame-Options, etc.)
- Rate limiting enabled
- Access log rotation
- Compression (gzip)

---

## High Priority Issues (SHOULD FIX)

### 4. Docker: Production Images Not Optimized

**Location:** `docker-compose.prod.yml:82-108`

**Issue:** Production services don't specify image tags or use multi-stage builds. This can lead to:
- Inconsistent deployments (different image versions)
- Larger image sizes
- Slower startup times

**Current:**
```yaml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
```

**Recommendation:**
Use image versioning:
```yaml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
    target: production  # if multi-stage build
  image: lunch-bot-backend:1.0.0
```

---

### 5. Docker: No Health Check for Telegram Bot Worker

**Location:** `docker-compose.prod.yml:137-155`

**Issue:** The `telegram-bot` service has no health check, making it harder to detect failures.

**Recommendation:**
Add health check:
```yaml
telegram-bot:
  # ... other config
  healthcheck:
    test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
    interval: 30s
    timeout: 10s
    retries: 3
```

Or implement a proper health endpoint in the bot code.

---

### 6. Backend: Health Check Missing Kafka Test

**Location:** `backend/src/routers/health.py:49-79`

**Issue:** The `/health/all` endpoint checks PostgreSQL and Redis, but **not Kafka**. Given that Kafka is critical for notifications and recommendations workers, this is a significant omission.

**Current:**
```python
async def health_all():
    # Check PostgreSQL ✓
    # Check Redis ✓
    # Check Kafka ✗ (MISSING)
```

**Recommendation:**
Add Kafka health check:
```python
# Check Kafka
try:
    from aiokafka import AIOKafkaProducer
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BROKER_URL)
    await producer.start()
    await producer.stop()
    results["services"]["kafka"] = "ok"
except Exception as e:
    results["status"] = "degraded"
    results["services"]["kafka"] = f"error: {str(e)}"
```

---

## Medium Priority Issues (NICE TO HAVE)

### 7. Docker: Duplicate Environment Variables

**Location:** `docker-compose.localdev.yml:85-102`

**Issue:** Environment variables are defined both in `env_file` and `environment` block, creating redundancy and potential conflicts.

**Current:**
```yaml
backend:
  env_file: ./backend/.env
  environment:
    DATABASE_URL: postgresql+asyncpg://...
    KAFKA_BROKER_URL: kafka:29092
    # ... etc
```

**Recommendation:**
Choose one approach:
- **Option A:** Use only `env_file` and put all variables in `.env`
- **Option B:** Use only `environment` with variable substitution

**Preferred (Option B):**
```yaml
backend:
  environment:
    DATABASE_URL: ${DATABASE_URL}
    KAFKA_BROKER_URL: ${KAFKA_BROKER_URL}
```

This makes it explicit which variables are required and allows `.env` file to be optional for advanced users.

---

### 8. Frontend: isTelegramWebApp Logic Issue

**Location:** `frontend_mini_app/src/lib/telegram/webapp.ts:118`

**Issue:** The `isTelegramWebApp()` function checks for `WebApp.initData`, but `initData` can be an empty string in development or when running outside Telegram.

**Current:**
```typescript
export function isTelegramWebApp(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }
  return Boolean(WebApp && WebApp.initData);  // ← Can be empty string
}
```

**Problem:** Empty string `""` is falsy, so this works correctly. However, the comment on line 3 says "for development", but the function will return `false` even in Telegram if `initData` is empty.

**Recommendation:**
More robust check:
```typescript
export function isTelegramWebApp(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }
  // Check if Telegram WebApp SDK is available
  return Boolean(WebApp && WebApp.platform && WebApp.platform !== 'unknown');
}
```

This checks for the Telegram platform instead of `initData`, which is more reliable.

---

### 9. Tests: Integration Tests Mock Too Much

**Location:** `backend/tests/integration/test_kafka_notifications.py`

**Issue:** The "integration" tests heavily mock external dependencies (httpx, Redis, Kafka), making them more like unit tests. True integration tests should test real interactions.

**Example:**
```python
@pytest.fixture
def mock_httpx_client(self):
    """Mock httpx.AsyncClient for Telegram API calls."""
    with patch("backend.workers.notifications.httpx.AsyncClient") as mock_client:
        # ... heavy mocking
```

**Impact:** These tests won't catch integration issues like:
- Network timeouts
- Actual Telegram API response format changes
- Redis serialization issues

**Recommendation:**
- Rename to `test_kafka_notifications_unit.py` (more accurate)
- Consider adding true integration tests that use:
  - Test Kafka instance (Testcontainers)
  - Test Redis instance
  - Mock Telegram API server (not mocked client)

---

### 10. Tests: E2E Tests Are Too Minimal

**Location:** `frontend_mini_app/tests/e2e/*.spec.ts`

**Issue:** The Playwright E2E tests are very basic and mostly check for static content. They don't test user flows or API interactions.

**Current coverage:**
- ✓ Page loads
- ✓ Shows fallback outside Telegram
- ✗ No user interaction testing
- ✗ No API mocking/testing
- ✗ No form submissions

**Recommendation:**
Add tests for:
- Menu browsing flow
- Order creation flow (with mocked backend)
- Error handling (network failures)
- Loading states

---

## Positive Aspects

### ✓ Good Architecture Decisions

1. **Clean separation** of local vs production configs
2. **Health check endpoints** implemented correctly
3. **Proper Docker networking** with named networks
4. **Volume management** for persistence
5. **Comprehensive .env.example files** with helpful comments

### ✓ Code Quality

1. **Type hints** in Python code (health.py)
2. **Error handling** in health checks (try/except with proper HTTP status codes)
3. **Async/await** used correctly throughout
4. **Clear comments** in Docker and .env files

### ✓ Testing

1. **Good test coverage** for workers (notifications, recommendations)
2. **Proper test fixtures** in conftest.py
3. **Realistic test scenarios** (rate limiting, API errors, multiple users)

---

## Security Checklist

- [ ] Remove hardcoded credentials from docker-compose.localdev.yml
- [ ] Update .gitignore to cover .env.production
- [ ] Create nginx.prod.conf with proper security headers
- [ ] Verify CORS_ORIGINS in production (no localhost!)
- [ ] Ensure JWT_SECRET_KEY is strong random value in production
- [ ] Review POSTGRES_PASSWORD requirements (min 16 chars, random)
- [ ] Add rate limiting to production nginx
- [ ] Enable HTTPS/TLS in production nginx

---

## Testing Recommendations

### Before Merging:
1. Test local development startup: `docker-compose up -d`
2. Verify all services are healthy: `docker-compose ps`
3. Test health endpoints: `curl http://localhost/health/all`
4. Verify frontend loads: `curl http://localhost`

### Before Production Deployment:
1. Create .env.production from template
2. Fill in real credentials (generated with `openssl rand -hex 32`)
3. Test production build: `docker-compose -f docker-compose.prod.yml build`
4. Dry-run: `docker-compose -f docker-compose.prod.yml config`
5. Create nginx.prod.conf with SSL certificates
6. Test with staging environment first

---

## Files Changed

**Added/Modified:**
- `docker-compose.yml` - Main config with include
- `docker-compose.localdev.yml` - Local development (NEW)
- `docker-compose.prod.yml` - Production config (NEW)
- `.env.localdev.example` - Local env template (NEW)
- `.env.production.example` - Production env template (NEW)
- `backend/src/routers/health.py` - Health check endpoints (NEW)
- `backend/tests/integration/test_kafka_*.py` - Worker tests (NEW)
- `frontend_mini_app/src/lib/telegram/webapp.ts` - Fixed isTelegramWebApp
- `frontend_mini_app/tests/e2e/*.spec.ts` - E2E tests (NEW)

**Missing:**
- `nginx/nginx.prod.conf` - Referenced but doesn't exist ❌

---

## Verdict

**Status:** CHANGES_REQUESTED

### Must Fix Before Production:
1. Security: Remove hardcoded credentials
2. Security: Fix .gitignore for .env files
3. Configuration: Create nginx.prod.conf or fix reference

### Should Fix for Better Quality:
4. Add Kafka health check
5. Add health check for telegram-bot worker
6. Simplify environment variable management

### Nice to Have:
7. Improve isTelegramWebApp() detection
8. Enhance E2E test coverage
9. Rename integration tests to unit tests

---

## Estimated Effort to Fix Critical Issues

- **Issue #1** (hardcoded credentials): 5 minutes
- **Issue #2** (.gitignore): 2 minutes
- **Issue #3** (nginx.prod.conf): 30-60 minutes (depending on SSL setup)

**Total:** ~1 hour to make production-ready

---

## Conclusion

The Docker configuration split is a solid architectural improvement that will benefit both development and production workflows. The code quality is generally good with proper error handling and async patterns.

However, **critical security issues** prevent this from being production-ready. The hardcoded credentials and missing production nginx configuration must be addressed immediately.

Once the critical issues are fixed, this will be a robust setup for deploying the Lunch Order Bot.

---

**Next Steps:**
1. Fix issues #1, #2, #3 (Critical)
2. Run full test suite: `pytest backend/tests/`
3. Test local development environment
4. Create production deployment checklist
5. Document production deployment process

**Reviewer:** Code Review Agent
**Date:** 2025-12-06
**Commit:** f9c0da5 (feat: docker split configs)
