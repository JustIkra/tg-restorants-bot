---
agent: coder
task_id: TSK-003
subtask: 10
subtask_name: "Gemini Client и Recommendation Service"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/src/gemini/prompts.py
    action: created
  - path: backend/src/gemini/client.py
    action: created
  - path: backend/src/gemini/__init__.py
    action: modified
---

# Gemini Client и Recommendation Service

## Выполнено

Реализованы следующие компоненты для интеграции с Gemini API:

### 1. Prompts (`backend/src/gemini/prompts.py`)

Создан модуль с промптом для генерации рекомендаций:

```python
RECOMMENDATION_PROMPT = """
Проанализируй привычки питания пользователя и дай персональные рекомендации.

Статистика за 30 дней:
- Всего заказов: {orders_count}
- Распределение по категориям: {categories}
- Уникальных блюд: {unique_dishes} из {total_available}
- Любимые блюда: {favorite_dishes}

Дай краткое резюме (1 предложение) и 2-3 совета:
1. По сбалансированности питания
2. По разнообразию рациона
3. Новые блюда для пробы

Ответ в формате JSON:
{
    "summary": "краткое резюме",
    "tips": ["совет 1", "совет 2", "совет 3"]
}
"""
```

### 2. Gemini Client (`backend/src/gemini/client.py`)

Реализован сервис `GeminiRecommendationService` с полной обработкой ошибок:

**Основные функции:**
- `generate_recommendations(user_stats)` - генерация рекомендаций с retry логикой
- `_format_prompt(user_stats)` - форматирование промпта с данными пользователя
- `_parse_response(text)` - парсинг JSON из ответа Gemini (с обработкой markdown блоков)

**Обработка ошибок:**
- **429 (Rate Limit)** → автоматическая ротация ключа через `key_pool.rotate_key()`
- **401 (Invalid Key)** → пометка ключа как недействительного + ротация
- **Network errors** → retry с переходом на следующий ключ
- **Malformed JSON** → graceful fallback на `{"summary": null, "tips": []}`

**Retry логика:**
- Максимум попыток = количество ключей в пуле
- При каждой ошибке 429/401 - ротация на следующий ключ
- При исчерпании всех ключей - `AllKeysExhaustedException`

**Используемая модель:** `gemini-2.0-flash-exp`

### 3. Singleton Factory

Создана функция `get_recommendation_service()` для получения singleton instance:

```python
def get_recommendation_service() -> GeminiRecommendationService:
    """Get singleton instance of GeminiRecommendationService."""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = GeminiRecommendationService(get_key_pool())
    return _recommendation_service
```

### 4. Обновление `__init__.py`

Добавлены экспорты:
- `GeminiRecommendationService`
- `get_recommendation_service`

## Технические детали

### Интеграция с Google GenAI SDK

Использован официальный Python SDK `google-genai`:

```python
from google import genai
from google.genai import errors as genai_errors

client = genai.Client(api_key=api_key)
response = await client.aio.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=prompt
)
```

### Обработка ответов

Парсинг JSON с поддержкой markdown code blocks:

```python
# Извлечение JSON из ```json ... ```
if "```json" in text:
    json_start = text.find("```json") + 7
    json_end = text.find("```", json_start)
    json_text = text[json_start:json_end].strip()
```

### Логирование

Все ключевые события логируются через `structlog`:
- Начало генерации рекомендаций
- Ротация ключей при ошибках
- Успешная генерация
- Ошибки парсинга JSON

## Зависимости от других компонентов

- `GeminiAPIKeyPool` - управление пулом API ключей (уже реализовано в 3.1)
- `OrderStatsService` - сбор статистики заказов (реализовано ранее)
- `Redis` - кэширование (используется через key_pool)

## Использование

```python
from backend.src.gemini import get_recommendation_service
from backend.src.services.order_stats import OrderStatsService

# Получить статистику пользователя
stats_service = OrderStatsService(session)
user_stats = await stats_service.get_user_stats(user_tgid=123456)

# Сгенерировать рекомендации
recommendation_service = get_recommendation_service()
recommendations = await recommendation_service.generate_recommendations(user_stats)

# Результат:
# {
#     "summary": "80% горячего, мало овощей",
#     "tips": ["Добавь салат", "Попробуй рыбу", "Больше разнообразия"]
# }
```

## Соответствие требованиям

✅ Создан `backend/src/gemini/prompts.py` с `RECOMMENDATION_PROMPT`
✅ Создан `backend/src/gemini/client.py` с `GeminiRecommendationService`
✅ Обновлен `backend/src/gemini/__init__.py` с экспортами
✅ Реализована обработка ошибок 429, 401, network errors
✅ Автоматическая ротация ключей при ошибках
✅ Singleton factory `get_recommendation_service()`
✅ Структурированное логирование
✅ Graceful fallback при ошибках парсинга
✅ Использован официальный SDK `google-genai`

## Следующие шаги

Этот компонент готов к использованию в:
- **Подзадача 3.4**: Recommendations API Endpoint (для прямых запросов)
- **Подзадача 3.5**: Recommendations Worker (для batch генерации)

## Примечания

- Используется `gemini-2.0-flash-exp` - экспериментальная модель с улучшенной производительностью
- При необходимости можно переключиться на `gemini-2.5-flash` (stable версия)
- Промпт оптимизирован для получения кратких, практичных рекомендаций
- JSON parsing устойчив к markdown форматированию от Gemini
