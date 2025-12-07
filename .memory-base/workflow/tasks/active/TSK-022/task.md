---
id: TSK-022
title: Добавить dropdown меню для принудительной генерации AI-рекомендаций
pipeline: feature
status: pending
created_at: 2025-12-07T11:00:00Z
related_files:
  - frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx
  - frontend_mini_app/src/lib/api/hooks.ts
  - backend/src/routers/users.py
  - backend/src/services/gemini_recommendations.py
impact:
  api: yes
  db: no
  frontend: yes
  services: yes
---

## Описание

В секции "AI-рекомендации" на странице профиля пользователя добавить:
1. Три точки (⋮) в правом верхнем углу заголовка секции
2. При клике на точки показывать выпадающее dropdown меню
3. В меню одна кнопка "Получить сейчас" для принудительной генерации рекомендаций

**Визуальное представление:**
```
┌─────────────────────────────────────┐
│ 💡 AI-рекомендации            ⋮    │  ← три точки справа
│                                  ▼  │
│  Сделайте минимум 5 заказов для    │
│  получения рекомендаций             │
│                                     │
│  [Dropdown menu при клике на ⋮]     │
│  ┌────────────────────┐             │
│  │ Получить сейчас    │             │
│  └────────────────────┘             │
└─────────────────────────────────────┘
```

**Поведение кнопки "Получить сейчас":**
- Вызывает новый API endpoint `POST /api/v1/users/{tgid}/recommendations/generate`
- Показывает loading state во время генерации
- После успешной генерации обновляет данные (через SWR mutate)
- При ошибке показывает сообщение пользователю

## Acceptance Criteria

### Frontend
- [ ] В заголовке секции ProfileRecommendations справа добавлена иконка три точки (⋮)
- [ ] При клике на иконку открывается dropdown меню
- [ ] Dropdown закрывается при клике вне его области
- [ ] В dropdown одна кнопка "Получить сейчас"
- [ ] При клике на кнопку вызывается API endpoint для генерации
- [ ] Во время генерации показывается loading state (spinner или disabled button)
- [ ] После успешной генерации данные обновляются через SWR mutate
- [ ] При ошибке показывается alert или toast с текстом ошибки
- [ ] Dropdown имеет фиолетовый градиент в стиле дизайн-системы
- [ ] Dropdown позиционируется корректно (не выходит за границы экрана)

### Backend
- [ ] Создан новый endpoint `POST /api/v1/users/{tgid}/recommendations/generate`
- [ ] Endpoint доступен только для manager или self (та же логика авторизации что и GET)
- [ ] Endpoint вызывает принудительную генерацию рекомендаций через Gemini
- [ ] Результат сохраняется в Redis cache с TTL 24 часа
- [ ] Endpoint возвращает сгенерированные рекомендации в формате RecommendationsResponse
- [ ] При ошибке генерации возвращается 500 с понятным сообщением
- [ ] Если у пользователя меньше 5 заказов, возвращается 400 Bad Request

### Hooks
- [ ] Создан новый hook `useGenerateRecommendations()`
- [ ] Hook принимает tgid и возвращает функцию для генерации
- [ ] Hook возвращает loading state и error
- [ ] После успешной генерации hook вызывает mutate для обновления кэша SWR

## Контекст

### Найденные компоненты

**ProfileRecommendations.tsx:**
- Путь: `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/Profile/ProfileRecommendations.tsx`
- Текущий заголовок: `<h2>AI-рекомендации</h2>` на строке 32 (empty state) и 49 (loaded state)
- Дизайн: Purple gradient (`from-[#8B23CB] to-[#A020F0]`), backdrop blur, semi-transparent cards
- Empty state: "Сделайте минимум 5 заказов для получения рекомендаций"

**Пример dropdown компонента:**
- Путь: `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/components/Order/DeliveryTimeSelector.tsx`
- Показывает как делать dropdown с:
  - `useState` для управления открытием/закрытием
  - `useRef` для клика вне области
  - Positioning с `absolute z-20`
  - Gradient styling и hover effects
  - Закрытие при выборе опции

**API Hooks:**
- Путь: `/Users/maksim/git_projects/tg_bot/frontend_mini_app/src/lib/api/hooks.ts`
- Уже есть `useUserRecommendations(tgid)` для получения данных
- Нужно добавить `useGenerateRecommendations()` для POST запроса

### Backend context

**Существующий GET endpoint:**
- `GET /api/v1/users/{tgid}/recommendations`
- Auth: manager | self
- Возвращает кэшированные данные из Redis

**Gemini Integration:**
- Сервис: `backend/src/services/gemini_recommendations.py` (предположительно)
- Worker: `backend/workers/recommendations.py`
- Генерация происходит ночью в 03:00 через batch job
- Используется API key pool для ротации ключей Gemini
- Результат кэшируется в Redis с TTL 24 часа

**Что нужно создать:**
- Новый endpoint `POST /api/v1/users/{tgid}/recommendations/generate`
- Endpoint должен вызвать тот же процесс генерации что и batch worker
- Результат сохранить в Redis так же как worker
- Валидировать минимум 5 заказов перед генерацией

### API Response Format

```typescript
interface RecommendationsResponse {
  summary: string | null;
  tips: string[];
  stats: OrderStats;
  generated_at: string | null;
}

interface OrderStats {
  orders_last_30_days: number;
  categories: { [category: string]: { count: number; percent: number } };
  unique_dishes: number;
  favorite_dishes: { name: string; count: number }[];
}
```

## Технические детали

### Frontend Implementation

**Dropdown управление:**
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

**Hook для генерации:**
```typescript
export function useGenerateRecommendations() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | undefined>();

  const generateRecommendations = async (tgid: number) => {
    setIsLoading(true);
    setError(undefined);

    try {
      const result = await apiRequest<RecommendationsResponse>(
        `/users/${tgid}/recommendations/generate`,
        { method: 'POST' }
      );

      // Mutate cache to update UI
      mutate(`/users/${tgid}/recommendations`);

      return result;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { generateRecommendations, isLoading, error };
}
```

### Backend Implementation

**Router (src/routers/users.py):**
```python
@router.post("/{tgid}/recommendations/generate", response_model=RecommendationsResponse)
async def generate_recommendations(
    tgid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Force generate AI recommendations for user."""
    # Check authorization (manager or self)
    if current_user.role != "manager" and current_user.tgid != tgid:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check minimum orders
    stats = await order_stats_service.get_user_stats(tgid, days=30)
    if stats["orders_count"] < 5:
        raise HTTPException(
            status_code=400,
            detail="Minimum 5 orders required for recommendations"
        )

    # Generate recommendations
    try:
        result = await gemini_service.generate_recommendations(stats)

        # Cache result
        await cache_recommendations(tgid, result, stats)

        return RecommendationsResponse(
            summary=result["summary"],
            tips=result["tips"],
            stats=stats,
            generated_at=datetime.now(timezone.utc)
        )
    except Exception as e:
        logger.error(f"Failed to generate recommendations for {tgid}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")
```

## Архитектурные решения

1. **Dropdown должен быть частью ProfileRecommendations компонента** — не выносить в отдельный компонент для упрощения
2. **Использовать существующий Gemini сервис** — переиспользовать код из worker без дублирования
3. **Кэширование** — результат должен попасть в тот же Redis ключ что и batch worker
4. **Авторизация** — та же логика что и для GET endpoint (manager | self)
5. **Валидация** — проверять минимум 5 заказов на backend, не на frontend
6. **Loading state** — показывать в dropdown кнопке, не блокировать всю секцию
7. **Error handling** — показывать alert с понятным текстом ошибки

## Зависимости

- React hooks: useState, useEffect, useRef
- SWR для mutate после генерации
- react-icons для иконки три точки (FaEllipsisVertical)
- Существующий Gemini API key pool
- Существующий OrderStatsService
- Существующий Redis cache

## Тестирование

### Frontend
- Проверить открытие/закрытие dropdown при клике на иконку
- Проверить закрытие dropdown при клике вне его области
- Проверить вызов API при клике на "Получить сейчас"
- Проверить loading state во время генерации
- Проверить обновление данных после успешной генерации
- Проверить отображение ошибки при провале API

### Backend
- Проверить 403 при попытке чужого пользователя
- Проверить 400 при недостаточном количестве заказов
- Проверить успешную генерацию и кэширование
- Проверить формат ответа RecommendationsResponse
- Проверить обработку ошибок Gemini API

## Риски

1. **Превышение лимитов Gemini API** — пользователь может спамить кнопкой
   - Mitigation: добавить rate limiting или cooldown (например, раз в час)

2. **Долгая генерация** — Gemini API может отвечать 10-30 секунд
   - Mitigation: показывать loading state, не блокировать UI

3. **Ошибки API** — ключи могут быть исчерпаны
   - Mitigation: понятное сообщение об ошибке, fallback на batch generation
