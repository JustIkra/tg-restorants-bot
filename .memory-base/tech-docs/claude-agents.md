# Claude Agents

Claude Agents — это специализированные AI-агенты, которые работают через Claude Code CLI и используют MCP (Model Context Protocol) для автоматизации задач.

В проекте используются два типа агентов:
1. **Workflow агенты** — для разработки кода (в `.memory-base/workflow/`)
2. **Playwright агенты** — для тестирования веб-приложений (в `.claude/agents/`)

---

## Что такое Claude Agents

Claude Agents — это markdown-файлы с YAML frontmatter, которые описывают специализированных агентов для выполнения конкретных задач. Каждый агент имеет:

- **name** — уникальное имя агента
- **description** — описание задач, которые агент выполняет
- **tools** — список MCP-инструментов, доступных агенту
- **model** — модель Claude (например, `sonnet`)
- **color** — цвет для UI (опционально)
- **prompt** — инструкции для агента (в теле markdown-файла)

### Формат файла агента

```markdown
---
name: my-agent
description: Краткое описание агента
tools: Read, Write, Bash
model: sonnet
color: blue
---

Промпт для агента с инструкциями...
```

---

## Playwright Agents

В проекте настроены 3 Playwright-агента для автоматизации тестирования веб-приложений.

### 1. Playwright Test Planner

**Файл:** `.claude/agents/playwright-test-planner.md`

**Роль:** Создает комплексный тест-план для веб-приложения

**Что делает:**
1. Навигирует по веб-приложению через браузер
2. Исследует интерфейс, формы, интерактивные элементы
3. Проектирует тест-сценарии:
   - Happy path (нормальное поведение пользователя)
   - Edge cases (граничные условия)
   - Error handling (обработка ошибок)
4. Создает документированный тест-план в markdown

**Доступные tools:**
- Базовые: `Read`, `Glob`, `Grep`, `LS`
- Браузер: `browser_navigate`, `browser_click`, `browser_type`, `browser_snapshot`, `browser_take_screenshot`
- Planner: `planner_setup_page`, `planner_save_plan`

**Когда использовать:**
- Нужно создать тест-план для нового веб-приложения
- Нужно расширить coverage существующих тестов
- Нужно проверить все user flows приложения

**Пример использования:**

Запуск агента происходит через Claude Code CLI. Агент автоматически откроет браузер, исследует приложение и создаст тест-план.

**Результат:**
- Markdown-файл с тест-планом (обычно `specs/plan.md`)
- Структурированные тест-сценарии с описанием шагов
- Seed файл для настройки начального состояния

---

### 2. Playwright Test Generator

**Файл:** `.claude/agents/playwright-test-generator.md`

**Роль:** Генерирует Playwright тесты по тест-плану

**Что делает:**
1. Читает тест-план (созданный Test Planner)
2. Для каждого сценария:
   - Настраивает начальное состояние страницы
   - Выполняет шаги вручную через браузер
   - Записывает действия в лог
   - Генерирует TypeScript-код теста
3. Сохраняет тесты в файлы `tests/`

**Доступные tools:**
- Базовые: `Read`, `Glob`, `Grep`, `LS`
- Браузер: `browser_click`, `browser_type`, `browser_navigate`, `browser_snapshot`, `browser_verify_*`
- Generator: `generator_setup_page`, `generator_read_log`, `generator_write_test`

**Когда использовать:**
- После создания тест-плана
- Нужно автоматизировать тест-сценарии
- Нужно создать end-to-end тесты

**Пример генерации:**

Для тест-плана:
```markdown
### 1. Adding New Todos
**Seed:** `tests/seed.spec.ts`

#### 1.1 Add Valid Todo
**Steps:**
1. Click in the "What needs to be done?" input field
2. Type "Buy groceries"
3. Press Enter
```

Агент сгенерирует:
```typescript
// spec: specs/plan.md
// seed: tests/seed.spec.ts

test.describe('Adding New Todos', () => {
  test('Add Valid Todo', async ({ page }) => {
    // 1. Click in the "What needs to be done?" input field
    await page.getByPlaceholder('What needs to be done?').click();

    // 2. Type "Buy groceries"
    await page.getByPlaceholder('What needs to be done?').fill('Buy groceries');

    // 3. Press Enter
    await page.getByPlaceholder('What needs to be done?').press('Enter');
  });
});
```

**Результат:**
- TypeScript файлы с Playwright тестами
- Один файл = один тест-сценарий
- Комментарии перед каждым шагом
- Best practices из лога

---

### 3. Playwright Test Healer

**Файл:** `.claude/agents/playwright-test-healer.md`

**Роль:** Отлаживает и исправляет falling Playwright тесты

**Что делает:**
1. Запускает все тесты через `test_run`
2. Для каждого failing теста:
   - Запускает в debug режиме (`test_debug`)
   - Анализирует ошибку
   - Исследует состояние страницы через snapshot
   - Определяет root cause (селекторы, timing, assertions)
   - Исправляет код теста
   - Перезапускает тест для проверки
3. Повторяет до тех пор, пока тест не пройдет

**Доступные tools:**
- Базовые: `Read`, `Edit`, `Write`, `Glob`, `Grep`, `LS`
- Браузер: `browser_snapshot`, `browser_console_messages`, `browser_network_requests`, `browser_generate_locator`
- Tests: `test_list`, `test_run`, `test_debug`

**Когда использовать:**
- Тесты падают после изменений в коде
- Нужно обновить селекторы
- Нужно исправить timing issues
- Нужно улучшить reliability тестов

**Принципы работы:**
- Систематический подход к debugging
- Фиксит одну ошибку за раз
- Использует Playwright best practices
- Не использует deprecated API (например, `networkidle`)
- Если тест нельзя исправить — помечает как `test.fixme()`

**Результат:**
- Исправленные тесты
- Обновленные селекторы
- Улучшенная стабильность тестов
- Документация изменений

---

## Workflow агентов vs Playwright агентов

| Аспект | Workflow агенты | Playwright агенты |
|--------|----------------|-------------------|
| **Расположение** | `.memory-base/workflow/prompts/roles/` | `.claude/agents/` |
| **Формат** | Markdown с промптами | Markdown с YAML frontmatter |
| **Запуск** | Через Supervisor + Task tool | Напрямую через Claude Code CLI |
| **Задачи** | Разработка кода (architect, coder, tester...) | Автоматизация тестирования веб-приложений |
| **MCP tools** | Общие (Read, Write, Bash, Grep...) | Playwright-специфичные (browser_*, test_*) |
| **Результаты** | `.memory-base/workflow/tasks/` | Тесты в `tests/`, планы в `specs/` |

---

## Создание нового агента

### 1. Создайте файл агента

```markdown
---
name: my-custom-agent
description: Описание того, что агент делает
tools: Read, Write, Bash
model: sonnet
color: purple
---

Промпт для агента.

Вы — эксперт в [область].

Ваш workflow:
1. Шаг 1
2. Шаг 2
3. Шаг 3

Принципы:
- Принцип 1
- Принцип 2
```

### 2. Выберите tools

Доступные tools зависят от установленных MCP-серверов:

**Базовые:**
- `Read`, `Write`, `Edit` — работа с файлами
- `Glob`, `Grep` — поиск файлов
- `Bash` — выполнение команд
- `LS` — список файлов

**Playwright MCP:**
- `browser_*` — взаимодействие с браузером
- `test_*` — запуск и debug тестов
- `planner_*` — создание тест-планов
- `generator_*` — генерация тестов

**Context7 MCP:**
- `mcp__context7__resolve-library-id`
- `mcp__context7__get-library-docs`

### 3. Определите workflow

Опишите четкую последовательность действий агента. Используйте примеры (как в Playwright агентах).

### 4. Сохраните в нужную директорию

- **Workflow агенты** → `.memory-base/workflow/prompts/roles/{agent}.md`
- **Специализированные агенты** → `.claude/agents/{agent}.md`

---

## Best Practices

### Для Playwright агентов

1. **Test Planner:**
   - Исследуйте приложение полностью перед созданием плана
   - Используйте `browser_snapshot` вместо скриншотов
   - Создавайте независимые сценарии (могут запускаться в любом порядке)
   - Покрывайте happy path, edge cases, error handling

2. **Test Generator:**
   - Следуйте структуре тест-плана
   - Используйте комментарии перед каждым шагом
   - Один файл = один тест
   - Применяйте best practices из лога

3. **Test Healer:**
   - Фиксите одну ошибку за раз
   - Используйте `browser_generate_locator` для надежных селекторов
   - Не используйте deprecated API
   - Помечайте нерешаемые тесты как `test.fixme()`

### Для workflow агентов

1. Следуйте принципу единственной ответственности
2. Используйте базовые инструкции из `base.md`
3. Четко определяйте границы роли
4. Документируйте результаты в YAML frontmatter
5. Не выполняйте работу других агентов

---

## Примеры использования

### Создать тест-план для веб-приложения

```
Пользователь: Создай тест-план для приложения на http://localhost:3000
```

→ Claude запустит **playwright-test-planner** агента
→ Агент исследует приложение и создаст `specs/plan.md`

### Сгенерировать тесты по плану

```
Пользователь: Сгенерируй тесты из specs/plan.md
```

→ Claude запустит **playwright-test-generator** агента
→ Агент создаст тесты в `tests/`

### Исправить падающие тесты

```
Пользователь: Почини failing тесты
```

→ Claude запустит **playwright-test-healer** агента
→ Агент найдет и исправит ошибки

---

## Ссылки

- [Playwright Documentation](https://playwright.dev/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/build-with-claude/claude-code)
- [Workflow агенты](./../workflow/config.yaml)
