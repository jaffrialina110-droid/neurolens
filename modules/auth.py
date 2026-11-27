
"""NeuroLens account signup, login and logout."""

import hashlib
import hmac
import re
import secrets
import sqlite3

import streamlit as st

from modules.storage import get_connection, init_db, log_activity


ITERATIONS = 310_000


def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
    )
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password, stored_hash):
    try:
        salt_hex, digest_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            ITERATIONS,
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def register_user(username, email, display_name, password):
    username = username.strip()
    email = email.strip().lower()
    display_name = display_name.strip()

    if not re.fullmatch(r"[A-Za-z0-9_]{3,24}", username):
        return False, "Username 3–24 characters ka ho; letters, numbers aur _ use karo."

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return False, "Valid email address enter karo."

    if not display_name:
        return False, "Display name required hai."

    if len(password) < 10:
        return False, "Password kam az kam 10 characters ka hona chahiye."

    password_hash = hash_password(password)

    try:
        init_db()
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users
                   (username, email, display_name, password_hash)
                   VALUES (?, ?, ?, ?)""",
                (username, email, display_name, password_hash),
            )
            user_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO user_profiles (user_id) VALUES (?)",
                (user_id,),
            )

        return True, "Account created. Ab login kar sakte ho."

    except sqlite3.IntegrityError:
        return False, "Ye username ya email pehle se registered hai."


def authenticate_user(username_or_email, password):
    init_db()
    identity = username_or_email.strip()

    with get_connection() as conn:
        user = conn.execute(
            """SELECT id, username, email, display_name, password_hash
               FROM users
               WHERE username = ? COLLATE NOCASE
                  OR email = ? COLLATE NOCASE""",
            (identity, identity),
        ).fetchone()

    if user and verify_password(password, user["password_hash"]):
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "display_name": user["display_name"],
        }

    return None


def current_user():
    return st.session_state.get("nl_user")


def logout():
    st.session_state.pop("nl_user", None)
    st.rerun()


def render_auth():
    init_db()

    st.title("🧠 NeuroLens Account")
    st.write("Join the NeuroLens learning community.")

    if current_user():
        user = current_user()
        st.success(f"Logged in as {user['display_name']}")
        st.caption(f"Username: @{user['username']}")
        if st.button("Log out", key="nl_logout"):
            logout()
        return

    signup_tab, login_tab = st.tabs(["Create account", "Log in"])

    with signup_tab:
        with st.form("nl_signup_form"):
            display_name = st.text_input("Display name")
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input(
                "Password (minimum 10 characters)",
                type="password",
            )
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button(
                "Create account",
                use_container_width=True,
            )

        if submitted:
            if password != confirm:
                st.error("Passwords match nahi karte.")
            else:
                ok, message = register_user(
                    username, email, display_name, password
                )
                if ok:
                    st.success(message)
                else:
                    st.error(message)

    with login_tab:
        with st.form("nl_login_form"):
            identity = st.text_input("Username or email")
            login_password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button(
                "Log in",
                use_container_width=True,
            )

        if login_clicked:
            user = authenticate_user(identity, login_password)
            if user:
                st.session_state["nl_user"] = user
                log_activity(user["id"], "login", 0, "User logged in")
                st.rerun()
            else:
                st.error("Login details sahi nahi hain.")
