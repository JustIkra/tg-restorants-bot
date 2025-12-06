---
agent: coder
task_id: TSK-005
subtask: 2
subtask_name: "Frontend (Modules 5-6)"
status: completed
next: reviewer
created_at: 2025-12-06T15:45:00
files_changed:
  - path: frontend_mini_app/src/app/page.tsx
    action: modified
  - path: frontend_mini_app/.env.example
    action: modified
  - path: frontend_mini_app/src/components/TelegramFallback/TelegramFallback.tsx
    action: exists (no changes needed)
---

## Реализация

Выполнена подзадача 2 для TSK-005: Frontend интеграция Telegram Mini App (Модули 5-6 из архитектурного плана).

### Модуль 5: Telegram Environment Check & Fallback UI

**Компонент TelegramFallback.tsx:**
- ✅ Компонент уже существовал и не требовал изменений
- Расположение: `frontend_mini_app/src/components/TelegramFallback/TelegramFallback.tsx`
- Функциональность:
  - Показывает friendly UI с иконкой Telegram
  - Объясняет пользователю, как открыть приложение через бот
  - Инструкции: найти бот → нажать Menu или /order
  - Использует дизайн-систему проекта (background blur effects, purple gradient)

**Обновление page.tsx:**

1. **Добавлены импорты:**
   ```tsx
   import TelegramFallback from "@/components/TelegramFallback/TelegramFallback";
   import { isTelegramWebApp, initTelegramWebApp, getTelegramInitData } from "@/lib/telegram/webapp";
   ```

2. **Добавлен state для отслеживания Telegram окружения:**
   ```tsx
   const [isInTelegram, setIsInTelegram] = useState<boolean | null>(null);
   ```
   - `null` = проверка в процессе (показываем loading spinner)
   - `true` = в Telegram (показываем основной UI)
   - `false` = не в Telegram (показываем fallback)

3. **Добавлен useEffect для инициализации Telegram WebApp:**
   ```tsx
   useEffect(() => {
     const inTelegram = isTelegramWebApp();
     setIsInTelegram(inTelegram);

     if (inTelegram) {
       initTelegramWebApp();  // Ready + Expand
       const initData = getTelegramInitData();
       // initData будет автоматически использоваться API client для auth
     }
   }, []);
   ```

4. **Добавлена логика early return:**
   - **Loading state** (пока проверяем Telegram):
     ```tsx
     if (isInTelegram === null) {
       return <div>...spinner...</div>;
     }
     ```
   - **Fallback UI** (не в Telegram):
     ```tsx
     if (!isInTelegram) {
       return <TelegramFallback />;
     }
     ```
   - **Main UI** (в Telegram):
     ```tsx
     return <div>...existing page content...</div>;
     ```

### Модуль 6: Frontend Environment Variables

**Обновление .env.example:**

Добавлены подробные комментарии для разных окружений:

1. **Development (local):**
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

2. **Development (Docker with nginx):**
   ```bash
   # NEXT_PUBLIC_API_URL=http://localhost/api/v1
   ```

3. **Development (ngrok for Telegram Mini App):**
   ```bash
   # NEXT_PUBLIC_API_URL=https://{ngrok-url}/api/v1
   ```
   - Требуется для тестирования как Telegram Mini App
   - Telegram требует HTTPS даже для dev

4. **Production:**
   ```bash
   # NEXT_PUBLIC_API_URL=https://lunchbot.vibe-labs.ru/api/v1
   ```
   - Домен из требований задачи

## Ключевые решения

### 1. Использование существующего TelegramFallback компонента

Компонент уже был реализован в проекте и полностью соответствует требованиям:
- Соответствует дизайн-системе (фиолетовые градиенты, blur effects)
- Четкие инструкции для пользователя
- Адаптивный дизайн
- Нет необходимости в изменениях

### 2. Three-state pattern для проверки Telegram окружения

Использован паттерн с тремя состояниями (`null | true | false`):
- Позволяет показать loading spinner во время проверки
- Избегает "мерцания" UI при переключении между states
- Четкое разделение ответственности (loading → fallback → main)

### 3. Автоматическая инициализация Telegram WebApp

Инициализация выполняется автоматически при монтировании компонента:
- `initTelegramWebApp()` вызывает `WebApp.ready()` и `WebApp.expand()`
- `getTelegramInitData()` получает данные для аутентификации
- Нет необходимости в ручной настройке со стороны пользователя

### 4. Комментарии для ngrok в .env.example

Явно документирована необходимость ngrok для development:
- Telegram Mini Apps требуют HTTPS
- ngrok - самый простой способ получить HTTPS туннель в dev
- Четкие инструкции по настройке для разработчиков

## Интеграция с существующим кодом

### Совместимость с API client

Текущий API client (`src/lib/api/client.ts`) уже настроен на работу с `NEXT_PUBLIC_API_URL`:
- Все API запросы автоматически используют правильный URL
- При переключении между окружениями (local → ngrok → production) не требуется изменений кода
- Только обновление переменной окружения

### Совместимость с SWR hooks

Hooks (`useCafes`, `useMenu`, `useCombos`) продолжают работать без изменений:
- Данные загружаются только если `isInTelegram === true`
- При показе fallback UI нет ненужных API запросов
- При показе loading spinner данные еще не загружаются

### Сохранение существующей логики

Вся существующая логика `page.tsx` сохранена:
- Выбор кафе и категорий
- Управление корзиной
- Загрузка доступных дат
- Валидация заказа
- Только добавлена проверка Telegram окружения в начале

## Что нужно проверить

### Функциональное тестирование

1. **Открытие в браузере (не в Telegram):**
   - [ ] Показывается TelegramFallback UI
   - [ ] Нет API запросов к backend
   - [ ] Отображаются инструкции для пользователя

2. **Открытие в Telegram WebApp:**
   - [ ] Показывается loading spinner на момент проверки
   - [ ] Telegram WebApp инициализируется (`ready()`, `expand()`)
   - [ ] Показывается основной UI с меню
   - [ ] API запросы работают корректно

3. **Переключение между окружениями:**
   - [ ] Local: `http://localhost:8000/api/v1` работает
   - [ ] Docker nginx: `http://localhost/api/v1` работает
   - [ ] ngrok: `https://xxx.ngrok.io/api/v1` работает
   - [ ] Production: `https://lunchbot.vibe-labs.ru/api/v1` будет работать

### Code Review

1. **TypeScript типизация:**
   - [ ] `isInTelegram: boolean | null` корректен
   - [ ] Нет any типов
   - [ ] Все импорты корректны

2. **React best practices:**
   - [ ] useEffect без лишних зависимостей
   - [ ] Early returns для разных состояний
   - [ ] Нет memory leaks

3. **Code style:**
   - [ ] Соответствует Tailwind CSS паттернам проекта
   - [ ] Двойные кавычки для строк
   - [ ] Импорты отсортированы

## Связь с другими модулями

### Зависимости от других модулей TSK-005

- **Модули 1-4 (Backend & Bot):** Независимы от этих изменений
  - Frontend работает с любым backend, который предоставляет правильный API
  - Environment variables позволяют настроить URL

- **Модуль 7 (Documentation):** Должен документировать:
  - Как настроить ngrok для dev
  - Как обновить .env для production
  - Как тестировать в Telegram

### Следующие шаги

После review и тестирования:

1. **Tester:** Проверить все три состояния (loading, fallback, main UI)
2. **Integration:** Объединить с изменениями из модулей 1-4 (Backend & Bot)
3. **E2E тестирование:** Полный флоу от бота до заказа
4. **Production deployment:** Обновить .env с production URL

## Примечания

- `TelegramFallback.tsx` уже существовал - отличное решение, не требует изменений
- Проверка `isTelegramWebApp()` выполняется мгновенно (нет async)
- Loading state нужен для консистентности UX, хотя проверка быстрая
- initData будет автоматически использоваться для аутентификации (реализация в API client)

## Риски и митигация

### Риск: Telegram WebApp SDK не инициализируется

**Симптомы:** `isTelegramWebApp()` возвращает `false` даже в Telegram

**Митигация:**
- Проверить, что `@twa-dev/sdk` установлен (`package.json`)
- Проверить, что Telegram WebApp запущен через правильный URL (Menu Button или /order)
- Проверить console logs для debug информации

### Риск: HTTPS требование в dev

**Симптомы:** Telegram Mini App не открывается с `http://localhost`

**Митигация:**
- Использовать ngrok: `ngrok http 80`
- Обновить `NEXT_PUBLIC_API_URL` в `.env.local`
- Документировано в `.env.example`

### Риск: CORS ошибки с ngrok

**Симптомы:** API запросы блокируются браузером

**Митигация:**
- Backend должен добавить ngrok URL в `CORS_ORIGINS`
- Это часть модулей 1-4 (Backend configuration)
- Проверить через Network tab в DevTools

## Заключение

Модули 5 и 6 реализованы успешно:

✅ **Модуль 5:** Telegram Environment Check & Fallback UI
- Проверка Telegram окружения при загрузке
- Early return с fallback UI для не-Telegram
- Автоматическая инициализация Telegram WebApp

✅ **Модуль 6:** Frontend Environment Variables
- Подробные комментарии для всех окружений
- Production URL для `lunchbot.vibe-labs.ru`
- Инструкции для ngrok setup

Код готов к review и тестированию.
