const BASE_URL = "https://cloud-password-tool.onrender.com";


// ================= REGISTER =================
window.register = async function () {

    alert("register clicked");

    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const res = await fetch(`${BASE_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });

        const data = await res.json();

        document.getElementById("result").innerText =
            data.message || data.error;

        if (res.ok) {
            window.location.href = "/login-page";
        }

    } catch (err) {
        console.log("Register error:", err);
        alert("Server not responding");
    }
};


// ================= LOGIN =================
window.login = async function () {

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const otpField = document.getElementById("otp");
    const otp = otpField ? otpField.value : null;

    try {
        const res = await fetch(`${BASE_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, otp })
        });

        const data = await res.json();

        document.getElementById("result").innerText =
            data.message || data.error;

        if (res.ok) {
            window.location.href =
                `/dashboard-page?email=${encodeURIComponent(email)}`;
        }

    } catch (err) {
        console.log("Login error:", err);
        alert("Server not responding");
    }
};
