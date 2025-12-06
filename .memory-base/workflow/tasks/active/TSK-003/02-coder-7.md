---
agent: coder
task_id: TSK-003
subtask: 7
subtask_name: "Gemini API Key Pool"
status: completed
next: null
created_at: 2025-12-06T15:45:00Z
files_changed:
  - path: backend/src/gemini/__init__.py
    action: created
  - path: backend/src/gemini/key_pool.py
    action: created
---

# Coder Report: Gemini API Key Pool

## Задача

Реализовать управление пулом API ключей для Gemini API с автоматической ротацией при достижении лимитов.

## Выполнено

### 1. Создан модуль `backend/src/gemini/`

**Файл: `backend/src/gemini/__init__.py`**
- Экспорт основных компонентов модуля
- Публичный API: `GeminiAPIKeyPool`, `get_key_pool()`, `AllKeysExhaustedException`

### 2. Реализован класс `GeminiAPIKeyPool`

**Файл: `backend/src/gemini/key_pool.py`**

#### Основные возможности:

1. **Инициализация пула ключей**
   - Принимает список API ключей
   - Настройка лимита запросов на ключ (default: 195)
   - Валидация наличия ключей

2. **Получение активного ключа** (`get_api_key()`)
   - Автоматическая проверка лимита использования
   - Автоматическая ротация при достижении лимита
   - Проверка валидности ключа
   - Инкремент счетчика использований

3. **Ротация ключей** (`rotate_key()`)
   - Ручная ротация на следующий доступный ключ
   - Пропуск невалидных ключей
   - Пропуск исчерпанных ключей
   - Логирование ротации

4. **Управление невалидными ключами** (`mark_key_invalid()`)
   - Пометка ключа как невалидного
   - Персистентность в Redis
   - Автоматический пропуск при ротации

5. **Мониторинг статуса** (`get_pool_status()`)
   - Текущий активный ключ
   - Счетчики использований для всех ключей
   - Список невалидных ключей
   - Общая статистика пула

#### Redis схема:

```
gemini:current_key_index         → "0" (индекс текущего ключа)
gemini:usage:{key_index}         → "187" (счетчик, TTL 24h)
gemini:invalid:{key_index}       → "1" (флаг невалидности)
gemini:rotation_log              → list (история ротаций, последние 100)
```

#### Обработка ошибок:

- **`AllKeysExhaustedException`**: выбрасывается когда все ключи исчерпаны или невалидны
- Детальное логирование через `structlog`
- Graceful fallback при ротации

### 3. Singleton factory `get_key_pool()`

- Создание единственного экземпляра пула
- Автоматическая инициализация из `settings`
- Проверка конфигурации `GEMINI_API_KEYS`

## Использование

### Пример 1: Получение API ключа

```python
from backend.src.gemini import get_key_pool

# Получить пул ключей (singleton)
key_pool = get_key_pool()

# Получить активный ключ (с автоматической ротацией)
api_key = await key_pool.get_api_key()

# Использовать ключ для запроса к Gemini API
# ... (будет реализовано в следующей подзадаче)
```

### Пример 2: Обработка ошибок API

```python
from backend.src.gemini import AllKeysExhaustedException, get_key_pool

try:
    api_key = await key_pool.get_api_key()
    # Запрос к API
except AllKeysExhaustedException:
    logger.error("All Gemini API keys exhausted")
    # Fallback: вернуть пустые рекомендации или retry позже
```

### Пример 3: Мониторинг состояния

```python
status = await key_pool.get_pool_status()
print(status)
# {
#   "current_key_index": 2,
#   "usage_counts": {0: 195, 1: 195, 2: 78},
#   "invalid_keys": [],
#   "total_keys": 3,
#   "max_requests_per_key": 195
# }
```

## Технические детали

### Зависимости

- `backend.src.cache.redis_client` - для работы с Redis
- `backend.src.config` - для доступа к настройкам (`settings.gemini_keys_list`)
- `structlog` - для структурированного логирования

### Redis операции

1. **Атомарность**: используется `INCRBY` для инкремента счетчиков
2. **TTL**: автоматическая установка TTL 24 часа для счетчиков
3. **Персистентность**: состояние пула сохраняется между перезапусками
4. **Ротация лог**: хранится последние 100 событий ротации (LTRIM)

### Логирование

Все критические операции логируются с контекстом:
- Инициализация пула
- Ротация ключей
- Достижение лимитов
- Пометка ключей как невалидных
- Исчерпание всех ключей

### Особенности реализации

1. **Циклическая ротация**: при достижении конца списка ключей начинается с начала
2. **Умная ротация**: автоматический пропуск невалидных и исчерпанных ключей
3. **Fail-fast**: исключение при отсутствии валидных ключей
4. **Thread-safe**: использование Redis для синхронизации состояния

## Интеграция с конфигурацией

Модуль использует настройки из `backend/src/config.py`:

```python
# .env
GEMINI_API_KEYS=key1,key2,key3
GEMINI_MAX_REQUESTS_PER_KEY=195

# settings.py
class Settings:
    GEMINI_API_KEYS: str
    GEMINI_MAX_REQUESTS_PER_KEY: int = 195

    @property
    def gemini_keys_list(self) -> list[str]:
        return [k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip()]
```

## Границы реализации

Согласно требованиям подзадачи 3.1:

✅ Создан `backend/src/gemini/__init__.py`
✅ Создан `backend/src/gemini/key_pool.py`
✅ Реализован класс `GeminiAPIKeyPool` с полным функционалом
✅ Реализована Redis схема для персистентности
✅ Реализован Exception `AllKeysExhaustedException`
✅ Реализован singleton factory `get_key_pool()`
❌ **НЕ создан** Gemini client (это подзадача 3.2)
❌ **НЕ написаны** тесты (это подзадача 5.x)

## Следующие шаги

1. **Подзадача 3.2**: Создать Gemini client wrapper (`backend/src/gemini/client.py`)
   - Интеграция с `GeminiAPIKeyPool`
   - Обработка ошибок API (429, 401, 400)
   - Автоматическая ротация при rate limits
   - Генерация рекомендаций

2. **Подзадача 5.1**: Написать unit тесты для `GeminiAPIKeyPool`
   - Тесты ротации
   - Тесты счетчиков
   - Тесты обработки невалидных ключей
   - Тесты исчерпания пула

## Статус

**Completed** ✅

Модуль готов к использованию в Gemini client (следующая подзадача).
