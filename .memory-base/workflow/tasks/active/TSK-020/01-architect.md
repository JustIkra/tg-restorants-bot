---
agent: architect
task_id: TSK-020
status: completed
next: coder
created_at: 2025-12-07T10:30:00Z
---

## Анализ

### Backend готов (TSK-016)

✅ **Backend полностью реализован и не требует изменений:**

1. **Auth endpoint** (`/Users/maksim/git_projects/tg_bot/backend/src/routers/auth.py`):
   - `POST /auth/telegram` создаёт `UserAccessRequest` для новых пользователей (строки 106-121)
   - Возвращает 403 с информативными сообщениями:
     - "Access request created. Please wait for manager approval." — новый запрос
     - "Access request pending approval" — запрос в ожидании
     - "Access request rejected" — отклонённый запрос

2. **Schema поддерживает office** (`/Users/maksim/git_projects/tg_bot/backend/src/auth/schemas.py`):
   ```python
   class TelegramAuthRequest(BaseModel):
       init_data: str
       office: str = "Default Office"  # ✅ Уже есть, значение по умолчанию
   ```
   - Поле `office` присутствует в схеме
   - Backend обрабатывает office в auth.py (строки 61-62, 111)

3. **User access requests компоненты уже существуют (для менеджера):**
   - `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/Manager/UserRequestCard.tsx` — карточка запроса
   - `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/Manager/UserRequestsList.tsx` — список запросов
   - Эти компоненты для менеджерской панели, не для обычного пользователя

### Текущая проблема во frontend

**Файл:** `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/app/page.tsx`

**Проблема 1: Простая обработка ошибок** (строки 94-113):
```typescript
authenticateWithTelegram(initData)
  .then(...)
  .catch(err => {
    // Любая ошибка показывается как общая ошибка
    const errorMessage = err instanceof Error ? err.message : ...
    setAuthError(errorMessage);
  });
```
- Нет различия между типами ошибок (403, 401, 500)
- Не парсится сообщение backend для определения типа 403 (created/pending/rejected)
- Показывается только общий экран ошибки (строки 340-350)

**Проблема 2: API client не поддерживает office** (`/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/lib/api/client.ts`):
```typescript
export async function authenticateWithTelegram(
  initData: string
  // Нет параметра office
)
```

**Проблема 3: Нет компонента формы запроса доступа для обычного пользователя**
- Существующие компоненты (UserRequestCard, UserRequestsList) для менеджера
- Нужен новый компонент AccessRequestForm для обычных пользователей

### Telegram user data доступен

**Файл:** `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/lib/telegram/webapp.ts`

Есть функция `getTelegramUser()` (строки 125-131):
```typescript
export function getTelegramUser() {
  if (typeof window === 'undefined' || !isTelegramWebApp()) {
    return null;
  }
  return WebApp.initDataUnsafe?.user || null;
}
```

Возвращает объект:
```typescript
{
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  // ... другие поля
}
```

Эту функцию можно использовать для получения данных Telegram пользователя для формы.

## Архитектурное решение

### Подход

Создать multi-state auth flow во frontend с формой запроса доступа для новых пользователей:

```
[Telegram WebApp] → POST /auth/telegram (без office)
                           ↓
          ┌─────────────────────────────────────┐
          │      Backend response               │
          └─────────────────────────────────────┘
                           ↓
     ┌───────────────────────────────────────────────┐
     │ 200 OK (успех)        │ 403 (ошибки доступа)  │ 401/500 (другие)
     └───────────────────────┴───────────────────────┘
            ↓                          ↓                       ↓
    authenticated           Parse error message         general error
            ↓                          ↓
       Main App UI          ┌─────────────────┐
                            │ "created"       │ → показать pending message
                            │ "pending"       │ → показать pending message
                            │ "rejected"      │ → показать rejected message
                            └─────────────────┘
```

**Важно:** Backend создаёт UserAccessRequest автоматически при первом заходе, но использует дефолтный office "Default Office". Пользователь должен иметь возможность указать свой офис.

**Решение:** Показывать форму AccessRequestForm для новых пользователей ПЕРЕД первым вызовом `/auth/telegram`.

### Auth states

Определить следующие состояния:

```typescript
type AuthState =
  | "loading"           // Начальная проверка Telegram
  | "needs_request"     // Новый пользователь, нужна форма
  | "success"           // Успешная авторизация
  | "pending"           // Запрос ожидает одобрения
  | "rejected"          // Запрос отклонён
  | "error";            // Общая ошибка
```

### Frontend компоненты

**1. AccessRequestForm component:**
- Форма с полями: name (readonly), username (readonly), office (input)
- При submit вызывает `authenticateWithTelegram(initData, office)`
- Обрабатывает loading state и ошибки

**2. Информационные экраны в page.tsx:**
- Pending message — "Запрос отправлен, ожидайте одобрения"
- Rejected message — "Запрос отклонён, обратитесь к менеджеру"

### API client

**Обновить `authenticateWithTelegram`:**
- Добавить необязательный параметр `office?: string`
- Передавать office в request body если предоставлен

### UX Flow

**Сценарий 1: Новый пользователь (первый раз):**
1. Telegram initData проверяется
2. **НЕ вызываем** `/auth/telegram` сразу
3. Показываем форму AccessRequestForm
4. Пользователь вводит office
5. Submit формы → `authenticateWithTelegram(initData, office)`
6. Backend создаёт запрос → 403 "Access request created..."
7. Показываем pending screen

**Сценарий 2: Пользователь с pending запросом:**
1. Вызываем `/auth/telegram` без office
2. Backend возвращает 403 "Access request pending approval"
3. Показываем pending screen

**Сценарий 3: Пользователь с rejected запросом:**
1. Вызываем `/auth/telegram` без office
2. Backend возвращает 403 "Access request rejected"
3. Показываем rejected screen

**Сценарий 4: Одобренный пользователь:**
1. Вызываем `/auth/telegram`
2. Backend возвращает 200 + JWT
3. Показываем main app UI

**Проблема:** Как определить, что пользователь новый (для показа формы)?

**Решение:**
1. Сначала вызываем `/auth/telegram` без office
2. Если 403 с "Access request created" → backend автоматически создал запрос с дефолтным офисом
3. Пользователь уже будет иметь pending запрос при следующем заходе
4. **НЕТ** способа показать форму ДО первого вызова

**Альтернативное решение (правильное):**
1. Показываем форму AccessRequestForm ВСЕГДА при первом заходе нового пользователя
2. Для определения "новый пользователь" нужно либо:
   - Сохранять флаг в localStorage (ненадёжно)
   - Backend должен возвращать специальный статус для "новых" пользователей

**Но backend уже реализован и создаёт запрос автоматически.**

**Компромиссное решение:**
Backend создаст запрос с дефолтным офисом "Default Office" при первом заходе. Это приемлемо для MVP. Если нужна форма — требуется изменение backend логики.

**Финальное решение (согласно требованиям пользователя):**
Нужна возможность пользователю указать офис. Реализуем через:
1. Показываем форму при состоянии "needs_request"
2. "needs_request" определяется если:
   - Нет токена в localStorage
   - Первый заход в приложение
3. Форма отправляет office вместе с initData

**Логика определения needs_request:**
- Проверяем localStorage.getItem("access_request_sent")
- Если нет — показываем форму
- После отправки формы — устанавливаем флаг
- При успешной авторизации — очищаем флаг

Это не идеально (localStorage может быть очищен), но работает для MVP.

## Подзадачи для Coder

### 1. Создать компонент AccessRequestForm

**Файл:** `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/AccessRequestForm/AccessRequestForm.tsx` (новый)

**Действия:**
- Создать React компонент с props: `{ name, username, onSubmit, onSuccess }`
- Форма с полями:
  - Имя (readonly, из props)
  - Username (readonly, из props, опционально)
  - Офис (input, обязательное)
  - Кнопка "Отправить запрос"
- Стилизация: glassmorphism, purple gradient, как в существующих компонентах
- Валидация: офис не должен быть пустым
- Loading state при submit
- Обработка ошибок

**Параллельно:** ДА — можно делать параллельно с подзадачей 3

**Детали:**
- Использовать иконки из `react-icons/fa6`: FaUser, FaBuilding, FaPaperPlane, FaSpinner
- Центрированный экран на весь viewport
- Responsive дизайн

### 2. Обновить API client для поддержки office

**Файл:** `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/lib/api/client.ts`

**Действия:**
- Обновить функцию `authenticateWithTelegram`:
  - Добавить параметр `office?: string`
  - Передавать office в request body если предоставлен

**Параллельно:** НЕТ — должно быть выполнено перед подзадачей 3

**Код:**
```typescript
export async function authenticateWithTelegram(
  initData: string,
  office?: string
): Promise<{ access_token: string; user: User }> {
  const response = await apiRequest<{ access_token: string; user: User }>(
    "/auth/telegram",
    {
      method: "POST",
      body: JSON.stringify({
        init_data: initData,
        ...(office && { office })
      }),
    }
  );

  // Save token
  setToken(response.access_token);

  return response;
}
```

### 3. Обновить логику авторизации в page.tsx

**Файл:** `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/app/page.tsx`

**Действия:**
1. Добавить состояния:
   - `authState: AuthState`
   - `telegramUserData: { name: string; username: string | null } | null`

2. Обновить логику useEffect для определения начального состояния:
   - Проверить localStorage флаг "access_request_sent"
   - Если нет токена и нет флага → `setAuthState("needs_request")`
   - Иначе → попытаться авторизоваться

3. Обновить catch в `authenticateWithTelegram`:
   - Получить Telegram user data через `getTelegramUser()`
   - Парсить error message:
     - "Access request created" → `setAuthState("pending")` + установить флаг
     - "Access request pending" → `setAuthState("pending")`
     - "Access request rejected" → `setAuthState("rejected")`
     - Иначе → `setAuthState("error")`

4. Добавить handler для формы:
   ```typescript
   const handleAccessRequestSubmit = async (office: string) => {
     const initData = getTelegramInitData();
     if (!initData) throw new Error("Telegram initData недоступен");

     await authenticateWithTelegram(initData, office);
     localStorage.setItem("access_request_sent", "true");
   };

   const handleAccessRequestSuccess = () => {
     setAuthState("pending");
   };
   ```

5. Обновить рендеринг:
   - `authState === "needs_request"` → показать AccessRequestForm
   - `authState === "pending"` → показать pending screen
   - `authState === "rejected"` → показать rejected screen
   - `authState === "error"` → показать error screen
   - `authState === "success"` → показать main app UI

**Параллельно:** ДА — можно делать параллельно с подзадачей 1

**Детали:**
- Импортировать AccessRequestForm
- Импортировать getTelegramUser из @/lib/telegram/webapp
- Использовать существующие иконки (FaSpinner, FaTriangleExclamation)
- Информационные экраны: glassmorphism, центрированы, responsive

## Риски и зависимости

### Риски

1. **localStorage флаг может быть очищен:**
   - Пользователь увидит форму повторно
   - **Митигация:** При успешной авторизации очищаем флаг

2. **Парсинг error message может быть хрупким:**
   - Если backend изменит текст сообщений, frontend сломается
   - **Митигация:** Использовать `includes()` вместо точного сравнения

3. **Backend может вернуть неожиданный формат ошибки:**
   - **Митигация:** Fallback на общий error state для неизвестных ошибок

### Зависимости

✅ **Нет зависимостей:**
- Backend уже реализован (TSK-016)
- Все необходимые API endpoints работают
- Schema поддерживает office
- Frontend утилиты (getTelegramUser) существуют

### Затронутые файлы

| Файл | Действие |
|------|----------|
| `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/AccessRequestForm/AccessRequestForm.tsx` | Создать: новый компонент формы |
| `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/lib/api/client.ts` | Обновить: добавить параметр office |
| `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/app/page.tsx` | Обновить: добавить authState, логику, информационные экраны |

**Всего: 3 файла (1 новый, 2 обновления)**

## Итоговая архитектура

### Новый auth flow

```
User → Telegram Mini App → page.tsx
                                ↓
                     Check localStorage flag
                                ↓
              ┌─────────────────────────────┐
              │ No token & no flag          │ Has token or flag
              └─────────────────────────────┘
                        ↓                            ↓
         Show AccessRequestForm          Try authenticateWithTelegram
                        ↓                            ↓
         User enters office            ┌─────────────────────────┐
                        ↓                │ 200 OK  │ 403 Forbidden │ 401/500
   Submit → authenticateWithTelegram    └─────────────────────────┘
              (initData, office)                ↓            ↓         ↓
                        ↓                   success    Parse msg   error
              POST /auth/telegram                     ↓
                        ↓                   ┌─────────────────┐
                  403 Created               │ created/pending │ → pending screen
                        ↓                   │ rejected        │ → rejected screen
              Set localStorage flag         └─────────────────┘
                        ↓
             Show pending screen
```

### UI states

| AuthState | Экран | Описание |
|-----------|-------|----------|
| `loading` | Spinner "Авторизация..." | Начальная проверка Telegram |
| `needs_request` | AccessRequestForm | Форма запроса доступа |
| `success` | Main App UI | Пользователь авторизован |
| `pending` | Pending message | Запрос в обработке |
| `rejected` | Rejected message | Запрос отклонён |
| `error` | Error message | Общая ошибка |

### Дизайн-система

**Используемые стили:**
- Background: `bg-[#130F30]`
- Gradient: `from-[#8B23CB] to-[#A020F0]`
- Glass: `bg-white/5 backdrop-blur-md border border-white/10`
- Text: `text-white`, `text-gray-300`
- Округление: `rounded-lg`, `rounded-2xl`

**Иконки:**
- react-icons/fa6: FaUser, FaBuilding, FaPaperPlane, FaSpinner, FaTriangleExclamation

### Преимущества решения

1. **Пользователь может указать офис** — требование выполнено
2. **Минимальные изменения backend** — используем существующий endpoint
3. **Чёткие UI states** — пользователь всегда понимает что происходит
4. **Graceful degradation** — если localStorage очищен, форма покажется повторно (не критично)

### Ограничения

1. **localStorage флаг не идеален:**
   - Может быть очищен пользователем
   - Не синхронизируется между устройствами
   - **Но:** приемлемо для MVP, т.к. повторный показ формы не критичен

2. **Backend создаёт запрос с любым office:**
   - Нет валидации списка офисов
   - **Но:** это решается на уровне менеджерской панели (можно отклонить неправильный офис)
