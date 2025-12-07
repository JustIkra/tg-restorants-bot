---
agent: coder
task_id: TSK-022
status: completed
next: reviewer
created_at: 2025-12-07T13:30:00Z
files_changed:
  - path: backend/src/routers/recommendations.py
    action: modified
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
  - path: frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx
    action: modified
---

## Исправления

Все критические и важные замечания от Reviewer исправлены.

### Issue 1: Backend type inconsistency in `generated_at`

**Файл:** `backend/src/routers/recommendations.py`
**Строки:** 63-69 (новые)

**Проблема:**
GET endpoint возвращал `generated_at` как ISO string из Redis cache, а POST endpoint возвращал datetime object. Это создавало inconsistency в response типах.

**Решение:**
Добавлен парсинг ISO string в datetime object в GET endpoint:

```python
# Parse generated_at from ISO string to datetime (if exists)
generated_at_str = data.get("generated_at")
generated_at = (
    datetime.fromisoformat(generated_at_str)
    if generated_at_str
    else None
)
```

Теперь оба endpoint (GET и POST) возвращают datetime object, который Pydantic автоматически сериализует в ISO string в JSON response.

---

### Issue 4: Backend missing None check in `generated_at` parsing

**Файл:** `backend/src/routers/recommendations.py`
**Строки:** 64-69

**Проблема:**
Если `generated_at` отсутствует в Redis cache или равен None, вызов `datetime.fromisoformat(None)` вызовет TypeError.

**Решение:**
Добавлена проверка через conditional expression:

```python
generated_at = (
    datetime.fromisoformat(generated_at_str)
    if generated_at_str  # ← проверка на None/empty
    else None
)
```

Используется `if generated_at_str` вместо `if data.get("generated_at")`, что безопаснее для обработки None и пустых строк.

---

### Issue 2: Frontend race condition in state management

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts`
**Строки:** 805-807 (новые)

**Проблема:**
`setIsLoading(false)` вызывался в двух местах (try и catch блоках):
1. Дублирование кода
2. Если `mutate()` выбросит ошибку, `setIsLoading(false)` в try блоке не выполнится
3. Race condition при обработке состояния

**Решение:**
Использован `finally` блок для гарантированного выполнения `setIsLoading(false)`:

```typescript
try {
  const result = await apiRequest<RecommendationsResponse>(...);
  await mutate(`/users/${tgid}/recommendations`, undefined, { revalidate: true });
  return result;
} catch (err) {
  const error = err instanceof Error ? err : new Error("Failed to generate recommendations");
  setError(error);
  throw error;
} finally {
  setIsLoading(false);  // ← выполнится всегда
}
```

Теперь `setIsLoading(false)` гарантированно выполняется независимо от успеха/ошибки/exception в mutate.

---

### Issue 3: Frontend wrong error variable in catch block

**Файл:** `frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx`
**Строки:** 44-45

**Проблема:**
В catch блоке использовался `error` из хука (`useGenerateRecommendations()`), а не локальный `err` из catch. Это могло показать устаревшую ошибку из предыдущего вызова вместо текущей.

**Решение:**
Используется локальный `err` из catch блока:

```typescript
catch (err) {
  const errorMessage = err instanceof Error ? err.message : "Не удалось сгенерировать рекомендации";
  alert(errorMessage);
}
```

Теперь показывается актуальная ошибка из текущего вызова, а не из состояния хука.

---

## Проверка изменений

### Backend

1. **Type consistency:** Оба endpoint (GET и POST) теперь возвращают datetime, который сериализуется в ISO string
2. **None safety:** Проверка `if generated_at_str` предотвращает TypeError при парсинге
3. **Backward compatibility:** Изменения не ломают существующий код, так как Pydantic автоматически сериализует datetime

### Frontend

1. **Race condition fixed:** `finally` блок гарантирует сброс loading state
2. **Correct error display:** Используется актуальная ошибка из catch блока
3. **No breaking changes:** Интерфейс хука не изменился, только внутренняя логика

---

## Примечания

- Все исправления следуют code-style проекта (type hints, comments на русском для backend, TypeScript best practices для frontend)
- Изменения минимальны и точечны - исправлены только указанные проблемы
- Не добавлены suggestions (accessibility, улучшенные сообщения об ошибках) - они будут рассмотрены после прохождения review
