---
agent: coder
task_id: TSK-019
status: completed
next: tester
created_at: 2025-12-07T06:59:23Z
files_changed:
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
  - path: frontend_mini_app/src/components/Manager/MenuManager.tsx
    action: modified
---

## Реализация

### Задача 1: Фикс исчезновения меню при деактивации

**Проблема:** При деактивации блюда или комбо оно исчезает из списка вместо отображения со статусом "Недоступно". Причина — SWR cache key mismatch, аналогично проблеме с кафе.

**Изменения в `frontend_mini_app/src/lib/api/hooks.ts`:**

1. **Обновлён `useMenu` hook** — добавлен параметр `activeOnly` (default: true):
   ```tsx
   export function useMenu(
     cafeId: number | null,
     category?: string,
     activeOnly = true
   ): UseDataResult<MenuItem>
   ```
   - Теперь формирует endpoint с `?available_only=${activeOnly ? "true" : "false"}`
   - Поддерживает оба параметра: `category` и `available_only`

2. **Обновлён `useCombos` hook** — добавлен параметр `activeOnly` (default: true):
   ```tsx
   export function useCombos(cafeId: number | null, activeOnly = true): UseDataResult<Combo>
   ```
   - Формирует endpoint: `/cafes/${cafeId}/combos?available_only=${activeOnly ? "true" : "false"}`

3. **Исправлены mutate вызовы** во всех mutation hooks:
   - `useCreateCombo`, `useUpdateCombo`, `useDeleteCombo` — используют matcher:
     ```tsx
     await mutate((key: string) => typeof key === "string" && key.startsWith(`/cafes/${cafeId}/combos`), ...)
     ```
   - `useCreateMenuItem`, `useUpdateMenuItem`, `useDeleteMenuItem` — используют matcher:
     ```tsx
     await mutate((key: string) => typeof key === "string" && key.startsWith(`/cafes/${cafeId}/menu`), ...)
     ```

   Это решает проблему cache key mismatch: теперь при изменении данных инвалидируются все связанные ключи, независимо от query параметров.

**Изменения в `frontend_mini_app/src/components/Manager/MenuManager.tsx`:**

1. **Обновлены вызовы hooks**:
   ```tsx
   const { data: combos } = useCombos(selectedCafeId, false); // activeOnly=false
   const { data: menuItems } = useMenu(selectedCafeId, undefined, false); // activeOnly=false
   ```

2. **Добавлены статус-бейджи** для комбо и блюд:
   - Для комбо: отображается "Доступно" (зелёный) или "Недоступно" (красный)
   - Для блюд: отображается "Доступно" (зелёный) или "Недоступно" (красный)
   - Цвета: `bg-green-500/20 text-green-400` / `bg-red-500/20 text-red-400`

**Результат:**
- При деактивации блюда/комбо оно остаётся в списке со статусом "Недоступно"
- SWR корректно обновляет все связанные кэши благодаря matcher pattern
- Менеджер видит все элементы (активные и неактивные) с визуальными индикаторами

### Задача 2: Замена иконок на текстовые кнопки в CafeList

**Статус:** Уже реализовано.

**Проверка `frontend_mini_app/src/components/Manager/CafeList.tsx`:**
- Строки 119-148 содержат текстовые кнопки:
  - "Редактировать" (blue-500/20, text-blue-400) — строка 123
  - "Деактивировать"/"Активировать" (yellow-500/20 / green-500/20) — строки 127-141
  - "Удалить" (red-500/20, text-red-400) — строки 142-147

Компонент уже соответствует требованиям задачи. Иконки отсутствуют, используются только текстовые кнопки с правильными цветами.

## Итого

**Задача 1:** ✅ Исправлена — меню больше не исчезает при деактивации
**Задача 2:** ✅ Уже реализовано — текстовые кнопки на месте

Изменено 2 файла, добавлены визуальные индикаторы статуса для комбо и блюд.
