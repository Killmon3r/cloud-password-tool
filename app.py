from flask import Flask, render_template
import os
from dotenv import load_dotenv

from routes.users import auth_bp, get_db_connection

import requests
import smtplib
from email.mime.text import MIMEText

load_dotenv()

app = Flask(__name__)


# ===== EMAIL FUNCTION =====
def send_email(to_email, subject, body):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    if not sender_email or not sender_password:
        print("Email not configured")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            print("Email sent")
    except Exception as e:
        print("Email error:", e)


# ===== ROUTES =====
app.register_blueprint(auth_bp)




@app.route("/login-page")
def login_page():
    return render_template("login.html")


@app.route("/register-page")
def register_page():
    return render_template("register.html")


@app.route("/reset-page")
def reset_page():
    return render_template("reset.html")


@app.route("/dashboard-page")
def dashboard_page():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)