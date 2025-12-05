---
description: Создать задачу для разработки с анализом кодовой базы
---

## Запрос пользователя

$ARGUMENTS

## Действие

Запусти субагент через Task tool:

```
Task tool:
  subagent_type: "general-purpose"
  description: "TaskCreator: создание задачи"
  prompt: |
    Ты — Task Creator Agent для проекта Telegram-бота заказа обедов.

    ## Запрос пользователя
    $ARGUMENTS

    ## Контекст проекта
    Прочитай документацию:
    - .memory-base/index.md — главный индекс
    - .memory-base/busness-logic/technical_requirements.md — бизнес-требования
    - .memory-base/tech-docs/api.md — API спецификация
    - .memory-base/tech-docs/stack.md — стек технологий

    ## Инструкции

    ### 1. Проанализируй запрос
    Пойми что нужно сделать.

    ### 2. Определи pipeline
    - feature — новая функциональность
    - bugfix — исправление бага
    - refactor — рефакторинг
    - docs — только документация
    - hotfix — срочное исправление

    ### 3. Исследуй кодовую базу
    Используй Glob и Grep чтобы найти:
    - Связанные файлы
    - Затронутые модули
    - Существующие паттерны

    ### 4. Нумерация
    Проверь существующие задачи:
    - .memory-base/workflow/tasks/active/
    - .memory-base/workflow/tasks/completed/
    - .memory-base/workflow/tasks/failed/

    Используй следующий свободный номер TSK-XXX.

    ### 5. Создай task.md
    Создай директорию и файл:
    .memory-base/workflow/tasks/active/TSK-XXX/task.md

    ## Формат task.md

    ```yaml
    ---
    id: TSK-XXX
    title: {краткое название}
    pipeline: feature | bugfix | refactor | docs | hotfix
    status: pending
    created_at: {ISO datetime}
    related_files:
      - {путь к файлу}
    impact:
      - api: {да/нет}
      - db: {да/нет}
      - frontend: {да/нет}
      - services: {да/нет}
    ---

    ## Описание
    {Подробное описание задачи}

    ## Acceptance Criteria
    - [ ] {критерий 1}
    - [ ] {критерий 2}

    ## Контекст
    {Найденная информация о кодовой базе}
    ```

    ## Выход
    После создания верни:
    - Task ID
    - Pipeline type
    - Список связанных файлов
    - Путь к task.md
```

После получения результата от субагента:
1. Покажи пользователю:
   ```
   Task ID: TSK-XXX
   Pipeline: {type}
   Связанные файлы:
   - file1.py
   - file2.py
   Путь: .memory-base/workflow/tasks/active/TSK-XXX/task.md
   ```
2. Спроси: "Запустить pipeline {type}? (да/нет)"
3. При подтверждении — выполни `/run TSK-XXX`
