# Frontend Components

**Location:** `frontend_mini_app/src/components/`

Telegram Mini App для заказа еды. Стек: Next.js 16, React 19, Tailwind CSS 4.

---

## Структура компонентов

```
src/
├── app/
│   ├── layout.tsx      # Root layout (Geist fonts)
│   ├── page.tsx        # Home page (main logic)
│   └── globals.css     # Tailwind + custom styles
└── components/
    ├── CafeSelector/
    │   └── CafeSelector.tsx
    ├── CategorySelector/
    │   └── CategorySelector.tsx
    ├── Menu/
    │   └── MenuSection.tsx
    └── Cart/
        ├── CartSummary.tsx
        └── CheckoutButton.tsx
```

---

## CafeSelector

Горизонтальный скролл с выбором кафе.

**Props:**
```tsx
interface CafeSelectorProps {
  cafes: Cafe[];              // { id: number; name: string }
  activeCafeId: number;       // ID выбранного кафе
  onCafeClick: (id: number) => void;
}
```

**Особенности:**
- Анимированный градиент на активной кнопке
- Hover эффекты
- Горизонтальный scroll без scrollbar

**Файл:** `frontend_mini_app/src/components/CafeSelector/CafeSelector.tsx`

---

## CategorySelector

Сетка категорий блюд с иконками.

**Props:**
```tsx
interface CategorySelectorProps {
  categories: Category[];     // { id: number; name: string; icon: ReactNode }
  activeCategoryId: number;
  onCategoryClick: (id: number) => void;
}
```

**Категории (id: 1 = "Все"):**
- Все, Второе, Салаты, Десерты, Напитки
- Закуски, Бургеры, Пицца, Суши, Стейки
- Вегетарианские, Паста

**Иконки:** react-icons/fa6 (Font Awesome 6)

**Файл:** `frontend_mini_app/src/components/CategorySelector/CategorySelector.tsx`

---

## MenuSection

Список блюд с корзиной.

**Props:**
```tsx
interface MenuSectionProps {
  dishes: Dish[];             // { id, name, description, price, categoryId }
  cart: { [key: number]: number };  // dishId -> quantity
  addToCart: (dishId: number) => void;
  removeFromCart: (dishId: number) => void;
}
```

**Особенности:**
- Карточка блюда с названием, описанием, ценой
- Кнопка "+ Добавить" если не в корзине
- Счётчик [-] [qty] [+] если в корзине
- Backdrop blur и прозрачность

**Файл:** `frontend_mini_app/src/components/Menu/MenuSection.tsx`

---

## CartSummary

Отображение итога корзины.

**Props:**
```tsx
interface CartSummaryProps {
  totalItems: number;         // Количество товаров
  totalPrice: number;         // Сумма в рублях
}
```

**Файл:** `frontend_mini_app/src/components/Cart/CartSummary.tsx`

---

## CheckoutButton

Кнопка оформления заказа.

**Props:**
```tsx
interface CheckoutButtonProps {
  disabled: boolean;          // true если корзина пуста
  onClick?: () => void;       // Callback оформления
}
```

**Состояния:**
- Активна: градиент purple
- Disabled: серый фон, курсор not-allowed

**Файл:** `frontend_mini_app/src/components/Cart/CheckoutButton.tsx`

---

## Home Page (page.tsx)

Главная страница со всей логикой.

**State:**
```tsx
const [activeCafeId, setActiveCafeId] = useState<number>(1);
const [activeCategoryId, setActiveCategoryId] = useState<number>(1);
const [cart, setCart] = useState<{ [key: number]: number }>({});
```

**Computed:**
```tsx
const totalItems = Object.values(cart).reduce((s, v) => s + v, 0);
const totalPrice = dishes.filter(d => !!cart[d.id])
  .reduce((sum, d) => sum + d.price * (cart[d.id] || 0), 0);
const filteredDishes = activeCategoryId === 1
  ? dishes
  : dishes.filter(d => d.categoryId === activeCategoryId);
```

**Layout:**
1. Header (Food Delivery title)
2. CafeSelector
3. CategorySelector
4. MenuSection
5. Fixed bottom: CartSummary + CheckoutButton

**Файл:** `frontend_mini_app/src/app/page.tsx`

---

## Цветовая схема

```tsx
const theme = {
  background: "#130F30",        // Темный фон
  accent: "#A020F0",            // Фиолетовый
  accentDark: "#8B23CB",        // Темный фиолетовый
  card: "#7B6F9C",              // Карточки (с opacity 20-30%)
  text: "white",
  textMuted: "gray-300",
};
```

**Градиенты:**
```tsx
// Активные элементы
"bg-gradient-to-r from-[#8B23CB] via-[#A020F0] to-[#7723B6]"

// Кнопки
"bg-gradient-to-r from-[#8B23CB]/80 to-[#A020F0]/80"

// Blur фон
"backdrop-blur-md bg-white/5 border border-white/10"
```

---

## TODO: Интеграция с Backend

Сейчас данные захардкожены. Для интеграции:

1. **API клиент** — fetch/axios для REST API
2. **Типы** — вынести в `types/` или получать из OpenAPI
3. **State management** — React Query или SWR для кэширования
4. **Telegram WebApp** — `@twa-dev/sdk` для интеграции с Telegram
