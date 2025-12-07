---
agent: coder
task_id: TSK-015
subtask: 4
subtask_name: "Services and Routers"
status: completed
next: null
created_at: 2025-12-07T12:00:00Z
files_changed:
  - path: backend/src/services/menu.py
    action: modified
  - path: backend/src/services/order.py
    action: modified
  - path: backend/src/routers/menu.py
    action: modified
---

## Реализация

Реализованы подзадачи 8-12 из плана Architect:
1. Добавлены методы в `MenuService` для CRUD операций с `MenuItemOption`
2. Добавлены методы валидации standalone items в `MenuService`
3. Обновлён метод `create_order` в `OrderService` для поддержки standalone заказов
4. Обновлён метод `update_order` в `OrderService` для поддержки items
5. Добавлены 4 эндпоинта в `menu.py` роутер для управления опциями блюд

### Изменения

#### `backend/src/services/menu.py`

**1. Добавлены импорты:**
```python
from ..repositories.menu import MenuItemOptionRepository
from ..schemas.menu import MenuItemOptionCreate, MenuItemOptionUpdate
```

**2. Инициализация репозитория опций:**
```python
def __init__(self, session: AsyncSession):
    self.combo_repo = ComboRepository(session)
    self.item_repo = MenuItemRepository(session)
    self.option_repo = MenuItemOptionRepository(session)  # Новый
```

**3. MenuItemOption CRUD методы:**

**`list_menu_item_options(item_id)`:**
- Возвращает список всех опций для блюда
- Использует `option_repo.list_by_menu_item()`

**`get_menu_item_option(option_id)`:**
- Получает опцию по ID
- Поднимает HTTPException 404 если не найдена

**`create_menu_item_option(cafe_id, item_id, data)`:**
- Проверяет что блюдо принадлежит кафе
- Создаёт новую опцию через `option_repo.create()`
- Параметры: `menu_item_id`, `name`, `values`, `is_required`

**`update_menu_item_option(cafe_id, item_id, option_id, data)`:**
- Проверяет что блюдо принадлежит кафе
- Проверяет что опция принадлежит блюду
- Обновляет опцию через `option_repo.update()`
- Использует `exclude_unset=True` для partial update

**`delete_menu_item_option(cafe_id, item_id, option_id)`:**
- Проверяет что блюдо принадлежит кафе
- Проверяет что опция принадлежит блюду
- Удаляет опцию через `option_repo.delete()`

**4. Валидация standalone items:**

**`validate_standalone_items(items: list[dict])`:**
Валидирует standalone items:
1. Фильтрует только items с `type: "standalone"`
2. Для каждого item:
   - Проверяет существование menu_item
   - Проверяет наличие price (не None)
   - Проверяет is_available (должен быть True)
   - Загружает опции блюда
   - Проверяет обязательные опции (is_required=True)
   - Проверяет корректность значений опций (selected_value in option.values)

**Exceptions:**
- 400 BAD_REQUEST если menu_item не найден
- 400 BAD_REQUEST если у menu_item нет price
- 400 BAD_REQUEST если menu_item недоступен
- 400 BAD_REQUEST если обязательная опция не выбрана
- 400 BAD_REQUEST если значение опции некорректно

**`calculate_standalone_price(items: list[dict]) -> Decimal`:**
- Фильтрует standalone items
- Суммирует: `menu_item.price * quantity`
- Возвращает общую сумму

#### `backend/src/services/order.py`

**1. Добавлен импорт:**
```python
from decimal import Decimal
```

**2. Обновлён `create_order` метод:**

**Логика валидации items:**
```python
items_dict = [item.model_dump() for item in data.items]

if data.combo_id:
    # Combo order - валидируем combo items
    combo_items = [item for item in items_dict if item.get("type") == "combo"]
    await self.menu_service.validate_combo_items(data.combo_id, combo_items)

    # Также валидируем standalone items (если есть)
    standalone_items = [item for item in items_dict if item.get("type") == "standalone"]
    if standalone_items:
        await self.menu_service.validate_standalone_items(standalone_items)
else:
    # Standalone order - все items должны быть standalone
    for item in items_dict:
        if item.get("type") == "combo":
            raise HTTPException(400, "Combo items require combo_id to be set")
    await self.menu_service.validate_standalone_items(items_dict)
```

**Логика расчёта цены:**
```python
# Combo price (если указан combo_id)
combo_price = Decimal("0")
if data.combo_id:
    combo = await self.menu_service.get_combo(data.combo_id)
    combo_price = combo.price

# Standalone price
standalone_items = [item for item in items_dict if item.get("type") == "standalone"]
standalone_price = await self.menu_service.calculate_standalone_price(standalone_items)

# Extras price
extras_price = await self.menu_service.calculate_extras_price(extras_dict)

# Total
total_price = combo_price + standalone_price + extras_price
```

**Создание заказа:**
```python
return await self.repo.create(
    # ...
    combo_id=data.combo_id,  # Может быть None
    items=items_dict,        # Новое имя поля
    # ...
)
```

**3. Обновлён `update_order` метод:**

Аналогично `create_order`, но с учётом partial update:
- Если `data.items` указан — валидирует и обновляет
- Если `data.combo_id` изменён — учитывает новое значение
- Пересчитывает `total_price` если изменены `combo_id`, `items` или `extras`
- Использует существующие значения order.items/order.extras если не переданы новые

**Расчёт цены при update:**
```python
if data.combo_id is not None or data.items is not None or data.extras is not None:
    combo_id = update_data.get("combo_id") if "combo_id" in update_data else order.combo_id
    items = update_data.get("items", order.items)
    extras = update_data.get("extras", order.extras)

    # Расчёт аналогично create_order
    # ...

    update_data["total_price"] = combo_price + standalone_price + extras_price
```

#### `backend/src/routers/menu.py`

**1. Добавлены импорты:**
```python
from ..schemas.menu import (
    # ...
    MenuItemOptionCreate, MenuItemOptionResponse, MenuItemOptionUpdate,
)
```

**2. Добавлены эндпоинты:**

**GET `/cafes/{cafe_id}/menu/{item_id}/options`:**
- Доступен всем пользователям (CurrentUser)
- Проверяет что item существует и принадлежит cafe
- Возвращает список опций

**POST `/cafes/{cafe_id}/menu/{item_id}/options` (201):**
- Требует ManagerUser (только менеджеры)
- Создаёт новую опцию для блюда
- Request body: `MenuItemOptionCreate`
- Response: `MenuItemOptionResponse`

**PATCH `/cafes/{cafe_id}/menu/{item_id}/options/{option_id}`:**
- Требует ManagerUser
- Обновляет существующую опцию
- Request body: `MenuItemOptionUpdate` (partial)
- Response: `MenuItemOptionResponse`

**DELETE `/cafes/{cafe_id}/menu/{item_id}/options/{option_id}` (204):**
- Требует ManagerUser
- Удаляет опцию
- No response body

**Валидация в эндпоинтах:**
- Проверка принадлежности item к cafe
- Проверка принадлежности option к item
- Проверка роли пользователя (manager для CUD операций)

## Примеры использования

### 1. Создание опции для блюда

**Request:**
```http
POST /cafes/1/menu/10/options
Authorization: Bearer <manager_token>
Content-Type: application/json

{
  "name": "Размер порции",
  "values": ["Стандарт", "Большая", "XL"],
  "is_required": true
}
```

**Response (201):**
```json
{
  "id": 1,
  "menu_item_id": 10,
  "name": "Размер порции",
  "values": ["Стандарт", "Большая", "XL"],
  "is_required": true
}
```

### 2. Получение опций блюда

**Request:**
```http
GET /cafes/1/menu/10/options
Authorization: Bearer <user_token>
```

**Response (200):**
```json
[
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
    "values": ["Без остроты", "Слабая", "Средняя", "Острая"],
    "is_required": false
  }
]
```

### 3. Создание standalone заказа

**Request:**
```http
POST /orders
Authorization: Bearer <user_token>
Content-Type: application/json

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

**Валидация:**
- Проверит что у menu_item 10 и 25 есть price
- Проверит что оба блюда доступны (is_available=True)
- Проверит обязательные опции для menu_item 10
- Проверит корректность значений "Большая" и "Средняя"
- Рассчитает total_price как сумму цен standalone items

### 4. Создание микс заказа (combo + standalone)

**Request:**
```http
POST /orders
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": 2,
  "items": [
    {"type": "combo", "category": "soup", "menu_item_id": 5},
    {"type": "combo", "category": "salad", "menu_item_id": 8},
    {"type": "combo", "category": "main", "menu_item_id": 12},
    {
      "type": "standalone",
      "menu_item_id": 20,
      "quantity": 1,
      "options": {"Размер": "Большая"}
    }
  ],
  "extras": [],
  "notes": "Доставить к 12:30"
}
```

**Расчёт цены:**
```
total_price = combo.price + (item_20.price * 1) + extras_price
```

### 5. Обновление опции

**Request:**
```http
PATCH /cafes/1/menu/10/options/1
Authorization: Bearer <manager_token>
Content-Type: application/json

{
  "values": ["Маленькая", "Стандарт", "Большая", "XL"],
  "is_required": false
}
```

**Response (200):**
```json
{
  "id": 1,
  "menu_item_id": 10,
  "name": "Размер порции",
  "values": ["Маленькая", "Стандарт", "Большая", "XL"],
  "is_required": false
}
```

## Валидация и проверки

### Валидация standalone items

**Проверка 1: Наличие menu_item**
```python
menu_item = await self.item_repo.get(menu_item_id)
if not menu_item:
    raise HTTPException(400, f"Menu item {menu_item_id} not found")
```

**Проверка 2: Наличие цены**
```python
if menu_item.price is None:
    raise HTTPException(400, f"Menu item '{menu_item.name}' has no price and cannot be ordered standalone")
```

**Проверка 3: Доступность**
```python
if not menu_item.is_available:
    raise HTTPException(400, f"Menu item '{menu_item.name}' is not available")
```

**Проверка 4: Обязательные опции**
```python
for option in options:
    if option.is_required and option.name not in selected_options:
        raise HTTPException(400, f"Required option '{option.name}' not selected for '{menu_item.name}'")
```

**Проверка 5: Корректность значений опций**
```python
if option.name in selected_options:
    selected_value = selected_options[option.name]
    if selected_value not in option.values:
        raise HTTPException(400, f"Invalid value '{selected_value}' for option '{option.name}'")
```

### Валидация при создании заказа

**Сценарий 1: Combo заказ с combo_id**
```python
if data.combo_id:
    combo_items = [item for item in items_dict if item.get("type") == "combo"]
    await validate_combo_items(data.combo_id, combo_items)

    standalone_items = [item for item in items_dict if item.get("type") == "standalone"]
    if standalone_items:
        await validate_standalone_items(standalone_items)
```

**Сценарий 2: Standalone заказ без combo_id**
```python
else:
    for item in items_dict:
        if item.get("type") == "combo":
            raise HTTPException(400, "Combo items require combo_id to be set")
    await validate_standalone_items(items_dict)
```

### Валидация опций в роутере

**Проверка принадлежности:**
```python
# В create_menu_item_option
item = await service.get_menu_item(item_id)
if item.cafe_id != cafe_id:
    raise HTTPException(404, "Menu item not found in this cafe")

# В update_menu_item_option
option = await service.get_menu_item_option(option_id)
if option.menu_item_id != item_id:
    raise HTTPException(404, "Option not found for this menu item")
```

## Соответствие требованиям

### Подзадача 8: Service для MenuItemOption CRUD ✅

| Метод | Статус | Комментарий |
|-------|--------|-------------|
| list_menu_item_options | ✅ | Возвращает список опций для блюда |
| get_menu_item_option | ✅ | С проверкой 404 |
| create_menu_item_option | ✅ | С проверкой cafe_id |
| update_menu_item_option | ✅ | С проверкой cafe_id и item_id |
| delete_menu_item_option | ✅ | С проверкой cafe_id и item_id |

### Подзадача 9: Service для валидации standalone items ✅

| Метод | Статус | Комментарий |
|-------|--------|-------------|
| validate_standalone_items | ✅ | Полная валидация (price, availability, options) |
| calculate_standalone_price | ✅ | Сумма price * quantity |

### Подзадача 10: Service для создания заказа ✅

| Функциональность | Статус | Комментарий |
|------------------|--------|-------------|
| Поддержка combo_id | ✅ | Валидация combo items |
| Поддержка standalone без combo_id | ✅ | Валидация standalone items |
| Поддержка микс (combo + standalone) | ✅ | Валидация обоих типов |
| Расчёт total_price | ✅ | combo + standalone + extras |
| Использование items вместо combo_items | ✅ | Передаётся в repo.create |

### Подзадача 11: Service для обновления заказа ✅

| Функциональность | Статус | Комментарий |
|------------------|--------|-------------|
| Обновление items | ✅ | С полной валидацией |
| Пересчёт total_price | ✅ | При изменении combo_id/items/extras |
| Использование существующих значений | ✅ | Если поля не переданы |

### Подзадача 12: Router для MenuItemOption ✅

| Эндпоинт | Метод | Роль | Статус |
|----------|-------|------|--------|
| /cafes/{cafe_id}/menu/{item_id}/options | GET | CurrentUser | ✅ |
| /cafes/{cafe_id}/menu/{item_id}/options | POST | ManagerUser | ✅ |
| /cafes/{cafe_id}/menu/{item_id}/options/{option_id} | PATCH | ManagerUser | ✅ |
| /cafes/{cafe_id}/menu/{item_id}/options/{option_id} | DELETE | ManagerUser | ✅ |

## Интеграция с существующим кодом

### Использование существующих паттернов

**1. Зависимости FastAPI:**
```python
service: Annotated[MenuService, Depends(get_menu_service)]
manager: ManagerUser
current_user: CurrentUser
```

**2. Обработка ошибок:**
```python
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="...")
raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="...")
```

**3. Response models:**
```python
@router.get("...", response_model=list[MenuItemOptionResponse])
@router.post("...", response_model=MenuItemOptionResponse, status_code=201)
@router.delete("...", status_code=204)
```

**4. Partial update с exclude_unset:**
```python
await repo.update(option, **data.model_dump(exclude_unset=True))
```

### Совместимость с репозиториями

**MenuItemOptionRepository:**
- Использует те же паттерны что ComboRepository и MenuItemRepository
- Whitelist защита при update
- Async/await для всех операций
- flush() вместо commit()

**OrderRepository:**
- Поддерживает как "items" так и "combo_items" в whitelist
- Обратная совместимость через property в модели

## Обратная совместимость

### Старые заказы с combo_id

**Существующие заказы:**
- Все старые заказы имеют combo_id NOT NULL
- После миграции combo_id может быть NULL
- Старые записи не затронуты

**Чтение старых заказов:**
```python
order = await order_repo.get(old_order_id)
# order.combo_id — заполнен (int)
# order.items — список combo items (type: "combo")
# Работает как раньше
```

### Миграция combo_items → items

**На уровне модели:**
```python
# В Order model:
items: Mapped[list] = mapped_column("combo_items", JSON, nullable=False)

@property
def combo_items(self):
    """Deprecated. Use 'items' instead."""
    return self.items
```

**На уровне схемы:**
```python
# В OrderCreate:
@model_validator(mode='before')
def migrate_combo_items(cls, data):
    if 'combo_items' in data and 'items' not in data:
        data['items'] = [{'type': 'combo', **item} for item in data['combo_items']]
    return data
```

**Поддержка в сервисах:**
- Старый код может использовать order.combo_items
- Новый код использует order.items
- Оба варианта работают корректно

## Следующие шаги

**Для Reviewer:**
- Проверить корректность валидации standalone items
- Проверить расчёт total_price для всех режимов
- Проверить обработку ошибок
- Проверить соответствие паттернам проекта

**Для Tester:**
- Тесты для CRUD операций с MenuItemOption
- Тесты для валидации standalone items (price, availability, options)
- Тесты для расчёта цены (combo, standalone, микс)
- Тесты для создания заказов (combo, standalone, микс)
- Тесты для обновления заказов
- Тесты для обязательных опций
- Тесты для некорректных значений опций
- Тесты для обратной совместимости

## Статус

✅ Подзадача 8 выполнена: MenuService CRUD для MenuItemOption
✅ Подзадача 9 выполнена: Валидация и расчёт цены для standalone items
✅ Подзадача 10 выполнена: OrderService.create_order с поддержкой standalone
✅ Подзадача 11 выполнена: OrderService.update_order с поддержкой items
✅ Подзадача 12 выполнена: Router эндпоинты для MenuItemOption

**Status:** completed
**Next:** null (готов к Reviewer)
