---
agent: coder
task_id: TSK-015
subtask: 5
subtask_name: "Frontend Types and API Client"
status: completed
next: null
created_at: 2025-12-07T12:00:00Z
files_changed:
  - path: frontend_mini_app/src/lib/api/types.ts
    action: modified
  - path: frontend_mini_app/src/lib/api/client.ts
    action: modified
---

## Изменения

### Подзадача 13: API types — добавить MenuItemOption

**Файл:** `frontend_mini_app/src/lib/api/types.ts`

#### Добавлено:

1. **MenuItemOption interface**
   ```typescript
   export interface MenuItemOption {
     id: number;
     menu_item_id: number;
     name: string;
     values: string[];
     is_required: boolean;
   }
   ```

2. **Обновлен MenuItem** — добавлено поле `options?`
   ```typescript
   export interface MenuItem {
     // ... existing fields ...
     options?: MenuItemOption[];
   }
   ```

3. **ComboItem и StandaloneItem типы**
   ```typescript
   export interface ComboItem {
     type: "combo";
     category: "soup" | "salad" | "main";
     menu_item_id: number;
   }

   export interface StandaloneItem {
     type: "standalone";
     menu_item_id: number;
     quantity: number;
     options: Record<string, string>;
   }

   export type OrderItem = ComboItem | StandaloneItem;
   ```

4. **ExtraInput interface**
   ```typescript
   export interface ExtraInput {
     menu_item_id: number;
     quantity: number;
   }
   ```

5. **Обновлен Order interface**
   - `combo_id: number | null` (вместо обязательного)
   - `combo?: OrderCombo` (опциональный, когда combo_id = null)
   - `items: OrderItem[]` (вместо фиксированного combo)

6. **Обновлен CreateOrderRequest**
   - `combo_id: number | null` (опциональный)
   - `items: OrderItem[]` (вместо `combo_items`)
   - `extras?: ExtraInput[]` (используем новый тип)

### Подзадача 14: API client — методы для опций

**Файл:** `frontend_mini_app/src/lib/api/client.ts`

#### Добавлено:

1. **Импорт MenuItemOption** в заголовок файла
   ```typescript
   import type { User, MenuItemOption } from "./types";
   ```

2. **getMenuItemOptions** — получить список опций блюда
   ```typescript
   export async function getMenuItemOptions(
     cafeId: number,
     itemId: number
   ): Promise<MenuItemOption[]>
   ```

3. **createMenuItemOption** — создать опцию (manager only)
   ```typescript
   export async function createMenuItemOption(
     cafeId: number,
     itemId: number,
     data: { name: string; values: string[]; is_required: boolean }
   ): Promise<MenuItemOption>
   ```

4. **updateMenuItemOption** — обновить опцию (manager only)
   ```typescript
   export async function updateMenuItemOption(
     cafeId: number,
     itemId: number,
     optionId: number,
     data: Partial<{ name: string; values: string[]; is_required: boolean }>
   ): Promise<MenuItemOption>
   ```

5. **deleteMenuItemOption** — удалить опцию (manager only)
   ```typescript
   export async function deleteMenuItemOption(
     cafeId: number,
     itemId: number,
     optionId: number
   ): Promise<void>
   ```

## Соответствие спецификации

✅ Все типы следуют backend схемам из архитектурного плана
✅ API client функции соответствуют паттернам существующего кода:
  - Используют `apiRequest<T>` helper
  - Правильный error handling
  - Корректные HTTP методы (GET, POST, PATCH, DELETE)
  - Consistent naming convention
✅ TypeScript типы полностью type-safe:
  - Union type для `OrderItem = ComboItem | StandaloneItem`
  - Nullable types для `combo_id` и `combo`
  - Partial<T> для update endpoints
✅ Следуем code style:
  - Двойные кавычки для строк
  - Explicit return types для всех функций
  - JSDoc комментарии для публичных функций
  - Правильная структура imports (типы в начале файла)

## Тестирование

Для проверки корректности изменений необходимо:

1. **TypeScript compilation:**
   ```bash
   cd frontend_mini_app && npm run build
   ```
   Не должно быть type errors.

2. **Runtime тестирование** (после деплоя backend):
   - Вызов `getMenuItemOptions(cafeId, itemId)` для блюда с опциями
   - Создание опции через `createMenuItemOption()` (manager role)
   - Обновление опции через `updateMenuItemOption()`
   - Удаление опции через `deleteMenuItemOption()`

## Обратная совместимость

✅ Сохранена обратная совместимость:
- `combo_id` теперь `number | null`, старые заказы продолжат работать
- `items` поддерживает оба типа: `ComboItem` и `StandaloneItem`
- `extras` использует новый тип `ExtraInput`, но структура не изменилась

## Next Steps

Следующие подзадачи (15-18) будут использовать эти типы:
- **15:** MenuSection — отображать цену для всех блюд
- **16:** DishModal — показывать опции
- **17:** Корзина — хранить опции для каждого блюда
- **18:** Создание заказа — поддержка standalone items
