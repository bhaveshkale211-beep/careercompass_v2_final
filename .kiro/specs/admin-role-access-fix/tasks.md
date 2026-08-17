# Tasks — admin-role-access-fix

## Implementation Tasks

- [x] 1. Fix session['is_admin'] missing on registration
  - [x] 1.1 In `app.py` `register()`, add `session['is_admin'] = False` after the existing session assignments
  - [x] 1.2 Verify that `POST /auth/register` response still returns `{'success': True}` and the session contains `is_admin`

- [x] 2. Fix admin route guard to check session first
  - [x] 2.1 In `app.py`, rewrite the `admin_required` decorator to check `session.get('is_admin')` before calling `get_user_by_id()`
  - [x] 2.2 Add DB fallback with session repair (`session['is_admin'] = True`) for pre-existing sessions
  - [x] 2.3 Confirm that a non-admin session still receives HTTP 403 on all admin routes

- [x] 3. Fix frontend login redirect
  - [x] 3.1 In `templates/login.html`, update the login form submit handler to read `data.is_admin` and redirect admins to `/admin` and regular users to `/dashboard`

- [x] 4. Fix /dashboard to redirect admins
  - [x] 4.1 In `app.py` `user_dashboard()`, add `if session.get('is_admin'): return redirect(url_for('admin_panel'))` before the `render_template` call

- [x] 5. Verify end-to-end correctness
  - [x] 5.1 Confirm `init_db()` seeds the admin account (already present — read-only verification)
  - [x] 5.2 Run `getDiagnostics` on `app.py` and `templates/login.html` to confirm no syntax errors
  - [x] 5.3 Manually verify the login → role-based redirect flow works for both admin and regular users
