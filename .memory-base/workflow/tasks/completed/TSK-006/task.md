---
id: TSK-006
title: "Настройка Nginx reverse proxy для единого входного порта"
pipeline: feature
status: pending
created_at: 2025-12-06T12:00:00
related_files:
  - docker-compose.yml
  - nginx/nginx.conf (будет создан)
impact:
  api: false
  db: false
  frontend: false
  services: true
  deployment: true
---

## Описание

Настроить Nginx в качестве reverse proxy для объединения всех публичных сервисов под одним доменом и портом. Вместо нескольких открытых портов (3000, 8000, 5432, 9092, 6379) будет один входной порт 80/443 для всех HTTP-сервисов.

## Проблема

Сейчас в docker-compose.yml открыто множество портов:
- **3000** - Frontend (Telegram Mini App)
- **8000** - Backend API
- **5432** - PostgreSQL (не должен быть публичным!)
- **9092** - Kafka (не должен быть публичным!)
- **6379** - Redis (не должен быть публичным!)

Это создаёт проблемы:
1. Нужно настраивать DNS для каждого порта отдельно
2. Базы данных и Kafka доступны извне (угроза безопасности)
3. Сложно использовать HTTPS (нужны сертификаты для каждого порта)
4. Нет единой точки входа для логирования и мониторинга

## Решение

Добавить Nginx как reverse proxy:

```
Internet → nginx:80/443
              ↓
    ┌─────────┴──────────┐
    ▼                    ▼
frontend:3000      backend:8000
```

**Nginx будет роутить:**
- `/` → frontend:3000 (Telegram Mini App)
- `/api/` → backend:8000 (Backend API)
- `/docs`, `/openapi.json` → backend:8000 (Swagger UI)

**Внутренние сервисы (БЕЗ публичных портов):**
- PostgreSQL:5432 - только внутри Docker network
- Kafka:29092 - только внутри Docker network
- Redis:6379 - только внутри Docker network

## Acceptance Criteria

### 1. Nginx конфигурация
- [ ] Создана директория `nginx/`
- [ ] Создан `nginx/nginx.conf` с маршрутизацией:
  - `/` → `http://frontend:3000`
  - `/api/` → `http://backend:8000/api/`
  - `/docs` → `http://backend:8000/docs`
  - `/openapi.json` → `http://backend:8000/openapi.json`
- [ ] Настроен proxy_pass с правильными заголовками (X-Real-IP, X-Forwarded-For, Host)
- [ ] WebSocket support для Telegram Mini App (если нужно)
- [ ] CORS headers проксируются корректно
- [ ] Client max body size настроен (для загрузки файлов)

### 2. Docker Compose обновлён
- [ ] Добавлен сервис `nginx`:
  - Образ: `nginx:alpine`
  - Порты: `80:80` (единственный публичный порт)
  - Volumes: `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`
  - Depends on: frontend, backend
  - Networks: lunch-bot-network
- [ ] Удалены публичные порты из:
  - `postgres` (убрать `5432:5432`)
  - `kafka` (убрать `9092:9092`)
  - `redis` (убрать `6379:6379`)
  - `backend` (убрать `8000:8000`)
  - `frontend` (убрать `3000:3000`)
- [ ] Health check для nginx

### 3. Безопасность
- [ ] PostgreSQL, Kafka, Redis доступны ТОЛЬКО внутри Docker network
- [ ] Backend и Frontend доступны ТОЛЬКО через nginx
- [ ] Nginx логирует все входящие запросы
- [ ] Rate limiting настроен (опционально, можно отложить)

### 4. Тестирование
- [ ] `docker-compose up` поднимает все сервисы включая nginx
- [ ] `curl http://localhost/` возвращает Frontend
- [ ] `curl http://localhost/api/health` возвращает Backend health
- [ ] `curl http://localhost/docs` возвращает Swagger UI
- [ ] Прямой доступ к PostgreSQL с хоста НЕВОЗМОЖЕН (`psql -h localhost -p 5432` НЕ работает)
- [ ] Прямой доступ к Kafka с хоста НЕВОЗМОЖЕН
- [ ] Прямой доступ к Redis с хоста НЕВОЗМОЖЕН
- [ ] Frontend может обращаться к Backend через `/api/`
- [ ] Backend может подключаться к PostgreSQL через internal network
- [ ] Workers могут подключаться к Kafka через internal network

### 5. Документация
- [ ] README обновлён:
  - Объяснение reverse proxy архитектуры
  - Как получить доступ к сервисам
  - Как подключиться к БД для дебага (через `docker exec`)
- [ ] `.env.example` обновлён (если нужно)
- [ ] Deployment guide обновлён

### 6. Production готовность
- [ ] Nginx конфигурация готова к добавлению HTTPS (комментарии/примеры)
- [ ] Настроены логи nginx (`/var/log/nginx/access.log`, `/var/log/nginx/error.log`)
- [ ] Готовность к добавлению Let's Encrypt (опционально)

## Контекст

### Текущая архитектура портов (из docker-compose.yml)

```yaml
services:
  postgres:
    ports:
      - "5432:5432"  # ❌ Убрать

  kafka:
    ports:
      - "9092:9092"  # ❌ Убрать

  redis:
    ports:
      - "6379:6379"  # ❌ Убрать

  backend:
    ports:
      - "8000:8000"  # ❌ Убрать (доступ через nginx)

  frontend:
    ports:
      - "3000:3000"  # ❌ Убрать (доступ через nginx)
```

### Целевая архитектура

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"      # ✅ Единственный публичный порт
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend
    networks:
      - lunch-bot-network

  postgres:
    # ports удалены - только internal
    networks:
      - lunch-bot-network

  kafka:
    # ports удалены - только internal
    networks:
      - lunch-bot-network

  redis:
    # ports удалены - только internal
    networks:
      - lunch-bot-network

  backend:
    # ports удалены - доступ через nginx
    environment:
      CORS_ORIGINS: '["http://localhost"]'  # ✅ Обновить на nginx URL
    networks:
      - lunch-bot-network

  frontend:
    # ports удалены - доступ через nginx
    environment:
      NEXT_PUBLIC_API_URL: http://localhost/api/v1  # ✅ Через nginx
    networks:
      - lunch-bot-network
```

### Пример Nginx конфигурации

```nginx
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }

    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # Логирование
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        # Frontend (Telegram Mini App)
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Swagger UI
        location /docs {
            proxy_pass http://backend/docs;
            proxy_set_header Host $host;
        }

        location /openapi.json {
            proxy_pass http://backend/openapi.json;
            proxy_set_header Host $host;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

## Ожидаемый результат

После выполнения задачи:

1. **Один публичный порт**: `http://localhost:80`
   - Frontend: `http://localhost/`
   - API: `http://localhost/api/`
   - Docs: `http://localhost/docs`

2. **Безопасность**:
   - PostgreSQL, Kafka, Redis недоступны извне
   - Только nginx имеет публичный порт

3. **Production-ready**:
   - Готово к добавлению SSL/TLS (Let's Encrypt)
   - Готово к настройке на реальный домен
   - Логи nginx для мониторинга

4. **Удобство разработки**:
   - Для дебага БД: `docker exec -it lunch-bot-postgres psql -U postgres -d lunch_bot`
   - Для дебага Redis: `docker exec -it lunch-bot-redis redis-cli`
   - Для дебага Kafka: используй Kafka CLI внутри контейнера

## Связь с другими задачами

- **TSK-004**: После добавления nginx архитектура для деплоя станет production-ready
- **TSK-005**: Nginx будет точкой входа для Telegram Mini App
- **Зависимости**: Требует текущий docker-compose.yml

## Примечания

- Это улучшение инфраструктуры, не влияет на функциональность
- Критично для продакшн деплоя (безопасность + простота настройки DNS)
- Nginx - стандартный выбор для reverse proxy (легковесный, надёжный)
- Альтернативы: Traefik, Caddy (если нужна автоматическая HTTPS)

## Приоритет

**High** - критично для production deployment, улучшает безопасность

## Подзадачи для Architect

1. Создать nginx конфигурацию (`nginx/nginx.conf`)
2. Обновить docker-compose.yml (добавить nginx, убрать публичные порты)
3. Обновить environment variables (CORS, API URLs)
4. Написать shell скрипт для тестирования (curl)
5. Обновить документацию (README, deployment guide)
