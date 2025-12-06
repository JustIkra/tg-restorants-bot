---
agent: coder
task_id: TSK-013
subtask: 5
status: completed
created_at: 2025-12-07
files_changed:
  - frontend_mini_app/src/app/page.tsx
  - frontend_mini_app/src/app/manager/page.tsx
---

# Coder Result: Navigation Integration

## Задача
Интегрировать навигацию - добавить кнопку профиля на главную страницу и вкладку "Балансы" в панель менеджера.

## Выполненные изменения

### 1. page.tsx (Главная страница)

#### Добавлен импорт FaUser
```typescript
import {
  // ... existing imports
  FaUserShield,
  FaUser  // NEW
} from "react-icons/fa6";
```

#### Добавлена кнопка профиля в header
Расположение в блоке кнопок (порядок слева направо):
1. **FaUser** (Профиль) - для ВСЕХ пользователей
2. **FaUserShield** (Менеджер) - только для менеджеров
3. **Fortune Wheel** (Колесо фортуны)

```tsx
<div className="flex items-center gap-2">
  {/* NEW: Profile button - visible for ALL users */}
  <button
    onClick={() => router.push("/profile")}
    className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B23CB]/50 to-[#A020F0]/50 border border-white/20 backdrop-blur-md shadow-lg"
    aria-label="Профиль"
  >
    <FaUser className="text-white text-xl" />
  </button>

  {/* Manager button - conditional */}
  {user?.role === "manager" && (
    <button
      onClick={() => router.push("/manager")}
      className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B23CB]/50 to-[#A020F0]/50 border border-white/20 backdrop-blur-md shadow-lg"
      aria-label="Панель менеджера"
    >
      <FaUserShield className="text-white text-xl" />
    </button>
  )}

  {/* Fortune Wheel button */}
  <button
    onClick={navigateToFortuneWheel}
    className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B23CB]/50 to-[#A020F0]/50 border border-white/20 backdrop-blur-md shadow-lg overflow-hidden"
  >
    <img ref={imgRef} src="/image.png" alt="Колесо фортуны" className="w-8 h-8 object-contain" />
  </button>
</div>
```

**Ключевые моменты:**
- Кнопка профиля отображается для ВСЕХ пользователей (не в условном блоке)
- При клике переходит на `/profile`
- Использует те же стили, что и остальные кнопки для единообразия

---

### 2. manager/page.tsx (Панель менеджера)

#### Добавлен импорт FaWallet
```typescript
import {
  // ... existing imports
  FaCartShopping,
  FaWallet,  // NEW
} from "react-icons/fa6";
```

#### Добавлен импорт компонента BalanceManager
```typescript
import BalanceManager from "@/components/Manager/BalanceManager";
```

#### Обновлен тип TabId
```typescript
type TabId = "users" | "balances" | "cafes" | "menu" | "requests" | "reports";
//                     ^^^^^^^^^^^ NEW
```

#### Добавлена вкладка "Балансы" в массив tabs
Расположение вкладок (слева направо):
1. Пользователи
2. **Балансы** (НОВАЯ)
3. Кафе
4. Меню
5. Запросы
6. Отчёты

```typescript
const tabs: Tab[] = [
  { id: "users", name: "Пользователи", icon: <FaUsers /> },
  { id: "balances", name: "Балансы", icon: <FaWallet /> },  // NEW
  { id: "cafes", name: "Кафе", icon: <FaStore /> },
  { id: "menu", name: "Меню", icon: <FaUtensils /> },
  { id: "requests", name: "Запросы", icon: <FaEnvelope /> },
  { id: "reports", name: "Отчёты", icon: <FaChartBar /> },
];
```

#### Добавлен рендеринг компонента для вкладки "balances"
```tsx
{activeTab === "balances" && (
  <div className="text-white">
    <BalanceManager />
  </div>
)}
```

**Расположение в коде:**
- После блока `{activeTab === "users" && (...)}`
- Перед блоком `{activeTab === "cafes" && (...)}`

---

## Validation

### page.tsx
- ✅ Импорт `FaUser` добавлен
- ✅ Кнопка профиля добавлена в header
- ✅ Кнопка расположена ПЕРЕД кнопкой менеджера
- ✅ Кнопка видна для ВСЕХ пользователей (не в условном блоке)
- ✅ При клике переходит на `/profile`
- ✅ Используются существующие стили для единообразия
- ✅ Порядок кнопок: Profile → Manager (conditional) → Fortune Wheel

### manager/page.tsx
- ✅ Импорт `FaWallet` добавлен
- ✅ Импорт `BalanceManager` добавлен
- ✅ Тип `TabId` обновлен
- ✅ Вкладка "Балансы" добавлена в массив tabs
- ✅ Вкладка расположена после "Пользователи"
- ✅ Компонент `BalanceManager` отображается при `activeTab === "balances"`
- ✅ Tab navigation работает через существующую логику

## Следующие шаги

Навигация интегрирована согласно спецификации. Компоненты готовы к использованию:
- Пользователи могут переходить на страницу профиля с главной страницы
- Менеджеры могут управлять балансами пользователей через новую вкладку в панели менеджера

**Готово для тестирования и review.**
