---
agent: architect
task_id: TSK-021
status: completed
next: coder
created_at: 2025-12-07T11:15:00Z
---

# Архитектурное решение: Deadlines Schedule UI

## Анализ задачи

### Проблема
Менеджер не может управлять расписанием дедлайнов заказов через UI. Backend API уже реализован и работает, но фронтенд компонент отсутствует.

### Scope
- **Только frontend** — backend полностью готов
- Новая вкладка в manager panel
- Компонент для настройки расписания по дням недели
- API hooks для GET/PUT операций
- TypeScript types

### Затронутые компоненты
- Frontend: manager panel, API layer, types
- Backend: **нет изменений** (уже реализован)

## Архитектурные решения

### 1. API Response Schema

**Важное замечание:** Backend возвращает:
```typescript
{
  cafe_id: number;
  schedule: DeadlineItem[];
}
```

Но в task.md указан response:
```typescript
{ schedules: DeadlineSchedule[] }
```

**Решение:** Использовать актуальную схему backend (`{ cafe_id, schedule }`), т.к. backend уже реализован и работает.

### 2. Структура компонента DeadlineSchedule

**Компонент:** `frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx`

**Паттерн:** Следовать структуре `ReportsList.tsx`:
- Form для выбора кафе (dropdown)
- Loading states (skeleton, spinner)
- Error handling (error messages)
- Success/error notifications
- Glassmorphism styling

**State management:**
- `selectedCafeId` — выбранное кафе
- `formData` — локальные изменения расписания (массив DeadlineItem)
- `successMessage` / `errorMessage` — уведомления

**Workflow:**
1. Показать dropdown кафе
2. При выборе кафе → GET `/cafes/{cafe_id}/deadlines`
3. Заполнить форму данными из API
4. Пользователь редактирует (checkbox, time, number inputs)
5. При submit → PUT `/cafes/{cafe_id}/deadlines`
6. Revalidate cache, показать success/error

### 3. TypeScript Types

**Файл:** `frontend_mini_app/src/lib/api/types.ts`

**Добавить:**
```typescript
// Deadlines
export interface DeadlineItem {
  weekday: number;          // 0=Mon, 1=Tue, ..., 6=Sun
  deadline_time: string;    // "10:00"
  is_enabled: boolean;
  advance_days: number;
}

export interface DeadlineScheduleResponse {
  cafe_id: number;
  schedule: DeadlineItem[];
}
```

**Примечание:** Имя изменено с `DeadlineSchedule` на `DeadlineScheduleResponse`, чтобы избежать путаницы. `DeadlineItem` соответствует backend схеме.

### 4. API Hooks

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts`

**Hook 1: useDeadlineSchedule (GET)**
```typescript
export function useDeadlineSchedule(cafeId: number | null): {
  data: DeadlineItem[] | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}
```

Паттерн: SWR с динамическим endpoint (`cafeId ? ... : null`)

**Hook 2: useUpdateDeadlineSchedule (PUT)**
```typescript
export function useUpdateDeadlineSchedule(): {
  updateSchedule: (cafeId: number, schedule: DeadlineItem[]) => Promise<DeadlineItem[]>;
  isLoading: boolean;
  error: Error | null;
}
```

Паттерн: useState для loading/error, async функция для mutation

### 5. Manager Panel Integration

**Файл:** `frontend_mini_app/src/app/manager/page.tsx`

**Изменения:**

1. **Import:**
```typescript
import { FaCalendar } from "react-icons/fa6";
import DeadlineSchedule from "@/components/Manager/DeadlineSchedule";
```

2. **TabId type:**
```typescript
type TabId = "users" | "user-requests" | "balances" | "cafes" | "menu" | "deadlines" | "requests" | "reports";
```

3. **Tabs array:** Добавить после "menu":
```typescript
{ id: "deadlines", name: "Расписание", icon: <FaCalendar /> }
```

4. **Render logic:** Добавить case для deadlines tab:
```typescript
{activeTab === "deadlines" && (
  <div className="text-white">
    <DeadlineSchedule />
  </div>
)}
```

### 6. UI Design

**Дизайн-система:**
- Background: `#130F30`
- Gradient: `from-[#8B23CB] to-[#A020F0]`
- Glass: `bg-white/5 backdrop-blur-md border border-white/10`
- Input: `bg-white/10 border border-white/20`
- Success: `bg-green-500/20 border border-green-500/30 text-green-400`
- Error: `bg-red-500/20 border border-red-500/30 text-red-400`

**Weekday names (Russian):**
```typescript
const WEEKDAY_NAMES = [
  "Понедельник",  // 0
  "Вторник",      // 1
  "Среда",        // 2
  "Четверг",      // 3
  "Пятница",      // 4
  "Суббота",      // 5
  "Воскресенье"   // 6
];
```

**Layout для дня недели:**
```
┌─────────────────────────────────────────────────────────────┐
│ [Понедельник] [✓ Включён] [10:00] [За 1 день]             │
└─────────────────────────────────────────────────────────────┘
```

- Responsive: stack на мобильных, flex-row на десктопе
- Disabled поля когда `is_enabled = false`
- Disabled submit button когда загружается

## Декомпозиция задач

### Подзадача 1: Добавить TypeScript types
**Файл:** `frontend_mini_app/src/lib/api/types.ts`

**Действия:**
- Добавить `DeadlineItem` interface
- Добавить `DeadlineScheduleResponse` interface

**Зависимости:** Нет

---

### Подзадача 2: Создать API hooks
**Файл:** `frontend_mini_app/src/lib/api/hooks.ts`

**Действия:**
- Создать `useDeadlineSchedule()` hook для GET запроса
- Создать `useUpdateDeadlineSchedule()` hook для PUT запроса
- Оба hook должны использовать типы из types.ts

**Зависимости:** Подзадача 1 (types)

---

### Подзадача 3: Создать компонент DeadlineSchedule
**Файл:** `frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx` (новый)

**Действия:**
- Создать компонент с dropdown для выбора кафе
- Показать 7 дней недели с полями:
  - Checkbox `is_enabled`
  - Input `deadline_time` (type="time")
  - Input `advance_days` (type="number", min=0, max=7)
- Loading state (spinner)
- Success/error messages
- Submit button с disabled state
- Следовать дизайн-системе (glassmorphism, purple gradient)

**Зависимости:** Подзадача 2 (hooks)

---

### Подзадача 4: Интегрировать в manager panel
**Файл:** `frontend_mini_app/src/app/manager/page.tsx`

**Действия:**
- Добавить import `FaCalendar` из react-icons/fa6
- Добавить import `DeadlineSchedule` компонента
- Обновить `TabId` type
- Добавить вкладку "Расписание" в tabs array
- Добавить render case для `activeTab === "deadlines"`

**Зависимости:** Подзадача 3 (компонент)

---

## Порядок выполнения

1. **Подзадача 1** (types) → независима
2. **Подзадача 2** (hooks) → зависит от #1
3. **Подзадача 3** (компонент) → зависит от #2
4. **Подзадача 4** (интеграция) → зависит от #3

**Рекомендация:** Выполнять последовательно, т.к. есть цепочка зависимостей.

## Риски и митигации

### Риск 1: Несоответствие backend schema
**Проблема:** В task.md указан response `{ schedules: [] }`, но backend возвращает `{ cafe_id, schedule: [] }`

**Решение:** Использовать актуальную backend схему. Проверить реальные API responses при тестировании.

### Риск 2: Weekday mapping
**Проблема:** Python weekday (0=Monday) vs JS Date.getDay() (0=Sunday)

**Решение:** Backend использует Python weekday (0-6, Mon-Sun). Frontend должен отображать в том же порядке. Не использовать JS Date.getDay() для маппинга.

### Риск 3: Timezone issues
**Проблема:** Backend использует UTC, фронтенд может быть в другом timezone

**Решение:** Input type="time" работает без timezone. Backend хранит только время ("10:00"). Проблем быть не должно.

## Валидация

### Frontend валидация
- Кафе должно быть выбрано перед submit
- `deadline_time` — обязательное если `is_enabled = true`
- `advance_days` — min=0, max=7

### Backend валидация
- Backend уже имеет валидацию в schemas
- Фронтенд должен только корректно отправлять данные

## Тестирование

### Manual testing checklist
1. Открыть manager panel → вкладка "Расписание"
2. Выбрать кафе → должно загрузиться расписание
3. Изменить `is_enabled` → поля должны enable/disable
4. Изменить время и advance_days
5. Submit → должен показать success message
6. Перезагрузить страницу → изменения сохранились
7. Попробовать без выбора кафе → должна показаться ошибка
8. Проверить responsive на мобильном

### Edge cases
- Кафе без расписания (пустой ответ от backend)
- API error при загрузке
- API error при сохранении
- Network timeout

## Файлы для изменения

| Файл | Действие | Строки |
|------|----------|--------|
| `frontend_mini_app/src/lib/api/types.ts` | Добавить | ~20 строк |
| `frontend_mini_app/src/lib/api/hooks.ts` | Добавить | ~60 строк |
| `frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx` | Создать | ~250 строк |
| `frontend_mini_app/src/app/manager/page.tsx` | Изменить | ~10 строк |

**Итого:** ~340 строк нового/изменённого кода

## Референсы

### Существующие компоненты для примера
- `ReportsList.tsx` — dropdown кафе, form submit, success/error messages
- `BalanceManager.tsx` — таблица с inline редактированием
- `MenuManager.tsx` — списки с вложенными данными

### Backend endpoints
- GET `/cafes/{cafe_id}/deadlines` — реализован в `backend/src/routers/deadlines.py:18`
- PUT `/cafes/{cafe_id}/deadlines` — реализован в `backend/src/routers/deadlines.py:28`

### Backend schemas
- `DeadlineItem` — `backend/src/schemas/deadline.py:6`
- `DeadlineSchedule` — `backend/src/schemas/deadline.py:13`

## Дополнительные рекомендации

### Code style
- Use async/await (не .then/.catch)
- Use TypeScript strict mode types
- Prefer functional components
- Use Tailwind classes (не inline styles)

### Accessibility
- Label inputs с `<label>` tags
- Use semantic HTML
- Provide aria-labels для buttons

### Performance
- SWR автоматически кэширует GET запросы
- Используй `mutate()` для revalidation после PUT

---

## Готовность к разработке

Все подзадачи чётко определены и готовы к передаче Coder агенту. Архитектурное решение согласовано с существующим кодом и паттернами проекта.
