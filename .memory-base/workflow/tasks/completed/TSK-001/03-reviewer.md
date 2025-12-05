---
agent: reviewer
task_id: TSK-001
status: completed
next: coder
created_at: 2025-12-06T00:30:00
---

## Review Result: CHANGES REQUESTED

Проведен code review всех изменений TSK-001 (8 подзадач). Обнаружены критические и важные проблемы, требующие исправления.

---

## Critical Issues

### 1. TypeScript Compilation Error
**Файл:** `frontend_mini_app/src/lib/api/client.ts:52`

**Проблема:**
```typescript
headers["Authorization"] = `Bearer ${token}`;
```

**Ошибка:**
```
Type error: Element implicitly has an 'any' type because expression of type
'"Authorization"' can't be used to index type 'HeadersInit'.
Property 'Authorization' does not exist on type 'HeadersInit'.
```

**Решение:**
Использовать явное приведение типа или создать объект как `Record<string, string>`:

```typescript
const headers: Record<string, string> = {
  "Content-Type": "application/json",
};

if (token) {
  headers["Authorization"] = `Bearer ${token}`;
}

const config: RequestInit = {
  ...options,
  headers: {
    ...headers,
    ...options?.headers,
  },
};
```

**Impact:** Проект не компилируется. Блокирует deployment.

---

### 2. Missing Error Handling in Authentication Flow
**Файл:** `frontend_mini_app/src/app/page.tsx:46-53`

**Проблема:**
```typescript
authenticateWithTelegram(initData)
  .then(({ access_token }) => {
    setIsAuthenticated(true);
    localStorage.setItem("jwt_token", access_token);
  })
  .catch(err => {
    console.error("Auth failed:", err);
  });
```

Ошибка авторизации не отображается пользователю. Приложение продолжает работу без токена, что приведёт к ошибкам при попытках API запросов.

**Решение:**
Добавить отображение ошибки пользователю:
```typescript
.catch(err => {
  console.error("Auth failed:", err);
  alert("Ошибка авторизации. Пожалуйста, перезапустите приложение.");
  setIsAuthenticated(false);
});
```

**Impact:** Пользователи не понимают, почему не могут сделать заказ. Плохой UX.

---

### 3. Race Condition in Token Storage
**Файл:** `frontend_mini_app/src/app/page.tsx:49` + `frontend_mini_app/src/lib/api/client.ts:124`

**Проблема:**
Токен сохраняется дважды:
1. В `client.ts:124` через `setToken(response.access_token)`
2. В `page.tsx:49` через `localStorage.setItem("jwt_token", access_token)`

Это избыточно и может привести к race condition если использовать разные ключи.

**Решение:**
Убрать дублирование в `page.tsx:49`:
```typescript
authenticateWithTelegram(initData)
  .then(({ access_token }) => {
    setIsAuthenticated(true);
    // Токен уже сохранён в authenticateWithTelegram
  })
```

**Impact:** Средний. Код избыточен, но работает корректно (пока используется один ключ).

---

## Important Issues

### 4. Missing null/undefined Checks in OrderSummary
**Файл:** `frontend_mini_app/src/components/OrderSummary/OrderSummary.tsx`

**Проблема:**
Компонент не используется в `page.tsx` (создан inline вариант в строках 256-306), но в нём есть потенциальные проблемы:
- Отсутствует проверка `extra.price !== null` при расчёте `subtotal`

**Решение:**
Если компонент будет использоваться, добавить проверки:
```typescript
{extra.price !== null && (
  <p className="text-white font-semibold text-base mt-2">{extra.price} ₽</p>
)}
```

**Примечание:** Компонент не используется, но создан согласно архитектуре. Можно удалить или исправить при будущем рефакторинге.

**Impact:** Низкий. Компонент не используется в текущей реализации.

---

### 5. Inconsistent Date Format
**Файл:** `frontend_mini_app/src/app/page.tsx:110`

**Проблема:**
```typescript
order_date: new Date().toISOString().split("T")[0], // YYYY-MM-DD
```

Используется текущая дата, но согласно бизнес-логике, заказы делаются на следующий день до 12:00.

**Решение:**
Уточнить у человека логику выбора даты заказа. Возможно нужно:
```typescript
// Завтра
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
order_date: tomorrow.toISOString().split("T")[0]
```

Или добавить UI для выбора даты.

**Impact:** Средний. Может привести к некорректным заказам если deadline уже прошёл.

---

### 6. Missing Loading States
**Файлы:** `frontend_mini_app/src/app/page.tsx`

**Проблема:**
Отсутствуют loading states для данных:
- `combos` может быть `undefined` во время загрузки
- `menuItems` может быть `undefined` во время загрузки
- `extras` может быть `undefined` во время загрузки

Компоненты отображаются только при `data !== undefined`, но нет индикации загрузки.

**Решение:**
Добавить loading states:
```tsx
{selectedCafe && (
  <div className="px-4 md:px-6 pb-4">
    <h2 className="text-white text-base md:text-lg font-semibold mb-3">Выберите комбо</h2>
    {combos ? (
      <ComboSelector combos={combos} ... />
    ) : (
      <div className="text-gray-300">Загрузка комбо...</div>
    )}
  </div>
)}
```

**Impact:** Средний. Пользователи не видят обратную связь при медленной загрузке.

---

### 7. No Validation for Empty Categories in Menu
**Файл:** `frontend_mini_app/src/app/page.tsx:207-219`

**Проблема:**
```typescript
{selectedCombo.categories.map(category => {
  const categoryItems = menuItems.filter(item => item.category === category);
  return (
    <MenuSection
      key={category}
      category={category}
      categoryLabel={categoryLabels[category] || category}
      items={categoryItems}
      ...
    />
  );
})}
```

Если для категории нет блюд (`categoryItems.length === 0`), секция всё равно отображается пустой.

**Решение:**
Добавить проверку:
```typescript
{selectedCombo.categories.map(category => {
  const categoryItems = menuItems.filter(item => item.category === category);
  if (categoryItems.length === 0) return null;
  return <MenuSection ... />;
})}
```

**Impact:** Средний. Пустые секции ухудшают UX.

---

## Suggestions (не критично)

### 8. Duplicate OrderSummary Component
**Файлы:**
- `frontend_mini_app/src/components/OrderSummary/OrderSummary.tsx` (создан, не используется)
- `frontend_mini_app/src/app/page.tsx:241-308` (inline реализация)

**Проблема:**
Создан компонент `OrderSummary`, но в `page.tsx` используется inline вариант с другой вёрсткой.

**Решение:**
Либо использовать созданный компонент, либо удалить его.

**Impact:** Низкий. Мёртвый код, но не влияет на работу.

---

### 9. Alert() для Feedback
**Файл:** `frontend_mini_app/src/app/page.tsx:124, 128`

**Проблема:**
```typescript
alert(`Заказ №${order.id} оформлен!`);
alert(`Ошибка: ${errorMessage}`);
```

Нативные `alert()` выглядят устаревшими. Лучше использовать toast notifications или custom modal.

**Решение:**
Добавить библиотеку для toast (например, `react-hot-toast`) или создать custom notification компонент.

**Impact:** Низкий. UX можно улучшить, но функционал работает.

---

### 10. Missing TypeScript strict null checks
**Файл:** `frontend_mini_app/src/app/page.tsx`

**Проблема:**
Много проверок на `?? null`, `|| 0`, `|| ""` для обработки `undefined`.

**Решение:**
Убедиться что в `tsconfig.json` включен `strict: true` и `strictNullChecks: true`. Это уже сделано, хорошо.

**Impact:** Нет. Код корректен.

---

## Code Style Compliance

### ✅ Соответствует стандартам:
- **TypeScript strict mode** — все типы явно определены
- **"use client"** директивы — корректно использованы
- **Functional components** — все компоненты функциональные
- **Двойные кавычки** — используются
- **Tailwind CSS** — следует дизайн-системе проекта
- **Import paths** — корректные (`@/` alias)
- **Naming conventions** — camelCase для переменных, PascalCase для компонентов

### ✅ Архитектура:
- API клиент реализован согласно `01-architect.md`
- Все компоненты соответствуют спецификации
- State management корректен
- SWR хуки правильно используются

### ✅ Безопасность:
- JWT токен корректно передаётся в заголовках
- SSR safety проверки присутствуют (`typeof window`)
- Нет SQL injection (используется ORM на backend)
- Нет XSS (React экранирует по умолчанию)

---

## Performance

### ✅ Хорошие практики:
- SWR автоматический кэш
- Conditional fetching (`cafeId ? endpoint : null`)
- Минимальные re-renders (useState корректно используется)

### ⚠️ Потенциальные улучшения:
- Добавить `React.memo` для `MenuSection`, `ExtrasSection` если списки большие
- Добавить `useMemo` для `extrasTotal` расчёта
- Добавить debounce для кнопок add/remove в extras

---

## Проверка файлов

### Созданные файлы:
✅ `frontend_mini_app/src/lib/api/client.ts` — есть критическая ошибка
✅ `frontend_mini_app/src/lib/api/types.ts` — соответствует API spec
✅ `frontend_mini_app/src/lib/api/hooks.ts` — корректен
✅ `frontend_mini_app/src/lib/telegram/webapp.ts` — корректен
✅ `frontend_mini_app/src/components/ComboSelector/ComboSelector.tsx` — корректен
✅ `frontend_mini_app/src/components/ExtrasSection/ExtrasSection.tsx` — корректен
✅ `frontend_mini_app/src/components/OrderSummary/OrderSummary.tsx` — не используется

### Изменённые файлы:
✅ `frontend_mini_app/src/components/Menu/MenuSection.tsx` — корректен
✅ `frontend_mini_app/src/app/page.tsx` — есть важные проблемы
✅ `frontend_mini_app/package.json` — SWR добавлен

### Удалённые файлы:
✅ `frontend_mini_app/src/components/CategorySelector/CategorySelector.tsx` — корректно
✅ `frontend_mini_app/src/components/Cart/CartSummary.tsx` — корректно

---

## Acceptance Criteria Check

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| Авторизация через Telegram WebApp работает | ⚠️ | Работает, но нет feedback при ошибке |
| Список кафе загружается из API | ✅ | Корректно |
| Комбо-наборы отображаются с ценами | ✅ | Корректно |
| Выбор блюд по категориям работает (radio) | ✅ | Корректно |
| Дополнительные товары добавляются в заказ | ✅ | Корректно |
| Итоговая сумма считается корректно | ✅ | Корректно |
| Заказ отправляется на backend | ✅ | Корректно |
| Обрабатываются ошибки API | ⚠️ | Частично, нужен feedback для auth |
| Код соответствует code-style | ✅ | Соответствует |
| Нет TypeScript ошибок | ❌ | **Есть критическая ошибка** |

---

## Резюме

### Что сделано хорошо:
- Архитектура соответствует плану
- Все компоненты реализованы
- TypeScript типы определены корректно
- SWR интеграция правильная
- Telegram SDK обёрнут безопасно
- Дизайн соответствует проекту
- Код чистый и читаемый

### Что нужно исправить:

**Критические (блокируют deployment):**
1. TypeScript compilation error в `client.ts:52`

**Важные (ухудшают UX):**
2. Error handling в authentication flow
3. Race condition в token storage (устранить дублирование)
4. Missing date logic для `order_date`
5. Missing loading states
6. Validation для пустых категорий

**Рекомендации:**
7. Удалить неиспользуемый `OrderSummary.tsx` или использовать его
8. Заменить `alert()` на toast notifications

---

## Следующие шаги

1. **Coder** должен исправить **Critical Issues** (пункты 1-3)
2. **Coder** должен исправить **Important Issues** (пункты 4-7)
3. После исправлений — повторный review
4. При успешном review → **Tester** (написать тесты)
5. **DocWriter** (обновить документацию компонентов)

---

## Оценка

**Общая оценка:** 7/10

Отличная работа по архитектуре и реализации. Код чистый и следует стандартам. Но критическая ошибка компиляции и недостаточная обработка ошибок требуют исправления перед переходом к тестированию.

**Status:** `completed` (review завершён)
**Next:** `coder` (исправить Critical + Important issues)
