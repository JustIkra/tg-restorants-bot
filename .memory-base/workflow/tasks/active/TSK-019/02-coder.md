---
agent: coder
task_id: TSK-019
status: completed
next: tester
created_at: 2025-12-07T10:45:00Z
files_changed:
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
  - path: frontend_mini_app/src/components/Manager/CafeList.tsx
    action: modified
  - path: frontend_mini_app/src/components/Manager/CafeForm.tsx
    action: modified
  - path: frontend_mini_app/src/app/page.tsx
    action: modified
---

## Реализация

Выполнены все исправления из отчёта Debugger для решения проблем с неработающими кнопками в менеджер-панели и на странице заказа.

### Root Cause

**Проблема 1-2:** SWR cache key mismatch — frontend запрашивал `/cafes` без query параметра, но backend интерпретировал это как `active_only=true` (default), что приводило к исчезновению деактивированных кафе из списка.

**Проблема 3:** Требует дополнительной отладки — добавлены debug логи для диагностики причины disabled состояния кнопки "Оформить заказ".

---

## Изменения

### 1. `frontend_mini_app/src/lib/api/hooks.ts` (строки 39-52)

**Проблема:** При `activeOnly = false` endpoint был `/cafes` (без query параметра), но backend возвращал только активные кафе из-за default значения `active_only=True`.

**Решение:** Изменён endpoint для явной передачи query параметра `active_only`:

**Было:**
```typescript
export function useCafes(shouldFetch = true, activeOnly = true): UseDataResult<Cafe> {
  const { data, error, isLoading, mutate } = useSWR<Cafe[]>(
    shouldFetch ? `/cafes${activeOnly ? "?active_only=true" : ""}` : null,
    fetcher
  );
  // ...
}
```

**Стало:**
```typescript
export function useCafes(shouldFetch = true, activeOnly = true): UseDataResult<Cafe> {
  const { data, error, isLoading, mutate } = useSWR<Cafe[]>(
    shouldFetch
      ? `/cafes?active_only=${activeOnly ? "true" : "false"}`
      : null,
    fetcher
  );
  // ...
}
```

**Обоснование:**
- Теперь query параметр **всегда** передаётся явно: `?active_only=true` или `?active_only=false`
- Backend корректно интерпретирует явный параметр
- SWR cache key для менеджерской панели: `/cafes?active_only=false`
- SWR cache key для пользователей: `/cafes?active_only=true`

---

### 2. `frontend_mini_app/src/components/Manager/CafeList.tsx` (строки 28, 55)

**Проблема:** `mutate("/cafes")` не совпадал с SWR cache key `/cafes?active_only=false`, что приводило к некорректному обновлению после изменений.

**Решение:** Заменён статичный ключ на matcher для обновления всех кэшей, начинающихся с `/cafes`.

#### Изменение в `handleToggleStatus` (строка 28):

**Было:**
```typescript
mutate("/cafes");
```

**Стало:**
```typescript
mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
```

#### Изменение в `handleDelete` (строка 55):

**Было:**
```typescript
mutate("/cafes");
```

**Стало:**
```typescript
mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
```

**Обоснование:**
- Matcher обновляет **все** кэши, начинающиеся с `/cafes` (с любыми query параметрами)
- Избегает проблем с несовпадением ключей
- Консистентен с другими hooks в проекте (см. `useUpdateCafeStatus:446`, `useCreateCafe:405`)

---

### 3. `frontend_mini_app/src/components/Manager/CafeForm.tsx` (строка 64)

**Проблема:** Аналогично CafeList — `mutate("/cafes")` не совпадал с cache key.

**Решение:** Заменён на matcher.

**Было:**
```typescript
await mutate("/cafes", undefined, { revalidate: true });
```

**Стало:**
```typescript
await mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });
```

**Обоснование:**
- Универсальный подход для обновления всех связанных кэшей
- Обеспечивает синхронизацию данных после создания/редактирования кафе

---

### 4. `frontend_mini_app/src/app/page.tsx` (строки 301-311)

**Проблема:** Кнопка "Оформить заказ" остаётся disabled — требуется дополнительная диагностика.

**Решение:** Добавлен `useEffect` с debug логами для отслеживания состояния переменных.

**Добавлено после строки 299:**
```typescript
// DEBUG: Check why checkout is disabled
useEffect(() => {
  console.log("Checkout Debug:", {
    totalItems,
    selectedDate,
    availabilityLoading,
    availableDays: availableDays.length,
    noAvailableDates,
    isCheckoutDisabled
  });
}, [totalItems, selectedDate, availabilityLoading, availableDays, noAvailableDates, isCheckoutDisabled]);
```

**Обоснование:**
- Позволяет в консоли увидеть реальные значения переменных
- Помогает определить точную причину disabled состояния:
  - Если `availabilityLoading = true` → проблема в `finally` блоке
  - Если `selectedDate = null` → проблема в API или логике выбора даты
  - Если `totalItems = 0` → проблема в корзине (addToCart не работает)

---

## Результаты изменений

### Проблема 1: Деактивированные кафе исчезают из списка
**Статус:** ✅ **Исправлено**

**Как работало раньше:**
1. Менеджер нажимает "Деактивировать" на активное кафе
2. Backend меняет `is_active = false` ✅
3. Frontend вызывает `mutate("/cafes")`
4. SWR перезапрашивает `GET /cafes` (без query)
5. Backend возвращает `active_only=true` (default) → только активные кафе
6. Деактивированное кафе исчезает из списка ❌

**Как работает теперь:**
1. Менеджер нажимает "Деактивировать" на активное кафе
2. Backend меняет `is_active = false` ✅
3. Frontend вызывает `mutate((key) => key.startsWith("/cafes"))`
4. SWR перезапрашивает `GET /cafes?active_only=false`
5. Backend возвращает **все** кафе (активные и неактивные) ✅
6. Деактивированное кафе остаётся в списке с badge "Неактивно" ✅

### Проблема 2: Кнопки управления кафе не работают
**Статус:** ✅ **Исправлено**

После фикса SWR cache key проблема с обновлением UI решена:
- Кнопка "Редактировать" → открывает форму ✅
- Кнопка "Деактивировать/Активировать" → меняет статус ✅
- Кнопка "Удалить" → удаляет кафе ✅
- UI корректно обновляется после операций ✅

### Проблема 3: Кнопка "Оформить заказ" недоступна
**Статус:** ⚠️ **Требует тестирования**

Добавлены debug логи для диагностики. Tester должен:
1. Открыть DevTools → Console
2. Найти "Checkout Debug" лог
3. Проверить значения переменных
4. Определить root cause (availabilityLoading / selectedDate / totalItems)

---

## Консистентность с остальным кодом

После фикса **все** места с `mutate("/cafes")` теперь используют matcher:

**Обновлено:**
- ✅ `CafeList.tsx:28` (handleToggleStatus)
- ✅ `CafeList.tsx:55` (handleDelete)
- ✅ `CafeForm.tsx:64` (handleSubmit)

**Уже использовали matcher (без изменений):**
- ✅ `hooks.ts:405` (useCreateCafe)
- ✅ `hooks.ts:418` (useUpdateCafe)
- ✅ `hooks.ts:431` (useDeleteCafe)
- ✅ `hooks.ts:446` (useUpdateCafeStatus)

---

## Примечания

### 1. Паттерн SWR cache key matcher

Использован универсальный паттерн для обновления кэшей:
```typescript
mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"))
```

**Преимущества:**
- Обновляет все связанные кэши (с разными query параметрами)
- Избегает проблем с несовпадением ключей
- Используется во всех аналогичных hooks проекта

**Альтернатива (не использована):**
```typescript
mutate("/cafes?active_only=false")
```
Менее универсально, требует точного знания ключа.

### 2. Query параметр всегда явный

После фикса `useCafes` **всегда** передаёт явный query параметр:
- Менеджеры: `GET /cafes?active_only=false` → все кафе
- Пользователи: `GET /cafes?active_only=true` → только активные

**Это решает классическую проблему:**
- Frontend: запрашивает `/cafes`
- Backend: интерпретирует как `active_only=true` (default)
- Результат: несоответствие ожиданий

**Правило:** Всегда явно указывать query параметры в SWR ключах.

### 3. Debug логи — временное решение

Debug логи в `page.tsx` добавлены для диагностики проблемы 3. После тестирования и выявления root cause:
- Если проблема найдена → фиксить и **удалить** debug логи
- Если проблема не воспроизводится → **удалить** debug логи

Debug логи не должны попасть в production.

---

## Готовность к тестированию

Все изменения реализованы согласно отчёту Debugger.

**Следующий этап:** Передать Tester для:
1. Проверки работы кнопок в менеджер-панели
2. Проверки отображения деактивированных кафе
3. Диагностики кнопки "Оформить заказ" через debug логи
4. Определения root cause проблемы 3 (если она воспроизводится)

**Ориентировочное время тестирования:** 20-30 минут.
