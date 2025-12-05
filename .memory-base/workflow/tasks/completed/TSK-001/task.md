---
task_id: TSK-001
title: "Интеграция frontend с API"
pipeline: feature
status: completed
created_at: 2025-12-05T23:00:00
completed_at: 2025-12-06T01:30:00
created_by: task-creator
---

## Описание

Интегрировать frontend (Telegram Mini App) с backend API. Заменить захардкоженные данные на реальные запросы к API. Переделать UI под новую структуру комбо-заказов.

## Анализ

### Связанные файлы

| Файл | Назначение |
|------|------------|
| `frontend_mini_app/src/app/page.tsx` | Главная страница с логикой заказа |
| `frontend_mini_app/src/components/CafeSelector/CafeSelector.tsx` | Выбор кафе |
| `frontend_mini_app/src/components/CategorySelector/CategorySelector.tsx` | Удалить, заменить на ComboSelector |
| `frontend_mini_app/src/components/Menu/MenuSection.tsx` | Переделать под выбор блюда для категории |
| `frontend_mini_app/src/components/Cart/CartSummary.tsx` | Заменить на OrderSummary |
| `.memory-base/tech-docs/api.md` | Спецификация API |
| `.memory-base/tech-docs/frontend-components.md` | Документация компонентов |

### Impact

- **API:** Использование endpoints: `/auth/telegram`, `/cafes`, `/cafes/{id}/combos`, `/cafes/{id}/menu`, `/orders`
- **Database:** без изменений
- **Frontend:** Полная переработка UI под комбо-структуру
- **Services:** Интеграция с Telegram WebApp SDK

### Зависимости

- **Требует:** Работающий backend API (или mock server)
- **Влияет на:** Весь пользовательский flow заказа

## Подзадачи

### 1. Инфраструктура API клиента
- [ ] Создать `frontend_mini_app/src/lib/api/client.ts` — базовый fetch клиент с JWT
- [ ] Создать `frontend_mini_app/src/lib/api/types.ts` — TypeScript типы из API spec
- [ ] Создать `frontend_mini_app/src/lib/api/hooks.ts` — React hooks для запросов (SWR)
- [ ] Настроить `@twa-dev/sdk` для Telegram WebApp

### 2. Авторизация
- [ ] Интеграция с Telegram WebApp initData
- [ ] Получение JWT токена через `POST /auth/telegram`
- [ ] Хранение токена и refresh логика

### 3. Компоненты UI

#### 3.1 ComboSelector (новый)
- [ ] Создать `frontend_mini_app/src/components/ComboSelector/ComboSelector.tsx`
- [ ] Получение комбо через `GET /cafes/{id}/combos`
- [ ] Отображение карточек комбо с ценами

#### 3.2 MenuSection (переделка)
- [ ] Переделать под radio-выбор одного блюда из категории
- [ ] Получение меню через `GET /cafes/{id}/menu?category={cat}`
- [ ] Группировка по категориям комбо

#### 3.3 ExtrasSection (новый)
- [ ] Создать `frontend_mini_app/src/components/ExtrasSection/ExtrasSection.tsx`
- [ ] Показ дополнительных товаров (category=extra)
- [ ] Счётчик количества

#### 3.4 OrderSummary (замена CartSummary)
- [ ] Создать `frontend_mini_app/src/components/OrderSummary/OrderSummary.tsx`
- [ ] Показ выбранного комбо + блюд + extras
- [ ] Итоговая сумма

### 4. Главная страница
- [ ] Переделать `page.tsx` под новую структуру
- [ ] State: selectedComboId, comboItems, extrasCart
- [ ] Логика валидации заказа (все категории заполнены)

### 5. Отправка заказа
- [ ] Создание заказа через `POST /orders`
- [ ] Обработка ошибок (deadline, access)
- [ ] Feedback пользователю (success/error)

## Acceptance Criteria

- [ ] Авторизация через Telegram WebApp работает
- [ ] Список кафе загружается из API
- [ ] Комбо-наборы отображаются с ценами
- [ ] Выбор блюд по категориям работает (radio)
- [ ] Дополнительные товары добавляются в заказ
- [ ] Итоговая сумма считается корректно
- [ ] Заказ отправляется на backend
- [ ] Обрабатываются ошибки API
- [ ] Код соответствует code-style (Next.js/React/Tailwind)
- [ ] Нет TypeScript ошибок
