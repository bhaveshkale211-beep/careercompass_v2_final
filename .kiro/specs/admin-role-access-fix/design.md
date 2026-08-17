# Design Document — admin-role-access-fix

## Overview

Five targeted fixes across `database.py`, `app.py`, and `templates/login.html` address every defect identified in the bugfix requirements. No new dependencies, no schema changes, and no alterations to existing admin management endpoints are required.

---

## Technical Context

### Relevant Files

| File | Affected Logic |
|------|---------------|
| `database.py` | `init_db()` — admin seed already present (verified); no changes needed here |
| `app.py` | `register()`, `admin_required`, `user_dashboard()` |
| `templates/login.html` | Login form submit handler JS |

### Key Finding — database.py

Reviewing `database.py` shows that `init_db()` **already seeds the admin account** (lines checking `SELECT COUNT(*) FROM users WHERE username = 'admin'`). Defect 1.5 is therefore already fixed in the DB layer. No change to `database.py` is needed.

### Root Cause Summary

| # | Defect | Root Cause |
|---|--------|-----------|
| 1.1 | Registration missing `session['is_admin']` | `register()` sets 3 session keys but omits `is_admin` |
| 1.2 | Admin guard always hits DB | `admin_required` skips the session flag and always calls `get_user_by_id()` |
| 1.3 | Frontend always redirects to `/` | Login JS `setTimeout` hardcodes `window.location.href = '/'` |
| 1.4 | `/dashboard` serves all users the same page | `user_dashboard()` has no admin redirect |
| 1.5 | No seeded admin | Already fixed in `database.py` — no action needed |

---

## Implementation Plan

### Fix 1 — `app.py`: Set `session['is_admin']` on registration

In `register()`, after the three existing session assignments, add:

```python
session['is_admin'] = False
```

This mirrors what `login()` already does and satisfies requirement 2.1.

### Fix 2 — `app.py`: Session-first admin guard

Replace the `admin_required` decorator body so it checks the session flag before touching the database:

```python
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        # Session-first: avoids a DB round-trip for every admin request
        if session.get('is_admin'):
            return f(*args, **kwargs)
        # Fallback: re-check DB in case session was created before this fix
        user = get_user_by_id(session['user_id'])
        if not user or not user.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        # Repair the session for future requests
        session['is_admin'] = True
        return f(*args, **kwargs)
    return decorated
```

Satisfies requirement 2.2. The DB fallback preserves compatibility for any existing sessions that pre-date the fix.

### Fix 3 — `templates/login.html`: Role-aware redirect after login

In the login form submit handler, replace the hardcoded redirect:

```js
// Before
setTimeout(() => { window.location.href = '/'; }, 1000);

// After
setTimeout(() => {
    window.location.href = data.is_admin ? '/admin' : '/dashboard';
}, 1000);
```

Satisfies requirement 2.3.

### Fix 4 — `app.py`: Admin redirect in `/dashboard`

In `user_dashboard()`, add a redirect for admin sessions before rendering:

```python
@app.route("/dashboard")
@login_required
def user_dashboard():
    if session.get('is_admin'):
        return redirect(url_for('admin_panel'))
    return render_template("dashboard.html")
```

Satisfies requirement 2.4.

---

## Bug Condition Pseudocode

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type Request (session + endpoint + role)
  OUTPUT: boolean

  RETURN (
    (X.endpoint = 'register'  AND 'is_admin' NOT IN X.session_after)  OR
    (X.endpoint = 'admin/*'   AND X.session.is_admin = True AND guard_queries_db(X))  OR
    (X.endpoint = 'login_js'  AND X.is_admin = True AND redirect_target = '/')  OR
    (X.endpoint = '/dashboard' AND X.session.is_admin = True AND response != redirect('/admin'))
  )
END FUNCTION
```

**Fix Checking Property:**
```pascal
FOR ALL X WHERE isBugCondition(X) DO
  result ← F'(X)
  ASSERT (
    ('is_admin' IN result.session AND result.session.is_admin = False)   // Fix 1
    OR (result.status != 403 AND db_query_count = 0)                     // Fix 2
    OR (result.redirect_url IN {'/admin', '/dashboard'})                 // Fix 3
    OR (result.status = 302 AND result.location = '/admin')              // Fix 4
  )
END FOR
```

**Preservation Property:**
```pascal
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

---

## Correctness Properties

### Property 1 — Registration populates `is_admin` in session (example)

After a successful `POST /auth/register`, the server session MUST contain `is_admin = False`. Verified by checking the session object in a test client after a fresh registration.

### Property 2 — Admin guard grants access for valid admin sessions without a DB query (property)

For all requests where `session['is_admin'] = True`, the `admin_required` decorator MUST return the wrapped response without calling `get_user_by_id()`. Counter-example would be any admin request that still issues a DB lookup when the session flag is set.

### Property 3 — Admin guard denies non-admin sessions (property)

For all requests where `session.get('is_admin')` is falsy, every admin route MUST return HTTP 403. This covers: no session, `is_admin=False`, and `is_admin` absent.

### Property 4 — Login JS redirects admin to `/admin` (example)

When the login response JSON contains `is_admin: true`, the frontend MUST redirect to `/admin`. When `is_admin` is false/absent, it MUST redirect to `/dashboard`.

### Property 5 — `/dashboard` redirects admins (property)

For all authenticated sessions where `session['is_admin'] = True`, `GET /dashboard` MUST return HTTP 302 with `Location: /admin`. For all non-admin sessions, it MUST return HTTP 200 with `dashboard.html`.

### Property 6 — Default admin exists after `init_db()` (example)

After calling `init_db()` on an empty database, `verify_user('admin', 'admin123')` MUST return a user dict with `is_admin = 1`.

### Property 7 — Regular user sessions preserve all three base keys (example)

After login or registration with a non-admin account, the session MUST contain `user_id`, `username`, `fullname`, and `is_admin = False`.

### Property 8 — Banned users cannot log in (example)

`POST /auth/login` for a banned user MUST return HTTP 403 and MUST NOT set any session keys.

### Property 9 — Admin management actions still function (example)

Each of the six admin action endpoints (`/ban`, `/unban`, `/promote`, `/demote`, `/reset-password`, `/delete`) called with a valid admin session MUST return `{"success": true}` and produce an audit log entry.

### Property 10 — Logout clears session (example)

After `POST /auth/logout`, `GET /auth/status` MUST return `{"authenticated": false}`.

---

## Files to Modify

| File | Changes |
|------|---------|
| `app.py` | Fix 1: add `session['is_admin'] = False` in `register()`; Fix 2: rewrite `admin_required`; Fix 4: add redirect in `user_dashboard()` |
| `templates/login.html` | Fix 3: update login redirect JS |
| `database.py` | No changes required |
| `templates/dashboard.html` | No changes required |
| `templates/admin.html` | No changes required |
