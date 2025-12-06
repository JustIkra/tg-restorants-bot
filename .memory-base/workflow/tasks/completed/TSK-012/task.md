---
id: TSK-012
title: Fix WebSocket configuration in nginx.prod.conf
pipeline: hotfix
status: pending
created_at: 2025-12-07T16:45:00+03:00
related_files:
  - nginx/nginx.prod.conf
  - nginx/nginx.conf
impact:
  api: no
  db: no
  frontend: no
  services: yes (nginx)
---

## Описание

В production nginx конфигурации (`nginx/nginx.prod.conf`) отсутствует `map` директива для корректной обработки WebSocket соединений. Это приводит к тому, что nginx всегда отправляет `Connection: upgrade` header, даже для обычных HTTP запросов.

### Проблема

**Текущее состояние (nginx.prod.conf, строки 86-87, 106-107):**
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection 'upgrade';  # <-- Всегда "upgrade"
```

**Правильная конфигурация (nginx.conf, строки 102-105):**
```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

# И затем:
proxy_set_header Connection $connection_upgrade;  # <-- Динамически
```

### Последствия

1. WebSocket ошибки в консоли браузера (Next.js HMR пытается подключиться)
2. Проблемы с HTTP keep-alive соединениями
3. Ошибки в логах nginx
4. Некорректная обработка обычных HTTP запросов как WebSocket

## Acceptance Criteria

- [ ] Добавлена `map` директива в `http` блок nginx.prod.conf
- [ ] Заменено фиксированное значение `'upgrade'` на переменную `$connection_upgrade` в двух местах:
  - location /api/ (строка 87)
  - location / (строка 107)
- [ ] Проверен синтаксис конфигурации (`nginx -t`)
- [ ] Перезапущен nginx в production
- [ ] Проверено отсутствие WebSocket ошибок в консоли браузера

## Технические детали

### Где добавить map директиву

В `nginx/nginx.prod.conf` в блоке `http`, после определений `upstream` и перед блоком `server` (после строки 58):

```nginx
http {
    # ... existing config ...

    # Frontend upstream
    upstream frontend {
        server frontend:3000;
    }

    # WebSocket connection upgrade map
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    # HTTP server
    server {
        # ...
    }
}
```

### Где заменить Connection header

**Место 1: location /api/ (строка 87)**
```nginx
location /api/ {
    # ...
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;  # <-- Было 'upgrade'
    # ...
}
```

**Место 2: location / (строка 107)**
```nginx
location / {
    # ...
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;  # <-- Было 'upgrade'
    # ...
}
```

## Как работает map директива

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;  # Если $http_upgrade не пустой → Connection: upgrade
    '' close;         # Если $http_upgrade пустой → Connection: close
}
```

- Если клиент отправляет `Upgrade: websocket` → nginx отвечает `Connection: upgrade`
- Если клиент НЕ отправляет `Upgrade` header → nginx отвечает `Connection: close`

Это позволяет nginx правильно обрабатывать и WebSocket, и обычные HTTP запросы.

## Проверка после применения

### 1. Локальная проверка синтаксиса
```bash
docker exec nginx nginx -t
```

### 2. Перезапуск nginx
```bash
docker exec nginx nginx -s reload
```

### 3. Проверка в браузере
- Открыть DevTools → Console
- Перейти на https://lunchbot.vibe-labs.ru
- Убедиться, что нет ошибок WebSocket

### 4. Проверка логов
```bash
docker logs nginx --tail=100 | grep -i upgrade
```

## Контекст

### Почему это важно

1. **WebSocket**: Next.js HMR (Hot Module Replacement) в development использует WebSocket, но в production это не нужно и вызывает ошибки
2. **HTTP/1.1 Keep-Alive**: Обычные HTTP запросы должны использовать `Connection: close` или `Connection: keep-alive`, а не `upgrade`
3. **Производительность**: Неправильные headers могут приводить к лишним попыткам upgrade и ошибкам

### Аналогия с development

Development конфигурация (`nginx/nginx.conf`) уже содержит правильную `map` директиву и работает корректно. Нужно просто скопировать этот подход в production.

## Риски

**Риск:** Изменение может повлиять на работающее production окружение
**Решение:** Изменения минимальны и являются исправлением. Map директива только улучшает обработку headers.

**Риск:** Синтаксическая ошибка может сломать nginx
**Решение:** Проверка синтаксиса (`nginx -t`) перед перезапуском. Если ошибка — откат изменений.

## Pipeline: hotfix

Это hotfix, pipeline состоит из:
1. **coder** — внести изменения в nginx.prod.conf
2. **tester** — проверить синтаксис, перезапустить nginx, проверить работу

## Дополнительная информация

- Development конфигурация: `/Users/maksim/git_projects/tg_bot/nginx/nginx.conf`
- Production конфигурация: `/Users/maksim/git_projects/tg_bot/nginx/nginx.prod.conf`
- Документация deployment: `.memory-base/tech-docs/deployment.md`
