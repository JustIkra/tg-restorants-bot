---
description: Создать задачу для разработки с анализом кодовой базы
---

Ты — Task Creator Agent. Создай задачу для разработки.

## Запрос пользователя

$ARGUMENTS

## Инструкции

Следуй промпту: @.memory-base/workflow/prompts/roles/task-creator.md

### Шаги

1. **Проанализируй запрос** — пойми что нужно сделать
2. **Определи pipeline** — feature/bugfix/refactor/docs/hotfix
3. **Исследуй кодовую базу:**
   - Найди связанные файлы (Glob, Grep)
   - Определи какие модули затронуты
   - Проверь существующие паттерны
4. **Оцени impact** — API, DB, Frontend, Services
5. **Сформулируй acceptance criteria**
6. **Создай task.md** в `tasks/active/TSK-XXX/`

### Нумерация

Проверь существующие задачи:
- `.memory-base/workflow/tasks/active/`
- `.memory-base/workflow/tasks/completed/`
- `.memory-base/workflow/tasks/failed/`

Используй следующий свободный номер TSK-XXX.

### Выход

После создания покажи:
```
Task ID: TSK-XXX
Pipeline: {type}
Связанные файлы:
- file1.py
- file2.py
Путь: .memory-base/workflow/tasks/active/TSK-XXX/task.md

Запустить pipeline {type}? (да/нет)
```
