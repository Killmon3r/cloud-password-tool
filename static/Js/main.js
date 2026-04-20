const BASE_URL = "http://127.0.0.1:5000";

// ===== REGISTER =====
async function register() {
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const res = await fetch(`${BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
    });

    const data = await res.json();

    document.getElementById("result").innerText = JSON.stringify(data);

    // ✅ Redirect to login page after successful registration
    if (data.message) {
        window.location.href = "/login-page";
    }
}


// ===== LOGIN =====
async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const otp = document.getElementById("otp").value;

    const res = await fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, otp })
    });

    const data = await res.json();

    // ⚠️ HANDLE PASSWORD RESET CASE
    if (data.error === "Password reset required") {
        alert("Your password was breached. Please reset it.");
    }

    document.getElementById("result").innerText = JSON.stringify(data);

    // ✅ Redirect to dashboard on successful login
    if (data.message) {
        window.location.href = `/dashboard-page?email=${encodeURIComponent(email)}`;
    }
}