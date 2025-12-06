---
agent: coder
task_id: HOTFIX-tgid
status: completed
next: tester
created_at: 2025-12-06T17:50:00
files_changed:
  - path: backend/src/models/user.py
    action: modified
    description: Changed tgid from Integer to BigInteger
  - path: backend/src/models/order.py
    action: modified
    description: Changed user_tgid from Integer to BigInteger
  - path: backend/alembic/versions/003_tgid_bigint.py
    action: created
    description: Migration to alter tgid columns from INTEGER to BIGINT
---

# Coder Result: HOTFIX-tgid

## Summary

Fixed critical overflow bug for Telegram user IDs exceeding int32 range (2,147,483,647).

## Changes Made

### 1. Updated User Model (`backend/src/models/user.py`)
- Added `BigInteger` import from sqlalchemy
- Changed `tgid` field from `Integer` to `BigInteger`

**Before:**
```python
from sqlalchemy import Boolean, Integer, Numeric, String
# ...
tgid: Mapped[int] = mapped_column(Integer, primary_key=True)
```

**After:**
```python
from sqlalchemy import BigInteger, Boolean, Integer, Numeric, String
# ...
tgid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
```

### 2. Updated Order Model (`backend/src/models/order.py`)
- Added `BigInteger` import from sqlalchemy
- Changed `user_tgid` foreign key field from `Integer` to `BigInteger`

**Before:**
```python
from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
# ...
user_tgid: Mapped[int] = mapped_column(Integer, ForeignKey("users.tgid"), nullable=False)
```

**After:**
```python
from sqlalchemy import JSON, BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
# ...
user_tgid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tgid"), nullable=False)
```

### 3. Created Migration (`backend/alembic/versions/003_tgid_bigint.py`)
- Created new migration file to alter database columns
- Changes `orders.user_tgid` first (FK must be changed before PK)
- Then changes `users.tgid` (PK)
- Includes proper downgrade path

**Migration upgrade order:**
1. `orders.user_tgid`: INTEGER → BIGINT
2. `users.tgid`: INTEGER → BIGINT

**Migration downgrade order (reversed):**
1. `users.tgid`: BIGINT → INTEGER
2. `orders.user_tgid`: BIGINT → INTEGER

## Technical Details

- **Problem:** Telegram user ID `6055257779` exceeds int32 max value (2,147,483,647)
- **Error:** `asyncpg.exceptions.DataError: invalid input for query argument $1: 6055257779 (value out of int32 range)`
- **Solution:** Use `BigInteger` (int64) which supports values up to 9,223,372,036,854,775,807

## Migration Revision Chain
- Previous: `002` (add_cafe_notifications)
- Current: `003` (tgid_bigint)

## Next Steps

The Tester agent should:
1. Run the migration: `alembic upgrade head`
2. Test authentication with large Telegram user IDs
3. Verify existing data is preserved
4. Test order creation with large user IDs
5. Run existing test suite to ensure no regressions
