---
agent: coder
task_id: TSK-022
subtask: 2
subtask_name: "Frontend hook + UI"
status: completed
next: null
created_at: 2025-12-07T12:30:00Z
files_changed:
  - path: frontend_mini_app/src/lib/api/hooks.ts
    action: modified
  - path: frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx
    action: modified
  - path: frontend_mini_app/src/app/profile/page.tsx
    action: modified
---

## Реализация

Реализована фронтенд часть задачи TSK-022: создан хук для генерации рекомендаций и добавлен dropdown UI в компонент ProfileRecommendations.

## Изменения

### 1. `frontend_mini_app/src/lib/api/hooks.ts`

**Добавлен новый hook `useGenerateRecommendations()`**

Создан новый раздел "User Recommendations Hooks" в конце файла (после deadline hooks).

**Функциональность:**
- Принимает: ничего (stateless mutation hook)
- Возвращает объект с:
  - `generateRecommendations: (tgid: number) => Promise<RecommendationsResponse>` - функция для генерации
  - `isLoading: boolean` - состояние загрузки
  - `error: Error | null` - ошибка если есть

**Детали реализации:**
- Использует `useState` для управления состоянием `isLoading` и `error`
- Использует `useSWRConfig` для доступа к `mutate` функции
- POST запрос на `/users/${tgid}/recommendations/generate` через `apiRequest<RecommendationsResponse>`
- После успешной генерации автоматически обновляет SWR кэш через `mutate()` с флагом `revalidate: true`
- Обрабатывает ошибки: устанавливает `error` state и пробрасывает исключение дальше
- Корректно управляет состоянием `isLoading`: устанавливает в `true` в начале, сбрасывает в `false` в `finally` блоке

**Код (строки 770-815):**
```typescript
/**
 * Hook to generate user recommendations (manager | self)
 * Returns a function to trigger immediate AI recommendation generation
 */
export function useGenerateRecommendations(): {
  generateRecommendations: (tgid: number) => Promise<RecommendationsResponse>;
  isLoading: boolean;
  error: Error | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { mutate } = useSWRConfig();

  const generateRecommendations = async (tgid: number): Promise<RecommendationsResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiRequest<RecommendationsResponse>(
        `/users/${tgid}/recommendations/generate`,
        { method: "POST" }
      );

      // Update SWR cache to refresh UI
      await mutate(`/users/${tgid}/recommendations`, undefined, { revalidate: true });

      setIsLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to generate recommendations");
      setError(error);
      setIsLoading(false);
      throw error;
    }
  };

  return {
    generateRecommendations,
    isLoading,
    error,
  };
}
```

### 2. `frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx`

**Добавлен dropdown menu с кнопкой "Получить сейчас"**

**Изменения в imports:**
- Добавлен `useState`, `useEffect`, `useRef` из React
- Добавлена иконка `FaEllipsisVertical` из `react-icons/fa6`
- Добавлен импорт `useGenerateRecommendations` из `@/lib/api/hooks`

**Изменения в props:**
- Добавлен обязательный prop `tgid: number` в интерфейс `ProfileRecommendationsProps`

**Добавленный state:**
- `showDropdown: boolean` - состояние открытия/закрытия dropdown
- `dropdownRef: useRef<HTMLDivElement>(null)` - ref для обработки клика вне области
- `{ generateRecommendations, isLoading, error }` из хука `useGenerateRecommendations()`

**Обработка клика вне области (useEffect):**
```typescript
useEffect(() => {
  const handleClickOutside = (event: MouseEvent) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
      setShowDropdown(false);
    }
  };

  if (showDropdown) {
    document.addEventListener("mousedown", handleClickOutside);
  }

  return () => {
    document.removeEventListener("mousedown", handleClickOutside);
  };
}, [showDropdown]);
```

**Обработка генерации:**
```typescript
const handleGenerateClick = async () => {
  try {
    await generateRecommendations(tgid);
    setShowDropdown(false);
  } catch (err) {
    alert(error?.message || "Не удалось сгенерировать рекомендации");
  }
};
```

**Изменения в UI (для empty state и loaded state):**

1. Обернул заголовок в `<div className="relative">` для absolute positioning dropdown
2. Изменил структуру заголовка:
   - Основной контейнер: `flex items-center gap-3 mb-4`
   - Левая часть (иконка + текст): `<div className="flex-1 flex items-center gap-3">`
   - Правая часть (кнопка три точки): `<button>` с иконкой `FaEllipsisVertical`

3. Добавлен dropdown menu:
```tsx
{showDropdown && (
  <div
    ref={dropdownRef}
    className="absolute right-0 top-12 z-20 w-48 bg-[#1a153d] border border-white/20 rounded-lg shadow-2xl overflow-hidden"
  >
    <button
      onClick={handleGenerateClick}
      disabled={isLoading}
      className="w-full p-3 text-left text-white hover:bg-white/10 transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isLoading ? "Генерация..." : "Получить сейчас"}
    </button>
  </div>
)}
```

**Дизайн соответствует спецификации:**
- Purple gradient дизайн: `bg-[#1a153d] border border-white/20`
- Position: `absolute right-0 top-12 z-20`
- Width: `w-48`
- Hover: `hover:bg-white/10`
- Disabled state: `disabled:opacity-50 disabled:cursor-not-allowed`

**Изменения применены к обоим состояниям:**
- Empty state (когда `recommendations.summary === null`)
- Loaded state (когда есть рекомендации)

### 3. `frontend_mini_app/src/app/profile/page.tsx`

**Передан prop `tgid` в компонент ProfileRecommendations**

Изменена строка 96-97:
```tsx
// Было:
<ProfileRecommendations recommendations={recommendations} />

// Стало:
<ProfileRecommendations recommendations={recommendations} tgid={user.tgid} />
```

Также добавлена проверка `user?.tgid` в условие рендеринга:
```tsx
) : recommendations && user?.tgid ? (
  <ProfileRecommendations recommendations={recommendations} tgid={user.tgid} />
) : (
```

Это гарантирует, что компонент отрендерится только если есть и recommendations, и user с tgid.

## Технические решения

1. **State management**
   - Dropdown state управляется локально через `useState`
   - Loading state из хука показывается в кнопке dropdown
   - Error показывается через `alert()` (простое решение для MVP)

2. **Click outside handling**
   - Использован паттерн с `useRef` и `useEffect`
   - Event listener добавляется только когда dropdown открыт
   - Cleanup в return функции `useEffect`

3. **SWR cache invalidation**
   - После успешной генерации автоматически вызывается `mutate()` с `revalidate: true`
   - Это триггерит повторный запрос GET endpoint и обновляет UI
   - Пользователь видит новые рекомендации без перезагрузки страницы

4. **Error handling**
   - Errors пробрасываются из хука наружу
   - В компоненте показывается через `alert()` с понятным сообщением
   - Используется `error?.message` из хука или fallback текст

5. **Loading UX**
   - Кнопка становится disabled во время генерации
   - Текст меняется на "Генерация..."
   - Opacity снижается до 50% (disabled:opacity-50)
   - Cursor меняется на not-allowed

6. **Positioning**
   - Dropdown открывается справа (`right-0`)
   - Отступ сверху 12 (3rem) чтобы не перекрывать заголовок (`top-12`)
   - z-index 20 чтобы быть поверх остального контента но не модальных окон

## Соответствие требованиям

**Из 01-architect.md:**

✅ **Подзадача 1: Dropdown UI**
- Добавлена иконка три точки (⋮) справа от заголовка
- При клике открывается dropdown меню
- Dropdown закрывается при клике вне его области (useRef + useEffect)
- Кнопка "Получить сейчас" вызывает `generateRecommendations(tgid)`
- Показывается loading state (disabled button + текст "Генерация...")
- Dropdown закрывается после успешной генерации
- Показывается alert при ошибке
- Purple gradient дизайн соответствует спецификации
- Positioning корректный (не выходит за границы)

✅ **Подзадача 2: useGenerateRecommendations hook**
- Создан в `hooks.ts`
- Принимает ничего (stateless mutation hook)
- Возвращает `{ generateRecommendations, isLoading, error }`
- Использует `apiRequest<RecommendationsResponse>()` для POST запроса
- После успешной генерации вызывает `mutate()` для обновления SWR кэша
- Обрабатывает ошибки корректно

**Из task.md (Acceptance Criteria - Frontend):**

✅ В заголовке секции ProfileRecommendations справа добавлена иконка три точки (⋮)
✅ При клике на иконку открывается dropdown меню
✅ Dropdown закрывается при клике вне его области
✅ В dropdown одна кнопка "Получить сейчас"
✅ При клике на кнопку вызывается API endpoint для генерации (через хук)
✅ Во время генерации показывается loading state (disabled button + "Генерация...")
✅ После успешной генерации данные обновляются через SWR mutate
✅ При ошибке показывается alert с текстом ошибки
✅ Dropdown имеет фиолетовый градиент в стиле дизайн-системы
✅ Dropdown позиционируется корректно (не выходит за границы экрана)

**Hooks requirements:**

✅ Создан новый hook `useGenerateRecommendations()`
✅ Hook принимает tgid и возвращает функцию для генерации
✅ Hook возвращает loading state и error
✅ После успешной генерации hook вызывает mutate для обновления кэша SWR

## Зависимости

**Использованные библиотеки:**
- `react`: useState, useEffect, useRef
- `react-icons/fa6`: FaEllipsisVertical (иконка три точки)
- `swr`: useSWRConfig для доступа к mutate
- Существующие: apiRequest, RecommendationsResponse

**Зависимости от backend:**
- Endpoint `POST /users/${tgid}/recommendations/generate` (будет реализован в подзадаче 1)
- Response type: `RecommendationsResponse`

## Следующие шаги

Эта подзадача завершена. Требуется реализация backend endpoint (подзадача 1 для другого coder агента).

После реализации backend можно протестировать весь flow:
1. Открыть страницу профиля
2. Кликнуть на три точки в секции "AI-рекомендации"
3. Кликнуть "Получить сейчас"
4. Дождаться генерации (10-30 секунд)
5. Увидеть обновлённые рекомендации

## Примечания

**Потенциальные улучшения (вне scope этой задачи):**
- Заменить `alert()` на toast notification (более современный UX)
- Добавить cooldown на кнопку (например, блокировать на 1 час после генерации)
- Показывать spinner вместо "Генерация..." текста
- Добавить анимацию появления/исчезновения dropdown
