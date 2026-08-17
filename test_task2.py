"""
Tests for Task 2 — Fix admin route guard to check session first.

Validates:
  2.1  Session-first path: admin_required skips the DB when session['is_admin'] is True
  2.2  DB fallback + session repair: pre-existing sessions without the flag get healed
  2.3  Non-admin sessions receive HTTP 403 on all admin routes
"""

import json
import pytest
from unittest.mock import patch
from app import app
from database import init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client backed by an isolated temporary database."""
    import database as db_module

    test_db = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_FILE", test_db)
    init_db()

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret"

    with app.test_client() as client:
        yield client


# ── Helper ────────────────────────────────────────────────────

def _seed_session(client, user_id=1, username="admin", fullname="Admin", is_admin=True):
    """Directly set session values without going through a login endpoint."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = username
        sess["fullname"] = fullname
        if is_admin is not None:
            sess["is_admin"] = is_admin


# ── Sub-task 2.1 — session-first, no DB call ─────────────────

def test_admin_required_skips_db_when_session_flag_is_true(client):
    """When session['is_admin'] is True, admin_required must NOT call get_user_by_id."""
    _seed_session(client, user_id=1, is_admin=True)

    with patch("app.get_user_by_id") as mock_get_user:
        resp = client.get("/admin/users")

    # Request should succeed (200) and the DB lookup must not have been triggered
    assert resp.status_code == 200
    mock_get_user.assert_not_called()


# ── Sub-task 2.2 — DB fallback and session repair ─────────────

def test_admin_required_falls_back_to_db_for_legacy_session(client):
    """
    A session without is_admin (legacy) but with a real admin user_id must:
      - succeed (200)
      - have is_admin repaired to True in the session
    """
    # Seed a session without is_admin key (simulates a pre-fix session)
    with client.session_transaction() as sess:
        sess["user_id"] = 1        # admin seeded by init_db
        sess["username"] = "admin"
        sess["fullname"] = "Admin"
        # intentionally omit is_admin

    resp = client.get("/admin/users")
    assert resp.status_code == 200

    # Session should now be repaired
    with client.session_transaction() as sess:
        assert sess.get("is_admin") is True, "Session repair must set is_admin = True"


def test_admin_required_falls_back_to_db_for_session_with_false_flag(client):
    """
    A session with is_admin=False but a user who is actually an admin in the DB
    must succeed and repair the session. (Covers the edge case where the flag
    was incorrectly stored as False for an admin account.)
    """
    # Seed session with is_admin=False but user_id pointing at the admin account
    _seed_session(client, user_id=1, is_admin=False)

    resp = client.get("/admin/users")
    assert resp.status_code == 200

    with client.session_transaction() as sess:
        assert sess.get("is_admin") is True


# ── Sub-task 2.3 — non-admin gets 403 ────────────────────────

ADMIN_ROUTES = [
    ("GET",    "/admin"),
    ("GET",    "/admin/users"),
    ("GET",    "/admin/logs"),
]


@pytest.mark.parametrize("method,route", ADMIN_ROUTES)
def test_non_admin_session_gets_403(client, method, route):
    """A session with is_admin=False must receive 403 on every admin route."""
    _seed_session(client, user_id=99, username="regular", fullname="Regular User", is_admin=False)

    # Patch get_user_by_id to return a non-admin user (for the DB fallback path)
    with patch("app.get_user_by_id", return_value={"id": 99, "username": "regular", "is_admin": False}):
        if method == "GET":
            resp = client.get(route)
        else:
            resp = client.post(route, data=json.dumps({}), content_type="application/json")

    assert resp.status_code == 403
    body = resp.get_json()
    assert "Admin access required" in body.get("error", "")


def test_unauthenticated_request_gets_401(client):
    """A request with no session at all must receive 401, not 403."""
    resp = client.get("/admin/users")
    assert resp.status_code == 401
    body = resp.get_json()
    assert "Authentication required" in body.get("error", "")
