---
agent: coder
task_id: TSK-020
status: completed
next: reviewer
created_at: 2025-12-07T12:00:00Z
files_changed:
  - path: frontend_mini_app/src/lib/api/client.ts
    action: modified
  - path: frontend_mini_app/src/components/AccessRequestForm/AccessRequestForm.tsx
    action: created
  - path: frontend_mini_app/src/app/page.tsx
    action: modified
---

## Реализация

Реализован UI формы запроса доступа для незарегистрированных пользователей согласно архитектурному плану. Изменения включают:

1. **API client** — добавлена поддержка параметра `office` в функции `authenticateWithTelegram`
2. **AccessRequestForm компонент** — создана форма для запроса доступа с указанием офиса
3. **Auth flow в page.tsx** — реализована multi-state логика авторизации с различными экранами

### Изменения

#### `frontend_mini_app/src/lib/api/client.ts`

**Добавлен параметр `office`:**
- Функция `authenticateWithTelegram` теперь принимает необязательный параметр `office?: string`
- Office передаётся в request body через spread оператор: `...(office && { office })`
- Сохраняется обратная совместимость — если office не передан, работает как раньше

**Код:**
```typescript
export async function authenticateWithTelegram(
  initData: string,
  office?: string
): Promise<{ access_token: string; user: User }> {
  const response = await apiRequest<{ access_token: string; user: User }>(
    "/auth/telegram",
    {
      method: "POST",
      body: JSON.stringify({
        init_data: initData,
        ...(office && { office })
      }),
    }
  );
  // ...
}
```

#### `frontend_mini_app/src/components/AccessRequestForm/AccessRequestForm.tsx`

**Создан новый компонент формы запроса доступа:**

**Props:**
- `name: string` — имя пользователя из Telegram (readonly)
- `username: string | null` — username из Telegram (readonly, опционально)
- `onSubmit: (office: string) => Promise<void>` — callback для отправки запроса
- `onSuccess: () => void` — callback при успешной отправке

**Функциональность:**
- Форма с тремя полями:
  - Имя (readonly, заполнено из props)
  - Username (readonly, заполнено из props, показывается только если есть)
  - Офис (input, обязательное поле)
- Валидация: офис не должен быть пустым
- Loading state при submit с анимацией spinner
- Обработка и отображение ошибок
- Кнопка submit disabled если офис пустой или идёт отправка

**Стилизация:**
- Glassmorphism дизайн: `bg-white/5 backdrop-blur-md border border-white/10`
- Purple gradient для кнопки и иконки: `from-[#8B23CB] to-[#A020F0]`
- Background: `bg-[#130F30]`
- Иконки: FaUser, FaBuilding, FaPaperPlane, FaSpinner из react-icons/fa6
- Центрированный layout с максимальной шириной 28rem
- Responsive дизайн с padding и адаптивными размерами

**UX:**
- Информативный заголовок "Запрос доступа"
- Описание "Заполните форму для получения доступа к приложению"
- Подсказка внизу "После отправки запроса дождитесь одобрения менеджера"
- Красный asterisk (*) у обязательного поля office
- Placeholder "Введите название офиса"

#### `frontend_mini_app/src/app/page.tsx`

**Добавлен AuthState тип:**
```typescript
type AuthState = "loading" | "needs_request" | "success" | "pending" | "rejected" | "error";
```

**Новые состояния:**
- `authState: AuthState` — текущее состояние авторизации
- `telegramUserData: { name, username } | null` — данные пользователя Telegram для формы

**Обновлена логика useEffect для авторизации:**

1. **Получение Telegram user data:**
   - Вызов `getTelegramUser()` для получения данных пользователя
   - Формирование полного имени: `first_name + last_name`
   - Сохранение в `telegramUserData`

2. **Определение начального состояния:**
   - Проверка `localStorage.getItem("access_request_sent")`
   - Проверка `localStorage.getItem("jwt_token")`
   - Если нет токена И нет флага → `setAuthState("needs_request")` (показ формы)
   - Иначе → попытка авторизации через `authenticateWithTelegram(initData)`

3. **Обработка успешной авторизации:**
   - `setAuthState("success")`
   - Сохранение user в state и localStorage
   - Очистка флага `access_request_sent` при успехе

4. **Парсинг ошибок авторизации:**
   - `includes("Access request created")` или `includes("Access request pending")` → `"pending"`
   - `includes("Access request rejected")` → `"rejected"`
   - Иначе → `"error"` + сохранение сообщения в `authError`

**Добавлены handlers:**

1. **`handleAccessRequestSubmit(office: string)`:**
   - Получает `initData` через `getTelegramInitData()`
   - Вызывает `authenticateWithTelegram(initData, office)`
   - Устанавливает флаг `localStorage.setItem("access_request_sent", "true")`
   - Пробрасывает ошибки в компонент формы

2. **`handleAccessRequestSuccess()`:**
   - Устанавливает `setAuthState("pending")`

**Обновлён рендеринг — добавлены экраны:**

1. **AuthState === "needs_request":**
   - Проверка наличия `telegramUserData`
   - Если нет данных → экран ошибки "Не удалось получить данные Telegram"
   - Иначе → рендер `<AccessRequestForm />`

2. **AuthState === "pending":**
   - Glassmorphism экран с жёлто-оранжевой иконкой spinner
   - Заголовок "Ожидание одобрения"
   - Описание "Ваш запрос на доступ отправлен менеджеру..."
   - Подсказка "Вы получите уведомление, когда ваш запрос будет обработан"

3. **AuthState === "rejected":**
   - Красный glassmorphism экран с иконкой предупреждения
   - Заголовок "Доступ отклонён"
   - Описание "К сожалению, ваш запрос на доступ был отклонён менеджером"
   - Подсказка "Для получения дополнительной информации обратитесь к менеджеру"

4. **AuthState === "error":**
   - Аналогичный rejected экрану, но с заголовком "Ошибка авторизации"
   - Отображает конкретное сообщение ошибки из `authError`

5. **AuthState === "success":**
   - Существующий main app UI (без изменений)

**Важные детали:**
- `isAuthenticated` вычисляется как `authState === "success"`
- Все информационные экраны имеют background blur эффекты
- Центрированный layout с максимальной шириной для мобильных устройств
- Responsive дизайн с padding 1rem на мобильных

## UX Flow

**Новый пользователь (первый раз):**
1. Telegram initData проверяется
2. Нет токена + нет флага `access_request_sent`
3. Показывается форма AccessRequestForm
4. Пользователь вводит офис и отправляет
5. Backend создаёт запрос с указанным офисом
6. Устанавливается флаг `access_request_sent`
7. Показывается pending screen

**Пользователь с pending запросом:**
1. Есть флаг `access_request_sent`, но нет токена
2. Попытка авторизации → 403 "pending"
3. Показывается pending screen

**Пользователь с rejected запросом:**
1. Попытка авторизации → 403 "rejected"
2. Показывается rejected screen

**Одобренный пользователь:**
1. Попытка авторизации → 200 + JWT
2. Флаг `access_request_sent` очищается
3. Показывается main app UI

## Примечания

### Технические решения

1. **localStorage флаг `access_request_sent`:**
   - Используется для определения "новый пользователь" vs "повторный заход"
   - Устанавливается после отправки формы
   - Очищается при успешной авторизации
   - Может быть очищен пользователем → форма покажется повторно (не критично для MVP)

2. **Парсинг error messages:**
   - Используется `includes()` вместо точного сравнения для гибкости
   - Fallback на general error state для неизвестных ошибок

3. **Получение Telegram user data:**
   - Функция `getTelegramUser()` возвращает данные пользователя из `WebApp.initDataUnsafe.user`
   - Используется только для предзаполнения формы
   - Реальная авторизация происходит через `initData` (безопасно)

### Соответствие требованиям

✅ **Пользователь может указать офис** — реализовано через форму
✅ **Чёткие UI states** — 6 различных экранов для всех сценариев
✅ **Graceful error handling** — обработка всех типов ошибок (403, 401, 500, network)
✅ **Минимальные изменения backend** — используется существующий API
✅ **Дизайн-система проекта** — glassmorphism, purple gradient, react-icons/fa6
✅ **Responsive дизайн** — адаптивные размеры и padding

### Ограничения

1. **localStorage флаг не идеален:**
   - Не синхронизируется между устройствами
   - Может быть очищен пользователем
   - **Митигация:** повторный показ формы не критичен, backend не создаст дубликат запроса

2. **Backend не валидирует офис:**
   - Пользователь может ввести любую строку
   - **Митигация:** менеджер может отклонить запрос с неправильным офисом

3. **Нет автообновления состояния:**
   - Пользователь должен перезагрузить приложение после одобрения
   - **Будущее улучшение:** Telegram notifications (TSK-015) или polling
