---
id: TSK-007
title: "Production deployment documentation"
pipeline: docs
status: pending
created_at: 2025-12-06T14:00:00Z
related_files:
  - .memory-base/tech-docs/deployment.md (to be created)
  - .memory-base/index.md (to be updated)
  - docker-compose.yml (reference)
  - backend/.env.example (reference)
impact:
  api: false
  db: false
  frontend: false
  services: false
  docs: true
---

# TSK-007: Production Deployment Documentation

## Описание

Создать полную документацию по production deployment Telegram-бота на выделенный сервер.

## Production Infrastructure

### Сервер
- **IP:** 172.25.0.200
- **SSH доступ:** user@172.25.0.200:22
- **Назначение:** Docker host для всех сервисов проекта

### Домен
- **Доменное имя:** lunchbot.vibe-labs.ru
- **HTTPS:** Let's Encrypt (управляется через Nginx Proxy Manager)

### Архитектура

```
Internet
    ↓
Nginx Proxy Manager (отдельный сервер)
    ↓ (proxy_pass to 172.25.0.200:80)
172.25.0.200 (Docker host)
    ↓
docker-compose stack:
    ├── nginx (внутренний reverse proxy)
    ├── frontend (Next.js app)
    ├── backend (FastAPI)
    ├── postgres
    ├── kafka
    ├── redis
    ├── telegram-bot
    ├── notifications-worker
    └── recommendations-worker
```

## Что нужно документировать

### 1. Deployment Guide
- Подготовка сервера (SSH, Docker, Docker Compose)
- Клонирование репозитория
- Настройка environment variables для production
- Запуск docker-compose
- Проверка работоспособности

### 2. Environment Variables
Для каждого сервиса описать:
- `backend/.env` — все переменные окружения для production
- Database credentials (production)
- Kafka configuration
- Redis configuration
- JWT secrets
- Telegram Bot token
- Gemini API keys
- CORS origins (включая домен)

### 3. Nginx Proxy Manager Configuration
- Как настроен proxy pass с внешнего сервера на 172.25.0.200:80
- SSL сертификаты (Let's Encrypt)
- Proxy headers

### 4. Docker Compose для Production
Изменения в docker-compose.yml для production:
- Убрать volume mounts с live code (--reload mode)
- Использовать production builds
- Правильные environment variables
- Health checks
- Resource limits (optional)

### 5. CI/CD (optional, если нужно)
- Как обновлять код на сервере
- Workflow для deploy (git pull + docker-compose up --build -d)

### 6. Monitoring & Logs
- Где смотреть логи (docker-compose logs)
- Как проверять статус сервисов (docker-compose ps)

### 7. Backup & Restore
- PostgreSQL backup strategy
- Восстановление из бэкапа

## Технические детали

### Docker Services (из docker-compose.yml)
- **postgres:** PostgreSQL 17, порт 5432
- **kafka:** Confluent Kafka, порт 9092
- **redis:** Redis 7, порт 6379
- **backend:** FastAPI на порту 8000
- **frontend:** Next.js на порту 3000
- **telegram-bot:** Telegram bot process
- **notifications-worker:** Kafka consumer для уведомлений
- **recommendations-worker:** Kafka consumer для рекомендаций

### Network
- Все сервисы в одной сети: `lunch-bot-network` (bridge)

### Volumes
- `postgres_data` — persistent PostgreSQL data
- `redis_data` — persistent Redis data

## Acceptance Criteria

- [ ] Создан файл `.memory-base/tech-docs/deployment.md`
- [ ] Обновлён `.memory-base/index.md` с ссылкой на deployment.md
- [ ] Документирована архитектура deployment
- [ ] Описаны шаги для первого deployment
- [ ] Описаны environment variables для production
- [ ] Описана настройка Nginx Proxy Manager
- [ ] Описан процесс обновления (re-deploy)
- [ ] Описаны команды для проверки статуса и логов
- [ ] Описана стратегия backup/restore

## Примечания

- DocWriter агент должен изучить:
  - `docker-compose.yml` — текущую конфигурацию
  - `backend/.env.example` — список переменных окружения
  - `.memory-base/tech-docs/stack.md` — используемый стек
  - `.memory-base/tech-docs/api.md` — backend API endpoints

## Приоритет

Medium (документация для будущего deployment)
