# Cloud Password Tool

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL-blue.svg)](https://www.mysql.com/)
[![Security](https://img.shields.io/badge/Security-Bcrypt%20%2B%202FA-red.svg)]()

A secure credential and user management application built with Flask and MySQL. The tool features custom two-tier hybrid encryption, multi-factor authentication (MFA) via TOTP, and proactive real-time credential security auditing via the **Have I Been Pwned (HIBP) API**.

---

## 🔒 Security & Architecture

This application employs a strict, proactive defense architecture to guarantee user security during transit, storage, and authentication.

### 1. Two-Tier Encryption Mechanism (Hybrid Hashing)
Unlike traditional applications that rely on a single hashing mechanism, this tool utilizes an innovative dual-layer pipeline:
* **Full-Length Protection (SHA-1):** The entire plaintext password string is initially processed using a non-reversible `SHA-1` hashing pass.
* **Prefix Isolation (Bcrypt):** The first 5 characters of the text are targeted and hashed via `Bcrypt`. Because Bcrypt handles salt and computation factors securely, these five characters are processed dynamically to support the k-anonymity validation workflow while the database stores the fully salted `Bcrypt` and profile states.

### 2. Privacy-Preserving Breach Checking (k-Anonymity)
To verify if a password has been compromised without revealing it to external networks:
1. The tool extracts a localized representation of the password prefix.
2. The isolated **5-character SHA-1 prefix** is cross-referenced over the internet against the **Have I Been Pwned (HIBP) API**.
3. If a match suffix returns from the HIBP API registry, a breach is detected.

### 3. Automated Breach Enforcements
If the API reports that a user's credential has been exposed in a known data leak:
* The user is **immediately and forcefully logged out** of their active session across all devices.
* The account status is flagged, and the user is **forced to change their password** before gaining access to the dashboard again.

### 4. Multi-Factor Authentication
Integrated with `pyotp`, providing strict Time-Based One-Time Password (TOTP) enforcement for standard operations.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask, Bcrypt (`flask-bcrypt`), PyOTP (`pyotp`)
* **Database:** MySQL
* **Frontend:** Clean Semantic HTML5, CSS3, JavaScript (Vanilla ES6)
* **Integrations:** Have I Been Pwned (HIBP) Pwned Passwords API

---

