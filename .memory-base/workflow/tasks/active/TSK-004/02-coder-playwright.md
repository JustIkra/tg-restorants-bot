---
agent: coder
task_id: TSK-004
subtask: 2.1
subtask_name: "Playwright Setup"
status: completed
next: null
created_at: 2025-12-06T14:30:00
files_changed:
  - path: frontend_mini_app/package.json
    action: modified
  - path: frontend_mini_app/playwright.config.ts
    action: created
  - path: frontend_mini_app/tests/e2e/.gitkeep
    action: created
---

## Реализация

Настроил Playwright для E2E тестирования Telegram Mini App (Next.js 16 + React 19).

### Описание изменений

Выполнена подзадача 2.1 из Фазы 2 (E2E Testing) согласно архитектурному плану:
- Добавлены зависимости Playwright
- Создан конфигурационный файл
- Настроена директория для E2E тестов
- Добавлены npm scripts для запуска тестов

### Изменения

#### 1. `frontend_mini_app/package.json` (modified)

**Добавлена зависимость:**
```json
"devDependencies": {
  "@playwright/test": "^1.40.0",
  ...
}
```

**Добавлены scripts:**
```json
"scripts": {
  "test:e2e": "playwright test",
  "test:e2e:ui": "playwright test --ui",
  "test:e2e:report": "playwright show-report"
}
```

- `test:e2e` - запуск тестов в headless режиме
- `test:e2e:ui` - запуск тестов в UI режиме (удобно для отладки)
- `test:e2e:report` - просмотр HTML отчета после запуска

#### 2. `frontend_mini_app/playwright.config.ts` (created)

Создан конфигурационный файл Playwright с настройками:

**Основные параметры:**
- `testDir: './tests/e2e'` - директория с E2E тестами
- `fullyParallel: true` - параллельный запуск тестов
- `retries: process.env.CI ? 2 : 0` - 2 повтора в CI, 0 локально
- `workers: process.env.CI ? 1 : undefined` - 1 worker в CI, auto локально
- `reporter: 'html'` - HTML отчет о результатах

**Настройки браузера:**
- `baseURL: 'http://localhost:3000'` - базовый URL приложения
- `trace: 'on-first-retry'` - запись trace при первом retry (для отладки)
- `projects: ['chromium']` - тестируем в Desktop Chrome

**Web Server:**
- `command: 'npm run dev'` - автоматически запускает dev server перед тестами
- `url: 'http://localhost:3000'` - проверка готовности сервера
- `reuseExistingServer: !process.env.CI` - переиспользование сервера локально

**Обоснование выбора параметров:**

1. **fullyParallel: true** - ускоряет выполнение, т.к. E2E тесты будут независимые
2. **retries в CI** - нестабильность сети/окружения в CI требует retry
3. **trace: 'on-first-retry'** - экономит место, но сохраняет отладочную информацию
4. **Только chromium** - для начала достаточно одного браузера, можно добавить firefox/webkit позже
5. **webServer** - автоматизация запуска dev server упрощает локальную разработку

#### 3. `frontend_mini_app/tests/e2e/.gitkeep` (created)

Создана пустая директория для E2E тестов с `.gitkeep`, чтобы она сохранилась в git.

## Следующие шаги

После выполнения этой подзадачи готова инфраструктура для E2E тестирования. Следующие этапы:

1. **Установка зависимостей:**
   ```bash
   cd frontend_mini_app
   npm install
   npx playwright install chromium
   ```

2. **2.2 E2E Test Planning** (через Playwright MCP Agent):
   - Supervisor должен запустить `playwright-test-planner` субагент
   - Субагент создаст comprehensive test plan для основных user flows

3. **2.3 E2E Test Generation** (через Playwright MCP Agent):
   - Supervisor должен запустить `playwright-test-generator` субагент
   - Субагент сгенерирует автотесты на основе test plan

4. **2.4 E2E Test Execution & Healing**:
   - Запуск тестов: `npm run test:e2e`
   - При падениях - `playwright-test-healer` субагент

## Технические детали

### Директорная структура

После настройки:
```
frontend_mini_app/
├── playwright.config.ts      ← конфигурация Playwright
├── tests/
│   └── e2e/                   ← E2E тесты (пока пусто)
│       └── .gitkeep
├── package.json               ← обновлен (Playwright зависимости и scripts)
└── ...
```

После генерации тестов (2.3):
```
frontend_mini_app/
├── tests/
│   └── e2e/
│       ├── .gitkeep
│       ├── auth.spec.ts            ← авторизация
│       ├── order-flow.spec.ts      ← создание заказа
│       ├── cafe-selection.spec.ts  ← выбор кафе
│       ├── combo-selection.spec.ts ← выбор комбо
│       └── ...
```

### Использование

**Локальная разработка:**
```bash
# Запуск всех тестов
npm run test:e2e

# UI режим (интерактивная отладка)
npm run test:e2e:ui

# Запуск конкретного теста
npx playwright test tests/e2e/order-flow.spec.ts

# Отладка теста с видимым браузером
npx playwright test --debug

# Просмотр HTML отчета
npm run test:e2e:report
```

**CI/CD:**
```yaml
# GitHub Actions example
- name: Install dependencies
  run: npm ci
- name: Install Playwright browsers
  run: npx playwright install chromium --with-deps
- name: Run E2E tests
  run: npm run test:e2e
- name: Upload test report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Проверка результата

Для проверки корректности настройки:

```bash
cd frontend_mini_app
npm install
npx playwright install chromium
npm run test:e2e
```

Ожидаемый результат:
- Playwright успешно установлен
- Конфигурация валидна
- Dev server запускается автоматически
- Тесты не найдены (директория пуста) - это OK на данном этапе
- Можно создать простой smoke test для проверки

## Соответствие требованиям

Подзадача 2.1 из architect plan выполнена полностью:

- [x] Добавить зависимости в `package.json` - `@playwright/test: ^1.40.0`
- [x] Создать `playwright.config.ts` с корректными настройками
- [x] Добавить scripts в `package.json` - test:e2e, test:e2e:ui, test:e2e:report
- [x] Создать директорию `tests/e2e/` с `.gitkeep`

## Зависимости

**Не требуется:** Эта подзадача не зависит от других подзадач и может выполняться независимо.

**Блокирует:**
- 2.2 E2E Test Planning (требует playwright.config.ts)
- 2.3 E2E Test Generation (требует tests/e2e/ директорию)

## Потенциальные проблемы и решения

1. **Telegram WebApp SDK может не работать в Playwright**
   - Решение: Mock telegram.initData в тестах или использовать seed script

2. **Backend API может быть недоступен при тестах**
   - Решение: В playwright.config.ts можно добавить второй webServer для backend
   - Альтернатива: Mock API через MSW (Mock Service Worker)

3. **Тесты могут быть медленными из-за SSR**
   - Решение: Использовать `waitForLoadState('networkidle')` в тестах
   - Решение: Настроить timeouts в config

## Примечания

- Конфигурация оптимизирована для Next.js 16 dev server
- При переходе на production build потребуется изменить `webServer.command` на `npm run build && npm start`
- Для Telegram Mini App может потребоваться настройка viewport размеров под мобильные устройства
- Playwright MCP tools будут использованы в следующих подзадачах (2.2, 2.3, 2.4)
