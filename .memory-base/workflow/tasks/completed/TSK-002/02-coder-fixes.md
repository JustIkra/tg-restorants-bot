---
agent: coder
task_id: TSK-002
subtask: "fixes"
status: completed
next: reviewer
created_at: 2025-12-06T05:00:00Z
files_changed:
  - path: backend/src/config.py
    action: modified
  - path: backend/src/auth/telegram.py
    action: modified
  - path: backend/src/auth/jwt.py
    action: modified
  - path: backend/src/repositories/order.py
    action: modified
  - path: backend/src/repositories/user.py
    action: modified
  - path: backend/src/repositories/cafe.py
    action: modified
  - path: backend/src/repositories/menu.py
    action: modified
  - path: backend/src/services/deadline.py
    action: modified
  - path: backend/src/schemas/order.py
    action: modified
  - path: backend/src/routers/orders.py
    action: modified
  - path: backend/src/routers/users.py
    action: modified
  - path: backend/src/routers/menu.py
    action: modified
---

## Code Review Fixes

Fixed all critical (1-4) and important (5-8) security and quality issues identified in code review (03-reviewer.md).

### Critical Issues Fixed

#### 1. SQL Injection Protection - ALLOWED_FIELDS in Repositories

Added whitelist validation for all repository update methods to prevent arbitrary attribute modification via `setattr()`.

**Files modified:**
- `backend/src/repositories/order.py`: Added `ALLOWED_UPDATE_FIELDS = {"combo_id", "combo_items", "extras", "notes", "total_price", "status"}`
- `backend/src/repositories/user.py`: Added `ALLOWED_UPDATE_FIELDS = {"name", "office", "role", "is_active", "weekly_limit"}`
- `backend/src/repositories/cafe.py`: Added `ALLOWED_UPDATE_FIELDS = {"name", "description", "is_active"}`
- `backend/src/repositories/menu.py`: Added `ALLOWED_COMBO_UPDATE_FIELDS` and `ALLOWED_MENU_ITEM_UPDATE_FIELDS`

All `update()` methods now validate field names before calling `setattr()`:
```python
for key, value in kwargs.items():
    if key not in ALLOWED_UPDATE_FIELDS:
        raise ValueError(f"Field '{key}' cannot be updated")
    if value is not None:
        setattr(entity, key, value)
```

#### 2. Removed Hardcoded Secrets from Config

**File:** `backend/src/config.py`

- Removed default values for `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, and `JWT_SECRET_KEY`
- Added `model_validator` to enforce minimum 32-character length for `JWT_SECRET_KEY`
- All sensitive values now MUST be provided via environment variables

#### 3. Telegram Auth - auth_date and user ID Validation

**File:** `backend/src/auth/telegram.py`

Added two critical security checks:
1. **auth_date expiration**: Rejects authentication data older than 24 hours (prevents replay attacks)
2. **user ID validation**: Ensures user ID is a positive integer

```python
# Validate auth_date expiration
auth_date = int(parsed.get("auth_date", "0"))
current_time = int(time.time())
if current_time - auth_date > 86400:  # 24 hours
    raise TelegramAuthError("Authentication data expired")

# Validate user ID
user_id = user_data.get("id")
if not isinstance(user_id, int) or user_id <= 0:
    raise TelegramAuthError("Invalid user ID")
```

#### 4. JWT Standard Claims

**File:** `backend/src/auth/jwt.py`

Added standard JWT claims to prevent token substitution attacks:
- `sub` (subject): Telegram user ID
- `aud` (audience): "lunch-bot-api"
- `iss` (issuer): "lunch-bot-backend"
- `iat` (issued at): Token creation timestamp

Both `create_access_token()` and `verify_token()` now enforce these claims.

### Important Issues Fixed

#### 5. HTTPException Imports - Moved to Module Level

**Files:**
- `backend/src/routers/orders.py`
- `backend/src/routers/users.py`
- `backend/src/routers/menu.py`

Removed inline imports of `HTTPException` and `status` from function bodies. All imports now at module level for better code quality and maintainability.

#### 6. Timezone Awareness in Deadline Service

**File:** `backend/src/services/deadline.py`

Changed `datetime.now()` to `datetime.now(timezone.utc)` to ensure correct deadline comparisons across timezones. This prevents incorrect availability checks when server timezone differs from user timezone.

#### 7-8. Pydantic Field Validators

**File:** `backend/src/schemas/order.py`

Added comprehensive validation to input schemas:

```python
class ComboItemInput(BaseModel):
    category: str = Field(..., pattern="^(soup|salad|main)$")
    menu_item_id: int = Field(..., gt=0)

class ExtraInput(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)
```

This ensures:
- Category can only be "soup", "salad", or "main"
- Menu item IDs must be positive integers
- Quantity must be between 1 and 100

## Impact

All critical security vulnerabilities have been addressed:
- SQL injection risk eliminated via field whitelisting
- No hardcoded secrets in production code
- Telegram auth protected against replay attacks and invalid user IDs
- JWT tokens secured with standard claims

Code quality improvements:
- Consistent import organization
- Timezone-aware datetime handling
- Strong input validation at API boundary

## Next Steps

Re-submit for code review to verify all issues are resolved.
