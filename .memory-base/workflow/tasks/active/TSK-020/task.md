---
id: TSK-020
title: Добавить UI формы запроса доступа для незарегистрированных пользователей
pipeline: feature
status: pending
created_at: 2025-12-07T10:15:00Z
related_files:
  - frontend_mini_app/src/app/page.tsx
  - frontend_mini_app/src/components/AccessRequestForm/AccessRequestForm.tsx
  - frontend_mini_app/src/lib/api/client.ts
  - backend/src/routers/auth.py
  - backend/src/auth/schemas.py
impact:
  api: нет (уже реализовано в TSK-016)
  db: нет
  frontend: да
  services: нет
---

## Описание

При заходе с незарегистрированного пользователя должно появляться окно составления запроса на предоставление доступа для последующего одобрения менеджером.

**Текущая проблема:**
На скриншоте показано текущее состояние: экран "Авторизация..." (спиннер загрузки). После неудачной авторизации показывается только общая ошибка вместо формы запроса доступа.

**Требуемое поведение:**
Вместо бесконечной загрузки или общей ошибки должна показываться форма запроса доступа с полями:
- Имя (автозаполняется из Telegram)
- Офис (dropdown или text input)
- Telegram username (readonly, из Telegram)
- Кнопка "Отправить запрос"

## Проблема

**Backend уже реализован в TSK-016:**
- `POST /auth/telegram` создаёт `UserAccessRequest` для новых пользователей
- Возвращает `403 Forbidden` с сообщением:
  - `"Access request created. Please wait for manager approval."` — для новых пользователей
  - `"Access request pending approval"` — для пользователей с pending запросом
  - `"Access request rejected"` — для пользователей с отклонённым запросом

**Frontend не обрабатывает эти случаи правильно:**
- `frontend_mini_app/src/app/page.tsx` (строки 94-113) показывает только общую ошибку при 403
- Нет компонента формы запроса доступа
- Нет логики определения типа ошибки (новый пользователь vs pending vs rejected)

## Acceptance Criteria

### UI компонент AccessRequestForm

- [ ] Создать компонент `AccessRequestForm.tsx` с полями:
  - Имя (readonly, из Telegram initData)
  - Офис (select или input)
  - Username (readonly, из Telegram initData)
  - Кнопка "Отправить запрос"
- [ ] Форма должна быть стилизована в соответствии с дизайн-системой приложения (purple gradient, glassmorphism)
- [ ] При отправке показывать loading состояние на кнопке
- [ ] После успешной отправки показывать сообщение "Запрос отправлен. Ожидайте одобрения менеджера."

### Логика обработки auth errors в page.tsx

- [ ] Различать типы 403 ошибок по тексту сообщения:
  - `"Access request created"` → показать success message
  - `"Access request pending"` → показать pending message
  - `"Access request rejected"` → показать rejected message с инструкциями
- [ ] Для новых пользователей (без запроса) показывать форму `AccessRequestForm`
- [ ] Для pending запросов показывать информационное сообщение
- [ ] Для rejected запросов показывать сообщение с контактами менеджера

### Backend (уже реализовано в TSK-016)

- [x] `POST /auth/telegram` создаёт UserAccessRequest
- [x] Endpoint возвращает 403 с информативным сообщением
- [x] TelegramAuthRequest schema включает поле `office`

**Примечание:** Backend уже готов, не требует изменений.

### UX Flow

1. **Новый пользователь заходит первый раз:**
   - Frontend: `POST /auth/telegram` с initData
   - Backend: создаёт UserAccessRequest, возвращает 403 "Access request created..."
   - Frontend: показывает success message "Запрос отправлен. Ожидайте одобрения."

2. **Пользователь с pending запросом заходит повторно:**
   - Frontend: `POST /auth/telegram`
   - Backend: находит pending запрос, возвращает 403 "Access request pending approval"
   - Frontend: показывает информационное сообщение "Ваш запрос ожидает одобрения менеджера."

3. **Пользователь с rejected запросом заходит:**
   - Frontend: `POST /auth/telegram`
   - Backend: находит rejected запрос, возвращает 403 "Access request rejected"
   - Frontend: показывает сообщение "Ваш запрос был отклонён. Обратитесь к менеджеру."

## Контекст

### Существующий код авторизации

**Файл:** `frontend_mini_app/src/app/page.tsx` (строки 88-113)

```typescript
authenticateWithTelegram(initData)
  .then((response) => {
    setIsAuthenticated(true);
    setUser(response.user);
    console.log("Telegram auth successful");

    // Save user object to localStorage
    localStorage.setItem("user", JSON.stringify(response.user));

    // Manager can stay on main page - no automatic redirect
  })
  .catch(err => {
    console.error("Telegram auth failed:", err);
    const errorMessage = err instanceof Error
      ? err.message
      : typeof err === 'string'
        ? err
        : (err?.detail || err?.message || "Не удалось авторизоваться");
    setAuthError(errorMessage);
  });
```

**Проблема:**
- Любая ошибка auth показывается как общее сообщение
- Нет различия между 403 (access request), 401 (invalid initData), 500 (server error)

### Backend auth endpoint

**Файл:** `backend/src/routers/auth.py` (строки 106-121)

```python
# No request exists - create new request
name = f"{tg_user['first_name']} {tg_user.get('last_name', '')}".strip()
new_request = UserAccessRequest(
    tgid=tgid,
    name=name or f"User {tgid}",
    office=request.office,
    username=tg_user.get("username"),
    status=UserAccessRequestStatus.PENDING,
)
db.add(new_request)
await db.commit()

raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Access request created. Please wait for manager approval.",
)
```

**Примечание:**
- Backend ожидает поле `office` в `TelegramAuthRequest`
- Если `office` не передано, будет `None` (nullable в schema)

### TelegramAuthRequest schema

**Файл:** `backend/src/auth/schemas.py`

Нужно проверить, есть ли поле `office` в схеме:

```python
class TelegramAuthRequest(BaseModel):
    init_data: str
    office: str | None = None  # Предполагаемая схема
```

**Если поля нет, нужно добавить.**

### Frontend API client

**Файл:** `frontend_mini_app/src/lib/api/client.ts` (строки 119-134)

```typescript
export async function authenticateWithTelegram(
  initData: string
): Promise<{ access_token: string; user: User }> {
  const response = await apiRequest<{ access_token: string; user: User }>(
    "/auth/telegram",
    {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    }
  );

  // Save token
  setToken(response.access_token);

  return response;
}
```

**Проблема:**
- Функция не поддерживает передачу `office`
- Нужно добавить параметр `office?: string`

### Дизайн-система приложения

**Цвета:**
- Background: `#130F30`
- Gradient: `from-[#8B23CB] to-[#A020F0]`
- Glass: `bg-white/5 backdrop-blur-md border border-white/10`
- Text: `text-white`, `text-gray-300`

**Компоненты:**
- Кнопки: gradient background с rounded-lg
- Inputs: glassmorphism с белой рамкой
- Иконки: `react-icons/fa6`

## Решение

### 1. Создать компонент AccessRequestForm

**Файл:** `frontend_mini_app/src/components/AccessRequestForm/AccessRequestForm.tsx` (новый)

```typescript
"use client";

import { useState } from "react";
import { FaUser, FaBuilding, FaPaperPlane, FaSpinner } from "react-icons/fa6";

interface AccessRequestFormProps {
  name: string;          // From Telegram
  username: string | null; // From Telegram
  onSubmit: (office: string) => Promise<void>;
  onSuccess: () => void;
}

const AccessRequestForm: React.FC<AccessRequestFormProps> = ({
  name,
  username,
  onSubmit,
  onSuccess,
}) => {
  const [office, setOffice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!office.trim()) {
      setError("Пожалуйста, укажите офис");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onSubmit(office);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось отправить запрос");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6">
          <h2 className="text-2xl font-bold text-white mb-2">Запрос доступа</h2>
          <p className="text-gray-300 text-sm mb-6">
            Заполните форму для получения доступа к системе
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name (readonly) */}
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                <FaUser className="inline mr-2" />
                Имя
              </label>
              <input
                type="text"
                value={name}
                readOnly
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#A020F0]/50"
              />
            </div>

            {/* Username (readonly, optional) */}
            {username && (
              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  Telegram Username
                </label>
                <input
                  type="text"
                  value={`@${username}`}
                  readOnly
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-gray-400 focus:outline-none"
                />
              </div>
            )}

            {/* Office (input) */}
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                <FaBuilding className="inline mr-2" />
                Офис <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={office}
                onChange={(e) => setOffice(e.target.value)}
                placeholder="Например: Офис A, Москва"
                required
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#A020F0]/50"
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
                <p className="text-red-200 text-sm">{error}</p>
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full px-6 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <FaSpinner className="animate-spin" />
                  Отправка...
                </>
              ) : (
                <>
                  <FaPaperPlane />
                  Отправить запрос
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AccessRequestForm;
```

### 2. Обновить authenticateWithTelegram для поддержки office

**Файл:** `frontend_mini_app/src/lib/api/client.ts` (строки 119-134)

**Изменить:**
```typescript
export async function authenticateWithTelegram(
  initData: string,
  office?: string  // Add office parameter
): Promise<{ access_token: string; user: User }> {
  const response = await apiRequest<{ access_token: string; user: User }>(
    "/auth/telegram",
    {
      method: "POST",
      body: JSON.stringify({
        init_data: initData,
        ...(office && { office })  // Include office if provided
      }),
    }
  );

  // Save token
  setToken(response.access_token);

  return response;
}
```

### 3. Обновить логику авторизации в page.tsx

**Файл:** `frontend_mini_app/src/app/page.tsx` (строки 38-113)

**Добавить состояния:**
```typescript
const [authState, setAuthState] = useState<
  "loading" | "success" | "needs_request" | "pending" | "rejected" | "error"
>("loading");
const [telegramUserData, setTelegramUserData] = useState<{
  name: string;
  username: string | null;
} | null>(null);
```

**Изменить логику авторизации:**
```typescript
useEffect(() => {
  const inTelegram = isTelegramWebApp();
  setIsInTelegram(inTelegram);

  if (!inTelegram) {
    return;
  }

  // Initialize Telegram WebApp
  initTelegramWebApp();

  // Authenticate with backend
  const initData = getTelegramInitData();
  if (!initData) {
    setAuthError("Telegram initData недоступен");
    setAuthState("error");
    return;
  }

  // Try initial auth without office (for existing users)
  authenticateWithTelegram(initData)
    .then((response) => {
      setIsAuthenticated(true);
      setUser(response.user);
      setAuthState("success");
      localStorage.setItem("user", JSON.stringify(response.user));
    })
    .catch(err => {
      console.error("Telegram auth failed:", err);
      const errorMessage = err instanceof Error
        ? err.message
        : typeof err === 'string'
          ? err
          : (err?.detail || err?.message || "Не удалось авторизоваться");

      // Parse Telegram user data for form
      const tgWebApp = window.Telegram?.WebApp;
      if (tgWebApp?.initDataUnsafe?.user) {
        const tgUser = tgWebApp.initDataUnsafe.user;
        setTelegramUserData({
          name: `${tgUser.first_name} ${tgUser.last_name || ""}`.trim(),
          username: tgUser.username || null,
        });
      }

      // Determine auth state based on error message
      if (errorMessage.includes("Access request created")) {
        setAuthState("pending");
      } else if (errorMessage.includes("Access request pending")) {
        setAuthState("pending");
      } else if (errorMessage.includes("Access request rejected")) {
        setAuthState("rejected");
      } else {
        setAuthError(errorMessage);
        setAuthState("error");
      }
    });
}, [router]);
```

**Добавить handler для отправки запроса:**
```typescript
const handleAccessRequestSubmit = async (office: string) => {
  const initData = getTelegramInitData();
  if (!initData) {
    throw new Error("Telegram initData недоступен");
  }

  await authenticateWithTelegram(initData, office);
};

const handleAccessRequestSuccess = () => {
  setAuthState("pending");
};
```

**Изменить рендеринг:**
```typescript
// Show loading while checking Telegram environment
if (isInTelegram === null || authState === "loading") {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
      <div className="text-center">
        <FaSpinner className="text-white text-4xl animate-spin mx-auto mb-4" />
        <p className="text-white">Авторизация...</p>
      </div>
    </div>
  );
}

// Show fallback UI if not in Telegram
if (!isInTelegram) {
  return <TelegramFallback />;
}

// Show access request form for new users
if (authState === "needs_request" && telegramUserData) {
  return (
    <AccessRequestForm
      name={telegramUserData.name}
      username={telegramUserData.username}
      onSubmit={handleAccessRequestSubmit}
      onSuccess={handleAccessRequestSuccess}
    />
  );
}

// Show pending message
if (authState === "pending") {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 max-w-md">
        <FaSpinner className="text-[#A020F0] text-4xl mx-auto mb-4" />
        <h2 className="text-white text-xl font-bold mb-2">Ожидание одобрения</h2>
        <p className="text-gray-300">
          Ваш запрос на доступ отправлен. Пожалуйста, ожидайте одобрения менеджера.
        </p>
      </div>
    </div>
  );
}

// Show rejected message
if (authState === "rejected") {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
      <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6 max-w-md">
        <FaTriangleExclamation className="text-red-400 text-4xl mx-auto mb-4" />
        <h2 className="text-white text-xl font-bold mb-2">Доступ отклонён</h2>
        <p className="text-red-200">
          Ваш запрос на доступ был отклонён. Пожалуйста, обратитесь к менеджеру.
        </p>
      </div>
    </div>
  );
}

// Show error
if (authState === "error" && authError) {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
      <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6 max-w-md">
        <FaTriangleExclamation className="text-red-400 text-4xl mx-auto mb-4" />
        <h2 className="text-white text-xl font-bold mb-2">Ошибка авторизации</h2>
        <p className="text-red-200">{authError}</p>
      </div>
    </div>
  );
}

// Normal app UI (authenticated)
return (
  <div className="relative w-full min-h-screen bg-[#130F30] overflow-x-hidden">
    {/* ... existing app UI ... */}
  </div>
);
```

### 4. Проверить backend schema (если нужно)

**Файл:** `backend/src/auth/schemas.py`

Убедиться что поле `office` присутствует:

```python
class TelegramAuthRequest(BaseModel):
    init_data: str
    office: str | None = None  # Если нет, добавить
```

**Если поля нет, добавить.**

## Затронутые файлы

| Файл | Действие |
|------|----------|
| `frontend_mini_app/src/components/AccessRequestForm/AccessRequestForm.tsx` | Создать: новый компонент формы запроса доступа |
| `frontend_mini_app/src/app/page.tsx` | Обновить: добавить логику обработки auth states и рендеринг формы |
| `frontend_mini_app/src/lib/api/client.ts` | Обновить: `authenticateWithTelegram()` поддержка параметра `office` |
| `backend/src/auth/schemas.py` | Проверить/добавить: поле `office` в `TelegramAuthRequest` (если отсутствует) |

## Тесты

**Manual Testing:**

1. **Новый пользователь (без запроса):**
   - Открыть Mini App с новым Telegram аккаунтом
   - Должна показаться форма запроса доступа
   - Заполнить офис, нажать "Отправить запрос"
   - Должно показаться сообщение "Ожидание одобрения"

2. **Пользователь с pending запросом:**
   - Открыть Mini App с аккаунтом, у которого pending запрос
   - Должно показаться сообщение "Ожидание одобрения" без формы

3. **Пользователь с rejected запросом:**
   - Открыть Mini App с аккаунтом, у которого rejected запрос
   - Должно показаться сообщение "Доступ отклонён"

4. **Одобренный пользователь:**
   - Открыть Mini App с одобренным аккаунтом
   - Должна загрузиться обычная страница приложения

**Unit Tests (опционально):**

Можно добавить тесты для компонента `AccessRequestForm`:
- Валидация поля office
- Обработка ошибок submit
- Состояние loading

## Приоритет

**High** — критичная функциональность для UX новых пользователей.

## Оценка сложности

**Medium:**
- Новый компонент формы
- Обновление логики auth в page.tsx
- Обновление API client
- Проверка backend schema (возможно не требуется)

**Ориентировочное время:** 2-3 часа (включая тестирование и стилизацию).

## Примечания

**Backend уже готов:**
- TSK-016 реализовала систему user access requests
- API endpoint `POST /auth/telegram` уже создаёт запросы
- Менеджерская панель уже имеет UI для одобрения запросов

**Эта задача фокусируется только на frontend UX для обычных пользователей.**

## Связанные задачи

- **TSK-016:** Implement user access request approval system (completed) — backend реализация
