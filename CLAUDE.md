# CLAUDE.md

Ты — AI-ассистент для разработки Telegram-бота заказа обедов.

## Документация проекта

@.memory-base/index.md

## Workflow

Система AI-агентов для разработки:
@.memory-base/plans/2025-12-05-ai-agents-workflow-design.md

Конфигурация:
@.memory-base/workflow/config.yaml

## Быстрые ссылки

| Документ | Путь |
|----------|------|
| Бизнес-требования | @.memory-base/busness-logic/technical_requirements.md |
| API | @.memory-base/tech-docs/api.md |
| Стек | @.memory-base/tech-docs/stack.md |
| Code style | @.memory-base/tech-docs/rules/code-style.md |
| Git workflow | @.memory-base/tech-docs/rules/git-workflow.md |
| Testing | @.memory-base/tech-docs/rules/testing.md |

## Команды

### Запуск агента
```
"Запусти {agent} для {задача}"
```

Агенты: architect, coder, reviewer, tester, debugger, docwriter

### Создание задачи
Создай файл `.memory-base/workflow/tasks/active/TSK-XXX/task.md`

### Pipelines
- `feature` — architect → coder → reviewer → tester → docwriter
- `bugfix` — debugger → coder → tester
- `refactor` — architect → coder → reviewer → tester
- `docs` — docwriter

## MCP

- **context7** — документация библиотек (resolve-library-id, get-library-docs)
