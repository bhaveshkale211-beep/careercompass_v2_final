# ============================================================
#   database.py — Enhanced with Full Admin Panel Support
# ============================================================

import sqlite3
import json
from datetime import datetime
import hashlib

DB_FILE = "careercompass.db"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname         TEXT    NOT NULL,
            username         TEXT    NOT NULL UNIQUE,
            password         TEXT    NOT NULL,
            is_admin         INTEGER DEFAULT 0,
            is_banned        INTEGER DEFAULT 0,
            restriction_note TEXT    DEFAULT '',
            login_count      INTEGER DEFAULT 0,
            last_login       TEXT,
            created_at       TEXT    NOT NULL
        )
    """)

    for col, definition in [
        ("is_banned",        "INTEGER DEFAULT 0"),
        ("restriction_note", "TEXT DEFAULT ''"),
        ("login_count",      "INTEGER DEFAULT 0"),
        ("last_login",       "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            persona     TEXT    NOT NULL,
            education   TEXT    NOT NULL,
            top_career  TEXT    NOT NULL,
            scores_json TEXT    NOT NULL,
            created_at  TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_progress (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            career_path   TEXT    NOT NULL,
            resource_name TEXT    NOT NULL,
            completed     INTEGER DEFAULT 0,
            completed_at  TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, career_path, resource_name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id    INTEGER NOT NULL,
            action      TEXT    NOT NULL,
            target_user INTEGER,
            details     TEXT,
            created_at  TEXT    NOT NULL,
            FOREIGN KEY (admin_id)    REFERENCES users (id),
            FOREIGN KEY (target_user) REFERENCES users (id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (fullname, username, password, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("Administrator", "admin", hash_password("admin123"), 1, now))

    connection.commit()
    connection.close()
    print("Database ready — admin_logs table enabled")


def create_user(fullname, username, password):
    try:
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (fullname, username, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (fullname, username.lower(), hash_password(password), now))
        user_id = cursor.lastrowid
        connection.commit()
        connection.close()
        return user_id
    except sqlite3.IntegrityError:
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def verify_user(username, password):
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, fullname, username, is_admin, is_banned, restriction_note, created_at
        FROM users WHERE username = ? AND password = ?
    """, (username.lower(), hash_password(password)))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def update_last_login(user_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE users SET last_login = ?, login_count = login_count + 1 WHERE id = ?
    """, (now, user_id))
    connection.commit()
    connection.close()


def is_username_taken(username):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username.lower(),))
    count = cursor.fetchone()[0]
    connection.close()
    return count > 0


def get_user_by_id(user_id):
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, fullname, username, is_admin, is_banned, restriction_note,
               created_at, last_login, login_count
        FROM users WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_all_users():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT u.id, u.fullname, u.username, u.is_admin, u.is_banned,
               u.restriction_note, u.created_at, u.last_login, u.login_count,
               COUNT(r.id) AS total_assessments,
               MAX(r.created_at) AS last_assessment
        FROM users u
        LEFT JOIN results r ON u.id = r.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def log_admin_action(admin_id, action, target_user_id=None, details=""):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO admin_logs (admin_id, action, target_user, details, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (admin_id, action, target_user_id, details, now))
    connection.commit()
    connection.close()


def get_admin_logs(limit=100):
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT l.id, l.action, l.details, l.created_at,
               a.username AS admin_username, a.fullname AS admin_fullname,
               t.username AS target_username, t.fullname AS target_fullname
        FROM admin_logs l
        JOIN users a ON l.admin_id = a.id
        LEFT JOIN users t ON l.target_user = t.id
        ORDER BY l.id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def ban_user(user_id, note=""):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET is_banned = 1, restriction_note = ? WHERE id = ?", (note, user_id))
    connection.commit()
    connection.close()


def unban_user(user_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET is_banned = 0, restriction_note = '' WHERE id = ?", (user_id,))
    connection.commit()
    connection.close()


def promote_user(user_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    connection.commit()
    connection.close()


def demote_user(user_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (user_id,))
    connection.commit()
    connection.close()


def reset_user_password(user_id, new_password):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(new_password), user_id))
    connection.commit()
    connection.close()


def delete_user(user_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM resource_progress WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM results WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    connection.commit()
    connection.close()


def get_user_full_details(user_id):
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, fullname, username, is_admin, is_banned,
               restriction_note, created_at, last_login, login_count
        FROM users WHERE id = ?
    """, (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        connection.close()
        return None
    user = dict(user_row)
    cursor.execute("""
        SELECT id, persona, education, top_career, scores_json, created_at
        FROM results WHERE user_id = ? ORDER BY id DESC
    """, (user_id,))
    results = []
    for r in cursor.fetchall():
        d = dict(r)
        d["scores"] = json.loads(d["scores_json"])
        del d["scores_json"]
        results.append(d)
    cursor.execute("""
        SELECT COUNT(*) FROM resource_progress WHERE user_id = ? AND completed = 1
    """, (user_id,))
    user["assessments"] = results
    user["completed_resources"] = cursor.fetchone()[0]
    connection.close()
    return user


def get_stats():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    admin_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM results")
    total_assessments = cursor.fetchone()[0]
    cursor.execute("SELECT top_career, COUNT(*) as c FROM results GROUP BY top_career ORDER BY c DESC")
    career_rows = cursor.fetchall()
    career_counts = {r[0]: r[1] for r in career_rows}
    cursor.execute("SELECT persona, COUNT(*) as c FROM results GROUP BY persona ORDER BY c DESC")
    persona_counts = {r[0]: r[1] for r in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) FROM results WHERE created_at >= date('now', '-7 days')")
    recent_assessments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-7 days')")
    new_users_week = cursor.fetchone()[0]
    connection.close()
    return {
        "total_users": total_users, "banned_users": banned_users, "admin_users": admin_users,
        "total_assessments": total_assessments, "most_popular_career": career_rows[0][0] if career_rows else "N/A",
        "career_counts": career_counts, "persona_counts": persona_counts,
        "recent_assessments": recent_assessments, "new_users_week": new_users_week,
    }


def save_result(user_id, persona, edu, top_career, scores):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO results (user_id, persona, education, top_career, scores_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, persona, edu, top_career, json.dumps(scores), now))
    connection.commit()
    connection.close()


def get_all_results():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT r.*, u.username, u.fullname FROM results r
        JOIN users u ON r.user_id = u.id ORDER BY r.id DESC
    """)
    rows = cursor.fetchall()
    connection.close()
    results = []
    for row in rows:
        result = dict(row)
        result["scores"] = json.loads(result["scores_json"])
        del result["scores_json"]
        results.append(result)
    return results


def get_user_results(user_id):
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM results WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    connection.close()
    results = []
    for row in rows:
        result = dict(row)
        result["scores"] = json.loads(result["scores_json"])
        del result["scores_json"]
        results.append(result)
    return results


def get_user_stats(user_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM results WHERE user_id = ?", (user_id,))
    total_assessments = cursor.fetchone()[0]
    cursor.execute("SELECT top_career FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    latest_career = row[0] if row else None
    cursor.execute("SELECT top_career, COUNT(*) FROM results WHERE user_id = ? GROUP BY top_career ORDER BY COUNT(*) DESC", (user_id,))
    career_counts = {r[0]: r[1] for r in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) FROM resource_progress WHERE user_id = ? AND completed = 1", (user_id,))
    completed_resources = cursor.fetchone()[0]
    connection.close()
    return {"total_assessments": total_assessments, "latest_career": latest_career,
            "career_counts": career_counts, "completed_resources": completed_resources}


def save_resource_progress(user_id, career_path, resource_name, completed):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if completed else None
    cursor.execute("""
        INSERT OR REPLACE INTO resource_progress (user_id, career_path, resource_name, completed, completed_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, career_path, resource_name, 1 if completed else 0, now))
    connection.commit()
    connection.close()


def get_user_resource_progress(user_id, career_path):
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("""
        SELECT resource_name, completed, completed_at FROM resource_progress
        WHERE user_id = ? AND career_path = ?
    """, (user_id, career_path))
    rows = cursor.fetchall()
    connection.close()
    return {r["resource_name"]: {"completed": bool(r["completed"]), "completed_at": r["completed_at"]} for r in rows}
