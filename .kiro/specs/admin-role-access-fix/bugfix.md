# Bugfix Requirements Document

## Introduction

CareerCompass has multiple interconnected role and session handling defects that prevent admin users from ever accessing the admin panel, cause all users to land on the wrong page after login, and leave no way to bootstrap an admin account. The fixes must be applied atomically — correcting session population on registration, login-time redirect logic, the admin route guard, dashboard role routing, and database seeding — while preserving all existing non-admin behaviour.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user completes registration THEN the system creates the account with `is_admin=0` and never writes `session['is_admin']`, so the admin flag is absent from the session for the rest of that session.

1.2 WHEN any request hits an admin-protected route THEN the system re-queries the database with `get_user_by_id()` and checks `user.get('is_admin', False)` — because no admin session flag is set and no admin users exist by default, all admin routes return 403.

1.3 WHEN a user logs in successfully THEN the server returns `{'success': True, 'is_admin': ...}` but the frontend JavaScript ignores `is_admin` and unconditionally redirects every user to `'/'` instead of routing admins to `/admin` and regular users to `/dashboard`.

1.4 WHEN any authenticated user navigates to `/dashboard` THEN the system renders `dashboard.html` for all users with no role-based differentiation or redirect for admins.

1.5 WHEN `init_db()` is called on a fresh database THEN the system creates the schema but seeds no admin account, so there is no way to log in as an admin without manual database intervention.

### Expected Behavior (Correct)

2.1 WHEN a user completes registration THEN the system SHALL set `session['is_admin'] = False` immediately after account creation so the flag is present for the duration of that session.

2.2 WHEN a request hits an admin-protected route THEN the system SHALL check `session.get('is_admin')` first and only fall back to a DB query when the session flag is absent, so a valid admin session passes the guard without an extra query.

2.3 WHEN a user logs in successfully THEN the frontend JavaScript SHALL read `is_admin` from the login response and redirect admins to `/admin` and regular users to `/dashboard`.

2.4 WHEN an authenticated admin user navigates to `/dashboard` THEN the system SHALL redirect them to `/admin` instead of rendering the user dashboard.

2.5 WHEN `init_db()` is called and no user with `username = 'admin'` exists THEN the system SHALL insert a default admin account (`username: admin`, `password: admin123`, `is_admin: 1`) so admin access is available immediately after first run.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a regular user logs in or registers THEN the system SHALL CONTINUE TO set `session['user_id']`, `session['username']`, and `session['fullname']` and redirect to `/dashboard`.

3.2 WHEN a banned user attempts to log in THEN the system SHALL CONTINUE TO return a 403 response with the restriction note and create no session.

3.3 WHEN a regular (non-admin) authenticated user requests an admin route THEN the system SHALL CONTINUE TO return a 403 response.

3.4 WHEN a regular user views `/dashboard` THEN the system SHALL CONTINUE TO display their profile, assessment history, and stats.

3.5 WHEN an admin performs user management actions (ban, unban, promote, demote, delete, reset password) THEN the system SHALL CONTINUE TO execute those actions and write audit log entries correctly.

3.6 WHEN any authenticated user calls `/auth/logout` THEN the system SHALL CONTINUE TO clear the session and return a success response.
