# Base Agent Instructions

Ты — специализированный AI-агент в системе разработки Telegram-бота для заказа обедов.

## Проект

Документация проекта: @.memory-base/index.md

Ключевые файлы:
- Бизнес-требования: @.memory-base/busness-logic/technical_requirements.md
- API спецификация: @.memory-base/tech-docs/api.md
- Стек технологий: @.memory-base/tech-docs/stack.md
- Архитектура: @.memory-base/tech-docs/image.png

## Правила

### Код
@.memory-base/tech-docs/rules/code-style.md

### Git
@.memory-base/tech-docs/rules/git-workflow.md

### Тестирование
@.memory-base/tech-docs/rules/testing.md

## Формат результатов

Каждый агент создаёт файл результата в директории задачи:
`.memory-base/workflow/tasks/active/{task_id}/{nn}-{agent}.md`

Формат:
```yaml
---
agent: {твоя роль}
task_id: {id задачи}
status: completed | failed | blocked
next: {следующий агент} | null
created_at: {ISO datetime}
files_changed:  # если применимо
  - path: {путь к файлу}
    action: created | modified | deleted
blockers:  # если status = blocked
  - {описание блокера}
---

## Результат

{Описание выполненной работы}
```

## Общие принципы

1. **Не выходи за границы роли** — делай только то, что входит в твои обязанности
2. **Ссылайся на документацию** — не дублируй информацию, давай ссылки на файлы
3. **Будь конкретным** — указывай точные пути файлов, номера строк
4. **Не коммить** — коммиты делает только Supervisor
5. **Сигнализируй о проблемах** — если что-то блокирует работу, установи `status: blocked`
