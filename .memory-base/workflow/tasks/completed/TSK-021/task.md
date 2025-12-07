---
id: TSK-021
title: Добавить UI для управления расписанием дедлайнов заказов (Deadlines Schedule)
pipeline: feature
status: pending
created_at: 2025-12-07T10:57:58Z
related_files:
  - frontend_mini_app/src/app/manager/page.tsx
  - frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx
  - frontend_mini_app/src/lib/api/hooks.ts
  - frontend_mini_app/src/lib/api/client.ts
  - frontend_mini_app/src/lib/api/types.ts
  - backend/src/routers/deadlines.py
impact:
  api: нет (backend уже реализован)
  db: нет
  frontend: да
  services: нет
---

## Описание

У менеджера отсутствует UI для управления расписанием дедлайнов заказов (Deadlines Schedule) для кафе. Backend уже реализован и предоставляет API endpoints для получения и обновления расписания, но фронтенд компонент не создан.

**Текущая проблема:**
- В менеджерской панели (`/manager`) нет вкладки или секции для управления deadlines
- Невозможно настроить:
  - Дни недели, когда доступен заказ
  - Время дедлайна для каждого дня (например, "до 10:00")
  - За сколько дней можно заказать (advance_days)
  - Включение/выключение дней

**Требуемое поведение:**
Добавить новую вкладку "Расписание" в менеджерской панели с UI для настройки расписания дедлайнов для каждого кафе.

## Backend API (уже реализован)

### Endpoints

**GET /cafes/{cafe_id}/deadlines**
```
Auth: manager
Response: { schedules: DeadlineSchedule[] }
```

**PUT /cafes/{cafe_id}/deadlines**
```
Auth: manager
Body: { schedules: DeadlineScheduleInput[] }
Response: { schedules: DeadlineSchedule[] }
```

### Схемы

**DeadlineSchedule:**
```typescript
interface DeadlineSchedule {
  weekday: number;          // 0=Пн, 1=Вт, ..., 6=Вс
  weekday_name: string;     // "Понедельник", "Вторник", ...
  deadline_time: string;    // "10:00"
  is_enabled: boolean;
  advance_days: number;     // за сколько дней можно заказать (default: 1)
}
```

**DeadlineScheduleInput:**
```typescript
interface DeadlineScheduleInput {
  weekday: number;
  deadline_time?: string;   // optional
  is_enabled: boolean;
  advance_days?: number;    // optional
}
```

### API Reference

**Источник:** `.memory-base/tech-docs/api.md` (строки 337-366)

## Acceptance Criteria

### UI Компонент DeadlineSchedule

- [ ] Создать компонент `DeadlineSchedule.tsx` для управления расписанием
- [ ] Компонент должен показывать список из 7 дней недели (Пн-Вс)
- [ ] Для каждого дня показывать:
  - Название дня недели (readonly)
  - Checkbox "Включён" (is_enabled)
  - Input для времени дедлайна (deadline_time) — type="time"
  - Input для advance_days (за сколько дней заказ)
- [ ] Добавить dropdown для выбора кафе
- [ ] При выборе кафе загружать текущее расписание через GET /cafes/{cafe_id}/deadlines
- [ ] Кнопка "Сохранить" отправляет PUT /cafes/{cafe_id}/deadlines
- [ ] Показывать loading state во время загрузки и сохранения
- [ ] Показывать success/error уведомления после сохранения

### Интеграция в Manager Panel

- [ ] Добавить новую вкладку "Расписание" (или "Дедлайны") в `manager/page.tsx`
- [ ] Вкладка должна рендерить компонент `DeadlineSchedule`
- [ ] Стилизация в соответствии с дизайн-системой приложения (purple gradient, glassmorphism)

### API Hooks

- [ ] Создать hook `useDeadlineSchedule(cafeId: number | null)` для GET запроса
- [ ] Создать hook `useUpdateDeadlineSchedule()` для PUT запроса
- [ ] Hooks должны использовать SWR для кэширования
- [ ] После успешного обновления revalidate SWR cache

### TypeScript Types

- [ ] Добавить `DeadlineSchedule` interface в `types.ts`
- [ ] Добавить `DeadlineScheduleInput` interface в `types.ts`
- [ ] Добавить `DeadlineScheduleListResponse` interface в `types.ts`

## Контекст

### Существующие компоненты менеджерской панели

**Файл:** `frontend_mini_app/src/app/manager/page.tsx` (строки 45-61)

```typescript
type TabId = "users" | "user-requests" | "balances" | "cafes" | "menu" | "requests" | "reports";

const tabs: Tab[] = [
  { id: "users", name: "Пользователи", icon: <FaUsers /> },
  { id: "user-requests", name: "Запросы доступа", icon: <FaEnvelope /> },
  { id: "balances", name: "Балансы", icon: <FaWallet /> },
  { id: "cafes", name: "Кафе", icon: <FaStore /> },
  { id: "menu", name: "Меню", icon: <FaUtensils /> },
  { id: "requests", name: "Кафе запросы", icon: <FaEnvelope /> },
  { id: "reports", name: "Отчёты", icon: <FaChartBar /> },
];
```

**Нужно добавить:**
```typescript
{ id: "deadlines", name: "Расписание", icon: <FaCalendar /> }
```

### Дизайн-система приложения

**Цвета:**
- Background: `#130F30`
- Gradient: `from-[#8B23CB] to-[#A020F0]`
- Glass: `bg-white/5 backdrop-blur-md border border-white/10`
- Text: `text-white`, `text-gray-300`
- Success: `bg-green-500/20 border border-green-500/30 text-green-400`
- Error: `bg-red-500/20 border border-red-500/30 text-red-400`

**Компоненты:**
- Кнопки: gradient background с rounded-lg
- Inputs: glassmorphism с белой рамкой
- Иконки: `react-icons/fa6`

**Пример из ReportsList:**
```typescript
<input
  type="date"
  value={formData.date}
  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
  className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
/>
```

### Существующие API hooks паттерны

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts` (строки 264-275)

**Паттерн GET:**
```typescript
export function useSummaries(): UseDataResult<Summary> {
  const { data, error, isLoading, mutate } = useSWR<Summary[]>(
    "/summaries",
    fetcher
  );
  return {
    data,
    error,
    isLoading,
    mutate
  };
}
```

**Паттерн POST/PUT:**
```typescript
export function useCreateSummary(): {
  createSummary: (cafeId: number, date: string) => Promise<Summary>;
  isLoading: boolean;
  error: Error | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createSummary = async (cafeId: number, date: string): Promise<Summary> => {
    setIsLoading(true);
    setError(null);
    try {
      const summary = await apiRequest<Summary>("/summaries", {
        method: "POST",
        body: JSON.stringify({ cafe_id: cafeId, date }),
      });
      return summary;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return { createSummary, isLoading, error };
}
```

## Решение

### 1. Добавить TypeScript types

**Файл:** `frontend_mini_app/src/lib/api/types.ts` (добавить в конец)

```typescript
// Deadlines
export interface DeadlineSchedule {
  weekday: number;          // 0=Пн, 1=Вт, ..., 6=Вс
  weekday_name: string;     // "Понедельник", "Вторник", ...
  deadline_time: string;    // "10:00"
  is_enabled: boolean;
  advance_days: number;     // за сколько дней можно заказать
}

export interface DeadlineScheduleInput {
  weekday: number;
  deadline_time?: string;
  is_enabled: boolean;
  advance_days?: number;
}

export interface DeadlineScheduleListResponse {
  schedules: DeadlineSchedule[];
}
```

### 2. Создать API hooks

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts` (добавить в конец файла)

```typescript
/**
 * Hook to fetch deadline schedule for a cafe
 */
export function useDeadlineSchedule(cafeId: number | null): {
  data: DeadlineSchedule[] | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
} {
  const { data, error, isLoading, mutate } = useSWR<DeadlineScheduleListResponse>(
    cafeId ? `/cafes/${cafeId}/deadlines` : null,
    fetcher
  );
  return {
    data: data?.schedules,
    error,
    isLoading,
    mutate,
  };
}

/**
 * Hook to update deadline schedule for a cafe
 */
export function useUpdateDeadlineSchedule(): {
  updateSchedule: (cafeId: number, schedules: DeadlineScheduleInput[]) => Promise<DeadlineSchedule[]>;
  isLoading: boolean;
  error: Error | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const updateSchedule = async (
    cafeId: number,
    schedules: DeadlineScheduleInput[]
  ): Promise<DeadlineSchedule[]> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiRequest<DeadlineScheduleListResponse>(
        `/cafes/${cafeId}/deadlines`,
        {
          method: "PUT",
          body: JSON.stringify({ schedules }),
        }
      );
      return response.schedules;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return { updateSchedule, isLoading, error };
}
```

### 3. Создать компонент DeadlineSchedule

**Файл:** `frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx` (новый)

```typescript
"use client";

import React, { useState, useEffect } from "react";
import {
  useCafes,
  useDeadlineSchedule,
  useUpdateDeadlineSchedule,
} from "@/lib/api/hooks";
import type { DeadlineScheduleInput } from "@/lib/api/types";
import { FaSpinner, FaCheck, FaTriangleExclamation } from "react-icons/fa6";
import { mutate } from "swr";

const DeadlineSchedule: React.FC = () => {
  const { data: cafes, isLoading: cafesLoading } = useCafes(true, false);
  const [selectedCafeId, setSelectedCafeId] = useState<number | null>(null);
  const {
    data: schedules,
    isLoading: schedulesLoading,
    mutate: mutateSchedules,
  } = useDeadlineSchedule(selectedCafeId);
  const { updateSchedule, isLoading: updating } = useUpdateDeadlineSchedule();

  const [formData, setFormData] = useState<DeadlineScheduleInput[]>([]);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initialize form data when schedules load
  useEffect(() => {
    if (schedules) {
      setFormData(
        schedules.map((schedule) => ({
          weekday: schedule.weekday,
          deadline_time: schedule.deadline_time,
          is_enabled: schedule.is_enabled,
          advance_days: schedule.advance_days,
        }))
      );
    }
  }, [schedules]);

  const handleCafeChange = (cafeId: string) => {
    setSelectedCafeId(cafeId ? parseInt(cafeId) : null);
    setSuccessMessage(null);
    setErrorMessage(null);
  };

  const handleScheduleChange = (
    weekday: number,
    field: keyof DeadlineScheduleInput,
    value: string | boolean | number
  ) => {
    setFormData((prev) =>
      prev.map((schedule) =>
        schedule.weekday === weekday ? { ...schedule, [field]: value } : schedule
      )
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCafeId) {
      setErrorMessage("Пожалуйста, выберите кафе");
      return;
    }

    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      await updateSchedule(selectedCafeId, formData);
      setSuccessMessage("Расписание успешно сохранено");
      // Revalidate schedule
      mutateSchedules();
      // Also revalidate any other related caches
      mutate((key) => typeof key === "string" && key.includes("/deadlines"));
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Не удалось сохранить расписание"
      );
    }
  };

  if (cafesLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <FaSpinner className="text-white text-4xl animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white">
          Расписание дедлайнов заказов
        </h2>
      </div>

      {/* Cafe selector */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Выберите кафе
        </label>
        <select
          value={selectedCafeId || ""}
          onChange={(e) => handleCafeChange(e.target.value)}
          className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
        >
          <option value="" className="bg-[#130F30]">
            -- Выберите кафе --
          </option>
          {cafes?.map((cafe) => (
            <option key={cafe.id} value={cafe.id} className="bg-[#130F30]">
              {cafe.name}
            </option>
          ))}
        </select>
      </div>

      {/* Loading state */}
      {schedulesLoading && selectedCafeId && (
        <div className="flex items-center justify-center py-12">
          <FaSpinner className="text-white text-4xl animate-spin" />
        </div>
      )}

      {/* Schedule form */}
      {!schedulesLoading && selectedCafeId && schedules && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 space-y-4">
            {formData.map((schedule) => {
              const weekdayName =
                schedules.find((s) => s.weekday === schedule.weekday)
                  ?.weekday_name || "";

              return (
                <div
                  key={schedule.weekday}
                  className="flex flex-col md:flex-row md:items-center gap-4 pb-4 border-b border-white/10 last:border-b-0 last:pb-0"
                >
                  {/* Weekday name */}
                  <div className="w-full md:w-32 flex-shrink-0">
                    <span className="text-white font-medium">{weekdayName}</span>
                  </div>

                  {/* Enabled checkbox */}
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={schedule.is_enabled}
                      onChange={(e) =>
                        handleScheduleChange(
                          schedule.weekday,
                          "is_enabled",
                          e.target.checked
                        )
                      }
                      className="w-5 h-5 rounded border-white/20 bg-white/10 text-purple-500 focus:ring-2 focus:ring-purple-500"
                      disabled={updating}
                    />
                    <label className="text-gray-300 text-sm">Включён</label>
                  </div>

                  {/* Deadline time */}
                  <div className="flex-1">
                    <label className="block text-xs text-gray-400 mb-1">
                      Время дедлайна
                    </label>
                    <input
                      type="time"
                      value={schedule.deadline_time || ""}
                      onChange={(e) =>
                        handleScheduleChange(
                          schedule.weekday,
                          "deadline_time",
                          e.target.value
                        )
                      }
                      className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500 transition disabled:opacity-50"
                      disabled={!schedule.is_enabled || updating}
                    />
                  </div>

                  {/* Advance days */}
                  <div className="w-full md:w-32">
                    <label className="block text-xs text-gray-400 mb-1">
                      За сколько дней
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="7"
                      value={schedule.advance_days || 1}
                      onChange={(e) =>
                        handleScheduleChange(
                          schedule.weekday,
                          "advance_days",
                          parseInt(e.target.value)
                        )
                      }
                      className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500 transition disabled:opacity-50"
                      disabled={!schedule.is_enabled || updating}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Success message */}
          {successMessage && (
            <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-4 flex items-center gap-3">
              <FaCheck className="text-green-400 text-lg flex-shrink-0" />
              <p className="text-green-400 text-sm">{successMessage}</p>
            </div>
          )}

          {/* Error message */}
          {errorMessage && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
              <FaTriangleExclamation className="text-red-400 text-lg flex-shrink-0" />
              <p className="text-red-400 text-sm">{errorMessage}</p>
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={updating}
            className="w-full px-6 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-semibold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {updating ? (
              <>
                <FaSpinner className="animate-spin" />
                Сохранение...
              </>
            ) : (
              <>
                <FaCheck />
                Сохранить расписание
              </>
            )}
          </button>
        </form>
      )}

      {/* No cafe selected */}
      {!selectedCafeId && !cafesLoading && (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center">
          <p className="text-gray-400">Выберите кафе для настройки расписания</p>
        </div>
      )}
    </div>
  );
};

export default DeadlineSchedule;
```

### 4. Добавить вкладку в manager/page.tsx

**Файл:** `frontend_mini_app/src/app/manager/page.tsx`

**Изменение 1: Добавить import (после строки 18):**
```typescript
import DeadlineSchedule from "@/components/Manager/DeadlineSchedule";
```

**Изменение 2: Обновить TabId type (строка 45):**
```typescript
type TabId = "users" | "user-requests" | "balances" | "cafes" | "menu" | "deadlines" | "requests" | "reports";
```

**Изменение 3: Добавить tab (строки 53-61):**
```typescript
const tabs: Tab[] = [
  { id: "users", name: "Пользователи", icon: <FaUsers /> },
  { id: "user-requests", name: "Запросы доступа", icon: <FaEnvelope /> },
  { id: "balances", name: "Балансы", icon: <FaWallet /> },
  { id: "cafes", name: "Кафе", icon: <FaStore /> },
  { id: "menu", name: "Меню", icon: <FaUtensils /> },
  { id: "deadlines", name: "Расписание", icon: <FaCalendar /> },  // NEW
  { id: "requests", name: "Кафе запросы", icon: <FaEnvelope /> },
  { id: "reports", name: "Отчёты", icon: <FaChartBar /> },
];
```

**Примечание:** Нужно добавить import для `FaCalendar`:
```typescript
import {
  FaSpinner,
  FaTriangleExclamation,
  FaUsers,
  FaStore,
  FaUtensils,
  FaEnvelope,
  FaChartBar,
  FaChevronLeft,
  FaChevronRight,
  FaCartShopping,
  FaWallet,
  FaCalendar,  // NEW
} from "react-icons/fa6";
```

**Изменение 4: Добавить рендеринг вкладки (после строки 437, перед `{activeTab === "requests"`):**
```typescript
{activeTab === "deadlines" && (
  <div className="text-white">
    <DeadlineSchedule />
  </div>
)}
```

## Затронутые файлы

| Файл | Действие |
|------|----------|
| `frontend_mini_app/src/lib/api/types.ts` | Добавить: `DeadlineSchedule`, `DeadlineScheduleInput`, `DeadlineScheduleListResponse` interfaces |
| `frontend_mini_app/src/lib/api/hooks.ts` | Добавить: `useDeadlineSchedule()`, `useUpdateDeadlineSchedule()` hooks |
| `frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx` | Создать: новый компонент для управления расписанием |
| `frontend_mini_app/src/app/manager/page.tsx` | Обновить: добавить вкладку "Расписание" и рендеринг компонента |

## Тесты

**Manual Testing:**

1. **Загрузка расписания:**
   - Открыть менеджерскую панель → вкладка "Расписание"
   - Выбрать кафе из dropdown
   - Должно загрузиться текущее расписание (7 дней недели)
   - Проверить что поля заполнены корректно

2. **Редактирование расписания:**
   - Включить/выключить день через checkbox
   - Изменить время дедлайна
   - Изменить advance_days
   - Нажать "Сохранить"
   - Должно показаться сообщение "Расписание успешно сохранено"

3. **Валидация:**
   - Попробовать сохранить без выбора кафе → должна показаться ошибка
   - Попробовать ввести некорректное время → браузер должен валидировать

4. **Loading states:**
   - Проверить что показывается spinner при загрузке
   - Проверить что кнопка disabled во время сохранения

5. **Backend sync:**
   - После сохранения перезагрузить страницу
   - Проверить что изменения сохранились

## Приоритет

**High** — критичная функциональность для менеджеров, необходима для настройки системы заказов.

## Оценка сложности

**Medium:**
- Новый компонент с формой
- Два новых API hooks
- Интеграция в manager panel
- TypeScript types
- Тестирование

**Ориентировочное время:** 3-4 часа (включая тестирование и стилизацию).

## Примечания

**Backend уже готов:**
- API endpoints реализованы в `backend/src/routers/deadlines.py`
- Документация в `api.md` (строки 337-366)
- Эта задача фокусируется только на frontend UI

**Дизайн:**
- Использовать существующую дизайн-систему (glassmorphism, purple gradient)
- Следовать паттернам из `ReportsList`, `CafeList`, `MenuManager`
- Responsive layout (мобильные + десктоп)

**UX:**
- Dropdown для выбора кафе (как в ReportsList)
- Список дней недели с inline редактированием
- Disabled состояния для полей, когда день выключен
- Success/Error уведомления после сохранения

## Связанные задачи

- **TSK-005:** Управление deadlines (backend) — backend реализация (completed)
