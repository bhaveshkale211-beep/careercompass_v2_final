# ============================================================
#   CareerCompass IT — Backend with Full Admin Panel
# ============================================================

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import sqlite3, json, os
from datetime import datetime
import hashlib

from recommendation_engine import calculate_scores, get_career_details
from database import (
    init_db, save_result, get_all_results, get_stats,
    create_user, verify_user, get_all_users,
    is_username_taken, get_user_by_id, get_user_results,
    save_resource_progress, get_user_resource_progress, get_user_stats,
    update_last_login, log_admin_action, get_admin_logs,
    ban_user, unban_user, promote_user, demote_user,
    reset_user_password, delete_user, get_user_full_details
)

app = Flask(__name__)
app.secret_key = 'careercompass_secret_key_2025_change_this_in_production'
CORS(app, supports_credentials=True)
init_db()


# ── Decorators ───────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

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


# ── Auth Routes ───────────────────────────────────────────────

@app.route("/login")
def login_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template("login.html")


@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    fullname = data.get('fullname', '').strip()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    if not fullname or len(fullname) < 2:
        return jsonify({'success': False, 'error': 'Full name must be at least 2 characters'}), 400
    if not username or len(username) < 3:
        return jsonify({'success': False, 'error': 'Username must be at least 3 characters'}), 400
    if not password or len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    if is_username_taken(username):
        return jsonify({'success': False, 'error': 'Username already taken'}), 400
    user_id = create_user(fullname, username, password)
    if user_id:
        session['user_id'] = user_id
        session['username'] = username
        session['fullname'] = fullname
        session['is_admin'] = False
        return jsonify({'success': True, 'message': 'Account created successfully!'})
    return jsonify({'success': False, 'error': 'Registration failed'}), 500


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    user = verify_user(username, password)
    if user:
        # Blocked user cannot log in
        if user.get('is_banned'):
            note = user.get('restriction_note') or 'Contact admin for details.'
            return jsonify({'success': False, 'error': f'Account suspended. {note}'}), 403
        update_last_login(user['id'])
        session['user_id']  = user['id']
        session['username'] = user['username']
        session['fullname'] = user['fullname']
        session['is_admin'] = user.get('is_admin', False)
        return jsonify({'success': True, 'message': 'Login successful!', 'is_admin': user.get('is_admin', False)})
    return jsonify({'success': False, 'error': 'Invalid username or password'}), 401


@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route("/auth/status")
def auth_status():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id':   session['user_id'],
            'username':  session['username'],
            'fullname':  session['fullname'],
            'is_admin':  session.get('is_admin', False)
        })
    return jsonify({'authenticated': False})


# ── App Routes ────────────────────────────────────────────────

@app.route("/")
@login_required
def home():
    return render_template("index.html", username=session.get('username'), fullname=session.get('fullname'))


@app.route("/recommend", methods=["POST"])
@login_required
def recommend():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    scores  = calculate_scores(
        persona=data.get("persona", "graduate"),
        edu=data.get("edu", "graduate"),
        tech=data.get("tech", []),
        strengths=data.get("strengths", []),
        work_style=data.get("workStyle", {}),
        goal=data.get("goal", "explore"),
        answers=data.get("answers", [])
    )
    results = get_career_details(scores, data.get("persona", "graduate"))
    save_result(user_id=session['user_id'], persona=data.get("persona"), edu=data.get("edu"),
                top_career=results[0]["key"], scores=scores)
    return jsonify({"success": True, "results": results, "top_match": results[0], "overall_score": results[0]["score"]})


@app.route("/dashboard")
@login_required
def user_dashboard():
    if session.get('is_admin'):
        return redirect(url_for('admin_panel'))
    return render_template("dashboard.html")


@app.route("/api/my-results")
@login_required
def my_results():
    return jsonify(get_user_results(session['user_id']))


@app.route("/api/my-stats")
@login_required
def my_stats():
    return jsonify(get_user_stats(session['user_id']))


@app.route("/api/resource-progress", methods=["POST"])
@login_required
def save_progress():
    data = request.get_json()
    career_path   = data.get('career_path')
    resource_name = data.get('resource_name')
    completed     = data.get('completed', False)
    if not career_path or not resource_name:
        return jsonify({'error': 'Missing required fields'}), 400
    save_resource_progress(session['user_id'], career_path, resource_name, completed)
    return jsonify({'success': True})


@app.route("/api/resource-progress/<career_path>")
@login_required
def get_progress(career_path):
    return jsonify(get_user_resource_progress(session['user_id'], career_path))


@app.route("/stats")
@login_required
def stats():
    return jsonify(get_stats())


@app.route("/results")
@login_required
def results():
    return jsonify(get_all_results())


@app.route("/health")
def health():
    return jsonify({"status": "running", "message": "CareerCompass IT backend is running!"})


# ── Admin Routes ─────────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin_panel():
    return render_template("admin.html")


@app.route("/admin/users")
@admin_required
def admin_users():
    return jsonify(get_all_users())


@app.route("/admin/users/<int:user_id>")
@admin_required
def admin_user_detail(user_id):
    """Full profile + assessment history for one user"""
    data = get_user_full_details(user_id)
    if not data:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(data)


@app.route("/admin/users/<int:user_id>/ban", methods=["POST"])
@admin_required
def admin_ban_user(user_id):
    """Ban a user — blocks login"""
    if user_id == session['user_id']:
        return jsonify({'error': 'You cannot ban yourself'}), 400
    data = request.get_json() or {}
    note = data.get('note', '')
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    if target.get('is_admin'):
        return jsonify({'error': 'Cannot ban another admin. Demote first.'}), 400
    ban_user(user_id, note)
    log_admin_action(session['user_id'], 'BAN', user_id, f'Note: {note}')
    return jsonify({'success': True, 'message': f'User @{target["username"]} has been banned'})


@app.route("/admin/users/<int:user_id>/unban", methods=["POST"])
@admin_required
def admin_unban_user(user_id):
    """Lift a ban"""
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    unban_user(user_id)
    log_admin_action(session['user_id'], 'UNBAN', user_id, '')
    return jsonify({'success': True, 'message': f'User @{target["username"]} has been unbanned'})


@app.route("/admin/users/<int:user_id>/promote", methods=["POST"])
@admin_required
def admin_promote_user(user_id):
    """Grant admin role"""
    if user_id == session['user_id']:
        return jsonify({'error': 'You are already an admin'}), 400
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    promote_user(user_id)
    log_admin_action(session['user_id'], 'PROMOTE_TO_ADMIN', user_id, '')
    return jsonify({'success': True, 'message': f'@{target["username"]} is now an admin'})


@app.route("/admin/users/<int:user_id>/demote", methods=["POST"])
@admin_required
def admin_demote_user(user_id):
    """Remove admin role"""
    if user_id == session['user_id']:
        return jsonify({'error': 'You cannot demote yourself'}), 400
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    demote_user(user_id)
    log_admin_action(session['user_id'], 'DEMOTE_FROM_ADMIN', user_id, '')
    return jsonify({'success': True, 'message': f'@{target["username"]} admin rights removed'})


@app.route("/admin/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def admin_reset_password(user_id):
    """Force a password reset for a user"""
    data = request.get_json() or {}
    new_password = data.get('password', '').strip()
    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    reset_user_password(user_id, new_password)
    log_admin_action(session['user_id'], 'RESET_PASSWORD', user_id, '')
    return jsonify({'success': True, 'message': f'Password reset for @{target["username"]}'})


@app.route("/admin/users/<int:user_id>/delete", methods=["DELETE"])
@admin_required
def admin_delete_user(user_id):
    """Permanently delete a user and all their data"""
    if user_id == session['user_id']:
        return jsonify({'error': 'You cannot delete yourself'}), 400
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    if target.get('is_admin'):
        return jsonify({'error': 'Cannot delete an admin account. Demote first.'}), 400
    log_admin_action(session['user_id'], 'DELETE_USER', user_id, f'Deleted user @{target["username"]}')
    delete_user(user_id)
    return jsonify({'success': True, 'message': f'User @{target["username"]} permanently deleted'})


@app.route("/admin/logs")
@admin_required
def admin_logs():
    """Get full admin audit log"""
    return jsonify(get_admin_logs(200))


# ── Start ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  CareerCompass IT — Full Admin Panel Edition")
    print("  http://localhost:5000")
    print("  Admin: username=admin  password=admin123")
    print("=" * 60)
    app.run(debug=True, port=5000)
