# Authorization & Roles

This project uses **role-based access control (RBAC)** on top of JWT
authentication. This document describes the roles, the permission matrix, and
the authorization approach.

## Roles

There are three roles, defined by `UserRole` in `backend/app/models.py`:

| Role      | Intent                                                            |
| --------- | ----------------------------------------------------------------- |
| `admin`   | Full access — manage users, assign roles, view everything.        |
| `manager` | View users and metrics; manage own profile. No write access to others. |
| `member`  | Manage own profile only. Default for new users.                   |

New users default to `member`. Only an `admin` can change a user's role.

### Relationship to `is_superuser`

The legacy `is_superuser` boolean is kept for backward compatibility. The
invariant is:

```
is_superuser == true  <->  role == "admin"
```

`crud.create_user` / `crud.update_user` keep the two in sync (setting either to
admin promotes the other; demoting the role clears the flag). Existing rows were
backfilled and resynced by Alembic migrations
(`b7c4f2a9d130`, `c3e1f0a2b4d5`).

## Permission matrix

| Capability                                  | Member       | Manager | Admin |
| ------------------------------------------- | ------------ | ------- | ----- |
| Log in / reset password                     | ✅ (public)  | ✅      | ✅    |
| View own profile (`GET /users/me`)          | ✅           | ✅      | ✅    |
| Update own profile / password               | ✅           | ✅      | ✅    |
| View a user by id (`GET /users/{id}`)       | own only     | ✅ any  | ✅ any |
| List users (`GET /users/`)                  | ❌           | ✅      | ✅    |
| View metrics (`GET /utils/metrics`)         | ❌           | ✅      | ✅    |
| Create user (`POST /users/`)                | ❌           | ❌      | ✅    |
| Update any user / assign role (`PATCH /users/{id}`) | ❌   | ❌      | ✅    |
| Delete a user (`DELETE /users/{id}`)        | ❌           | ❌      | ✅    |
| Send test email (`POST /utils/test-email/`) | ❌           | ❌      | ✅    |

Notes:

- `member` can read their **own** record via `GET /users/{id}`, but not others.
- `admin` short-circuits every role check, so admins pass any `require_role`.
- Item endpoints (`/items`) use ownership-or-admin checks, not roles.

## Authorization approach

Authorization is implemented with **dependency factories**, not middleware or
decorators. This keeps checks composable with FastAPI's dependency injection,
unit-testable in isolation, per-route, and visible in the OpenAPI schema.

The core primitive is `require_role` in `backend/app/api/deps.py`:

```python
def require_role(*roles: UserRole) -> Callable[[User], User]:
    allowed = {UserRole.ADMIN, *roles}  # admin can do everything

    def dependency(current_user: CurrentUser) -> User:
        if current_user.is_superuser or current_user.role in allowed:
            return current_user
        raise HTTPException(status_code=403, detail="...")

    return dependency
```

It is attached to routes as a dependency:

```python
@router.get("/", dependencies=[Depends(require_role(UserRole.MANAGER))])  # admin + manager
def read_users(...): ...

@router.post("/", dependencies=[Depends(require_role(UserRole.ADMIN))])   # admin only
def create_user(...): ...
```

`require_role(UserRole.MANAGER)` admits managers **and** admins, because admin is
always in the allowed set. `require_role(UserRole.ADMIN)` admits admins only.

### Why store the role as a string

`role` is a `VARCHAR` column (via a SQLAlchemy `TypeDecorator`), not a native
Postgres `ENUM`. New roles can be added by extending the `UserRole` enum **without
a database migration**.

### Adding a new role

1. Add the value to `UserRole` in `backend/app/models.py`.
2. Add a label/option in `frontend/src/lib/roles.ts` (`ROLE_LABELS`, `ROLE_OPTIONS`).
3. Reference it in `require_role(...)` on the routes that should admit it.

No migration is required for the column itself.

## Frontend

The frontend mirrors these rules for UX only — **the API is the source of
truth**. Helpers live in `frontend/src/lib/roles.ts`:

- `isAdmin(user)` — `role === "admin"` or `is_superuser`. Gates management UI
  (Add/Edit/Delete user).
- `canViewUsers(user)` — admin or manager. Gates the Users page route, the
  sidebar "Users" link, and read access to the users table.

Managers see the users table read-only (no Add User button, no row actions);
admins get the full management UI.