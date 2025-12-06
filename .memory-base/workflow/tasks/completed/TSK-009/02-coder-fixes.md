---
agent: coder
task_id: TSK-009
subtask: fixes
subtask_name: "Исправление замечаний Reviewer"
status: completed
next: reviewer
created_at: 2025-12-06T14:30:00Z
files_changed:
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
    description: "Добавлен JSON.stringify для всех mutation hooks"
  - path: frontend_mini_app/src/lib/api/client.ts
    action: modified
    description: "Улучшена обработка 403 ошибки с alert и редиректом"
  - path: frontend_mini_app/src/app/manager/page.tsx
    action: modified
    description: "Рефакторинг useEffect для избежания cascading renders"
  - path: frontend_mini_app/src/app/page.tsx
    action: modified
    description: "Рефакторинг useEffect для избежания cascading renders"
---

## Исправления замечаний Reviewer

Все критичные и некритичные замечания исправлены.

### 1. API hooks сериализация body (КРИТИЧНО)

**Проблема:** В mutation hooks передавались объекты напрямую в `apiRequest`, но нужен JSON string.

**Решение:** Добавлен `JSON.stringify()` для всех mutation hooks в `hooks.ts`:

- `useCreateUser`: `body: JSON.stringify(data)`
- `useUpdateUserAccess`: `body: JSON.stringify({ is_active })`
- `useCreateCafe`: `body: JSON.stringify(data)`
- `useUpdateCafe`: `body: JSON.stringify(data)`
- `useUpdateCafeStatus`: `body: JSON.stringify({ is_active })`
- `useCreateCombo`: `body: JSON.stringify(data)`
- `useUpdateCombo`: `body: JSON.stringify(data)`
- `useCreateMenuItem`: `body: JSON.stringify(data)`
- `useUpdateMenuItem`: `body: JSON.stringify(data)`

**Проверка:**
- Функция `apiRequest` в `client.ts` ожидает `body` как string в `RequestInit`
- Hooks, которые уже использовали `JSON.stringify` (`useCreateOrder`, `useCreateSummary`, `authenticateWithTelegram`), оставлены без изменений

### 2. ESLint warnings: setState в useEffect

**Проблема:** Cascading renders из-за сложной структуры условных setState внутри useEffect.

**Решение:** Рефакторинг useEffect в обоих файлах:

**manager/page.tsx:**
- Убраны вложенные условия
- Используется early return для не-Telegram случая
- Избегаются множественные setState в одном useEffect
- Зависимости в deps массиве корректны ([router])

**page.tsx:**
- Аналогичный рефакторинг
- Early returns для упрощения логики
- Избегаются вложенные условия с setState

**Структура после рефакторинга:**
```typescript
useEffect(() => {
  const inTelegram = isTelegramWebApp();
  setIsInTelegram(inTelegram);

  if (!inTelegram) {
    return; // early return
  }

  // ... остальная логика без вложенности
}, [router]);
```

### 3. Обработка 403 Forbidden

**Проблема:** Нет централизованной обработки 403 ошибки с user-friendly сообщением.

**Решение:** В `client.ts` добавлена обработка:

```typescript
} else if (response.status === 403) {
  // Forbidden - show alert and redirect to home
  if (typeof window !== "undefined") {
    alert("У вас нет доступа к этой функции");
    window.location.href = "/";
  }
  throw new Error("Forbidden");
}
```

**Поведение:**
1. При 403 ответе показывается alert с сообщением на русском
2. Пользователь редиректится на главную страницу
3. Выбрасывается Error для обработки в catch блоках

## Итог

Все замечания Reviewer исправлены:
- JSON сериализация body в mutation hooks
- Улучшена структура useEffect для избежания cascading renders
- Централизованная обработка 403 с alert и редиректом

Код готов к повторному review.
