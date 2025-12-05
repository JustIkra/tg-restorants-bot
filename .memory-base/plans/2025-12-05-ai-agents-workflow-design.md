# AI Agents Workflow Design

## Обзор

Система оркестрации AI-агентов для разработки Telegram-бота заказа обедов.

**Модель:** Supervisor + специализированные агенты
- Claude Code CLI — supervisor (точка входа, координация)
- 6 агентов через Python SDK (Architect, Coder, Reviewer, Tester, Debugger, DocWriter)
- Коммуникация через файлы в `.memory-base/workflow/`

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code CLI                       │
│                     (Supervisor)                         │
│  - Получает задачу от человека                          │
│  - Решает, какие агенты нужны                           │
│  - Координирует выполнение                              │
│  - Собирает результаты                                  │
│  - Эскалирует проблемы человеку                         │
└─────────────────┬───────────────────────────────────────┘
                  │ Python SDK
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Специализированные агенты                   │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│Architect │  Coder   │ Reviewer │  Tester  │  Debugger   │ DocWriter
│          │          │          │          │             │
│Проектирует│Пишет код│Проверяет │Пишет     │Анализирует  │Пишет
│архитектуру│         │качество  │тесты     │проблемы     │документацию
└──────────┴──────────┴──────────┴──────────┴─────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              .memory-base/workflow/                      │
│  - prompts/        (инструкции для агентов)             │
│  - tasks/          (задачи и результаты)                │
│  - config.yaml     (настройки pipeline)                 │
└─────────────────────────────────────────────────────────┘
```

## Агенты

| Агент | Роль | Вход | Выход |
|-------|------|------|-------|
| **Architect** | Проектирует архитектуру, разбивает задачи | task.md | architect.md |
| **Coder** | Пишет код по спецификации | task.md, architect.md | код + coder.md |
| **Reviewer** | Проверяет код на качество | код, coder.md | reviewer.md |
| **Tester** | Пишет и запускает тесты | код | тесты + tester.md |
| **Debugger** | Анализирует проблемы | ошибки | debugger.md |
| **DocWriter** | Пишет документацию | код | документация |

## Структура файлов

```
.memory-base/
├── index.md                        # Индекс документации
├── busness-logic/                  # Бизнес-требования
├── tech-docs/                      # Техническая документация
│   ├── stack.md
│   ├── api.md
│   ├── roles.md
│   └── rules/                      # Правила
│       ├── code-style.md
│       ├── git-workflow.md
│       └── testing.md
│
└── workflow/                       # Система агентов
    ├── config.yaml                 # Настройки
    ├── prompts/
    │   ├── base.md                 # Общие правила
    │   └── roles/
    │       ├── architect.md
    │       ├── coder.md
    │       ├── reviewer.md
    │       ├── tester.md
    │       ├── debugger.md
    │       └── docwriter.md
    │
    └── tasks/
        ├── active/                 # Текущие задачи
        │   └── TSK-XXX/
        │       ├── task.md
        │       ├── 01-architect.md
        │       ├── 02-coder.md
        │       └── ...
        ├── completed/              # Завершённые
        └── failed/                 # С ошибками
```

## Формат файлов

Markdown + YAML frontmatter:

```yaml
---
agent: coder
task_id: TSK-001
status: completed
next: reviewer
created_at: 2025-12-05T21:35:00
files_changed:
  - path: src/api/routes/orders.py
    action: modified
---
## Реализация

Описание что сделано...
```

**Метаданные:**
- `agent` — кто создал файл
- `task_id` — ID задачи
- `status` — completed | failed | blocked
- `next` — следующий агент или null
- `created_at` — время создания

## Pipeline

Supervisor контролирует pipeline динамически:

```
Задача: "Добавить endpoint отмены заказа"
→ Architect → Coder → Reviewer → Tester ✓

Задача: "Исправить опечатку в README"
→ DocWriter ✓

Задача: "Тесты падают после мержа"
→ Debugger → Coder → Tester ✓
```

**Типовые pipelines (из config.yaml):**
- `feature`: architect → coder → reviewer → tester → docwriter
- `bugfix`: debugger → coder → tester
- `refactor`: architect → coder → reviewer → tester
- `docs`: docwriter

## Обработка ошибок

```
Агент упал
    ↓
Debugger анализирует проблему
    ↓
Формирует отчёт
    ↓
Supervisor показывает человеку
    ↓
Человек решает: retry / skip / fix manually
```

## Иерархия промптов

Каждый агент получает: `base.md` + `roles/{role}.md`

**base.md** — ссылки на документацию проекта:
```markdown
## Проект
@.memory-base/index.md

## Правила
@.memory-base/tech-docs/rules/code-style.md
@.memory-base/tech-docs/rules/git-workflow.md
```

**roles/coder.md** — специфика роли:
```markdown
# Coder Agent

## Контекст
@.memory-base/index.md

## Правила
@.memory-base/tech-docs/rules/code-style.md

## Границы
- Не пишешь тесты (Tester)
- Не коммитишь (Supervisor)
```

## Инициация задач

**Вариант 1: Ручной запуск**
```
"Запусти Architect для добавления endpoint отмены заказа"
```

**Вариант 2: Файл задачи**
1. Создать `.memory-base/workflow/tasks/active/TSK-001/task.md`
2. Supervisor подхватит задачу

## Что реализовать

### Файлы документации
- [ ] `.memory-base/tech-docs/rules/code-style.md`
- [ ] `.memory-base/tech-docs/rules/git-workflow.md`
- [ ] `.memory-base/tech-docs/rules/testing.md`

### Workflow система
- [ ] `.memory-base/workflow/config.yaml`
- [ ] `.memory-base/workflow/prompts/base.md`
- [ ] `.memory-base/workflow/prompts/roles/architect.md`
- [ ] `.memory-base/workflow/prompts/roles/coder.md`
- [ ] `.memory-base/workflow/prompts/roles/reviewer.md`
- [ ] `.memory-base/workflow/prompts/roles/tester.md`
- [ ] `.memory-base/workflow/prompts/roles/debugger.md`
- [ ] `.memory-base/workflow/prompts/roles/docwriter.md`
- [ ] `.memory-base/workflow/tasks/active/.gitkeep`
- [ ] `.memory-base/workflow/tasks/completed/.gitkeep`
- [ ] `.memory-base/workflow/tasks/failed/.gitkeep`

### Корневой файл
- [ ] `CLAUDE.md`

## Технологии

- **Supervisor:** Claude Code CLI
- **Агенты:** Python + Claude Agent SDK
- **Коммуникация:** Файлы Markdown + YAML frontmatter
- **Хранение:** `.memory-base/workflow/`
