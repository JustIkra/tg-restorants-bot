---
agent: coder
task_id: TSK-022
subtask: 1
subtask_name: "Backend endpoint"
status: completed
next: null
created_at: 2025-12-07T12:30:00Z
files_changed:
  - path: backend/src/routers/recommendations.py
    action: modified
---

## Реализация

Создан POST endpoint для принудительной генерации AI-рекомендаций через Gemini API.

### Endpoint

**URL:** `POST /api/v1/users/{tgid}/recommendations/generate`

**Авторизация:** manager | self (403 при нарушении)

**Требования:**
- Минимум 5 заказов за последние 30 дней (400 при нарушении)
- Валидный JWT токен

**Ответ:** `RecommendationsResponse`

**Ошибки:**
- `403 Forbidden` — попытка генерации для чужого пользователя (не manager)
- `400 Bad Request` — недостаточно заказов (меньше 5)
- `500 Internal Server Error` — ошибка Gemini API или исчерпаны ключи

### Изменения

#### `backend/src/routers/recommendations.py`

**Добавлены импорты:**
- `datetime`, `timezone` для timestamp генерации
- `structlog` для логирования
- `HTTPException` для обработки ошибок
- `CurrentUser`, `get_current_user` для авторизации
- `set_cache` для кэширования результатов
- `AllKeysExhaustedException`, `get_recommendation_service` для Gemini интеграции

**Добавлен endpoint `generate_user_recommendations()`:**

1. **Авторизация** (строки 117-123):
   - Проверяет: `current_user.role == "manager" OR current_user.tgid == tgid`
   - Логирует неавторизованные попытки
   - Возвращает 403 при нарушении

2. **Сбор статистики** (строка 126):
   - Использует `OrderStatsService.get_user_stats(tgid, days=30)`
   - Получает свежие данные из БД

3. **Валидация** (строки 129-138):
   - Проверяет: `stats["orders_count"] >= 5`
   - Логирует недостаточное количество заказов
   - Возвращает 400 с понятным сообщением

4. **Генерация рекомендаций** (строки 141-149):
   - Получает singleton `GeminiRecommendationService`
   - Вызывает `generate_recommendations(stats)`
   - Логирует начало процесса

5. **Кэширование** (строки 152-160):
   - Использует ключ `recommendations:user:{tgid}` (как batch worker)
   - TTL: 86400 секунд (24 часа)
   - Сохраняет: summary, tips, generated_at (ISO format)

6. **Формирование ответа** (строки 170-180):
   - Возвращает `RecommendationsResponse`
   - Включает сгенерированные рекомендации + статистику
   - Устанавливает `generated_at` в текущее время UTC

7. **Обработка ошибок** (строки 182-202):
   - `AllKeysExhaustedException` → 500 "Service temporarily unavailable"
   - Любая другая ошибка → 500 "Failed to generate recommendations"
   - Все ошибки логируются с полным стектрейсом

### Ключевые решения

1. **Переиспользование кода**
   - Используется существующий `GeminiRecommendationService` (без дублирования)
   - Используется существующий `OrderStatsService` (без изменений)
   - Кэширование по тому же ключу что и batch worker

2. **Авторизация**
   - Та же логика что и для GET endpoint: manager | self
   - Используется `CurrentUser` type alias для DI

3. **Валидация**
   - Проверка на стороне backend (не frontend)
   - Понятные сообщения об ошибках для пользователя

4. **Логирование**
   - Все операции логируются (structlog)
   - Разные уровни: info (success), warning (auth), error (failures)
   - Контекст: tgid, orders_count, error details

5. **Кэш консистентность**
   - Тот же ключ Redis что и worker: `recommendations:user:{tgid}`
   - Тот же TTL: 24 часа
   - Тот же формат данных: summary, tips, generated_at

### Тестирование

**Endpoint можно протестировать:**

```bash
# Успешная генерация (manager или self с ≥5 заказами)
curl -X POST http://localhost:8000/api/v1/users/{tgid}/recommendations/generate \
  -H "Authorization: Bearer {token}"

# 403 Forbidden (попытка генерации для другого пользователя)
curl -X POST http://localhost:8000/api/v1/users/999/recommendations/generate \
  -H "Authorization: Bearer {user_token}"

# 400 Bad Request (меньше 5 заказов)
curl -X POST http://localhost:8000/api/v1/users/{tgid}/recommendations/generate \
  -H "Authorization: Bearer {token}"

# 500 Internal Server Error (исчерпаны Gemini ключи)
# Будет возвращено автоматически при AllKeysExhaustedException
```

**Проверить кэш:**

```bash
# Redis
redis-cli GET "recommendations:user:{tgid}"
```

### Совместимость

- Полностью совместим с существующим GET endpoint
- Использует те же схемы: `RecommendationsResponse`, `OrderStats`
- Использует тот же Redis ключ (может перезаписать результат batch worker)
- Не ломает существующие интеграции

### Зависимости

**Используемые сервисы:**
- `OrderStatsService` — сбор статистики (без изменений)
- `GeminiRecommendationService` — генерация через Gemini API (без изменений)
- Redis — кэширование результатов (без изменений)

**Dependency injection:**
- `CurrentUser` — авторизация через JWT
- `get_order_stats_service()` — DI для OrderStatsService
- `get_recommendation_service()` — singleton Gemini сервиса

### Производительность

- **Время выполнения:** 10-30 секунд (зависит от Gemini API)
- **Timeout:** 30 секунд (установлен в GeminiRecommendationService)
- **Кэш:** 24 часа TTL, разделяется между batch worker и этим endpoint

### Безопасность

- Авторизация на уровне роутера (manager | self)
- Валидация входных данных (tgid должен быть int)
- Защита от спама: Gemini API имеет встроенный rate limiting
- Логирование всех попыток (включая неавторизованные)

### Ограничения

**Не реализовано в этой задаче:**
- Rate limiting на стороне приложения (можно добавить позже)
- Cooldown между генерациями для одного пользователя
- Очередь запросов (если несколько пользователей генерируют одновременно)

**Известные риски:**
- Пользователь может спамить кнопкой "Получить сейчас"
- Gemini API может быть медленным (10-30 секунд)
- Ключи могут исчерпаться при большой нагрузке

**Mitigation:**
- Loading state на фронтенде (предотвращает двойные клики)
- Понятное сообщение при ошибках
- Автоматическая ротация ключей (уже реализована в GeminiAPIKeyPool)

### Следующие шаги

Endpoint готов для интеграции с фронтендом. Следующие подзадачи:
- **02-coder-2.md** — Frontend hook `useGenerateRecommendations()`
- **02-coder-3.md** — Frontend UI dropdown в `ProfileRecommendations.tsx`
