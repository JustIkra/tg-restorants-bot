---
agent: coder
task_id: TSK-003
subtask: 8
subtask_name: "Order Statistics Service"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/src/services/order_stats.py
    action: created
  - path: backend/src/services/__init__.py
    action: updated
---

# Coder Report: Order Statistics Service

## Подзадача
**Подзадача 3.3:** Order Statistics Service

## Что сделано

Создан сервис для сбора и анализа статистики заказов пользователей, который будет использоваться для генерации персональных рекомендаций через Gemini API.

### Измененные файлы

#### 1. `backend/src/services/order_stats.py` (создан)

#### 2. `backend/src/services/__init__.py` (обновлен)
Добавлен импорт `OrderStatsService` в `__all__` для доступности сервиса.

---

### Реализация OrderStatsService

Реализован класс `OrderStatsService` со следующими методами:

**Публичные методы:**

1. **`get_user_stats(user_tgid: int, days: int = 30) -> dict`**
   - Собирает полную статистику заказов пользователя за последние N дней
   - Возвращает:
     - Количество заказов
     - Распределение по категориям (count + percent)
     - Количество уникальных блюд
     - Общее количество доступных блюд в меню
     - Топ любимых блюд
     - Дата последнего заказа

2. **`get_active_users(min_orders: int = 5, days: int = 30) -> list[int]`**
   - Получает список tgid активных пользователей с минимальным количеством заказов
   - Используется для batch-генерации рекомендаций в worker

**Приватные методы (реализация):**

1. **`_count_orders(user_tgid, since)`** - подсчет количества заказов
2. **`_get_categories_distribution(user_tgid, since)`** - распределение по категориям блюд
3. **`_count_unique_dishes(user_tgid, since)`** - количество уникальных блюд
4. **`_get_total_dishes_count()`** - общее количество блюд в меню
5. **`_get_favorite_dishes(user_tgid, since, limit=5)`** - топ любимых блюд
6. **`_get_last_order_date(user_tgid)`** - дата последнего заказа

## Технические детали

### Анализ структуры данных

Сервис работает с JSON структурами в модели `Order`:
- **`combo_items`**: `[{"category": "soup", "menu_item_id": 123}, ...]`
- **`extras`**: `[{"menu_item_id": 456, "quantity": 2}, ...]`

### Запросы к базе данных

**1. Подсчет заказов:**
```python
select(func.count(Order.id)).where(
    Order.user_tgid == user_tgid,
    Order.created_at >= since
)
```

**2. Распределение по категориям:**
- Извлекает все `combo_items` из заказов
- Парсит JSON для подсчета категорий
- Вычисляет проценты от общего количества

**3. Уникальные блюда:**
- Собирает все `menu_item_id` из `combo_items` и `extras`
- Использует `set` для удаления дубликатов

**4. Любимые блюда:**
- Подсчитывает частоту каждого блюда
- JOIN с `MenuItem` для получения названий
- Сортирует по убыванию и возвращает топ-5

**5. Активные пользователи:**
```python
select(Order.user_tgid, func.count(Order.id))
    .group_by(Order.user_tgid)
    .having(func.count(Order.id) >= min_orders)
```

### Соответствие стандартам кода

✅ **Python 3.13+ type hints:**
- Используется новый синтаксис `dict[str, dict]` вместо `Dict` из typing
- Все параметры и возвращаемые значения типизированы

✅ **SQLAlchemy async:**
- Все запросы используют `async/await`
- `AsyncSession` для работы с БД

✅ **Code style:**
- Line length < 100 символов
- Snake_case для методов
- Docstrings для публичных методов
- Приватные методы с префиксом `_`

✅ **Оптимизация:**
- Минимум запросов к БД
- Использование агрегатных функций SQL
- Эффективная обработка JSON структур

## Пример использования

```python
from backend.src.services.order_stats import OrderStatsService
from sqlalchemy.ext.asyncio import AsyncSession

async def get_recommendations(user_tgid: int, session: AsyncSession):
    stats_service = OrderStatsService(session)

    # Получить статистику пользователя за 30 дней
    stats = await stats_service.get_user_stats(user_tgid, days=30)

    # Результат:
    # {
    #     "orders_count": 15,
    #     "categories": {
    #         "soup": {"count": 10, "percent": 33.3},
    #         "salad": {"count": 8, "percent": 26.7},
    #         "main": {"count": 12, "percent": 40.0}
    #     },
    #     "unique_dishes": 25,
    #     "total_dishes_available": 150,
    #     "favorite_dishes": [
    #         {"name": "Борщ", "count": 5},
    #         {"name": "Цезарь", "count": 3}
    #     ],
    #     "last_order_date": datetime(2025, 12, 6, 12, 0, 0)
    # }

    # Получить активных пользователей для batch-обработки
    active_users = await stats_service.get_active_users(min_orders=5, days=30)
    # [123456, 789012, 345678, ...]
```

## Интеграция

Этот сервис будет использоваться в:

1. **Recommendations Worker** (подзадача 3.5):
   - `get_active_users()` - для batch-генерации рекомендаций ночью
   - `get_user_stats()` - для получения данных для каждого пользователя

2. **Recommendations API Endpoint** (подзадача 3.4):
   - `get_user_stats()` - для отображения статистики вместе с рекомендациями

3. **Gemini Recommendation Service** (подзадача 3.2):
   - Статистика передается в промпт для генерации персональных советов

## Следующие шаги

- [ ] **Подзадача 3.4**: Создать API endpoint для получения рекомендаций (использует этот сервис)
- [ ] **Подзадача 3.5**: Создать Kafka worker для batch-генерации (использует `get_active_users()`)

## Статус
✅ **Completed**

Сервис готов к использованию. Реализованы все методы согласно спецификации архитектора.
