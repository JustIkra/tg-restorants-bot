---
agent: coder
task_id: TSK-009
subtask: 7
subtask_name: "Компоненты для запросов и отчётов"
status: completed
next: null
created_at: 2025-12-06T22:15:00+03:00
files_changed:
  - path: frontend_mini_app/src/lib/api/types.ts
    action: modified
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
  - path: frontend_mini_app/src/components/Manager/RequestsList.tsx
    action: created
  - path: frontend_mini_app/src/components/Manager/ReportsList.tsx
    action: created
---

## Реализация

Созданы компоненты для управления запросами на подключение кафе и отчётами в менеджерской панели.

### Изменения

#### `frontend_mini_app/src/lib/api/types.ts`

Добавлены новые TypeScript интерфейсы:

- **CafeRequest** — тип для запросов на подключение кафе
  - `id: number` — ID запроса
  - `cafe_name: string` — название кафе
  - `status: "pending" | "approved" | "rejected"` — статус запроса
  - `created_at: string` — дата создания запроса

- **Summary** — тип для отчётов
  - `id: number` — ID отчёта
  - `cafe_id: number` — ID кафе
  - `cafe_name: string` — название кафе
  - `date: string` — дата отчёта
  - `status: "pending" | "completed"` — статус отчёта
  - `created_at: string` — дата создания отчёта

#### `frontend_mini_app/src/lib/api/hooks.ts`

Добавлены новые SWR hooks для работы с API:

**Запросы на подключение:**
- `useCafeRequests()` — получение списка запросов (GET /cafe-requests)
- `useApproveCafeRequest()` — одобрение запроса (POST /cafe-requests/{id}/approve)
- `useRejectCafeRequest()` — отклонение запроса (POST /cafe-requests/{id}/reject)

**Отчёты:**
- `useSummaries()` — получение списка отчётов (GET /summaries)
- `useCreateSummary()` — создание отчёта (POST /summaries)
- `useDeleteSummary()` — удаление отчёта (DELETE /summaries/{id})

Все mutation hooks используют паттерн с `useState` для отслеживания состояния загрузки и ошибок.

#### `frontend_mini_app/src/components/Manager/RequestsList.tsx`

Компонент для отображения и управления запросами на подключение кафе.

**Функциональность:**
- Отображение списка всех запросов (pending, approved, rejected)
- Для pending запросов: кнопки "Одобрить" и "Отклонить"
- Для approved/rejected запросов: только отображение статуса
- Loading state с skeleton loaders
- Empty state для пустого списка
- Error handling с отображением ошибок
- Confirm dialog перед отклонением запроса
- Автоматическое обновление списка через `mutate()` после действий

**Дизайн:**
- Cards: `bg-white/5 backdrop-blur-md border border-white/10`
- Status badges:
  - Pending: `bg-yellow-500/20 text-yellow-400`
  - Approved: `bg-green-500/20 text-green-400`
  - Rejected: `bg-red-500/20 text-red-400`
- Форматирование даты в формате "дд.мм.гггг чч:мм"
- Кнопки с loading spinner при обработке
- Адаптивность: `flex-col sm:flex-row` для кнопок

#### `frontend_mini_app/src/components/Manager/ReportsList.tsx`

Компонент для отображения и управления отчётами.

**Функциональность:**
- Отображение списка всех отчётов
- Кнопка "Создать отчёт" → открывает форму
- Форма создания отчёта:
  - Dropdown выбора кафе (из `useCafes(false)`)
  - Date picker для выбора даты
  - Валидация обязательных полей
  - Отправка POST /summaries
- Кнопка "Удалить" для каждого отчёта
- Confirm dialog перед удалением
- Loading states, empty state, error handling
- Автоматическое обновление списка через `mutate()` после создания/удаления

**Дизайн:**
- Header с кнопкой "Создать отчёт"
- Форма создания: gradient submit button, styled inputs
- Cards для отчётов:
  - Название кафе + status badge
  - Дата отчёта (формат "дд.мм.гггг")
  - Дата создания (формат "дд.мм.гггг чч:мм")
  - Кнопка "Удалить" справа
- Status badges:
  - Pending: `bg-yellow-500/20 text-yellow-400`
  - Completed: `bg-green-500/20 text-green-400`
- Адаптивность для мобильных устройств

### Интеграция

Оба компонента готовы для интеграции в `/manager` страницу:

```tsx
// В manager/page.tsx
import RequestsList from "@/components/Manager/RequestsList";
import ReportsList from "@/components/Manager/ReportsList";

// В табах:
{activeTab === "requests" && <RequestsList />}
{activeTab === "reports" && <ReportsList />}
```

## Примечания

- **Переиспользование стилей:** компоненты следуют дизайн-системе проекта (purple gradients, blur backgrounds, loading spinners)
- **Консистентность:** используется тот же подход к error handling и loading states, что и в UserList/CafeList
- **Типобезопасность:** все типы экспортированы из types.ts
- **UX:** confirm dialogs перед деструктивными операциями (reject, delete)
- **Optimistic updates:** нет, используется revalidation через `mutate()` после успешных операций
- **Форматирование дат:** используется `toLocaleDateString("ru-RU")` для корректного отображения на русском языке

## Что нужно проверить

1. API endpoints `/cafe-requests` и `/summaries` возвращают данные в ожидаемом формате
2. POST endpoints для approve/reject/create/delete работают корректно
3. Роль "manager" имеет доступ к этим endpoints (403 для обычных пользователей)
4. Интеграция компонентов в /manager страницу с табами "Запросы" и "Отчёты"
5. Мобильная адаптивность в Telegram Mini App
