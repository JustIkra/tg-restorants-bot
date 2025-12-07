# User Roles

## User

**Role:** `user`

**Description:** Regular employee who orders lunch through the Telegram Mini App.

**Attributes:**
- `tgid` (number) - Telegram user ID
- `name` (string) - Full name
- `office` (string) - Office location
- `role` (string) - Always `"user"`
- `is_active` (boolean) - Access status

**Permissions:**
- View active cafes and menus
- Create orders for themselves
- View their own orders
- Use FortuneWheel
- Access user interface at `/`

**Access:**
- Main page: `/` (order interface)
- Cannot access: `/manager` (redirected to `/`)

**Access Request Workflow:**
- New users must submit an access request on first authentication
- Requests are reviewed by managers in the Manager Panel
- Users can only access the system after their request is approved

---

## Manager

**Role:** `manager`

**Description:** Administrator who manages cafes, menus, users, and orders. **Managers have access to both user and administrative interfaces.**

**Attributes:**
- `tgid` (number) - Telegram user ID
- `name` (string) - Full name
- `office` (string) - Office location
- `role` (string) - Always `"manager"`
- `is_active` (boolean) - Access status

**Permissions:**
- All user permissions (can create orders, view menus, use FortuneWheel)
- Manage users (create, update, block, delete)
- Approve/reject user access requests
- Manage cafes (create, edit, activate/deactivate, delete)
- Manage menus and combos
- Approve/reject cafe connection requests
- Generate order summaries and reports

**Access:**
- Main page: `/` (user interface with "Панель менеджера" button in top-right)
- Manager panel: `/manager` (administrative interface with "Сделать заказ" button)
- **Dual Interface:** Managers can switch between user and admin interfaces using navigation buttons

**Navigation:**
- On `/`: Fixed button "Панель менеджера" (top-right corner) → navigates to `/manager`
- On `/manager`: Button "Сделать заказ" (in header) → navigates to `/`
- After login: Manager stays on `/` (no automatic redirect to `/manager`)

**UI Indicators:**
- Role badge: "Manager" displayed in user lists
- Navigation buttons visible only for manager role
- Purple gradient buttons (`#8B23CB` to `#A020F0`)

---

## Backend Role-Based Access Control

**Dependencies:**
- `CurrentUser` - Any authenticated user (user or manager)
- `ManagerUser` - Only managers (raises 403 for non-managers)

**Endpoint Access:**

| Endpoint | Required Role |
|----------|---------------|
| `POST /auth/telegram` | None (public) |
| `GET /cafes` | None (public) |
| `GET /cafes/{id}/menu` | None (public) |
| `POST /orders` | `CurrentUser` (user or manager) |
| `GET /orders` | `CurrentUser` (user or manager) |
| `GET /users` | `ManagerUser` (manager only) |
| `POST /users` | `ManagerUser` (manager only) |
| `PATCH /users/{tgid}` | `ManagerUser` (manager only) |
| `PATCH /users/{tgid}/access` | `ManagerUser` (manager only) |
| `DELETE /users/{tgid}` | `ManagerUser` (manager only) |
| `GET /user-requests` | `ManagerUser` (manager only) |
| `POST /user-requests/{id}/approve` | `ManagerUser` (manager only) |
| `POST /user-requests/{id}/reject` | `ManagerUser` (manager only) |
| `POST /cafes` | `ManagerUser` (manager only) |
| `PATCH /cafes/{id}` | `ManagerUser` (manager only) |
| `DELETE /cafes/{id}` | `ManagerUser` (manager only) |
| All menu/combo management | `ManagerUser` (manager only) |
| All cafe request management | `ManagerUser` (manager only) |
| All summary management | `ManagerUser` (manager only) |

---

## Frontend Role Checks

**Conditional Rendering:**

```typescript
// Show manager navigation button only for managers
{user?.role === "manager" && (
  <button onClick={() => router.push("/manager")}>
    Панель менеджера
  </button>
)}
```

**Route Protection:**

```typescript
// Redirect non-managers from /manager page
if (response.user.role !== "manager") {
  router.push("/");
  return;
}
```

---

## Notes

- **Managers can make orders:** Backend endpoints for orders use `CurrentUser`, allowing managers to create orders just like regular users.
- **No automatic redirect:** Managers are no longer redirected to `/manager` after login. They stay on `/` and can switch interfaces manually.
- **Role enforcement:** Manager-only endpoints return 403 Forbidden for non-manager users.
- **Token-based auth:** User role is determined by JWT token payload after Telegram authentication.