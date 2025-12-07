---
agent: coder
task_id: TSK-015
subtask: 2
subtask_name: "Pydantic Schemas"
status: completed
next: null
created_at: 2025-12-07T12:00:00Z
files_changed:
  - path: backend/src/schemas/menu.py
    action: modified
  - path: backend/src/schemas/order.py
    action: modified
---

## Реализация

Реализованы подзадачи 4-5 из плана Architect:
1. Созданы Pydantic схемы для `MenuItemOption` (base, create, update, response)
2. Обновлена `MenuItemResponse` для включения списка опций
3. Созданы типы для order items с discriminated union (`ComboItem`, `StandaloneItem`)
4. Обновлены схемы `OrderCreate`, `OrderUpdate`, `OrderResponse` для поддержки items
5. Добавлена обратная совместимость через model_validator для миграции `combo_items` → `items`

### Изменения

#### `backend/src/schemas/menu.py`

**1. Добавлен импорт Field:**
```python
from pydantic import BaseModel, Field
```

**2. Обновлена `MenuItemResponse`:**
Добавлено поле `options` для включения списка опций блюда:
```python
class MenuItemResponse(BaseModel):
    # ... existing fields ...
    options: list["MenuItemOptionResponse"] = []
```

- Использована forward reference `"MenuItemOptionResponse"` (т.к. класс определён ниже)
- Default значение `[]` — пустой список, если у блюда нет опций
- При сериализации SQLAlchemy модели автоматически загрузятся через relationship

**3. Созданы схемы для MenuItemOption:**

**MenuItemOptionBase:**
```python
class MenuItemOptionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    values: list[str] = Field(..., min_length=1)
    is_required: bool = False
```

- `name` — название опции (например "Размер порции"), валидация длины 1-100 символов
- `values` — список возможных значений (например ["Стандарт", "Большая"]), минимум 1 значение
- `is_required` — обязательна ли опция, по умолчанию False

**MenuItemOptionCreate:**
```python
class MenuItemOptionCreate(MenuItemOptionBase):
    pass
```

- Наследует все поля от Base
- Используется при создании опции через POST эндпоинт

**MenuItemOptionUpdate:**
```python
class MenuItemOptionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    values: list[str] | None = Field(None, min_length=1)
    is_required: bool | None = None
```

- Все поля опциональные (partial update)
- Сохранена валидация для полей, которые передаются
- Используется при обновлении опции через PATCH эндпоинт

**MenuItemOptionResponse:**
```python
class MenuItemOptionResponse(MenuItemOptionBase):
    id: int
    menu_item_id: int

    model_config = {"from_attributes": True}
```

- Наследует поля от Base + добавляет id и menu_item_id
- `from_attributes=True` для совместимости с SQLAlchemy моделью
- Используется при возврате данных из API

#### `backend/src/schemas/order.py`

**1. Добавлены импорты:**
```python
from typing import Literal
from pydantic import BaseModel, Field, model_validator
```

- `Literal` для discriminated union (type: "combo" | "standalone")
- `model_validator` для валидатора обратной совместимости

**2. Созданы типы для order items:**

**ComboItem:**
```python
class ComboItem(BaseModel):
    type: Literal["combo"] = "combo"
    category: str = Field(..., pattern="^(soup|salad|main)$")
    menu_item_id: int = Field(..., gt=0)
```

- `type: Literal["combo"]` — дискриминатор, всегда "combo"
- `category` — категория блюда в комбо (soup, salad, main)
- `menu_item_id` — ID блюда из меню

**StandaloneItem:**
```python
class StandaloneItem(BaseModel):
    type: Literal["standalone"] = "standalone"
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)
    options: dict[str, str] = {}
```

- `type: Literal["standalone"]` — дискриминатор, всегда "standalone"
- `menu_item_id` — ID блюда из меню
- `quantity` — количество, по умолчанию 1, максимум 100
- `options` — выбранные опции в формате `{option_name: selected_value}`, по умолчанию пустой dict

**OrderItem (Union):**
```python
OrderItem = ComboItem | StandaloneItem
```

- Discriminated union для автоматического выбора типа по полю `type`
- Pydantic автоматически определит тип при валидации

**3. Обновлена `OrderCreate`:**

```python
class OrderCreate(BaseModel):
    cafe_id: int
    order_date: date
    combo_id: int | None = None  # ИЗМЕНЕНИЕ: теперь optional
    items: list[OrderItem]       # ИЗМЕНЕНИЕ: вместо combo_items
    extras: list[ExtraInput] = []
    notes: str | None = None

    @model_validator(mode='before')
    @classmethod
    def migrate_combo_items(cls, data):
        """Migrate old combo_items field to items for backward compatibility."""
        if isinstance(data, dict) and 'combo_items' in data and 'items' not in data:
            # Convert combo_items to items with type="combo"
            data['items'] = [
                {'type': 'combo', **item} for item in data['combo_items']
            ]
        return data
```

**Изменения:**
- `combo_id: int | None = None` — теперь опциональный (для standalone заказов)
- `items: list[OrderItem]` — вместо `combo_items: list[ComboItemInput]`
- Валидатор `migrate_combo_items` для обратной совместимости:
  - Запускается в режиме `'before'` (до основной валидации)
  - Проверяет наличие старого поля `combo_items`
  - Конвертирует его в `items` с добавлением `type: "combo"`
  - Позволяет старому коду продолжать работать

**4. Обновлена `OrderUpdate`:**

```python
class OrderUpdate(BaseModel):
    combo_id: int | None = None
    items: list[OrderItem] | None = None  # ИЗМЕНЕНИЕ: вместо combo_items
    extras: list[ExtraInput] | None = None
    notes: str | None = None

    @model_validator(mode='before')
    @classmethod
    def migrate_combo_items(cls, data):
        """Migrate old combo_items field to items for backward compatibility."""
        if isinstance(data, dict) and 'combo_items' in data and 'items' not in data:
            # Convert combo_items to items with type="combo"
            data['items'] = [
                {'type': 'combo', **item} for item in data['combo_items']
            ]
        return data
```

- Аналогично `OrderCreate`, но все поля опциональные (partial update)
- Тот же валидатор для обратной совместимости

**5. Обновлена `OrderResponse`:**

```python
class OrderResponse(BaseModel):
    id: int
    user_tgid: int
    cafe_id: int
    order_date: date
    status: str
    combo_id: int | None  # ИЗМЕНЕНИЕ: nullable
    items: list[dict]     # ИЗМЕНЕНИЕ: вместо combo_items
    extras: list[dict]
    notes: str | None
    total_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

**Изменения:**
- `combo_id: int | None` — теперь может быть None
- `items: list[dict]` — вместо `combo_items: list[dict]`
- Тип `list[dict]` сохранён (JSON поле из БД)

### Особенности реализации

#### 1. Discriminated Union для OrderItem

Использован discriminated union (по полю `type`):
```python
OrderItem = ComboItem | StandaloneItem
```

**Преимущества:**
- Pydantic автоматически выбирает правильный класс по полю `type`
- Валидация полей зависит от типа (combo требует category, standalone требует quantity)
- Type-safe в IDE (автодополнение работает корректно)

**Пример валидации:**
```python
# Combo item
{"type": "combo", "category": "soup", "menu_item_id": 10}  # ✓ Valid

# Standalone item
{"type": "standalone", "menu_item_id": 25, "quantity": 2, "options": {...}}  # ✓ Valid

# Invalid (missing required field)
{"type": "combo", "menu_item_id": 10}  # ✗ Missing 'category'
{"type": "standalone", "menu_item_id": 25}  # ✓ Valid (quantity defaults to 1)
```

#### 2. Обратная совместимость через model_validator

Валидатор `migrate_combo_items` обеспечивает плавную миграцию:

**Старый формат (всё ещё работает):**
```json
{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": 2,
  "combo_items": [
    {"category": "soup", "menu_item_id": 10},
    {"category": "salad", "menu_item_id": 5}
  ]
}
```

**Конвертируется в:**
```json
{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": 2,
  "items": [
    {"type": "combo", "category": "soup", "menu_item_id": 10},
    {"type": "combo", "category": "salad", "menu_item_id": 5}
  ]
}
```

**Новый формат (рекомендуемый):**
```json
{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": null,
  "items": [
    {
      "type": "standalone",
      "menu_item_id": 25,
      "quantity": 2,
      "options": {"Размер порции": "Большая"}
    }
  ]
}
```

#### 3. Валидация полей

**MenuItemOption:**
- `name`: минимум 1 символ, максимум 100
- `values`: минимум 1 значение в списке
- `is_required`: булево значение

**StandaloneItem:**
- `menu_item_id`: больше 0
- `quantity`: от 1 до 100
- `options`: словарь (ключ и значение — строки)

**ComboItem:**
- `category`: только "soup", "salad" или "main" (regex pattern)
- `menu_item_id`: больше 0

### Совместимость с моделями

**Соответствие MenuItemOption модели:**
```python
# Model (SQLAlchemy)
class MenuItemOption(Base):
    id: Mapped[int]
    menu_item_id: Mapped[int]
    name: Mapped[str]  # String(100)
    values: Mapped[list[str]]  # JSON
    is_required: Mapped[bool]  # Boolean, default=False

# Schema (Pydantic)
class MenuItemOptionResponse(BaseModel):
    id: int
    menu_item_id: int
    name: str
    values: list[str]
    is_required: bool

    model_config = {"from_attributes": True}  # ✓ Полная совместимость
```

**Соответствие Order.items:**
```python
# Model (SQLAlchemy)
class Order(Base):
    items: Mapped[list] = mapped_column("combo_items", JSON, nullable=False)

# Schema (Pydantic)
class OrderResponse(BaseModel):
    items: list[dict]  # ✓ JSON из БД конвертируется в list[dict]
```

### Примеры использования

#### 1. Создание опции для блюда

**Request:**
```json
POST /cafes/1/menu/10/options
{
  "name": "Размер порции",
  "values": ["Стандарт", "Большая", "XL"],
  "is_required": true
}
```

**Response:**
```json
{
  "id": 1,
  "menu_item_id": 10,
  "name": "Размер порции",
  "values": ["Стандарт", "Большая", "XL"],
  "is_required": true
}
```

#### 2. Получение блюда с опциями

**Request:**
```
GET /cafes/1/menu
```

**Response:**
```json
[
  {
    "id": 10,
    "cafe_id": 1,
    "name": "Борщ",
    "category": "soup",
    "price": 150.00,
    "is_available": true,
    "options": [
      {
        "id": 1,
        "menu_item_id": 10,
        "name": "Размер порции",
        "values": ["Стандарт", "Большая", "XL"],
        "is_required": true
      },
      {
        "id": 2,
        "menu_item_id": 10,
        "name": "Острота",
        "values": ["Без остроты", "Слабая", "Средняя"],
        "is_required": false
      }
    ]
  }
]
```

#### 3. Создание standalone заказа

**Request:**
```json
POST /orders
{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": null,
  "items": [
    {
      "type": "standalone",
      "menu_item_id": 10,
      "quantity": 1,
      "options": {
        "Размер порции": "Большая",
        "Острота": "Средняя"
      }
    },
    {
      "type": "standalone",
      "menu_item_id": 25,
      "quantity": 2,
      "options": {}
    }
  ],
  "extras": [],
  "notes": null
}
```

#### 4. Создание заказа с комбо (обратная совместимость)

**Request (старый формат):**
```json
POST /orders
{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": 2,
  "combo_items": [
    {"category": "soup", "menu_item_id": 10},
    {"category": "salad", "menu_item_id": 5},
    {"category": "main", "menu_item_id": 12}
  ]
}
```

**Автоматически конвертируется в:**
```json
{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": 2,
  "items": [
    {"type": "combo", "category": "soup", "menu_item_id": 10},
    {"type": "combo", "category": "salad", "menu_item_id": 5},
    {"type": "combo", "category": "main", "menu_item_id": 12}
  ]
}
```

#### 5. Микс комбо + standalone

**Request:**
```json
POST /orders
{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": 2,
  "items": [
    {"type": "combo", "category": "soup", "menu_item_id": 10},
    {"type": "combo", "category": "salad", "menu_item_id": 5},
    {"type": "combo", "category": "main", "menu_item_id": 12},
    {
      "type": "standalone",
      "menu_item_id": 20,
      "quantity": 1,
      "options": {"Размер": "Большая"}
    }
  ]
}
```

### Следующие шаги

**Для следующих субагентов Coder:**
- Подзадача 6: Создать `MenuItemOptionRepository` (CRUD для опций)
- Подзадача 7: Обновить `OrderRepository` whitelist (добавить "items")
- Подзадача 8: Добавить методы в `MenuService` для работы с опциями
- Подзадача 9: Добавить валидацию standalone items в `MenuService`
- Подзадача 10: Обновить `create_order` в `OrderService` для поддержки standalone
- Подзадача 11: Обновить `update_order` в `OrderService`
- Подзадача 12: Создать эндпоинты в `menu.py` роутере для CRUD опций

**Для Reviewer:**
- Проверить корректность схем и валидаторов
- Проверить соответствие типов между моделями и схемами
- Проверить обратную совместимость с существующими эндпоинтами

**Для Tester:**
- Тесты для валидации MenuItemOption (min_length, max_length, min items)
- Тесты для discriminated union (правильный выбор ComboItem/StandaloneItem)
- Тесты для model_validator (миграция combo_items → items)
- Тесты для создания заказов в старом формате (обратная совместимость)
- Тесты для создания standalone заказов
- Тесты для валидации обязательных опций (is_required)

## Статус

✅ Подзадача 4 выполнена: Схемы для MenuItemOption созданы
✅ Подзадача 5 выполнена: Схемы для Order обновлены с поддержкой items

**Status:** completed
**Next:** подзадачи 6-7 (Repository для MenuItemOption и Order)
