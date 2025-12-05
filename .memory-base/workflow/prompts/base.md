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

## Параллельное выполнение

Supervisor может запустить несколько экземпляров одного агента параллельно для независимых подзадач.

### Когда ты работаешь в параллельном режиме

Supervisor передаст тебе конкретную подзадачу. Твоя ответственность:

1. **Работай только со своими файлами** — не изменяй файлы, которые не указаны в твоей подзадаче
2. **Не создавай общие зависимости** — если нужен shared код, укажи это в blockers
3. **Именуй результат с суффиксом** — например `02-coder-1.md` для первой параллельной подзадачи

### Формат результата при параллельном выполнении

```yaml
---
agent: coder
task_id: TSK-001
subtask: 1  # номер параллельной подзадачи
subtask_name: "API client"  # краткое название
status: completed
next: null  # Supervisor решит сам
created_at: 2025-12-05T12:00:00
files_changed:
  - path: src/lib/api/client.ts
    action: created
---
```

### Конфликты

Если ты обнаружишь, что твоя подзадача конфликтует с другой:
1. Установи `status: blocked`
2. Опиши конфликт в `blockers`
3. Supervisor разрешит конфликт
