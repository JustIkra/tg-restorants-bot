# Production Deployment Guide

Руководство по развертыванию Lunch Order Bot в production.

## Требования к серверу

- Linux (Ubuntu 22.04+ рекомендуется)
- Docker & Docker Compose v2.20+
- 4GB RAM minimum (рекомендуется 8GB для Kafka)
- 20GB disk space
- Открытые порты: 80, 443
- Доменное имя с настроенным DNS

## Подготовка

### 1. Настройка SSL сертификата

Используйте Let's Encrypt для бесплатного SSL:

```bash
# Установить certbot
sudo apt update
sudo apt install certbot

# Получить сертификат (требуется остановить nginx/apache)
sudo certbot certonly --standalone -d your-domain.com

# Сертификаты будут сохранены в:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 2. Подготовка конфигурации

```bash
# Клонировать репозиторий
git clone <repository-url>
cd tg_bot

# Скопировать production шаблоны
cp backend/.env.example backend/.env.production
cp frontend_mini_app/.env.example frontend_mini_app/.env.production

# Отредактировать с реальными значениями
nano backend/.env.production
```

**Обязательные переменные (backend/.env.production):**

```bash
# Database (используйте сильный пароль!)
DATABASE_URL=postgresql+asyncpg://postgres:STRONG_PASSWORD@postgres:5432/lunch_bot

# JWT (сгенерировать новый ключ!)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7

# Telegram
TELEGRAM_BOT_TOKEN=your_real_bot_token_from_botfather
TELEGRAM_MINI_APP_URL=https://your-domain.com

# Gemini API (опционально, для рекомендаций)
GEMINI_API_KEYS=key1,key2,key3
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MAX_REQUESTS_PER_KEY=195

# Kafka
KAFKA_BROKER_URL=kafka:29092

# Redis
REDIS_URL=redis://redis:6379

# CORS (укажите ваш домен!)
CORS_ORIGINS=["https://your-domain.com","https://web.telegram.org"]
```

**Frontend (.env.production):**

```bash
NEXT_PUBLIC_API_URL=https://your-domain.com/api/v1
```

### 3. Настройка nginx для SSL

Создайте `nginx/nginx.prod.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Backend API
        location /api/v1/ {
            proxy_pass http://backend/api/v1/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://backend/health;
        }

        # Frontend
        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

Скопировать SSL сертификаты:
```bash
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chmod 644 nginx/ssl/*.pem
```

### 4. Production Docker Compose

Создайте `docker-compose.prod.yml`:

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    container_name: lunch-bot-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    restart: always
    networks:
      - lunch-bot-network

  postgres:
    image: postgres:17-alpine
    container_name: lunch-bot-postgres-prod
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: lunch_bot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    networks:
      - lunch-bot-network

  kafka:
    image: confluentinc/cp-kafka:latest
    container_name: lunch-bot-kafka-prod
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_LISTENERS: PLAINTEXT://kafka:29092,CONTROLLER://kafka:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk
    restart: always
    networks:
      - lunch-bot-network

  redis:
    image: redis:7-alpine
    container_name: lunch-bot-redis-prod
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: always
    networks:
      - lunch-bot-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: lunch-bot-backend-prod
    env_file: ./backend/.env.production
    depends_on:
      - postgres
      - kafka
      - redis
    restart: always
    networks:
      - lunch-bot-network

  frontend:
    build:
      context: ./frontend_mini_app
      dockerfile: Dockerfile
      target: production
      args:
        NEXT_PUBLIC_API_URL: https://your-domain.com/api/v1
    container_name: lunch-bot-frontend-prod
    env_file: ./frontend_mini_app/.env.production
    restart: always
    networks:
      - lunch-bot-network

  telegram-bot:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: lunch-bot-telegram-prod
    env_file: ./backend/.env.production
    depends_on:
      - postgres
      - redis
    command: python -m src.telegram.bot
    restart: always
    networks:
      - lunch-bot-network

  notifications-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: lunch-bot-notifications-worker-prod
    env_file: ./backend/.env.production
    depends_on:
      - postgres
      - kafka
      - redis
    command: python -m workers.notifications
    restart: always
    networks:
      - lunch-bot-network

  recommendations-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: lunch-bot-recommendations-worker-prod
    env_file: ./backend/.env.production
    depends_on:
      - postgres
      - kafka
      - redis
    command: python -m workers.recommendations
    restart: always
    networks:
      - lunch-bot-network

volumes:
  postgres_data:
  redis_data:

networks:
  lunch-bot-network:
    driver: bridge
```

## Запуск

### 1. Сборка и запуск

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 2. Применить миграции

```bash
docker exec lunch-bot-backend-prod alembic upgrade head
```

### 3. Проверить статус

```bash
# Проверить все контейнеры
docker-compose -f docker-compose.prod.yml ps

# Health check
curl https://your-domain.com/health
curl https://your-domain.com/health/all
```

### 4. Настроить автообновление SSL

```bash
# Добавить в crontab
sudo crontab -e

# Обновлять сертификат каждые 60 дней
0 0 1 */2 * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /path/to/tg_bot/nginx/ssl/ && docker restart lunch-bot-nginx-prod
```

## Обновление

### Стандартное обновление

```bash
# Получить обновления
git pull

# Пересобрать и перезапустить
docker-compose -f docker-compose.prod.yml up -d --build

# Применить новые миграции (если есть)
docker exec lunch-bot-backend-prod alembic upgrade head
```

### Rolling update (без даунтайма)

```bash
# Обновить по одному сервису
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend
docker-compose -f docker-compose.prod.yml up -d --no-deps --build frontend
# и т.д.
```

## Бэкапы

### PostgreSQL

```bash
# Создать бэкап
docker exec lunch-bot-postgres-prod pg_dump -U postgres lunch_bot > backup-$(date +%Y%m%d-%H%M%S).sql

# Восстановить
docker exec -i lunch-bot-postgres-prod psql -U postgres lunch_bot < backup.sql
```

### Автоматизация бэкапов

Создайте скрипт `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/lunch-bot"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker exec lunch-bot-postgres-prod pg_dump -U postgres lunch_bot | gzip > $BACKUP_DIR/postgres-$DATE.sql.gz

# Redis backup
docker exec lunch-bot-redis-prod redis-cli BGSAVE
sleep 5
docker cp lunch-bot-redis-prod:/data/dump.rdb $BACKUP_DIR/redis-$DATE.rdb

# Удалить старые бэкапы (старше 30 дней)
find $BACKUP_DIR -mtime +30 -delete

echo "Backup completed: $DATE"
```

Добавьте в crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### Redis

```bash
# Создать бэкап
docker exec lunch-bot-redis-prod redis-cli BGSAVE
docker cp lunch-bot-redis-prod:/data/dump.rdb ./redis-backup.rdb

# Восстановить
docker cp ./redis-backup.rdb lunch-bot-redis-prod:/data/dump.rdb
docker restart lunch-bot-redis-prod
```

## Мониторинг

### Логи

```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker logs -f lunch-bot-backend-prod
docker logs -f lunch-bot-telegram-prod

# Последние 100 строк
docker logs --tail 100 lunch-bot-backend-prod
```

### Health checks

```bash
# API health
curl https://your-domain.com/health

# Полная проверка всех компонентов
curl https://your-domain.com/health/all
```

### Метрики

```bash
# Использование ресурсов
docker stats

# Диск
df -h
docker system df

# PostgreSQL
docker exec lunch-bot-postgres-prod psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('lunch_bot'));"

# Redis
docker exec lunch-bot-redis-prod redis-cli INFO memory
```

## Безопасность

### Firewall

```bash
# Открыть только необходимые порты
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
```

### Регулярные обновления

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Обновить Docker образы
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Проверка секретов

```bash
# Убедитесь что .env файлы НЕ в git
git check-ignore backend/.env.production
git check-ignore frontend_mini_app/.env.production
```

## Масштабирование

### Горизонтальное масштабирование workers

```bash
# Увеличить количество notifications workers
docker-compose -f docker-compose.prod.yml up -d --scale notifications-worker=3

# Увеличить количество recommendations workers
docker-compose -f docker-compose.prod.yml up -d --scale recommendations-worker=2
```

### Resource limits

В `docker-compose.prod.yml` добавьте:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        memory: 1G
```

## Troubleshooting

### Backend не отвечает

```bash
# Проверить статус
docker ps | grep backend

# Проверить логи
docker logs --tail 50 lunch-bot-backend-prod

# Проверить health
curl http://localhost:8000/health

# Перезапустить
docker restart lunch-bot-backend-prod
```

### PostgreSQL проблемы

```bash
# Проверить подключения
docker exec lunch-bot-postgres-prod psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Проверить размер БД
docker exec lunch-bot-postgres-prod psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('lunch_bot'));"

# Проверить логи
docker logs lunch-bot-postgres-prod
```

### Kafka проблемы

```bash
# Проверить topics
docker exec lunch-bot-kafka-prod kafka-topics --list --bootstrap-server localhost:29092

# Проверить consumer lag
docker exec lunch-bot-kafka-prod kafka-consumer-groups --bootstrap-server localhost:29092 --describe --all-groups
```

### SSL сертификат истек

```bash
# Обновить сертификат
sudo certbot renew

# Скопировать новые сертификаты
sudo cp /etc/letsencrypt/live/your-domain.com/*.pem /path/to/nginx/ssl/

# Перезапустить nginx
docker restart lunch-bot-nginx-prod
```

## Откат (Rollback)

```bash
# Откатиться к предыдущему commit
git log --oneline
git checkout <previous-commit>

# Пересобрать
docker-compose -f docker-compose.prod.yml up -d --build

# Откатить миграции (осторожно!)
docker exec lunch-bot-backend-prod alembic downgrade -1
```

## Дополнительные ресурсы

- [Environment Variables](environment.md) - полный справочник переменных
- [Quick Start](quick-start.md) - локальная разработка
- [Troubleshooting](../troubleshooting.md) - решение проблем
