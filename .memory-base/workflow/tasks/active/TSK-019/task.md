---
id: TSK-019
title: Исправить неработающие кнопки в интерфейсе (менеджер + заказ)
pipeline: bugfix
status: pending
created_at: 2025-12-07T09:40:00Z
related_files:
  - frontend_mini_app/src/components/Manager/CafeList.tsx
  - frontend_mini_app/src/lib/api/hooks.ts
  - frontend_mini_app/src/lib/api/client.ts
  - frontend_mini_app/src/app/manager/page.tsx
  - frontend_mini_app/src/app/page.tsx
  - backend/src/routers/cafes.py
  - backend/src/services/cafe.py
impact:
  api: нет
  db: нет
  frontend: да
  services: нет
---

## Описание

В интерфейсе обнаружены критические проблемы с кнопками:

### Проблема 1: Менеджер-панель — кнопки управления кафе
1. **Кнопки не реагируют на клики**: Кнопки "Редактировать", "Деактивировать/Активировать", "Удалить" в списке кафе не работают при нажатии
2. **Деактивированные кафе исчезают из списка**: При деактивации кафе через кнопку "Деактивировать" кафе полностью исчезает из списка вместо того, чтобы отобразиться со статусом "Неактивно"

### Проблема 2: Страница заказа — кнопка "Оформить заказ"
3. **Кнопка "Оформить заказ" недоступна**: Кнопка отображается в disabled состоянии и не реагирует на клики

## Проблемная область

Компонент `CafeList` в менеджерской панели (`/manager` → вкладка "Кафе").

## Acceptance Criteria

### Функциональность кнопок
- [ ] Кнопка "Редактировать" открывает форму редактирования кафе
- [ ] Кнопка "Деактивировать" меняет статус кафе на неактивно
- [ ] Кнопка "Активировать" меняет статус кафе на активно
- [ ] Кнопка "Удалить" удаляет кафе после подтверждения
- [ ] Все кнопки корректно реагируют на клики

### Отображение статусов
- [ ] Активные кафе показываются с зелёным badge "Активно"
- [ ] Неактивные кафе показываются с красным badge "Неактивно"
- [ ] Деактивированные кафе остаются в списке и не исчезают
- [ ] После деактивации кнопка меняется на "Активировать"
- [ ] После активации кнопка меняется на "Деактивировать"

### UI состояния
- [ ] Во время обработки запроса кнопка показывает "..." и disabled
- [ ] После успешной операции список обновляется
- [ ] При ошибке показывается alert с сообщением

## Контекст

### Текущая реализация CafeList

**Файл:** `frontend_mini_app/src/components/Manager/CafeList.tsx`

```typescript
const CafeList: React.FC<CafeListProps> = ({ onEdit, shouldFetch = true }) => {
  const { data: cafes, error, isLoading } = useCafes(shouldFetch, false); // Get all cafes, not just active
  const [processingId, setProcessingId] = useState<number | null>(null);

  const handleToggleStatus = async (cafe: Cafe) => {
    setProcessingId(cafe.id);
    try {
      await apiRequest(`/cafes/${cafe.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !cafe.is_active }),
      });
      // Revalidate cafes list
      mutate("/cafes");
    } catch (err) {
      console.error("Failed to toggle cafe status:", err);
      alert(`Ошибка: ${err instanceof Error ? err.message : "Не удалось изменить статус"}`);
    } finally {
      setProcessingId(null);
    }
  };
  // ... остальной код
}
```

**Используется:**
- `useCafes(shouldFetch, false)` — второй параметр `activeOnly=false` означает загрузку всех кафе (активных и неактивных)
- `mutate("/cafes")` — обновление SWR кэша после изменений

### API Hook useCafes

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts` (строки 39-50)

```typescript
export function useCafes(shouldFetch = true, activeOnly = true): UseDataResult<Cafe> {
  const { data, error, isLoading, mutate } = useSWR<Cafe[]>(
    shouldFetch ? `/cafes${activeOnly ? "?active_only=true" : ""}` : null,
    fetcher
  );
  return {
    data,
    error,
    isLoading,
    mutate
  };
}
```

**Проблема:** Hook использует endpoint `/cafes` или `/cafes?active_only=true` в зависимости от параметра `activeOnly`.

В `CafeList` вызывается:
```typescript
useCafes(shouldFetch, false) // activeOnly = false → endpoint = "/cafes"
```

Но при `mutate("/cafes")` обновляется **только** ключ `/cafes` без query параметров.

### Backend API

**Файл:** `backend/src/routers/cafes.py` (строки 18-30)

```python
@router.get("", response_model=list[CafeResponse])
async def list_cafes(
    current_user: CurrentUser,
    service: Annotated[CafeService, Depends(get_cafe_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),  # По умолчанию True
):
    """List all cafes."""
    # Non-managers only see active cafes
    if current_user.role != "manager":
        active_only = True
    return await service.list_cafes(skip=skip, limit=limit, active_only=active_only)
```

**Важно:**
- Endpoint `GET /cafes` **по умолчанию** возвращает только активные кафе (`active_only=True`)
- Чтобы получить все кафе, нужно передать `?active_only=false`
- Менеджеры могут видеть все кафе, обычные пользователи — только активные

### Вызов в manager/page.tsx

**Файл:** `frontend_mini_app/src/app/manager/page.tsx` (строки 424-430)

```typescript
<CafeList
  shouldFetch={isAuthenticated}
  onEdit={(cafe) => {
    setEditingCafe(cafe);
    setShowCafeForm(false);
  }}
/>
```

**onEdit** передаётся как callback для открытия формы редактирования.

## Возможные причины проблем

### 1. Кнопки не реагируют на клики

**Гипотезы:**
- Событие клика не пробрасывается из-за CSS (pointer-events, z-index)
- onClick handler не вызывается
- processingId блокирует все кнопки (bug в условии disabled)
- React не обновляет DOM после клика

### 2. Деактивированные кафе исчезают

**Гипотезы:**
- **SWR cache key mismatch:** Hook запрашивает `/cafes` (без query), но backend возвращает только активные по умолчанию
- После `mutate("/cafes")` SWR перезапрашивает данные с тем же endpoint `/cafes` → backend возвращает только active кафе
- `useCafes(shouldFetch, false)` вызывает endpoint `/cafes` (без `?active_only=false`), но backend интерпретирует это как `active_only=true` (default)

**Root Cause (наиболее вероятный):**

```typescript
// CafeList.tsx
useCafes(shouldFetch, false) // activeOnly=false
↓
// hooks.ts
shouldFetch ? `/cafes${activeOnly ? "?active_only=true" : ""}` : null
↓
activeOnly = false → endpoint = "/cafes" (без query параметра)
↓
Backend GET /cafes (no query) → active_only defaults to True
↓
Возвращаются только активные кафе
```

**Решение:** Изменить endpoint на `/cafes?active_only=false` для менеджерской панели.

## Решение

### Фикс 1: Исправить endpoint для менеджерской панели

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts`

**Текущий код (строка 40-42):**
```typescript
const { data, error, isLoading, mutate } = useSWR<Cafe[]>(
  shouldFetch ? `/cafes${activeOnly ? "?active_only=true" : ""}` : null,
  fetcher
);
```

**Исправленный код:**
```typescript
const { data, error, isLoading, mutate } = useSWR<Cafe[]>(
  shouldFetch
    ? `/cafes?active_only=${activeOnly ? "true" : "false"}`
    : null,
  fetcher
);
```

**Обоснование:**
- Теперь явно передаём `?active_only=false` для менеджеров
- Backend корректно интерпретирует query параметр
- SWR cache key будет `/cafes?active_only=false` для менеджерской панели

### Фикс 2: Исправить mutate() после изменений

**Файл:** `frontend_mini_app/src/components/Manager/CafeList.tsx`

**Текущий код (строка 26):**
```typescript
mutate("/cafes");
```

**Исправленный код:**
```typescript
mutate("/cafes?active_only=false");
```

**Альтернативный подход (более универсальный):**

Использовать SWR matcher для обновления всех ключей, начинающихся с `/cafes`:

```typescript
mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
```

**Обоснование:**
- Обновит все кэши, связанные с `/cafes` (с разными query параметрами)
- Избегает проблем с несовпадением ключей
- Аналогично используется в других hooks (см. `useUpdateCafeStatus` в hooks.ts:446)

### Фикс 3: Проверить кнопки (если проблема сохранится)

Если после фикса 1-2 кнопки всё ещё не работают, проверить:

1. **CSS pointer-events:**
   - Убедиться что `.bg-white/5` или другие overlay не блокируют клики
   - Проверить z-index для кнопок

2. **processingId logic:**
   - Убедиться что `disabled={processingId === cafe.id}` работает корректно
   - Проверить что processingId сбрасывается в finally

3. **React event bubbling:**
   - Убедиться что onClick не блокируется stopPropagation

## План действий для Coder

1. **Обновить `useCafes` hook:**
   - Изменить endpoint на `/cafes?active_only=${activeOnly ? "true" : "false"}`
   - Убедиться что SWR cache key корректный

2. **Обновить `handleToggleStatus` в CafeList:**
   - Заменить `mutate("/cafes")` на `mutate((key) => key.startsWith("/cafes"))`
   - Добавить revalidate option если нужно

3. **Обновить `handleDelete` в CafeList:**
   - Аналогично заменить `mutate("/cafes")` на matcher

4. **Проверить другие места использования `mutate("/cafes")`:**
   - `CafeForm.tsx` (строка 64)
   - Обновить аналогичным образом

5. **Тестирование:**
   - Проверить что деактивированные кафе остаются в списке
   - Проверить что кнопки работают
   - Проверить что UI обновляется после операций

## Затронутые файлы

| Файл | Действие |
|------|----------|
| `frontend_mini_app/src/lib/api/hooks.ts` | Исправить: `useCafes` hook — изменить endpoint на `/cafes?active_only=false` |
| `frontend_mini_app/src/components/Manager/CafeList.tsx` | Исправить: `mutate` вызовы — использовать matcher вместо статичного ключа |
| `frontend_mini_app/src/components/Manager/CafeForm.tsx` | Исправить: `mutate` вызов — использовать matcher |

## Тесты

После фикса проверить:

1. **Менеджерская панель → вкладка "Кафе":**
   - Загружаются все кафе (активные и неактивные)
   - Кнопка "Редактировать" открывает форму
   - Кнопка "Деактивировать" меняет статус на неактивно
   - Кафе остаётся в списке с badge "Неактивно"
   - Кнопка меняется на "Активировать"
   - Кнопка "Активировать" возвращает статус на активно
   - Кнопка "Удалить" удаляет кафе после подтверждения

2. **Обычная страница пользователя (`/`):**
   - Загружаются только активные кафе
   - Неактивные кафе не показываются

## Приоритет

**High** — критичный bug для менеджерской панели, блокирует управление кафе.

## Оценка сложности

**Low:**
- Изменение endpoint в одном hook
- Замена нескольких `mutate()` вызовов
- Тестирование UI

**Ориентировочное время:** 30 минут - 1 час (включая тестирование).

## Примечания

Этот bug является примером классической проблемы с SWR cache key mismatch:
- Frontend запрашивает данные с одним ключом (`/cafes`)
- Backend возвращает данные на основе query параметров
- После мутации SWR перезапрашивает с тем же ключом
- Но backend интерпретирует отсутствие query как default значение
- Результат: данные не соответствуют ожиданиям

**Решение:** Всегда явно указывать query параметры в SWR ключах.
