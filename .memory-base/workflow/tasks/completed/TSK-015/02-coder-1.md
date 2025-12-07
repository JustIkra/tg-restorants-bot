---
agent: coder
task_id: TSK-015
subtask: 1
subtask_name: "Migration and Models"
status: completed
next: null
created_at: 2025-12-07T12:00:00Z
files_changed:
  - path: backend/alembic/versions/004_add_menu_item_options_and_standalone_orders.py
    action: created
  - path: backend/src/models/cafe.py
    action: modified
  - path: backend/src/models/order.py
    action: modified
  - path: backend/src/models/__init__.py
    action: modified
---

## Реализация

Реализованы подзадачи 1-3 из плана Architect:
1. Создана миграция базы данных для таблицы `menu_item_options` и изменения `orders.combo_id`
2. Добавлена модель `MenuItemOption` с relationship к `MenuItem`
3. Обновлена модель `Order`: `combo_id` сделан nullable, `combo_items` переименован в `items`

### Изменения

#### `backend/alembic/versions/004_add_menu_item_options_and_standalone_orders.py`

**Создана новая миграция** с ревизией `004`:

**Upgrade:**
1. Создаёт таблицу `menu_item_options` с полями:
   - `id` (SERIAL PRIMARY KEY, autoincrement)
   - `menu_item_id` (INTEGER NOT NULL, FK → menu_items.id ON DELETE CASCADE)
   - `name` (VARCHAR(100) NOT NULL)
   - `values` (JSONB NOT NULL)
   - `is_required` (BOOLEAN NOT NULL DEFAULT FALSE)

2. Создаёт индекс `idx_menu_item_options_menu_item_id` на `menu_item_id` для оптимизации запросов

3. Изменяет `orders.combo_id` на nullable (ALTER COLUMN combo_id DROP NOT NULL)

**Downgrade:**
1. Возвращает `orders.combo_id` к NOT NULL (требует чтобы все заказы имели combo_id)
2. Удаляет индекс
3. Удаляет таблицу `menu_item_options`

**Особенности:**
- Использован `postgresql.JSONB` для поля `values` (вместо обычного JSON)
- `ondelete='CASCADE'` обеспечивает автоматическое удаление опций при удалении блюда
- `server_default=sa.text('false')` для `is_required` обеспечивает значение по умолчанию на уровне БД

#### `backend/src/models/cafe.py`

**Изменения в `MenuItem`:**
1. Обновлён комментарий для `price`: теперь указано `# can be set for any category now` вместо `# only for extras`
2. Добавлен relationship `options`:
   ```python
   options: Mapped[list["MenuItemOption"]] = relationship(
       "MenuItemOption",
       back_populates="menu_item",
       cascade="all, delete-orphan"
   )
   ```
   - `cascade="all, delete-orphan"` обеспечивает автоматическое удаление опций при удалении блюда
   - Двусторонняя связь через `back_populates`

**Создан класс `MenuItemOption`:**
```python
class MenuItemOption(Base):
    """Options for menu items (e.g., size, spice level, toppings)."""

    __tablename__ = "menu_item_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("menu_items.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    values: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="options")
```

**Особенности:**
- `values: Mapped[list[str]]` — Python type hint для списка строк, но mapped_column использует JSON
- `ondelete="CASCADE"` в ForeignKey синхронизирован с миграцией
- Relationship `menu_item` для обратной навигации

#### `backend/src/models/order.py`

**Изменения в `Order`:**

1. **`combo_id` сделан nullable:**
   ```python
   # Было:
   combo_id: Mapped[int] = mapped_column(Integer, ForeignKey("combos.id"), nullable=False)

   # Стало:
   combo_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("combos.id"), nullable=True)
   ```

2. **`combo_items` переименован в `items`:**
   ```python
   # Было:
   combo_items: Mapped[list] = mapped_column(JSON, nullable=False)

   # Стало:
   items: Mapped[list] = mapped_column("combo_items", JSON, nullable=False)
   ```
   - Первый аргумент `"combo_items"` — имя колонки в БД (сохраняется старое)
   - Атрибут модели называется `items` (новое имя в коде)
   - Никаких DDL изменений в БД не требуется

3. **Relationship `combo` сделан nullable:**
   ```python
   # Было:
   combo: Mapped["Combo"] = relationship("Combo", back_populates="orders")

   # Стало:
   combo: Mapped["Combo | None"] = relationship("Combo", back_populates="orders")
   ```

4. **Добавлена property для обратной совместимости:**
   ```python
   @property
   def combo_items(self):
       """Deprecated. Use 'items' instead. Kept for backward compatibility."""
       return self.items
   ```
   - Старый код, использующий `order.combo_items`, продолжит работать
   - Property только для чтения (сеттер не нужен, т.к. код будет обновлён)

**Обновлён комментарий:**
```python
items: Mapped[list] = mapped_column("combo_items", JSON, nullable=False)
# Комментарий: Renamed from combo_items, supports combo and standalone
```

#### `backend/src/models/__init__.py`

**Добавлен импорт и экспорт `MenuItemOption`:**
```python
from .cafe import Cafe, CafeLinkRequest, Combo, MenuItem, MenuItemOption

__all__ = [
    ...,
    "MenuItemOption",
    ...
]
```

## Примечания

### Почему использован mapped_column("combo_items", ...) вместо переименования колонки?

1. **Нулевое время простоя:** не требуется DDL изменение (ALTER TABLE RENAME COLUMN)
2. **Безопасность:** старые данные остаются нетронутыми
3. **Обратная совместимость:** колонка в БД сохраняет старое имя, но код использует новое
4. **Градуальная миграция:** можно обновить код постепенно, используя property `combo_items`

### Обратная совместимость

**Существующие заказы:**
- Все старые заказы имеют `combo_id NOT NULL` — они не затронуты миграцией
- После миграции `combo_id` может быть NULL, но существующие записи сохранят значения
- Relationship `combo` стал nullable, но для старых заказов всегда будет заполнен

**Старый код:**
- Код, использующий `order.combo_items`, продолжит работать через property
- Код должен быть обновлён для использования `order.items`

**Новый код:**
- Может создавать заказы с `combo_id = None` (standalone orders)
- Может использовать `order.items` напрямую

### Миграция базы данных

**Порядок выполнения:**
1. Запустить миграцию: `alembic upgrade head`
2. Проверить создание таблицы: `\d menu_item_options` в psql
3. Проверить nullable: `\d orders` (combo_id должен быть nullable)

**Безопасность:**
- Миграция не изменяет существующие данные
- Только добавляет таблицу и меняет схему (nullable)
- Downgrade возможен, но требует отсутствия заказов с combo_id = NULL

### Следующие шаги (для других субагентов)

**Coder (подзадачи 4-12):**
- Создать схемы Pydantic для `MenuItemOption`
- Обновить схемы `Order` для поддержки `items` с `type: combo | standalone`
- Создать репозиторий для `MenuItemOption`
- Обновить сервисы для валидации standalone заказов
- Создать эндпоинты для CRUD операций с опциями

**Tester:**
- Тесты для создания/получения/обновления/удаления `MenuItemOption`
- Тесты для создания заказов с `combo_id = null`
- Тесты для валидации обязательных опций
- Тесты для расчёта `total_price` в standalone режиме
- Тесты обратной совместимости (старые заказы с combo_id)

**Reviewer:**
- Проверить корректность миграции
- Проверить соответствие моделей архитектурному плану
- Проверить каскадное удаление опций при удалении блюда
