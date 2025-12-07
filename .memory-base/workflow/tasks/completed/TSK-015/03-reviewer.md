---
agent: reviewer
task_id: TSK-015
status: completed
next: tester
created_at: 2025-12-07T12:00:00Z
---

## Review Result: CHANGES REQUESTED

Код в целом соответствует архитектуре и требованиям, но обнаружены критические и важные проблемы, которые необходимо исправить.

---

## Critical Issues

### 1. Migration: Missing `down_revision` link
**File:** `backend/alembic/versions/004_add_menu_item_options_and_standalone_orders.py:14`

**Problem:**
```python
down_revision: Union[str, None] = '003'
```

Миграция ссылается на ревизию `'003'`, но необходимо проверить существование этой ревизии в проекте. Если миграция 003 отсутствует, это приведёт к ошибке при выполнении `alembic upgrade`.

**Action required:**
- Проверить наличие файла `backend/alembic/versions/003_*.py`
- Если отсутствует — исправить `down_revision` на актуальную последнюю ревизию

---

### 2. Service: Incomplete `calculate_standalone_price` method
**File:** `backend/src/services/menu.py:198-200`

**Problem:**
Метод обрывается на строке 200 без реализации логики:
```python
async def calculate_standalone_price(self, items: list[dict]) -> Decimal:
    """Сумма: menu_item.price * quantity для каждого standalone item"""
    total = Decimal("0")
    # КОД ОБРЫВАЕТСЯ - нет loop и return
```

**Expected implementation:**
```python
async def calculate_standalone_price(self, items: list[dict]) -> Decimal:
    """Сумма: menu_item.price * quantity для каждого standalone item"""
    total = Decimal("0")
    for item in items:
        if item.get("type") != "standalone":
            continue
        menu_item = await self.item_repo.get(item["menu_item_id"])
        if menu_item and menu_item.price:
            total += menu_item.price * item.get("quantity", 1)
    return total
```

**Action required:**
- Завершить реализацию метода
- Добавить обработку отсутствующих menu_item
- Добавить валидацию quantity

---

### 3. Service: Incomplete `update_order` method
**File:** `backend/src/services/order.py:150`

**Problem:**
Метод `update_order` обрывается на строке 150 (`# Update extras if changed`) без завершения логики:
- Нет обработки extras update
- Нет обработки notes update
- Нет финального пересчёта total_price
- Нет вызова `self.repo.update(order, **update_data)`

**Expected completion:**
```python
# Update extras if changed
if data.extras is not None:
    extras_dict = [extra.model_dump() for extra in data.extras]
    await self.menu_service.calculate_extras_price(extras_dict)
    update_data["extras"] = extras_dict

# Update notes if changed
if data.notes is not None:
    update_data["notes"] = data.notes

# Recalculate total_price if any of combo_id, items, or extras changed
if data.combo_id is not None or data.items is not None or data.extras is not None:
    combo_id = update_data.get("combo_id") if "combo_id" in update_data else order.combo_id
    items = update_data.get("items", order.items)
    extras = update_data.get("extras", order.extras)

    combo_price = Decimal("0")
    if combo_id:
        combo = await self.menu_service.get_combo(combo_id)
        combo_price = combo.price

    standalone_items = [item for item in items if item.get("type") == "standalone"]
    standalone_price = await self.menu_service.calculate_standalone_price(standalone_items)
    extras_price = await self.menu_service.calculate_extras_price(extras)

    update_data["total_price"] = combo_price + standalone_price + extras_price

return await self.repo.update(order, **update_data)
```

**Action required:**
- Завершить реализацию метода
- Добавить пересчёт total_price
- Добавить return statement

---

## Important Issues

### 4. Missing eager loading for MenuItem.options relationship
**File:** `backend/src/services/menu.py:42-43`

**Problem:**
При получении списка menu_items через `list_menu_items()` связь `options` не загружается заранее (N+1 problem):
```python
async def list_menu_items(self, cafe_id: int, category: str | None = None, available_only: bool = False):
    return await self.item_repo.list_by_cafe(cafe_id, category=category, available_only=available_only)
```

При сериализации `MenuItemResponse` с полем `options: list[MenuItemOptionResponse]` будет выполнен дополнительный запрос для каждого item.

**Recommendation:**
Добавить eager loading в `MenuItemRepository.list_by_cafe()`:
```python
from sqlalchemy.orm import selectinload

query = select(MenuItem).options(selectinload(MenuItem.options)).where(...)
```

**Impact:** Performance degradation при большом количестве блюд в меню

---

### 5. Missing validation: `combo_id = None` but `combo_items` present
**File:** `backend/src/services/order.py:62-69`

**Problem:**
Валидация проверяет что при `combo_id = None` не должно быть `type: "combo"` items, но не проверяет обратное: при `combo_id != None` должен быть хотя бы один `type: "combo"` item.

**Current code:**
```python
else:
    # Standalone order - all items must be standalone
    for item in items_dict:
        if item.get("type") == "combo":
            raise HTTPException(...)
    await self.menu_service.validate_standalone_items(items_dict)
```

**Missing check:**
```python
if data.combo_id:
    combo_items = [item for item in items_dict if item.get("type") == "combo"]
    if not combo_items:
        raise HTTPException(400, "Combo order requires at least one combo item")
```

**Action required:**
- Добавить проверку наличия combo items при combo_id != None

---

### 6. Missing validation: standalone items without `type` field
**File:** `backend/src/services/menu.py:154-156`

**Problem:**
Валидация проверяет `item.get("type") != "standalone"` и пропускает такие items, но не проверяет наличие самого поля `type`.

Items без поля `type` пройдут валидацию незамеченными:
```python
for item in items:
    if item.get("type") != "standalone":
        continue  # Пропускает items без type
```

**Recommendation:**
Добавить explicit проверку:
```python
if "type" not in item:
    raise HTTPException(400, "Item must have 'type' field")
if item["type"] != "standalone":
    continue
```

---

### 7. Inconsistent NULL handling in `calculate_extras_price`
**File:** `backend/src/services/menu.py:96-97`

**Problem:**
Метод проверяет `if item.price:` перед расчётом, но это пропустит items с `price = 0` (хотя extras с нулевой ценой — edge case).

Для консистентности лучше использовать explicit `is not None`:
```python
if item.price is not None:
    total += item.price * extra["quantity"]
```

**Impact:** Low (extras обычно платные)

---

## Code Style Issues

### 8. Missing type hints in repositories
**File:** `backend/src/repositories/order.py:9`

**Problem:**
Whitelist константа не имеет type hint:
```python
ALLOWED_UPDATE_FIELDS = {"combo_id", "items", "combo_items", "extras", "notes", "total_price", "status"}
```

**Recommendation:**
```python
ALLOWED_UPDATE_FIELDS: set[str] = {...}
```

**Same issue in:**
- `backend/src/repositories/menu.py:7-9`

---

### 9. Redundant property in Order model
**File:** `backend/src/models/order.py:35-38`

**Problem:**
Property `combo_items` помечен как deprecated, но не имеет setter, что может вызвать confusion:
```python
@property
def combo_items(self):
    """Deprecated. Use 'items' instead. Kept for backward compatibility."""
    return self.items
```

Попытка установить `order.combo_items = [...]` вызовет `AttributeError`.

**Recommendation:**
Либо добавить setter:
```python
@combo_items.setter
def combo_items(self, value):
    self.items = value
```

Либо явно указать в docstring:
```python
"""Deprecated (read-only). Use 'items' instead."""
```

---

### 10. Inconsistent docstring style
**Files:** `backend/src/services/menu.py`, `backend/src/routers/menu.py`

**Problem:**
Часть методов имеет docstrings на русском, часть — на английском, часть — без docstrings.

**Examples:**
```python
# Русский
async def list_menu_item_options(self, item_id: int):
    """Список опций для блюда"""

# Английский (в коде есть)
async def calculate_extras_price(self, extras: list[dict]) -> Decimal:
    # No docstring

# Смешанный
async def validate_standalone_items(self, items: list[dict]) -> None:
    """
    Валидация standalone items:
    - Проверить что у каждого menu_item есть price
    - Проверить обязательные опции (is_required=True)
    - Проверить корректность значений опций
    """
```

**Recommendation:**
- Выбрать единый язык для docstrings (рекомендую английский)
- Или использовать Google-style docstrings только для сложной логики (как указано в code-style.md)

---

### 11. Frontend: Missing null check for `dish.price`
**File:** `frontend_mini_app/src/components/Menu/MenuSection.tsx`

**Problem:**
Код показывает цену как `{dish.price ? \`${dish.price} ₽\` : "Входит в комбо"}`, но не проверяет `null` vs `0`.

Блюдо с `price = 0` покажет "Входит в комбо", хотя это бесплатное standalone блюдо.

**Recommendation:**
```tsx
{dish.price !== null ? `${dish.price} ₽` : "Входит в комбо"}
```

---

### 12. Frontend: Missing options display in DishModal
**File:** `frontend_mini_app/src/components/Menu/DishModal.tsx:150`

**Problem:**
Файл обрывается на строке 150 внутри рендеринга опций. Не видно:
- Как отображается select для выбора значений опций
- Как обрабатывается изменение selectedOptions
- Как валидируются обязательные опции при добавлении в корзину

**Action required:**
- Проверить полноту реализации UI для опций
- Убедиться что валидация is_required работает корректно

---

## Security & Edge Cases

### 13. SQL injection protection verified ✅
**Files:** All repositories

SQLAlchemy ORM используется корректно с параметризованными запросами:
```python
select(MenuItem).where(MenuItem.id == item_id)  # ✓ Safe
```

---

### 14. Authorization checks verified ✅
**File:** `backend/src/routers/menu.py`

Все CUD операции с опциями требуют `ManagerUser`:
```python
@router.post("/cafes/{cafe_id}/menu/{item_id}/options", ...)
async def create_menu_item_option(..., manager: ManagerUser, ...)
```

---

### 15. Cascade delete protection verified ✅
**Files:** `backend/src/models/cafe.py:82`, migration

Cascade delete настроен на двух уровнях:
- ORM: `cascade="all, delete-orphan"`
- DB: `ondelete="CASCADE"`

---

### 16. Missing edge case: Empty options dict for required option
**File:** `backend/src/services/menu.py:184-188`

**Problem:**
Валидация проверяет `option.name not in selected_options`, но не проверяет пустое значение:
```python
if option.is_required and option.name not in selected_options:
    raise HTTPException(...)
```

Payload `{"options": {"Размер": ""}}` пройдёт валидацию для обязательной опции "Размер".

**Recommendation:**
```python
if option.is_required:
    value = selected_options.get(option.name)
    if not value:  # Проверка и отсутствия и пустоты
        raise HTTPException(...)
```

---

### 17. Missing edge case: Negative quantity validation
**File:** `backend/src/schemas/order.py:28`

**Current validation:**
```python
quantity: int = Field(default=1, gt=0, le=100)
```

Валидация `gt=0` корректна, но нет проверки на уровне сервиса.

**Recommendation:** Add explicit check в `validate_standalone_items`:
```python
quantity = item.get("quantity", 1)
if quantity <= 0:
    raise HTTPException(400, "Quantity must be positive")
```

---

## Architecture Compliance

### ✅ Соответствие архитектурному плану:

| Requirement | Status | Comment |
|-------------|--------|---------|
| Migration создана | ✅ | С индексом и downgrade |
| MenuItemOption модель | ✅ | Все поля соответствуют |
| Order.combo_id nullable | ✅ | Nullable в модели и схемах |
| Order.items вместо combo_items | ✅ | С обратной совместимостью |
| API CRUD для опций | ✅ | 4 эндпоинта с manager auth |
| POST /orders поддержка standalone | ✅ | С валидацией |
| Валидация обязательных опций | ✅ | В validate_standalone_items |
| Расчёт total_price | ⚠️ | **КРИТИЧНО:** метод неполный |
| Frontend типы | ✅ | OrderItem union types |
| Frontend UI опций | ⚠️ | **ПРОВЕРИТЬ:** файл обрывается |

---

## Backward Compatibility

### ✅ Проверено:

1. **model_validator в OrderCreate:**
   - Мигрирует `combo_items` → `items` с добавлением `type: "combo"`
   - Работает в режиме `'before'` (до основной валидации)

2. **Property в Order модели:**
   - `order.combo_items` возвращает `order.items` (read-only)

3. **Whitelist в OrderRepository:**
   - Поддерживает оба поля: `"items"` и `"combo_items"`

4. **Старые заказы:**
   - Миграция не меняет данных, только схему
   - Существующие записи с `combo_id NOT NULL` не затронуты

---

## Performance

### ⚠️ Potential N+1 Problem:

**Location:** `MenuService.list_menu_items()` + `MenuItemResponse.options`

**Impact:** При получении списка из 50 блюд будет выполнено 50 дополнительных запросов для загрузки опций.

**Mitigation:**
```python
# В MenuItemRepository.list_by_cafe()
from sqlalchemy.orm import selectinload

query = select(MenuItem).options(selectinload(MenuItem.options)).where(...)
```

---

## Testing Requirements

Для Tester agent необходимо покрыть:

1. **CRUD MenuItemOption:**
   - Создание опции с is_required=True/False
   - Обновление values списка
   - Удаление опции
   - Каскадное удаление при удалении MenuItem

2. **Валидация standalone items:**
   - MenuItem без price → 400 error
   - MenuItem.is_available=False → 400 error
   - Обязательная опция не выбрана → 400 error
   - Некорректное значение опции → 400 error
   - Пустое значение для обязательной опции → 400 error

3. **Создание заказов:**
   - Только combo (combo_id + combo items)
   - Только standalone (combo_id=null + standalone items)
   - Микс (combo_id + combo items + standalone items)
   - Combo items при combo_id=null → 400 error
   - Combo_id без combo items → 400 error (после исправления)

4. **Расчёт total_price:**
   - Combo only: combo.price + extras
   - Standalone only: sum(item.price * quantity) + extras
   - Микс: combo.price + sum(standalone) + extras

5. **Обратная совместимость:**
   - POST /orders с `combo_items` вместо `items`
   - PATCH /orders с `combo_items`
   - Чтение старых заказов через order.combo_items property

6. **Authorization:**
   - User не может создавать/изменять опции
   - Manager может создавать/изменять опции
   - User может читать опции

---

## Summary

**Critical issues requiring immediate fix:**
1. Неполная реализация `calculate_standalone_price()` в MenuService
2. Неполная реализация `update_order()` в OrderService
3. Проверить ссылку миграции на существующую ревизию 003

**Important issues for improvement:**
1. Добавить eager loading для MenuItem.options (N+1 problem)
2. Добавить валидацию наличия combo items при combo_id != None
3. Проверить полноту реализации DishModal (файл обрывается)
4. Добавить проверку пустых значений для обязательных опций

**Code quality suggestions:**
- Добавить type hints для whitelist констант
- Унифицировать язык docstrings
- Добавить setter для deprecated property или пометить read-only
- Исправить null check для dish.price во frontend

**Security:** ✅ No critical security issues found

**Architecture:** ✅ Соответствует плану с оговорками по неполным методам

