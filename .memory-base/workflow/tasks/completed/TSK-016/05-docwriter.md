---
agent: docwriter
task_id: TSK-016
status: completed
next: null
created_at: 2025-12-07T05:00:00Z
files_changed:
  - path: .memory-base/tech-docs/api.md
    action: modified
  - path: .memory-base/tech-docs/roles.md
    action: modified
---

## Documentation Updates

Successfully documented the user access request approval system implemented in TSK-016. All changes follow the existing documentation structure and style.

### Updated Files

#### `.memory-base/tech-docs/api.md`

**1. Updated Auth Section**
- Added error codes and notes for `POST /auth/telegram`
- Documented behavior for new users (creates UserAccessRequest → returns 403)
- Documented behavior for pending requests (returns 403 "Access request pending approval")
- Documented behavior for rejected requests (returns 403 "Access request rejected")
- Documented behavior for approved users (normal authentication flow)

**2. Added User Access Requests Section**
- New section after Recommendations, before HTTP Status Codes
- Documented all three endpoints:
  - `GET /api/v1/user-requests` - List access requests with pagination and filtering
  - `POST /api/v1/user-requests/{id}/approve` - Approve request and create user
  - `POST /api/v1/user-requests/{id}/reject` - Reject request
- Included complete schema definitions for:
  - `UserAccessRequestListResponse` - paginated list response
  - `UserAccessRequest` - individual request object
- Added workflow example showing the complete user approval flow (5 steps)

**3. Updated Users Section**
- Added new endpoint `PATCH /users/{tgid}` for updating user data
- Positioned between `DELETE /users/{tgid}` and `PATCH /users/{tgid}/access`
- Documented optional fields: name, office, role

#### `.memory-base/tech-docs/roles.md`

**1. Updated User Role**
- Added "Access Request Workflow" section explaining:
  - New users must submit access request on first authentication
  - Requests are reviewed by managers in Manager Panel
  - Users can only access system after approval

**2. Updated Manager Role**
- Updated Permissions list to include:
  - "Manage users (create, update, block, delete)" - added "update"
  - "Approve/reject user access requests" - new permission

**3. Updated Backend Role-Based Access Control**
- Added `PATCH /users/{tgid}` endpoint to table
- Added three new user-requests endpoints:
  - `GET /user-requests`
  - `POST /user-requests/{id}/approve`
  - `POST /user-requests/{id}/reject`
- All marked as `ManagerUser` (manager only)

### Documentation Consistency

**Followed existing patterns:**
- API endpoint documentation format (Auth, Query, Body, Response, Errors)
- Schema definitions with field descriptions and types
- Error code documentation in endpoint headers
- Workflow examples showing step-by-step processes
- Backend RBAC table format

**Maintained style:**
- Russian language for user-facing text in workflow examples
- English for technical documentation
- Code examples in JSON format
- Consistent indentation and spacing
- Proper markdown headers and lists

### Coverage

All aspects of TSK-016 implementation are now documented:

**Backend:**
- ✓ UserAccessRequest model and schema
- ✓ Approval workflow endpoints
- ✓ Updated auth endpoint behavior
- ✓ User update endpoint
- ✓ Manager-only access control

**Frontend:**
- ✓ Manager Panel "Запросы доступа" tab mentioned in workflow
- ✓ User approval/rejection flow described
- ✓ Integration with existing Manager Panel documented

**Security:**
- ✓ Manager-only access clearly documented
- ✓ Status-based access control explained
- ✓ Role-based permissions updated

### Notes

**Why User Access Requests section is placed after Recommendations:**
- Follows logical grouping: Auth → Users → Data entities → Workflows → System features
- User Access Requests is a system feature related to Users
- Placement before HTTP Status Codes keeps all API documentation together

**Backward compatibility noted:**
- Existing users continue to authenticate normally (mentioned in Auth section notes)
- Only new users go through approval workflow
- No breaking changes to existing endpoints

**Cross-references:**
- Auth section references UserAccessRequest creation
- User role references Manager Panel approval
- Manager role references user request management
- All connected for easy navigation
