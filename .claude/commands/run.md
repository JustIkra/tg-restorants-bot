---
description: Запустить задачу TSK-XXX или pipeline для задачи
---

## Аргументы

$ARGUMENTS

## Инструкции для Supervisor

Ты — Supervisor. Оркеструй выполнение pipeline через субагентов.

### 1. Определи задачу

Прочитай `.memory-base/workflow/tasks/active/$ARGUMENTS/task.md`:
- Извлеки `pipeline` из frontmatter
- Пойми требования задачи

### 2. Определи текущий этап

Проверь существующие файлы результатов в директории задачи:
- `01-architect.md` или `01-debugger.md`
- `02-coder.md`
- `03-reviewer.md`
- `04-tester.md`
- `05-docwriter.md`

Найди последний завершённый этап и определи следующий.

### 3. Pipelines

| Pipeline | Этапы |
|----------|-------|
| feature | architect → coder → reviewer → tester → docwriter |
| bugfix | debugger → coder → tester |
| refactor | architect → coder → reviewer → tester |
| docs | docwriter |
| hotfix | coder → tester |

### 4. Запуск субагентов

Для каждого этапа запусти субагент через Task tool:

```
Task tool:
  subagent_type: "general-purpose"
  description: "{Agent}: {task_id}"
  prompt: |
    [Промпт агента из соответствующей команды]

    Задача: $ARGUMENTS
```

**Последовательность:**
1. Запусти первого агента pipeline
2. Дождись результата
3. Проверь status в результате:
   - `completed` → запусти следующего агента
   - `blocked` → сообщи пользователю о блокере
   - `CHANGES_REQUESTED` (reviewer) → вернись к coder
   - `FAILED` (tester) → вернись к coder
4. Повтори до завершения pipeline

### 5. Завершение

После успешного завершения всех этапов:

1. Перемести задачу в `tasks/completed/`:
   ```bash
   mv .memory-base/workflow/tasks/active/TSK-XXX .memory-base/workflow/tasks/completed/
   ```

2. Обнови status в task.md на `completed`

3. Сообщи пользователю:
   ```
   Pipeline {type} завершён для {task_id}

   Результаты:
   - 01-architect.md: {summary}
   - 02-coder.md: {files_changed}
   - 03-reviewer.md: {verdict}
   - 04-tester.md: {test_results}
   - 05-docwriter.md: {docs_updated}
   ```

### 6. Обработка ошибок

**При блокере:**
```
Задача {task_id} заблокирована на этапе {agent}

Причина: {blocker description}

Что делать?
1. Уточнить требования
2. Пропустить этап
3. Отменить задачу
```

**При CHANGES_REQUESTED от Reviewer:**
- Передай замечания в Coder
- После исправлений запусти Reviewer повторно
- Максимум 2 итерации, потом эскалируй

**При FAILED от Tester:**
- Передай описание проблем в Coder
- После исправлений запусти Tester повторно
- Максимум 2 итерации, потом эскалируй

### Пример выполнения

```
/run TSK-001

1. Читаю task.md... Pipeline: feature
2. Проверяю прогресс... Найден 01-architect.md
3. Следующий этап: coder

Запускаю Coder субагент...
[Task tool: subagent_type="general-purpose", description="Coder: TSK-001"]

Coder завершил работу:
- Изменены файлы: src/services/order.py, src/api/orders.py
- Status: completed

Запускаю Reviewer субагент...
[Task tool: subagent_type="general-purpose", description="Reviewer: TSK-001"]

Reviewer завершил:
- Verdict: APPROVED
- Next: tester

...и так далее до завершения pipeline
```
