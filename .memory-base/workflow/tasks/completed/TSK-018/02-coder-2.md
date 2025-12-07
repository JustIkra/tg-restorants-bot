---
agent: coder
task_id: TSK-018
status: completed
created_at: 2025-12-07T15:30:00Z
files_changed:
  - frontend_mini_app/src/lib/api/hooks.ts
  - frontend_mini_app/src/app/manager/page.tsx
  - frontend_mini_app/src/components/Manager/CafeList.tsx
---

# Coder Report: TSK-018 (Continuation)

## Problem

After authentication, data was not loading in the manager panel because SWR hooks made requests BEFORE the authentication token was available.

### Root Cause

1. In `manager/page.tsx`, hooks like `useUsers()` were called during the first render
2. Authentication happened in useEffect (asynchronously)
3. When hooks made their first requests, the token didn't exist yet
4. API returned 401, SWR cached the error
5. After successful authentication, data was not revalidated

## Solution Implemented

Applied a **two-layer defense** approach:

### 1. Added `shouldFetch` parameter to `useUsers()` hook

Modified the hook to accept an optional parameter that prevents fetching when false:

```typescript
export function useUsers(shouldFetch = true): UseDataResult<User> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<User>>(
    shouldFetch ? "/users" : null,  // null = skip request
    fetcher
  );
  // ...
}
```

This matches the existing pattern used by `useCafes()`.

### 2. Global SWR cache revalidation after auth

After successful authentication, we revalidate all SWR caches:

```typescript
authenticateWithTelegram(initData)
  .then(async (response) => {
    // ... existing checks ...

    setIsAuthenticated(true);

    // Revalidate all SWR caches after successful authentication
    await mutate(() => true, undefined, { revalidate: true });

    console.log("Manager authenticated successfully");
  })
```

### 3. Pass `isAuthenticated` to hooks

Updated hook calls to use the authentication state:

```typescript
// In manager/page.tsx
const { data: users } = useUsers(isAuthenticated);

// In CafeList component
<CafeList shouldFetch={isAuthenticated} ... />
```

## Changes Made

### File: `frontend_mini_app/src/lib/api/hooks.ts`

- Added `shouldFetch` parameter to `useUsers()` hook
- Defaults to `true` for backward compatibility
- When `false`, passes `null` to SWR to prevent requests

### File: `frontend_mini_app/src/app/manager/page.tsx`

- Added `import { mutate } from "swr"`
- Changed `useUsers()` call to `useUsers(isAuthenticated)`
- Added global cache revalidation after `setIsAuthenticated(true)`
- Made the `.then()` callback async to await the revalidation
- Passed `shouldFetch={isAuthenticated}` prop to `CafeList`

### File: `frontend_mini_app/src/components/Manager/CafeList.tsx`

- Added `shouldFetch?: boolean` to `CafeListProps` interface
- Added default value `shouldFetch = true` to component props
- Passed `shouldFetch` to `useCafes()` hook

## How It Works

1. **Before auth**: `isAuthenticated = false`
   - `useUsers(false)` → SWR receives `null` → no request
   - `CafeList` receives `shouldFetch={false}` → no request
   - No 401 errors, no cache pollution

2. **After auth**: `isAuthenticated = true`
   - `setIsAuthenticated(true)` triggers re-render
   - Global `mutate()` revalidates all existing caches
   - Hooks receive `shouldFetch={true}` → make requests with token
   - API returns data successfully

## Testing

Build succeeded without errors:

```bash
$ cd frontend_mini_app && npm run build
✓ Compiled successfully in 3.2s
✓ Generating static pages using 7 workers (10/10) in 1051.9ms
```

## Benefits

1. **No wasted requests**: Hooks don't try to fetch without a token
2. **No cache pollution**: No 401 errors stored in SWR cache
3. **Automatic retry**: Global revalidation ensures all caches refresh after auth
4. **Consistent pattern**: Matches existing `useCafes()` pattern
5. **Backward compatible**: Default `shouldFetch = true` doesn't break existing code

## Next Steps

This fix ensures that:
- Manager panel loads data correctly after authentication
- No 401 errors are cached
- Data is automatically fetched once auth is successful

The solution is complete and ready for testing in the Telegram Mini App environment.
