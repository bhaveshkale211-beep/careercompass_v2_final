# CareerCompass IT

A web-based career recommendation platform that helps users discover the best IT career path based on their background, skills, and goals. Built with Flask and SQLite.

---

## What It Does

Users answer a short survey about their education, tech exposure, strengths, and work style. The recommendation engine scores five IT careers and returns a personalised ranked list with salary ranges, demand levels, and tailored explanations.

**5 career paths covered:**
- AI / ML Engineer
- Data Scientist / Analyst
- Full Stack Developer
- Cloud / DevOps Engineer
- Cybersecurity Analyst

---

## Project Structure

```
careercompass/
├── app.py                  # Flask app — all routes and decorators
├── database.py             # SQLite setup, all DB functions
├── recommendation_engine.py# Scoring logic for career matching
├── requirements.txt        # Python dependencies
├── careercompass.db        # SQLite database (auto-created)
└── templates/
    ├── index.html          # Main assessment page
    ├── login.html          # Login / register page
    ├── dashboard.html      # User results dashboard
    └── admin.html          # Admin panel
```

---

## Getting Started

**Requirements:** Python 3.8+

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

App starts at `http://localhost:5000`

**Default admin account (auto-created on first run):**
- Username: `admin`
- Password: `admin123`

---

## Features

### User Side
- Register and log in with a personal account
- Take a multi-step career assessment survey
- View ranked career recommendations with match scores
- Track learning resource progress per career path
- View personal assessment history and stats on the dashboard

### Admin Panel (`/admin`)
- View all registered users with assessment counts and login history
- Ban / unban users with a reason note
- Promote / demote users to/from admin
- Reset any user's password
- Delete user accounts (non-admin only)
- Full audit log of all admin actions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / Flask 3.0 |
| Database | SQLite (via `sqlite3`) |
| Auth | Server-side sessions (Flask session) |
| Frontend | HTML / CSS / Vanilla JS (Jinja2 templates) |
| CORS | flask-cors 4.0 |

---

## API Routes

### Auth
| Method | Route | Description |
|---|---|---|
| GET | `/login` | Login / register page |
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Log in |
| POST | `/auth/logout` | Log out |
| GET | `/auth/status` | Check session status |

### User
| Method | Route | Description |
|---|---|---|
| GET | `/` | Main assessment page |
| POST | `/recommend` | Submit survey, get career recommendations |
| GET | `/dashboard` | User dashboard (redirects admins to `/admin`) |
| GET | `/api/my-results` | User's assessment history |
| GET | `/api/my-stats` | User's personal stats |
| POST | `/api/resource-progress` | Save learning resource progress |
| GET | `/api/resource-progress/<career>` | Get progress for a career path |

### Admin (requires admin session)
| Method | Route | Description |
|---|---|---|
| GET | `/admin` | Admin panel |
| GET | `/admin/users` | All users list |
| GET | `/admin/users/<id>` | Full user profile + history |
| POST | `/admin/users/<id>/ban` | Ban a user |
| POST | `/admin/users/<id>/unban` | Unban a user |
| POST | `/admin/users/<id>/promote` | Grant admin role |
| POST | `/admin/users/<id>/demote` | Remove admin role |
| POST | `/admin/users/<id>/reset-password` | Reset user password |
| DELETE | `/admin/users/<id>/delete` | Delete user account |
| GET | `/admin/logs` | Admin audit log (last 200 entries) |

---

## Database Schema

**users** — stores accounts and role flags  
**results** — stores each user's assessment submissions  
**resource_progress** — tracks completed learning resources per user  
**admin_logs** — audit trail for all admin actions  

Passwords are hashed with SHA-256. The database file (`careercompass.db`) is auto-created on first run via `init_db()`.

---

## Role-Based Access

- Regular users → access `/dashboard` and all `/api/*` routes
- Admin users → redirected to `/admin` on login and from `/dashboard`
- Admin routes are protected by the `@admin_required` decorator (session-first check, DB fallback)
- Banned users are blocked at login before any session is created

---

## Dependencies

```
flask==3.0.3
flask-cors==4.0.1
```
