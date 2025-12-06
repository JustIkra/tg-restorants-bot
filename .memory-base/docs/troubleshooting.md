# Troubleshooting Guide

Руководство по решению типичных проблем Lunch Order Bot.

## Оглавление

1. [Frontend проблемы](#frontend-проблемы)
2. [Backend проблемы](#backend-проблемы)
3. [Database проблемы](#database-проблемы)
4. [Kafka проблемы](#kafka-проблемы)
5. [Redis проблемы](#redis-проблемы)
6. [Telegram Bot проблемы](#telegram-bot-проблемы)
7. [Gemini API проблемы](#gemini-api-проблемы)
8. [Docker проблемы](#docker-проблемы)

---

## Frontend проблемы

### Frontend не подключается к Backend (CORS ошибка)

**Симптомы:**
- В консоли браузера: `Access-Control-Allow-Origin` ошибка
- API запросы блокируются
- Network tab показывает статус `(failed)` или `(blocked:cors)`

**Решение:**
1. Проверить `CORS_ORIGINS` в `backend/.env`:
   ```bash
   CORS_ORIGINS=["http://localhost","http://localhost:80","https://lunchbot.vibe-labs.ru","https://web.telegram.org"]
   ```
2. Убедиться что URL фронтенда добавлен в массив
3. Перезапустить backend:
   ```bash
   docker restart lunch-bot-backend
   ```

**Важно:** CORS_ORIGINS должен быть валидным JSON массивом строк.

### Пустой экран в Mini App

**Симптомы:**
- Белый экран при открытии в Telegram
- Нет ошибок в консоли или "Failed to load resource"

**Решение:**
1. Проверить `NEXT_PUBLIC_API_URL` в `frontend_mini_app/.env`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost/api/v1
   ```
2. Проверить что backend доступен:
   ```bash
   curl http://localhost/api/v1/health
   ```
   Ожидаемый ответ: `{"status":"ok"}`

3. Проверить логи frontend:
   ```bash
   docker logs lunch-bot-frontend
   ```
4. Проверить что Nginx проксирует запросы (см. `nginx/nginx.conf`)

### Telegram WebApp SDK не инициализируется

**Симптомы:**
- `window.Telegram.WebApp` is undefined
- Не работает авторизация

**Решение:**
1. Проверить что скрипт загружается в `<head>`:
   ```html
   <script src="https://telegram.org/js/telegram-web-app.js"></script>
   ```
2. Открыть Mini App **через Telegram**, не через браузер напрямую
3. Для локальной разработки использовать ngrok/tunneling:
   ```bash
   ngrok http 80
   ```

### Build ошибки при `npm run build`

**Симптомы:**
- TypeScript errors при сборке
- "Module not found" ошибки

**Решение:**
1. Очистить кэш и пересобрать:
   ```bash
   docker exec lunch-bot-frontend rm -rf .next node_modules
   docker exec lunch-bot-frontend npm install
   docker restart lunch-bot-frontend
   ```

2. Проверить версии зависимостей в `package.json`
3. Проверить что все импорты корректны

---

## Backend проблемы

### API возвращает 500 Internal Server Error

**Симптомы:**
- Любой endpoint возвращает 500
- В Swagger UI ошибка при попытке запроса

**Диагностика:**
```bash
docker logs lunch-bot-backend --tail 100
```

**Частые причины:**
1. **База данных недоступна** → проверить PostgreSQL:
   ```bash
   docker exec lunch-bot-postgres pg_isready
   ```

2. **Неверные переменные окружения**:
   ```bash
   docker exec lunch-bot-backend env | grep -E "DATABASE_URL|REDIS_URL|KAFKA_BROKER_URL"
   ```

3. **Ошибка в миграциях**:
   ```bash
   docker exec lunch-bot-backend alembic current
   docker exec lunch-bot-backend alembic upgrade head
   ```

4. **Не хватает JWT_SECRET_KEY** или он слишком короткий (<32 символов)

### JWT токен не валидируется (401 Unauthorized)

**Симптомы:**
- 401 Unauthorized на защищенные endpoints
- `{"detail":"Could not validate credentials"}`

**Решение:**
1. Проверить `JWT_SECRET_KEY` одинаков во всех сервисах:
   ```bash
   docker exec lunch-bot-backend printenv JWT_SECRET_KEY
   docker exec lunch-bot-telegram printenv JWT_SECRET_KEY
   ```

2. Проверить `JWT_EXPIRE_DAYS` не слишком маленький (default: 7)

3. Очистить токен в клиенте и перелогиниться через `/auth/telegram`

4. Проверить формат токена в header:
   ```
   Authorization: Bearer <token>
   ```

### Telegram авторизация не работает (POST /auth/telegram → 400)

**Симптомы:**
- `{"detail":"Invalid Telegram data"}`
- Авторизация через Mini App не проходит

**Решение:**
1. Проверить что `initData` передается от Telegram WebApp SDK:
   ```javascript
   const initData = window.Telegram.WebApp.initData
   ```

2. Проверить что `TELEGRAM_BOT_TOKEN` совпадает с токеном бота в BotFather

3. Проверить срок действия `initData` (не более 24 часов)

4. В локальной разработке использовать моковый `initData` (см. документацию)

### Миграции Alembic не применяются

**Симптомы:**
- `sqlalchemy.exc.ProgrammingError: relation "users" does not exist`
- Таблицы не созданы в БД

**Диагностика:**
```bash
# Проверить текущую ревизию
docker exec lunch-bot-backend alembic current

# Проверить историю миграций
docker exec lunch-bot-backend alembic history
```

**Решение:**
```bash
# Применить все миграции
docker exec lunch-bot-backend alembic upgrade head

# Если ошибка - downgrade и повторить
docker exec lunch-bot-backend alembic downgrade -1
docker exec lunch-bot-backend alembic upgrade head
```

**Создать новую миграцию:**
```bash
docker exec lunch-bot-backend alembic revision --autogenerate -m "description"
```

---

## Database проблемы

### PostgreSQL не запускается

**Симптомы:**
- Контейнер `lunch-bot-postgres` постоянно рестартится
- `connection refused` ошибки в backend
- Backend не может подключиться к БД

**Диагностика:**
```bash
docker logs lunch-bot-postgres --tail 50
docker exec lunch-bot-postgres pg_isready
```

**Решения:**

1. **Недостаточно места на диске:**
   ```bash
   df -h
   # Если мало места - очистить Docker
   docker system prune -a --volumes
   ```

2. **Неверные credentials:**
   Проверить `docker-compose.yml`:
   ```yaml
   POSTGRES_USER: postgres
   POSTGRES_PASSWORD: password
   POSTGRES_DB: lunch_bot
   ```

3. **Поврежденный volume:**
   ```bash
   docker-compose down -v
   docker volume rm tg_bot_postgres_data
   docker-compose up -d postgres
   ```
   **Внимание:** Это удалит все данные!

4. **Права на volume:**
   ```bash
   docker volume inspect tg_bot_postgres_data
   ```

### Медленные запросы в БД

**Симптомы:**
- API endpoints отвечают медленно
- Таймауты на запросы

**Диагностика:**
```sql
-- Подключиться к БД
docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot

-- Проверить медленные запросы
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Проверить индексы
\di
```

**Решение:**

1. **Добавить индексы** (должны быть в миграциях):
   ```sql
   CREATE INDEX idx_orders_user_date ON orders(user_tgid, order_date);
   CREATE INDEX idx_orders_cafe_date ON orders(cafe_id, order_date);
   CREATE INDEX idx_menu_items_cafe_category ON menu_items(cafe_id, category);
   ```

2. **Проверить connection pooling** в SQLAlchemy:
   ```python
   # backend/src/database.py
   engine = create_async_engine(
       settings.DATABASE_URL,
       pool_size=10,
       max_overflow=20
   )
   ```

3. **Vacuum и analyze:**
   ```bash
   docker exec lunch-bot-postgres vacuumdb -U postgres -d lunch_bot -z
   ```

### Ошибка подключения: "too many connections"

**Симптомы:**
- `FATAL: sorry, too many clients already`

**Решение:**
1. Проверить количество подключений:
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

2. Перезапустить сервисы для сброса пула:
   ```bash
   docker-compose restart backend notifications-worker recommendations-worker
   ```

3. Увеличить `max_connections` в PostgreSQL (если нужно):
   ```bash
   # В docker-compose.yml добавить
   command: postgres -c max_connections=200
   ```

---

## Kafka проблемы

### Kafka не стартует

**Симптомы:**
- `Connection refused` к порту `29092`
- Workers не получают события
- Healthcheck фейлится

**Диагностика:**
```bash
docker logs lunch-bot-kafka --tail 100

# Проверить что Kafka слушает порт
docker exec lunch-bot-kafka kafka-broker-api-versions --bootstrap-server localhost:29092
```

**Решения:**

1. **Недостаточно памяти:**
   Увеличить memory limit в `docker-compose.yml`:
   ```yaml
   kafka:
     deploy:
       resources:
         limits:
           memory: 2G
   ```

2. **Порт 9092/29092 занят:**
   ```bash
   lsof -i :29092
   # Убить процесс или изменить порт
   ```

3. **Cluster ID конфликт:**
   ```bash
   docker-compose down -v
   docker volume rm tg_bot_kafka_data
   docker-compose up -d kafka
   ```

4. **Kafka Controller не готов:**
   Подождать 30-60 секунд после запуска

### Topics не создаются автоматически

**Симптомы:**
- События не отправляются/не обрабатываются
- `UNKNOWN_TOPIC_OR_PARTITION` ошибки

**Решение:**

Создать topics вручную:
```bash
docker exec lunch-bot-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create \
  --topic order.deadline.passed \
  --partitions 3 \
  --replication-factor 1

docker exec lunch-bot-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create \
  --topic recommendations.generate \
  --partitions 1 \
  --replication-factor 1
```

Проверить созданные topics:
```bash
docker exec lunch-bot-kafka kafka-topics --bootstrap-server localhost:29092 --list
```

### Уведомления не отправляются в кафе

**Симптомы:**
- Кафе не получает заказы после deadline
- События есть в Kafka, но не обрабатываются

**Диагностика:**
```bash
# Проверить notifications worker
docker logs lunch-bot-notifications-worker --tail 100

# Проверить consumer group lag
docker exec lunch-bot-kafka kafka-consumer-groups \
  --bootstrap-server localhost:29092 \
  --group notifications-worker \
  --describe
```

**Решение:**

1. Проверить что worker запущен:
   ```bash
   docker ps | grep notifications-worker
   ```

2. Проверить события в topic:
   ```bash
   docker exec lunch-bot-kafka kafka-console-consumer \
     --bootstrap-server localhost:29092 \
     --topic order.deadline.passed \
     --from-beginning \
     --max-messages 10
   ```

3. Перезапустить worker:
   ```bash
   docker restart lunch-bot-notifications-worker
   ```

4. Проверить что у кафе есть `tg_chat_id` и `notifications_enabled=true`

---

## Redis проблемы

### Redis недоступен

**Симптомы:**
- Рекомендации не кэшируются
- `Connection refused` в логах backend/workers
- Health check `/health/redis` возвращает 503

**Диагностика:**
```bash
docker logs lunch-bot-redis --tail 50
docker exec lunch-bot-redis redis-cli ping
```

**Решение:**

1. Перезапустить Redis:
   ```bash
   docker restart lunch-bot-redis
   ```

2. Проверить volume:
   ```bash
   docker volume inspect tg_bot_redis_data
   ```

3. Проверить `REDIS_URL` в сервисах:
   ```bash
   docker exec lunch-bot-backend printenv REDIS_URL
   # Должно быть: redis://redis:6379
   ```

### Кэш переполнен (OOM)

**Симптомы:**
- Redis использует слишком много памяти
- `OOM command not allowed when used memory > 'maxmemory'`

**Диагностика:**
```bash
docker exec lunch-bot-redis redis-cli INFO memory
```

**Решение:**

1. Очистить устаревшие ключи:
   ```bash
   # Проверить количество ключей
   docker exec lunch-bot-redis redis-cli DBSIZE

   # Посмотреть ключи (осторожно, может быть много)
   docker exec lunch-bot-redis redis-cli --scan --pattern "recommendations:*"

   # Очистить БД (ОСТОРОЖНО! Удалит все данные)
   docker exec lunch-bot-redis redis-cli FLUSHDB
   ```

2. Настроить eviction policy:
   ```bash
   docker exec lunch-bot-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
   docker exec lunch-bot-redis redis-cli CONFIG SET maxmemory 256mb
   ```

3. Увеличить память для Redis в `docker-compose.yml`:
   ```yaml
   redis:
     deploy:
       resources:
         limits:
           memory: 512M
   ```

### Gemini API счетчики не работают

**Симптомы:**
- Все запросы идут на один ключ
- Ротация ключей не происходит

**Диагностика:**
```bash
# Проверить счетчики в Redis
docker exec lunch-bot-redis redis-cli KEYS "gemini:*"
docker exec lunch-bot-redis redis-cli GET "gemini:key:0:count"
```

**Решение:**

1. Сбросить счетчики:
   ```bash
   docker exec lunch-bot-redis redis-cli DEL "gemini:key:0:count"
   docker exec lunch-bot-redis redis-cli DEL "gemini:current_key_index"
   ```

2. Проверить TTL (должен сброситься в полночь):
   ```bash
   docker exec lunch-bot-redis redis-cli TTL "gemini:key:0:count"
   ```

3. Перезапустить recommendations worker:
   ```bash
   docker restart lunch-bot-recommendations-worker
   ```

---

## Telegram Bot проблемы

### Telegram Bot не отвечает

**Симптомы:**
- Бот не реагирует на команды
- `/start` не работает

**Диагностика:**
```bash
docker logs lunch-bot-telegram --tail 100
```

**Решение:**

1. Проверить что контейнер запущен:
   ```bash
   docker ps | grep telegram
   ```

2. Проверить `TELEGRAM_BOT_TOKEN`:
   ```bash
   docker exec lunch-bot-telegram printenv TELEGRAM_BOT_TOKEN
   ```

3. Проверить токен в BotFather (`/token`)

4. Перезапустить бота:
   ```bash
   docker restart lunch-bot-telegram
   ```

5. Проверить что webhook не установлен (polling mode):
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
   # Должно быть: "url": ""
   ```

### Кафе не может подключиться (/start в боте)

**Симптомы:**
- После `/start` бот не просит выбрать кафе
- Inline кнопки не появляются

**Решение:**

1. Проверить что есть активные кафе в БД:
   ```sql
   docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot -c "SELECT id, name, is_active FROM cafes;"
   ```

2. Проверить логи бота:
   ```bash
   docker logs lunch-bot-telegram | grep "cafes"
   ```

3. Проверить что бот может достучаться до backend API:
   ```bash
   docker exec lunch-bot-telegram curl http://backend:8000/api/v1/cafes
   ```

### Уведомления кафе не форматируются (Markdown)

**Симптомы:**
- Уведомление приходит как plain text
- `*bold*` не работает

**Решение:**

1. Проверить `parse_mode='Markdown'` в коде:
   ```python
   await bot.send_message(chat_id, text, parse_mode='Markdown')
   ```

2. Проверить экранирование спецсимволов:
   ```
   Не `_text_`, а `\_text\_` для Markdown v1
   ```

3. Использовать MarkdownV2 или HTML:
   ```python
   parse_mode='HTML'
   # <b>bold</b>, <i>italic</i>
   ```

---

## Gemini API проблемы

### 429 Too Many Requests (Rate limit)

**Симптомы:**
- `google.api_core.exceptions.ResourceExhausted`
- Рекомендации не генерируются

**Диагностика:**
```bash
docker logs lunch-bot-recommendations-worker | grep "429\|ResourceExhausted"
```

**Решение:**

1. Проверить счетчик запросов в Redis:
   ```bash
   docker exec lunch-bot-redis redis-cli GET "gemini:key:0:count"
   ```

2. Убедиться что ротация работает (должна переключаться на следующий ключ после 195 запросов)

3. Добавить больше ключей в `GEMINI_API_KEYS`:
   ```bash
   GEMINI_API_KEYS=key1,key2,key3,key4
   ```

4. Увеличить `GEMINI_MAX_REQUESTS_PER_KEY` (default: 195):
   ```bash
   GEMINI_MAX_REQUESTS_PER_KEY=180  # Оставить запас
   ```

5. Подождать сброса лимита (счетчики сбрасываются в полночь UTC)

### 401 Unauthorized (Invalid API key)

**Симптомы:**
- `google.api_core.exceptions.Unauthenticated`
- Все ключи возвращают 401

**Решение:**

1. Проверить что ключи валидны:
   ```bash
   # Проверить в Google AI Studio
   curl -H "x-goog-api-key: YOUR_KEY" \
     https://generativelanguage.googleapis.com/v1beta/models
   ```

2. Убедиться что Gemini API включен в Google Cloud Console

3. Проверить что ключи не просрочены

4. Обновить ключи в `.env`:
   ```bash
   GEMINI_API_KEYS=new_key1,new_key2
   ```

5. Перезапустить worker:
   ```bash
   docker restart lunch-bot-recommendations-worker
   ```

### Рекомендации не генерируются

**Симптомы:**
- `/users/{tgid}/recommendations` возвращает пустые tips
- Worker работает, но ничего не создает

**Диагностика:**
```bash
docker logs lunch-bot-recommendations-worker --tail 200
```

**Возможные причины:**

1. **Недостаточно заказов** (минимум 5 за 30 дней):
   ```sql
   SELECT user_tgid, COUNT(*) as orders_count
   FROM orders
   WHERE created_at > NOW() - INTERVAL '30 days'
   GROUP BY user_tgid
   HAVING COUNT(*) < 5;
   ```

2. **Batch job не запускается** (должен быть ночью):
   Проверить APScheduler в логах:
   ```bash
   docker logs lunch-bot-recommendations-worker | grep "scheduler\|batch"
   ```

3. **Redis кэш пустой**:
   ```bash
   docker exec lunch-bot-redis redis-cli KEYS "recommendations:*"
   ```

4. Вручную запустить генерацию для пользователя:
   ```bash
   # Отправить Kafka событие
   docker exec lunch-bot-kafka kafka-console-producer \
     --bootstrap-server localhost:29092 \
     --topic recommendations.generate
   # Ввести: {"user_tgid": 123456789}
   ```

---

## Docker проблемы

### Контейнеры не стартуют

**Симптомы:**
- `docker-compose up` зависает
- Сервисы в состоянии `Restarting`

**Диагностика:**
```bash
docker-compose ps
docker-compose logs
```

**Решения:**

1. **Очистить и пересобрать:**
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Проверить ресурсы системы:**
   ```bash
   docker system df
   # Очистить неиспользуемые ресурсы
   docker system prune -a
   ```

3. **Проверить Docker Daemon:**
   ```bash
   docker info
   # Перезапустить Docker Desktop / dockerd
   ```

4. **Проверить зависимости сервисов:**
   ```yaml
   # В docker-compose.yml
   depends_on:
     postgres:
       condition: service_healthy  # Проверить что healthcheck работает
   ```

### Port already in use

**Симптомы:**
- `bind: address already in use`
- Nginx не может стартовать на порту 80

**Решение:**

1. Найти процесс:
   ```bash
   # macOS/Linux
   lsof -i :80
   sudo lsof -i :80

   # Linux альтернатива
   netstat -tulpn | grep :80
   ```

2. Убить процесс:
   ```bash
   kill -9 <PID>
   ```

3. Или изменить порт в `docker-compose.yml`:
   ```yaml
   nginx:
     ports:
       - "8080:80"  # Использовать 8080 вместо 80
   ```

### Volumes не обновляются (код не меняется)

**Симптомы:**
- Изменения в коде не отражаются в контейнере
- Hot reload не работает

**Решение:**

1. **Для backend** (Python):
   ```bash
   docker restart lunch-bot-backend
   ```

2. **Для frontend** (Next.js):
   ```bash
   docker exec lunch-bot-frontend rm -rf .next
   docker restart lunch-bot-frontend
   ```

3. Проверить volume mounts в `docker-compose.yml`:
   ```yaml
   volumes:
     - ./backend:/app  # Должен быть актуальный путь
   ```

4. Пересоздать контейнеры:
   ```bash
   docker-compose up -d --force-recreate
   ```

### Ошибки сборки образов

**Симптомы:**
- `docker-compose build` фейлится
- `ERROR [internal] load metadata for...`

**Решение:**

1. Очистить build cache:
   ```bash
   docker builder prune -a
   ```

2. Проверить Dockerfile:
   ```bash
   docker build -t test ./backend
   ```

3. Проверить `.dockerignore`:
   ```
   # Должны быть исключены:
   .env
   __pycache__
   .venv
   node_modules
   .next
   ```

4. Проверить доступ к базовым образам:
   ```bash
   docker pull python:3.13-slim
   docker pull node:20-alpine
   ```

### Недостаточно места на диске

**Симптомы:**
- `no space left on device`
- Контейнеры не могут записывать данные

**Решение:**

1. Проверить использование диска:
   ```bash
   df -h
   docker system df
   ```

2. Очистить неиспользуемые ресурсы:
   ```bash
   # Удалить остановленные контейнеры
   docker container prune

   # Удалить неиспользуемые образы
   docker image prune -a

   # Удалить неиспользуемые volumes
   docker volume prune

   # Очистить всё (ОСТОРОЖНО!)
   docker system prune -a --volumes
   ```

3. Удалить старые volumes вручную:
   ```bash
   docker volume ls
   docker volume rm <volume_name>
   ```

---

## Health Check команды

### Проверить все сервисы сразу

```bash
# Статус всех сервисов (backend health endpoint)
curl http://localhost/api/v1/health/all

# Статус контейнеров
docker-compose ps

# Статус Docker containers
docker ps --filter "name=lunch-bot"
```

### Проверить отдельные компоненты

```bash
# Backend API
curl http://localhost/api/v1/health
# Ожидается: {"status":"ok"}

# PostgreSQL
curl http://localhost/api/v1/health/db
# Ожидается: {"status":"ok","service":"postgresql"}

# Redis
curl http://localhost/api/v1/health/redis
# Ожидается: {"status":"ok","service":"redis"}

# PostgreSQL (напрямую)
docker exec lunch-bot-postgres pg_isready -U postgres

# Redis (напрямую)
docker exec lunch-bot-redis redis-cli ping

# Kafka (напрямую)
docker exec lunch-bot-kafka kafka-broker-api-versions --bootstrap-server localhost:29092
```

### Проверить логи

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker logs -f lunch-bot-backend
docker logs -f lunch-bot-frontend
docker logs -f lunch-bot-postgres
docker logs -f lunch-bot-kafka
docker logs -f lunch-bot-redis
docker logs -f lunch-bot-telegram
docker logs -f lunch-bot-notifications-worker
docker logs -f lunch-bot-recommendations-worker

# Последние N строк
docker logs lunch-bot-backend --tail 100

# Логи с timestamp
docker logs lunch-bot-backend --timestamps
```

---

## Полезные команды

### Docker Compose

```bash
# Запустить все сервисы
docker-compose up -d

# Остановить все сервисы
docker-compose down

# Остановить и удалить volumes (УДАЛИТ ДАННЫЕ!)
docker-compose down -v

# Пересобрать образы
docker-compose build --no-cache

# Перезапустить сервис
docker-compose restart backend

# Посмотреть логи
docker-compose logs -f

# Посмотреть статус
docker-compose ps
```

### Работа с контейнерами

```bash
# Войти в контейнер
docker exec -it lunch-bot-backend bash
docker exec -it lunch-bot-postgres bash

# Выполнить команду
docker exec lunch-bot-backend python -m pytest
docker exec lunch-bot-backend alembic upgrade head

# Копировать файлы
docker cp lunch-bot-backend:/app/logs.txt ./logs.txt
docker cp ./file.txt lunch-bot-backend:/app/
```

### База данных

```bash
# Подключиться к PostgreSQL
docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot

# Выполнить SQL
docker exec lunch-bot-postgres psql -U postgres -d lunch_bot -c "SELECT COUNT(*) FROM users;"

# Сделать backup
docker exec lunch-bot-postgres pg_dump -U postgres lunch_bot > backup.sql

# Восстановить backup
docker exec -i lunch-bot-postgres psql -U postgres lunch_bot < backup.sql

# Vacuum база
docker exec lunch-bot-postgres vacuumdb -U postgres -d lunch_bot -z
```

### Kafka

```bash
# Список topics
docker exec lunch-bot-kafka kafka-topics --bootstrap-server localhost:29092 --list

# Создать topic
docker exec lunch-bot-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic test-topic \
  --partitions 1 --replication-factor 1

# Удалить topic
docker exec lunch-bot-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --delete --topic test-topic

# Читать сообщения
docker exec lunch-bot-kafka kafka-console-consumer \
  --bootstrap-server localhost:29092 \
  --topic order.deadline.passed \
  --from-beginning

# Отправить сообщение
docker exec -it lunch-bot-kafka kafka-console-producer \
  --bootstrap-server localhost:29092 \
  --topic order.deadline.passed
```

### Redis

```bash
# Redis CLI
docker exec -it lunch-bot-redis redis-cli

# Список ключей
docker exec lunch-bot-redis redis-cli KEYS "*"

# Получить значение
docker exec lunch-bot-redis redis-cli GET "recommendations:123456789"

# Удалить ключ
docker exec lunch-bot-redis redis-cli DEL "key"

# Очистить всё (ОСТОРОЖНО!)
docker exec lunch-bot-redis redis-cli FLUSHALL

# Информация о памяти
docker exec lunch-bot-redis redis-cli INFO memory
```

### Очистка Docker

```bash
# Остановить все контейнеры
docker stop $(docker ps -aq)

# Удалить все контейнеры
docker rm $(docker ps -aq)

# Удалить неиспользуемые образы
docker image prune -a

# Удалить неиспользуемые volumes
docker volume prune

# Очистить всё
docker system prune -a --volumes
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Конкретный контейнер
docker stats lunch-bot-backend

# Использование диска
docker system df

# Детальная информация
docker system df -v
```

---

## Debug Workflow

Когда что-то не работает, следуйте этому чек-листу:

### 1. Проверить статус контейнеров
```bash
docker-compose ps
# Все должны быть "Up" и "healthy"
```

### 2. Проверить health endpoints
```bash
curl http://localhost/api/v1/health/all
# Должно вернуть 200 OK
```

### 3. Проверить логи
```bash
docker-compose logs -f
# Искать ERROR, CRITICAL, Exception
```

### 4. Проверить переменные окружения
```bash
docker exec lunch-bot-backend env | grep -E "DATABASE_URL|REDIS_URL|KAFKA"
```

### 5. Проверить сетевое подключение
```bash
docker network ls
docker network inspect tg_bot_lunch-bot-network
```

### 6. Тестовый запрос к API
```bash
curl -X GET http://localhost/api/v1/health
curl -X GET http://localhost/api/v1/cafes
```

### 7. Перезапустить проблемный сервис
```bash
docker restart lunch-bot-<service>
```

### 8. Полный перезапуск (если ничего не помогло)
```bash
docker-compose down
docker-compose up -d
```

---

## Связаться с поддержкой

Если проблема не решается после выполнения инструкций:

### 1. Собрать информацию

```bash
# Логи всех сервисов
docker-compose logs > logs.txt

# Статус системы
docker-compose ps > status.txt
docker system df >> status.txt
docker network ls >> status.txt

# Информация о среде
echo "OS: $(uname -a)" > env.txt
echo "Docker: $(docker --version)" >> env.txt
docker-compose --version >> env.txt
```

### 2. Описать проблему

Включите в отчет:
- **Симптомы:** Что именно не работает?
- **Шаги воспроизведения:** Как воспроизвести проблему?
- **Логи:** Прикрепите `logs.txt`, `status.txt`, `env.txt`
- **Версии:** Docker, docker-compose, OS
- **Изменения:** Что делали перед появлением проблемы?

### 3. Контакты

- GitHub Issues: `https://github.com/your-repo/issues`
- Email: `support@example.com`
- Telegram: `@support_bot`

---

## Дополнительные ресурсы

- **Документация проекта:** `.memory-base/index.md`
- **API документация:** `http://localhost/api/v1/docs` (Swagger UI)
- **Deployment guide:** `.memory-base/docs/deployment/`
- **Architecture:** `.memory-base/tech-docs/image.png`
- **Docker Compose reference:** `https://docs.docker.com/compose/`
- **FastAPI docs:** `https://fastapi.tiangolo.com/`
- **Next.js docs:** `https://nextjs.org/docs`
