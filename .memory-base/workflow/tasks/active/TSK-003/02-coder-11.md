---
agent: coder
task_id: TSK-003
subtask: 11
subtask_name: "Recommendations API Endpoint"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/src/routers/recommendations.py
    action: created
  - path: backend/src/schemas/recommendations.py
    action: created
  - path: backend/src/routers/__init__.py
    action: modified
  - path: backend/src/main.py
    action: modified
---

# Подзадача 3.4: Recommendations API Endpoint

## Описание

Реализован API endpoint для получения персональных рекомендаций по питанию для пользователей.

## Реализованные компоненты

### 1. Pydantic схемы (`backend/src/schemas/recommendations.py`)

**OrderStats:**
- `orders_last_30_days: int` - количество заказов за 30 дней
- `categories: dict[str, dict]` - распределение по категориям с процентами
- `unique_dishes: int` - количество уникальных блюд
- `favorite_dishes: list[dict]` - список любимых блюд с частотой

**RecommendationsResponse:**
- `summary: str | None` - краткое резюме рекомендаций (из Gemini)
- `tips: list[str]` - список советов по питанию (из Gemini)
- `stats: OrderStats` - текущая статистика заказов
- `generated_at: datetime | None` - время генерации рекомендаций

### 2. API роутер (`backend/src/routers/recommendations.py`)

**Endpoint:** `GET /api/v1/users/{tgid}/recommendations`

**Логика работы:**

1. **Проверка кэша Redis:**
   - Ключ: `recommendations:user:{tgid}`
   - Если данные в кэше - парсинг JSON и возврат

2. **Получение статистики:**
   - Вызов `OrderStatsService.get_user_stats(tgid)`
   - Всегда свежие данные из БД

3. **Формирование ответа:**
   - Если есть кэш: `summary` + `tips` из кэша, `stats` из БД
   - Если нет кэша: `summary=None`, `tips=[]`, `stats` из БД

**Зависимости:**
- `OrderStatsService` - для сбора статистики заказов
- `get_cache()` - для чтения из Redis

**Особенности:**
- Endpoint **только читает** из кэша, не генерирует рекомендации
- Генерация выполняется отдельным worker (batch job ночью)
- Всегда возвращает актуальную статистику, даже если рекомендации не сгенерированы

### 3. Регистрация роутера

**Обновлены файлы:**
- `backend/src/routers/__init__.py` - добавлен импорт `recommendations_router`
- `backend/src/main.py` - зарегистрирован роутер в FastAPI app

**Префикс:** `/api/v1/users/{tgid}/recommendations`

## Архитектурные решения

### Разделение ответственности

**Read-only endpoint:**
- Не выполняет тяжелые вычисления
- Быстрый ответ из кэша или БД
- Не блокирует пользователя

**Batch worker (отдельно):**
- Генерация рекомендаций ночью (03:00)
- Вызов Gemini API с пулом ключей
- Сохранение в Redis с TTL 24h

### Кэш + Статистика

**Зачем возвращать stats всегда свежими?**
- Рекомендации (summary/tips) кэшируются на 24 часа
- Статистика (orders_count, categories) всегда актуальная
- Пользователь видит текущее состояние даже если советы "вчерашние"

### Graceful Degradation

**Если рекомендации не сгенерированы:**
- `summary: null`, `tips: []`
- Но `stats` все равно показывается
- Frontend может отобразить "Рекомендации пока не готовы"

## Интеграция с существующими компонентами

### OrderStatsService

Используется для сбора статистики:
```python
stats = await service.get_user_stats(tgid)
# Возвращает:
# {
#   "orders_count": 25,
#   "categories": {"soup": {"count": 10, "percent": 40.0}},
#   "unique_dishes": 15,
#   "favorite_dishes": [{"name": "Борщ", "count": 5}],
#   ...
# }
```

### Redis Client

Используется `get_cache()` из `backend/src/cache/redis_client.py`:
```python
cached = await get_cache(f"recommendations:user:{tgid}")
# Возвращает JSON string или None
```

## Формат кэшированных данных

**Структура JSON в Redis:**
```json
{
  "summary": "80% горячего, мало овощей и клетчатки",
  "tips": [
    "Попробуйте добавить салат к обеду",
    "Разнообразьте рацион рыбными блюдами",
    "Больше овощных гарниров"
  ],
  "generated_at": "2025-12-06T03:15:00Z"
}
```

**TTL:** 24 часа (устанавливается worker при генерации)

## Следующие шаги

**Зависимые компоненты (еще не реализованы):**

1. **Recommendations Worker** (подзадача 3.5):
   - Batch генерация рекомендаций ночью
   - Вызов Gemini API через key pool
   - Сохранение в Redis

2. **Gemini Client** (подзадача 3.2):
   - Интеграция с Gemini API
   - Форматирование промптов
   - Обработка ответов

3. **Gemini Key Pool** (подзадача 3.1):
   - Управление пулом API ключей
   - Ротация после 195 запросов
   - Персистентность счетчиков

**Текущий endpoint работает автономно:**
- Возвращает пустые рекомендации если worker не запущен
- Всегда показывает актуальную статистику
- Готов к интеграции с worker

## Тестирование

**Для полного тестирования понадобится:**

1. **Unit тесты:**
   - Mock `get_cache()` для проверки обработки кэша
   - Mock `OrderStatsService` для проверки формирования ответа
   - Проверка формата JSON response

2. **Integration тесты:**
   - Реальный Redis (testcontainers)
   - Реальная БД с тестовыми заказами
   - Проверка полного flow

## Соответствие спецификации

**Подзадача 3.4 из архитектуры:**
- ✅ `backend/src/routers/recommendations.py` - создан
- ✅ `backend/src/schemas/recommendations.py` - создан
- ✅ Endpoint `GET /api/v1/users/{tgid}/recommendations` - реализован
- ✅ Чтение из Redis кэша - реализовано
- ✅ Fallback на пустые рекомендации - реализовано
- ✅ Всегда свежая статистика - реализовано
- ✅ Интеграция с OrderStatsService - реализовано
- ✅ Регистрация в main.py - выполнено

**Code style:**
- ✅ Python 3.13+ type hints
- ✅ FastAPI conventions (Annotated, Depends)
- ✅ Pydantic v2 models
- ✅ Docstrings для публичных методов
- ✅ 100 символов line length

## Готовность к продакшену

**Текущее состояние:** endpoint полностью рабочий, но требует worker для генерации рекомендаций.

**Что работает сейчас:**
- ✅ API endpoint доступен
- ✅ Возвращает статистику из БД
- ✅ Читает кэш из Redis (если есть)
- ✅ Graceful degradation при отсутствии кэша

**Что нужно для полной функциональности:**
- ⏳ Worker для генерации рекомендаций (подзадача 3.5)
- ⏳ Gemini API integration (подзадачи 3.1, 3.2)
- ⏳ Тесты (фаза 5)

---

**Статус:** completed
**Следующая подзадача:** 3.5 (Recommendations Worker) или тестирование текущего endpoint
