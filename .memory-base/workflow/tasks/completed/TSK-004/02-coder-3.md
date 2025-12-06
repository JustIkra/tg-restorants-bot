---
agent: coder
task_id: TSK-004
subtask: 3
subtask_name: "Docker Compose Frontend Integration"
status: completed
next: null
created_at: 2025-12-06T14:30:00
files_changed:
  - path: frontend_mini_app/Dockerfile
    action: created
  - path: frontend_mini_app/.dockerignore
    action: created
  - path: docker-compose.yml
    action: modified
---

## Результат

Успешно добавлена поддержка Frontend в Docker Compose для полной интеграции системы.

### Выполненные действия

#### 1. Создан `frontend_mini_app/Dockerfile`

Реализован multi-stage build для оптимизации размера образа:

**Builder stage:**
- Использует `node:20-alpine` как базовый образ
- Копирует `package*.json` и выполняет `npm ci` (чистая установка зависимостей)
- Копирует исходный код
- Принимает build argument `NEXT_PUBLIC_API_URL` для настройки API endpoint
- Выполняет `npm run build` для production сборки

**Production stage:**
- Использует минимальный `node:20-alpine` образ
- Копирует только необходимые файлы из builder stage:
  - `.next/` - собранное Next.js приложение
  - `node_modules/` - production зависимости
  - `package.json` - для запуска приложения
  - `public/` - статические файлы (изображения, иконки и т.д.)
- Открывает порт 3000
- Запускает приложение через `npm start` (production server)

**Особенности:**
- Multi-stage build значительно уменьшает размер финального образа
- Build-time переменная `NEXT_PUBLIC_API_URL` позволяет настраивать API endpoint при сборке
- Копирование `public/` директории обеспечивает доступность статических ресурсов

#### 2. Создан `frontend_mini_app/.dockerignore`

Добавлен `.dockerignore` для исключения ненужных файлов из Docker context:

**Исключенные файлы:**
- `node_modules` - будут установлены внутри контейнера
- `.next` - будет собран внутри контейнера
- `.git` - история Git не нужна в образе
- `.env.local`, `.env` - файлы с переменными окружения (secrets)
- `*.log` - лог файлы
- `.swc` - временные файлы компилятора
- `README.md`, `.gitignore`, `.dockerignore` - документация
- `tsconfig.tsbuildinfo` - временные файлы TypeScript
- `jest.config.js`, `jest.setup.js` - тестовая конфигурация

**Результат:** Ускорение сборки образа и уменьшение его размера за счет исключения ненужных файлов.

#### 3. Обновлен `docker-compose.yml`

**Добавлен frontend service:**

```yaml
frontend:
  build:
    context: ./frontend_mini_app
    dockerfile: Dockerfile
    args:
      NEXT_PUBLIC_API_URL: http://backend:8000/api/v1
  container_name: lunch-bot-frontend
  depends_on:
    - backend
  ports:
    - "3000:3000"
  environment:
    NEXT_PUBLIC_API_URL: http://backend:8000/api/v1
  volumes:
    - ./frontend_mini_app:/app
    - /app/node_modules
    - /app/.next
  networks:
    - lunch-bot-network
```

**Ключевые параметры:**
- `build.args.NEXT_PUBLIC_API_URL: http://backend:8000/api/v1` - использует Docker hostname `backend` для внутренней коммуникации
- `depends_on: backend` - гарантирует что backend стартует первым
- `ports: 3000:3000` - проксирует порт для доступа с хоста
- `volumes`:
  - `./frontend_mini_app:/app` - монтирует код для hot reload в dev режиме
  - `/app/node_modules` - предотвращает перезапись node_modules хоста
  - `/app/.next` - предотвращает перезапись собранных файлов
- `networks: lunch-bot-network` - подключен к общей сети с backend

**Добавлена сетевая изоляция:**

Все сервисы подключены к единой bridge сети `lunch-bot-network`:
- `postgres`
- `kafka`
- `redis`
- `backend`
- `frontend` ← новый
- `telegram-bot`
- `notifications-worker`
- `recommendations-worker`

**Определена сеть:**
```yaml
networks:
  lunch-bot-network:
    driver: bridge
```

**Обновлен CORS в backend:**
```yaml
CORS_ORIGINS: '["http://localhost:3000","http://frontend:3000"]'
```
Теперь backend принимает запросы как с хоста (`localhost:3000`), так и от Docker контейнера (`frontend:3000`).

### Технические детали

#### API URL для Docker

**Важно:** Внутри Docker Compose сервисы обращаются друг к другу по **имени контейнера как hostname**.

- **Внутри Docker:** `http://backend:8000/api/v1`
- **С хоста:** `http://localhost:8000/api/v1`

Frontend контейнер использует `http://backend:8000/api/v1`, так как он работает внутри Docker network.

#### Development vs Production

**Текущая конфигурация (Development):**
- Volumes монтируют код для hot reload
- `npm start` запускает production server, но можно изменить на `npm run dev` для development server с hot reload

**Для Production (в будущем):**
- Убрать volumes для кода (использовать только образ)
- Использовать `npm start` (production server)
- Настроить `NEXT_PUBLIC_API_URL` на production домен через `.env.production`

#### Health Checks

Frontend пока не имеет health check. Можно добавить в будущем:
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Проверка работоспособности

Для проверки интеграции:

```bash
# Собрать и запустить все сервисы
docker-compose up -d --build

# Проверить логи frontend
docker logs lunch-bot-frontend

# Проверить доступность
curl http://localhost:3000

# Проверить что frontend может обратиться к backend (из контейнера)
docker exec lunch-bot-frontend wget -O- http://backend:8000/health
```

### Следующие шаги

После запуска Docker Compose:

1. **Frontend → Backend интеграция (Subtask 1.1):**
   - Заменить mock данные в `page.tsx` на реальные API calls
   - Использовать SWR hooks для data fetching

2. **Тестирование:**
   - Проверить что Telegram Mini App открывается
   - Проверить авторизацию через Telegram WebApp
   - Проверить создание заказа через UI

3. **E2E Testing (Phase 2):**
   - Настроить Playwright для тестирования против Docker Compose окружения
   - Создать test plan
   - Сгенерировать автотесты

### Файлы

**Созданные:**
- `/Users/maksim/git_projects/tg_bot/frontend_mini_app/Dockerfile`
- `/Users/maksim/git_projects/tg_bot/frontend_mini_app/.dockerignore`

**Изменённые:**
- `/Users/maksim/git_projects/tg_bot/docker-compose.yml`
  - Добавлен `frontend` service
  - Добавлена сеть `lunch-bot-network`
  - Все сервисы подключены к единой сети
  - Обновлен `CORS_ORIGINS` в backend для поддержки Docker hostname

### Важные замечания

1. **API URL конфигурация:**
   - Для Docker используется `http://backend:8000` (hostname сервиса)
   - Для локальной разработки вне Docker используется `http://localhost:8000`

2. **Volumes для development:**
   - Текущая конфигурация монтирует код для удобства разработки
   - В production рекомендуется убрать volumes и использовать только собранный образ

3. **Network isolation:**
   - Все сервисы в единой сети `lunch-bot-network`
   - Обеспечивает безопасную внутреннюю коммуникацию
   - Сервисы доступны друг другу по имени контейнера

4. **Public directory:**
   - Копируется в Dockerfile для доступности статических файлов (favicon, изображения)
   - Если добавляются новые статические файлы, они будут доступны после пересборки образа

5. **Multi-stage build преимущества:**
   - Уменьшенный размер образа (не содержит dev dependencies и исходники)
   - Быстрая сборка при изменениях (кэширование слоев)
   - Оптимизация для production

## Исправления по review

### Issue #4 - Docker dev mode

**Проблема:** Dockerfile использует production build (`npm run build`), но volumes монтируют код для hot reload. При этом запускается `npm start` (production server), что несовместимо с dev режимом.

**Решение:** Добавлен `command: npm run dev` в `docker-compose.yml` для frontend service.

**Файл:** `/Users/maksim/git_projects/tg_bot/docker-compose.yml`

**Изменения:**
```yaml
frontend:
  # ... existing config ...
  command: npm run dev  # ← Добавлено для development режима с hot reload
  volumes:
    - ./frontend_mini_app:/app
    - /app/node_modules
    - /app/.next
```

**Результат:**
- В development режиме (Docker Compose): используется `npm run dev` с hot reload
- Volumes корректно работают с dev сервером
- При изменении кода изменения автоматически применяются без пересборки образа

**Замечание для production:**
Для production окружения рекомендуется:
- Убрать `command: npm run dev` (использовать CMD из Dockerfile: `npm start`)
- Убрать volumes для кода
- Использовать только собранный образ

## Статус

✅ **Завершено успешно** (с исправлениями по review)

Все файлы созданы и настроены корректно. Issue #4 исправлен - добавлен `npm run dev` для development режима. Frontend готов к интеграции с backend через Docker Compose.
