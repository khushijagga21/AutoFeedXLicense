# auth.py — AutoFeedX (client-side; licensing removed but UI unchanged)

import tkinter as tk
from tkinter import messagebox
import json
import os
import uuid
import socket
import requests  # kept for compatibility if you re-enable features later
from dotenv import load_dotenv
load_dotenv()

CREDENTIALS_FILE = 'credentials.json'

# ---- Lemon Squeezy placeholders (kept for compatibility, NOT used) ----
LS_LICENSE_BASE = "https://api.lemonsqueezy.com/v1"
LS_API_KEY = os.getenv("LEMON_API_KEY", "").strip()
LS_STORE_ID = os.getenv("LS_STORE_ID", "").strip()
LS_PRODUCT_ID = os.getenv("LS_PRODUCT_ID", "").strip()
LS_VARIANT_ID = os.getenv("LS_VARIANT_ID", "").strip()

# ---------------- App storage ----------------

def _load_db() -> dict:
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def _save_db(db: dict) -> None:
    with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4)

# ---------------- Core logic (license removed) ----------------

def save_user(username, password, company, email, license_key):
    """
    Create a local user without any license activation.
    The license_key is accepted but IGNORED (kept only for UI compatibility).
    """
    db = _load_db()

    if not username or not password or not email:
        return False

    if username in db:
        return False  # user already exists

    user_id = str(uuid.uuid4())

    db[username] = {
        "user_id": user_id,
        "password": password,
        "company": company,
        "email": email,
        "status": "allowed",
        # keep fields to avoid breaking other code/exports
        "license_key": license_key,
        "license_id": None,
        "instance_id": None,
        "license_status": "not_enforced",
        "expires_at": None,
    }

    _save_db(db)
    return True

def validate_user(username, password):
    """
    Validate username/password only.
    License validation is REMOVED but return shape is preserved.
    """
    db = _load_db()
    user = db.get(username)
    if not user:
        return False, {}

    if user.get("password") != password:
        return False, {}

    if user.get("status") == "denied":
        return "denied", {}

    # Build the info object as before
    return True, {
        "username": username,
        "company": user.get("company", ""),
        "user_id": user.get("user_id", ""),
        "email": user.get("email", ""),
        # keep keys so downstream code doesn't break
        "license": user.get("license_key", None),
        "instance_id": user.get("instance_id", None),
    }

# ---------------- Tkinter windows ----------------

def signup_window():
    window = tk.Tk()
    window.title("Signup")

    tk.Label(window, text="Username").pack()
    username_entry = tk.Entry(window)
    username_entry.pack()

    tk.Label(window, text="Password").pack()
    password_entry = tk.Entry(window, show="*")
    password_entry.pack()

    tk.Label(window, text="Company").pack()
    company_entry = tk.Entry(window)
    company_entry.pack()

    tk.Label(window, text="Email").pack()
    email_entry = tk.Entry(window)
    email_entry.pack()

    tk.Label(window, text="License Key").pack()
    license_entry = tk.Entry(window)
    license_entry.pack()

    def register():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        company = company_entry.get().strip()
        email = email_entry.get().strip()
        license_key = license_entry.get().strip()  # accepted but ignored

        if save_user(username, password, company, email, license_key):
            messagebox.showinfo("Success", "Signup successful! Please log in.")
            window.destroy()
            login_window()
        else:
            # keep original generic wording so UI/messages don't change
            messagebox.showerror("Error", "Signup failed! User may exist or license invalid.")

    tk.Button(window, text="Signup", command=register).pack()
    tk.Button(
        window,
        text="Already have an account? Login",
        command=lambda: [window.destroy(), login_window()]
    ).pack()

    window.mainloop()

def login_window():
    window = tk.Tk()
    window.title("Login")

    tk.Label(window, text="Username").pack()
    username_entry = tk.Entry(window)
    username_entry.pack()

    tk.Label(window, text="Password").pack()
    password_entry = tk.Entry(window, show="*")
    password_entry.pack()

    def login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        result, user_info = validate_user(username, password)
        if result == 'denied':
            messagebox.showerror("Access Restricted", "Access restricted. Contact admin.")
        elif result:
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            window.destroy()
            launch_viewer(user_info)
        else:
            # keep original wording
            messagebox.showerror("Login Failed", "Invalid username, password, or license.")

    tk.Button(window, text="Login", command=login).pack()
    tk.Button(
        window,
        text="Forgot Password?",
        command=lambda: [window.destroy(), forgot_password_window()]
    ).pack(pady=5)
    tk.Button(
        window,
        text="Don't have an account? Signup",
        command=lambda: [window.destroy(), signup_window()]
    ).pack()

    window.mainloop()

def forgot_password_window():
    window = tk.Tk()
    window.title("Forgot Password")

    tk.Label(window, text="❓ Can't access your account?", font=("Segoe UI", 12)).pack(pady=10)
    tk.Label(window, text="Please contact the administrator for password help.", font=("Segoe UI", 10)).pack(pady=5)
    tk.Label(window, text="📧 Email: Ned.esports@gmail.com", font=("Segoe UI", 10, "bold"), fg="blue").pack(pady=10)
    tk.Label(window, text="📱 Phone: +919555518143", font=("Segoe UI", 10, "bold"), fg="blue").pack()

    tk.Button(window, text="Close", command=window.destroy).pack(pady=15)
    window.mainloop()

def launch_viewer(user_info):
    import main
    main.launch_viewer(user_info)

if __name__ == "__main__":
    signup_window()
