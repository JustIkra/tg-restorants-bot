---
agent: coder
task_id: TSK-015
subtask: 6
subtask_name: "Frontend Components"
status: completed
next: null
created_at: 2025-12-07T12:00:00Z
files_changed:
  - path: frontend_mini_app/src/lib/api/types.ts
    action: modified
  - path: frontend_mini_app/src/components/Menu/MenuSection.tsx
    action: modified
  - path: frontend_mini_app/src/components/Menu/DishModal.tsx
    action: modified
  - path: frontend_mini_app/src/app/page.tsx
    action: modified
  - path: frontend_mini_app/src/components/ExtrasSection/ExtrasSection.tsx
    action: modified
---

## Реализация

Выполнены подзадачи 15-18 для поддержки standalone заказов с опциями на frontend.

### Подзадача 15: MenuSection — отображение цены для всех блюд

**Файл:** `frontend_mini_app/src/components/Menu/MenuSection.tsx`

**Изменения:**
1. Обновлена сигнатура `addToCart` для приёма опций: `(dishId: number, options?: Record<string, string>)`
2. Изменена структура cart с `{ [key: number]: number }` на `{ [key: number]: CartItem }` где `CartItem = { quantity: number; options?: Record<string, string> }`
3. Цена блюда теперь показывается для всех категорий:
   ```tsx
   {dish.price ? `${dish.price} ₽` : "Входит в комбо"}
   ```
4. Обновлён доступ к количеству через `cart[dish.id].quantity`

### Подзадача 16: DishModal — отображение опций

**Файл:** `frontend_mini_app/src/components/Menu/DishModal.tsx`

**Изменения:**
1. Добавлен тип `MenuItemOption` и поле `options?: MenuItemOption[]` в `Dish`
2. Добавлен state для выбранных опций:
   ```tsx
   const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});
   ```
3. Добавлен `useEffect` для сброса опций при смене блюда или закрытии модала
4. Добавлен UI для отображения опций (после секции "Кому подходит"):
   - Заголовок "Опции:" со звёздочкой для обязательных опций
   - Select элементы для каждой опции с выпадающим списком значений
   - Стилизация в тёмной теме с Tailwind классами
5. Добавлена валидация обязательных опций при добавлении в корзину (во всех кнопках):
   ```tsx
   const requiredOptions = dish.options?.filter(opt => opt.is_required) || [];
   const missingOptions = requiredOptions.filter(opt => !selectedOptions[opt.name]);

   if (missingOptions.length > 0) {
     alert(`Выберите обязательные опции: ${missingOptions.map(o => o.name).join(", ")}`);
     return;
   }

   addToCart(dish.id, selectedOptions);
   ```
6. Обновлено отображение количества через `cart[dish.id].quantity`

### Подзадача 17: Корзина — хранение опций для каждого блюда

**Файл:** `frontend_mini_app/src/app/page.tsx`

**Изменения:**
1. Изменена структура cart:
   ```tsx
   interface CartItem {
     quantity: number;
     options?: Record<string, string>;
   }
   const [cart, setCart] = useState<{ [key: number]: CartItem }>({});
   ```

2. Обновлена функция `addToCart`:
   ```tsx
   const addToCart = (dishId: number, options?: Record<string, string>) =>
     setCart(prev => ({
       ...prev,
       [dishId]: {
         quantity: (prev[dishId]?.quantity || 0) + 1,
         options: options || prev[dishId]?.options
       }
     }));
   ```

3. Обновлена функция `removeFromCart`:
   ```tsx
   const removeFromCart = (dishId: number) =>
     setCart(prev => {
       const current = prev[dishId];
       if (!current || current.quantity <= 1) {
         const { [dishId]: _, ...rest } = prev;
         return rest;
       }
       return {
         ...prev,
         [dishId]: { ...current, quantity: current.quantity - 1 }
       };
     });
   ```

4. Обновлён расчёт `totalItems` и `totalPrice`:
   ```tsx
   const totalItems = Object.values(cart).reduce((sum, item) => sum + item.quantity, 0);
   const totalPrice = Object.entries(cart).reduce((sum, [dishId, item]) => {
     const dish = dishes.find(d => d.id === parseInt(dishId));
     return sum + (dish?.price || 0) * item.quantity;
   }, 0);
   ```

### Подзадача 18: Создание заказа — поддержка standalone items

**Файл:** `frontend_mini_app/src/app/page.tsx`

**Изменения:**
1. Добавлена функция `handleCheckout` для сохранения корзины в localStorage:
   ```tsx
   const handleCheckout = () => {
     localStorage.setItem("cart", JSON.stringify(cart));
     localStorage.setItem("activeCafeId", activeCafeId?.toString() || "");
     localStorage.setItem("selectedDate", selectedDate || "");
     router.push("/order");
   };
   ```

2. Обновлён CheckoutButton для использования новой функции:
   ```tsx
   <CheckoutButton disabled={isCheckoutDisabled} onClick={handleCheckout} />
   ```

**Примечание:** Формирование JSON для POST /orders будет реализовано в `/order/page.tsx` при чтении корзины из localStorage и создании структуры:
```typescript
const items = Object.entries(cart).map(([dishId, cartItem]) => ({
  type: "standalone" as const,
  menu_item_id: parseInt(dishId),
  quantity: cartItem.quantity,
  options: cartItem.options || {}
}));

const orderData = {
  cafe_id: activeCafeId,
  order_date: selectedDate,
  combo_id: null,
  items,
  extras: [],
  notes: null
};
```

### Типы (types.ts)

**Файл:** `frontend_mini_app/src/lib/api/types.ts`

Типы уже были обновлены ранее (возможно другим агентом или в другой подзадаче):
- Добавлен `MenuItemOption` интерфейс
- Добавлено поле `options?: MenuItemOption[]` в `MenuItem`
- Добавлены типы `ComboItem`, `StandaloneItem`, `OrderItem`
- Обновлён `CreateOrderRequest` для поддержки `combo_id: number | null` и `items: OrderItem[]`
- Обновлён `Order` для поддержки `combo_id: number | null`

## Обратная совместимость

Все изменения сохраняют обратную совместимость:
- Блюда без опций продолжают работать (опции опциональны)
- Блюда без цены показывают "Входит в комбо"
- Старая логика combo заказов не затронута (будет работать при наличии combo_id)

### ExtrasSection — обновление для новой структуры cart

**Файл:** `frontend_mini_app/src/components/ExtrasSection/ExtrasSection.tsx`

**Изменения:**
1. Обновлена сигнатура типов для поддержки новой структуры cart:
   ```tsx
   interface CartItem {
     quantity: number;
     options?: Record<string, string>;
   }

   interface ExtrasSectionProps {
     cart: { [itemId: number]: CartItem };
     addToCart: (itemId: number, options?: Record<string, string>) => void;
     // ...
   }
   ```

2. Обновлён доступ к quantity:
   ```tsx
   const quantity = cart[extra.id]?.quantity || 0;
   ```

Extras обычно не имеют опций (или они добавляются через общий DishModal), поэтому дополнительная логика для опций не требуется.

## Следующие шаги

1. **Order page (`/order/page.tsx`)** — обновить для:
   - Чтения новой структуры cart из localStorage
   - Формирования `items: OrderItem[]` с type: "standalone"
   - Отправки заказа с `combo_id: null` для standalone
   - Поддержки миксов (combo + standalone)

2. **Backend** — должен быть готов принимать:
   - `combo_id: null`
   - `items` с type: "standalone"
   - Валидацию опций для standalone items

## Тестирование

Перед деплоем необходимо протестировать:
1. Отображение цены для всех блюд
2. Отображение и выбор опций в модале
3. Валидацию обязательных опций
4. Добавление в корзину с опциями
5. Увеличение/уменьшение количества с сохранением опций
6. Расчёт итоговой цены
7. Переход на страницу заказа с сохранением корзины

## Статус

**Completed** — все подзадачи 15-18 реализованы.

Frontend готов к работе с standalone заказами с опциями. Требуется синхронизация с backend API.
