---
agent: reviewer
task_id: TSK-004
status: completed
next: tester
created_at: 2025-12-06T15:00:00
---

## Review Result: CHANGES REQUESTED

Code review для Batch 1 (Frontend Integration) завершен. Обнаружены проблемы разной степени критичности, требующие исправления перед переходом к тестированию.

## Проверенные компоненты

**Coder #1 (Frontend API Integration):**
- ✅ `frontend_mini_app/src/app/page.tsx` - замена mock данных на API
- ✅ `frontend_mini_app/src/components/CategorySelector/CategorySelector.tsx` - поддержка string category IDs
- ✅ `frontend_mini_app/.env.example` - API URL конфигурация

**Coder #2 (CORS Configuration):**
- ✅ `backend/.env.example` - CORS настройки

**Coder #3 (Docker Compose Frontend):**
- ✅ `frontend_mini_app/Dockerfile` - multi-stage build
- ✅ `frontend_mini_app/.dockerignore` - исключение файлов
- ✅ `docker-compose.yml` - frontend service

---

## Critical Issues

### 1. `page.tsx:33-37` - Неправильное использование useMemo для side effects

**Файл:** `frontend_mini_app/src/app/page.tsx`

**Проблема:**
```tsx
// Line 33-37
useMemo(() => {
  if (cafes.length > 0 && activeCafeId === null) {
    setActiveCafeId(cafes[0].id);
  }
}, [cafes, activeCafeId]);
```

**Причина:** `useMemo` предназначен для мемоизации вычислений, а не для side effects (вызов `setActiveCafeId`). Это нарушает React guidelines и может привести к непредсказуемому поведению.

**Решение:** Использовать `useEffect`:
```tsx
useEffect(() => {
  if (cafes.length > 0 && activeCafeId === null) {
    setActiveCafeId(cafes[0].id);
  }
}, [cafes, activeCafeId]);
```

**Ссылки:**
- React docs: "useMemo is for performance optimization, not side effects"
- Use useEffect for state updates based on dependency changes

---

### 2. `page.tsx:118` - Некорректное условие isLoading

**Файл:** `frontend_mini_app/src/app/page.tsx`

**Проблема:**
```tsx
// Line 117
const isLoading = cafesLoading || (activeCafeId && (menuLoading || combosLoading));
```

**Причина:** Логическая ошибка - `activeCafeId` может быть `0` (валидный ID), и условие вернет `false`. Правильная проверка: `activeCafeId !== null`.

**Решение:**
```tsx
const isLoading = cafesLoading || (activeCafeId !== null && (menuLoading || combosLoading));
```

**Impact:** При выборе кафе с ID=0 не будет отображаться loading state.

---

### 3. `Dockerfile:28` - Отсутствует копирование `.next/static`

**Файл:** `frontend_mini_app/Dockerfile`

**Проблема:**
```dockerfile
# Line 25
COPY --from=builder /app/.next ./.next
```

**Причина:** При использовании `npm start` Next.js требует `.next/standalone` для production режима. Текущая конфигурация копирует всю `.next/` директорию, что неоптимально.

**Решение:** Использовать standalone build для минимального размера образа:
```dockerfile
# В production stage:
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
```

**И обновить `next.config.ts`:**
```typescript
export default {
  output: 'standalone',
};
```

**Альтернативное решение (если standalone не нужен):** Текущий Dockerfile работает, но образ будет больше. Для dev режима это приемлемо.

**Приоритет:** Medium (работает, но не оптимально для production)

---

### 4. `docker-compose.yml:108-110` - Volumes конфликтуют с production build

**Файл:** `docker-compose.yml`

**Проблема:**
```yaml
# Lines 107-110
volumes:
  - ./frontend_mini_app:/app
  - /app/node_modules
  - /app/.next
```

**Причина:** Монтирование всей директории `./frontend_mini_app:/app` перезаписывает собранные файлы из Docker build. Это работает для dev режима (с hot reload), но не для production build.

**Решение для development:**
- Изменить CMD в Dockerfile на `npm run dev` для hot reload
- Текущие volumes корректны

**Решение для production:**
- Удалить volumes полностью (использовать только собранный образ)
- Использовать отдельный `docker-compose.prod.yml`

**Текущее состояние:** Сейчас используется `npm start` (production server), но с dev volumes. Это несоответствие.

**Рекомендация:**
1. Для dev режима: изменить CMD на `npm run dev` в docker-compose через `command`
2. Или убрать volume `./frontend_mini_app:/app` для production build

**Приоритет:** High (несоответствие между build и runtime режимом)

---

## Important Issues

### 5. `page.tsx:24` - Нет обработки extras в UI

**Файл:** `frontend_mini_app/src/app/page.tsx`

**Проблема:**
```tsx
// Line 24
const { data: extraItems, error: extrasError, isLoading: extrasLoading } = useMenu(activeCafeId, "extra");
```

Данные fetching для extras есть, но они **не используются** нигде в UI.

**Причина:** ExtrasSection компонент не рендерится на странице.

**Решение:** Добавить ExtrasSection в рендер:
```tsx
{activeCafeId && (
  <>
    {/* ... existing menu ... */}

    {/* Extras section */}
    {extrasLoading ? (
      <div className="flex items-center justify-center py-4">
        <FaSpinner className="text-white animate-spin" />
        <span className="ml-2 text-white">Загрузка дополнений...</span>
      </div>
    ) : extraItems && extraItems.length > 0 ? (
      <ExtrasSection extras={extraItems} cart={cart} addToCart={addToCart} removeFromCart={removeFromCart} />
    ) : null}
  </>
)}
```

**Impact:** Пользователь не может заказать extras (напитки, десерты и т.д.).

---

### 6. `page.tsx:156` - Fallback для activeCafeId может быть 0

**Файл:** `frontend_mini_app/src/app/page.tsx`

**Проблема:**
```tsx
// Line 156
<CafeSelector cafes={cafes} activeCafeId={activeCafeId || 0} onCafeClick={handleCafeClick} />
```

**Причина:** Если `activeCafeId === null`, передается `0`. Но `0` может быть валидным ID кафе из БД.

**Решение:**
```tsx
<CafeSelector cafes={cafes} activeCafeId={activeCafeId ?? -1} onCafeClick={handleCafeClick} />
```

Или обновить `CafeSelector` для поддержки `null`:
```tsx
interface CafeSelectorProps {
  cafes: Cafe[];
  activeCafeId: number | null;
  onCafeClick: (id: number) => void;
}
```

**Приоритет:** Medium (маловероятно что ID=0, но технически некорректно)

---

### 7. `.env.example` - Отсутствует комментарий для копирования в `.env.local`

**Файл:** `frontend_mini_app/.env.example`

**Проблема:** Нет инструкций для разработчика о том, как использовать этот файл.

**Решение:** Добавить комментарий в начало файла:
```bash
# Frontend Environment Variables
# Copy this file to .env.local for local development:
#   cp .env.example .env.local
# Then update the values as needed.

# Backend API Configuration
# Development (local backend)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
...
```

**Приоритет:** Low (documentation improvement)

---

### 8. `backend/.env.example` - CORS_ORIGINS требует специального парсинга

**Файл:** `backend/.env.example`

**Проблема:**
```bash
# Line 26
CORS_ORIGINS=["http://localhost:3000","http://frontend:3000"]
```

Это JSON array в виде строки. Pydantic парсит это корректно **только** если тип поля `list[str]` с правильным валидатором.

**Проверка:**
- ✅ `src/config.py:18` - тип `list[str]` корректный
- ✅ Pydantic Settings автоматически парсит JSON строку в список

**Рекомендация:** Добавить комментарий в `.env.example` для ясности:
```bash
# CORS
# Development: Multiple origins for local dev and Docker networking
# IMPORTANT: This is a JSON array as a string, parsed automatically by Pydantic
# For Docker Compose: frontend service hostname is "frontend"
# For local development: localhost
CORS_ORIGINS=["http://localhost:3000","http://frontend:3000"]
```

**Приоритет:** Low (работает, но требует пояснения)

---

## Security Review

### ✅ No hardcoded secrets
- JWT_SECRET_KEY требует изменения в production (комментарий есть)
- Telegram Bot Token из env
- Gemini API keys из env

### ✅ CORS правильно ограничен
- Development: localhost:3000, frontend:3000
- Production пример с комментарием
- Не используется wildcard `*`

### ✅ Dockerfile безопасен
- Используется non-root user (node)
- Multi-stage build минимизирует attack surface
- No secrets в образе

### ✅ Input validation
- Pydantic модели валидируют данные на backend
- TypeScript типы на frontend (runtime validation может быть улучшена)

---

## Performance Review

### ✅ useMemo используется правильно (кроме issue #1)
- Мемоизация `cafes`, `categories`, `dishes` корректна
- Предотвращает лишние перерендеры

### ⚠️ Docker образ не оптимизирован
- См. Issue #3 - рекомендуется standalone build для production
- Текущий размер образа будет больше чем необходимо

### ✅ SWR caching работает
- Автоматический кэш данных
- Revalidation on focus
- Dedupe запросов

### ⚠️ Нет debounce для category switching
- При быстром переключении категорий могут быть лишние фильтрации
- Рекомендуется добавить useMemo для filteredDishes (уже есть ✅)

---

## Architecture Compliance

### ✅ Соответствует плану Architect (01-architect.md)

**Подзадача 1.1 (Frontend API Integration):**
- ✅ Mock данные удалены
- ✅ SWR hooks используются корректно
- ✅ State management обновлен
- ✅ Loading states добавлены
- ✅ Error handling добавлен

**Подзадача 1.2 (CORS Configuration):**
- ✅ CORS_ORIGINS обновлен в `.env.example`
- ✅ Поддержка localhost и Docker hostname
- ✅ Production пример добавлен

**Подзадача 1.3 (Docker Compose Frontend):**
- ✅ Dockerfile создан с multi-stage build
- ✅ .dockerignore настроен
- ✅ Frontend service добавлен в docker-compose.yml
- ✅ Networking настроен (lunch-bot-network)
- ✅ Volumes для dev режима

### ⚠️ Отклонения от плана

**Issue #4:** Docker volumes конфликтуют с production build
- План предполагал dev режим с volumes
- Но Dockerfile делает production build (`npm run build`)
- Несоответствие между build и runtime

---

## Code Style Compliance

### TypeScript/React (frontend_mini_app/)

**✅ Соответствует code-style.md:**
- ✅ Functional components с React.FC
- ✅ TypeScript интерфейсы для props
- ✅ "use client" directive для интерактивных компонентов
- ✅ Импорты организованы правильно (React → иконки → компоненты)
- ✅ Tailwind utility classes используются
- ✅ Цветовая схема проекта соблюдена (#130F30, #A020F0, #7B6F9C)

**⚠️ Отклонения:**
- Issue #1: `useMemo` используется для side effects (должен быть `useEffect`)
- `CategorySelector.tsx`: типы `number | string` корректны для поддержки API

### Python (backend/)

**✅ Соответствует code-style.md:**
- ✅ Pydantic Settings для config
- ✅ Type hints (`list[str]`, встроенный синтаксис Python 3.13+)
- ✅ Нет использования `typing` модуля (используется встроенный синтаксис)
- ✅ `snake_case` для переменных
- ✅ `UPPER_CASE` для констант (env variables)

### Docker

**✅ Best practices:**
- ✅ Multi-stage build
- ✅ Alpine base image (минимальный размер)
- ✅ .dockerignore настроен
- ✅ Layer caching оптимизирован (package*.json копируется отдельно)

**⚠️ Рекомендации:**
- Issue #3: Использовать standalone build для минимального образа

---

## Error Handling Review

### Frontend (`page.tsx`)

**✅ Хороший error handling:**
- ✅ Combined error state (Line 120)
- ✅ Error banner с иконкой (Lines 135-143)
- ✅ Graceful degradation (пустые состояния)

**✅ Loading states:**
- ✅ Skeleton loaders для cafes (Lines 147-158)
- ✅ Spinners для категорий и меню (Lines 165-169, 179-183)
- ✅ Текстовые индикаторы ("Загрузка...")

**✅ Empty states:**
- ✅ "Нет доступных кафе" (Line 153)
- ✅ "Меню пока не добавлено" (Line 186)
- ✅ "Выберите кафе, чтобы увидеть меню" (Line 197)

### Backend (CORS)

**✅ Validation:**
- ✅ `validate_secrets` проверяет JWT_SECRET_KEY length (config.py:38-42)
- ✅ Pydantic автоматически валидирует типы

---

## Testing Gaps

**Что не покрыто (но не критично для review):**
- Unit тесты для новых изменений в `page.tsx`
- Integration тест для CORS (будет в подзадаче 1.4)
- E2E тесты (будет в Phase 2)

**Рекомендация:** Запустить существующие тесты после исправления issues:
```bash
# Frontend
cd frontend_mini_app && npm test

# Backend
cd backend && pytest
```

---

## Summary

### Code Quality: 7/10

**Strengths:**
- ✅ Правильное использование SWR hooks
- ✅ Хороший error handling и loading states
- ✅ Корректная интеграция с API
- ✅ Безопасная Docker конфигурация
- ✅ Соответствие code style guide
- ✅ CORS правильно настроен

**Weaknesses:**
- ❌ Неправильное использование `useMemo` для side effects (critical)
- ❌ Docker volumes конфликтуют с production build (important)
- ❌ Extras не отображаются в UI (important)
- ⚠️ Некорректное условие `isLoading` (medium)
- ⚠️ Неоптимальный Dockerfile для production (medium)

### Blockers

**Критичные проблемы, требующие исправления:**
1. Issue #1: Заменить `useMemo` на `useEffect` для auto-select кафе
2. Issue #4: Определиться с dev/prod режимом Docker (использовать `npm run dev` для dev)
3. Issue #5: Добавить ExtrasSection в UI

**Важные проблемы (рекомендуется исправить):**
4. Issue #2: Исправить условие `isLoading`
5. Issue #6: Исправить fallback для `activeCafeId`

**Можно отложить (не блокирует тестирование):**
6. Issue #3: Оптимизация Dockerfile для production
7. Issue #7-8: Улучшение документации в `.env.example`

---

## Recommended Actions

### Для Supervisor:

1. **Вернуть задачу Coder #1** с issues #1, #2, #5, #6
2. **Вернуть задачу Coder #3** с issue #4
3. После исправлений - повторный review
4. Если все OK - переход к подзадаче 1.4 (Integration test)

### Для Coder:

**Coder #1 (Frontend API Integration) - Исправления:**
```tsx
// 1. Заменить useMemo на useEffect (Line 33-37)
useEffect(() => {
  if (cafes.length > 0 && activeCafeId === null) {
    setActiveCafeId(cafes[0].id);
  }
}, [cafes, activeCafeId]);

// 2. Исправить isLoading (Line 117)
const isLoading = cafesLoading || (activeCafeId !== null && (menuLoading || combosLoading));

// 3. Добавить ExtrasSection в UI (после MenuSection)
import ExtrasSection from "@/components/ExtrasSection/ExtrasSection";
// ... render ExtrasSection с extraItems

// 4. Исправить fallback для activeCafeId (Line 156)
<CafeSelector cafes={cafes} activeCafeId={activeCafeId ?? -1} onCafeClick={handleCafeClick} />
```

**Coder #3 (Docker Compose Frontend) - Исправления:**
```yaml
# docker-compose.yml - изменить command для dev режима
frontend:
  # ... existing config ...
  command: npm run dev  # ← Добавить эту строку для hot reload в dev режиме
  volumes:
    - ./frontend_mini_app:/app
    - /app/node_modules
    - /app/.next
```

---

## Files Reviewed

**Frontend:**
- `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/app/page.tsx` - CHANGES REQUESTED
- `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/CategorySelector/CategorySelector.tsx` - APPROVED
- `/Users/maksim/git_projects/tg_bot/frontend_mini_app/.env.example` - APPROVED (minor suggestions)

**Backend:**
- `/Users/maksim/git_projects/tg_bot/backend/.env.example` - APPROVED (minor suggestions)
- `/Users/maksim/git_projects/tg_bot/backend/src/config.py` - APPROVED

**Docker:**
- `/Users/maksim/git_projects/tg_bot/frontend_mini_app/Dockerfile` - APPROVED (optimization suggestions)
- `/Users/maksim/git_projects/tg_bot/frontend_mini_app/.dockerignore` - APPROVED
- `/Users/maksim/git_projects/tg_bot/docker-compose.yml` - CHANGES REQUESTED

---

## Next Steps

После исправления critical и important issues:
1. Повторный review (возможно быстрый spot check)
2. Переход к Integration Testing (подзадача 1.4)
3. Запуск Docker Compose и проверка работоспособности
4. E2E тестирование (Phase 2)
