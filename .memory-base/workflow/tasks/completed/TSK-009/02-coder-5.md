---
agent: coder
task_id: TSK-009
subtask: 5
subtask_name: "Компоненты Cafes"
status: completed
next: null
created_at: 2025-12-06T22:15:00+03:00
files_changed:
  - path: frontend_mini_app/src/components/Manager/CafeList.tsx
    action: created
  - path: frontend_mini_app/src/components/Manager/CafeForm.tsx
    action: created
---

## Реализация

Созданы два компонента для управления кафе в менеджерском интерфейсе.

### 1. CafeList.tsx

**Функциональность:**
- Отображает список всех кафе (активных и неактивных) через hook `useCafes(false)`
- Каждое кафе отображается в виде карточки с информацией:
  - Название
  - Описание (если есть)
  - ID
  - Статус (активно/неактивно) в виде badge
- Кнопки управления:
  - "Редактировать" - вызывает callback `onEdit(cafe)`
  - "Активировать"/"Деактивировать" - переключает статус через PATCH `/cafes/{id}/status`
  - "Удалить" - удаляет кафе через DELETE `/cafes/{id}` с подтверждением

**Обработка состояний:**
- Loading state - показывает "Загрузка кафе..." с анимацией пульса
- Error state - отображает ошибку в красной карточке
- Empty state - показывает "Кафе не найдены"
- Processing state - отключает кнопки во время операций, показывает "..."

**Дизайн:**
- Карточки: `bg-white/5 backdrop-blur-md border border-white/10 rounded-lg`
- Hover effect: `hover:bg-white/10`
- Status badge активный: `bg-green-500/20 text-green-400`
- Status badge неактивный: `bg-red-500/20 text-red-400`
- Кнопка "Редактировать": `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- Кнопка "Активировать": `bg-green-500/20 text-green-400 border border-green-500/30`
- Кнопка "Деактивировать": `bg-yellow-500/20 text-yellow-400 border border-yellow-500/30`
- Кнопка "Удалить": `bg-red-500/20 text-red-400 border border-red-500/30`

**Интеграция:**
- Использует `mutate("/cafes")` для автоматического обновления списка после операций
- Поддерживает callback `onEdit` для интеграции с формой редактирования

### 2. CafeForm.tsx

**Функциональность:**
- Универсальная форма для создания и редактирования кафе
- Два режима: `mode: "create" | "edit"`
- Поля формы:
  - **Название** (обязательное) - text input
  - **Описание** (опциональное) - textarea

**Валидация:**
- Название обязательно (не может быть пустым)
- Trim пробелов по краям
- Пустое описание отправляется как `null`

**Логика сохранения:**
- Create mode: POST `/cafes` с payload `{ name, description }`
- Edit mode: PATCH `/cafes/{id}` с payload `{ name, description }`
- После успеха:
  - Вызывается `mutate("/cafes")` для обновления списка
  - Форма очищается
  - Вызывается callback `onSubmit()`

**Props:**
```typescript
interface CafeFormProps {
  mode: "create" | "edit";
  initialData?: Cafe;      // Данные для режима редактирования
  onSubmit?: () => void;   // Callback после успешного сохранения
  onCancel?: () => void;   // Callback для отмены
}
```

**Обработка состояний:**
- Error state - показывает ошибку в красной карточке над формой
- Submitting state - отключает кнопки, показывает "Сохранение..."
- `useEffect` для обновления полей при изменении `initialData`

**Дизайн:**
- Форма: `bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6`
- Input поля: `bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2`
- Focus состояние: `focus:border-[#A020F0] focus:ring-1 focus:ring-[#A020F0]`
- Placeholder: `placeholder-gray-400`
- Textarea: `resize-none` для фиксированной высоты
- Кнопка "Сохранить": `bg-gradient-to-r from-[#8B23CB] to-[#A020F0]`
- Кнопка "Отмена": `bg-white/10 border border-white/20 text-gray-300`

**Доступность:**
- Labels с htmlFor для связи с input
- Обязательные поля помечены красной звездочкой
- Attribute `required` на обязательных полях

### Типы

Используются существующие типы из `@/lib/api/types.ts`:

```typescript
interface Cafe {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}
```

### Интеграция в /manager

Компоненты готовы к интеграции в страницу `/manager` → таб "Кафе":

```tsx
// Пример использования
const [editingCafe, setEditingCafe] = useState<Cafe | null>(null);
const [showCreateForm, setShowCreateForm] = useState(false);

// Создание
{showCreateForm && (
  <CafeForm
    mode="create"
    onSubmit={() => setShowCreateForm(false)}
    onCancel={() => setShowCreateForm(false)}
  />
)}

// Редактирование
{editingCafe && (
  <CafeForm
    mode="edit"
    initialData={editingCafe}
    onSubmit={() => setEditingCafe(null)}
    onCancel={() => setEditingCafe(null)}
  />
)}

// Список
<CafeList onEdit={(cafe) => setEditingCafe(cafe)} />
```

### API endpoints используемые

- `GET /cafes?active_only=false` - через `useCafes(false)` hook (уже существует)
- `POST /cafes` - создание кафе
- `PATCH /cafes/{id}` - редактирование кафе
- `PATCH /cafes/{id}/status` - изменение статуса
- `DELETE /cafes/{id}` - удаление кафе

### Зависимости

- `useCafes` hook из `@/lib/api/hooks.ts` (уже реализован)
- `apiRequest` из `@/lib/api/client.ts` (уже реализован)
- `mutate` из `swr` для ревалидации
- Типы `Cafe` из `@/lib/api/types.ts`

### Следующие шаги

Компоненты готовы к использованию. Для полной интеграции в менеджерскую панель нужно:

1. Импортировать компоненты в `/manager/page.tsx`
2. Добавить состояние для управления формами (create/edit)
3. Добавить кнопку "Создать кафе" в начале таба
4. Обработать показ/скрытие форм

Все компоненты используют дизайн-систему проекта и готовы к мобильному использованию в Telegram Mini App.
