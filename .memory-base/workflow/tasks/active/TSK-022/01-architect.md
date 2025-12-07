---
agent: architect
task_id: TSK-022
status: completed
next: coder
created_at: 2025-12-07T12:00:00Z
---

## Анализ

Задача: добавить dropdown меню в секцию "AI-рекомендации" на странице профиля для принудительной генерации рекомендаций через Gemini API.

### Контекст

**Существующие компоненты:**
- `ProfileRecommendations.tsx` — компонент отображения рекомендаций (строки 11-85)
- `useUserRecommendations()` — хук для получения рекомендаций через GET endpoint (hooks.ts:563-569)
- `GET /users/{tgid}/recommendations` — endpoint для чтения кэшированных рекомендаций (recommendations.py:21-79)
- `GeminiRecommendationService` — сервис генерации через Gemini API (client.py:21-254)
- `OrderStatsService` — сервис сбора статистики заказов (order_stats.py:10-244)
- Batch worker — ночная генерация рекомендаций в 03:00 (workers/recommendations.py:36-165)

**Технологии:**
- Frontend: React 19, Next.js 16, Tailwind CSS 4, TypeScript, SWR
- Backend: FastAPI, Python 3.13, Redis для кэширования
- Gemini API: генерация через API key pool с ротацией ключей

**Дизайн-система:**
- Purple gradient: `from-[#8B23CB] to-[#A020F0]`
- Semi-transparent cards: `bg-white/5 backdrop-blur-md border border-white/10`
- Hover effects: `hover:bg-white/10`

## Архитектурное решение

### Подход

Добавить **inline dropdown** в заголовок секции ProfileRecommendations с кнопкой "Получить сейчас" для принудительной генерации рекомендаций.

**Ключевые принципы:**
1. **Переиспользование кода** — использовать существующий GeminiRecommendationService из batch worker
2. **Авторизация** — та же логика что и для GET (manager | self)
3. **Кэширование** — результат попадает в тот же Redis ключ (`recommendations:user:{tgid}`)
4. **Валидация** — проверка минимум 5 заказов на backend
5. **UX** — показывать loading state, автоматически обновлять данные после генерации

### Изменения в API

#### Новый endpoint

```python
POST /api/v1/users/{tgid}/recommendations/generate
  Auth: manager | self
  Response: RecommendationsResponse
  Errors:
    - 403 Forbidden (не manager и не self)
    - 400 Bad Request (меньше 5 заказов)
    - 500 Internal Server Error (ошибка Gemini API)
```

**Схема ответа:**
```typescript
interface RecommendationsResponse {
  summary: string | null;
  tips: string[];
  stats: OrderStats;
  generated_at: string | null;
}
```

### Изменения в структуре данных

**Нет изменений в БД** — используем существующие таблицы и Redis кэш.

### Компоненты для изменения

**Frontend:**
1. `ProfileRecommendations.tsx` — добавить dropdown в заголовок
2. `hooks.ts` — новый хук `useGenerateRecommendations()`

**Backend:**
3. `routers/recommendations.py` — новый endpoint POST
4. Переиспользуем:
   - `services/order_stats.py` (без изменений)
   - `gemini/client.py` (без изменений)
   - `cache/redis_client.py` (без изменений)

## Подзадачи для Coder

### 1. Frontend: Добавить dropdown в ProfileRecommendations

**Файл:** `frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx`

**Действия:**
- Добавить state для управления dropdown: `showDropdown`, `isGenerating`
- Добавить useRef для обработки клика вне области
- Добавить useEffect для закрытия dropdown при клике снаружи
- Добавить иконку три точки (⋮) справа от заголовка "AI-рекомендации"
- Добавить dropdown меню с кнопкой "Получить сейчас"
- Вызывать `generateRecommendations()` при клике на кнопку
- Показывать loading state (disabled button + spinner) во время генерации
- Закрывать dropdown после успешной генерации
- Показывать alert при ошибке

**Зависимости:**
- `FaEllipsisVertical` из `react-icons/fa6` для иконки три точки
- `useGenerateRecommendations` hook (создать в hooks.ts)
- React hooks: `useState`, `useEffect`, `useRef`

**Дизайн dropdown:**
```tsx
// Пример структуры
<div className="absolute right-0 top-12 z-20 w-48 bg-[#1a153d] border border-white/20 rounded-lg shadow-2xl">
  <button
    onClick={handleGenerate}
    disabled={isGenerating}
    className="w-full p-3 text-left hover:bg-white/10 transition"
  >
    {isGenerating ? 'Генерация...' : 'Получить сейчас'}
  </button>
</div>
```

**Positioning:**
- Dropdown должен открываться справа под иконкой (не перекрывать заголовок)
- Использовать `absolute` positioning относительно родителя с `relative`
- z-index: 20 (не перекрывать модальные окна)

### 2. Frontend: Создать хук useGenerateRecommendations

**Файл:** `frontend_mini_app/src/lib/api/hooks.ts`

**Действия:**
- Создать новый hook `useGenerateRecommendations()`
- Принимает: ничего (stateless mutation hook)
- Возвращает: `{ generateRecommendations: (tgid: number) => Promise<RecommendationsResponse>, isLoading: boolean, error: Error | null }`
- Использовать `apiRequest<RecommendationsResponse>()` для POST запроса
- После успешной генерации вызвать `mutate()` для обновления кэша SWR
- Обрабатывать ошибки и устанавливать состояние error

**Пример:**
```typescript
export function useGenerateRecommendations() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { mutate } = useSWRConfig();

  const generateRecommendations = async (tgid: number): Promise<RecommendationsResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiRequest<RecommendationsResponse>(
        `/users/${tgid}/recommendations/generate`,
        { method: 'POST' }
      );

      // Update SWR cache
      await mutate(`/users/${tgid}/recommendations`, undefined, { revalidate: true });

      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to generate recommendations');
      setError(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return { generateRecommendations, isLoading, error };
}
```

**Зависимости:**
- `useSWRConfig` для доступа к mutate
- `apiRequest` из `./client`
- `RecommendationsResponse` из `./types`

### 3. Backend: Создать POST endpoint для генерации

**Файл:** `backend/src/routers/recommendations.py`

**Действия:**
- Добавить новый endpoint `@router.post("/{tgid}/recommendations/generate")`
- Dependency injection для:
  - `current_user: CurrentUser` (авторизация)
  - `db: AsyncSession` (для OrderStatsService)
- Проверить авторизацию: `current_user.role == "manager" or current_user.tgid == tgid`
- Получить статистику через `OrderStatsService.get_user_stats(tgid, days=30)`
- Проверить минимум 5 заказов: `stats["orders_count"] < 5` → raise 400
- Вызвать `get_recommendation_service().generate_recommendations(stats)`
- Сохранить результат в Redis через `set_cache()`
- Вернуть `RecommendationsResponse`
- Обработать ошибки Gemini API → raise 500

**Пример:**
```python
@router.post("/{tgid}/recommendations/generate", response_model=RecommendationsResponse)
async def generate_user_recommendations(
    tgid: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderStatsService, Depends(get_order_stats_service)],
) -> RecommendationsResponse:
    """
    Force generate AI recommendations for user.

    Triggers immediate Gemini API generation instead of waiting for batch job.
    Requires minimum 5 orders in last 30 days.

    Auth: manager | self
    """
    # Authorization check
    if current_user.role != "manager" and current_user.tgid != tgid:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get stats
    stats = await service.get_user_stats(tgid, days=30)

    # Validate minimum orders
    if stats["orders_count"] < 5:
        raise HTTPException(
            status_code=400,
            detail="Minimum 5 orders required for recommendations"
        )

    try:
        # Generate recommendations
        from ..gemini.client import get_recommendation_service

        gemini_service = get_recommendation_service()
        result = await gemini_service.generate_recommendations(stats)

        # Cache result (same as batch worker)
        cache_key = f"recommendations:user:{tgid}"
        cache_data = {
            "summary": result.get("summary"),
            "tips": result.get("tips", []),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        await set_cache(cache_key, json.dumps(cache_data), ttl=86400)

        # Return response
        return RecommendationsResponse(
            summary=result.get("summary"),
            tips=result.get("tips", []),
            stats=OrderStats(
                orders_last_30_days=stats["orders_count"],
                categories=stats["categories"],
                unique_dishes=stats["unique_dishes"],
                favorite_dishes=stats["favorite_dishes"],
            ),
            generated_at=cache_data["generated_at"],
        )

    except AllKeysExhaustedException as e:
        logger.error("All Gemini API keys exhausted", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Service temporarily unavailable. Please try again later."
        )
    except Exception as e:
        logger.error(f"Failed to generate recommendations for {tgid}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations"
        )
```

**Зависимости:**
- `get_current_user` из `..auth.dependencies`
- `get_recommendation_service` из `..gemini.client`
- `set_cache` из `..cache.redis_client`
- `OrderStats`, `RecommendationsResponse` из `..schemas.recommendations`
- `AllKeysExhaustedException` из `..gemini`

**Imports:**
```python
import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser, get_current_user
from ..cache.redis_client import get_cache, set_cache
from ..database import get_db
from ..gemini import AllKeysExhaustedException
from ..schemas.recommendations import OrderStats, RecommendationsResponse
from ..services.order_stats import OrderStatsService

import structlog
logger = structlog.get_logger(__name__)
```

## Риски и зависимости

### Риски

1. **Превышение лимитов Gemini API**
   - Пользователь может спамить кнопкой "Получить сейчас"
   - **Mitigation:**
     - Не добавляем rate limiting в этой задаче (можно добавить позже)
     - Показываем loading state чтобы избежать двойных кликов
     - При исчерпании ключей возвращаем понятное сообщение 500

2. **Долгое время генерации (10-30 секунд)**
   - Gemini API может медленно отвечать
   - **Mitigation:**
     - Показываем spinner/loading state
     - Timeout 30 секунд уже установлен в GeminiRecommendationService
     - При timeout возвращаем 500 с понятным сообщением

3. **Ошибки Gemini API**
   - Ключи могут быть исчерпаны или невалидны
   - **Mitigation:**
     - Автоматическая ротация ключей уже реализована в key_pool
     - При AllKeysExhaustedException возвращаем 500 + сообщение "попробуйте позже"
     - Логируем все ошибки для мониторинга

4. **Конфликты при одновременной генерации**
   - Batch worker может генерировать в тот же момент
   - **Mitigation:**
     - Redis cache атомарно перезаписывает ключ
     - Last write wins (это приемлемо для рекомендаций)

### Зависимости

**Внешние сервисы:**
- Redis (для кэширования)
- Gemini API (для генерации)

**Существующий код (без изменений):**
- `GeminiRecommendationService` (backend/src/gemini/client.py)
- `OrderStatsService` (backend/src/services/order_stats.py)
- `GeminiAPIKeyPool` (backend/src/gemini/key_pool.py)
- Redis client (backend/src/cache/redis_client.py)

**Библиотеки:**
- react-icons (уже используется)
- SWR (уже используется)

## Порядок выполнения

1. **Backend endpoint** — создать POST endpoint (подзадача 3)
2. **Frontend hook** — создать `useGenerateRecommendations()` (подзадача 2)
3. **Frontend UI** — добавить dropdown в ProfileRecommendations (подзадача 1)

**Обоснование порядка:**
- Backend сначала — фронтенд будет зависеть от работающего API
- Hook перед UI — компонент будет использовать хук

## Acceptance Criteria

### Frontend
- [ ] Иконка три точки (⋮) добавлена в заголовок секции справа
- [ ] При клике на иконку открывается dropdown меню
- [ ] Dropdown закрывается при клике вне его области
- [ ] Кнопка "Получить сейчас" вызывает API endpoint
- [ ] Во время генерации показывается loading state (disabled button)
- [ ] После успешной генерации данные обновляются автоматически (через SWR)
- [ ] При ошибке показывается alert с текстом ошибки
- [ ] Dropdown имеет purple gradient дизайн
- [ ] Dropdown корректно позиционируется (не выходит за границы)

### Backend
- [ ] Endpoint `POST /users/{tgid}/recommendations/generate` создан
- [ ] Авторизация: manager | self (403 при нарушении)
- [ ] Валидация: минимум 5 заказов (400 при нарушении)
- [ ] Генерация через `GeminiRecommendationService`
- [ ] Результат кэшируется в Redis с TTL 24 часа
- [ ] Возвращается `RecommendationsResponse` с generated_at
- [ ] Обработка ошибок: 400, 403, 500 с понятными сообщениями
- [ ] Логирование всех операций и ошибок

### Hooks
- [ ] Хук `useGenerateRecommendations()` создан
- [ ] Возвращает: `generateRecommendations`, `isLoading`, `error`
- [ ] После успешной генерации вызывает `mutate()` для SWR
- [ ] Корректная обработка ошибок

## Технические детали

### Dropdown state management

```typescript
const [showDropdown, setShowDropdown] = useState(false);
const dropdownRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  const handleClickOutside = (event: MouseEvent) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
      setShowDropdown(false);
    }
  };

  if (showDropdown) {
    document.addEventListener('mousedown', handleClickOutside);
  }

  return () => {
    document.removeEventListener('mousedown', handleClickOutside);
  };
}, [showDropdown]);
```

### Positioning dropdown

```tsx
<div className="relative">
  {/* Header with icon */}
  <div className="flex items-center gap-3 mb-4">
    <div className="flex-1 flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
        <FaLightbulb className="text-white text-lg" />
      </div>
      <h2 className="text-white text-xl font-bold">AI-рекомендации</h2>
    </div>

    {/* Three dots icon */}
    <button
      onClick={() => setShowDropdown(!showDropdown)}
      className="p-2 rounded-lg hover:bg-white/10 transition"
    >
      <FaEllipsisVertical className="text-white/70 text-lg" />
    </button>
  </div>

  {/* Dropdown menu */}
  {showDropdown && (
    <div
      ref={dropdownRef}
      className="absolute right-0 top-12 z-20 w-48 bg-[#1a153d] border border-white/20 rounded-lg shadow-2xl overflow-hidden"
    >
      <button
        onClick={handleGenerateClick}
        disabled={isGenerating}
        className="w-full p-3 text-left text-white hover:bg-white/10 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isGenerating ? 'Генерация...' : 'Получить сейчас'}
      </button>
    </div>
  )}
</div>
```

### Error handling

```typescript
const handleGenerateClick = async () => {
  try {
    await generateRecommendations(tgid);
    setShowDropdown(false);
  } catch (err) {
    alert(error?.message || 'Не удалось сгенерировать рекомендации');
  }
};
```

### Backend caching

```python
# Same as batch worker
cache_key = f"recommendations:user:{tgid}"
cache_data = {
    "summary": result.get("summary"),
    "tips": result.get("tips", []),
    "generated_at": datetime.now(timezone.utc).isoformat(),
}

await set_cache(cache_key, json.dumps(cache_data), ttl=86400)
```

## Ссылки

- Task: `.memory-base/workflow/tasks/active/TSK-022/task.md`
- Gemini Integration: `.memory-base/tech-docs/gemini-integration.md`
- API Spec: `.memory-base/tech-docs/api.md`
- Frontend Components: `.memory-base/tech-docs/frontend-components.md`
- Code Style: `.memory-base/tech-docs/rules/code-style.md`
