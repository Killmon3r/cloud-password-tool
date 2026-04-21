# routes/users.py

import flask
import bcrypt
import psycopg2
import hashlib
import requests
import re
import pyotp
import secrets
import os
from datetime import datetime, timedelta

auth_bp = flask.Blueprint('auth', __name__)


# ===== DATABASE CONNECTION =====
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


# ===== PASSWORD STRENGTH =====
def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"\d", password) and
        re.search(r"[!@#$%^&*()_+]", password)
    )


# =========================================================
# REGISTER
# =========================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    data = flask.request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return flask.jsonify({"error": "All fields required"}), 400

    if not is_strong_password(password):
        return flask.jsonify({"error": "Weak password"}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
    sha1_password = hashlib.sha1(password.encode()).hexdigest().upper()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (username, email, password_hash, password_sha1, force_password_reset)
        VALUES (%s, %s, %s, %s, %s)
    """, (username, email, hashed, sha1_password, False))

    conn.commit()
    cursor.close()
    conn.close()

    return flask.jsonify({"message": "User registered"}), 201


# =========================================================
# LOGIN
# =========================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    data = flask.request.json
    email = data.get('email')
    password = data.get('password')
    otp = data.get('otp')

    if not email or not password:
        return flask.jsonify({"error": "Email and password required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            return flask.jsonify({"error": "User not found"}), 404

        columns = [desc[0] for desc in cursor.description]
        user = dict(zip(columns, user))

        if user.get("force_password_reset"):
            return flask.jsonify({
                "error": "Password compromised. Reset required."
            }), 403

        stored_hash = user['password_hash']

        if isinstance(stored_hash, memoryview):
            stored_hash = stored_hash.tobytes()
        elif isinstance(stored_hash, str):
            stored_hash = stored_hash.encode()

        if not bcrypt.checkpw(password.encode(), stored_hash):
            return flask.jsonify({"error": "Incorrect password"}), 401

        return flask.jsonify({"message": "Login successful"}), 200

    except Exception as e:
        print("LOGIN ERROR:", e)
        return flask.jsonify({"error": "Server error"}), 500

    finally:
        cursor.close()
        conn.close()


# =========================================================
# DASHBOARD (🔥 UPDATED WITH REAL BREACH LOGS)
# =========================================================
@auth_bp.route('/dashboard', methods=['GET'])
def dashboard():
    email = flask.request.args.get('email')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user
    cursor.execute("""
        SELECT username, email, force_password_reset
        FROM users
        WHERE email=%s
    """, (email,))

    user = cursor.fetchone()

    if not user:
        return flask.jsonify({"error": "User not found"}), 404

    columns = [desc[0] for desc in cursor.description]
    user = dict(zip(columns, user))

    # =====================================================
    # 🔥 FAKE BREACH HISTORY FOR DEMO USER
    # =====================================================
    if email == "valentino@gmail.com":
        breach_logs = [
            {"breach_count": 1, "created_at": "2026-04-10"},
            {"breach_count": 2, "created_at": "2026-04-09"},
            {"breach_count": 3, "created_at": "2026-04-08"},
            {"breach_count": 4, "created_at": "2026-04-07"},
            {"breach_count": 5, "created_at": "2026-04-06"},
            {"breach_count": 6, "created_at": "2026-04-05"},
            {"breach_count": 7, "created_at": "2026-04-04"},
            {"breach_count": 8, "created_at": "2026-04-03"},
        ]
        user["force_password_reset"] = True

    else:
        # normal users
        cursor.execute("""
            SELECT breach_count, created_at
            FROM breach_logs
            WHERE email=%s
            ORDER BY created_at DESC
        """, (email,))

        logs = cursor.fetchall()

        breach_logs = [
            {"breach_count": row[0], "created_at": str(row[1])}
            for row in logs
        ]

    cursor.close()
    conn.close()

    return flask.jsonify({
        "user": user,
        "breach_logs": breach_logs
    })


# =========================================================
# RESET REQUEST
# =========================================================
@auth_bp.route('/request-reset', methods=['POST'])
def request_reset():
    email = flask.request.json.get('email')

    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(minutes=15)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET reset_token=%s, reset_token_expiry=%s
        WHERE email=%s
    """, (token, expiry, email))

    conn.commit()
    cursor.close()
    conn.close()

    return flask.jsonify({"reset_token": token})


# =========================================================
# RESET PASSWORD
# =========================================================
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = flask.request.json
    token = data.get('token')
    new_password = data.get('new_password')

    if not is_strong_password(new_password):
        return flask.jsonify({"error": "Weak password"}), 400

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    sha1_password = hashlib.sha1(new_password.encode()).hexdigest().upper()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE reset_token=%s AND reset_token_expiry > NOW()
    """, (token,))
    user = cursor.fetchone()

    if not user:
        return flask.jsonify({"error": "Invalid or expired token"}), 400

    columns = [desc[0] for desc in cursor.description]
    user = dict(zip(columns, user))

    cursor.execute("""
        UPDATE users
        SET password_hash=%s,
            password_sha1=%s,
            reset_token=NULL,
            reset_token_expiry=NULL,
            force_password_reset=FALSE
        WHERE id=%s
    """, (hashed, sha1_password, user['id']))

    conn.commit()
    cursor.close()
    conn.close()

    return flask.jsonify({"message": "Password reset successful"})
