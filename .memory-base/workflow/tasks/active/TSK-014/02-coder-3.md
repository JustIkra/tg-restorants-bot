---
agent: coder
task_id: TSK-014
subtask: 3
subtask_name: "cafe-requests 404 fix"
status: completed
next: null
created_at: 2025-12-07T01:52:00+0300
files_changed:
  - path: backend/src/routers/cafe_links.py
    action: modified
  - path: backend/src/routers/__init__.py
    action: modified
  - path: backend/src/main.py
    action: modified
---

## Реализация

Исправлена проблема с 404 ошибкой для endpoint'а `/api/v1/cafe-requests` путём разделения единого router'а на два отдельных:

1. `cafe_links_router` — endpoints для работы с конкретными кафе (prefix `/cafes`)
2. `cafe_requests_router` — endpoints для работы со списком запросов (без prefix)

Теперь:
- `GET /api/v1/cafe-requests` — доступен (список запросов для менеджера)
- `POST /api/v1/cafe-requests/{request_id}/approve` — доступен
- `POST /api/v1/cafe-requests/{request_id}/reject` — доступен
- `POST /api/v1/cafes/{cafe_id}/link-request` — работает как раньше
- `PATCH /api/v1/cafes/{cafe_id}/notifications` — работает как раньше
- `DELETE /api/v1/cafes/{cafe_id}/link` — работает как раньше

### Изменения

#### `backend/src/routers/cafe_links.py`

**Было:**
```python
router = APIRouter(prefix="/cafes", tags=["cafe-links"])

@router.get("/cafe-requests", ...)  # Становится /cafes/cafe-requests
@router.post("/cafe-requests/{request_id}/approve", ...)
@router.post("/cafe-requests/{request_id}/reject", ...)
```

**Стало:**
```python
# Router for cafe-specific endpoints (with /cafes prefix)
cafe_links_router = APIRouter(prefix="/cafes", tags=["cafe-links"])

# Router for cafe-requests endpoints (no prefix)
cafe_requests_router = APIRouter(tags=["cafe-requests"])

# Endpoints для cafe links (остались в cafe_links_router)
@cafe_links_router.post("/{cafe_id}/link-request", ...)
@cafe_links_router.patch("/{cafe_id}/notifications", ...)
@cafe_links_router.delete("/{cafe_id}/link", ...)

# Endpoints для cafe requests (перенесены в cafe_requests_router)
@cafe_requests_router.get("/cafe-requests", ...)
@cafe_requests_router.post("/cafe-requests/{request_id}/approve", ...)
@cafe_requests_router.post("/cafe-requests/{request_id}/reject", ...)
```

**Обоснование:**
- Endpoints для работы с конкретным кафе логически относятся к `/cafes/{cafe_id}/*`
- Endpoints для работы со списком всех запросов не привязаны к конкретному кафе, поэтому должны быть на уровне `/cafe-requests`

#### `backend/src/routers/__init__.py`

**Было:**
```python
from .cafe_links import router as cafe_links_router

__all__ = [
    ...,
    "cafe_links_router",
    ...,
]
```

**Стало:**
```python
from .cafe_links import cafe_links_router, cafe_requests_router

__all__ = [
    ...,
    "cafe_links_router",
    "cafe_requests_router",
    ...,
]
```

Добавлен экспорт нового router'а `cafe_requests_router`.

#### `backend/src/main.py`

**Было:**
```python
from .routers import (
    ...,
    cafe_links_router,
    ...,
)

app.include_router(cafe_links_router, prefix="/api/v1")
```

**Стало:**
```python
from .routers import (
    ...,
    cafe_links_router,
    cafe_requests_router,
    ...,
)

app.include_router(cafe_links_router, prefix="/api/v1")
app.include_router(cafe_requests_router, prefix="/api/v1")
```

Добавлен импорт и подключение нового router'а.

## Примечания

- Разделение на два router'а позволяет избежать конфликта prefixes и сохранить чёткую семантику URL'ов
- Все существующие endpoints продолжают работать на тех же путях
- Новые endpoints для `cafe-requests` теперь доступны на правильных путях без лишнего `/cafes` prefix
- Оба router'а используют общий сервис `CafeLinkService` и dependency `get_cafe_link_service`
