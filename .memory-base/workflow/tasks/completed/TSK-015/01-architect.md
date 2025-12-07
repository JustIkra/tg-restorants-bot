---
agent: architect
task_id: TSK-015
status: completed
next: coder
created_at: 2025-12-07T12:00:00Z
---

## Анализ

Задача требует расширения системы заказов для поддержки отдельных блюд (standalone items) с опциями вместо только комбо-наборов. Это фундаментальное изменение бизнес-логики, затрагивающее:

- **База данных**: новая таблица `menu_item_options`, изменение nullable полей в `orders`
- **Модели**: новая модель `MenuItemOption`, изменения в `MenuItem` и `Order`
- **API**: 5 новых эндпоинтов для опций, изменения в `POST /orders`
- **Валидация**: новая логика для standalone заказов и обязательных опций
- **Расчёт цен**: поддержка двух режимов (combo-based и item-based)
- **Frontend**: отображение цен для всех блюд, UI для выбора опций, поддержка standalone заказов

### Текущие ограничения

1. `Order.combo_id` — обязательное поле (nullable=False)
2. `MenuItem.price` — NULL для soup/salad/main (только для extras)
3. Нет модели опций блюд
4. `Order.combo_items` — JSON с фиксированной структурой для комбо
5. Frontend не показывает цены для soup/salad/main

## Архитектурное решение

### Принцип обратной совместимости

Все изменения должны сохранять работоспособность старых заказов:
- Существующие заказы с `combo_id` продолжают работать
- Новые заказы могут быть с `combo_id` (комбо), без него (standalone) или микс

### Стратегия миграции

**Порядок изменений:**
1. Создать таблицу `menu_item_options` (новая, не влияет на старый код)
2. Сделать `Order.combo_id` nullable (не ломает старые заказы)
3. Добавить псевдоним `Order.items` → `Order.combo_items` (обратная совместимость)
4. Обновить валидацию для поддержки обоих режимов
5. Обновить расчёт цены для поддержки standalone

### Изменения в данных

#### 1. Новая таблица `menu_item_options`

```python
class MenuItemOption(Base):
    __tablename__ = "menu_item_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Размер порции"
    values: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # ["Стандарт", "Большая"]
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="options")
```

**Миграция:**
```sql
CREATE TABLE menu_item_options (
    id SERIAL PRIMARY KEY,
    menu_item_id INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    values JSONB NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_menu_item_options_menu_item_id ON menu_item_options(menu_item_id);
```

#### 2. Изменения в `MenuItem`

```python
class MenuItem(Base):
    # ... existing fields ...

    # Добавить relationship
    options: Mapped[list["MenuItemOption"]] = relationship(
        "MenuItemOption",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )
```

**Изменения:**
- Поле `price` уже nullable, никаких DDL изменений не нужно
- Менеджер может указывать price для любой категории (не только extra)

#### 3. Изменения в `Order`

```python
class Order(Base):
    # ... existing fields ...

    # ИЗМЕНЕНИЕ: сделать combo_id nullable
    combo_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("combos.id"), nullable=True)

    # ПЕРЕИМЕНОВАНИЕ: combo_items → items (с алиасом)
    items: Mapped[list] = mapped_column("combo_items", JSON, nullable=False)

    # RELATIONSHIP: combo теперь optional
    combo: Mapped["Combo | None"] = relationship("Combo", back_populates="orders")
```

**Миграция:**
```sql
-- Сделать combo_id nullable
ALTER TABLE orders ALTER COLUMN combo_id DROP NOT NULL;
```

**Примечание:** переименование `combo_items` → `items` делается через mapped_column("combo_items", ...), чтобы сохранить имя колонки в БД, но использовать новое имя в коде.

### Структура данных Order.items

**Формат items (JSON):**

```python
# Combo items (если combo_id указан)
items = [
    {"type": "combo", "category": "soup", "menu_item_id": 10},
    {"type": "combo", "category": "salad", "menu_item_id": 5},
    {"type": "combo", "category": "main", "menu_item_id": 12}
]

# Standalone items (если combo_id = null)
items = [
    {
        "type": "standalone",
        "menu_item_id": 25,
        "quantity": 2,
        "options": {"Размер порции": "Большая", "Острота": "Средняя"}
    }
]

# Микс (combo_id указан + standalone items)
items = [
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
```

### API изменения

#### Новые эндпоинты для опций (Menu API)

```
POST   /cafes/{cafe_id}/menu/{item_id}/options       — создать опцию
GET    /cafes/{cafe_id}/menu/{item_id}/options       — список опций
PATCH  /cafes/{cafe_id}/menu/{item_id}/options/{option_id}  — обновить опцию
DELETE /cafes/{cafe_id}/menu/{item_id}/options/{option_id}  — удалить опцию
```

**Все эндпоинты требуют manager role.**

#### Изменения в Orders API

**POST /orders** — теперь принимает:
- `combo_id` (optional)
- `items` (required, вместо `combo_items`)
- `extras` (optional, как раньше)

**Валидация:**
1. Если `combo_id` указан:
   - Все items с `type: "combo"` проверяются на соответствие категориям комбо
   - Разрешены также items с `type: "standalone"`
2. Если `combo_id = null`:
   - Все items должны быть `type: "standalone"`
   - У каждого menu_item должен быть price != null
3. Для standalone items:
   - Проверить наличие обязательных опций (is_required=True)
   - Проверить корректность значений опций

## Подзадачи для Coder

### Backend подзадачи

#### Подзадача 1: Миграция базы данных
**Файл:** `backend/alembic/versions/XXXX_add_menu_item_options_and_standalone_orders.py`

Создать миграцию Alembic:
1. Создать таблицу `menu_item_options` с индексом на `menu_item_id`
2. Изменить `orders.combo_id` на nullable (ALTER COLUMN DROP NOT NULL)

**Действия:**
- Сгенерировать миграцию: `alembic revision --autogenerate -m "add menu item options and standalone orders"`
- Проверить сгенерированный код
- При необходимости скорректировать вручную

#### Подзадача 2: Модель MenuItemOption
**Файл:** `backend/src/models/cafe.py`

Действия:
1. Добавить класс `MenuItemOption` с полями: id, menu_item_id, name, values, is_required
2. Добавить relationship `options` в `MenuItem`
3. Импортировать в `backend/src/models/__init__.py`

#### Подзадача 3: Модель Order — сделать combo_id nullable
**Файл:** `backend/src/models/order.py`

Действия:
1. Изменить `combo_id: Mapped[int | None]` с nullable=True
2. Изменить relationship `combo: Mapped["Combo | None"]`
3. Добавить псевдоним для обратной совместимости:
   ```python
   items: Mapped[list] = mapped_column("combo_items", JSON, nullable=False)

   # Для обратной совместимости (deprecated)
   @property
   def combo_items(self):
       return self.items
   ```

#### Подзадача 4: Схемы для MenuItemOption
**Файл:** `backend/src/schemas/menu.py`

Создать схемы:
- `MenuItemOptionBase(name, values, is_required)`
- `MenuItemOptionCreate(MenuItemOptionBase)`
- `MenuItemOptionUpdate(BaseModel)` — все поля optional
- `MenuItemOptionResponse(MenuItemOptionBase + id, menu_item_id)`

Обновить `MenuItemResponse`:
- Добавить поле `options: list[MenuItemOptionResponse] = []`

#### Подзадача 5: Схемы для Order — поддержка items
**Файл:** `backend/src/schemas/order.py`

Действия:
1. Создать `ComboItem` и `StandaloneItem` классы:
   ```python
   class ComboItem(BaseModel):
       type: Literal["combo"] = "combo"
       category: str = Field(..., pattern="^(soup|salad|main)$")
       menu_item_id: int = Field(..., gt=0)

   class StandaloneItem(BaseModel):
       type: Literal["standalone"] = "standalone"
       menu_item_id: int = Field(..., gt=0)
       quantity: int = Field(default=1, gt=0, le=100)
       options: dict[str, str] = {}  # {option_name: selected_value}

   # Union type для items
   OrderItem = ComboItem | StandaloneItem
   ```

2. Обновить `OrderCreate`:
   ```python
   combo_id: int | None = None  # ИЗМЕНЕНИЕ: теперь optional
   items: list[OrderItem]       # ИЗМЕНЕНИЕ: вместо combo_items
   ```

3. Обновить `OrderResponse`:
   ```python
   combo_id: int | None
   items: list[dict]  # вместо combo_items
   ```

4. Удалить старый `ComboItemInput` (или оставить deprecated)

#### Подзадача 6: Repository для MenuItemOption
**Файл:** `backend/src/repositories/menu.py`

Создать `MenuItemOptionRepository`:
- `get(option_id) -> MenuItemOption | None`
- `list_by_menu_item(menu_item_id) -> list[MenuItemOption]`
- `create(menu_item_id, **kwargs) -> MenuItemOption`
- `update(option, **kwargs) -> MenuItemOption`
- `delete(option) -> None`

**Whitelist полей:** `{"name", "values", "is_required"}`

#### Подзадача 7: Repository для Order — обновить whitelist
**Файл:** `backend/src/repositories/order.py`

Действия:
1. Обновить `ALLOWED_UPDATE_FIELDS`:
   ```python
   ALLOWED_UPDATE_FIELDS = {"combo_id", "items", "extras", "notes", "total_price", "status"}
   ```
   (добавили "items", убрали "combo_items" или оставили оба для совместимости)

#### Подзадача 8: Service для MenuItemOption CRUD
**Файл:** `backend/src/services/menu.py`

Добавить методы в `MenuService`:
1. `list_menu_item_options(item_id) -> list[MenuItemOption]`
2. `get_menu_item_option(option_id) -> MenuItemOption` (с проверкой 404)
3. `create_menu_item_option(item_id, data: MenuItemOptionCreate) -> MenuItemOption`
4. `update_menu_item_option(cafe_id, item_id, option_id, data: MenuItemOptionUpdate) -> MenuItemOption`
5. `delete_menu_item_option(cafe_id, item_id, option_id) -> None`

**Валидация:**
- Проверять, что item принадлежит cafe
- Проверять, что option принадлежит item

#### Подзадача 9: Service для валидации standalone items
**Файл:** `backend/src/services/menu.py`

Добавить методы:
1. `validate_standalone_items(items: list[dict]) -> bool`
   - Проверить, что у каждого menu_item есть price
   - Проверить обязательные опции (is_required=True)
   - Проверить корректность значений опций
   - Raise HTTPException при ошибках

2. `calculate_standalone_price(items: list[dict]) -> Decimal`
   - Сумма: menu_item.price * quantity для каждого item

#### Подзадача 10: Service для создания заказа — поддержка standalone
**Файл:** `backend/src/services/order.py`

Обновить метод `create_order`:
1. Проверить deadline (как раньше)
2. Если `combo_id` указан:
   - Валидировать combo items (существующая логика)
   - Опционально валидировать standalone items в той же структуре
3. Если `combo_id = null`:
   - Валидировать standalone items (новая логика)
4. Рассчитать total_price:
   ```python
   if data.combo_id:
       combo = await self.menu_service.get_combo(data.combo_id)
       combo_price = combo.price
   else:
       combo_price = Decimal("0")

   # Найти standalone items
   standalone = [item for item in items_dict if item.get("type") == "standalone"]
   standalone_price = await self.menu_service.calculate_standalone_price(standalone)

   extras_price = await self.menu_service.calculate_extras_price(extras_dict)
   total_price = combo_price + standalone_price + extras_price
   ```

5. Создать заказ с `items` (вместо `combo_items`)

#### Подзадача 11: Service для обновления заказа — поддержка items
**Файл:** `backend/src/services/order.py`

Обновить метод `update_order`:
1. Аналогично create_order, но для обновления
2. Пересчитывать total_price при изменении combo_id или items
3. Проверять валидацию для новых items

#### Подзадача 12: Router для MenuItemOption
**Файл:** `backend/src/routers/menu.py`

Добавить эндпоинты:
```python
@router.get("/cafes/{cafe_id}/menu/{item_id}/options", response_model=list[MenuItemOptionResponse])
async def list_menu_item_options(...)

@router.post("/cafes/{cafe_id}/menu/{item_id}/options", response_model=MenuItemOptionResponse, status_code=201)
async def create_menu_item_option(..., manager: ManagerUser)

@router.patch("/cafes/{cafe_id}/menu/{item_id}/options/{option_id}", response_model=MenuItemOptionResponse)
async def update_menu_item_option(..., manager: ManagerUser)

@router.delete("/cafes/{cafe_id}/menu/{item_id}/options/{option_id}", status_code=204)
async def delete_menu_item_option(..., manager: ManagerUser)
```

**Все требуют ManagerUser (manager role).**

### Frontend подзадачи

#### Подзадача 13: API types — добавить MenuItemOption
**Файл:** `frontend_mini_app/src/lib/api/types.ts`

Добавить типы:
```typescript
export interface MenuItemOption {
  id: number;
  menu_item_id: number;
  name: string;
  values: string[];
  is_required: boolean;
}

export interface MenuItem {
  // ... existing fields ...
  options?: MenuItemOption[];
}
```

#### Подзадача 14: API client — методы для опций
**Файл:** `frontend_mini_app/src/lib/api/client.ts`

Добавить функции:
- `getMenuItemOptions(cafeId, itemId)`
- `createMenuItemOption(cafeId, itemId, data)` — manager only
- `updateMenuItemOption(cafeId, itemId, optionId, data)` — manager only
- `deleteMenuItemOption(cafeId, itemId, optionId)` — manager only

#### Подзадача 15: MenuSection — отображать цену для всех блюд
**Файл:** `frontend_mini_app/src/components/Menu/MenuSection.tsx`

Действия:
1. Показывать `dish.price` для всех категорий (не только extras)
2. Если price = 0 или null, показывать "Входит в комбо"

#### Подзадача 16: DishModal — показывать опции
**Файл:** `frontend_mini_app/src/components/Menu/DishModal.tsx`

Добавить:
1. Отображение списка опций (если есть)
2. Для каждой опции — выпадающий список (select) с values
3. Валидация обязательных опций (is_required)
4. При добавлении в корзину — сохранять выбранные опции

**State:**
```typescript
const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});
```

**Валидация при добавлении:**
```typescript
const handleAddToCart = () => {
  // Проверить обязательные опции
  const requiredOptions = dish.options?.filter(opt => opt.is_required) || [];
  const missingOptions = requiredOptions.filter(opt => !selectedOptions[opt.name]);

  if (missingOptions.length > 0) {
    alert("Выберите все обязательные опции");
    return;
  }

  addToCart(dish.id, selectedOptions);
};
```

#### Подзадача 17: Корзина — хранить опции для каждого блюда
**Файл:** `frontend_mini_app/src/app/page.tsx`

Изменить структуру cart:
```typescript
// Было:
const [cart, setCart] = useState<{ [key: number]: number }>({});

// Стало:
interface CartItem {
  quantity: number;
  options?: Record<string, string>;
}
const [cart, setCart] = useState<{ [key: number]: CartItem }>({});
```

Обновить функции:
- `addToCart(dishId, options?)` — добавить с опциями
- `removeFromCart(dishId)` — учитывать quantity
- Расчёт `totalPrice` и `totalItems` соответственно

#### Подзадача 18: Создание заказа — поддержка standalone items
**Файл:** `frontend_mini_app/src/app/order/page.tsx` (или где создаётся заказ)

Формировать JSON для POST /orders:
```typescript
const items = Object.entries(cart).map(([dishId, cartItem]) => ({
  type: "standalone",
  menu_item_id: parseInt(dishId),
  quantity: cartItem.quantity,
  options: cartItem.options || {}
}));

const orderData = {
  cafe_id: activeCafeId,
  order_date: selectedDate,
  combo_id: null,  // для standalone заказа
  items,
  extras: [],
  notes: null
};
```

**Поддержать также:**
- Заказы с combo_id (старая логика)
- Микс combo + standalone

## Риски и зависимости

### Риски

1. **Миграция существующих данных**
   - Все старые заказы имеют combo_id NOT NULL
   - После миграции combo_id станет nullable, но старые записи сохранят значения
   - **Митигация:** тщательное тестирование миграции на копии продакшн БД

2. **Обратная совместимость API**
   - Frontend может отправлять `combo_items` вместо `items`
   - **Митигация:** поддержка обоих полей в схемах (alias)

3. **Сложность валидации**
   - Нужно проверять 3 режима: combo, standalone, микс
   - **Митигация:** тщательные юнит-тесты для каждого режима

4. **Производительность**
   - Загрузка опций для каждого блюда (N+1 проблема)
   - **Митигация:** использовать relationship с eager loading

### Зависимости

1. **Alembic миграция должна выполниться ДО деплоя кода**
   - Иначе код упадёт при попытке создать Order с combo_id=null

2. **Frontend не должен использовать новые фичи до деплоя backend**
   - Поэтапный деплой: сначала backend, потом frontend

3. **Тестирование на staging окружении обязательно**
   - Проверить создание всех типов заказов (combo, standalone, микс)

### Последовательность развёртывания

1. **Backend:**
   - Деплой миграции (без кода)
   - Деплой кода (новые эндпоинты, валидация)

2. **Frontend:**
   - Деплой после подтверждения работы backend
   - Постепенное включение фич (feature flags при необходимости)

3. **Проверка:**
   - Старые заказы с combo_id работают
   - Новые standalone заказы создаются
   - Опции сохраняются и валидируются

## Acceptance Criteria Mapping

| Критерий | Подзадача |
|----------|-----------|
| Миграция создана | Подзадача 1 |
| MenuItem.price для любой категории | Подзадача 2 (документация) |
| MenuItemOption модель | Подзадача 2 |
| Order.combo_id nullable | Подзадача 3 |
| Order.items с type поддержкой | Подзадача 3, 5 |
| API CRUD для опций | Подзадача 8, 12 |
| POST /orders без combo_id | Подзадача 10 |
| Валидация цены для standalone | Подзадача 9 |
| Валидация обязательных опций | Подзадача 9 |
| Расчёт total_price для standalone | Подзадача 10 |
| Frontend показывает цены | Подзадача 15 |
| Frontend UI для опций | Подзадача 16 |
| Frontend создание standalone заказа | Подзадача 18 |
| Тесты для API | (будет в Tester agent) |
| Тесты для валидации | (будет в Tester agent) |
| Обратная совместимость | Подзадача 3, 10, 11 |

## Итого

**18 подзадач:**
- Backend: 12 подзадач (миграция, модели, схемы, репозитории, сервисы, роутеры)
- Frontend: 6 подзадач (типы, API client, компоненты, корзина, создание заказа)

**Рекомендуемый порядок выполнения:**
1. Подзадачи 1-3 (миграция, модели)
2. Подзадачи 4-7 (схемы, репозитории)
3. Подзадачи 8-12 (сервисы, роутеры)
4. Подзадачи 13-14 (frontend типы, API)
5. Подзадачи 15-18 (frontend UI, корзина, заказы)

**Критические точки для code review:**
- Корректность миграции Alembic
- Валидация обязательных опций
- Расчёт total_price для всех режимов
- Обратная совместимость с существующими заказами
