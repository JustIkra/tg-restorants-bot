# Git Workflow

## Ветки

### Основные
- `main` — production, защищённая
- `develop` — интеграция (опционально)

### Feature branches
```
feature/TSK-001-add-order-cancellation
bugfix/TSK-002-fix-deadline-calculation
refactor/TSK-003-extract-notification-service
docs/TSK-004-update-api-docs
```

Формат: `{type}/TSK-{id}-{short-description}`

## Коммиты

### Формат
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat` — новая функциональность
- `fix` — исправление бага
- `refactor` — рефакторинг без изменения поведения
- `docs` — документация
- `test` — тесты
- `chore` — настройка, зависимости

### Scope
- `api`, `bot`, `worker`, `frontend`, `db`

### Примеры
```
feat(api): add order cancellation endpoint

- Add DELETE /orders/{id} endpoint
- Add deadline validation before cancellation
- Update order status to 'cancelled'

Closes TSK-001
```

```
fix(worker): handle missing cafe notification settings

Previously crashed when cafe had no tg_chat_id.
Now skips notification gracefully.

Fixes TSK-002
```

## Pull Requests

### Название
```
[TSK-001] Add order cancellation feature
```

### Описание
```markdown
## Summary
- Added endpoint for order cancellation
- Users can cancel before deadline

## Changes
- `src/api/routes/orders.py` — new DELETE endpoint
- `src/services/order_service.py` — cancellation logic

## Testing
- [ ] Unit tests pass
- [ ] Manual testing done
```

### Review checklist
- [ ] Code follows style guide (@.memory-base/tech-docs/rules/code-style.md)
- [ ] Tests added/updated
- [ ] No sensitive data in code
- [ ] Error handling present

## Merge Strategy

- **Squash merge** для feature branches
- Один коммит на фичу
- Удалять ветку после мержа
