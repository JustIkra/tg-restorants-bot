---
agent: coder
task_id: TSK-017
status: completed
next: tester
created_at: 2025-12-07T12:30:00
files_changed:
  - path: frontend_mini_app/src/components/Manager/CafeList.tsx
    action: modified
  - path: frontend_mini_app/src/components/Manager/ReportsList.tsx
    action: modified
  - path: frontend_mini_app/src/components/Manager/MenuManager.tsx
    action: modified
---

## Реализация

Исправлена проблема с отображением кафе в панели менеджера (/manager). Проблема заключалась в неправильном использовании хука `useCafes()` в трех компонентах менеджера.

### Root Cause

Хук `useCafes()` имеет следующую сигнатуру:
```typescript
useCafes(shouldFetch = true, activeOnly = true)
```

В компонентах использовался вызов `useCafes(false)`, где:
- `shouldFetch=false` — это блокировало выполнение запроса к API
- `activeOnly` не передавался, используя дефолтное значение `true`

Результат: SWR хук не выполнял запрос, и данные никогда не загружались.

### Изменения

#### 1. CafeList.tsx (строка 14)
**До:**
```tsx
const { data: cafes, error, isLoading } = useCafes(false);
```

**После:**
```tsx
const { data: cafes, error, isLoading } = useCafes(true, false);
```

**Параметры:**
- `shouldFetch=true` — включает выполнение запроса
- `activeOnly=false` — получает все кафе (активные и неактивные)

#### 2. ReportsList.tsx (строка 14)
**До:**
```tsx
const { data: cafes } = useCafes(false);
```

**После:**
```tsx
const { data: cafes } = useCafes(true, false);
```

Та же логика: включаем запрос и получаем все кафе для dropdown выбора кафе при создании отчета.

#### 3. MenuManager.tsx (строка 24)
**До:**
```tsx
const { data: cafes, isLoading: cafesLoading } = useCafes(false);
```

**После:**
```tsx
const { data: cafes, isLoading: cafesLoading } = useCafes(true, false);
```

Та же логика: включаем запрос и получаем все кафе для dropdown выбора кафе при управлении меню.

### Результат

После изменений:
- CafeList будет отображать все кафе (активные и неактивные)
- ReportsList сможет выбирать любое кафе для создания отчета
- MenuManager сможет выбирать любое кафе для редактирования меню

Все компоненты теперь выполняют запрос к `/cafes` API endpoint при монтировании.

## Примечания

- В компонентах менеджера требуется доступ ко всем кафе (активным и неактивным), поэтому используется `activeOnly=false`
- Для пользовательских компонентов (не менеджерских) следует использовать `useCafes(true, true)` или `useCafes()` (дефолтные значения) для получения только активных кафе
- Изменения минимальны и затрагивают только вызов хука, без изменения логики компонентов
