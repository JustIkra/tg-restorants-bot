---
agent: coder
task_id: TSK-015
subtask: 3
subtask_name: "Repositories"
status: completed
next: null
created_at: 2025-12-07T12:00:00Z
files_changed:
  - path: backend/src/repositories/menu.py
    action: modified
  - path: backend/src/repositories/order.py
    action: modified
---

## Реализация

Реализованы подзадачи 6-7 из плана Architect:
1. Создан `MenuItemOptionRepository` с полным набором CRUD операций
2. Обновлён `ALLOWED_UPDATE_FIELDS` в `OrderRepository` для поддержки поля `items`

### Изменения

#### `backend/src/repositories/menu.py`

**1. Добавлен импорт `MenuItemOption`:**
```python
from ..models import Combo, MenuItem, MenuItemOption
```

**2. Добавлен whitelist для опций:**
```python
ALLOWED_MENU_ITEM_OPTION_UPDATE_FIELDS = {"name", "values", "is_required"}
```

**3. Создан класс `MenuItemOptionRepository`:**

Полный набор CRUD операций для работы с опциями блюд:

```python
class MenuItemOptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, option_id: int) -> MenuItemOption | None:
        """Получить опцию по ID."""
        result = await self.session.execute(
            select(MenuItemOption).where(MenuItemOption.id == option_id)
        )
        return result.scalar_one_or_none()

    async def list_by_menu_item(self, menu_item_id: int) -> list[MenuItemOption]:
        """Получить все опции для блюда."""
        result = await self.session.execute(
            select(MenuItemOption)
            .where(MenuItemOption.menu_item_id == menu_item_id)
            .order_by(MenuItemOption.id)
        )
        return list(result.scalars().all())

    async def create(self, menu_item_id: int, **kwargs) -> MenuItemOption:
        """Создать новую опцию для блюда."""
        option = MenuItemOption(menu_item_id=menu_item_id, **kwargs)
        self.session.add(option)
        await self.session.flush()
        return option

    async def update(self, option: MenuItemOption, **kwargs) -> MenuItemOption:
        """Обновить опцию (только разрешённые поля)."""
        for key, value in kwargs.items():
            if key not in ALLOWED_MENU_ITEM_OPTION_UPDATE_FIELDS:
                raise ValueError(f"Field '{key}' cannot be updated")
            if value is not None:
                setattr(option, key, value)
        await self.session.flush()
        return option

    async def delete(self, option: MenuItemOption) -> None:
        """Удалить опцию."""
        await self.session.delete(option)
        await self.session.flush()
```

**Особенности реализации:**

1. **`get(option_id)`** - базовый метод получения по ID
   - Возвращает `MenuItemOption | None`
   - Использует `scalar_one_or_none()` для обработки отсутствия записи

2. **`list_by_menu_item(menu_item_id)`** - список опций для конкретного блюда
   - Фильтрация по `menu_item_id`
   - Сортировка по `id` для стабильного порядка
   - Возвращает список (может быть пустым)

3. **`create(menu_item_id, **kwargs)`** - создание новой опции
   - Принимает `menu_item_id` явно (обязательный параметр)
   - Остальные поля (`name`, `values`, `is_required`) через kwargs
   - Использует `flush()` вместо `commit()` для работы в транзакции

4. **`update(option, **kwargs)`** - обновление опции
   - Принимает объект опции (уже загруженный из БД)
   - Whitelist защита через `ALLOWED_MENU_ITEM_OPTION_UPDATE_FIELDS`
   - Пропускает `None` значения (не обновляет если не указано)
   - Поднимает `ValueError` для недопустимых полей

5. **`delete(option)`** - удаление опции
   - Принимает объект опции
   - Использует `flush()` для работы в транзакции

**Соответствие паттернам:**
- Следует тому же стилю, что `ComboRepository` и `MenuItemRepository`
- Async/await для всех операций
- Использует `flush()` вместо `commit()` (для контроля транзакций на уровне сервисов)
- Whitelist полей для безопасности

#### `backend/src/repositories/order.py`

**Обновлён whitelist полей:**

```python
# Было:
ALLOWED_UPDATE_FIELDS = {"combo_id", "combo_items", "extras", "notes", "total_price", "status"}

# Стало:
ALLOWED_UPDATE_FIELDS = {"combo_id", "items", "combo_items", "extras", "notes", "total_price", "status"}
```

**Изменения:**
1. Добавлено поле `"items"` — новое название для combo_items
2. Сохранено поле `"combo_items"` для обратной совместимости
3. Оба поля могут использоваться при обновлении заказа

**Обратная совместимость:**
- Старый код может передавать `combo_items` — работает через property в модели
- Новый код использует `items` — прямое обновление поля
- Оба варианта валидны и не вызывают ошибок

## Валидация

### Whitelist защита

`MenuItemOptionRepository.update()` защищён от обновления недопустимых полей:

```python
# Разрешено обновлять:
ALLOWED_MENU_ITEM_OPTION_UPDATE_FIELDS = {"name", "values", "is_required"}

# Запрещено обновлять:
# - id (primary key, автоинкремент)
# - menu_item_id (foreign key, не должен меняться после создания)
```

Попытка обновить `id` или `menu_item_id` вызовет:
```python
ValueError: Field 'id' cannot be updated
ValueError: Field 'menu_item_id' cannot be updated
```

### Примеры использования

#### Создание опции:
```python
repo = MenuItemOptionRepository(session)
option = await repo.create(
    menu_item_id=10,
    name="Размер порции",
    values=["Стандарт", "Большая", "XL"],
    is_required=True
)
```

#### Получение опций блюда:
```python
options = await repo.list_by_menu_item(menu_item_id=10)
# [MenuItemOption(name="Размер порции"), MenuItemOption(name="Острота"), ...]
```

#### Обновление опции:
```python
option = await repo.get(option_id=5)
await repo.update(
    option,
    values=["Маленькая", "Стандарт", "Большая", "XL"],  # добавили "Маленькая"
    is_required=False  # сделали опциональной
)
```

#### Удаление опции:
```python
option = await repo.get(option_id=5)
await repo.delete(option)
```

## Примечания

### Почему `menu_item_id` передаётся в `create()` отдельно?

```python
async def create(self, menu_item_id: int, **kwargs) -> MenuItemOption:
```

**Причины:**
1. **Явность** — `menu_item_id` обязательное поле, это подчёркивается сигнатурой
2. **Безопасность** — невозможно создать опцию без привязки к блюду
3. **Консистентность** — аналогично `ComboRepository.create(cafe_id, ...)` и `MenuItemRepository.create(cafe_id, ...)`

### Почему используется `flush()` вместо `commit()`?

**Repository уровень НЕ управляет транзакциями:**
- `flush()` — сбрасывает изменения в БД, но не коммитит
- Транзакции управляются на уровне **Service** или **Router**
- Это позволяет группировать несколько операций в одну транзакцию

**Пример:**
```python
# В сервисе можно сделать несколько операций в одной транзакции
async with session.begin():
    menu_item = await menu_repo.create(cafe_id=1, name="Борщ", ...)
    option1 = await option_repo.create(menu_item.id, name="Размер", ...)
    option2 = await option_repo.create(menu_item.id, name="Острота", ...)
    # Все 3 операции коммитятся вместе
```

### Обработка каскадного удаления

При удалении блюда (`MenuItem`) все его опции автоматически удаляются:

```python
# В модели MenuItem:
options: Mapped[list["MenuItemOption"]] = relationship(
    "MenuItemOption",
    back_populates="menu_item",
    cascade="all, delete-orphan"  # ← автоматическое удаление опций
)

# В модели MenuItemOption:
menu_item_id: Mapped[int] = mapped_column(
    Integer,
    ForeignKey("menu_items.id", ondelete="CASCADE"),  # ← каскадное удаление на уровне БД
    nullable=False
)
```

**Двойная защита:**
1. SQLAlchemy ORM: `cascade="all, delete-orphan"`
2. PostgreSQL: `ON DELETE CASCADE` в foreign key

## Интеграция с остальной системой

### Следующие шаги (для других субагентов)

**Schemas (подзадача 4):**
- Создать Pydantic схемы для `MenuItemOption`:
  - `MenuItemOptionBase`
  - `MenuItemOptionCreate`
  - `MenuItemOptionUpdate`
  - `MenuItemOptionResponse`

**Services (подзадача 8):**
- Добавить методы в `MenuService`:
  - `list_menu_item_options(item_id)`
  - `get_menu_item_option(option_id)` — с проверкой 404
  - `create_menu_item_option(item_id, data)`
  - `update_menu_item_option(cafe_id, item_id, option_id, data)`
  - `delete_menu_item_option(cafe_id, item_id, option_id)`

**Routers (подзадача 12):**
- Создать эндпоинты:
  - `GET /cafes/{cafe_id}/menu/{item_id}/options`
  - `POST /cafes/{cafe_id}/menu/{item_id}/options` (manager only)
  - `PATCH /cafes/{cafe_id}/menu/{item_id}/options/{option_id}` (manager only)
  - `DELETE /cafes/{cafe_id}/menu/{item_id}/options/{option_id}` (manager only)

**Tester:**
- Тесты для CRUD операций `MenuItemOptionRepository`
- Тесты для каскадного удаления
- Тесты для whitelist защиты
- Тесты для обновления заказов через `items` и `combo_items`

## Соответствие требованиям Architect

| Требование | Статус | Комментарий |
|------------|--------|-------------|
| MenuItemOptionRepository.get() | ✅ | Реализован |
| MenuItemOptionRepository.list_by_menu_item() | ✅ | Реализован |
| MenuItemOptionRepository.create() | ✅ | Реализован с явным menu_item_id |
| MenuItemOptionRepository.update() | ✅ | С whitelist защитой |
| MenuItemOptionRepository.delete() | ✅ | Реализован |
| Whitelist {"name", "values", "is_required"} | ✅ | ALLOWED_MENU_ITEM_OPTION_UPDATE_FIELDS |
| Импорт MenuItemOption | ✅ | Добавлен в imports |
| Order.items в ALLOWED_UPDATE_FIELDS | ✅ | Добавлено "items" |
| Обратная совместимость combo_items | ✅ | Сохранено в whitelist |

## Финальная структура

**`backend/src/repositories/menu.py`:**
- `ComboRepository` (существующий)
- `MenuItemRepository` (существующий)
- `MenuItemOptionRepository` (новый)

**`backend/src/repositories/order.py`:**
- `OrderRepository` (обновлён whitelist)

Все репозитории следуют единому паттерну:
- Async/await для всех операций
- Whitelist защита при update
- Использование `flush()` для транзакционности
- Возврат моделей SQLAlchemy (не Pydantic схем)
