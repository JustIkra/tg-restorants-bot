---
id: TSK-014
title: Fix React Hydration Mismatch errors and 404 cafe-requests
pipeline: bugfix
status: pending
created_at: 2025-12-07T00:41:04+0300
related_files:
  # Frontend - hydration mismatch
  - frontend_mini_app/src/app/FortuneWheel/page.tsx
  - frontend_mini_app/src/app/manager/page.tsx

  # Backend - missing route
  - backend/src/main.py
  - backend/src/routers/cafe_links.py

  # API hooks
  - frontend_mini_app/src/lib/api/hooks.ts

impact:
  api: да (исправление маршрутизации)
  db: нет
  frontend: да (исправление hydration)
  services: нет
---

## Описание

Исправить три критических проблемы в production:

1. **React Hydration Mismatch в FortuneWheel** (`/FortuneWheel`)
   - **Проблема:** Сервер рендерит `disabled={null}` и текст "Крутить колесо", клиент рендерит `disabled={true}` и "Доступно через: 23:59:17"
   - **Причина:** Время до следующего спина вычисляется на клиенте из localStorage
   - **Последствия:** React hydration warnings, UX скачки при загрузке

2. **React Hydration Mismatch в ManagerPage** (`/manager`)
   - **Проблема:** Сервер рендерит loading spinner (svg), клиент рендерит div с контентом
   - **Причина:** Состояние аутентификации доступно только на клиенте
   - **Последствия:** React hydration warnings, UX скачки при загрузке

3. **404 Error: Missing cafe-requests endpoint**
   - **Проблема:** `GET /api/v1/cafe-requests` возвращает 404
   - **Причина:** Router `cafe_links_router` имеет prefix `/cafes`, эндпоинт `/cafe-requests` становится `/cafes/cafe-requests`
   - **Файл:** `backend/src/routers/cafe_links.py` line 40, `backend/src/main.py` line 45
   - **Последствия:** RequestsList компонент не загружает данные

## Acceptance Criteria

### 1. FortuneWheel Hydration Fix
- [ ] Кнопка "Крутить колесо" рендерится одинаково на сервере и клиенте
- [ ] Нет hydration mismatch warnings в console
- [ ] Таймер показывается корректно после первого рендера на клиенте
- [ ] localStorage доступ перенесен в useEffect
- [ ] SSR рендерит нейтральное состояние (например, disabled=true, текст "Загрузка...")

### 2. ManagerPage Hydration Fix
- [ ] isInTelegram state инициализируется как null на сервере
- [ ] Loading spinner рендерится одинаково на сервере и клиенте
- [ ] Нет hydration mismatch warnings в console
- [ ] После монтирования компонент корректно определяет Telegram environment
- [ ] SSR рендерит loading spinner, CSR заменяет на контент после проверки

### 3. cafe-requests Endpoint Fix
- [ ] `GET /api/v1/cafe-requests` возвращает 200 OK
- [ ] Router prefix исправлен или эндпоинт перенесен
- [ ] RequestsList компонент загружает данные без ошибок
- [ ] Все тесты для cafe-requests endpoints проходят

## Контекст

### Проблема 1: FortuneWheel Hydration

**Текущий код** (`FortuneWheel/page.tsx`, строки 30-53):

```tsx
const [canSpin, setCanSpin] = useState(() => {
  if (typeof window !== 'undefined') {
    const lastSpin = localStorage.getItem("lastSpin");
    if (lastSpin) {
      const nextSpinTime = parseInt(lastSpin) + ONE_DAY;
      const now = Date.now();
      return now >= nextSpinTime;
    }
  }
  return true;  // <-- На сервере всегда true
});

const [timeLeft, setTimeLeft] = useState(() => {
  if (typeof window !== 'undefined') {
    const lastSpin = localStorage.getItem("lastSpin");
    if (lastSpin) {
      const nextSpinTime = parseInt(lastSpin) + ONE_DAY;
      const now = Date.now();
      if (now < nextSpinTime) {
        return nextSpinTime - now;
      }
    }
  }
  return 0;  // <-- На сервере всегда 0
});
```

**Текст кнопки** (строка 252-257):
```tsx
{isSpinning
  ? "Крутим..."
  : canSpin
  ? "Крутить колесо"        // <-- На сервере (canSpin=true)
  : `Доступно через: ${formatTime(timeLeft)}`  // <-- На клиенте (canSpin=false)
}
```

**Решение:**
- Инициализировать `canSpin=false` и `timeLeft=0` в state (нейтральное состояние для SSR)
- Переместить логику проверки localStorage в `useEffect` после монтирования
- SSR рендерит: `disabled={true}`, текст "Загрузка..." или "Крутить колесо"
- После монтирования useEffect обновляет state на основе localStorage

**Пример фикса:**
```tsx
const [canSpin, setCanSpin] = useState(false);  // Нейтральное состояние для SSR
const [timeLeft, setTimeLeft] = useState(0);
const [mounted, setMounted] = useState(false);

useEffect(() => {
  setMounted(true);
  const lastSpin = localStorage.getItem("lastSpin");
  if (lastSpin) {
    const nextSpinTime = parseInt(lastSpin) + ONE_DAY;
    const now = Date.now();
    if (now >= nextSpinTime) {
      setCanSpin(true);
      setTimeLeft(0);
    } else {
      setCanSpin(false);
      setTimeLeft(nextSpinTime - now);
    }
  } else {
    setCanSpin(true);
  }
}, []);

// В JSX:
<button disabled={!canSpin || isSpinning}>
  {isSpinning
    ? "Крутим..."
    : !mounted || canSpin
    ? "Крутить колесо"
    : `Доступно через: ${formatTime(timeLeft)}`}
</button>
```

### Проблема 2: ManagerPage Hydration

**Текущий код** (`manager/page.tsx`, строки 59-64):

```tsx
const [isInTelegram] = useState<boolean | null>(() => {
  if (typeof window !== 'undefined') {
    return isTelegramWebApp();
  }
  return null;  // <-- На сервере null
});
```

**Проверка на null** (строки 165-171):
```tsx
if (isInTelegram === null) {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
      <FaSpinner className="text-white text-4xl animate-spin" />  // <-- Сервер
    </div>
  );
}
```

**Проверка на аутентификацию** (строки 191-200):
```tsx
if (isInTelegram && !isAuthenticated && !authError) {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
      <div className="text-center">
        <FaSpinner className="text-white text-4xl animate-spin mx-auto mb-4" />
        <p className="text-white">Авторизация...</p>  // <-- Клиент после проверки
      </div>
    </div>
  );
}
```

**Решение:**
- `isInTelegram` уже корректно инициализируется как `null` для SSR
- Проблема: после `useEffect` (строка 86) `isInTelegram` остается `null`, но state меняется внутри условия
- Решение: вынести `setIsInTelegram()` в useEffect, убрать useState initializer

**Пример фикса:**
```tsx
const [isInTelegram, setIsInTelegram] = useState<boolean | null>(null);

useEffect(() => {
  const inTelegram = isTelegramWebApp();
  setIsInTelegram(inTelegram);

  if (!inTelegram) return;
  // ... rest of logic
}, []);
```

**АЛЬТЕРНАТИВА:** Использовать `useState(() => null)` без проверки `typeof window`, так как функция-инициализатор и так выполняется только на клиенте. Но это НЕ решит hydration mismatch, если разметка меняется.

### Проблема 3: cafe-requests 404

**Backend маршрутизация:**

`cafe_links.py` (строка 18):
```python
router = APIRouter(prefix="/cafes", tags=["cafe-links"])
```

`cafe_links.py` (строка 40):
```python
@router.get("/cafe-requests", response_model=LinkRequestListSchema)
async def list_cafe_requests(...):
```

`main.py` (строка 45):
```python
app.include_router(cafe_links_router, prefix="/api/v1")
```

**Результат:** endpoint становится `/api/v1/cafes/cafe-requests` вместо `/api/v1/cafe-requests`

**Frontend запрос** (`hooks.ts`, строка 162):
```typescript
export function useCafeRequests(): UseDataResult<CafeRequest> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<CafeRequest>>(
    "/cafe-requests",  // <-- Запрос идет на /api/v1/cafe-requests
    fetcher
  );
```

**Решение Option 1 (рекомендуется):**
Переместить `/cafe-requests` endpoints в отдельный router без prefix `/cafes`:

```python
# backend/src/routers/cafe_links.py
cafe_links_router = APIRouter(prefix="/cafes", tags=["cafe-links"])
cafe_requests_router = APIRouter(tags=["cafe-requests"])

# Endpoints для cafe links (prefix=/cafes)
@cafe_links_router.post("/{cafe_id}/link-request", ...)
@cafe_links_router.patch("/{cafe_id}/notifications", ...)
@cafe_links_router.delete("/{cafe_id}/link", ...)

# Endpoints для cafe requests (no prefix)
@cafe_requests_router.get("/cafe-requests", ...)
@cafe_requests_router.post("/cafe-requests/{request_id}/approve", ...)
@cafe_requests_router.post("/cafe-requests/{request_id}/reject", ...)
```

```python
# backend/src/main.py
app.include_router(cafe_links_router, prefix="/api/v1")
app.include_router(cafe_requests_router, prefix="/api/v1")
```

**Решение Option 2 (менее предпочтительно):**
Исправить frontend hook на `/cafes/cafe-requests`:

```typescript
export function useCafeRequests(): UseDataResult<CafeRequest> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<CafeRequest>>(
    "/cafes/cafe-requests",  // <-- Исправлено
    fetcher
  );
```

**Рекомендация:** Использовать Option 1, так как логически `/cafe-requests` — это endpoint для менеджера, а не конкретного кафе. Prefix `/cafes` подходит только для endpoints `/cafes/{cafe_id}/...`.

## Технические детали

### React Hydration Mismatch

**Что такое hydration mismatch:**
- SSR генерирует HTML на сервере
- React на клиенте "гидрирует" HTML (прикрепляет event handlers)
- Если client-side render отличается от server-side HTML → warning + re-render

**Почему происходит:**
- localStorage доступен только в браузере (`typeof window !== 'undefined'`)
- SSR рендерит с дефолтными значениями (canSpin=true, timeLeft=0)
- CSR рендерит с реальными значениями из localStorage (canSpin=false, timeLeft=86400000)

**Как исправить:**
1. Использовать нейтральное начальное состояние (loading state)
2. Отложить клиент-специфичную логику в useEffect
3. Показывать loading до завершения гидрации

**Паттерн "mounted" флаг:**
```tsx
const [mounted, setMounted] = useState(false);

useEffect(() => {
  setMounted(true);
}, []);

if (!mounted) {
  return <div>Loading...</div>;  // Совпадает с SSR
}

return <div>{clientSpecificData}</div>;  // Только на клиенте
```

### FastAPI Router Prefix

**Как работает prefix:**
```python
router = APIRouter(prefix="/cafes")

@router.get("/cafe-requests")
# Результат: /cafes/cafe-requests
```

**Nested prefixes:**
```python
app.include_router(router, prefix="/api/v1")
# Результат: /api/v1/cafes/cafe-requests
```

**Логика префиксов:**
- `/cafes/{cafe_id}/...` — операции конкретного кафе
- `/cafe-requests` — глобальный список запросов для менеджера

Поэтому `/cafe-requests` не должен иметь prefix `/cafes`.

## Подзадачи

### Подзадача 1: Fix FortuneWheel Hydration
**Файлы:** `frontend_mini_app/src/app/FortuneWheel/page.tsx`

**Действия:**
1. Изменить начальное состояние `canSpin` и `timeLeft`:
   - `const [canSpin, setCanSpin] = useState(false);`
   - `const [timeLeft, setTimeLeft] = useState(0);`
2. Добавить `mounted` флаг:
   - `const [mounted, setMounted] = useState(false);`
3. Переместить localStorage логику в useEffect:
   ```tsx
   useEffect(() => {
     setMounted(true);
     const lastSpin = localStorage.getItem("lastSpin");
     if (lastSpin) {
       const nextSpinTime = parseInt(lastSpin) + ONE_DAY;
       const now = Date.now();
       if (now >= nextSpinTime) {
         setCanSpin(true);
       } else {
         setCanSpin(false);
         setTimeLeft(nextSpinTime - now);
       }
     } else {
       setCanSpin(true);
     }
   }, []);
   ```
4. Обновить JSX кнопки:
   ```tsx
   <button disabled={!canSpin || isSpinning}>
     {isSpinning
       ? "Крутим..."
       : !mounted || canSpin
       ? "Крутить колесо"
       : `Доступно через: ${formatTime(timeLeft)}`}
   </button>
   ```
5. Проверить отсутствие hydration warnings в console

### Подзадача 2: Fix ManagerPage Hydration
**Файлы:** `frontend_mini_app/src/app/manager/page.tsx`

**Действия:**
1. Изменить инициализацию `isInTelegram`:
   ```tsx
   const [isInTelegram, setIsInTelegram] = useState<boolean | null>(null);
   ```
2. Переместить логику проверки Telegram в useEffect:
   ```tsx
   useEffect(() => {
     const inTelegram = isTelegramWebApp();
     setIsInTelegram(inTelegram);

     if (!inTelegram) return;

     initTelegramWebApp();

     const initData = getTelegramInitData();
     if (!initData) {
       setAuthError("Telegram initData недоступен");
       return;
     }

     authenticateWithTelegram(initData)
       .then((response) => {
         if (response.user.role !== "manager") {
           router.push("/");
           return;
         }
         if (typeof window !== "undefined") {
           localStorage.setItem("user", JSON.stringify(response.user));
         }
         setIsAuthenticated(true);
       })
       .catch((err) => {
         setAuthError(err.message || "Не удалось авторизоваться");
       });
   }, [router]);
   ```
3. SSR и CSR рендерят одинаковый loading spinner пока `isInTelegram === null`
4. Проверить отсутствие hydration warnings

### Подзадача 3: Fix cafe-requests 404
**Файлы:**
- `backend/src/routers/cafe_links.py`
- `backend/src/routers/__init__.py` (если нужно экспортировать новый router)
- `backend/src/main.py`

**Действия:**

**Option 1 (рекомендуется):**
1. Создать отдельный router для cafe-requests в `cafe_links.py`:
   ```python
   cafe_links_router = APIRouter(prefix="/cafes", tags=["cafe-links"])
   cafe_requests_router = APIRouter(tags=["cafe-requests"])
   ```
2. Переместить endpoints `/cafe-requests*` в `cafe_requests_router`:
   ```python
   @cafe_requests_router.get("/cafe-requests", response_model=LinkRequestListSchema)
   @cafe_requests_router.post("/cafe-requests/{request_id}/approve", ...)
   @cafe_requests_router.post("/cafe-requests/{request_id}/reject", ...)
   ```
3. Экспортировать оба router'а из `__init__.py`:
   ```python
   from .cafe_links import cafe_links_router, cafe_requests_router
   ```
4. Подключить оба router'а в `main.py`:
   ```python
   app.include_router(cafe_links_router, prefix="/api/v1")
   app.include_router(cafe_requests_router, prefix="/api/v1")
   ```
5. Проверить:
   ```bash
   curl http://localhost:8000/api/v1/cafe-requests
   # Должен вернуть 200 OK или 401 Unauthorized (если требуется auth)
   ```

**Option 2 (если Option 1 неприемлем):**
1. Исправить frontend hook в `hooks.ts`:
   ```typescript
   export function useCafeRequests(): UseDataResult<CafeRequest> {
     const { data, error, isLoading, mutate } = useSWR<ListResponse<CafeRequest>>(
       "/cafes/cafe-requests",  // <-- Изменить путь
       fetcher
     );
   ```
2. Аналогично для `useApproveCafeRequest` и `useRejectCafeRequest`

**Рекомендуется Option 1**, так как URL `/api/v1/cafe-requests` более семантичен для глобального списка запросов менеджера.

## Тестирование

### Hydration Fix Tests
1. Запустить Next.js в production mode:
   ```bash
   cd frontend_mini_app
   npm run build
   npm start
   ```
2. Открыть DevTools → Console
3. Перейти на `/FortuneWheel`
4. Проверить отсутствие "Hydration failed" или "Text content did not match"
5. Перейти на `/manager`
6. Проверить отсутствие hydration warnings
7. Проверить корректную работу таймера в FortuneWheel после загрузки

### API Fix Tests
1. Запустить backend:
   ```bash
   docker-compose up backend
   ```
2. Проверить endpoint:
   ```bash
   curl -X GET http://localhost:8000/api/v1/cafe-requests \
     -H "Authorization: Bearer <manager_token>"
   ```
   Ожидается: 200 OK с данными или 401 Unauthorized
3. Открыть frontend `/manager` → таб "Requests"
4. Проверить, что RequestsList загружает данные без 404 ошибок

### Regression Tests
- [ ] FortuneWheel: таймер обновляется каждую секунду
- [ ] FortuneWheel: кнопка disabled корректно работает
- [ ] ManagerPage: аутентификация работает
- [ ] ManagerPage: редирект не-менеджеров на `/`
- [ ] RequestsList: approve/reject запросов работает

## Риски

### Риск 1: Изменение initial state может сломать логику
**Решение:** Тщательно протестировать все сценарии:
- Первый запуск (нет lastSpin в localStorage)
- После спина (lastSpin сохранен, таймер активен)
- После истечения таймера (canSpin восстанавливается)

### Риск 2: useEffect может вызвать задержку UI
**Решение:** Показывать loading state или дефолтный текст кнопки до завершения useEffect. Это нормально для гидрации.

### Риск 3: Разделение router'а может сломать существующие endpoints
**Решение:** Проверить все endpoints из `cafe_links.py`:
- `/cafes/{cafe_id}/link-request` (POST)
- `/cafe-requests` (GET)
- `/cafe-requests/{request_id}/approve` (POST)
- `/cafe-requests/{request_id}/reject` (POST)
- `/cafes/{cafe_id}/notifications` (PATCH)
- `/cafes/{cafe_id}/link` (DELETE)

Убедиться, что все работают после изменений.

## Документация

После применения фикса обновить:
- `.memory-base/tech-docs/frontend-components.md` — добавить note о hydration fixes
- `.memory-base/tech-docs/issues/` — создать `hydration-mismatch-fix.md` с описанием решения

## Примечания

- Hydration mismatch — это warning, не error, но влияет на UX и производительность
- Next.js в production mode показывает hydration errors более явно
- localStorage всегда требует `typeof window !== 'undefined'` проверки
- FastAPI router prefix складываются: `app.include_router(router, prefix="/api") + router(prefix="/v1") = /api/v1`
