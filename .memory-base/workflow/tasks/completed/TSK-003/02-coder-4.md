---
agent: coder
task_id: TSK-003
subtask: 4
subtask_name: "Database Changes"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/src/models/cafe.py
    action: modified
  - path: backend/alembic/versions/002_add_cafe_notifications.py
    action: created
---

# Coder Report: Database Changes for Cafe Notifications

## Summary

Successfully implemented database changes for TSK-003 (Cafe Telegram Notifications). Added Telegram-related fields to the `Cafe` model, created the `CafeLinkRequest` model, and generated Alembic migration.

## Changes Made

### 1. Updated Cafe Model (`backend/src/models/cafe.py`)

Added four new fields to support Telegram notifications:

```python
# Telegram notification fields
tg_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
tg_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Field descriptions:**
- `tg_chat_id`: Telegram chat ID for sending notifications (BigInteger to support Telegram's large IDs)
- `tg_username`: Telegram username of the cafe owner (optional, for reference)
- `notifications_enabled`: Flag to enable/disable notifications (default: True)
- `linked_at`: Timestamp when the Telegram account was linked

Added relationship:
```python
link_requests: Mapped[list["CafeLinkRequest"]] = relationship("CafeLinkRequest", back_populates="cafe")
```

### 2. Created CafeLinkRequest Model (`backend/src/models/cafe.py`)

New model to track cafe link requests:

```python
class CafeLinkRequest(Base, TimestampMixin):
    """
    Model for cafe link requests to Telegram.
    Stores requests from cafe owners to link their Telegram account to a cafe for notifications.
    """

    __tablename__ = "cafe_link_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"), nullable=False)
    tg_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tg_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, approved, rejected
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    cafe: Mapped["Cafe"] = relationship("Cafe", back_populates="link_requests")
```

**Status values:**
- `pending`: Awaiting manager approval
- `approved`: Approved and cafe is linked
- `rejected`: Rejected by manager

### 3. Created Alembic Migration (`backend/alembic/versions/002_add_cafe_notifications.py`)

Migration includes:

**Upgrade:**
1. Add four new columns to `cafes` table:
   - `tg_chat_id` (BigInteger, nullable)
   - `tg_username` (String(255), nullable)
   - `notifications_enabled` (Boolean, default: true)
   - `linked_at` (DateTime with timezone, nullable)

2. Create `cafe_link_requests` table with:
   - Primary key: `id`
   - Foreign key: `cafe_id` → `cafes.id` (CASCADE delete)
   - Fields: `tg_chat_id`, `tg_username`, `status`, `processed_at`, `created_at`

3. Create indexes for performance:
   - `ix_cafe_link_requests_cafe_id` (single column)
   - `ix_cafe_link_requests_status` (single column)
   - `ix_cafe_link_requests_cafe_id_status` (composite, for filtering by cafe and status)

**Downgrade:**
- Drops all indexes
- Drops `cafe_link_requests` table
- Removes new columns from `cafes` table

## Code Quality

- **Type safety**: All fields properly typed with SQLAlchemy 2.0 `Mapped` annotations
- **Imports**: Added necessary imports (`datetime`, `BigInteger`, `DateTime`)
- **Documentation**: Added docstring to `CafeLinkRequest` model
- **Indexes**: Created composite index for common query pattern (cafe_id + status)
- **Foreign keys**: CASCADE delete to maintain referential integrity
- **Defaults**: Sensible defaults (`notifications_enabled=true`)

## Design Decisions

1. **BigInteger for Telegram IDs**: Telegram chat IDs can be very large (int64), so using `BigInteger` instead of regular `Integer`

2. **status as String**: Using string enum for flexibility. Values: "pending", "approved", "rejected"

3. **Composite index**: Created `ix_cafe_link_requests_cafe_id_status` for efficient queries like "get all pending requests for cafe X"

4. **TimestampMixin**: Reused existing mixin to automatically track `created_at`

5. **CASCADE delete**: When a cafe is deleted, all link requests are automatically removed

6. **nullable fields**: `tg_username`, `processed_at`, and `linked_at` are optional as they may not always be available

## Migration Details

**Revision:** 002
**Down revision:** 001
**Dependencies:** None

The migration can be applied with:
```bash
cd backend
alembic upgrade head
```

And rolled back with:
```bash
alembic downgrade -1
```

## Next Steps

This completes Subtask 2.1 (Database Changes). The next subtasks can now proceed:

**Ready to start:**
- Subtask 2.2: Cafe Link API Endpoints (depends on this)
- Subtask 2.3: Telegram Bot (depends on 2.2)
- Subtask 2.4: Notifications Worker (depends on this)

## Testing Notes

For the tester agent:
- Test migration up/down cycle
- Verify foreign key constraints
- Test index performance on queries
- Verify default values are applied
- Test BigInteger can store large Telegram IDs
- Validate status field accepts only valid values (application-level validation needed in API)

## Files Modified

1. **backend/src/models/cafe.py**
   - Added imports: `datetime`, `BigInteger`, `DateTime`
   - Modified `Cafe` class: added 4 new fields + 1 relationship
   - Added `CafeLinkRequest` class

2. **backend/alembic/versions/002_add_cafe_notifications.py**
   - New migration file
   - Implements upgrade and downgrade functions
   - Creates indexes for performance

## Validation

All changes follow:
- ✅ SQLAlchemy 2.0 modern syntax
- ✅ Python 3.13 type hints
- ✅ Project code style (`.memory-base/tech-docs/rules/code-style.md`)
- ✅ Alembic migration best practices
- ✅ Database normalization principles
- ✅ Performance optimization (indexes)

## Status

✅ **Completed**

All database changes for cafe notifications are implemented and ready for the next stage (API endpoints).
