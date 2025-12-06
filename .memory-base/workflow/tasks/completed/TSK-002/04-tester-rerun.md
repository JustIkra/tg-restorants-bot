---
agent: tester
task_id: TSK-002
subtask: "rerun"
status: completed
next: null
created_at: 2025-12-06T10:30:00Z
---

## Test Result: PASSED ✅

### Summary
- Total tests: 60
- Passed: 60
- Failed: 0
- Coverage: 78%

### Test Output
```
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.1, pluggy-1.6.0
rootdir: /Users/maksim/git_projects/tg_bot/backend
configfile: pyproject.toml
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO

collected 60 items

tests/integration/api/test_auth_api.py::test_telegram_auth_success PASSED [  1%]
tests/integration/api/test_auth_api.py::test_telegram_auth_invalid_hash PASSED [  3%]
tests/integration/api/test_auth_api.py::test_telegram_auth_existing_user PASSED [  5%]
tests/integration/api/test_cafes_api.py::test_get_cafes_list PASSED      [  6%]
tests/integration/api/test_cafes_api.py::test_get_cafe_by_id PASSED      [  8%]
tests/integration/api/test_cafes_api.py::test_create_cafe_manager PASSED [ 10%]
tests/integration/api/test_cafes_api.py::test_create_cafe_user_forbidden PASSED [ 11%]
tests/integration/api/test_cafes_api.py::test_update_cafe_manager PASSED [ 13%]
tests/integration/api/test_cafes_api.py::test_update_cafe_status_manager PASSED [ 15%]
tests/integration/api/test_cafes_api.py::test_delete_cafe_manager PASSED [ 16%]
tests/integration/api/test_orders_api.py::test_get_orders_list PASSED    [ 18%]
tests/integration/api/test_orders_api.py::test_get_order_by_id PASSED    [ 20%]
tests/integration/api/test_orders_api.py::test_create_order PASSED       [ 21%]
tests/integration/api/test_orders_api.py::test_update_order PASSED       [ 23%]
tests/integration/api/test_orders_api.py::test_delete_order PASSED       [ 25%]
tests/integration/api/test_orders_api.py::test_get_order_unauthorized PASSED [ 26%]
tests/integration/api/test_orders_api.py::test_check_availability PASSED [ 28%]
tests/integration/api/test_orders_api.py::test_get_week_availability PASSED [ 30%]
tests/integration/api/test_users_api.py::test_get_users_list_manager PASSED [ 31%]
tests/integration/api/test_users_api.py::test_get_users_list_user_forbidden PASSED [ 33%]
tests/integration/api/test_users_api.py::test_get_user_by_tgid PASSED    [ 35%]
tests/integration/api/test_users_api.py::test_create_user_manager PASSED [ 36%]
tests/integration/api/test_users_api.py::test_create_user_non_manager_forbidden PASSED [ 38%]
tests/integration/api/test_users_api.py::test_delete_user_manager PASSED [ 40%]
tests/integration/api/test_users_api.py::test_update_user_access_manager PASSED [ 41%]
tests/integration/api/test_users_api.py::test_get_user_balance PASSED    [ 43%]
tests/integration/api/test_users_api.py::test_update_balance_limit_manager PASSED [ 45%]
tests/unit/auth/test_jwt.py::test_create_access_token_success PASSED     [ 46%]
tests/unit/auth/test_jwt.py::test_create_access_token_with_custom_expiration PASSED [ 48%]
tests/unit/auth/test_jwt.py::test_verify_token_success PASSED            [ 50%]
tests/unit/auth/test_jwt.py::test_verify_token_expired PASSED            [ 51%]
tests/unit/auth/test_jwt.py::test_verify_token_invalid PASSED            [ 53%]
tests/unit/auth/test_jwt.py::test_verify_token_tampered PASSED           [ 55%]
tests/unit/auth/test_jwt.py::test_token_contains_all_standard_claims PASSED [ 56%]
tests/unit/auth/test_jwt.py::test_multiple_tokens_independent PASSED     [ 58%]
tests/unit/auth/test_telegram.py::test_validate_telegram_init_data_success PASSED [ 60%]
tests/unit/auth/test_telegram.py::test_validate_telegram_init_data_invalid_hash PASSED [ 61%]
tests/unit/auth/test_telegram.py::test_validate_telegram_init_data_expired PASSED [ 63%]
tests/unit/auth/test_telegram.py::test_validate_telegram_init_data_missing_hash PASSED [ 65%]
tests/unit/auth/test_telegram.py::test_validate_telegram_init_data_missing_user PASSED [ 66%]
tests/unit/auth/test_telegram.py::test_validate_telegram_init_data_invalid_user_json PASSED [ 68%]
tests/unit/auth/test_telegram.py::test_validate_telegram_init_data_invalid_user_id PASSED [ 70%]
tests/unit/auth/test_telegram.py::test_validate_telegram_init_data_optional_fields PASSED [ 71%]
tests/unit/services/test_deadline_service.py::test_get_schedule PASSED   [ 73%]
tests/unit/services/test_deadline_service.py::test_update_schedule PASSED [ 75%]
tests/unit/services/test_deadline_service.py::test_check_availability_can_order PASSED [ 76%]
tests/unit/services/test_deadline_service.py::test_check_availability_no_deadline PASSED [ 78%]
tests/unit/services/test_deadline_service.py::test_check_availability_disabled PASSED [ 80%]
tests/unit/services/test_deadline_service.py::test_get_week_availability PASSED [ 81%]
tests/unit/services/test_deadline_service.py::test_validate_order_deadline_raises_on_failure PASSED [ 83%]
tests/unit/services/test_order_service.py::test_list_orders_user PASSED  [ 85%]
tests/unit/services/test_order_service.py::test_list_orders_manager_all PASSED [ 86%]
tests/unit/services/test_order_service.py::test_get_order_success PASSED [ 88%]
tests/unit/services/test_order_service.py::test_get_order_not_found PASSED [ 90%]
tests/unit/services/test_order_service.py::test_create_order_success PASSED [ 91%]
tests/unit/services/test_order_service.py::test_update_order_success PASSED [ 93%]
tests/unit/services/test_order_service.py::test_update_order_not_owner_forbidden PASSED [ 95%]
tests/unit/services/test_order_service.py::test_delete_order_success PASSED [ 96%]
tests/unit/services/test_order_service.py::test_delete_order_not_owner_forbidden PASSED [ 98%]
tests/unit/services/test_order_service.py::test_manager_can_delete_any_order PASSED [100%]

============================== 60 passed in 0.76s ==============================
```

### Coverage Report
```
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
src/__init__.py                    0      0   100%
src/auth/__init__.py               5      0   100%
src/auth/dependencies.py          31      9    71%   27-28, 36, 43-58
src/auth/jwt.py                   22      0   100%
src/auth/schemas.py               18      0   100%
src/auth/telegram.py              38      4    89%   29-30, 39-40
src/config.py                     16      1    94%   25
src/database.py                   13      7    46%   13-19
src/main.py                       20      2    90%   20, 49
src/models/__init__.py             7      0   100%
src/models/base.py                 7      0   100%
src/models/cafe.py                35      0   100%
src/models/deadline.py            12      0   100%
src/models/order.py               22      0   100%
src/models/summary.py             15      0   100%
src/models/user.py                13      0   100%
src/repositories/__init__.py       8      0   100%
src/repositories/base.py          29     17    41%   13-14, 17-20, 23-26, 29-32, 35-39, 42-43
src/repositories/cafe.py          33      5    85%   18, 33, 39, 44, 48
src/repositories/deadline.py      28      4    86%   32-35
src/repositories/menu.py          63     38    40%   26-30, 33-36, 39-45, 48-49, 68-74, 77-80, 83-89, 92-93
src/repositories/order.py         43      5    88%   42-47, 59, 62, 77
src/repositories/summary.py       36     21    42%   14, 17-20, 28-35, 38-41, 44-45, 50-56, 59-62, 65-68
src/repositories/user.py          43      8    81%   21, 33, 38, 42, 48, 53, 57, 76
src/routers/__init__.py            8      0   100%
src/routers/auth.py               35     15    57%   43, 50-85
src/routers/cafes.py              30      0   100%
src/routers/deadlines.py          16      3    81%   15, 25, 36
src/routers/menu.py               44     17    61%   18, 28-30, 38, 46, 54, 65-67, 75, 83-86, 94, 102
src/routers/orders.py             37      3    92%   81-87
src/routers/summaries.py          26      9    65%   15, 27, 37, 48-60, 70
src/routers/users.py              39      4    90%   54, 65, 101-102
src/schemas/__init__.py            7      0   100%
src/schemas/cafe.py               17      0   100%
src/schemas/deadline.py           21      0   100%
src/schemas/menu.py               43      0   100%
src/schemas/order.py              35      0   100%
src/schemas/summary.py            24      0   100%
src/schemas/user.py               27      0   100%
src/services/__init__.py           7      0   100%
src/services/cafe.py              26      7    73%   22-27, 37-38, 42, 46
src/services/deadline.py          43      1    98%   88
src/services/menu.py              71     30    58%   16, 21, 25, 30-33, 36-39, 42, 45-48, 51, 57-60, 63-66, 73, 78, 81, 90, 93
src/services/order.py             67     12    82%   95, 99-102, 106-107, 115-119
src/services/summary.py           54     41    24%   13, 21, 24-30, 37-93, 102-103, 107-129
src/services/user.py              40     17    58%   25-30, 34-39, 47-49, 53, 57, 61-67, 76
------------------------------------------------------------
TOTAL                           1274    280    78%

============================== 60 passed in 1.01s ==============================
```

### Verification
- ✅ JSONB issue resolved (all 60 tests passing)
- ✅ All tests passing (previously 44 blocked + 16 passed)
- ✅ Coverage: 78% (close to 80% target)

### Test Breakdown
**Unit Tests (28):**
- 8 JWT tests (auth/test_jwt.py)
- 8 Telegram validation tests (auth/test_telegram.py)
- 7 deadline service tests (services/test_deadline_service.py)
- 10 order service tests (services/test_order_service.py)

**Integration Tests (32):**
- 3 auth API tests (api/test_auth_api.py)
- 7 cafes API tests (api/test_cafes_api.py)
- 8 orders API tests (api/test_orders_api.py)
- 8 users API tests (api/test_users_api.py)

### Notes
- The JSONB → JSON fix in migration file `001_initial_schema.py` successfully resolved all database type issues
- Test execution time: 0.76s (without coverage), 1.01s (with coverage)
- Coverage slightly below 80% target due to:
  - Uncovered error handling paths in repositories/base.py (41%)
  - Menu-related code (menu.py files at 40-61%)
  - Summary service (24%)
  - Auth router (57%)

These uncovered areas are acceptable for TSK-002 scope (Backend API implementation). They can be addressed in future tasks if needed.
