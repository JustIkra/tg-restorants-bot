---
agent: coder
task_id: TSK-016
subtask: frontend (7-9)
status: completed
next: reviewer
created_at: 2025-12-07T04:30:00Z
files_changed:
  - path: frontend_mini_app/src/lib/api/types.ts
    action: modified
  - path: frontend_mini_app/src/lib/api/client.ts
    action: modified
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
  - path: frontend_mini_app/src/components/Manager/UserRequestCard.tsx
    action: created
  - path: frontend_mini_app/src/components/Manager/UserRequestsList.tsx
    action: created
  - path: frontend_mini_app/src/components/Manager/UserEditModal.tsx
    action: created
  - path: frontend_mini_app/src/components/Manager/UserList.tsx
    action: modified
  - path: frontend_mini_app/src/app/manager/page.tsx
    action: modified
---

## Реализация

Успешно реализованы все frontend компоненты для управления запросами на доступ пользователей и редактирования пользователей в Manager Panel. Реализация следует существующим паттернам проекта и использует установленные стили Tailwind CSS 4.

### Изменения

#### `frontend_mini_app/src/lib/api/types.ts`

Добавлены новые типы для работы с User Access Requests:

- **UserAccessRequestStatus** — тип для статусов запросов ("pending" | "approved" | "rejected")
- **UserAccessRequest** — интерфейс для запроса на доступ (id, tgid, name, office, username, status, processed_at, created_at)
- **UserAccessRequestListResponse** — обёртка для списка запросов (items, total)
- **UserUpdate** — интерфейс для обновления пользователя (name?, office?, role?)

#### `frontend_mini_app/src/lib/api/client.ts`

Добавлены API методы для работы с user-requests:

- **getUserRequests(status?)** — получить список запросов на доступ с опциональным фильтром по статусу
- **approveUserRequest(requestId)** — одобрить запрос на доступ (POST /user-requests/{id}/approve)
- **rejectUserRequest(requestId)** — отклонить запрос на доступ (POST /user-requests/{id}/reject)
- **updateUser(tgid, data)** — обновить данные пользователя (PATCH /users/{tgid})

Все методы используют `apiRequest` helper для единообразной обработки ошибок и JWT авторизации.

#### `frontend_mini_app/src/lib/api/hooks.ts`

Добавлены React hooks для работы с user-requests API:

- **useUserRequests(status?)** — SWR hook для загрузки списка запросов с опциональным фильтром
- **useApproveRequest()** — mutation hook для одобрения запросов с автоматической ревалидацией
- **useRejectRequest()** — mutation hook для отклонения запросов с автоматической ревалидацией
- **useUpdateUser()** — mutation hook для обновления пользователей с ревалидацией списка

Все hooks следуют паттерну существующих hooks в проекте (useCafeRequests, useApproveCafeRequest).

#### `frontend_mini_app/src/components/Manager/UserRequestCard.tsx` (новый)

Компонент карточки запроса на доступ:

- Отображает информацию о запросе (имя, username/tgid, офис, дату создания)
- Показывает статус с цветными бэйджами (pending/approved/rejected)
- Кнопки Approve/Reject для pending запросов
- Loading states с анимированными спиннерами
- Следует стилям из RequestsList.tsx (cafe requests)

#### `frontend_mini_app/src/components/Manager/UserRequestsList.tsx` (новый)

Компонент списка запросов на доступ:

- Фильтрация по статусу (Все / Ожидают / Одобрено / Отклонено)
- Использует useUserRequests hook для загрузки данных
- Обработка approve/reject с подтверждением для reject
- Loading skeleton состояние
- Error handling с красными уведомлениями
- Empty state для пустых списков
- Следует паттерну существующего RequestsList компонента

#### `frontend_mini_app/src/components/Manager/UserEditModal.tsx` (новый)

Модальное окно для редактирования пользователя:

- Поля: Telegram ID (readonly), Имя, Офис, Роль (user/manager)
- Валидация полей (обязательные, минимальная длина)
- Отправляет только изменённые поля (оптимизация)
- Закрывается по Escape или кнопке Отмена
- Loading state во время submit
- Error handling с отображением ошибок
- Следует стилям UserForm.tsx

#### `frontend_mini_app/src/components/Manager/UserList.tsx`

Добавлена поддержка редактирования пользователей:

- Добавлен prop `onEdit: (user: User) => void`
- Кнопка "Изменить" для каждого пользователя
- Кнопка использует синие цвета (bg-blue-500/20) для отличия от других действий
- Расположена первой в списке кнопок действий

#### `frontend_mini_app/src/app/manager/page.tsx`

Интеграция новых компонентов в Manager Panel:

**Добавлен tab "user-requests":**
- Новый таб "Запросы доступа" между "Пользователи" и "Балансы"
- Отображает компонент UserRequestsList
- Использует существующую Tab систему с горизонтальным скроллом

**Обновлён tab "users":**
- Добавлена кнопка "Изменить" в UserList
- Модальное окно UserEditModal для редактирования пользователей
- Интеграция useUpdateUser hook

**State management:**
- `editingUser: User | null` — состояние для выбранного пользователя
- `updateUser` — функция из useUpdateUser hook
- Обработка onEdit, onSubmit, onClose для модалки

**Renamed existing tab:**
- "Запросы" → "Кафе запросы" (для ясности, что это cafe link requests)

## Примечания

### Ключевые архитектурные решения

1. **Следование существующим паттернам:**
   - API hooks используют тот же паттерн, что useCafeRequests/useApproveCafeRequest
   - Компоненты следуют стилям UserList, RequestsList, UserForm
   - Модальное окно использует те же стили и структуру, что и формы в проекте

2. **SWR для кэширования и ревалидации:**
   - useUserRequests использует SWR для автоматического кэширования
   - approve/reject автоматически ревалидируют списки запросов
   - updateUser ревалидирует список пользователей

3. **Оптимизация запросов:**
   - UserEditModal отправляет только изменённые поля
   - Status фильтр в UserRequestsList использует query параметр
   - SWR dedupe предотвращает дублирование запросов

4. **UX improvements:**
   - Confirmation для reject запросов (destructive action)
   - Loading states с анимированными спиннерами
   - Error messages с понятными текстами на русском
   - Keyboard shortcut (Escape) для закрытия модалки

5. **Цветовая схема:**
   - Pending: yellow (bg-yellow-500/20)
   - Approved: green (bg-green-500/20)
   - Rejected: red (bg-red-500/20)
   - Edit button: blue (bg-blue-500/20)
   - Следует существующим цветам проекта

### Соответствие требованиям

Все подзадачи выполнены согласно архитектурному плану:

**Подзадача 7:** API hooks и типы
- ✓ Типы UserAccessRequest, UserAccessRequestStatus, UserUpdate
- ✓ Hooks useUserRequests, useApproveRequest, useRejectRequest, useUpdateUser
- ✓ API методы в client.ts

**Подзадача 8:** Компоненты для User Requests
- ✓ UserRequestCard с кнопками Approve/Reject
- ✓ UserRequestsList с фильтрацией по статусу
- ✓ UserEditModal для редактирования пользователя

**Подзадача 9:** Интеграция в Manager Page
- ✓ Вкладка "Запросы доступа" в Tab системе
- ✓ Секция редактирования пользователей
- ✓ Интеграция всех новых компонентов

### Тестирование

Для тестирования необходимо:

1. Запустить backend с миграцией для user_access_requests
2. Создать несколько запросов на доступ (POST /auth/telegram с новым tgid)
3. Открыть Manager Panel → вкладка "Запросы доступа"
4. Протестировать фильтрацию, approve, reject
5. Открыть вкладку "Пользователи"
6. Протестировать редактирование пользователя (имя, офис, роль)

### Потенциальные улучшения (не в scope текущей задачи)

1. Real-time updates через WebSocket для новых запросов
2. Pagination для больших списков запросов
3. Bulk operations (одобрить/отклонить несколько запросов)
4. Audit log для изменений пользователей
5. Search/filter в списке пользователей
