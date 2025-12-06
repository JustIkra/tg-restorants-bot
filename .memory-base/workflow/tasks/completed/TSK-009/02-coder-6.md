---
agent: coder
task_id: TSK-009
subtask: 6
subtask_name: "Menu Components"
status: completed
next: null
created_at: 2025-12-06T22:15:00+03:00
files_changed:
  - path: frontend_mini_app/src/components/Manager/MenuManager.tsx
    action: created
  - path: frontend_mini_app/src/components/Manager/ComboForm.tsx
    action: created
  - path: frontend_mini_app/src/components/Manager/MenuItemForm.tsx
    action: created
---

## Реализация

Созданы три React компонента для управления меню кафе в Telegram Mini App.

### 1. MenuManager.tsx

Главный компонент для управления меню кафе. Функциональность:

- **Выбор кафе**: Dropdown для выбора кафе из списка
- **Управление комбо-наборами**:
  - Список комбо с названием, категориями и ценой
  - Кнопки добавления, редактирования, удаления
  - Переключатель доступности (is_available)
- **Управление блюдами**:
  - Группировка блюд по категориям
  - Отображение названия, описания, цены
  - Кнопки редактирования, удаления
  - Переключатель доступности
- **Интеграция с API**: Используются хуки из `lib/api/hooks.ts`
- **Автоматическое обновление**: После каждой операции данные обновляются через `mutate()`

### 2. ComboForm.tsx

Форма создания/редактирования комбо-набора. Особенности:

- **Режимы**: create / edit
- **Поля**:
  - Название (текстовое поле)
  - Категории (чекбоксы): Первое, Салат, Второе, Десерт
  - Цена (числовое поле с шагом 0.01)
- **Валидация**: Проверка заполнения всех полей
- **Modal**: Полноэкранное модальное окно с размытым фоном
- **Дизайн**: Использует дизайн-систему проекта (glassmorphism, purple gradient)

### 3. MenuItemForm.tsx

Форма создания/редактирования блюда. Особенности:

- **Режимы**: create / edit
- **Поля**:
  - Название (текстовое поле)
  - Описание (textarea, необязательное)
  - Категория (dropdown): Первое, Салат, Второе, Дополнительно
  - Цена (числовое поле, только для категории "extra")
- **Динамическое отображение**: Поле цены показывается только для категории "Дополнительно"
- **Валидация**:
  - Обязательные поля: название, категория
  - Цена обязательна только для "extra"
- **Modal**: Полноэкранное модальное окно

## Дизайн-система

Все компоненты используют единую дизайн-систему:

- **Cards**: `bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4`
- **Price**: `text-[#A020F0] font-semibold`
- **Category badge**: `bg-white/10 text-gray-300 px-2 py-1 rounded text-sm`
- **Button primary**: `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- **Input**: `bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2`
- **Modal**: `bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl`

## Категории

Маппинг категорий API → UI:

- `soup` → "Первое"
- `salad` → "Салат"
- `main` → "Второе"
- `extra` → "Дополнительно" (для комбо) / "Десерт" (для комбо категорий)

## API интеграция

Используются хуки:

- `useCafes(false)` - получение всех кафе
- `useCombos(cafeId)` - получение комбо для кафе
- `useMenu(cafeId)` - получение блюд для кафе
- `useCreateCombo()` - создание комбо
- `useUpdateCombo()` - обновление комбо
- `useDeleteCombo()` - удаление комбо
- `useCreateMenuItem()` - создание блюда
- `useUpdateMenuItem()` - обновление блюда
- `useDeleteMenuItem()` - удаление блюда

## Файлы

1. `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/Manager/MenuManager.tsx` - главный компонент
2. `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/Manager/ComboForm.tsx` - форма комбо
3. `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/Manager/MenuItemForm.tsx` - форма блюда

## Статус

Все компоненты созданы и готовы к использованию. Хуки для CRUD операций уже существуют в `lib/api/hooks.ts`.
