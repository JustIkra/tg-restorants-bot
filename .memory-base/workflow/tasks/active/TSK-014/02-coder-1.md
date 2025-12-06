---
agent: coder
task_id: TSK-014
subtask: 1
subtask_name: "FortuneWheel hydration fix"
status: completed
next: null
created_at: 2025-12-07T14:30:00+0300
files_changed:
  - path: frontend_mini_app/src/app/FortuneWheel/page.tsx
    action: modified
---

## Реализация

Исправлена проблема React Hydration Mismatch в компоненте FortuneWheel. Проблема возникала из-за того, что сервер и клиент рендерили разное начальное состояние кнопки спина колеса.

### Проблема

- Сервер: `disabled={null}` и текст "Крутить колесо" (localStorage недоступен)
- Клиент: `disabled={true}` и "Доступно через: 23:59:17" (читает из localStorage)
- Причина: время до следующего спина вычислялось в initializer функции useState

### Решение

1. **Нейтральное начальное состояние** — установлены значения по умолчанию:
   - `canSpin: false`
   - `timeLeft: 0`
   - Добавлен флаг `mounted: false`

2. **Перенос логики localStorage в useEffect** — вся работа с localStorage теперь выполняется после монтирования компонента на клиенте

3. **Условный рендеринг** — кнопка показывает "Крутить колесо" пока компонент не смонтирован (`!mounted || canSpin`)

### Изменения

#### `frontend_mini_app/src/app/FortuneWheel/page.tsx`

**1. Убраны initializer функции из useState (строки 30-32):**

До:
```tsx
const [canSpin, setCanSpin] = useState(() => {
  if (typeof window !== 'undefined') {
    const lastSpin = localStorage.getItem("lastSpin");
    if (lastSpin) {
      const nextSpinTime = parseInt(lastSpin) + ONE_DAY;
      const now = Date.now();
      return now >= nextSpinTime;
    }
  }
  return true;
});
const [timeLeft, setTimeLeft] = useState(() => {
  if (typeof window !== 'undefined') {
    const lastSpin = localStorage.getItem("lastSpin");
    if (lastSpin) {
      const nextSpinTime = parseInt(lastSpin) + ONE_DAY;
      const now = Date.now();
      if (now < nextSpinTime) {
        return nextSpinTime - now;
      }
    }
  }
  return 0;
});
```

После:
```tsx
const [mounted, setMounted] = useState(false);
const [canSpin, setCanSpin] = useState(false);
const [timeLeft, setTimeLeft] = useState(0);
```

**2. Добавлен useEffect для инициализации состояния (строки 43-58):**

```tsx
useEffect(() => {
  setMounted(true);
  const lastSpin = localStorage.getItem("lastSpin");
  if (lastSpin) {
    const nextSpinTime = parseInt(lastSpin) + ONE_DAY;
    const now = Date.now();
    if (now >= nextSpinTime) {
      setCanSpin(true);
    } else {
      setCanSpin(false);
      setTimeLeft(nextSpinTime - now);
    }
  } else {
    setCanSpin(true);
  }
}, []);
```

**3. Обновлена логика рендеринга кнопки (строки 249-253):**

До:
```tsx
{isSpinning
  ? "Крутим..."
  : canSpin
  ? "Крутить колесо"
  : `Доступно через: ${formatTime(timeLeft)}`}
```

После:
```tsx
{isSpinning
  ? "Крутим..."
  : !mounted || canSpin
  ? "Крутить колесо"
  : `Доступно через: ${formatTime(timeLeft)}`}
```

## Примечания

- **SSR-совместимость**: Сервер всегда рендерит кнопку с текстом "Крутить колесо" и `disabled={false}` (т.к. `canSpin` инициализируется как `false`, но кнопка показывает нейтральное состояние пока `!mounted`)
- **Клиентская гидратация**: После монтирования useEffect проверяет localStorage и обновляет состояние. Если нужно показать таймер — кнопка перерендерится на клиенте
- **Нет race conditions**: Флаг `mounted` гарантирует, что во время первого рендера на клиенте компонент отобразит то же состояние, что и на сервере
- **Поведение сохранено**: После монтирования компонент работает так же, как и раньше — показывает таймер или кнопку спина в зависимости от localStorage

## Критерии приёмки

- [x] Кнопка "Крутить колесо" рендерится одинаково на сервере и клиенте
- [x] Нет hydration mismatch warnings
- [x] Таймер показывается корректно после монтирования
- [x] localStorage доступ перенесен в useEffect
- [x] SSR рендерит нейтральное состояние
