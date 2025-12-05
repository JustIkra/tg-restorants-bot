---
agent: reviewer
task_id: TSK-001
status: completed
next: coder
created_at: 2025-12-06T01:45:00
---

## Review Result: CHANGES REQUESTED

Повторный code review после исправлений от Coder (02-coder-fixes.md). Из 7 запрошенных fixes:
- **4 issues полностью исправлены**
- **3 issues частично исправлены или введены новые проблемы**
- **Обнаружены 5 новых TypeScript compilation errors** (блокируют deployment)

---

## Проверка исправлений из первого review

### ✅ Issue #1: TypeScript compilation error в client.ts — ИСПРАВЛЕНО

**Статус:** Полностью исправлено

**Что было сделано:**
- Изменён тип `headers` с `HeadersInit` на `Record<string, string>`
- Теперь TypeScript позволяет динамическое присвоение `headers["Authorization"]`

**Проверка:**
```typescript
// frontend_mini_app/src/lib/api/client.ts:45-52
const headers: Record<string, string> = {
  "Content-Type": "application/json",
};

if (token) {
  headers["Authorization"] = `Bearer ${token}`; // ✅ Works
}
```

**Вердикт:** Ошибка устранена. Код корректен.

---

### ✅ Issue #2: Missing error handling в auth flow — ИСПРАВЛЕНО

**Статус:** Полностью исправлено

**Что было сделано:**
- Добавлен `alert()` с понятным сообщением при ошибке авторизации
- Добавлен `setIsAuthenticated(false)` для корректного состояния

**Проверка:**
```typescript
// frontend_mini_app/src/app/page.tsx:50-54
.catch(err => {
  console.error("Auth failed:", err);
  alert("Ошибка авторизации. Пожалуйста, перезапустите приложение.");
  setIsAuthenticated(false);
});
```

**Вердикт:** Ошибка устранена. UX улучшен.

---

### ✅ Issue #3: Race condition в token storage — ИСПРАВЛЕНО

**Статус:** Полностью исправлено

**Что было сделано:**
- Удалено дублирование `localStorage.setItem("jwt_token", access_token)` из `page.tsx`
- Токен сохраняется только в функции `authenticateWithTelegram()` (client.ts:126)

**Проверка:**
```typescript
// frontend_mini_app/src/app/page.tsx:46-49
.then(() => {
  setIsAuthenticated(true);
  // Token is already saved in authenticateWithTelegram ✅
})
```

**Вердикт:** Дублирование устранено. Race condition исправлен.

---

### ✅ Issue #4: Incorrect order_date — ИСПРАВЛЕНО

**Статус:** Полностью исправлено

**Что было сделано:**
- Добавлено вычисление завтрашней даты
- Используется `tomorrow.setDate(tomorrow.getDate() + 1)`

**Проверка:**
```typescript
// frontend_mini_app/src/app/page.tsx:110-112
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
const orderDate = tomorrow.toISOString().split("T")[0]; // ✅ Tomorrow
```

**Вердикт:** Бизнес-логика исправлена. Заказы теперь создаются на следующий день.

---

### ⚠️ Issue #5: Missing loading states — ЧАСТИЧНО ИСПРАВЛЕНО

**Статус:** Частично исправлено

**Что было сделано:**
- Добавлены loading messages для `combos`, `menuItems`, `extras`

**Проблема:**
Loading states показываются корректно, но проверки работают только с `undefined`. Если API вернёт ошибку, компонент также покажет "Загрузка...", а не "Ошибка".

**Проверка:**
```tsx
// frontend_mini_app/src/app/page.tsx:202-210
{combos ? (
  <ComboSelector combos={combos} ... />
) : (
  <div className="text-gray-300">Загрузка комбо...</div>
)}
// ❌ Не обрабатывается error state
```

**Рекомендация:**
Использовать error из SWR hook:
```tsx
const { data: combos, error: combosError } = useCombos(selectedCafe?.id ?? null);

{combosError ? (
  <div className="text-red-400">Ошибка загрузки комбо</div>
) : combos ? (
  <ComboSelector combos={combos} ... />
) : (
  <div className="text-gray-300">Загрузка комбо...</div>
)}
```

**Вердикт:** Частично исправлено. Loading states есть, но нет error handling для API failures.

---

### ✅ Issue #6: Empty categories validation — ИСПРАВЛЕНО

**Статус:** Полностью исправлено

**Что было сделано:**
- Добавлена проверка `if (categoryItems.length === 0) return null;`

**Проверка:**
```tsx
// frontend_mini_app/src/app/page.tsx:218-222
selectedCombo.categories.map(category => {
  const categoryItems = menuItems.filter(item => item.category === category);
  if (categoryItems.length === 0) return null; // ✅
  return <MenuSection ... />;
})
```

**Вердикт:** Пустые категории больше не отображаются. UX улучшен.

---

### ✅ Issue #7: Unused OrderSummary component — ИСПРАВЛЕНО

**Статус:** Полностью исправлено

**Что было сделано:**
- Удалён файл `frontend_mini_app/src/components/OrderSummary/OrderSummary.tsx`
- Удалён неиспользуемый импорт

**Проверка:**
```bash
$ find frontend_mini_app -name "OrderSummary.tsx"
# No results ✅
```

**Вердикт:** Мёртвый код удалён.

---

## Новые критические проблемы

### ❌ Critical #1: TypeScript compilation errors в hooks.ts

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts:33, 49, 69, 131`

**Проблема:**
SWR hooks возвращают тип `SWRResponse<ListResponse<T>>`, но функции объявлены с типом возврата `SWRResponse<T[]>`. Это создаёт type incompatibility для `mutate` property.

**Ошибка компилятора:**
```
error TS2322: Type '{ data: Cafe[] | undefined; ... mutate: KeyedMutator<ListResponse<Cafe>>; ... }'
  is not assignable to type 'SWRResponse<Cafe[], Error, any>'.
  Types of property 'mutate' are incompatible.
```

**Root cause:**
Проблема в том, что:
1. useSWR возвращает `SWRResponse<ListResponse<T>>`
2. Мы распаковываем `data?.items` и возвращаем как `Cafe[]`
3. Но остальные поля (включая `mutate`) остаются от оригинального типа `ListResponse<T>`

**Решение:**
Вариант 1: Изменить return type на `SWRResponse<ListResponse<Cafe>>` и работать с `data?.items` в компоненте
Вариант 2: Создать кастомный return type без полного `SWRResponse`

**Рекомендуемое решение (Option 2):**
```typescript
// Кастомный тип для упрощённого API
interface UseDataResult<T> {
  data: T | undefined;
  error: Error | undefined;
  isLoading: boolean;
}

export function useCafes(activeOnly = true): UseDataResult<Cafe[]> {
  const endpoint = `/cafes${activeOnly ? "?active_only=true" : ""}`;
  const { data, error, isLoading } = useSWR<ListResponse<Cafe>, Error>(endpoint, fetcher);

  return {
    data: data?.items,
    error,
    isLoading,
  };
}
```

**Impact:** Критический. Проект **НЕ КОМПИЛИРУЕТСЯ**.

---

### ❌ Critical #2: TypeScript error в webapp.ts

**Файл:** `frontend_mini_app/src/lib/telegram/webapp.ts:102`

**Проблема:**
```typescript
MainButton.offClick(); // ❌ Expected 1 arguments, but got 0
```

Метод `offClick()` требует callback аргумент (тот же, что был передан в `onClick()`).

**Решение:**
Вариант 1: Сохранить ссылку на callback и передать в `offClick(callback)`
Вариант 2: Использовать `MainButton.hide()` без вызова `offClick()` (часто hide достаточно)

**Рекомендуемое решение (Option 1 - proper cleanup):**
```typescript
let currentCallback: (() => void) | null = null;

export function showMainButton(text: string, onClick: () => void): void {
  // ... SSR checks ...

  const MainButton = WebApp.MainButton;

  // Remove previous callback if exists
  if (currentCallback) {
    MainButton.offClick(currentCallback);
  }

  currentCallback = onClick;

  MainButton.setText(text);
  MainButton.show();
  MainButton.onClick(onClick);
}

export function hideMainButton(): void {
  // ... SSR checks ...

  const MainButton = WebApp.MainButton;
  MainButton.hide();

  if (currentCallback) {
    MainButton.offClick(currentCallback);
    currentCallback = null;
  }
}
```

**Impact:** Критический. Проект **НЕ КОМПИЛИРУЕТСЯ**.

---

## Резюме проверки

### Исправлено (7 issues из review #1):
✅ **Issue #1** — TypeScript error в client.ts (headers)
✅ **Issue #2** — Error handling в auth flow
✅ **Issue #3** — Race condition в token storage
✅ **Issue #4** — Order date (tomorrow)
⚠️ **Issue #5** — Loading states (частично, нет error states)
✅ **Issue #6** — Empty categories validation
✅ **Issue #7** — OrderSummary component удалён

### Новые проблемы (блокируют deployment):
❌ **Critical #1** — TypeScript compilation errors в hooks.ts (4 ошибки)
❌ **Critical #2** — TypeScript error в webapp.ts:102 (offClick)

---

## TypeScript компиляция

Запущен `npx tsc --noEmit`:

**Результат:** ❌ **5 ERRORS**

```
src/lib/api/hooks.ts(33,3): error TS2322
src/lib/api/hooks.ts(49,3): error TS2322
src/lib/api/hooks.ts(69,3): error TS2322
src/lib/api/hooks.ts(131,3): error TS2322
src/lib/telegram/webapp.ts(102,14): error TS2554
```

**Вердикт:** Проект **НЕ компилируется**. Deployment невозможен.

---

## Code Style Compliance

### ✅ Соответствует стандартам:
- **"use client"** директивы — корректно используются
- **Functional components** — все компоненты функциональные
- **Двойные кавычки** — используются
- **Tailwind CSS** — следует дизайн-системе проекта
- **Import paths** — корректные (`@/` alias)
- **Naming conventions** — camelCase для переменных, PascalCase для компонентов

### ✅ Архитектура:
- Все изменения соответствуют архитектуре от Architect
- State management корректен
- API интеграция правильная (если исправить TypeScript errors)

### ✅ Безопасность:
- JWT токен корректно передаётся
- SSR safety проверки присутствуют
- Нет security issues

---

## Acceptance Criteria Check

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| Авторизация через Telegram WebApp работает | ✅ | Корректно + error handling |
| Список кафе загружается из API | ✅ | Корректно |
| Комбо-наборы отображаются с ценами | ✅ | Корректно |
| Выбор блюд по категориям работает (radio) | ✅ | Корректно |
| Дополнительные товары добавляются в заказ | ✅ | Корректно |
| Итоговая сумма считается корректно | ✅ | Корректно |
| Заказ отправляется на backend | ✅ | Корректно |
| Обрабатываются ошибки API | ⚠️ | Auth errors — да. Loading errors — нет |
| Код соответствует code-style | ✅ | Соответствует |
| Нет TypeScript ошибок | ❌ | **5 TypeScript errors** |

---

## Что нужно исправить

### Критические (блокируют deployment):

**1. Исправить TypeScript errors в hooks.ts (4 ошибки)**
- Изменить return type на кастомный `UseDataResult<T>` вместо `SWRResponse<T[], Error>`
- Убрать type incompatibility между `ListResponse<T>` и `T[]`

**2. Исправить TypeScript error в webapp.ts:102**
- Добавить callback tracking для правильного вызова `offClick(callback)`
- Или упростить до `hide()` без cleanup

### Важные (улучшения UX):

**3. Добавить error states для SWR hooks**
- Показывать ошибки загрузки, а не бесконечный "Загрузка..."
- Использовать `error` из SWR response

---

## Следующие шаги

1. **Coder** должен исправить **Critical Issues #1-2** (TypeScript compilation)
2. **Coder** должен добавить **error handling** для loading states (Important #3)
3. После исправлений — **повторный review #3**
4. При успешной компиляции → **Tester** (написать тесты)

---

## Оценка

**Общая оценка:** 6/10

Отличная работа по исправлению 6 из 7 issues. Код стал значительно лучше (убран race condition, исправлена бизнес-логика, добавлены loading states). Но введены новые **критические TypeScript ошибки**, которые блокируют deployment.

Необходимо исправить compilation errors перед переходом к тестированию.

**Status:** `completed` (review завершён)
**Next:** `coder` (исправить TypeScript compilation errors)
