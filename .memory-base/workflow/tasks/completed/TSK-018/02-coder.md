---
agent: coder
task_id: TSK-018
status: completed
created_at: 2025-12-07T03:30:00Z
files_changed:
  - frontend_mini_app/src/lib/api/hooks.ts
  - frontend_mini_app/src/components/Manager/CafeForm.tsx
---

## Изменения

### frontend_mini_app/src/lib/api/hooks.ts

Исправлено 14 mutation hooks для синхронного обновления UI после создания/изменения/удаления записей:

1. **useCreateUser** (строка 359) - добавлен `await` и `{ revalidate: true }`
2. **useUpdateUserAccess** (строка 375) - добавлен `await` и `{ revalidate: true }`
3. **useDeleteUser** (строка 388) - добавлен `await` и `{ revalidate: true }`
4. **useCreateCafe** (строка 404) - добавлен `await` (revalidate уже был)
5. **useUpdateCafe** (строка 417) - добавлен `await` (revalidate уже был)
6. **useDeleteCafe** (строка 430) - добавлен `await` (revalidate уже был)
7. **useUpdateCafeStatus** (строка 445) - добавлен `await` (revalidate уже был)
8. **useCreateCombo** (строка 462) - добавлен `await` и `{ revalidate: true }`
9. **useUpdateCombo** (строка 475) - добавлен `await` и `{ revalidate: true }`
10. **useDeleteCombo** (строка 488) - добавлен `await` и `{ revalidate: true }`
11. **useCreateMenuItem** (строка 504) - добавлен `await` и `{ revalidate: true }`
12. **useUpdateMenuItem** (строка 517) - добавлен `await` и `{ revalidate: true }`
13. **useDeleteMenuItem** (строка 530) - добавлен `await` и `{ revalidate: true }`
14. **useUpdateBalanceLimit** (строки 573-574) - добавлен `await` и `{ revalidate: true }` для обоих mutate

**Паттерн изменения:**

```typescript
// Было:
mutate("/endpoint");

// Стало:
await mutate("/endpoint", undefined, { revalidate: true });
```

Для cafe hooks (которые используют filter function):
```typescript
// Было:
mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });

// Стало:
await mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });
```

### frontend_mini_app/src/components/Manager/CafeForm.tsx

Исправлен прямой вызов `mutate()` в handleSubmit (строка 64):

```typescript
// Было:
mutate("/cafes");

// Стало:
await mutate("/cafes", undefined, { revalidate: true });
```

## Объяснение исправления

**Root cause:** `mutate()` из `useSWRConfig()` по умолчанию НЕ возвращает Promise и НЕ делает revalidation (повторный запрос к API). Он только помечает cache как stale.

**Решение:** Использовать `await mutate(key, undefined, { revalidate: true })` для:
1. Принудительного запроса к API (revalidation)
2. Ожидания обновления cache перед закрытием формы
3. Синхронного обновления UI

## Тестирование

Для проверки:
1. Открыть менеджерскую панель (`/manager`)
2. Создать запись в любой форме:
   - Пользователь (User)
   - Кафе (Cafe)
   - Комбо (Combo)
   - Блюдо (MenuItem)
3. После создания запись должна **сразу появиться** в списке
4. Попробовать редактирование и удаление - список должен обновляться сразу

## Следующие шаги

Рекомендуется запустить **Tester** агента для:
1. Написания E2E тестов для проверки UI обновления
2. Тестирования всех форм создания/редактирования/удаления
3. Проверки что форма закрывается только ПОСЛЕ обновления списка
