---
agent: reviewer
task_id: TSK-018
status: CHANGES_REQUESTED
created_at: 2025-12-07T18:45:00Z
---

# Code Review: ConfirmDialog Component

## Verdict: CHANGES_REQUESTED

Компонент реализован в целом хорошо, но есть несколько критических и важных замечаний, которые необходимо исправить перед интеграцией.

---

## Findings

### Critical (блокируют)

1. **Утечка памяти в useConfirm hook**
   - **Файл:** `frontend_mini_app/src/hooks/useConfirm.tsx`
   - **Строка:** 36
   - **Проблема:** `setResolvePromise(() => resolve)` создаёт новую функцию при каждом вызове, но старые промисы могут не очищаться при быстрых последовательных вызовах
   - **Решение:** Добавить cleanup при размонтировании компонента или закрытии диалога без ответа
   ```typescript
   // Добавить cleanup в useEffect для ConfirmProvider
   useEffect(() => {
     return () => {
       if (resolvePromise) {
         resolvePromise(false);
       }
     };
   }, []);
   ```

2. **Missing cleanup в useEffect**
   - **Файл:** `frontend_mini_app/src/components/UI/ConfirmDialog.tsx`
   - **Строка:** 26-34
   - **Проблема:** ESC listener не учитывает зависимость от `onCancel`, что может привести к вызову устаревшей версии callback
   - **Решение:** Уже исправлено правильно - зависимости указаны корректно

### Major (нужно исправить)

3. **Множественные alert() остались в коде**
   - **Файлы:** CafeList.tsx, MenuManager.tsx, и другие
   - **Проблема:** В коде всё ещё используется браузерный `alert()` для отображения ошибок, что противоречит цели замены нативных диалогов
   - **Примеры:**
     - `frontend_mini_app/src/components/Manager/CafeList.tsx:31` - `alert('Ошибка: ...')`
     - `frontend_mini_app/src/components/Manager/MenuManager.tsx:45` - `alert("Ошибка при создании комбо")`
   - **Решение:** Создать отдельный хук `useToast` или `useAlert` для уведомлений об ошибках (не блокирующий диалог)

4. **Accessibility: Missing ARIA attributes**
   - **Файл:** `frontend_mini_app/src/components/UI/ConfirmDialog.tsx`
   - **Проблема:** Отсутствуют ARIA атрибуты для screen readers
   - **Решение:** Добавить:
   ```tsx
   <div
     role="alertdialog"
     aria-modal="true"
     aria-labelledby="confirm-dialog-title"
     aria-describedby="confirm-dialog-message"
     // ... existing classes
   >
     <h2 id="confirm-dialog-title" ...>{title}</h2>
     <p id="confirm-dialog-message" ...>{message}</p>
   ```

5. **Keyboard navigation: нет автофокуса на кнопках**
   - **Файл:** `frontend_mini_app/src/components/UI/ConfirmDialog.tsx`
   - **Проблема:** При открытии диалога фокус не переводится на кнопки, что плохо для accessibility
   - **Решение:** Добавить `autoFocus` на кнопку "Отмена" или использовать `useRef` + `useEffect` для управления фокусом
   ```tsx
   const cancelButtonRef = useRef<HTMLButtonElement>(null);

   useEffect(() => {
     if (isOpen && cancelButtonRef.current) {
       cancelButtonRef.current.focus();
     }
   }, [isOpen]);
   ```

6. **Focus trap отсутствует**
   - **Файл:** `frontend_mini_app/src/components/UI/ConfirmDialog.tsx`
   - **Проблема:** Пользователь может выйти TAB-ом за пределы диалога
   - **Решение:** Добавить библиотеку `focus-trap-react` или реализовать ручной focus trap

### Minor (рекомендации)

7. **Отсутствие Enter handler**
   - **Файл:** `frontend_mini_app/src/components/UI/ConfirmDialog.tsx`
   - **Проблема:** Нет обработки клавиши Enter для подтверждения
   - **Решение:** Добавить в useEffect обработку:
   ```tsx
   if (e.key === "Enter" && isOpen) {
     onConfirm();
   }
   ```

8. **Z-index hardcoded**
   - **Файл:** `frontend_mini_app/src/components/UI/ConfirmDialog.tsx`
   - **Строка:** 46
   - **Проблема:** `z-50` может конфликтовать с другими overlay компонентами
   - **Решение:** Вынести z-index в общие константы или использовать CSS переменные

9. **Анимация выхода отсутствует**
   - **Файл:** `frontend_mini_app/src/components/UI/ConfirmDialog.tsx`
   - **Проблема:** При закрытии диалог исчезает резко (`if (!isOpen) return null`)
   - **Решение:** Использовать state transitions для плавного закрытия (например, через библиотеку `framer-motion` или CSS transitions с задержкой unmount)

10. **Type safety: resolvePromise может быть null**
    - **Файл:** `frontend_mini_app/src/hooks/useConfirm.tsx`
    - **Строки:** 42-44, 50-52
    - **Проблема:** Проверка `if (resolvePromise)` повторяется в обоих handlers
    - **Решение:** Рефакторинг для устранения дублирования:
    ```tsx
    const resolveAndCleanup = useCallback((value: boolean) => {
      setIsOpen(false);
      resolvePromise?.(value);
      setResolvePromise(null);
    }, [resolvePromise]);

    const handleConfirm = useCallback(() => resolveAndCleanup(true), [resolveAndCleanup]);
    const handleCancel = useCallback(() => resolveAndCleanup(false), [resolveAndCleanup]);
    ```

11. **React 19: useCallback dependencies**
    - **Файл:** `frontend_mini_app/src/hooks/useConfirm.tsx`
    - **Проблема:** В React 19 compiler автоматически мемоизирует, `useCallback` может быть избыточным
    - **Рекомендация:** После перехода на React 19 production рассмотреть удаление `useCallback` (если React Compiler включен)

12. **Missing loading state**
    - **Файл:** `frontend_mini_app/src/components/UI/ConfirmDialog.tsx`
    - **Проблема:** Нет индикации загрузки, если async операция занимает время
    - **Решение:** Добавить optional `loading` prop для блокировки кнопок во время async операций

---

## Files Reviewed

### Created Files
- ✅ `frontend_mini_app/src/components/UI/ConfirmDialog.tsx` - **Issues found** (Accessibility, keyboard nav)
- ✅ `frontend_mini_app/src/hooks/useConfirm.tsx` - **Issues found** (Memory leak, type safety)

### Modified Files
- ✅ `frontend_mini_app/src/app/layout.tsx` - **OK** (Provider интеграция корректна)
- ✅ `frontend_mini_app/src/app/globals.css` - **OK** (Анимации добавлены правильно)
- ⚠️ `frontend_mini_app/src/components/Manager/CafeList.tsx` - **Issues** (alert() для ошибок)
- ⚠️ `frontend_mini_app/src/components/Manager/UserList.tsx` - **OK** (useConfirm использован правильно)
- ⚠️ `frontend_mini_app/src/components/Manager/MenuManager.tsx` - **Issues** (alert() для ошибок)

### Other Components Using useConfirm
- ✅ `frontend_mini_app/src/components/Manager/ReportsList.tsx` - **OK**
- ✅ `frontend_mini_app/src/components/Manager/RequestsList.tsx` - **OK**
- ✅ `frontend_mini_app/src/components/Manager/BalanceManager.tsx` - **OK** (но alert() для ошибок)
- ✅ `frontend_mini_app/src/components/Manager/UserRequestsList.tsx` - **OK**

---

## Code Quality Assessment

### TypeScript ✓ Good
- Полная типизация без `any`
- Корректные интерфейсы для Props
- Type safety в целом хорошая (есть пространство для улучшений в useConfirm)

### React Best Practices ⚠️ Needs Improvement
- ✅ Hooks используются правильно
- ✅ useEffect dependencies корректны
- ⚠️ Нет cleanup для resolvePromise
- ⚠️ Отсутствует focus management
- ⚠️ Нет анимации выхода

### Styling ✓ Good
- Tailwind классы корректны
- Дизайн соответствует существующему стилю приложения
- Градиенты и цвета согласованы с палитрой проекта
- Responsive дизайн не проверен (mobile viewport)

### UX ⚠️ Needs Improvement
- ✅ Анимации плавные (fadeIn, slideUp)
- ✅ ESC для отмены работает
- ✅ Backdrop click для отмены
- ⚠️ Нет обработки Enter для подтверждения
- ⚠️ Отсутствует focus management
- ⚠️ Нет focus trap
- ⚠️ Нет анимации закрытия

### Accessibility ❌ Critical Issues
- ❌ Отсутствуют ARIA атрибуты (`role`, `aria-modal`, `aria-labelledby`, etc.)
- ❌ Нет автофокуса на интерактивных элементах
- ❌ Нет focus trap (TAB выходит за пределы диалога)
- ⚠️ Keyboard navigation неполная (нет Enter handler)

### Security ✓ Good
- ✅ Нет XSS уязвимостей
- ✅ `dangerouslySetInnerHTML` не используется
- ✅ Props корректно экранируются React

### Integration ✓ Good
- ✅ Provider добавлен в layout корректно
- ✅ Все компоненты обновлены для использования useConfirm
- ⚠️ alert() для ошибок всё ещё используется (неконсистентность)

---

## Summary

**Общая оценка:** Компонент реализован **хорошо**, но требует **обязательных доработок** перед production.

### Сильные стороны:
1. Правильная архитектура (Context API + Promise-based API)
2. Хорошая типизация TypeScript
3. Чистый, читаемый код
4. Красивый дизайн, согласованный с приложением
5. Базовая keyboard navigation (ESC)

### Обязательно исправить (блокирует merge):
1. **Accessibility** - добавить ARIA атрибуты, focus management, focus trap
2. **Memory leak** - cleanup для resolvePromise
3. **Keyboard UX** - добавить Enter handler, автофокус

### Желательно исправить (не блокирует, но важно):
4. **Консистентность** - заменить alert() на toast notifications
5. **UX** - добавить анимацию закрытия
6. **Code quality** - рефакторинг resolveAndCleanup

### Можно отложить (tech debt):
7. Loading state для async операций
8. Z-index management через CSS variables
9. React 19 compiler optimization

---

## Next Steps

1. **Coder** должен исправить Critical и Major issues
2. После исправлений - повторный review
3. **Tester** должен проверить:
   - Keyboard navigation (ESC, Enter, TAB)
   - Screen reader compatibility
   - Mobile viewport
   - Race conditions при быстрых кликах
   - Memory leaks при множественных открытиях/закрытиях

---

## Code Examples

### Пример улучшенного ConfirmDialog с ARIA:

```tsx
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = "OK",
  cancelText = "Отмена",
  onConfirm,
  onCancel,
}) => {
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        onCancel();
      } else if (e.key === "Enter") {
        onConfirm();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onCancel, onConfirm]);

  // Auto-focus on cancel button
  useEffect(() => {
    if (isOpen && cancelButtonRef.current) {
      cancelButtonRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn"
      onClick={(e) => e.target === e.currentTarget && onCancel()}
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
    >
      <div className="relative w-full max-w-sm bg-gradient-to-b from-[#1E1B3A] to-[#130F30] rounded-2xl border border-white/10 shadow-2xl animate-slideUp">
        {/* Icon */}
        <div className="flex justify-center pt-6">
          <div className="w-16 h-16 flex items-center justify-center bg-yellow-500/10 rounded-full border border-yellow-500/20">
            <FaExclamationTriangle className="text-yellow-400 text-2xl" aria-hidden="true" />
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-4 text-center">
          <h2 id="confirm-dialog-title" className="text-xl font-bold text-white mb-3">
            {title}
          </h2>
          <p id="confirm-dialog-message" className="text-gray-300 text-sm leading-relaxed">
            {message}
          </p>
        </div>

        {/* Buttons */}
        <div className="px-6 pb-6 flex gap-3">
          <button
            ref={cancelButtonRef}
            onClick={onCancel}
            className="flex-1 px-4 py-3 bg-white/10 text-gray-300 font-medium rounded-lg hover:bg-white/20 transition-all border border-white/10"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-medium rounded-lg hover:opacity-90 transition-all shadow-lg shadow-[#8B23CB]/20"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};
```

### Пример улучшенного useConfirm с cleanup:

```tsx
export const ConfirmProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [options, setOptions] = useState<ConfirmOptions>({
    title: "",
    message: "",
  });
  const [resolvePromise, setResolvePromise] = useState<
    ((value: boolean) => void) | null
  >(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (resolvePromise) {
        resolvePromise(false);
      }
    };
  }, [resolvePromise]);

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    setOptions(options);
    setIsOpen(true);

    return new Promise<boolean>((resolve) => {
      setResolvePromise(() => resolve);
    });
  }, []);

  const resolveAndCleanup = useCallback((value: boolean) => {
    setIsOpen(false);
    resolvePromise?.(value);
    setResolvePromise(null);
  }, [resolvePromise]);

  const handleConfirm = useCallback(() => {
    resolveAndCleanup(true);
  }, [resolveAndCleanup]);

  const handleCancel = useCallback(() => {
    resolveAndCleanup(false);
  }, [resolveAndCleanup]);

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      <ConfirmDialog
        isOpen={isOpen}
        title={options.title}
        message={options.message}
        confirmText={options.confirmText}
        cancelText={options.cancelText}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </ConfirmContext.Provider>
  );
};
```

---

## Testing Recommendations

После исправления issues, Tester должен проверить:

### Functional Tests
1. ✅ Диалог открывается при вызове `confirm()`
2. ✅ Клик на "OK" возвращает `true`
3. ✅ Клик на "Отмена" возвращает `false`
4. ✅ ESC закрывает диалог с `false`
5. ✅ Enter подтверждает с `true`
6. ✅ Backdrop click закрывает с `false`

### Accessibility Tests
7. ✅ Screen reader корректно читает title и message
8. ✅ Фокус автоматически переводится на кнопку при открытии
9. ✅ TAB не выходит за пределы диалога (focus trap)
10. ✅ Keyboard navigation работает полностью

### Edge Cases
11. ✅ Быстрые последовательные вызовы confirm()
12. ✅ Вызов confirm() при уже открытом диалоге
13. ✅ Unmount компонента с открытым диалогом
14. ✅ Race conditions при async операциях

### Performance
15. ✅ Нет memory leaks при множественных открытиях/закрытиях
16. ✅ Анимации не лагают
17. ✅ Re-renders минимизированы

---

**Status:** CHANGES_REQUESTED
**Priority:** High
**Estimated fix time:** 2-3 hours
