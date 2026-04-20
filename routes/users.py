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


# ===== DATABASE CONNECTION (POSTGRES / NEON) =====
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


# ===== REGISTER =====
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


# ===== LOGIN =====
@auth_bp.route('/login', methods=['POST'])
def login():
    data = flask.request.json
    email = data.get('email')
    password = data.get('password')
    otp = data.get('otp')

    conn = get_db_connection()
    cursor = conn.cursor()
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

    stored_hash = user['password_hash'].encode()

    if not bcrypt.checkpw(password.encode(), stored_hash):
        return flask.jsonify({"error": "Incorrect password"}), 401

    if user.get('mfa_enabled'):
        if not otp:
            return flask.jsonify({"error": "OTP required"}), 401

        totp = pyotp.TOTP(user['mfa_secret'])
        if not totp.verify(otp):
            return flask.jsonify({"error": "Invalid OTP"}), 401

    return flask.jsonify({"message": "Login successful"})


# ===== REQUEST RESET =====
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


# ===== RESET PASSWORD =====
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