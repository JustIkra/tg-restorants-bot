---
agent: reviewer
task_id: TSK-005
status: completed
verdict: CHANGES_REQUESTED
next: coder
created_at: 2025-12-06T16:30:00
---

# Code Review: TSK-005 - Интеграция фронтенда как Telegram Mini App

## Общая оценка

Код в целом хорошего качества, следует принятым конвенциям проекта, но есть **критические проблемы**, которые требуют исправления перед переходом к тестированию.

**Статус:** CHANGES_REQUESTED

**Основные проблемы:**
1. ❌ **CRITICAL**: Некорректная инициализация Telegram WebApp в page.tsx
2. ❌ **CRITICAL**: Отсутствует обработка аутентификации после получения initData
3. ⚠️ **IMPORTANT**: docker-compose.yml переопределяет CORS_ORIGINS некорректным значением
4. ⚠️ **IMPORTANT**: Отсутствует обработка ошибок в setup_menu_button
5. ⚠️ **SUGGESTION**: Жестко закодирован API_BASE_URL в handlers.py

---

## Backend Review

### 1. backend/.env.example ✅

**Статус:** APPROVED

**Положительные стороны:**
- ✅ Корректно добавлен `TELEGRAM_MINI_APP_URL` с production доменом
- ✅ Хорошие комментарии с примерами для разных окружений
- ✅ CORS_ORIGINS содержит все необходимые домены:
  - `http://localhost` - development
  - `https://lunchbot.vibe-labs.ru` - production
  - `https://web.telegram.org` - Telegram WebApp iframe
- ✅ Формат JSON массива корректен (двойные кавычки)

**Замечания:** Нет

---

### 2. backend/src/config.py ✅

**Статус:** APPROVED

**Положительные стороны:**
- ✅ Type hints соответствуют Python 3.13+ (используется `list[str]` вместо `List[str]`)
- ✅ Fallback значение для `TELEGRAM_MINI_APP_URL` корректно
- ✅ `CORS_ORIGINS` имеет разумный fallback
- ✅ Pydantic Settings корректно настроен

**Замечания:** Нет

---

### 3. backend/src/main.py ✅

**Статус:** APPROVED

**Положительные стороны:**
- ✅ CORS middleware корректно использует `settings.CORS_ORIGINS`
- ✅ Все необходимые опции CORS настроены:
  - `allow_credentials=True` - для cookies/auth
  - `allow_methods=["*"]` - все HTTP методы
  - `allow_headers=["*"]` - все headers
- ✅ Code style соответствует проекту

**Замечания:** Нет

---

### 4. backend/src/telegram/handlers.py ⚠️

**Статус:** CHANGES_REQUESTED

**Положительные стороны:**
- ✅ Все команды корректно реализованы (`/start`, `/order`, `/help`)
- ✅ Используется `settings.TELEGRAM_MINI_APP_URL` для WebAppInfo
- ✅ Inline keyboard правильно сформирован
- ✅ Docstrings в Google style для всех функций
- ✅ Error handling в `/link` команде подробный и информативный
- ✅ Логирование критичных событий присутствует

**Критические замечания:**

#### IMPORTANT: Hardcoded API_BASE_URL (строка 17)

```python
API_BASE_URL = "http://localhost:8000/api/v1"
```

**Проблема:**
- Жестко закодирован localhost URL
- Не будет работать в Docker контейнере (нужен hostname `backend`)
- Не гибко для разных окружений

**Решение:**
```python
# backend/src/telegram/handlers.py
from ..config import settings

# Вместо hardcoded URL
API_BASE_URL = settings.API_BASE_URL  # или settings.BACKEND_URL

# Добавить в config.py:
# API_BASE_URL: str = "http://backend:8000/api/v1"
```

**Альтернатива:**
Если URL используется только для internal communication в `/link` команде, можно вычислять динамически:
```python
API_BASE_URL = "http://backend:8000/api/v1"  # Docker hostname
```

**Приоритет:** IMPORTANT (не критично для Mini App интеграции, но критично для `/link` команды)

---

**Рекомендации:**

#### SUGGESTION: Обработка ошибок сети (строки 89-152)

Хорошая обработка ошибок в `/link`, но можно улучшить:

```python
# Добавить обработку конкретных HTTP статусов
elif response.status_code == 409:
    # Conflict - already linked
    await message.answer(
        "❌ Это кафе уже привязано к другому чату.\n\n"
        "Обратитесь к администратору для переноса."
    )
```

**Приоритет:** LOW

---

### 5. backend/src/telegram/bot.py ⚠️

**Статус:** CHANGES_REQUESTED

**Положительные стороны:**
- ✅ Функция `setup_menu_button()` корректно реализована
- ✅ Используется `settings.TELEGRAM_MINI_APP_URL`
- ✅ `MenuButtonWebApp` создан правильно
- ✅ Логирование успешной настройки
- ✅ Try-except для обработки ошибок
- ✅ Вызов в правильном месте (до `start_polling`)

**Критические замечания:**

#### IMPORTANT: Недостаточная обработка ошибок (строки 19-27)

```python
async def setup_menu_button():
    """Configure Menu Button for Mini App launch."""
    try:
        webapp = WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL)
        menu_button = MenuButtonWebApp(text="Заказать обед", web_app=webapp)
        await bot.set_chat_menu_button(menu_button=menu_button)
        logger.info(f"Menu button configured with URL: {settings.TELEGRAM_MINI_APP_URL}")
    except Exception as e:
        logger.error(f"Failed to setup menu button: {e}")
```

**Проблемы:**

1. **Слишком общий except:**
   - Ловит все исключения, включая `KeyboardInterrupt`, `SystemExit`
   - Не различает типы ошибок (сеть, конфигурация, invalid token)

2. **Не эскалирует критические ошибки:**
   - Если `TELEGRAM_BOT_TOKEN` невалиден - бот продолжает работу
   - Пользователь не увидит Menu Button, но не будет понятно почему

3. **F-string в logger:**
   - Используется f-string вместо lazy formatting
   - Строка форматируется даже если логирование отключено

**Решение:**

```python
from aiogram.exceptions import TelegramAPIError

async def setup_menu_button():
    """Configure Menu Button for Mini App launch."""
    try:
        webapp = WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL)
        menu_button = MenuButtonWebApp(text="Заказать обед", web_app=webapp)
        await bot.set_chat_menu_button(menu_button=menu_button)
        logger.info(
            "Menu button configured with URL: %s",
            settings.TELEGRAM_MINI_APP_URL
        )
    except TelegramAPIError as e:
        logger.error(
            "Failed to setup menu button (Telegram API error): %s",
            e,
            exc_info=True
        )
        # Не падаем - бот может работать без Menu Button (есть /order команда)
    except Exception as e:
        logger.error(
            "Unexpected error during menu button setup: %s",
            e,
            exc_info=True
        )
        # Critical error - пробрасываем дальше
        raise
```

**Приоритет:** IMPORTANT

---

## Frontend Review

### 6. frontend_mini_app/src/app/page.tsx ❌

**Статус:** CHANGES_REQUESTED

**Положительные стороны:**
- ✅ Three-state pattern для `isInTelegram` (null → true/false)
- ✅ Loading spinner при проверке окружения
- ✅ Fallback UI для не-Telegram окружения
- ✅ SSR safety через проверку `typeof window`
- ✅ Корректные TypeScript типы
- ✅ Tailwind CSS классы соответствуют дизайн-системе проекта
- ✅ Сохранена вся существующая логика

**Критические замечания:**

#### CRITICAL: Некорректная инициализация Telegram WebApp (строки 58-76)

```tsx
useEffect(() => {
  const inTelegram = isTelegramWebApp();
  setIsInTelegram(inTelegram);

  if (inTelegram) {
    // Initialize Telegram WebApp
    initTelegramWebApp();

    // Get Telegram init data for authentication
    const initData = getTelegramInitData();
    if (initData) {
      // Note: Authentication would be handled by the API client
      // The initData is automatically included in API requests via the client
      console.log("Telegram WebApp initialized with initData");
    } else {
      console.warn("Telegram WebApp initialized but no initData available");
    }
  }
}, []);
```

**Проблемы:**

1. **Отсутствует обработка аутентификации:**
   - Комментарий говорит "Authentication would be handled by the API client"
   - НО API client **НЕ делает это автоматически**
   - `initData` получается, но **нигде не используется**
   - Нет вызова `/auth/telegram` endpoint

2. **API запросы будут фейлиться:**
   - Все API endpoints требуют JWT токен (кроме `/auth/telegram`)
   - Без аутентификации запросы будут возвращать 401 Unauthorized
   - Это сломает весь флоу приложения

3. **Несоответствие архитектуре:**
   - В task.md и архитектурном плане явно указано:
     ```
     useEffect(() => {
       initTelegramWebApp();
       const initData = getTelegramInitData();
       if (initData) {
         authenticateWithTelegram(initData)
           .then(() => setIsAuthenticated(true))
           .catch(err => console.error("Auth failed:", err));
       }
     }, []);
     ```

**Решение:**

```tsx
import { authenticateWithTelegram } from "@/lib/api/client";

export default function Home() {
  const [isInTelegram, setIsInTelegram] = useState<boolean | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    const inTelegram = isTelegramWebApp();
    setIsInTelegram(inTelegram);

    if (inTelegram) {
      // Initialize Telegram WebApp
      initTelegramWebApp();

      // Authenticate with backend
      const initData = getTelegramInitData();
      if (initData) {
        authenticateWithTelegram(initData)
          .then(() => {
            setIsAuthenticated(true);
            console.log("Authenticated successfully");
          })
          .catch(err => {
            console.error("Authentication failed:", err);
            setAuthError(err.message || "Не удалось авторизоваться");
          });
      } else {
        setAuthError("Telegram initData недоступен");
      }
    }
  }, []);

  // Show loading while authenticating
  if (isInTelegram && !isAuthenticated && !authError) {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="text-white text-4xl animate-spin mx-auto mb-4" />
          <p className="text-white">Авторизация...</p>
        </div>
      </div>
    );
  }

  // Show error if auth failed
  if (isInTelegram && authError) {
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

  // ... rest of the component (existing code)
}
```

**Приоритет:** CRITICAL - без этого приложение не будет работать

---

#### IMPORTANT: Проверить наличие функции `authenticateWithTelegram`

Необходимо убедиться, что функция `authenticateWithTelegram` существует в `src/lib/api/client.ts`:

```typescript
// src/lib/api/client.ts
export async function authenticateWithTelegram(initData: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/telegram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: initData }),
  });

  if (!response.ok) {
    throw new Error('Authentication failed');
  }

  const data = await response.json();
  const token = data.access_token;

  // Store token for subsequent requests
  localStorage.setItem('jwt_token', token);
}
```

**Если функция отсутствует - это критическая проблема.**

---

**Рекомендации:**

#### SUGGESTION: Улучшить UX при загрузке (строки 215-221)

Текущий loading state показывает просто спиннер:

```tsx
if (isInTelegram === null) {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
      <FaSpinner className="text-white text-4xl animate-spin" />
    </div>
  );
}
```

**Рекомендация:** Добавить текст и фоновые эффекты для консистентности:

```tsx
if (isInTelegram === null) {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
      {/* Background blur effects */}
      <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
      <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

      <div className="relative text-center">
        <FaSpinner className="text-white text-4xl animate-spin mx-auto mb-4" />
        <p className="text-white">Загрузка приложения...</p>
      </div>
    </div>
  );
}
```

**Приоритет:** LOW

---

### 7. frontend_mini_app/src/components/TelegramFallback/TelegramFallback.tsx ✅

**Статус:** APPROVED

**Положительные стороны:**
- ✅ Корректная структура компонента
- ✅ Хорошая типизация (Props interface отсутствует, т.к. нет props)
- ✅ Tailwind CSS соответствует дизайн-системе
- ✅ Фоновые blur эффекты как в основном UI
- ✅ Четкие инструкции для пользователя
- ✅ Адаптивный дизайн (`max-w-md`, `p-4`)
- ✅ Использует корректную иконку Telegram от `react-icons/fa6`
- ✅ HTML entities (`&quot;`) экранированы корректно

**Замечания:** Нет

---

### 8. frontend_mini_app/.env.example ✅

**Статус:** APPROVED

**Положительные стороны:**
- ✅ Подробные комментарии для каждого окружения
- ✅ Production URL корректен (`https://lunchbot.vibe-labs.ru/api/v1`)
- ✅ Явно указана необходимость ngrok для Telegram Mini App testing
- ✅ Все варианты URL задокументированы

**Замечания:** Нет

---

## Infrastructure Review

### 9. docker-compose.yml ⚠️

**Статус:** CHANGES_REQUESTED

**Критические замечания:**

#### IMPORTANT: CORS_ORIGINS переопределен некорректным значением (строка 99)

```yaml
backend:
  env_file: ./backend/.env
  environment:
    CORS_ORIGINS: '["http://localhost"]'  # ❌ ПРОБЛЕМА
```

**Проблема:**
- В `.env.example` корректно указано:
  ```bash
  CORS_ORIGINS=["http://localhost","https://lunchbot.vibe-labs.ru","https://web.telegram.org"]
  ```
- Но `docker-compose.yml` **переопределяет** это значение на только `["http://localhost"]`
- **Результат:** Telegram Mini App (который загружается с `https://web.telegram.org`) будет получать CORS ошибки

**Решение 1 (рекомендуется):** Убрать переопределение

```yaml
backend:
  env_file: ./backend/.env
  environment:
    DATABASE_URL: postgresql+asyncpg://postgres:password@postgres:5432/lunch_bot
    KAFKA_BROKER_URL: kafka:29092
    REDIS_URL: redis://redis:6379
    JWT_ALGORITHM: HS256
    JWT_EXPIRE_DAYS: 7
    # CORS_ORIGINS - удалить, чтобы использовалось значение из .env
```

**Решение 2 (альтернатива):** Сделать динамическим через .env переменную

```yaml
backend:
  environment:
    CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost"]}
```

Тогда в корневом `.env`:
```bash
CORS_ORIGINS=["http://localhost","https://lunchbot.vibe-labs.ru","https://web.telegram.org"]
```

**Приоритет:** IMPORTANT - критично для работы Telegram Mini App

---

#### SUGGESTION: Frontend API URL можно сделать гибче

```yaml
frontend:
  build:
    args:
      NEXT_PUBLIC_API_URL: http://localhost/api/v1  # Build-time
  environment:
    NEXT_PUBLIC_API_URL: http://localhost/api/v1   # Runtime
```

**Рекомендация:** Использовать env variable для гибкости

```yaml
frontend:
  build:
    args:
      NEXT_PUBLIC_API_URL: ${FRONTEND_API_URL:-http://localhost/api/v1}
  environment:
    NEXT_PUBLIC_API_URL: ${FRONTEND_API_URL:-http://localhost/api/v1}
```

Тогда для ngrok testing:
```bash
# В корневом .env
FRONTEND_API_URL=https://xxx.ngrok.io/api/v1
```

**Приоритет:** LOW

---

## Security Review

### CORS Configuration ✅

**Статус:** SECURE (после исправления docker-compose.yml)

**Анализ:**
- ✅ `allow_credentials=True` - корректно для JWT auth
- ✅ `allow_methods=["*"]` - приемлемо для internal API
- ✅ `allow_headers=["*"]` - приемлемо для internal API
- ✅ `allow_origins` ограничен списком доменов (не `*`)
- ✅ Домены корректны:
  - `http://localhost` - dev only
  - `https://lunchbot.vibe-labs.ru` - production frontend
  - `https://web.telegram.org` - Telegram WebApp iframe

**Рекомендации:**
- ⚠️ В production убрать `http://localhost` из CORS_ORIGINS
- ⚠️ Рассмотреть ограничение `allow_methods` до `["GET", "POST", "PUT", "DELETE"]`

---

### Telegram Bot Token ✅

**Статус:** SECURE

**Анализ:**
- ✅ Token хранится в environment variable
- ✅ Не commit в git (в `.env.example` placeholder)
- ✅ Загружается через `pydantic-settings`

---

### JWT Configuration ⚠️

**Статус:** SECURE (с замечанием)

**Анализ:**
- ✅ Validator требует минимум 32 символа для `JWT_SECRET_KEY`
- ✅ Algorithm можно настроить (по умолчанию HS256)
- ⚠️ Expire days можно настроить (по умолчанию 7 дней)

**Рекомендация:**
- Для production рассмотреть `JWT_EXPIRE_DAYS=1` для большей безопасности

---

## Code Style Compliance

### Python Code Style ✅

**Проверка соответствия `.memory-base/tech-docs/rules/code-style.md`:**

- ✅ Line length: все файлы в пределах 100 символов
- ✅ Quotes: используются двойные кавычки (`"`)
- ✅ Imports: корректная сортировка (stdlib → third-party → local)
- ✅ Naming:
  - `snake_case` для функций: `setup_menu_button`, `cmd_start`
  - `UPPER_CASE` для констант: `API_BASE_URL`
- ✅ Type hints:
  - Python 3.13+ синтаксис: `list[str]` вместо `List[str]`
  - Pydantic models: корректные type hints
  - Async functions: корректные return types
- ✅ Docstrings: Google style для всех public функций

**Замечания:** Нет нарушений

---

### TypeScript/React Code Style ✅

**Проверка соответствия code-style.md:**

- ✅ Functional components с TypeScript
- ✅ `"use client"` директива для client components
- ✅ Tailwind CSS utility classes:
  - Цвета: `bg-[#130F30]`, `text-white`, `text-gray-300`
  - Backdrop blur: `backdrop-blur-md`
  - Gradients: `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- ✅ TypeScript типы:
  - State типизирован: `useState<boolean | null>(null)`
  - Props типизированы через interfaces (где нужно)
- ✅ Импорты правильно организованы:
  - React hooks
  - Third-party (react-icons)
  - Local components (`@/components/...`)
  - Local utilities (`@/lib/...`)

**Замечания:** Нет нарушений

---

## Performance Review

### Backend Performance ✅

**Анализ:**
- ✅ Async/await используется корректно
- ✅ Database queries через AsyncSession
- ✅ CORS middleware - минимальный overhead
- ✅ Health check endpoint простой и быстрый

---

### Frontend Performance ⚠️

**Анализ:**
- ✅ SWR hooks для кэширования API запросов
- ✅ `useMemo` для вычисляемых значений (categories, dishes, filtered dishes)
- ✅ Lazy loading компонентов не требуется (приложение маленькое)
- ⚠️ `useEffect` без cleanup функции - OK для данного случая

**Рекомендация:**
- Loading states могут быть улучшены с помощью skeleton loaders вместо спиннеров

**Приоритет:** LOW

---

## Testing Recommendations

### Backend Tests

**Что нужно протестировать:**

1. **Menu Button Setup:**
   ```python
   @pytest.mark.asyncio
   async def test_setup_menu_button_success():
       """Test successful menu button configuration."""
       await setup_menu_button()
       # Assert bot.set_chat_menu_button was called with correct parameters

   @pytest.mark.asyncio
   async def test_setup_menu_button_api_error():
       """Test menu button setup with Telegram API error."""
       # Mock bot.set_chat_menu_button to raise TelegramAPIError
       # Assert error is logged but not raised
   ```

2. **Handlers:**
   ```python
   @pytest.mark.asyncio
   async def test_cmd_start():
       """Test /start command sends correct message and keyboard."""
       # Assert message contains welcome text
       # Assert keyboard has web_app button with correct URL

   @pytest.mark.asyncio
   async def test_cmd_order():
       """Test /order command sends web_app button."""
       # Similar to test_cmd_start
   ```

3. **CORS:**
   ```python
   async def test_cors_origins():
       """Test CORS middleware allows correct origins."""
       # Test request from http://localhost - should succeed
       # Test request from https://web.telegram.org - should succeed
       # Test request from unknown origin - should fail
   ```

---

### Frontend Tests

**Что нужно протестировать:**

1. **Telegram Environment Check:**
   ```typescript
   describe('Page - Telegram Environment', () => {
     it('shows loading spinner while checking Telegram', () => {
       // Assert spinner is visible initially
     });

     it('shows fallback UI when not in Telegram', () => {
       // Mock isTelegramWebApp to return false
       // Assert TelegramFallback component is rendered
     });

     it('initializes Telegram WebApp when in Telegram', () => {
       // Mock isTelegramWebApp to return true
       // Assert initTelegramWebApp was called
     });
   });
   ```

2. **Authentication Flow:**
   ```typescript
   describe('Page - Authentication', () => {
     it('authenticates with backend when in Telegram', () => {
       // Mock getTelegramInitData to return valid data
       // Mock authenticateWithTelegram to succeed
       // Assert main UI is rendered
     });

     it('shows error when authentication fails', () => {
       // Mock authenticateWithTelegram to throw error
       // Assert error message is displayed
     });
   });
   ```

---

## Summary of Issues

### Critical Issues (Must Fix)

| # | File | Issue | Priority |
|---|------|-------|----------|
| 1 | `frontend_mini_app/src/app/page.tsx` | Отсутствует обработка аутентификации с backend | CRITICAL |
| 2 | `frontend_mini_app/src/app/page.tsx` | Необходимо добавить вызов `authenticateWithTelegram()` | CRITICAL |

### Important Issues (Should Fix)

| # | File | Issue | Priority |
|---|------|-------|----------|
| 3 | `docker-compose.yml` | CORS_ORIGINS переопределен некорректным значением | IMPORTANT |
| 4 | `backend/src/telegram/bot.py` | Недостаточная обработка ошибок в `setup_menu_button` | IMPORTANT |
| 5 | `backend/src/telegram/handlers.py` | Hardcoded `API_BASE_URL` вместо использования config | IMPORTANT |

### Suggestions (Nice to Have)

| # | File | Issue | Priority |
|---|------|-------|----------|
| 6 | `frontend_mini_app/src/app/page.tsx` | Улучшить UX loading state | LOW |
| 7 | `docker-compose.yml` | Сделать FRONTEND_API_URL динамическим | LOW |
| 8 | `backend/src/telegram/handlers.py` | Добавить обработку 409 status в `/link` | LOW |

---

## Detailed Changes Required

### 1. Fix Authentication in page.tsx (CRITICAL)

**File:** `frontend_mini_app/src/app/page.tsx`

**Changes:**

1. Добавить импорт:
   ```tsx
   import { authenticateWithTelegram } from "@/lib/api/client";
   ```

2. Добавить state:
   ```tsx
   const [isAuthenticated, setIsAuthenticated] = useState(false);
   const [authError, setAuthError] = useState<string | null>(null);
   ```

3. Обновить useEffect (строки 58-76):
   ```tsx
   useEffect(() => {
     const inTelegram = isTelegramWebApp();
     setIsInTelegram(inTelegram);

     if (inTelegram) {
       initTelegramWebApp();

       const initData = getTelegramInitData();
       if (initData) {
         authenticateWithTelegram(initData)
           .then(() => {
             setIsAuthenticated(true);
             console.log("Authenticated successfully");
           })
           .catch(err => {
             console.error("Authentication failed:", err);
             setAuthError(err.message || "Не удалось авторизоваться");
           });
       } else {
         setAuthError("Telegram initData недоступен");
       }
     }
   }, []);
   ```

4. Добавить loading state для аутентификации (после строки 221):
   ```tsx
   if (isInTelegram && !isAuthenticated && !authError) {
     return (
       <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
         <div className="text-center">
           <FaSpinner className="text-white text-4xl animate-spin mx-auto mb-4" />
           <p className="text-white">Авторизация...</p>
         </div>
       </div>
     );
   }
   ```

5. Добавить error state для аутентификации (после предыдущего блока):
   ```tsx
   if (isInTelegram && authError) {
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
   ```

6. **Проверить наличие функции `authenticateWithTelegram` в `src/lib/api/client.ts`**
   - Если отсутствует - реализовать по спецификации выше

---

### 2. Fix CORS in docker-compose.yml (IMPORTANT)

**File:** `docker-compose.yml`

**Change (строка 99):**

```yaml
# BEFORE:
environment:
  CORS_ORIGINS: '["http://localhost"]'

# AFTER:
environment:
  # CORS_ORIGINS - removed, use value from .env file
```

Или использовать переменную окружения:

```yaml
environment:
  CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost","https://lunchbot.vibe-labs.ru","https://web.telegram.org"]}
```

---

### 3. Improve Error Handling in bot.py (IMPORTANT)

**File:** `backend/src/telegram/bot.py`

**Change (строки 19-27):**

```python
# BEFORE:
except Exception as e:
    logger.error(f"Failed to setup menu button: {e}")

# AFTER:
from aiogram.exceptions import TelegramAPIError

except TelegramAPIError as e:
    logger.error(
        "Failed to setup menu button (Telegram API error): %s",
        e,
        exc_info=True
    )
    # Don't re-raise - bot can work without Menu Button
except Exception as e:
    logger.error(
        "Unexpected error during menu button setup: %s",
        e,
        exc_info=True
    )
    raise  # Critical error - propagate
```

---

### 4. Fix API_BASE_URL in handlers.py (IMPORTANT)

**File:** `backend/src/telegram/handlers.py`

**Option 1 - Add to config:**

```python
# backend/src/config.py
class Settings(BaseSettings):
    # ...
    BACKEND_API_URL: str = "http://backend:8000/api/v1"

# backend/src/telegram/handlers.py
from ..config import settings

API_BASE_URL = settings.BACKEND_API_URL
```

**Option 2 - Use Docker hostname:**

```python
# backend/src/telegram/handlers.py
# Use Docker service name for inter-container communication
API_BASE_URL = "http://backend:8000/api/v1"
```

---

## Verdict

**Status:** CHANGES_REQUESTED

**Причины:**
1. ❌ **CRITICAL**: Отсутствует аутентификация в page.tsx - приложение не будет работать
2. ⚠️ **IMPORTANT**: CORS_ORIGINS переопределен в docker-compose.yml - Telegram Mini App получит CORS ошибки
3. ⚠️ **IMPORTANT**: Недостаточная обработка ошибок в setup_menu_button
4. ⚠️ **IMPORTANT**: Hardcoded API_BASE_URL в handlers.py

**Next Steps:**
1. Coder должен исправить все CRITICAL и IMPORTANT issues
2. После исправлений - повторный review
3. Только после успешного review - переход к Tester

**Общее качество кода:** Хорошее, но требует критических исправлений для работоспособности.

---

## Files Changed Summary

| File | Status | Changes Required |
|------|--------|------------------|
| `backend/.env.example` | ✅ APPROVED | None |
| `backend/src/config.py` | ✅ APPROVED | None |
| `backend/src/main.py` | ✅ APPROVED | None |
| `backend/src/telegram/handlers.py` | ⚠️ CHANGES_REQUESTED | Fix API_BASE_URL |
| `backend/src/telegram/bot.py` | ⚠️ CHANGES_REQUESTED | Improve error handling |
| `frontend_mini_app/src/app/page.tsx` | ❌ CHANGES_REQUESTED | Add authentication flow |
| `frontend_mini_app/src/components/TelegramFallback/TelegramFallback.tsx` | ✅ APPROVED | None |
| `frontend_mini_app/.env.example` | ✅ APPROVED | None |
| `docker-compose.yml` | ⚠️ CHANGES_REQUESTED | Fix CORS_ORIGINS |

---

## Acknowledgments

**Что сделано хорошо:**
- ✅ Архитектурный план от Architect был подробным и качественным
- ✅ Code style соответствует проекту на 100%
- ✅ TypeScript типизация на высоком уровне
- ✅ Tailwind CSS используется правильно
- ✅ Error handling в большинстве случаев хороший
- ✅ Docstrings для всех Python функций
- ✅ Безопасность (CORS, JWT, tokens) продумана

**Основная проблема:**
- Упущен критически важный шаг - аутентификация в frontend
- Это приведет к полной неработоспособности приложения

**Рекомендации для Coder:**
1. Внимательно следовать архитектурному плану (там была указана аутентификация)
2. Тестировать изменения перед отправкой на review
3. Проверять dependency между компонентами (page.tsx зависит от API client)
