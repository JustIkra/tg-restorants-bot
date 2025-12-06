---
agent: coder
task_id: TSK-004
subtask: 1
subtask_name: "Frontend API Integration"
status: completed
next: null
created_at: 2025-12-06T14:30:00
files_changed:
  - path: frontend_mini_app/src/app/page.tsx
    action: modified
  - path: frontend_mini_app/src/components/CategorySelector/CategorySelector.tsx
    action: modified
  - path: frontend_mini_app/.env.example
    action: created
blockers: []
---

## Результат

Успешно реализована интеграция Frontend с Backend API. Mock данные заменены на реальные API calls через SWR hooks.

### Изменения

#### 1. `frontend_mini_app/src/app/page.tsx`

**Удалено:**
- Все mock данные (hardcoded cafes, categories, dishes)
- Статические типы для activeCafeId и activeCategoryId

**Добавлено:**
- Импорт SWR hooks: `useCafes`, `useCombos`, `useMenu`
- Реальные API calls через SWR hooks:
  - `useCafes(true)` - получение списка активных кафе
  - `useCombos(activeCafeId)` - получение комбо для выбранного кафе
  - `useMenu(activeCafeId)` - получение menu items для кафе
  - `useMenu(activeCafeId, "extra")` - получение extras для кафе

**State Management:**
- `activeCafeId` теперь `number | null` (для корректной обработки начального состояния)
- `activeCategoryId` изменен на `string` (вместо number) для работы с реальными категориями API
- Автоматический выбор первого кафе при загрузке данных
- Сброс корзины при переключении кафе

**Data Transformation:**
- Маппинг cafes из API в формат CafeSelector
- Динамическое извлечение категорий из menu items
- Маппинг category names на иконки (soup → FaBowlFood, main → FaDrumstickBite и т.д.)
- Маппинг menu items в формат MenuSection

**Loading States:**
- Skeleton loaders для cafes, categories, menu
- Spinner индикаторы с текстом "Загрузка..."
- Graceful handling пустых состояний ("Нет доступных кафе", "Меню пока не добавлено")

**Error Handling:**
- Компонент Error banner с красным фоном
- Отображение понятных сообщений об ошибках
- Иконка FaExclamationTriangle для визуального выделения
- Обработка всех типов ошибок (cafesError, menuError, combosError, extrasError)

**UX Improvements:**
- Prompt для выбора кафе, если ни одно не выбрано
- Условный рендеринг категорий и меню только после выбора кафе
- Информативные пустые состояния

#### 2. `frontend_mini_app/src/components/CategorySelector/CategorySelector.tsx`

**Изменения типов:**
```typescript
// Было:
type Category = { id: number; name: string; icon: React.ReactNode };
activeCategoryId: number;
onCategoryClick: (id: number) => void;

// Стало:
type Category = { id: number | string; name: string; icon: React.ReactNode };
activeCategoryId: number | string;
onCategoryClick: (id: number | string) => void;
```

**Причина:** API возвращает category как string (например, "soup", "main", "salad"), а не number. Поддержка string | number обеспечивает совместимость с реальными данными.

#### 3. `frontend_mini_app/.env.example`

Создан файл с конфигурацией API URL:

```bash
# Development (local backend)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Production (example)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1

# Docker development (use service name)
NEXT_PUBLIC_API_URL=http://backend:8000/api/v1
```

**Важно:** Пользователь должен создать `.env.local` на основе `.env.example` для локальной разработки.

### Использованные SWR hooks

Все hooks уже реализованы в `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/lib/api/hooks.ts`:

1. **useCafes(activeOnly: boolean)**
   - Endpoint: `/cafes?active_only=true`
   - Возвращает: `{ data: Cafe[], error, isLoading, mutate }`

2. **useCombos(cafeId: number | null)**
   - Endpoint: `/cafes/${cafeId}/combos`
   - Возвращает: `{ data: Combo[], error, isLoading, mutate }`
   - Пропускает запрос если cafeId === null

3. **useMenu(cafeId: number | null, category?: string)**
   - Endpoint: `/cafes/${cafeId}/menu?category=${category}`
   - Возвращает: `{ data: MenuItem[], error, isLoading, mutate }`
   - Пропускает запрос если cafeId === null

4. **useMenu(cafeId: number | null, "extra")**
   - Endpoint: `/cafes/${cafeId}/menu?category=extra`
   - Возвращает extras для кафе

### Архитектурные решения

1. **useMemo для производительности**
   - Маппинг cafes, categories, dishes кэшируется через useMemo
   - Предотвращает ненужные перерендеры при изменении других state

2. **Условный рендеринг**
   - Categories и menu отображаются только после выбора кафе
   - Предотвращает лишние API calls

3. **Auto-select первого кафе**
   - Улучшает UX - пользователь сразу видит меню
   - Реализовано через useMemo с проверкой `activeCafeId === null`

4. **Сброс корзины при смене кафе**
   - Предотвращает несоответствие между menu items разных кафе
   - Логично с точки зрения UX

### Тестирование

Для проверки интеграции:

1. **Запустить backend:**
   ```bash
   cd backend
   uvicorn src.main:app --reload
   ```

2. **Создать `.env.local` во frontend:**
   ```bash
   cd frontend_mini_app
   cp .env.example .env.local
   ```

3. **Запустить frontend:**
   ```bash
   npm run dev
   ```

4. **Проверить в браузере:**
   - http://localhost:3000
   - Должны загружаться реальные кафе из API
   - При выборе кафе должно загружаться реальное меню
   - Loading states должны отображаться корректно
   - Error states должны появляться при проблемах с API

### Известные зависимости

**Backend должен быть запущен и доступен:**
- PostgreSQL с данными (кафе, меню)
- Backend API на порту 8000
- CORS настроен для localhost:3000

**CORS конфигурация (будет настроена в подзадаче 1.2):**
```python
# backend/src/main.py
CORS_ORIGINS = ["http://localhost:3000", "http://frontend:3000"]
```

### Следующие шаги

Эта подзадача завершена. Готово для интеграции с:
- **Подзадача 1.2:** CORS Configuration (critical dependency)
- **Подзадача 1.3:** Docker Compose для Frontend
- **Подзадача 2.1:** Playwright E2E тесты

### Потенциальные проблемы

1. **CORS errors при первом запуске**
   - Решение: Подзадача 1.2 настроит CORS в backend

2. **Пустая БД → пустые кафе**
   - Решение: Добавить seed data или проверить миграции

3. **JWT авторизация не работает в dev mode**
   - Решение: Временно можно отключить JWT middleware для `/cafes` и `/menu` endpoints (read-only)
   - Или использовать Telegram WebApp SDK для получения initData

4. **CategorySelector ожидает number ID**
   - Решение: ✅ Уже исправлено - теперь поддерживает string | number

### Метрики

- **Файлы изменены:** 2
- **Файлы созданы:** 1
- **Строк кода добавлено:** ~120
- **Строк кода удалено:** ~30
- **Mock данные удалены:** 100%
- **API endpoints интегрированы:** 4

---

## Исправления по review (2025-12-06T16:00:00)

После code review от Reviewer были выявлены следующие проблемы, которые были исправлены:

### Issue #1 - useMemo → useEffect (Critical)

**Проблема:**
Строки 33-37: `useMemo` использовался для side effects (вызов `setActiveCafeId`), что нарушает React guidelines.

**Было:**
```tsx
useMemo(() => {
  if (cafes.length > 0 && activeCafeId === null) {
    setActiveCafeId(cafes[0].id);
  }
}, [cafes, activeCafeId]);
```

**Исправлено:**
```tsx
useEffect(() => {
  if (cafes.length > 0 && activeCafeId === null) {
    setActiveCafeId(cafes[0].id);
  }
}, [cafes, activeCafeId]);
```

**Результат:** Теперь используется правильный хук для side effects. Добавлен импорт `useEffect` в строку 3.

---

### Issue #2 - isLoading condition (Important)

**Проблема:**
Строка 117: `activeCafeId` может быть `0` (валидный ID), но условие `activeCafeId && ...` вернет `false` для 0.

**Было:**
```tsx
const isLoading = cafesLoading || (activeCafeId && (menuLoading || combosLoading));
```

**Исправлено:**
```tsx
const isLoading = cafesLoading || (activeCafeId !== null && (menuLoading || combosLoading));
```

**Результат:** Теперь корректно проверяется null вместо falsy значения. Loading state будет работать даже для кафе с ID=0.

---

### Issue #5 - ExtrasSection в UI (Important)

**Проблема:**
Данные extras fetching есть (строка 24), но компонент ExtrasSection не рендерился в UI.

**Было:**
```tsx
// ExtrasSection отсутствовал в render
{extrasLoading ? ... : extraItems && extraItems.length > 0 ? null : null}
```

**Исправлено:**
```tsx
// Добавлен импорт
import ExtrasSection from "@/components/ExtrasSection/ExtrasSection";

// Добавлен рендер после MenuSection (строки 194-203)
<div className="px-4 md:px-6 pt-4 pb-[180px]">
  {extrasLoading ? (
    <div className="flex items-center justify-center py-4">
      <FaSpinner className="text-white animate-spin" />
      <span className="ml-2 text-white">Загрузка дополнений...</span>
    </div>
  ) : extraItems && extraItems.length > 0 ? (
    <ExtrasSection extras={extraItems} cart={cart} addToCart={addToCart} removeFromCart={removeFromCart} />
  ) : null}
</div>
```

**Результат:** Теперь пользователь может добавлять extras (напитки, десерты) в корзину. Компонент отображается с loading state и graceful handling пустого состояния.

**Изменения в структуре:**
- Удалено `pb-[180px]` из MenuSection контейнера (строка 178)
- Добавлено `pb-[180px]` в ExtrasSection контейнер (строка 194) для корректного отступа от нижней корзины

---

### Issue #6 - activeCafeId fallback (Medium)

**Проблема:**
Строка 156: Fallback `activeCafeId || 0` может конфликтовать с валидным ID=0.

**Было:**
```tsx
<CafeSelector cafes={cafes} activeCafeId={activeCafeId || 0} onCafeClick={handleCafeClick} />
```

**Исправлено:**
```tsx
<CafeSelector cafes={cafes} activeCafeId={activeCafeId ?? -1} onCafeClick={handleCafeClick} />
```

**Результат:** Используется nullish coalescing оператор `??` вместо логического OR `||`. Fallback значение `-1` не конфликтует с валидными ID из БД (которые начинаются с 0 или 1).

---

### Итоговые изменения

**Измененные файлы:**
- `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/app/page.tsx`

**Количество исправлений:**
- Critical: 1 (useMemo → useEffect)
- Important: 2 (isLoading condition, ExtrasSection)
- Medium: 1 (activeCafeId fallback)

**Добавленные импорты:**
```tsx
// Строка 3
import { useState, useMemo, useEffect } from "react";

// Строка 11
import ExtrasSection from "@/components/ExtrasSection/ExtrasSection";
```

---

## Выводы

Интеграция Frontend с Backend API **завершена успешно**. Все mock данные заменены на реальные API calls через SWR hooks. Добавлены loading states, error handling и улучшен UX.

После code review были исправлены критические и важные проблемы:
- ✅ Правильное использование React hooks (useEffect вместо useMemo для side effects)
- ✅ Корректная проверка null для activeCafeId
- ✅ ExtrasSection теперь отображается в UI
- ✅ Безопасный fallback для activeCafeId

**Status: completed**
