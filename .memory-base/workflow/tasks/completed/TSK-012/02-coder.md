---
agent: coder
task_id: TSK-012
status: completed
next: tester
created_at: 2025-12-07T17:15:00+03:00
files_changed:
  - path: nginx/nginx.prod.conf
    action: modified
---

## Реализация

Исправлена конфигурация WebSocket в nginx.prod.conf. Добавлена `map` директива для динамической установки `Connection` header в зависимости от наличия `Upgrade` header в запросе.

### Изменения

#### `nginx/nginx.prod.conf`

**1. Добавлена map директива (после строки 58, перед блоком server):**

```nginx
# WebSocket connection upgrade map
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
```

Эта директива создает переменную `$connection_upgrade`, которая:
- Устанавливается в `upgrade` если клиент отправил `Upgrade` header (WebSocket запрос)
- Устанавливается в `close` если `Upgrade` header отсутствует (обычный HTTP запрос)

**2. Заменен фиксированный Connection header на динамический в location /api/ (строка 87):**

```nginx
# Было:
proxy_set_header Connection 'upgrade';

# Стало:
proxy_set_header Connection $connection_upgrade;
```

**3. Заменен фиксированный Connection header на динамический в location / (строка 107):**

```nginx
# Было:
proxy_set_header Connection 'upgrade';

# Стало:
proxy_set_header Connection $connection_upgrade;
```

### Логика работы

До изменений:
- Все запросы (HTTP и WebSocket) получали `Connection: upgrade` header
- Это приводило к ошибкам для обычных HTTP запросов
- Next.js HMR пытался установить WebSocket соединение и получал ошибки

После изменений:
- WebSocket запросы (с `Upgrade: websocket` header) → `Connection: upgrade`
- Обычные HTTP запросы (без `Upgrade` header) → `Connection: close`
- Nginx корректно обрабатывает оба типа запросов

## Примечания

- Использован тот же подход, что и в development конфигурации (`nginx/nginx.conf`)
- Изменения минимальны и не влияют на другие части конфигурации
- Map директива размещена в блоке `http`, что делает переменную `$connection_upgrade` доступной во всех server блоках
- Изменения применены к обоим location блокам (/api/ и /) для единообразия
