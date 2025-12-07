---
agent: coder
task_id: TSK-021
status: completed
next: reviewer
created_at: 2025-12-07T14:30:00Z
files_changed:
  - path: frontend_mini_app/src/lib/api/types.ts
    action: modified
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
  - path: frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx
    action: created
  - path: frontend_mini_app/src/app/manager/page.tsx
    action: modified
---

## Реализация

Успешно реализован UI для управления расписанием дедлайнов заказов (Deadlines Schedule) в панели менеджера.

## Изменения

### 1. `frontend_mini_app/src/lib/api/types.ts`

**Добавлены типы:**
- `DeadlineItem` — представляет один день в расписании (weekday, deadline_time, is_enabled, advance_days)
- `DeadlineScheduleResponse` — ответ API с расписанием для кафе (cafe_id, schedule)

### 2. `frontend_mini_app/src/lib/api/hooks.ts`

**Добавлены хуки:**
- `useDeadlineSchedule(cafeId)` — GET запрос для загрузки расписания кафе
  - Использует SWR для кеширования и автообновления
  - Возвращает: data, error, isLoading, mutate
- `useUpdateDeadlineSchedule()` — PUT запрос для обновления расписания
  - Использует useState для управления состоянием загрузки
  - Автоматически инвалидирует кеш после успешного обновления
  - Возвращает: updateSchedule(cafeId, schedule), isLoading, error

**Паттерны:**
- Следует существующим паттернам из hooks.ts
- SWR для GET запросов
- useState + async для мутаций
- Автоматическая revalidation через useSWRConfig

### 3. `frontend_mini_app/src/components/Manager/DeadlineSchedule.tsx` (новый файл)

**Структура компонента:**
- Dropdown для выбора кафе (useCafes hook)
- Форма с 7 днями недели (WEEKDAY_NAMES массив на русском)
- Для каждого дня:
  - Checkbox is_enabled
  - Input time (deadline_time)
  - Input number (advance_days, 0-6)
- Loading states (skeleton UI)
- Success/error сообщения
- Submit кнопка с индикатором загрузки

**Дизайн-система:**
- Glass эффект: `bg-white/5 backdrop-blur-md border border-white/10`
- Inputs: `bg-white/10 border border-white/20`
- Success: `bg-green-500/20 border border-green-500/30 text-green-400`
- Error: `bg-red-500/20 border border-red-500/30 text-red-400`
- Gradient кнопка: `from-[#8B23CB] to-[#A020F0]`

**Логика:**
- Инициализация formData из scheduleData при загрузке
- Если расписание не существует — дефолтные значения (все дни disabled, 10:00, 0 дней заранее)
- При смене кафе — очистка сообщений и перезагрузка данных
- Условный рендеринг полей (время и дни заранее) только для is_enabled=true
- Автоматическое скрытие success сообщения через 3 секунды

**Референсные паттерны:**
- Следует структуре ReportsList.tsx (dropdown кафе, форма, сообщения)
- Использует те же стили и компоненты UI

### 4. `frontend_mini_app/src/app/manager/page.tsx`

**Изменения:**
1. Import `FaCalendar` из react-icons/fa6
2. Import `DeadlineSchedule` компонента
3. Добавлен TabId: `"deadlines"`
4. Добавлен tab в массив tabs:
   ```typescript
   { id: "deadlines", name: "Расписание", icon: <FaCalendar /> }
   ```
5. Добавлен render case:
   ```typescript
   {activeTab === "deadlines" && (
     <div className="text-white">
       <DeadlineSchedule />
     </div>
   )}
   ```

## Backend API интеграция

Компонент готов к работе со следующими endpoints:
- `GET /cafes/{cafe_id}/deadlines` — получение расписания
- `PUT /cafes/{cafe_id}/deadlines` — обновление расписания (body: { schedule: DeadlineItem[] })

## Тестирование

**Рекомендуется протестировать:**
1. Выбор кафе из dropdown
2. Загрузка существующего расписания
3. Включение/выключение дней недели
4. Изменение времени дедлайна
5. Изменение количества дней заранее
6. Сохранение расписания
7. Success/error сообщения
8. Loading states
9. Responsive дизайн (mobile/desktop)

## Соответствие архитектурному плану

Все подзадачи из 01-architect.md выполнены:
- ✅ TypeScript types добавлены в types.ts
- ✅ API hooks созданы в hooks.ts (useDeadlineSchedule, useUpdateDeadlineSchedule)
- ✅ Компонент DeadlineSchedule.tsx создан с полным функционалом
- ✅ Интеграция в manager/page.tsx завершена

Код следует всем паттернам проекта:
- Дизайн-система (glass, gradients, colors)
- SWR для data fetching
- useState для mutations
- Русская локализация
- Responsive UI
- Loading/error states
