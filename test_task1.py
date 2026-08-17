"""
Tests for Task 1 — Fix session['is_admin'] missing on registration.
Validates requirement 2.1: after POST /auth/register the session must
contain is_admin = False.
"""

import json
import pytest
from app import app
from database import init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client with an isolated in-memory database."""
    # Point the app at a temporary DB so tests don't touch production data
    import database as db_module

    test_db = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_FILE", test_db)

    # Re-initialise the DB with the patched path
    init_db()

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret"

    with app.test_client() as client:
        yield client


def test_register_returns_success(client):
    """POST /auth/register with valid data must return {'success': True}."""
    payload = {
        "fullname": "Test User",
        "username": "testuser",
        "password": "password123",
    }
    resp = client.post(
        "/auth/register",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True


def test_register_sets_is_admin_false_in_session(client):
    """After registration the session must contain is_admin = False."""
    payload = {
        "fullname": "Session Test",
        "username": "sessiontest",
        "password": "password123",
    }
    with client.session_transaction() as sess:
        # Session should be empty before registration
        assert "is_admin" not in sess

    client.post(
        "/auth/register",
        data=json.dumps(payload),
        content_type="application/json",
    )

    with client.session_transaction() as sess:
        assert "is_admin" in sess, "is_admin key must be present in session after registration"
        assert sess["is_admin"] is False, "is_admin must be False for a newly registered user"


def test_register_sets_all_expected_session_keys(client):
    """Session must contain user_id, username, fullname, and is_admin after registration."""
    payload = {
        "fullname": "Full Keys",
        "username": "fullkeys",
        "password": "password123",
    }
    client.post(
        "/auth/register",
        data=json.dumps(payload),
        content_type="application/json",
    )
    with client.session_transaction() as sess:
        for key in ("user_id", "username", "fullname", "is_admin"):
            assert key in sess, f"Expected session key '{key}' to be set after registration"
