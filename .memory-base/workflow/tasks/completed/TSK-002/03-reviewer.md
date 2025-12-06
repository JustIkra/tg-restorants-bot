---
agent: reviewer
task_id: TSK-002
status: completed
next: coder
created_at: 2025-12-06T04:30:00Z
---

## Review Result: CHANGES REQUESTED

The backend code has been reviewed for TSK-002. While the overall architecture is solid and follows many best practices, there are several **critical security issues** and important improvements needed before proceeding to testing.

---

## Critical Issues

### 1. **SQL Injection Risk in Repository Update Methods**
**File:** `backend/src/repositories/order.py:71-76`, `backend/src/repositories/base.py:34-39`

```python
async def update(self, order: Order, **kwargs) -> Order:
    for key, value in kwargs.items():
        if value is not None:
            setattr(order, key, value)  # UNSAFE: allows arbitrary attribute assignment
    await self.session.flush()
    return order
```

**Issue:** Using `setattr` with unchecked `kwargs` allows arbitrary attribute assignment. An attacker could potentially modify protected attributes or bypass validation.

**Fix:** Use explicit field mapping or validate allowed fields:
```python
ALLOWED_FIELDS = {"combo_id", "combo_items", "extras", "notes", "total_price"}

async def update(self, order: Order, **kwargs) -> Order:
    for key, value in kwargs.items():
        if key not in ALLOWED_FIELDS:
            raise ValueError(f"Field {key} cannot be updated")
        if value is not None:
            setattr(order, key, value)
    await self.session.flush()
    return order
```

**Severity:** CRITICAL - Could lead to privilege escalation or data corruption.

---

### 2. **Hardcoded Secrets in Config**
**File:** `backend/src/config.py:6, 12`

```python
DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/lunch_bot"
JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
```

**Issue:** Hardcoded default values include actual credentials and weak secrets. This violates OWASP A02:2021 - Cryptographic Failures.

**Fix:** Remove defaults for sensitive values:
```python
DATABASE_URL: str  # No default - MUST be set via .env
JWT_SECRET_KEY: str  # No default - MUST be set via .env
```

Add validation in `__init__`:
```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if self.JWT_SECRET_KEY == "your-secret-key-change-in-production":
        raise ValueError("JWT_SECRET_KEY must be changed from default")
```

**Severity:** CRITICAL - Exposes production systems to attacks.

---

### 3. **Missing Input Validation in Telegram Auth**
**File:** `backend/src/auth/telegram.py:27-29, 59-66`

**Issue:** Missing validation for:
- `auth_date` expiration (Telegram recommends checking if auth_date is recent)
- User ID type validation (should be positive integer)
- Missing rate limiting

**Fix:** Add timestamp validation:
```python
import time

# After parsing
auth_date = int(parsed.get("auth_date", 0))
current_time = int(time.time())
if current_time - auth_date > 86400:  # 24 hours
    raise TelegramAuthError("Authentication data expired")

# Validate user ID
if not isinstance(user_data.get("id"), int) or user_data["id"] <= 0:
    raise TelegramAuthError("Invalid user ID")
```

**Severity:** CRITICAL - Could allow replay attacks.

---

### 4. **JWT Token Missing Subject and Audience Claims**
**File:** `backend/src/auth/jwt.py:13-29`

**Issue:** JWT tokens don't include `sub`, `aud`, or `iss` claims, making them vulnerable to token substitution attacks.

**Fix:**
```python
to_encode.update({
    "exp": expire,
    "sub": str(data["tgid"]),  # Subject
    "aud": "lunch-bot-api",    # Audience
    "iss": "lunch-bot-backend", # Issuer
    "iat": datetime.now(timezone.utc),  # Issued at
})
```

And verify in `verify_token`:
```python
payload = jwt.decode(
    token,
    settings.JWT_SECRET_KEY,
    algorithms=[settings.JWT_ALGORITHM],
    audience="lunch-bot-api",
    issuer="lunch-bot-backend",
)
```

**Severity:** CRITICAL - Token security vulnerability.

---

## Important Issues

### 5. **Inconsistent Error Handling in Routers**
**Files:** `backend/src/routers/orders.py:82-86`, `backend/src/routers/users.py:64-69`

**Issue:** HTTPException import is done inside function instead of at module level:
```python
if current_user.role != "manager" and current_user.tgid != tgid:
    from fastapi import HTTPException, status  # Should be at top
    raise HTTPException(...)
```

**Fix:** Move imports to module level (already imported in line 4 in orders.py, just missing usage).

**Severity:** IMPORTANT - Code quality issue, affects maintainability.

---

### 6. **Missing Timezone Awareness in Deadline Service**
**File:** `backend/src/services/deadline.py:84`

```python
now = datetime.now()  # NAIVE datetime
```

**Issue:** Using naive datetime when database uses `timezone=True`. This can cause incorrect deadline comparisons across timezones.

**Fix:**
```python
from datetime import timezone
now = datetime.now(timezone.utc)
```

**Severity:** IMPORTANT - Business logic bug, affects deadline validation.

---

### 7. **Missing SQL Injection Protection in Repository Filters**
**File:** `backend/src/repositories/order.py:53-62`

**Issue:** While SQLAlchemy protects against SQL injection by default, the dynamic query building should validate enum values:

```python
if order_date:
    query = query.where(Order.order_date == order_date)
```

**Fix:** Add validation for status field if it's ever added as a filter:
```python
VALID_STATUSES = {"pending", "confirmed", "cancelled"}
if status and status not in VALID_STATUSES:
    raise ValueError(f"Invalid status: {status}")
```

**Severity:** IMPORTANT - Defense in depth.

---

### 8. **Pydantic Model Missing Field Validators**
**File:** `backend/src/schemas/order.py:7-14`

**Issue:** No validation on `category` and `quantity` fields:

```python
class ComboItemInput(BaseModel):
    category: str  # Should validate against allowed categories
    menu_item_id: int

class ExtraInput(BaseModel):
    menu_item_id: int
    quantity: int = 1  # Should validate > 0
```

**Fix:**
```python
from pydantic import Field, field_validator

class ComboItemInput(BaseModel):
    category: str = Field(..., pattern="^(soup|salad|main|extra)$")
    menu_item_id: int = Field(..., gt=0)

class ExtraInput(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)
```

**Severity:** IMPORTANT - Input validation missing.

---

### 9. **Repository Delete Method Missing Cascade Handling**
**File:** `backend/src/repositories/order.py:78-80`

```python
async def delete(self, order: Order) -> None:
    await self.session.delete(order)
    await self.session.flush()
```

**Issue:** No check for related records or soft delete pattern. Hard deletes can cause data integrity issues.

**Recommendation:** Consider soft delete pattern:
```python
async def delete(self, order: Order) -> None:
    order.status = "cancelled"
    order.deleted_at = datetime.now(timezone.utc)
    await self.session.flush()
```

**Severity:** IMPORTANT - Data integrity concern.

---

### 10. **Missing Rate Limiting Configuration**
**File:** `backend/src/routers/auth.py:17-87`

**Issue:** No rate limiting on authentication endpoint. Vulnerable to brute force attacks.

**Recommendation:** Add rate limiting middleware (e.g., `slowapi`):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/telegram", response_model=AuthResponse)
@limiter.limit("5/minute")  # Max 5 auth attempts per minute
async def authenticate_telegram(...):
    ...
```

**Severity:** IMPORTANT - Security best practice.

---

## Suggestions (Non-blocking)

### 11. **Type Hints Could Use Python 3.13 Features**
**Files:** Various

The code uses older type hint syntax. While not incorrect, Python 3.13 allows newer syntax:

```python
# Current
from typing import Annotated
def foo(x: list[int] | None) -> dict:

# Could use (already in code style guide)
def foo[T](x: list[T] | None) -> dict:  # Generics with PEP 695
```

**Note:** This is optional and not blocking.

---

### 12. **Consider Adding Request ID Tracing**
Add correlation IDs for request tracing:
```python
# middleware
import uuid
from fastapi import Request

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

---

### 13. **Add Comprehensive Logging**
Current code has no logging. Add structured logging:
```python
import logging
logger = logging.getLogger(__name__)

# In services
logger.info("Order created", extra={
    "user_tgid": user_tgid,
    "order_id": order.id,
    "cafe_id": data.cafe_id
})
```

---

## Summary

### Checked:
- [x] Code style (Python 3.13 compliance)
- [x] Security (OWASP Top 10)
- [x] Error handling
- [x] Architecture compliance (Clean Architecture)
- [x] Type hints
- [x] SQLAlchemy best practices
- [x] Pydantic validation
- [x] Authentication & Authorization

### Stats:
- **Files reviewed:** 20+
- **Critical issues:** 4
- **Important issues:** 6
- **Suggestions:** 3

### Recommendation:
**CHANGES REQUESTED** - Fix critical security issues (1-4) and important issues (5-10) before proceeding to testing. Suggestions (11-13) are optional but recommended.

---

## Next Steps for Coder

1. **Priority 1 (CRITICAL):** Fix issues #1-4 immediately
2. **Priority 2 (IMPORTANT):** Fix issues #5-10
3. **Priority 3 (OPTIONAL):** Consider suggestions #11-13
4. **Re-submit for review** once critical and important issues are resolved

---

## Positive Aspects

The code demonstrates many good practices:
- ✅ Clean Architecture with layers (models, repositories, services, routers)
- ✅ Async/await used correctly throughout
- ✅ Type hints on all functions
- ✅ Pydantic models for validation
- ✅ SQLAlchemy 2.0 modern syntax with `Mapped` annotations
- ✅ Dependency injection pattern
- ✅ Separation of concerns
- ✅ Consistent naming conventions
- ✅ Python 3.13 union syntax (`|` instead of `Union`)
- ✅ HTTPException with proper status codes

The foundation is solid. Addressing the security issues will make this production-ready.
