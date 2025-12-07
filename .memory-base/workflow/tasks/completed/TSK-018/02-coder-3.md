---
agent: coder
task_id: TSK-018
status: completed
created_at: 2025-12-07T17:30:00Z
files_changed:
  - frontend_mini_app/src/lib/api/hooks.ts
---

# Coder Report: TSK-018 (Fix API Response Format Mismatch)

## Problem Analysis

Backend API возвращает разные форматы для разных endpoints:
- **Простые массивы**: `/cafes`, `/combos`, `/menu`, `/users`, `/orders`, `/summaries`
- **Объекты с pagination**: `/cafe-requests`, `/user-requests`

Frontend hooks.ts использовал `ListResponse<T>` и `data?.items` для всех endpoints, что вызывало ошибку для endpoints возвращающих простые массивы.

## Root Cause

```typescript
// БЫЛО (неправильно для endpoints возвращающих массив):
const { data } = useSWR<ListResponse<Cafe>>('/cafes', fetcher);
return { data: data?.items }; // ❌ data - массив, не объект!
```

## Solution Implemented

### Исправленные hooks (backend возвращает массивы):

1. **useCafes** (строки 39-50)
   - Backend: `list[CafeResponse]` → `[{...}, {...}]`
   - Changed: `useSWR<Cafe[]>` + `return { data }`

2. **useCombos** (строки 56-67)
   - Backend: `list[ComboResponse]` → `[{...}, {...}]`
   - Changed: `useSWR<Combo[]>` + `return { data }`

3. **useMenu** (строки 74-90)
   - Backend: `list[MenuItemResponse]` → `[{...}, {...}]`
   - Changed: `useSWR<MenuItem[]>` + `return { data }`

4. **useOrders** (строки 134-156)
   - Backend: `list[OrderResponse]` → `[{...}, {...}]`
   - Changed: `useSWR<Order[]>` + `return { data }`

5. **useUsers** (строки 340-351)
   - Backend: `list[UserResponse]` → `[{...}, {...}]`
   - Changed: `useSWR<User[]>` + `return { data }`

6. **useSummaries** (строки 247-258)
   - Backend: `list[SummaryResponse]` → `[{...}, {...}]`
   - Changed: `useSWR<Summary[]>` + `return { data }`

### Hooks без изменений (backend возвращает объекты с items):

1. **useCafeRequests** (строки 161-172)
   - Backend: `LinkRequestListSchema` → `{ items: [...], total, skip, limit }`
   - No change needed: `useSWR<ListResponse<CafeRequest>>` + `return { data: data?.items }` ✓

2. **useUserRequests** (строки 589-602)
   - Backend: `UserAccessRequestListSchema` → `{ items: [...], total, skip, limit }`
   - No change needed: already correct ✓

## Changes Made

### File: `frontend_mini_app/src/lib/api/hooks.ts`

```diff
// useCafes
-  const { data, error, isLoading, mutate } = useSWR<ListResponse<Cafe>>(
+  const { data, error, isLoading, mutate } = useSWR<Cafe[]>(
     shouldFetch ? `/cafes${activeOnly ? "?active_only=true" : ""}` : null,
     fetcher
   );
   return {
-    data: data?.items,
+    data,
     error,
     isLoading,
     mutate
   };

// useCombos
-  const { data, error, isLoading, mutate } = useSWR<ListResponse<Combo>>(
+  const { data, error, isLoading, mutate } = useSWR<Combo[]>(
     cafeId ? `/cafes/${cafeId}/combos` : null,
     fetcher
   );
   return {
-    data: data?.items,
+    data,

// useMenu
-  const { data, error, isLoading, mutate } = useSWR<ListResponse<MenuItem>>(
+  const { data, error, isLoading, mutate } = useSWR<MenuItem[]>(
     cafeId
       ? `/cafes/${cafeId}/menu${category ? `?category=${category}` : ""}`
       : null,
     fetcher
   );
   return {
-    data: data?.items,
+    data,

// useOrders
-  const { data, error, isLoading, mutate } = useSWR<ListResponse<Order>>(
+  const { data, error, isLoading, mutate } = useSWR<Order[]>(
     endpoint,
     fetcher
   );
   return {
-    data: data?.items,
+    data,

// useUsers
-  const { data, error, isLoading, mutate } = useSWR<ListResponse<User>>(
+  const { data, error, isLoading, mutate } = useSWR<User[]>(
     shouldFetch ? "/users" : null,
     fetcher
   );
   return {
-    data: data?.items,
+    data,

// useSummaries
-  const { data, error, isLoading, mutate } = useSWR<ListResponse<Summary>>(
+  const { data, error, isLoading, mutate } = useSWR<Summary[]>(
     "/summaries",
     fetcher
   );
   return {
-    data: data?.items,
+    data,
```

## Verification

### Build Test
```bash
cd frontend_mini_app && npm run build
```

**Result**: ✅ Build successful
- No TypeScript errors
- All pages compiled successfully
- Production build optimized

### API Format Reference

| Endpoint | Backend Return Type | Frontend Hook Type | Access Pattern |
|----------|-------------------|-------------------|---------------|
| `/cafes` | `list[CafeResponse]` | `Cafe[]` | `data` |
| `/cafes/{id}/combos` | `list[ComboResponse]` | `Combo[]` | `data` |
| `/cafes/{id}/menu` | `list[MenuItemResponse]` | `MenuItem[]` | `data` |
| `/orders` | `list[OrderResponse]` | `Order[]` | `data` |
| `/users` | `list[UserResponse]` | `User[]` | `data` |
| `/summaries` | `list[SummaryResponse]` | `Summary[]` | `data` |
| `/cafe-requests` | `LinkRequestListSchema` | `ListResponse<CafeRequest>` | `data?.items` |
| `/user-requests` | `UserAccessRequestListSchema` | `ListResponse<UserAccessRequest>` | `data?.items` |

## Impact Analysis

### Fixed Components
All components using these hooks will now receive data correctly:
- `CafeList.tsx` - cafe selection
- `MenuSection.tsx` - menu display
- `ComboSelector.tsx` - combo selection
- `ReportsList.tsx` - summaries
- `BalanceManager.tsx` - user list
- Order components - order list

### No Breaking Changes
- API interface remains the same
- Component code doesn't need changes
- Only hook implementation fixed

## Status

✅ **COMPLETED**

All hooks now correctly match backend API response formats. TypeScript build passes without errors.

## Next Steps

1. Test in development environment
2. Verify cafe list loads correctly
3. Verify menu items display
4. Verify user management works
