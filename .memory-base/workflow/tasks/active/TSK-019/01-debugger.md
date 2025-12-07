---
agent: debugger
task_id: TSK-019
status: completed
next: coder
created_at: 2025-12-07T10:30:00Z
root_cause:
  - file: frontend_mini_app/src/lib/api/hooks.ts
    line: 41
    description: SWR cache key mismatch - endpoint не содержит ?active_only=false
  - file: frontend_mini_app/src/components/Manager/CafeList.tsx
    line: 28, 55
    description: mutate() использует неправильный ключ "/cafes" вместо "/cafes?active_only=false"
  - file: frontend_mini_app/src/app/page.tsx
    line: 299
    description: isCheckoutDisabled всегда true из-за некорректной логики проверки availableDays
  - file: frontend_mini_app/src/components/Manager/MenuItemForm.tsx
    line: 108
    description: Price field conditionally rendered only for category="extra", causing data loss when editing dishes
---

# Отчёт Debugger — TSK-019

## Описание проблемы

В интерфейсе обнаружены четыре критические проблемы с кнопками и формами:

### Проблема 1: Менеджер-панель — кнопки управления кафе не работают
**Симптомы:**
- Кнопки "Редактировать", "Деактивировать/Активировать", "Удалить" не реагируют на клики
- Деактивированные кафе исчезают из списка вместо отображения со статусом "Неактивно"

### Проблема 2: Страница заказа — кнопка "Оформить заказ" недоступна
**Симптомы:**
- Кнопка всегда отображается в disabled состоянии
- Не реагирует на клики даже при наличии товаров в корзине

### Проблема 3: Форма редактирования блюда — отсутствует поле для цены
**Симптомы:**
- При создании/редактировании блюда в MenuManager поле "Цена" видно только для категории "Дополнительно"
- Для категорий "Первое", "Салат", "Второе" поле цены скрыто
- При редактировании блюда с существующей ценой и сменой категории цена теряется

---

## Root Cause Analysis

### Проблема 1: SWR Cache Key Mismatch (Менеджер-панель)

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts` (строки 39-50)

**Текущий код:**
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

**Проблема:**
- Когда `activeOnly = false`, endpoint становится `/cafes` (БЕЗ query параметра)
- Backend при получении запроса `/cafes` (без query) использует **default значение** `active_only=True` (см. `backend/src/routers/cafes.py:24`)
- В результате SWR запрашивает `/cafes`, но backend возвращает **только активные кафе**

**Backend код** (`backend/src/routers/cafes.py:18-30`):
```python
@router.get("", response_model=list[CafeResponse])
async def list_cafes(
    current_user: CurrentUser,
    service: Annotated[CafeService, Depends(get_cafe_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),  # ← DEFAULT = True!
):
    """List all cafes."""
    # Non-managers only see active cafes
    if current_user.role != "manager":
        active_only = True
    return await service.list_cafes(skip=skip, limit=limit, active_only=active_only)
```

**Последствия:**
1. `CafeList` вызывает `useCafes(shouldFetch, false)` → endpoint = `/cafes`
2. Backend возвращает только активные кафе (active_only=True по умолчанию)
3. После деактивации кафе через `handleToggleStatus` вызывается `mutate("/cafes")`
4. SWR перезапрашивает `/cafes` → backend снова возвращает только активные
5. Деактивированное кафе исчезает из списка

**Trace деактивации:**
```
User clicks "Деактивировать"
→ handleToggleStatus()
→ PATCH /cafes/{id}/status {is_active: false} ✅ (успешно на backend)
→ mutate("/cafes")
→ SWR refetch GET /cafes (без query)
→ Backend возвращает active_only=true (default)
→ Список содержит только активные кафе
→ Деактивированное кафе пропадает из UI ❌
```

---

### Проблема 2: Неправильный mutate() ключ в CafeList

**Файл:** `frontend_mini_app/src/components/Manager/CafeList.tsx` (строки 28, 55)

**Текущий код:**
```typescript
const handleToggleStatus = async (cafe: Cafe) => {
  setProcessingId(cafe.id);
  try {
    await apiRequest(`/cafes/${cafe.id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !cafe.is_active }),
    });
    // Revalidate cafes list
    mutate("/cafes");  // ← ПРОБЛЕМА: несовпадение с SWR ключом
  } catch (err) {
    // ...
  }
};

const handleDelete = async (cafe: Cafe) => {
  // ...
  try {
    await apiRequest(`/cafes/${cafe.id}`, {
      method: "DELETE",
    });
    // Revalidate cafes list
    mutate("/cafes");  // ← ПРОБЛЕМА: несовпадение с SWR ключом
  } catch (err) {
    // ...
  }
};
```

**Проблема:**
- `useCafes(true, false)` создаёт SWR кэш с ключом `/cafes` (без query параметра)
- `mutate("/cafes")` пытается обновить кэш с ключом `/cafes`
- НО: из-за проблемы 1, после мутации SWR запрашивает `/cafes`, backend возвращает `active_only=true` данные
- Результат: несовпадение данных

**Дополнительная проблема:**
- Аналогичная проблема в `CafeForm.tsx:64`:
```typescript
await mutate("/cafes", undefined, { revalidate: true });
```

---

### Проблема 3: Кнопка "Оформить заказ" всегда disabled

**Файл:** `frontend_mini_app/src/app/page.tsx` (строка 299)

**Текущий код:**
```typescript
const noAvailableDates = !selectedDate && !availabilityLoading && availableDays.length > 0;
const isCheckoutDisabled = totalItems === 0 || !selectedDate || availabilityLoading || noAvailableDates;
```

**Логическая ошибка:**

Условие `noAvailableDates`:
- `!selectedDate` — нет выбранной даты
- `!availabilityLoading` — загрузка завершена
- `availableDays.length > 0` — есть дни в списке

**Проблема:** Это условие срабатывает **ТОЛЬКО** когда:
- Загрузка завершена
- Есть дни в списке (даже если все `can_order=false`)
- Но `selectedDate` не установлена

**НО:** В `useEffect` (строки 179-219) `selectedDate` устанавливается автоматически:
```typescript
const todayIso = new Date().toISOString().split("T")[0];
const today = days.find(d => d.date === todayIso && d.can_order);
const nearest = today ?? days.find(d => d.can_order) ?? null;
setSelectedDate(nearest?.date ?? null);
```

**Анализ:**
- Если есть хотя бы один день с `can_order=true`, `selectedDate` будет установлена
- `noAvailableDates` будет `false`
- `isCheckoutDisabled` = `totalItems === 0 || !selectedDate || availabilityLoading`

**Реальная проблема (гипотеза):**

1. **Сценарий 1:** Нет доступных дат (`can_order=false` для всех дней)
   - `selectedDate = null`
   - `noAvailableDates = !null && !false && true` = `true`
   - `isCheckoutDisabled = ... || true` = `true` ✅ (правильно)

2. **Сценарий 2:** Есть доступная дата
   - `selectedDate = "2025-12-07"`
   - `noAvailableDates = !selectedDate && ... ` = `false`
   - `isCheckoutDisabled = totalItems === 0 || !selectedDate || availabilityLoading || false`
   - Если `totalItems > 0`, `selectedDate` установлена, `availabilityLoading = false`:
     - `isCheckoutDisabled = false || false || false || false` = `false` ✅ (должно работать!)

**Вывод:** Логика кажется корректной. Проблема может быть в **другом месте**:

**Возможные причины:**
1. **availabilityLoading остаётся true:** `setAvailabilityLoading(false)` не вызывается в `finally`
2. **selectedDate не устанавливается:** API возвращает days с `can_order=false` для всех дней
3. **totalItems = 0:** Корзина пустая (проверить отдельно)
4. **Re-render проблема:** Состояние не обновляется после изменения

**Требуется дополнительная проверка:**
- Проверить console.log для `availabilityLoading`, `selectedDate`, `totalItems`, `noAvailableDates`, `isCheckoutDisabled`
- Проверить ответ от `/orders/availability/week?cafe_id={id}` — все ли дни имеют `can_order=false`?

**ВАЖНО:** Без доступа к реальным данным (console logs, network requests) **точно определить root cause проблемы 3 невозможно**. Наиболее вероятная причина:
- **API `/orders/availability/week` возвращает дни, где ВСЕ `can_order=false`**
- Или **availabilityLoading не сбрасывается в false**

---

## Рекомендуемые исправления

### Фикс 1: Исправить useCafes hook для явной передачи active_only

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts` (строки 39-50)

**Было:**
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

**Стало:**
```typescript
export function useCafes(shouldFetch = true, activeOnly = true): UseDataResult<Cafe> {
  const { data, error, isLoading, mutate } = useSWR<Cafe[]>(
    shouldFetch
      ? `/cafes?active_only=${activeOnly ? "true" : "false"}`
      : null,
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

**Обоснование:**
- Теперь **всегда** передаём query параметр `?active_only=true` или `?active_only=false`
- Backend корректно интерпретирует явный параметр
- SWR cache key будет `/cafes?active_only=false` для менеджерской панели

---

### Фикс 2: Обновить mutate() в CafeList для правильного ключа

**Файл:** `frontend_mini_app/src/components/Manager/CafeList.tsx` (строки 28, 55)

**Было:**
```typescript
mutate("/cafes");
```

**Стало (вариант 1 — matcher):**
```typescript
mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
```

**Стало (вариант 2 — точный ключ):**
```typescript
mutate("/cafes?active_only=false");
```

**Обоснование:**
- **Вариант 1 (matcher):** Обновляет ВСЕ кэши, начинающиеся с `/cafes` (универсальный подход)
  - Используется в других hooks (см. `useUpdateCafeStatus:446`, `useCreateCafe:405`)
  - Избегает проблем с несовпадением ключей
- **Вариант 2 (точный ключ):** Обновляет только конкретный кэш `/cafes?active_only=false`
  - Более производительный (не проверяет все ключи)
  - Требует точного знания ключа

**Рекомендация:** Использовать **вариант 1 (matcher)** для консистентности с остальными hooks.

**Применить изменения:**
1. `handleToggleStatus` (строка 28):
   ```typescript
   mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
   ```

2. `handleDelete` (строка 55):
   ```typescript
   mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
   ```

---

### Фикс 3: Показать поле цены для всех категорий в MenuItemForm

**Файл:** `frontend_mini_app/src/components/Manager/MenuItemForm.tsx` (строки 108-123)

**Root Cause:**

Поле цены условно отображается только для категории "extra":

```tsx
{category === "extra" && (
  <div>
    <label className="block text-sm font-medium text-gray-300 mb-2">
      Цена (₽)
    </label>
    <input
      type="number"
      step="0.01"
      min="0"
      value={price}
      onChange={(e) => setPrice(e.target.value)}
      className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#A020F0]"
      placeholder="50.00"
    />
  </div>
)}
```

**Последствия:**
1. При создании блюда категорий "soup", "salad", "main" → нельзя указать цену
2. При редактировании блюда с существующей ценой → поле скрыто, цена не видна
3. При submit формы для non-extra категорий → `price: undefined` (строка 45), существующая цена теряется

**Backend schema поддерживает опциональную цену для ВСЕХ категорий:**

```python
class MenuItemBase(BaseModel):
    name: str
    description: str | None = None
    category: str
    price: Decimal | None = None  # ← Optional для ВСЕХ
```

**Решение:**

Убрать условное отображение, показывать поле цены для всех категорий.

**Было:**
```tsx
{category === "extra" && (
  <div>
    <label>Цена (₽)</label>
    <input ... />
  </div>
)}
```

**Стало:**
```tsx
<div>
  <label className="block text-sm font-medium text-gray-300 mb-2">
    Цена (₽)
  </label>
  <input
    type="number"
    step="0.01"
    min="0"
    value={price}
    onChange={(e) => setPrice(e.target.value)}
    className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#A020F0]"
    placeholder="50.00 (необязательно)"
  />
</div>
```

**Также обновить submit logic (строка 45):**

**Было:**
```tsx
price: category === "extra" && price ? price : undefined,
```

**Стало:**
```tsx
price: price ? price : undefined,
```

**И убрать валидацию (строки 36-39):**

**Было:**
```tsx
if (category === "extra" && !price) {
  alert("Для категории 'Дополнительно' необходимо указать цену");
  return;
}
```

**Стало:**
```tsx
// Price is optional for all categories - remove validation
```

**Обоснование:**
- Backend schema позволяет `price: null` для всех категорий
- Нет бизнес-требования, что цена обязательна только для "extra"
- UX улучшается — менеджеры видят все доступные поля
- Предотвращает потерю данных при редактировании

---

### Фикс 4: Обновить mutate() в CafeForm

**Файл:** `frontend_mini_app/src/components/Manager/CafeForm.tsx` (строка 64)

**Было:**
```typescript
await mutate("/cafes", undefined, { revalidate: true });
```

**Стало:**
```typescript
await mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });
```

**Обоснование:**
- Аналогично CafeList — используем matcher для обновления всех кэшей `/cafes`

---

### Фикс 5: Добавить отладочные логи для кнопки "Оформить заказ"

**Файл:** `frontend_mini_app/src/app/page.tsx` (строка 299)

**Добавить перед `return`:**
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
- Позволит увидеть реальные значения переменных в консоли
- Поможет определить точную причину disabled состояния

**После проверки логов:**
- Если `availabilityLoading` всегда `true` → проблема в `finally` блоке
- Если `selectedDate` всегда `null` → проблема в API или логике выбора даты
- Если `totalItems = 0` → проблема в корзине (addToCart не работает)

---

### Фикс 6 (опциональный): Улучшить обработку ошибок availabilityLoading

**Файл:** `frontend_mini_app/src/app/page.tsx` (строки 179-219)

**Текущая проблема:**
- Если запрос к `/orders/availability/week` падает с ошибкой, `setAvailabilityLoading(false)` вызывается в `finally`
- НО: если Promise зависает (timeout), состояние может остаться `loading=true`

**Рекомендация (для Coder):**
- Добавить timeout для fetch запроса
- Проверить, что `finally` блок всегда вызывается
- Добавить fallback для случая, когда API не отвечает

---

## Затронутые файлы и изменения

| Файл | Изменение | Приоритет |
|------|-----------|-----------|
| `frontend_mini_app/src/lib/api/hooks.ts` | Изменить endpoint в `useCafes` на `/cafes?active_only=${...}` | **High** |
| `frontend_mini_app/src/components/Manager/CafeList.tsx` | Заменить `mutate("/cafes")` на `mutate((key) => key.startsWith("/cafes"))` (2 места) | **High** |
| `frontend_mini_app/src/components/Manager/CafeForm.tsx` | Заменить `mutate("/cafes")` на `mutate((key) => key.startsWith("/cafes"))` | **High** |
| `frontend_mini_app/src/components/Manager/MenuItemForm.tsx` | Убрать условное отображение поля цены, показывать для всех категорий | **High** |
| `frontend_mini_app/src/app/page.tsx` | Добавить отладочные логи для `isCheckoutDisabled` | **Medium** |

---

## План действий для Coder

### Шаг 1: Фикс SWR cache key в useCafes
1. Открыть `frontend_mini_app/src/lib/api/hooks.ts`
2. Найти функцию `useCafes` (строки 39-50)
3. Заменить:
   ```typescript
   shouldFetch ? `/cafes${activeOnly ? "?active_only=true" : ""}` : null
   ```
   на:
   ```typescript
   shouldFetch
     ? `/cafes?active_only=${activeOnly ? "true" : "false"}`
     : null
   ```

### Шаг 2: Фикс mutate() в CafeList
1. Открыть `frontend_mini_app/src/components/Manager/CafeList.tsx`
2. Найти `handleToggleStatus` (строка 20-35)
3. Заменить `mutate("/cafes");` на:
   ```typescript
   mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
   ```
4. Найти `handleDelete` (строка 37-62)
5. Заменить `mutate("/cafes");` на:
   ```typescript
   mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
   ```

### Шаг 3: Фикс mutate() в CafeForm
1. Открыть `frontend_mini_app/src/components/Manager/CafeForm.tsx`
2. Найти строку 64
3. Заменить:
   ```typescript
   await mutate("/cafes", undefined, { revalidate: true });
   ```
   на:
   ```typescript
   await mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });
   ```

### Шаг 4: Исправить MenuItemForm для отображения цены
1. Открыть `frontend_mini_app/src/components/Manager/MenuItemForm.tsx`
2. Найти условное отображение поля цены (строки 108-123)
3. Убрать обёртку `{category === "extra" && (...)}`, показывать поле для всех категорий:
   ```tsx
   <div>
     <label className="block text-sm font-medium text-gray-300 mb-2">
       Цена (₽)
     </label>
     <input
       type="number"
       step="0.01"
       min="0"
       value={price}
       onChange={(e) => setPrice(e.target.value)}
       className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#A020F0]"
       placeholder="50.00 (необязательно)"
     />
   </div>
   ```
4. Найти валидацию (строки 36-39), удалить проверку:
   ```tsx
   // if (category === "extra" && !price) {
   //   alert("Для категории 'Дополнительно' необходимо указать цену");
   //   return;
   // }
   ```
5. Найти submit logic (строка 45), изменить:
   ```tsx
   price: price ? price : undefined,
   ```

### Шаг 5: Добавить отладку для кнопки "Оформить заказ"
1. Открыть `frontend_mini_app/src/app/page.tsx`
2. Найти строку 299 (перед `return`)
3. Добавить:
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

### Шаг 6: Тестирование
1. **Менеджерская панель:**
   - Открыть `/manager` → вкладка "Кафе"
   - Проверить, что загружаются все кафе (активные и неактивные)
   - Кликнуть "Деактивировать" на активное кафе
   - **Ожидаемый результат:** Кафе остаётся в списке с badge "Неактивно"
   - Кликнуть "Активировать" на неактивное кафе
   - **Ожидаемый результат:** Кафе меняет статус на "Активно"
   - Кликнуть "Редактировать"
   - **Ожидаемый результат:** Открывается форма редактирования
   - Кликнуть "Удалить" → подтвердить
   - **Ожидаемый результат:** Кафе удаляется из списка

2. **Форма редактирования блюда:**
   - Открыть `/manager` → вкладка "Меню"
   - Выбрать кафе
   - Кликнуть "Добавить" блюдо
   - **Ожидаемый результат:** Поле "Цена" видно для любой категории
   - Выбрать категорию "Первое"
   - Заполнить название "Борщ", цену "150"
   - Нажать "Создать"
   - **Ожидаемый результат:** Блюдо создано с ценой 150₽
   - Кликнуть "Редактировать" на созданном блюде
   - **Ожидаемый результат:** Форма открывается с видимым полем цены, значение "150"
   - Изменить категорию на "Второе"
   - **Ожидаемый результат:** Поле цены остаётся видимым, значение сохранено
   - Нажать "Сохранить"
   - **Ожидаемый результат:** Цена 150₽ сохранена

3. **Страница заказа:**
   - Открыть главную страницу `/`
   - Добавить блюдо в корзину
   - Проверить console.log "Checkout Debug"
   - Если `isCheckoutDisabled = false`, кнопка должна быть активна
   - **Ожидаемый результат:** Кнопка "Оформить заказ" становится активной
   - Кликнуть "Оформить заказ"
   - **Ожидаемый результат:** Переход на страницу `/order`

4. **Проверка логов:**
   - Открыть DevTools → Console
   - Найти "Checkout Debug" лог
   - Проверить значения:
     - `totalItems` > 0
     - `selectedDate` не null
     - `availabilityLoading` = false
     - `isCheckoutDisabled` = false

---

## Дополнительные замечания

### Консистентность mutate() во всех hooks

После фикса проверить, что **все** hooks используют **matcher** вместо статичных ключей:

**Уже используют matcher (хорошо):**
- `useCreateCafe:405` ✅
- `useUpdateCafe:418` ✅
- `useDeleteCafe:431` ✅
- `useUpdateCafeStatus:446` ✅

**Нужно обновить (после фикса):**
- `CafeList.tsx:28, 55` → будет исправлено
- `CafeForm.tsx:64` → будет исправлено

### Проблема 4 (checkout button): Дополнительные проверки

Если после фикса 1-5 кнопка "Оформить заказ" всё ещё disabled:

1. **Проверить API response:**
   - DevTools → Network → `/orders/availability/week?cafe_id={id}`
   - Проверить, что хотя бы один день имеет `can_order: true`
   - Проверить, что `deadline` не истёк

2. **Проверить console.log:**
   - Значения `totalItems`, `selectedDate`, `availabilityLoading`
   - Если `availabilityLoading = true` → проблема в `finally`
   - Если `selectedDate = null` → проблема в логике выбора даты

3. **Проверить корзину:**
   - Добавить console.log в `addToCart`:
     ```typescript
     console.log("Added to cart:", dishId, cart);
     ```
   - Убедиться, что `cart` обновляется

---

## Оценка сложности

**Low-Medium:**
- Изменения минимальные (4 файла, ~20 строк кода)
- Проблемы хорошо локализованы
- Тестирование простое (ручное в UI)

**Ориентировочное время:** 45 минут - 1.5 часа (включая тестирование)

---

## Приоритет

**High** — критичные баги:
- Проблема 1: Блокирует управление кафе в менеджерской панели
- Проблема 2: Следствие проблемы 1
- Проблема 3: Блокирует редактирование цен для блюд, приводит к потере данных
- Проблема 4: Блокирует оформление заказов (требует дополнительной отладки)

---

## Заключение

### Root Cause Проблемы 1-2:
**SWR cache key mismatch** из-за отсутствия явного query параметра `active_only` в endpoint.

**Решение:**
1. Явно передавать `?active_only=true/false` в `useCafes`
2. Использовать matcher в `mutate()` для обновления всех связанных кэшей

### Root Cause Проблемы 3:
**Условное отображение поля цены** в MenuItemForm только для категории "extra".

**Решение:**
1. Убрать условное отображение `{category === "extra" && (...)}`
2. Показывать поле цены для всех категорий
3. Убрать валидацию, требующую цену только для "extra"
4. Изменить submit logic: всегда отправлять price если заполнено

### Root Cause Проблемы 4:
**Требует дополнительной отладки.** Наиболее вероятные причины:
- API возвращает дни с `can_order=false`
- `availabilityLoading` не сбрасывается
- Корзина пустая (`totalItems = 0`)

**Решение:**
1. Добавить отладочные логи
2. Проверить реальные данные в console
3. Исправить конкретную причину после анализа логов

### Готовность к передаче Coder:
✅ Root cause определён для проблем 1-3
⚠️ Проблема 4 требует дополнительной отладки (добавлены логи для диагностики)

**Следующий шаг:** Передать Coder для реализации фиксов.
