---
agent: architect
task_id: TSK-005
status: completed
next: coder
created_at: 2025-12-06T14:30:00
files_changed: []
---

## Анализ

Задача TSK-005 требует интеграции существующего Next.js фронтенда как Telegram Mini App, запускаемого через Telegram бота.

**Текущее состояние:**
- ✅ Frontend готов (Next.js 16, React 19, Tailwind CSS 4)
- ✅ Telegram WebApp SDK интегрирован (`@twa-dev/sdk`)
- ✅ Обертка `webapp.ts` с функциями `initTelegramWebApp()`, `getTelegramInitData()`, `isTelegramWebApp()`
- ✅ Backend API с JWT авторизацией через `/auth/telegram`
- ✅ Docker Compose с nginx reverse proxy
- ✅ Aiogram 3.0 бот с handlers (`/start`, `/help`, `/link`)

**Что НЕ сделано:**
- ❌ Telegram бот не имеет команд для запуска Mini App (`/order`)
- ❌ Не настроен Menu Button для Mini App
- ❌ Фронтенд не имеет fallback UI для не-Telegram окружения
- ❌ URL фронтенда не настроен для публичного доступа (нужен HTTPS)
- ❌ Environment variables не настроены для Mini App URL

**Ключевые зависимости:**
- Telegram Mini Apps требуют HTTPS URL (обязательно)
- Development: нужен ngrok/CloudFlare Tunnel для HTTPS туннеля
- Production: deploy на `lunchbot.vibe-labs.ru` через Nginx Proxy Manager

**Риски:**
1. HTTPS настройка может потребовать внешнюю инфраструктуру (ngrok для dev)
2. CORS может требовать дополнительной настройки для Telegram домена (`https://web.telegram.org`)
3. Telegram WebApp SDK может вести себя по-разному на разных платформах (iOS, Android, Desktop, Web)
4. BotFather требует валидный HTTPS URL даже для test окружения

## Архитектурное решение

### Стратегия интеграции

**1. Development Setup (Phase 1):**
- Использовать ngrok для HTTPS туннеля: `ngrok http 80`
- Обновить environment variables для ngrok URL
- Настроить CORS в backend для ngrok домена

**2. Telegram Bot Integration (Phase 2):**
- Добавить команду `/order` с inline button типа `web_app`
- Обновить `/start` и `/help` с информацией о Mini App
- Настроить Menu Button через Bot API (не BotFather, для автоматизации)

**3. Frontend Enhancements (Phase 3):**
- Добавить проверку `isTelegramWebApp()` при загрузке
- Показать fallback UI если открыто не в Telegram
- Интеграция Telegram MainButton (опционально, отложить)

**4. Production Deployment (Phase 4):**
- Deploy на production сервер `172.25.0.200`
- Настроить внешний Nginx Proxy Manager для HTTPS
- Обновить CORS и environment variables для production
- Обновить Bot URL

### Изменения в данных

**Нет изменений в базе данных.**

Все данные и API уже готовы. Требуется только:
- Environment variables для TELEGRAM_MINI_APP_URL
- CORS настройка для Telegram доменов

### API изменения

**Нет новых API endpoints.**

Используются существующие:
- `POST /auth/telegram` - уже реализован
- `GET /cafes?active_only=true` - уже реализован
- `GET /cafes/{id}/menu` - уже реализован
- `POST /orders` - уже реализован

**CORS обновление:**
```python
# backend/.env
CORS_ORIGINS=[
  "http://localhost",
  "https://{ngrok-url}",  # dev
  "https://lunchbot.vibe-labs.ru",  # production
  "https://web.telegram.org"  # Telegram WebApp iframe
]
```

### Bot changes

**Telegram Bot API integration:**

1. **Команда `/order`:**
   - Отправляет inline keyboard с кнопкой типа `web_app`
   - URL: динамически из environment variable `TELEGRAM_MINI_APP_URL`

2. **Menu Button:**
   - Настройка через Bot API `setChatMenuButton`
   - Вызывается при старте бота (в `bot.py`)
   - URL: из `TELEGRAM_MINI_APP_URL`

3. **Обновление `/start` и `/help`:**
   - Добавить информацию о запуске Mini App
   - Показать inline кнопку для быстрого доступа

## Подзадачи для Coder

Разделяем задачу на **независимые модули**, которые можно выполнять **параллельно**.

### Модуль 1: Backend Environment & CORS Configuration

**Файлы:**
- `backend/.env.example`
- `backend/src/config.py`
- `backend/src/main.py` (CORS middleware)

**Действия:**
1. Добавить `TELEGRAM_MINI_APP_URL` в `.env.example`:
   ```bash
   # Telegram Mini App URL (для Menu Button и /order команды)
   TELEGRAM_MINI_APP_URL=http://localhost  # dev через ngrok: https://xxx.ngrok.io
   ```

2. Обновить `CORS_ORIGINS` в `.env.example` для поддержки Telegram:
   ```bash
   CORS_ORIGINS=["http://localhost","https://web.telegram.org"]
   ```

3. Убедиться, что `config.py` читает `TELEGRAM_MINI_APP_URL` из environment:
   ```python
   TELEGRAM_MINI_APP_URL: str = Field(default="http://localhost")
   ```

4. Проверить, что CORS middleware в `main.py` корректно обрабатывает список `CORS_ORIGINS`

**Результат:** Backend готов к работе с Telegram Mini App URLs и CORS

### Модуль 2: Telegram Bot - `/order` Command Handler

**Файлы:**
- `backend/src/telegram/handlers.py`

**Действия:**
1. Добавить новый handler для команды `/order`:
   ```python
   from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup

   @router.message(Command("order"))
   async def cmd_order(message: Message):
       """Handle /order command - launch Mini App."""
       webapp = WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL)
       keyboard = InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text="🍽 Заказать обед", web_app=webapp)]
       ])
       await message.answer(
           "Откройте приложение для заказа обеда:",
           reply_markup=keyboard
       )
   ```

2. Импортировать `settings` для доступа к `TELEGRAM_MINI_APP_URL`

**Результат:** Команда `/order` работает и открывает Mini App

### Модуль 3: Telegram Bot - Update `/start` and `/help` Commands

**Файлы:**
- `backend/src/telegram/handlers.py`

**Действия:**
1. Обновить `cmd_start` для показа Mini App кнопки:
   ```python
   @router.message(CommandStart())
   async def cmd_start(message: Message):
       webapp = WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL)
       keyboard = InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text="🍽 Заказать обед", web_app=webapp)],
           [InlineKeyboardButton(text="📖 Помощь", callback_data="help")]
       ])
       await message.answer(
           "👋 Привет! Это бот для заказа обедов.\n\n"
           "Нажмите кнопку ниже, чтобы открыть меню и сделать заказ.\n\n"
           "Для привязки кафе используйте команду /link <cafe_id>",
           reply_markup=keyboard
       )
   ```

2. Обновить `cmd_help` с информацией о Mini App:
   ```python
   @router.message(Command("help"))
   async def cmd_help(message: Message):
       await message.answer(
           "📖 Доступные команды:\n\n"
           "/start - Начать работу с ботом\n"
           "/order - Открыть меню для заказа обеда\n"
           "/link <cafe_id> - Привязать кафе к этому чату (для менеджеров)\n"
           "/status - Проверить статус привязки кафе\n"
           "/help - Показать эту справку\n\n"
           "💡 Для заказа обеда нажмите кнопку Menu или используйте команду /order"
       )
   ```

**Результат:** `/start` и `/help` показывают информацию о Mini App

### Модуль 4: Telegram Bot - Menu Button Configuration

**Файлы:**
- `backend/src/telegram/bot.py`

**Действия:**
1. Добавить настройку Menu Button при старте бота:
   ```python
   from aiogram.types import MenuButtonWebApp, WebAppInfo

   async def setup_menu_button():
       """Configure Menu Button for Mini App launch."""
       webapp = WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL)
       menu_button = MenuButtonWebApp(text="Заказать обед", web_app=webapp)
       await bot.set_chat_menu_button(menu_button=menu_button)
       logger.info(f"Menu button configured with URL: {settings.TELEGRAM_MINI_APP_URL}")

   async def main():
       """Main entrypoint for running the bot."""
       from .handlers import router
       dp.include_router(router)

       # Setup Menu Button
       await setup_menu_button()

       # Start polling for updates
       await dp.start_polling(bot)
   ```

2. Импортировать `settings` для доступа к `TELEGRAM_MINI_APP_URL`

**Результат:** Menu Button настроена и открывает Mini App

### Модуль 5: Frontend - Telegram Environment Check & Fallback UI

**Файлы:**
- `frontend_mini_app/src/app/page.tsx`
- `frontend_mini_app/src/components/TelegramFallback.tsx` (новый файл)

**Действия:**
1. Создать компонент `TelegramFallback.tsx`:
   ```tsx
   import { FaTelegram } from "react-icons/fa6";

   export default function TelegramFallback() {
     return (
       <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
         <div className="max-w-md w-full bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center">
           <FaTelegram className="text-[#26A5E4] text-6xl mx-auto mb-4" />
           <h1 className="text-white text-2xl font-bold mb-4">
             Откройте через Telegram
           </h1>
           <p className="text-gray-300 mb-6">
             Это приложение работает только внутри Telegram.
             Откройте бот и нажмите кнопку "Заказать обед" или используйте команду /order.
           </p>
           <div className="bg-white/5 border border-white/10 rounded-lg p-4 text-left">
             <p className="text-gray-400 text-sm mb-2">Инструкция:</p>
             <ol className="text-gray-300 text-sm space-y-1">
               <li>1. Откройте Telegram</li>
               <li>2. Найдите бот @your_bot_username</li>
               <li>3. Нажмите кнопку Menu или отправьте /order</li>
             </ol>
           </div>
         </div>
       </div>
     );
   }
   ```

2. Обновить `page.tsx` для проверки Telegram окружения:
   ```tsx
   'use client';

   import { useState, useEffect } from 'react';
   import { isTelegramWebApp, initTelegramWebApp, getTelegramInitData } from '@/lib/telegram/webapp';
   import { authenticateWithTelegram } from '@/lib/api/client';
   import TelegramFallback from '@/components/TelegramFallback';

   export default function Home() {
     const [isInTelegram, setIsInTelegram] = useState<boolean | null>(null);
     const [isAuthenticated, setIsAuthenticated] = useState(false);

     useEffect(() => {
       // Check if running in Telegram
       const inTelegram = isTelegramWebApp();
       setIsInTelegram(inTelegram);

       if (inTelegram) {
         // Initialize Telegram WebApp
         initTelegramWebApp();

         // Authenticate with Telegram
         const initData = getTelegramInitData();
         if (initData) {
           authenticateWithTelegram(initData)
             .then(() => setIsAuthenticated(true))
             .catch(err => console.error('Auth failed:', err));
         }
       }
     }, []);

     // Show loading while checking
     if (isInTelegram === null) {
       return <div className="min-h-screen bg-[#130F30]" />;
     }

     // Show fallback if not in Telegram
     if (!isInTelegram) {
       return <TelegramFallback />;
     }

     // Original page content (existing code)
     // ...
   }
   ```

**Результат:** Фронтенд показывает fallback UI если открыт не в Telegram

### Модуль 6: Frontend Environment Variables

**Файлы:**
- `frontend_mini_app/.env.example`
- `docker-compose.yml`

**Действия:**
1. Обновить `.env.example` с комментариями для ngrok:
   ```bash
   # Backend API URL
   # Development (local): http://localhost:8000/api/v1
   # Development (ngrok): https://{ngrok-url}/api/v1
   # Production: https://lunchbot.vibe-labs.ru/api/v1
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

2. Обновить `docker-compose.yml` для динамической подстановки URL:
   ```yaml
   frontend:
     build:
       args:
         NEXT_PUBLIC_API_URL: ${FRONTEND_API_URL:-http://localhost/api/v1}
     environment:
       NEXT_PUBLIC_API_URL: ${FRONTEND_API_URL:-http://localhost/api/v1}
   ```

3. Создать файл `.env` в корне проекта (для docker-compose):
   ```bash
   # Development (через nginx)
   FRONTEND_API_URL=http://localhost/api/v1

   # Development (через ngrok)
   # FRONTEND_API_URL=https://{ngrok-url}/api/v1

   # Production
   # FRONTEND_API_URL=https://lunchbot.vibe-labs.ru/api/v1
   ```

**Результат:** Environment variables настроены для разных окружений

### Модуль 7: Documentation - Development Setup Guide

**Файлы:**
- `.memory-base/tech-docs/deployment.md` (уже существует, обновить)
- `README.md` (корневой, обновить)

**Действия:**
1. Обновить `deployment.md` секцию "Development with ngrok":
   ```markdown
   ## Development Setup (Telegram Mini App)

   ### HTTPS Tunnel с ngrok

   Telegram Mini Apps требуют HTTPS URL даже для development.

   1. Установить ngrok: https://ngrok.com/download
   2. Запустить проект: `docker-compose up`
   3. Открыть ngrok туннель: `ngrok http 80`
   4. Получить HTTPS URL: `https://xxxx.ngrok.io`
   5. Обновить `.env`:
      ```bash
      TELEGRAM_MINI_APP_URL=https://xxxx.ngrok.io
      FRONTEND_API_URL=https://xxxx.ngrok.io/api/v1
      CORS_ORIGINS=["http://localhost","https://xxxx.ngrok.io","https://web.telegram.org"]
      ```
   6. Перезапустить сервисы: `docker-compose restart backend telegram-bot frontend`
   7. Отправить `/order` боту - должно открыть Mini App

   ### Альтернатива: CloudFlare Tunnel
   ```bash
   cloudflared tunnel --url http://localhost:80
   ```
   ```

2. Обновить `README.md` с quick start инструкцией:
   ```markdown
   ## Quick Start (Telegram Mini App)

   1. Clone repo
   2. Setup environment:
      ```bash
      cp backend/.env.example backend/.env
      # Edit backend/.env - add TELEGRAM_BOT_TOKEN
      ```
   3. Start project:
      ```bash
      docker-compose up
      ```
   4. Setup ngrok (for Telegram Mini App):
      ```bash
      ngrok http 80
      # Update backend/.env with TELEGRAM_MINI_APP_URL=https://xxx.ngrok.io
      docker-compose restart backend telegram-bot
      ```
   5. Open Telegram bot and send `/order`
   ```

**Результат:** Документация обновлена для development setup

### Модуль 8: Testing Instructions

**Файлы:**
- `.memory-base/workflow/tasks/active/TSK-005/manual-testing-checklist.md` (новый файл)

**Действия:**
Создать файл `manual-testing-checklist.md` с чек-листом для тестирования:

```markdown
# TSK-005 Manual Testing Checklist

## Prerequisites
- [ ] ngrok установлен и запущен: `ngrok http 80`
- [ ] `TELEGRAM_MINI_APP_URL` обновлён в `backend/.env`
- [ ] Backend и telegram-bot перезапущены
- [ ] Telegram бот доступен в Telegram

## Test Cases

### 1. Menu Button Launch
- [ ] Открыть чат с ботом
- [ ] Нажать на Menu Button (слева от поля ввода)
- [ ] Mini App открывается в полноэкранном режиме
- [ ] Авторизация проходит автоматически
- [ ] Список кафе загружается

### 2. /order Command
- [ ] Отправить `/order` боту
- [ ] Получить сообщение с inline кнопкой "🍽 Заказать обед"
- [ ] Нажать на кнопку
- [ ] Mini App открывается
- [ ] Функционал работает

### 3. /start Command
- [ ] Отправить `/start` боту (или создать новый чат)
- [ ] Получить welcome сообщение с кнопкой Mini App
- [ ] Нажать на кнопку
- [ ] Mini App открывается

### 4. /help Command
- [ ] Отправить `/help` боту
- [ ] Получить список команд с упоминанием Mini App

### 5. Fallback UI (не в Telegram)
- [ ] Открыть `http://localhost` в браузере
- [ ] Увидеть fallback UI с инструкцией
- [ ] Проверить что список кафе НЕ загружается

### 6. Order Flow (E2E)
- [ ] Открыть Mini App через бота
- [ ] Выбрать кафе
- [ ] Выбрать комбо
- [ ] Заполнить все категории
- [ ] Добавить extras (опционально)
- [ ] Нажать "Оформить заказ"
- [ ] Получить подтверждение
- [ ] Проверить заказ в базе данных

### 7. Cross-Platform Testing
- [ ] iOS Telegram
- [ ] Android Telegram
- [ ] Desktop Telegram (Windows/macOS/Linux)
- [ ] Telegram Web (web.telegram.org)

## Known Issues
- Mini App не работает с `http://localhost` напрямую - нужен ngrok
- CORS может требовать добавления ngrok URL в `CORS_ORIGINS`
```

**Результат:** Чек-лист для ручного тестирования готов

## Execution Strategy

**Параллельное выполнение:**

Модули **1-4** (Backend & Bot) и Модули **5-6** (Frontend) **независимы** и могут выполняться **параллельно**:

**Параллельный блок 1 (Backend & Bot):**
- Модуль 1: Backend Environment & CORS
- Модуль 2: `/order` Command
- Модуль 3: Update `/start` and `/help`
- Модуль 4: Menu Button Configuration

**Параллельный блок 2 (Frontend):**
- Модуль 5: Telegram Check & Fallback UI
- Модуль 6: Frontend Environment Variables

**Последовательное выполнение:**
- Модуль 7: Documentation (после завершения блоков 1 и 2)
- Модуль 8: Testing Instructions (после завершения модуля 7)

**Рекомендация для Supervisor:**
1. Запустить **два параллельных Coder субагента**:
   - Coder 1: Модули 1-4 (Backend & Bot)
   - Coder 2: Модули 5-6 (Frontend)
2. После завершения обоих - запустить Coder для модулей 7-8 (Documentation)
3. После завершения всех модулей - запустить Tester для проверки

## Риски и зависимости

### Критические риски:
1. **HTTPS требование:** Telegram Mini Apps НЕ работают без HTTPS
   - **Решение:** Использовать ngrok для development
   - **Митигация:** Документировать setup process

2. **CORS для Telegram:** `https://web.telegram.org` должен быть в whitelist
   - **Решение:** Добавить в `CORS_ORIGINS`
   - **Митигация:** Тестировать на Telegram Web

3. **Bot API Menu Button:** Может не работать в старых версиях Telegram
   - **Решение:** Fallback на `/order` команду
   - **Митигация:** Документировать оба способа

### Зависимости:
- **ngrok:** Обязателен для development (нет альтернативы без публичного сервера)
- **TELEGRAM_BOT_TOKEN:** Должен быть валидным
- **Production server:** `172.25.0.200` должен быть доступен для deployment

### Эскалация:
Спросить человека если:
- ngrok URL недоступен или не работает
- CORS ошибки после добавления Telegram домена
- Menu Button не отображается в боте (может быть версия Telegram)
- Production deployment не удаётся из-за инфраструктуры

## Next Steps

После завершения архитектурной фазы:
1. **Coder (параллельно):**
   - Coder 1: Реализовать модули 1-4 (Backend & Bot)
   - Coder 2: Реализовать модули 5-6 (Frontend)
   - Coder 3: Реализовать модули 7-8 (Documentation)

2. **Reviewer:**
   - Проверить код на соответствие стандартам
   - Проверить безопасность (CORS, env vars)
   - Проверить документацию

3. **Tester:**
   - Выполнить manual testing checklist
   - E2E тест: `/order` → выбор кафе → заказ → подтверждение
   - Cross-platform тестирование

4. **DocWriter:**
   - Обновить tech docs с screenshots
   - Создать troubleshooting guide

## Summary

Задача TSK-005 разбита на **8 модулей**, из которых:
- **4 модуля** (Backend & Bot) - независимы и могут выполняться одним Coder
- **2 модуля** (Frontend) - независимы и могут выполняться другим Coder
- **2 модуля** (Documentation) - зависят от завершения предыдущих

**Общий timeline:**
1. Phase 1 (параллельно): Backend & Bot + Frontend (~2-3 часа)
2. Phase 2: Documentation (~1 час)
3. Phase 3: Testing & fixes (~2-3 часа)
4. Phase 4: Production deployment (~1-2 часа)

**Итого:** ~6-9 часов работы (с учётом тестирования и fixes)

**Критический путь:** HTTPS setup (ngrok) - без него ничего не работает.
