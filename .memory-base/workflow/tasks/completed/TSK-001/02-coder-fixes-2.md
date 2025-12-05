---
agent: coder
task_id: TSK-001
status: completed
next: reviewer
created_at: 2025-12-05T21:19:16
files_changed:
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
  - path: frontend_mini_app/src/lib/telegram/webapp.ts
    action: modified
---

## Исправления TypeScript ошибок

Исправлены ошибки компиляции TypeScript в двух файлах API клиента.

### Проблема 1: Несоответствие типов в hooks.ts

**Описание:**
Функции `useCafes`, `useCombos`, `useMenu`, `useOrders` возвращали тип `SWRResponse<T[], Error>`, но фактически возвращали модифицированный объект где `data` имел тип `T[] | undefined`, а не весь `SWRResponse`.

SWR возвращает `ListResponse<T>` из API, но мы хотим предоставить пользователям напрямую массив `T[]`.

**Решение:**
1. Добавлен новый интерфейс `UseDataResult<T>`:
```typescript
interface UseDataResult<T> {
  data: T[] | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}
```

2. Изменены сигнатуры всех четырёх функций для использования нового типа:
```typescript
export function useCafes(activeOnly = true): UseDataResult<Cafe>
export function useCombos(cafeId: number | null): UseDataResult<Combo>
export function useMenu(cafeId: number | null, category?: string): UseDataResult<MenuItem>
export function useOrders(filters?: {...}): UseDataResult<Order>
```

3. Рефакторинг реализации функций для явного деструктурирования:
```typescript
const { data, error, isLoading, mutate } = useSWR<ListResponse<T>>(...);
return {
  data: data?.items,
  error,
  isLoading,
  mutate
};
```

### Проблема 2: Отсутствие callback в MainButton.offClick()

**Описание:**
В `webapp.ts` функция `hideMainButton` вызывала `MainButton.offClick()` без параметра, но TypeScript SDK требует передачи callback-функции для удаления конкретного обработчика.

**Решение:**
1. Добавлена переменная модуля для хранения текущего callback:
```typescript
let mainButtonCallback: (() => void) | null = null;
```

2. Изменена функция `showMainButton` для сохранения callback:
```typescript
export function showMainButton(text: string, onClick: () => void): void {
  mainButtonCallback = onClick;
  WebApp.MainButton.setText(text);
  WebApp.MainButton.onClick(onClick);
  WebApp.MainButton.show();
}
```

3. Изменена функция `hideMainButton` для корректного удаления обработчика:
```typescript
export function hideMainButton(): void {
  if (mainButtonCallback) {
    WebApp.MainButton.offClick(mainButtonCallback);
    mainButtonCallback = null;
  }
  WebApp.MainButton.hide();
}
```

### Проверка

Выполнена компиляция TypeScript без ошибок:
```bash
cd frontend_mini_app && npx tsc --noEmit
```
Результат: успешно, ошибок не обнаружено.

### Итоги

- ✅ Все функции hooks теперь имеют корректные типы возвращаемых значений
- ✅ MainButton lifecycle управляется корректно с правильным удалением обработчиков
- ✅ TypeScript компиляция проходит успешно
- ✅ Сохранена обратная совместимость с существующим кодом компонентов

Изменения готовы к code review.
