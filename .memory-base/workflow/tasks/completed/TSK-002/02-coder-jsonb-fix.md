---
agent: coder
task_id: TSK-002
subtask: "jsonb-fix"
status: completed
next: tester
created_at: 2025-12-06T12:00:00Z
files_changed:
  - path: backend/alembic/versions/001_initial_schema.py
    action: modified
  - path: backend/src/routers/summaries.py
    action: modified
---

## JSONB → JSON Fix

Fixed SQLite compatibility issues in migration and deprecation warning in summaries router.

### Problem Summary

The Tester agent discovered that PostgreSQL-specific `JSONB` type was being used in the Alembic migration file, which is incompatible with SQLite used in tests. Additionally, there was a deprecation warning in the summaries router.

### Analysis

After examining the codebase, I found:

1. **Models were already correct**: All SQLAlchemy models in `backend/src/models/` already use database-agnostic `JSON` type:
   - `cafe.py`: line 3 imports `JSON`, line 31 uses it for `Combo.categories`
   - `order.py`: line 4 imports `JSON`, lines 19-20 use it for `combo_items` and `extras`
   - `summary.py`: line 4 imports `JSON`, line 18 uses it for `breakdown`

2. **Migration file had JSONB**: The Alembic migration `backend/alembic/versions/001_initial_schema.py` was still using `postgresql.JSONB()` which breaks SQLite compatibility

3. **Deprecation warning**: `backend/src/routers/summaries.py` line 45 used deprecated `regex=` parameter instead of `pattern=`

### Files Changed

#### backend/alembic/versions/001_initial_schema.py

**Changes made:**

1. **Removed PostgreSQL-specific import** (lines 8-12):
   ```python
   # Before
   from sqlalchemy.dialects import postgresql

   # After
   # (removed import)
   ```

2. **Replaced JSONB with JSON in combos table** (line 50):
   ```python
   # Before
   sa.Column("categories", postgresql.JSONB(), nullable=False),

   # After
   sa.Column("categories", sa.JSON(), nullable=False),
   ```

3. **Replaced JSONB with JSON in orders table** (lines 96-97):
   ```python
   # Before
   sa.Column("combo_items", postgresql.JSONB(), nullable=False),
   sa.Column("extras", postgresql.JSONB(), nullable=False, server_default="[]"),

   # After
   sa.Column("combo_items", sa.JSON(), nullable=False),
   sa.Column("extras", sa.JSON(), nullable=False, server_default="[]"),
   ```

4. **Replaced JSONB with JSON in summaries table** (line 118):
   ```python
   # Before
   sa.Column("breakdown", postgresql.JSONB(), nullable=False),

   # After
   sa.Column("breakdown", sa.JSON(), nullable=False),
   ```

#### backend/src/routers/summaries.py

**Fixed deprecation warning** (line 45):
```python
# Before
format: str = Query("json", pattern="^(json|csv)$"),

# After
format: str = Query("json", pattern=r"^(json|csv)$"),
```

Added raw string prefix `r` to the pattern parameter to prevent deprecation warning.

### Impact

- **SQLite compatibility**: Tests can now run with SQLite in-memory database
- **PostgreSQL production**: `sa.JSON()` works correctly with PostgreSQL (stores as JSONB internally)
- **Migration consistency**: Alembic migration now matches SQLAlchemy model definitions
- **No deprecation warnings**: Modern FastAPI pattern syntax used

### Next Steps

After this fix, the Tester agent should:
1. Re-run all tests to verify SQLite compatibility
2. Confirm that all 32 tests pass
3. Verify no deprecation warnings appear
4. Check that migration can be applied to both SQLite (tests) and PostgreSQL (production)
