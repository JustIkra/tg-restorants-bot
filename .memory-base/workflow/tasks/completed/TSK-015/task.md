---
id: TSK-015
title: Добавить возможность заказа отдельных блюд с опциями
pipeline: feature
status: completed
created_at: 2025-12-07T00:00:00Z
related_files:
  - backend/src/models/cafe.py
  - backend/src/models/order.py
  - backend/src/schemas/menu.py
  - backend/src/schemas/order.py
  - backend/src/services/menu.py
  - backend/src/services/order.py
  - backend/src/routers/menu.py
  - backend/src/routers/orders.py
  - frontend_mini_app/src/app/page.tsx
  - frontend_mini_app/src/components/ComboSelector/ComboSelector.tsx
  - frontend_mini_app/src/components/Menu/MenuSection.tsx
impact:
  - api: 40
  - db: 40
  - frontend: 40
  - services: 40
---

## Описание

Добавить возможность заказывать отдельные блюда из меню без привязки к комбо-наборам. Каждое блюдо должно иметь свою цену и может иметь опциональные модификаторы (например, размер порции, степень прожарки, дополнительные ингредиенты), которые заполняет менеджер и выбирает пользователь.

### Текущее состояние

Сейчас система поддерживает только:
- **Комбо-наборы** (Combo) — фиксированная комбинация категорий (salad + soup + main) с одной ценой
- **Блюда меню** (MenuItem) — блюда, которые входят в комбо (без собственной цены для soup/salad/main)
- **Дополнительные товары** (extras) — категория "extra" с ценой, покупаются отдельно в дополнение к комбо

Заказ (Order) обязательно содержит:
- combo_id — ID комбо-набора
- combo_items — выбранные блюда для каждой категории комбо (JSON)
- extras — дополнительные товары (опционально, JSON)

### Что нужно изменить

1. **Сделать combo_id опциональным в Order**
   - Разрешить создавать заказы без комбо (только отдельные блюда)
   - Сохранить обратную совместимость (старые заказы с combo_id остаются валидными)

2. **Добавить цену для всех категорий MenuItem**
   - Сейчас price NULL для soup/salad/main (только для extra есть цена)
   - Нужно разрешить указывать цену для любой категории
   - Блюда с ценой можно заказывать отдельно
   - Блюда без цены остаются доступными только в комбо

3. **Добавить модель MenuItemOption для опций блюд**
   - Создать таблицу menu_item_options
   - Связь: MenuItem → MenuItemOption (one-to-many)
   - Поля:
     - id: int (PK)
     - menu_item_id: int (FK → menu_items.id)
     - name: str (название опции, например "Размер порции")
     - values: list[str] (JSON, варианты выбора, например ["Стандарт", "Большая"])
     - is_required: bool (обязательная ли опция)
   - Менеджер управляет опциями через API
   - Пользователь выбирает значения при заказе

4. **Расширить Order.combo_items → Order.items**
   - Переименовать поле combo_items → items (сохранить обратную совместимость через алиас)
   - Добавить структуру для standalone блюд:
     ```json
     items: [
       // Блюда из комбо (если combo_id указан)
       { "type": "combo", "category": "soup", "menu_item_id": 10 },

       // Отдельные блюда
       {
         "type": "standalone",
         "menu_item_id": 25,
         "quantity": 2,
         "options": { "Размер порции": "Большая", "Острота": "Средняя" }
       }
     ]
     ```

5. **Обновить API эндпоинты**

   **Menu API:**
   - PATCH /cafes/{cafe_id}/menu/{item_id} — разрешить указывать price для любых категорий
   - POST /cafes/{cafe_id}/menu/{item_id}/options — создать опцию для блюда
   - GET /cafes/{cafe_id}/menu/{item_id}/options — получить список опций
   - PATCH /cafes/{cafe_id}/menu/{item_id}/options/{option_id} — обновить опцию
   - DELETE /cafes/{cafe_id}/menu/{item_id}/options/{option_id} — удалить опцию

   **Orders API:**
   - POST /orders — принимать:
     - combo_id (опционально)
     - items (вместо combo_items, с поддержкой standalone)
     - extras (опционально, как и раньше)
   - Валидация:
     - Если combo_id указан — проверять items.type === "combo"
     - Если combo_id null — проверять items.type === "standalone"
     - Для standalone проверять, что у menu_item есть price
     - Проверять обязательные опции (is_required)

6. **Обновить расчёт цены**
   - Если combo_id указан: combo.price + extras_price
   - Если combo_id null: sum(standalone_items) + extras_price
   - standalone_item.price = menu_item.price * quantity

7. **Frontend изменения**
   - Показывать цену для всех блюд (не только extras)
   - Добавить UI для выбора опций (например, выпадающий список)
   - В DishModal показывать опции и их варианты
   - При добавлении в корзину сохранять выбранные опции
   - Показывать цену за единицу и общую цену с учётом количества
   - Разрешить создание заказа:
     - Только из отдельных блюд (без комбо)
     - Только из комбо (как раньше)
     - Микс: комбо + отдельные блюда

## Acceptance Criteria

- [ ] Миграция создана для MenuItemOption и изменений в Order
- [ ] MenuItem.price может быть указана для любой категории (не только extra)
- [ ] MenuItemOption модель создана с полями: id, menu_item_id, name, values, is_required
- [ ] Order.combo_id сделан nullable (опциональный)
- [ ] Order.combo_items переименован в Order.items с поддержкой type: "combo" | "standalone"
- [ ] API эндпоинты для управления опциями блюд (CRUD)
- [ ] POST /orders принимает заказы без combo_id (только standalone items)
- [ ] Валидация проверяет наличие цены для standalone блюд
- [ ] Валидация проверяет обязательные опции (is_required)
- [ ] Расчёт total_price корректен для standalone заказов
- [ ] Frontend отображает цену для всех блюд
- [ ] Frontend показывает UI для выбора опций блюда
- [ ] Frontend позволяет создать заказ без комбо
- [ ] Тесты для всех новых эндпоинтов
- [ ] Тесты для валидации standalone заказов
- [ ] Обратная совместимость: старые заказы с combo_id работают как раньше

## Контекст

### Текущая модель MenuItem (backend/src/models/cafe.py)

```python
class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50))  # soup, salad, main, extra
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # only for extras
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
```

**Изменение:** разрешить price для любой категории, добавить relationship к MenuItemOption.

### Текущая модель Order (backend/src/models/order.py)

```python
class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_tgid: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.tgid"))
    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafes.id"))
    order_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    combo_id: Mapped[int] = mapped_column(Integer, ForeignKey("combos.id"), nullable=False)
    combo_items: Mapped[list] = mapped_column(JSON)  # [{ category, menu_item_id }]
    extras: Mapped[list] = mapped_column(JSON, default=list)  # [{ menu_item_id, quantity }]
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
```

**Изменения:**
- combo_id: nullable=True
- combo_items → items с поддержкой type: "combo" | "standalone"

### Текущие схемы (backend/src/schemas/order.py)

```python
class OrderCreate(BaseModel):
    cafe_id: int
    order_date: date
    combo_id: int  # сделать опциональным
    combo_items: list[ComboItemInput]  # переименовать в items
    extras: list[ExtraInput] = []
    notes: str | None = None
```

### Текущая логика создания заказа (backend/src/services/order.py:43-67)

```python
async def create_order(self, user_tgid: int, data: OrderCreate):
    # 1. Validate deadline
    await self.deadline_service.validate_order_deadline(data.cafe_id, data.order_date)

    # 2. Validate combo items
    combo_items_dict = [item.model_dump() for item in data.combo_items]
    await self.menu_service.validate_combo_items(data.combo_id, combo_items_dict)

    # 3. Calculate total price
    combo = await self.menu_service.get_combo(data.combo_id)
    extras_dict = [extra.model_dump() for extra in data.extras]
    extras_price = await self.menu_service.calculate_extras_price(extras_dict)
    total_price = combo.price + extras_price

    # 4. Create order
    return await self.repo.create(...)
```

**Изменение:** добавить ветку для standalone заказов (когда combo_id is None).

### Frontend (frontend_mini_app/src/app/page.tsx)

Сейчас используется:
- ComboSelector — выбор комбо-набора
- MenuSection — показывает блюда без цены (кроме extras)
- ExtrasSection — показывает дополнительные товары с ценой

**Изменения:**
- Показывать цену для всех блюд
- Добавить UI для выбора опций (в DishModal)
- Разрешить создание заказа без комбо

## Примеры использования

### Пример 1: Заказ только отдельных блюд

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
      "options": { "Размер": "Стандарт" }
    },
    {
      "type": "standalone",
      "menu_item_id": 15,
      "quantity": 2,
      "options": { "Размер": "Большая", "Острота": "Средняя" }
    }
  ],
  "extras": [],
  "notes": null
}
```

### Пример 2: Заказ комбо + отдельные блюда

```json
POST /orders
{
  "cafe_id": 1,
  "order_date": "2025-12-08",
  "combo_id": 2,
  "items": [
    { "type": "combo", "category": "soup", "menu_item_id": 5 },
    { "type": "combo", "category": "salad", "menu_item_id": 8 },
    { "type": "combo", "category": "main", "menu_item_id": 12 },
    {
      "type": "standalone",
      "menu_item_id": 20,
      "quantity": 1,
      "options": { "Размер": "Большая" }
    }
  ],
  "extras": [],
  "notes": "Доставить к 12:30"
}
```

### Пример управления опциями

```json
POST /cafes/1/menu/10/options
{
  "name": "Размер порции",
  "values": ["Стандарт", "Большая", "XL"],
  "is_required": true
}

POST /cafes/1/menu/10/options
{
  "name": "Острота",
  "values": ["Без остроты", "Слабая", "Средняя", "Острая"],
  "is_required": false
}
```
