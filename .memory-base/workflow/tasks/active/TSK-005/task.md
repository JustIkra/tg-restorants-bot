---
id: TSK-005
title: "Интеграция фронтенда как Telegram Mini App"
pipeline: feature
status: pending
created_at: 2025-12-06T12:00:00
related_files:
  - backend/src/telegram/bot.py
  - backend/src/telegram/handlers.py
  - frontend_mini_app/src/lib/telegram/webapp.ts
  - frontend_mini_app/package.json
  - backend/.env.example
  - docker-compose.yml
impact:
  api: false
  db: false
  frontend: true
  services: true
  telegram_bot: true
---

## Описание

Интегрировать существующий Next.js фронтенд как **Telegram Mini App**, запускаемое через Telegram бот. Сейчас фронтенд работает как standalone веб-приложение, но не интегрирован с Telegram ботом для запуска как Mini App.

## Текущее состояние

### Что уже есть:

**Frontend (TSK-001):**
- ✅ Next.js 16 + React 19 + Tailwind CSS 4
- ✅ Telegram WebApp SDK интегрирован (`@twa-dev/sdk`)
- ✅ Обертка `src/lib/telegram/webapp.ts` с функциями:
  - `initTelegramWebApp()`
  - `getTelegramInitData()`
  - `closeTelegramWebApp()`
  - `isTelegramWebApp()`
- ✅ Авторизация через `initData` (backend endpoint `/auth/telegram`)
- ✅ UI компоненты готовы
- ✅ Docker Compose сервис `frontend` (порт 3000)

**Backend Telegram Bot:**
- ✅ Aiogram 3.0 бот (`backend/src/telegram/bot.py`)
- ✅ Handlers для заявок от кафе (`/link`, `/start`, `/help`)
- ✅ JWT авторизация для Telegram WebApp (`POST /auth/telegram`)
- ✅ Docker Compose сервис `telegram-bot`

**Infrastructure:**
- ✅ Docker Compose с сервисами backend, frontend, telegram-bot
- ✅ Environment variables в `.env`

### Что НЕ сделано:

**Telegram Bot ↔ Mini App интеграция:**
- ❌ Telegram бот не имеет команд для запуска Mini App
- ❌ Не настроен Menu Button для Mini App через BotFather
- ❌ Фронтенд доступен только по `http://localhost:3000`, не как Telegram Mini App
- ❌ URL фронтенда не настроен для публичного доступа (нужен HTTPS для production)
- ❌ Нет inline button для запуска Mini App из чата с ботом

**Deployment:**
- ❌ Фронтенд не deploy на публичный HTTPS URL (требуется для Telegram Mini Apps)
- ❌ Webhook для production (сейчас polling)
- ❌ CORS может требовать настройки для Telegram домена

## Acceptance Criteria

### 1. Настройка Telegram Bot для Mini App

#### BotFather Configuration
- [ ] Зарегистрировать Mini App через BotFather `/newapp`:
  - Привязать к существующему боту
  - Указать название Mini App
  - Загрузить иконку (опционально)
  - Указать URL фронтенда (нужен HTTPS в production)
- [ ] Настроить Menu Button через BotFather `/setmenubutton`:
  - Текст кнопки: "Заказать обед" или "Order Lunch"
  - URL: `https://your-domain.com` (в dev: ngrok/локальный туннель)
  - Альтернатива: использовать Bot API метод `setChatMenuButton`

#### Bot Commands для запуска Mini App
- [ ] Добавить команду `/order` в `handlers.py`:
  - Отправляет inline keyboard с кнопкой типа `web_app`
  - Кнопка открывает Mini App URL
  - Пример:
    ```python
    from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup

    @router.message(Command("order"))
    async def cmd_order(message: Message):
        webapp = WebAppInfo(url="https://your-domain.com")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Заказать обед", web_app=webapp)]
        ])
        await message.answer("Откройте меню для заказа:", reply_markup=keyboard)
    ```
- [ ] Обновить команду `/start` для новых пользователей:
  - Показывать кнопку запуска Mini App
  - Объяснить, как сделать заказ через Mini App
- [ ] Обновить `/help` с информацией о Mini App

### 2. Frontend Deployment для Telegram Mini App

#### HTTPS URL (обязательно для Telegram Mini Apps)
- [ ] **Development:**
  - Использовать ngrok или CloudFlare Tunnel для HTTPS туннеля:
    ```bash
    ngrok http 3000
    # или
    cloudflared tunnel --url http://localhost:3000
    ```
  - Обновить URL в BotFather и bot handlers
  - Обновить `NEXT_PUBLIC_API_URL` для ngrok URL backend

- [ ] **Production:**
  - Deploy фронтенд на:
    - Vercel (рекомендуется для Next.js)
    - Netlify
    - Railway
    - AWS S3 + CloudFront
    - Собственный VPS с Nginx + SSL (Let's Encrypt)
  - Получить HTTPS домен
  - Настроить CORS в backend для production домена

#### Environment Variables
- [ ] Добавить в `frontend_mini_app/.env.local`:
  ```bash
  NEXT_PUBLIC_API_URL=https://api.your-domain.com/api/v1
  ```
- [ ] Добавить в `backend/.env`:
  ```bash
  TELEGRAM_BOT_TOKEN=your_bot_token
  TELEGRAM_MINI_APP_URL=https://miniapp.your-domain.com
  CORS_ORIGINS=["https://miniapp.your-domain.com","https://web.telegram.org"]
  ```

### 3. Telegram WebApp SDK Integration Testing

#### Frontend Initialization
- [ ] Проверить корректную инициализацию в `page.tsx`:
  ```typescript
  useEffect(() => {
    initTelegramWebApp();

    const initData = getTelegramInitData();
    if (initData) {
      authenticateWithTelegram(initData)
        .then(() => setIsAuthenticated(true))
        .catch(err => console.error("Auth failed:", err));
    } else {
      // Development fallback или показать ошибку
      console.warn("Not in Telegram WebApp");
    }
  }, []);
  ```
- [ ] Добавить обработку кейса "не в Telegram":
  - Показать сообщение "Откройте приложение через Telegram бот"
  - Или показать QR код для запуска Mini App

#### Theme Integration
- [ ] Использовать Telegram тему (опционально):
  ```typescript
  const theme = getTelegramTheme();
  if (theme) {
    // Применить theme.bg_color, theme.text_color и т.д.
  }
  ```

#### Main Button Integration (опционально)
- [ ] Заменить CheckoutButton на Telegram MainButton:
  ```typescript
  useEffect(() => {
    if (isOrderComplete) {
      showMainButton("Оформить заказ", handleCheckout);
    } else {
      hideMainButton();
    }

    return () => hideMainButton();
  }, [isOrderComplete]);
  ```

### 4. Backend Integration

#### JWT Auth для Telegram WebApp
- [ ] Проверить работу endpoint `POST /auth/telegram`:
  - Валидация `initData` от Telegram
  - Создание/получение пользователя по `tgid`
  - Возврат JWT токена
  - Обработка ошибок (invalid initData, expired, etc.)

#### CORS Configuration
- [ ] Обновить CORS для Telegram домена:
  ```python
  CORS_ORIGINS = [
      "https://miniapp.your-domain.com",
      "https://web.telegram.org",  # Telegram WebApp iframe
      "http://localhost:3000",  # Development
  ]
  ```

### 5. Testing

#### Manual Testing Checklist
- [ ] **Запуск через Menu Button:**
  1. Открыть чат с ботом в Telegram
  2. Нажать на Menu Button (слева от поля ввода)
  3. Mini App открывается в полноэкранном режиме
  4. Авторизация проходит автоматически
  5. Данные меню загружаются

- [ ] **Запуск через /order команду:**
  1. Отправить `/order` боту
  2. Нажать на inline кнопку "Заказать обед"
  3. Mini App открывается
  4. Функционал работает

- [ ] **Создание заказа:**
  1. Выбрать кафе
  2. Выбрать комбо
  3. Заполнить все категории
  4. Добавить extras (опционально)
  5. Нажать "Оформить заказ"
  6. Получить подтверждение
  7. Mini App закрывается (`closeTelegramWebApp()`)

- [ ] **Обработка ошибок:**
  1. Попытка открыть Mini App не из Telegram → показать сообщение
  2. Ошибка авторизации → показать ошибку
  3. Ошибка API → показать понятное сообщение

- [ ] **Кроссплатформенность:**
  1. iOS Telegram
  2. Android Telegram
  3. Desktop Telegram
  4. Telegram Web (web.telegram.org)

#### Integration Tests
- [ ] E2E тест: запуск Mini App → авторизация → заказ → закрытие
- [ ] Тест обработки Telegram initData в backend
- [ ] Тест CORS для Telegram домена

### 6. Documentation

- [ ] Обновить README с инструкциями:
  - Как запустить Mini App в development (ngrok)
  - Как настроить BotFather
  - Как deploy в production
  - Troubleshooting (частые проблемы)

- [ ] Создать deployment guide:
  - Frontend deployment (Vercel/Netlify)
  - Backend deployment с HTTPS
  - Настройка CORS
  - Настройка Telegram Bot (Menu Button, commands)

- [ ] User guide для сотрудников:
  - Как открыть Mini App через бот
  - Как сделать заказ
  - Скриншоты интерфейса

## Контекст

### Архитектура Telegram Mini Apps

```
┌─────────────────────────────────────────────┐
│         Telegram Mobile/Desktop App         │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │    Mini App (Next.js Frontend)        │  │
│  │    https://miniapp.your-domain.com    │  │
│  │                                       │  │
│  │  - Telegram WebApp SDK                │  │
│  │  - initData для авторизации           │  │
│  │  - MainButton, BackButton             │  │
│  └──────────────┬────────────────────────┘  │
│                 │ HTTPS API Requests         │
└─────────────────┼────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│          Backend API (FastAPI)              │
│      https://api.your-domain.com            │
│                                             │
│  POST /auth/telegram                        │
│    - Validate initData                      │
│    - Return JWT token                       │
│                                             │
│  GET /cafes, /menu, /orders, etc.          │
│    - Authorization: Bearer {jwt}            │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│       Telegram Bot (aiogram)                │
│                                             │
│  /start → Welcome + Mini App button         │
│  /order → Inline button (web_app)           │
│  /link  → Cafe linking                      │
│  Menu Button → Direct Mini App launch       │
└─────────────────────────────────────────────┘
```

### Способы запуска Mini App

Telegram предлагает несколько способов запуска Mini Apps:

1. **Menu Button** (рекомендуется):
   - Настраивается через BotFather `/setmenubutton`
   - Или через Bot API `setChatMenuButton`
   - Кнопка слева от поля ввода в чате с ботом
   - Самый быстрый доступ для пользователей

2. **Inline Button (web_app type)**:
   - Кнопка в сообщении бота
   - Используется в `/order` команде
   - Можно отправлять в любое время

3. **Direct Link** (после `/newapp`):
   - Формат: `https://t.me/{bot_username}/{app_short_name}`
   - Можно шарить в других чатах
   - Требует создания app через BotFather

4. **Attachment Menu** (для продвинутых кейсов):
   - Бот добавляется в attachment menu
   - Доступен из любого чата
   - Требует одобрения Telegram (для крупных рекламодателей)

### Требования Telegram Mini Apps

**Обязательные:**
- ✅ HTTPS URL (обязательно, даже для dev через ngrok)
- ✅ Telegram WebApp SDK инициализация
- ✅ Валидация `initData` на backend (безопасность)
- ✅ Responsive дизайн (мобильные устройства)

**Рекомендуемые:**
- Использование Telegram MainButton вместо обычной кнопки
- Поддержка Telegram темы (light/dark)
- Haptic Feedback для нативного ощущения
- BackButton для навигации

### Related Files

**Telegram Bot:**
- `backend/src/telegram/bot.py` - инициализация бота
- `backend/src/telegram/handlers.py` - команды бота (нужно добавить `/order`)

**Frontend:**
- `frontend_mini_app/src/lib/telegram/webapp.ts` - обертка SDK
- `frontend_mini_app/src/app/page.tsx` - main page (использует Telegram SDK)
- `frontend_mini_app/package.json` - зависимости (`@twa-dev/sdk`)

**Backend Auth:**
- `backend/src/auth/telegram.py` - валидация `initData`
- `backend/src/api/routes/auth.py` - endpoint `/auth/telegram`

**Configuration:**
- `backend/.env.example` - env vars (TELEGRAM_BOT_TOKEN, CORS_ORIGINS)
- `docker-compose.yml` - сервисы frontend, backend, telegram-bot
- `frontend_mini_app/.env.example` - NEXT_PUBLIC_API_URL

### Документация

**Telegram Mini Apps:**
- Official Docs: https://core.telegram.org/bots/webapps
- SDK Reference: https://docs.telegram-mini-apps.com/
- BotFather Guide: https://core.telegram.org/bots/features#botfather

**Deployment Options:**
- Vercel: https://vercel.com/docs/deployments/overview
- ngrok (dev): https://ngrok.com/docs
- CloudFlare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

## Подзадачи для Architect

Architect должен разбить задачу на модули:

### Фаза 1: Development Setup
1. Настроить ngrok/CloudFlare Tunnel для HTTPS в dev
2. Обновить environment variables для dev туннеля
3. Протестировать авторизацию через Telegram WebApp SDK

### Фаза 2: Telegram Bot Integration
4. Добавить команду `/order` с inline button (web_app)
5. Настроить Menu Button через BotFather (или Bot API)
6. Обновить `/start` и `/help` с инструкциями для Mini App
7. Зарегистрировать Mini App через BotFather `/newapp` (опционально)

### Фаза 3: Frontend Enhancements
8. Добавить проверку `isTelegramWebApp()` с fallback UI
9. Интеграция Telegram MainButton (опционально)
10. Применение Telegram темы (опционально)
11. Haptic Feedback для кнопок (опционально)

### Фаза 4: Testing
12. Manual testing на всех платформах (iOS, Android, Desktop, Web)
13. E2E тесты для полного флоу
14. Тестирование CORS и авторизации

### Фаза 5: Production Deployment
15. Deploy фронтенда на Vercel/Netlify с HTTPS
16. Настройка production CORS в backend
17. Обновление Bot URL в BotFather
18. Production testing

### Фаза 6: Documentation
19. User guide для сотрудников
20. Deployment guide для админов
21. Troubleshooting guide

## Ожидаемый результат

После выполнения задачи:

1. **Фронтенд доступен как Telegram Mini App:**
   - Запускается через Menu Button в боте
   - Запускается через команду `/order` с inline кнопкой
   - Работает на всех платформах Telegram (iOS, Android, Desktop, Web)

2. **Авторизация работает seamless:**
   - Пользователь автоматически авторизован при открытии Mini App
   - JWT токен получается из Telegram `initData`
   - Нет необходимости вводить логин/пароль

3. **Full user flow работает:**
   - Открыть бот → Нажать Menu Button → Выбрать кафе → Создать заказ → Закрыть Mini App
   - Заказ сохраняется в PostgreSQL
   - Пользователь видит подтверждение

4. **Development и Production окружения настроены:**
   - Dev: ngrok туннель для локальной разработки
   - Prod: HTTPS deployment (Vercel/Netlify)
   - CORS настроен корректно

5. **Документация готова:**
   - Инструкции для пользователей
   - Deployment guide
   - Troubleshooting

## Связь с другими задачами

- **TSK-001**: Frontend готов, нужно интегрировать с Telegram Bot
- **TSK-002**: Backend API готов, авторизация через Telegram уже реализована
- **TSK-004**: E2E тестирование будет включать тесты Mini App
- **Зависимости**: TSK-005 зависит от TSK-001 (frontend) и TSK-002 (backend auth)

## Примечания

- Для development обязательно использовать HTTPS туннель (ngrok/CloudFlare)
- Telegram Mini Apps НЕ работают с `http://localhost` напрямую
- BotFather требует HTTPS URL даже для test сервера
- `initData` валидация критична для безопасности (уже реализована в TSK-002)
- Menu Button - самый удобный способ для пользователей
- После deploy на production обновить URL в BotFather

## Приоритет

**Critical:**
- HTTPS туннель для dev
- Telegram Bot команды (`/order`)
- Menu Button настройка

**High:**
- Frontend fallback для не-Telegram окружения
- Production deployment
- Testing на всех платформах

**Medium:**
- Telegram MainButton интеграция
- Telegram Theme support
- Direct link через `/newapp`

**Low:**
- Haptic Feedback
- Attachment Menu (не доступен без одобрения Telegram)
