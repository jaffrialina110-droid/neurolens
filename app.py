import os
import io
import re
import json
import random
import sqlite3
import hashlib
import hmac

from datetime import datetime, timedelta

import streamlit as st
import pandas as pd

from PIL import Image, ImageEnhance, ImageFilter

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

try:
    from supabase import create_client
except ImportError:
    create_client = None


# =========================================================
# APP CONFIGURATION
# =========================================================

APP_NAME = "NEUROLENS"
OWNER = "Ayna Jaffri"
DB_PATH = "neurolens.db"

MODEL = "gemini-2.5-flash"

st.set_page_config(
    page_title="NeuroLens | Explore the Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# DATABASE
# =========================================================

def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def query(sql, params=(), one=False):
    conn = db()
    try:
        rows = conn.execute(sql, params).fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def execute(sql, params=()):
    conn = db()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def init_db():

    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'member',
        is_active INTEGER NOT NULL DEFAULT 1,
        force_password_change INTEGER NOT NULL DEFAULT 0,
        last_login TEXT
    );

    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        mood TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS research (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        topic TEXT,
        notes TEXT,
        tags TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity TEXT NOT NULL,
        score REAL,
        details TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS voice_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        transcript TEXT,
        reflection TEXT,
        emoji TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        preferred_date TEXT,
        preferred_time TEXT,
        message TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id)
        ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        reaction TEXT NOT NULL,
        UNIQUE(post_id, user_id),
        FOREIGN KEY(post_id) REFERENCES posts(id)
        ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS concepts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        concept TEXT NOT NULL,
        connects_to TEXT,
        explanation TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_user_id INTEGER,
        actor_username TEXT,
        action TEXT NOT NULL,
        target_type TEXT,
        target_id TEXT,
        details TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS login_attempts (
        username TEXT PRIMARY KEY,
        failed_count INTEGER NOT NULL DEFAULT 0,
        locked_until TEXT,
        updated_at TEXT NOT NULL
    );
    """

    conn = db()

    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


init_db()


# =========================================================
# USER DATA HELPERS
# =========================================================

def get_user_rows(table, uid):

    allowed = {
        "activities",
        "journal",
        "research",
        "voice_logs",
        "appointments",
        "concepts"
    }

    if table not in allowed:
        raise ValueError("Invalid database table.")

    return query(
        f"""
        SELECT * FROM {table}
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (uid,)
    )


def section_title(title, description=""):

    st.title(title)

    if description:
        st.caption(description)


# =========================================================
# PASSWORD SECURITY
# =========================================================

def hash_password(password, salt=None):

    salt = salt or os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310000
    )

    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):

    try:
        salt_hex, expected_hash = stored.split(":", 1)

        salt = bytes.fromhex(salt_hex)

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            310000
        ).hex()

        return hmac.compare_digest(
            digest,
            expected_hash
        )

    except (ValueError, TypeError, AttributeError):
        return False


# =========================================================
# STREAMLIT SECRETS
# =========================================================

def get_secret_value(key):

    try:
        value = st.secrets.get(key)

        if value:
            return str(value).strip()

    except Exception:
        pass

    return os.environ.get(key, "").strip()


# =========================================================
# OWNER ACCOUNT SETUP
# =========================================================

def bootstrap_owner():

    existing_owner = query(
        """
        SELECT id FROM users
        WHERE role='owner'
        LIMIT 1
        """,
        one=True
    )

    if existing_owner:
        return

    username = get_secret_value(
        "OWNER_USERNAME"
    ).lower()

    email = get_secret_value("OWNER_EMAIL")

    password = get_secret_value(
        "OWNER_PASSWORD"
    )

    if not username or not password:
        return

    if not re.fullmatch(
        r"[a-z0-9_.-]{3,30}",
        username
    ):
        return

    if len(password) < 14:
        return

    try:

        execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password_hash,
                created_at,
                role,
                is_active
            )
            VALUES (?, ?, ?, ?, 'owner', 1)
            """,
            (
                username,
                email,
                hash_password(password),
                now()
            )
        )

    except sqlite3.IntegrityError:
        return


bootstrap_owner()


# =========================================================
# AUDIT LOGS
# =========================================================

def audit_event(
    actor_user_id,
    actor_username,
    action,
    target_type=None,
    target_id=None,
    details=None
):

    execute(
        """
        INSERT INTO audit_logs
        (
            actor_user_id,
            actor_username,
            action,
            target_type,
            target_id,
            details,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            actor_user_id,
            actor_username,
            action,
            target_type,
            str(target_id)
            if target_id is not None else None,
            details,
            now()
        )
    )


# =========================================================
# LOGIN SECURITY
# =========================================================

def login_is_locked(username):

    row = query(
        """
        SELECT locked_until
        FROM login_attempts
        WHERE username=?
        """,
        (username,),
        one=True
    )

    if not row or not row["locked_until"]:
        return False

    try:

        return (
            datetime.fromisoformat(row["locked_until"])
            > datetime.now()
        )

    except (ValueError, TypeError):
        return False


def record_login_failure(username):

    row = query(
        """
        SELECT failed_count, locked_until
        FROM login_attempts
        WHERE username=?
        """,
        (username,),
        one=True
    )

    failed_count = (
        row["failed_count"] if row else 0
    )

    failed_count += 1

    lock_time = None

    if failed_count >= 5:

        lock_time = (
            datetime.now() + timedelta(minutes=15)
        ).strftime("%Y-%m-%d %H:%M:%S")

    execute(
        """
        INSERT INTO login_attempts
        (
            username,
            failed_count,
            locked_until,
            updated_at
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(username)
        DO UPDATE SET
            failed_count=excluded.failed_count,
            locked_until=excluded.locked_until,
            updated_at=excluded.updated_at
        """,
        (
            username,
            failed_count,
            lock_time,
            now()
        )
    )


def clear_login_failures(username):

    execute(
        """
        DELETE FROM login_attempts
        WHERE username=?
        """,
        (username,)
    )


# =========================================================
# AUTHENTICATION
# =========================================================

def authenticate_user(
    username,
    password,
    expected_role=None
):

    username = username.strip().lower()

    if login_is_locked(username):

        return (
            False,
            "Too many failed attempts. Try again after 15 minutes."
        )

    row = query(
        """
        SELECT * FROM users
        WHERE username=?
        """,
        (username,),
        one=True
    )

    if (
        not row
        or not verify_password(
            password,
            row["password_hash"]
        )
    ):

        record_login_failure(username)

        return (
            False,
            "Username or password is incorrect."
        )

    if not row["is_active"]:

        return (
            False,
            "This account is inactive."
        )

    if expected_role and row["role"] != expected_role:

        return (
            False,
            "Username or password is incorrect."
        )

    clear_login_failures(username)

    execute(
        """
        UPDATE users
        SET last_login=?
        WHERE id=?
        """,
        (now(), row["id"])
    )

    audit_event(
        row["id"],
        row["username"],
        "login_success",
        "user",
        row["id"]
    )

    return True, row


# =========================================================
# CURRENT USER / SESSION
# =========================================================

def get_user():

    user = st.session_state.get("user")

    if not user:
        return None

    current_time = datetime.now().timestamp()

    last_activity = st.session_state.get(
        "last_activity"
    )

    if last_activity is not None:

        if current_time - last_activity > 1800:

            st.session_state.pop("user", None)

            st.session_state.pop(
                "last_activity",
                None
            )

            st.warning(
                "Your session expired. Please log in again."
            )

            return None

    st.session_state["last_activity"] = current_time

    row = query(
        """
        SELECT
            id,
            username,
            email,
            role,
            is_active,
            force_password_change
        FROM users
        WHERE id=?
        """,
        (user["id"],),
        one=True
    )

    if not row or not row["is_active"]:

        st.session_state.pop("user", None)

        st.session_state.pop(
            "last_activity",
            None
        )

        return None

    updated_user = {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
        "force_password_change": row[
            "force_password_change"
        ]
    }

    st.session_state["user"] = updated_user
    return updated_user
# =========================================================
# PART 2 — LOGIN AND REGISTRATION
# =========================================================

def logout():

    user = st.session_state.get("user")

    if user:
        audit_event(
            user["id"],
            user["username"],
            "logout",
            "user",
            user["id"]
        )

    st.session_state.pop("user", None)
    st.session_state.pop("last_activity", None)

    st.rerun()


def login_screen():

    st.title("🧠 NEUROLENS")

    st.subheader("Welcome to NeuroLens")

    st.write(
        "Explore cognition, behavior & the brain."
    )

    st.caption(
        "Welcome! Let's explore the brain, "
        "behaviour, and cognition together."
    )

    login_tab, register_tab = st.tabs(
        ["Login", "Create Account"]
    )

    with login_tab:

        st.markdown("### Welcome Back")

        with st.form("neurolens_login_form"):

            username = st.text_input(
                "Username",
                key="login_username"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if submitted:

            if not username.strip() or not password:

                st.error(
                    "Please enter your username and password."
                )

            else:

                success, result = authenticate_user(
                    username,
                    password
                )

                if success:

                    st.session_state["user"] = {
                        "id": result["id"],
                        "username": result["username"],
                        "email": result["email"],
                        "role": result["role"],
                        "force_password_change":
                            result["force_password_change"]
                    }

                    st.session_state["last_activity"] = (
                        datetime.now().timestamp()
                    )

                    st.success("Login successful!")

                    st.rerun()

                else:

                    st.error(result)

    with register_tab:

        st.markdown("### Create Your Account")

        with st.form("neurolens_register_form"):

            new_username = st.text_input(
                "Choose Username"
            )

            new_email = st.text_input(
                "Email (optional)"
            )

            new_password = st.text_input(
                "Create Password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            register = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

        if register:

            username = new_username.strip().lower()

            if not re.fullmatch(
                r"[a-z0-9_.-]{3,30}",
                username
            ):

                st.error(
                    "Username must be 3–30 characters "
                    "and use letters, numbers, dots, "
                    "underscores or hyphens."
                )

            elif new_email.strip() and not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                new_email.strip()
            ):

                st.error("Please enter a valid email.")

            elif len(new_password) < 10:

                st.error(
                    "Password must contain at least 10 characters."
                )

            elif new_password != confirm_password:

                st.error("Passwords do not match.")

            else:

                existing = query(
                    """
                    SELECT id FROM users
                    WHERE username=?
                    """,
                    (username,),
                    one=True
                )

                if existing:

                    st.error(
                        "This username is already taken."
                    )

                else:

                    try:

                        user_id = execute(
                            """
                            INSERT INTO users
                            (
                                username,
                                email,
                                password_hash,
                                created_at,
                                role,
                                is_active
                            )
                            VALUES (?, ?, ?, ?, 'member', 1)
                            """,
                            (
                                username,
                                new_email.strip() or None,
                                hash_password(new_password),
                                now()
                            )
                        )

                        audit_event(
                            user_id,
                            username,
                            "account_created",
                            "user",
                            user_id
                        )

                        st.success(
                            "Account created successfully. "
                            "You can now log in."
                        )

                    except sqlite3.IntegrityError:

                        st.error(
                            "Could not create account. "
                            "Please try another username."
                        )


# =========================================================
# CHANGE PASSWORD
# =========================================================

def change_password_page(user):

    section_title(
        "🔐 Change Password",
        "Update your NeuroLens account password."
    )

    with st.form("change_password_form"):

        current_password = st.text_input(
            "Current Password",
            type="password"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Update Password"
        )

    if submitted:

        row = query(
            """
            SELECT password_hash
            FROM users
            WHERE id=?
            """,
            (user["id"],),
            one=True
        )

        if not row:

            st.error("Account not found.")

        elif not verify_password(
            current_password,
            row["password_hash"]
        ):

            st.error("Current password is incorrect.")

        elif len(new_password) < 10:

            st.error(
                "New password must contain at least 10 characters."
            )

        elif new_password != confirm_password:

            st.error("New passwords do not match.")

        elif hmac.compare_digest(
            current_password,
            new_password
        ):

            st.error(
                "New password must be different "
                "from your current password."
            )

        else:

            execute(
                """
                UPDATE users
                SET password_hash=?,
                    force_password_change=0
                WHERE id=?
                """,
                (
                    hash_password(new_password),
                    user["id"]
                )
            )

            audit_event(
                user["id"],
                user["username"],
                "password_changed",
                "user",
                user["id"]
            )

            st.session_state["user"][
                "force_password_change"
            ] = 0

            st.success("Password updated successfully.")


# =========================================================
# GEMINI AI CONNECTION
# =========================================================

def get_api_key():

    return get_secret_value("GEMINI_API_KEY")


def get_gemini_client():

    if genai is None:

        return None

    api_key = get_api_key()

    if not api_key:

        return None

    try:

        return genai.Client(
            api_key=api_key
        )

    except Exception:

        return None


def ask_gemini(prompt, system_instruction=None):

    if not prompt or not prompt.strip():

        return "Please enter a message."

    client = get_gemini_client()

    if client is None:

        return (
            "Gemini AI is not configured. "
            "Please add GEMINI_API_KEY in "
            "Streamlit Secrets."
        )

    try:

        instructions = (
            system_instruction
            or
            """
            You are Ayna, the AI assistant inside NeuroLens.

            Help users explore cognitive neuroscience,
            brain functions, behavior, learning,
            memory, attention, emotions and decision-making.

            Explain scientific concepts clearly.
            Distinguish established evidence from hypotheses.
            Do not invent scientific references.
            Do not diagnose mental or neurological conditions.
            Do not claim that games measure actual brain activity.
            Encourage professional support when appropriate.
            """
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=instructions,
                temperature=0.7,
                max_output_tokens=1500
            )
        )

        answer = getattr(
            response,
            "text",
            None
        )

        if answer:

            return answer.strip()

        return "I couldn't generate a response. Please try again."

    except Exception as error:

        return (
            "Gemini request failed. "
            "Please check your API key and model configuration. "
            f"Technical details: {str(error)[:250]}"
        )


# =========================================================
# ASK AYNA AI PAGE
# =========================================================

def ask_ayna_page(user):

    section_title(
        "🤖 Ask Ayna AI",
        "Explore cognition, behavior and neuroscience through conversation."
    )

    if "ayna_messages" not in st.session_state:

        st.session_state["ayna_messages"] = []

    if "ayna_request_count" not in st.session_state:

        st.session_state["ayna_request_count"] = 0

    if "ayna_request_user" not in st.session_state:

        st.session_state["ayna_request_user"] = user["id"]

    if st.session_state["ayna_request_user"] != user["id"]:

        st.session_state["ayna_messages"] = []
        st.session_state["ayna_request_count"] = 0

        st.session_state["ayna_request_user"] = user["id"]

    for message in st.session_state["ayna_messages"]:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    if st.session_state["ayna_request_count"] >= 20:

        st.warning(
            "You have reached this session's "
            "20-message request limit."
        )

        return

    prompt = st.chat_input(
        "Ask Ayna about the brain, behavior or cognition..."
    )

    if prompt:

        st.session_state["ayna_messages"].append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):

            st.markdown(prompt)

        with st.chat_message("assistant"):

            with st.spinner("Ayna is thinking..."):

                answer = ask_gemini(prompt)

                st.markdown(answer)

        st.session_state["ayna_messages"].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.session_state["ayna_request_count"] += 1

        st.rerun()


# =========================================================
# SUPABASE CONNECTION
# =========================================================

@st.cache_resource
def get_supabase_client():

    if create_client is None:

        return None

    url = get_secret_value("SUPABASE_URL")

    key = get_secret_value("SUPABASE_KEY")

    if not url or not key:

        return None

    try:

        return create_client(
            url,
            key
        )

    except Exception:

        return None


def test_supabase_connection():

    client = get_supabase_client()

    if client is None:

        return (
            False,
            "Supabase is not configured. "
            "Check SUPABASE_URL and SUPABASE_KEY."
        )

    try:

        client.table("profiles").select(
            "*"
        ).limit(1).execute()

        return (
            True,
            "Supabase connection successful."
        )

    except Exception as error:

        return (
            False,
            f"Supabase test failed: {str(error)[:250]}"
        )


# =========================================================
# END OF PART 2
# =========================================================
# =========================================================
# PART 3 — HOME DASHBOARD
# =========================================================

def home_page(user):

    st.title("🧠 Welcome to NeuroLens")

    st.markdown(
        """
        ### Explore cognition, behavior & the brain

        Welcome to NeuroLens! I'm Ayna.
        Let's explore the brain, behaviour, and cognition together.
        """
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Your Role", user["role"].title())

    with col2:
        activities = get_user_rows(
            "activities",
            user["id"]
        )
        st.metric("Activities", len(activities))

    with col3:
        research = get_user_rows(
            "research",
            user["id"]
        )
        st.metric("Research Notes", len(research))

    st.subheader("Explore NeuroLens")

    modules = [
        ("🧠 Brain Explorer", "Learn about brain regions."),
        ("🔄 CSTC Circuit", "Explore cortico-striato-thalamo-cortical pathways."),
        ("🔬 Neuroscience Lab", "Try interactive cognitive activities."),
        ("🧩 Brain Puzzle", "Challenge your pattern recognition."),
        ("🤖 Ask Ayna AI", "Discuss neuroscience with AI."),
        ("📚 Research Book", "Save your research notes.")
    ]

    for name, description in modules:

        st.markdown(
            f"**{name}**  \n{description}"
        )


# =========================================================
# BRAIN EXPLORER
# =========================================================

def brain_explorer_page(user):

    section_title(
        "🧠 Brain Explorer",
        "Explore important brain regions and their functions."
    )

    regions = {
        "Prefrontal Cortex": {
            "function": (
                "Involved in executive functions such as "
                "planning, working memory, cognitive control "
                "and decision-making."
            ),
            "example": (
                "Planning your day or controlling an impulsive response."
            )
        },

        "Hippocampus": {
            "function": (
                "Important for forming and organizing "
                "new episodic memories and spatial memory."
            ),
            "example": (
                "Remembering a recent experience or navigating a route."
            )
        },

        "Striatum": {
            "function": (
                "Part of the basal ganglia. It contributes "
                "to action selection, reinforcement learning "
                "and goal-directed behavior."
            ),
            "example": (
                "Learning which action is likely to produce a reward."
            )
        },

        "Anterior Cingulate Cortex": {
            "function": (
                "Contributes to conflict monitoring, "
                "error processing, motivation and cognitive control."
            ),
            "example": (
                "Noticing a mistake and adjusting your response."
            )
        },

        "Amygdala": {
            "function": (
                "Contributes to emotional learning, "
                "salience detection and threat processing."
            ),
            "example": (
                "Learning to recognize a potentially threatening situation."
            )
        },

        "Thalamus": {
            "function": (
                "Acts as a major relay and processing hub "
                "for information traveling to the cerebral cortex."
            ),
            "example": (
                "Relaying sensory information to cortical regions."
            )
        },

        "Cerebellum": {
            "function": (
                "Important for movement coordination, "
                "motor learning and aspects of cognition."
            ),
            "example": (
                "Learning to coordinate a new movement."
            )
        },

        "Insula": {
            "function": (
                "Contributes to interoception, emotional "
                "awareness and integration of bodily signals."
            ),
            "example": (
                "Noticing changes in your heartbeat."
            )
        }
    }

    selected_region = st.selectbox(
        "Choose a brain region",
        list(regions.keys())
    )

    details = regions[selected_region]

    st.subheader(selected_region)

    st.write("**Main functions**")

    st.write(details["function"])

    st.write("**Everyday example**")

    st.info(details["example"])

    st.divider()

    st.subheader("Knowledge Check")

    questions = {
        "Which region is strongly involved in forming new episodic memories?":
            ["Hippocampus", "Cerebellum", "Thalamus"],

        "Which region contributes to executive control?":
            ["Prefrontal Cortex", "Amygdala", "Brainstem"],

        "Which structure is part of the basal ganglia?":
            ["Striatum", "Hippocampus", "Insula"]
    }

    correct_answers = {
        list(questions.keys())[0]: "Hippocampus",
        list(questions.keys())[1]: "Prefrontal Cortex",
        list(questions.keys())[2]: "Striatum"
    }

    question = st.selectbox(
        "Select a question",
        list(questions.keys())
    )

    answer = st.radio(
        "Choose your answer",
        questions[question]
    )

    if st.button("Check Answer"):

        if answer == correct_answers[question]:

            st.success("Correct answer!")

        else:

            st.error(
                "Not quite. Review the brain region information and try again."
            )


# =========================================================
# CSTC CIRCUIT LEARNING
# =========================================================

def cstc_circuit_page(user):

    section_title(
        "🔄 CSTC Circuit Learning",
        "Cortico-striato-thalamo-cortical circuits."
    )

    st.markdown(
        """
        The CSTC system consists of interconnected
        cortical, striatal, pallidal, subthalamic
        and thalamic structures.

        These circuits contribute to motor, cognitive,
        motivational and behavioral processes.
        """
    )

    circuit_type = st.selectbox(
        "Choose a circuit pathway",
        [
            "Direct Pathway",
            "Indirect Pathway",
            "Hyperdirect Pathway"
        ]
    )

    if circuit_type == "Direct Pathway":

        st.subheader("Direct Pathway")

        pathway = [
            "Cerebral Cortex",
            "Striatum — D1-expressing neurons",
            "GPi / SNr",
            "Thalamus",
            "Cerebral Cortex"
        ]

        st.markdown(
            "The direct pathway is commonly associated "
            "with facilitating selected actions."
        )

        for index, structure in enumerate(pathway):

            st.markdown(
                f"**{index + 1}. {structure}**"
            )

            if index < len(pathway) - 1:
                st.markdown("↓")

        st.info(
            "Simplified model: striatal inhibition of GPi/SNr "
            "reduces inhibitory output to the thalamus, "
            "which can facilitate selected cortical activity."
        )

    elif circuit_type == "Indirect Pathway":

        st.subheader("Indirect Pathway")

        pathway = [
            "Cerebral Cortex",
            "Striatum — D2-expressing neurons",
            "GPe",
            "Subthalamic Nucleus (STN)",
            "GPi / SNr",
            "Thalamus",
            "Cerebral Cortex"
        ]

        st.markdown(
            "The indirect pathway is commonly associated "
            "with suppressing competing or unwanted actions."
        )

        for index, structure in enumerate(pathway):

            st.markdown(
                f"**{index + 1}. {structure}**"
            )

            if index < len(pathway) - 1:
                st.markdown("↓")

        st.info(
            "Simplified model: reduced GPe inhibition of STN "
            "allows greater STN excitation of GPi/SNr, "
            "increasing inhibitory output to the thalamus."
        )

    else:

        st.subheader("Hyperdirect Pathway")

        pathway = [
            "Cerebral Cortex",
            "Subthalamic Nucleus (STN)",
            "GPi / SNr",
            "Thalamus"
        ]

        st.markdown(
            "The hyperdirect pathway provides a relatively "
            "rapid route from cortex to the subthalamic nucleus."
        )

        for index, structure in enumerate(pathway):

            st.markdown(
                f"**{index + 1}. {structure}**"
            )

            if index < len(pathway) - 1:
                st.markdown("↓")

        st.info(
            "This simplified pathway can contribute to "
            "rapid global or selective action suppression."
        )

    st.divider()

    st.subheader("Dopamine and the CSTC System")

    st.write(
        """
        Dopamine from the substantia nigra pars compacta
        (SNc) modulates striatal activity.

        D1 and D2 receptor-expressing populations are
        commonly used to describe direct and indirect
        pathway organization, respectively.

        Real CSTC networks are more complex than a
        simple two-pathway model.
        """
    )

    st.caption(
        "Educational model only. Circuit functions depend "
        "on context, cell populations and network interactions."
    )


# =========================================================
# NEUROSCIENCE LAB
# =========================================================

def save_activity(user, activity, score, details=None):

    execute(
        """
        INSERT INTO activities
        (
            user_id,
            activity,
            score,
            details,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user["id"],
            activity,
            score,
            details,
            now()
        )
    )


def neuroscience_lab_page(user):

    section_title(
        "🔬 Interactive Neuroscience Lab",
        "Try simple cognitive tasks and explore your responses."
    )

    experiment = st.selectbox(
        "Choose an experiment",
        [
            "Attention Challenge",
            "Memory Sequence",
            "Decision and Reward",
            "Stroop Control",
            "Pattern Recognition"
        ]
    )

    st.divider()

    # -----------------------------------------------------
    # ATTENTION CHALLENGE
    # -----------------------------------------------------

    if experiment == "Attention Challenge":

        st.subheader("🔎 Find the Target")

        st.write(
            "Find the letter X in the sequence below."
        )

        letters = [
            random.choice(["A", "B", "C", "D", "E"])
            for _ in range(25)
        ]

        target_position = random.randint(
            0,
            len(letters) - 1
        )

        letters[target_position] = "X"

        st.markdown(
            "### " + "   ".join(letters)
        )

        selected = st.selectbox(
            "Choose the position of X",
            list(range(1, 26))
        )

        if st.button("Submit Attention Answer"):

            if selected - 1 == target_position:

                st.success("Correct! You found X.")

                save_activity(
                    user,
                    "Attention Challenge",
                    100,
                    "Correct target selection"
                )

            else:

                st.error(
                    "Incorrect position. Try another challenge."
                )

                save_activity(
                    user,
                    "Attention Challenge",
                    0,
                    "Incorrect target selection"
                )

    # -----------------------------------------------------
    # MEMORY SEQUENCE
    # -----------------------------------------------------

    elif experiment == "Memory Sequence":

        st.subheader("🧠 Memory Challenge")

        st.write(
            "Remember this sequence, then enter it below."
        )

        sequence = "729418"

        st.code(sequence)

        answer = st.text_input(
            "Enter the six-digit sequence",
            max_chars=6
        )

        if st.button("Check Memory Answer"):

            if answer == sequence:

                st.success("Correct sequence!")

                save_activity(
                    user,
                    "Memory Sequence",
                    100,
                    "Correct sequence recalled"
                )

            else:

                st.error(
                    "That sequence does not match. Try again."
                )

                save_activity(
                    user,
                    "Memory Sequence",
                    0,
                    "Incorrect sequence recalled"
                )

    # -----------------------------------------------------
    # DECISION AND REWARD
    # -----------------------------------------------------

    elif experiment == "Decision and Reward":

        st.subheader("💰 Decision Challenge")

        st.write(
            "Choose between two hypothetical rewards."
        )

        choice = st.radio(
            "Which reward would you choose?",
            [
                "Receive Rs. 1,000 today",
                "Receive Rs. 1,500 after 30 days"
            ]
        )

        if st.button("Save Decision"):

            st.info(
                f"Your choice: {choice}"
            )

            st.write(
                """
                This task introduces intertemporal choice:
                decisions involving rewards available at
                different points in time.
                """
            )

            save_activity(
                user,
                "Decision and Reward",
                0,
                choice
            )

    # -----------------------------------------------------
    # STROOP CONTROL
    # -----------------------------------------------------

    elif experiment == "Stroop Control":

        st.subheader("🎨 Stroop Challenge")

        st.write(
            "Choose the INK COLOR, not the word meaning."
        )

        colors = [
            "Red",
            "Blue",
            "Green",
            "Yellow"
        ]

        word = random.choice(colors)

        ink_color = random.choice(
            [c for c in colors if c != word]
        )

        st.markdown(
            f"## {word}"
        )

        st.caption(
            f"Actual ink color: {ink_color}"
        )

        answer = st.radio(
            "What was the ink color?",
            colors
        )

        if st.button("Submit Stroop Answer"):

            if answer == ink_color:

                st.success("Correct!")

                save_activity(
                    user,
                    "Stroop Control",
                    100,
                    "Correct ink-color response"
                )

            else:

                st.error(
                    "Incorrect. Focus on the ink color."
                )

                save_activity(
                    user,
                    "Stroop Control",
                    0,
                    "Incorrect ink-color response"
                )

    # -----------------------------------------------------
    # PATTERN RECOGNITION
    # -----------------------------------------------------

    elif experiment == "Pattern Recognition":

        st.subheader("🔢 Number Pattern")

        st.markdown(
            "### 2 → 4 → 8 → 16 → 32 → ?"
        )

        answer = st.number_input(
            "Enter the next number",
            min_value=0,
            max_value=10000,
            step=1
        )

        if st.button("Check Pattern"):

            if answer == 64:

                st.success(
                    "Correct! Each number is multiplied by 2."
                )

                save_activity(
                    user,
                    "Pattern Recognition",
                    100,
                    "Correct pattern answer"
                )

            else:

                st.error(
                    "Try again. Look at how each number changes."
                )

                save_activity(
                    user,
                    "Pattern Recognition",
                    0,
                    "Incorrect pattern answer"
                )

    st.divider()

    st.caption(
        "These activities are educational demonstrations. "
        "They do not measure brain activity, diagnose conditions "
        "or provide clinical cognitive assessments."
    )


# =========================================================
# END OF PART 3
# =========================================================
# =========================================================
# PART 4 — SECURITY MIGRATION
# =========================================================

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None
    InvalidToken = Exception


def ensure_user_security_columns():

    conn = db()

    try:

        existing_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(users)"
            ).fetchall()
        }

        required_columns = {
            "journal_pin_hash": "TEXT",
            "journal_pin_failures": "INTEGER DEFAULT 0",
            "journal_locked_until": "TEXT"
        }

        for column, definition in required_columns.items():

            if column not in existing_columns:

                conn.execute(
                    f"ALTER TABLE users ADD COLUMN "
                    f"{column} {definition}"
                )

        conn.commit()

    finally:
        conn.close()


ensure_user_security_columns()


# =========================================================
# JOURNAL ENCRYPTION
# =========================================================

def get_journal_fernet():

    if Fernet is None:
        return None

    key = get_secret_value(
        "JOURNAL_ENCRYPTION_KEY"
    )

    if not key:
        return None

    try:

        return Fernet(
            key.encode("utf-8")
        )

    except Exception:

        return None


def encrypt_journal_text(value):

    fernet = get_journal_fernet()

    if fernet is None:
        raise RuntimeError(
            "Journal encryption is not configured."
        )

    encrypted = fernet.encrypt(
        str(value).encode("utf-8")
    )

    return "enc:v1:" + encrypted.decode("utf-8")


def decrypt_journal_text(value):

    if value is None:
        return ""

    if not value.startswith("enc:v1:"):

        raise ValueError(
            "This is an older unencrypted journal entry."
        )

    fernet = get_journal_fernet()

    if fernet is None:

        raise RuntimeError(
            "Journal encryption key is unavailable."
        )

    encrypted = value[len("enc:v1:"):].encode("utf-8")

    try:

        return fernet.decrypt(
            encrypted
        ).decode("utf-8")

    except InvalidToken:

        raise ValueError(
            "Journal entry could not be decrypted. "
            "Check the encryption key."
        )


# =========================================================
# PRIVATE JOURNAL PIN SECURITY
# =========================================================

def hash_journal_pin(pin):

    salt = os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        310000
    )

    return (
        salt.hex()
        + ":"
        + digest.hex()
    )


def verify_journal_pin(pin, stored_hash):

    try:

        salt_hex, expected_hash = stored_hash.split(":", 1)

        salt = bytes.fromhex(salt_hex)

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            310000
        ).hex()

        return hmac.compare_digest(
            digest,
            expected_hash
        )

    except (ValueError, TypeError, AttributeError):

        return False


def journal_is_locked(user_id):

    row = query(
        """
        SELECT journal_locked_until
        FROM users
        WHERE id=?
        """,
        (user_id,),
        one=True
    )

    if not row or not row["journal_locked_until"]:
        return False

    try:

        locked_until = datetime.fromisoformat(
            row["journal_locked_until"]
        )

        return datetime.now() < locked_until

    except (ValueError, TypeError):

        return False


def record_journal_pin_failure(user_id):

    row = query(
        """
        SELECT journal_pin_failures
        FROM users
        WHERE id=?
        """,
        (user_id,),
        one=True
    )

    failures = (
        row["journal_pin_failures"] or 0
        if row else 0
    )

    failures += 1

    locked_until = None

    if failures >= 5:

        locked_until = (
            datetime.now() + timedelta(minutes=15)
        ).strftime("%Y-%m-%d %H:%M:%S")

        failures = 0

    execute(
        """
        UPDATE users
        SET journal_pin_failures=?,
            journal_locked_until=?
        WHERE id=?
        """,
        (
            failures,
            locked_until,
            user_id
        )
    )


def clear_journal_pin_failures(user_id):

    execute(
        """
        UPDATE users
        SET journal_pin_failures=0,
            journal_locked_until=NULL
        WHERE id=?
        """,
        (user_id,)
    )


def journal_pin_exists(user_id):

    row = query(
        """
        SELECT journal_pin_hash
        FROM users
        WHERE id=?
        """,
        (user_id,),
        one=True
    )

    return bool(
        row and row["journal_pin_hash"]
    )


def set_journal_pin(user_id, pin):

    if not re.fullmatch(r"\d{6}", pin):
        raise ValueError(
            "PIN must contain exactly 6 digits."
        )

    execute(
        """
        UPDATE users
        SET journal_pin_hash=?,
            journal_pin_failures=0,
            journal_locked_until=NULL
        WHERE id=?
        """,
        (
            hash_journal_pin(pin),
            user_id
        )
    )


def check_journal_pin(user_id, pin):

    if journal_is_locked(user_id):
        return False

    row = query(
        """
        SELECT journal_pin_hash
        FROM users
        WHERE id=?
        """,
        (user_id,),
        one=True
    )

    if not row or not row["journal_pin_hash"]:
        return False

    if verify_journal_pin(
        pin,
        row["journal_pin_hash"]
    ):

        clear_journal_pin_failures(user_id)

        return True

    record_journal_pin_failure(user_id)

    return False


# =========================================================
# JOURNAL SESSION LOCK
# =========================================================

def journal_session_key(user_id):

    return f"journal_unlock_{user_id}"


def journal_is_unlocked(user_id):

    key = journal_session_key(user_id)

    session = st.session_state.get(key)

    if not session:
        return False

    current_time = datetime.now().timestamp()

    if current_time - session > 600:

        st.session_state.pop(key, None)

        return False

    st.session_state[key] = current_time

    return True


def unlock_journal(user_id):

    st.session_state[
        journal_session_key(user_id)
    ] = datetime.now().timestamp()


def lock_journal(user_id):

    st.session_state.pop(
        journal_session_key(user_id),
        None
    )


# =========================================================
# PRIVATE JOURNAL PAGE
# =========================================================

def private_journal_page(user):

    uid = user["id"]

    section_title(
        "🔒 Private Journal",
        "A private space for reflection and personal writing."
    )

    st.warning(
        "Your journal is designed to use encryption. "
        "Do not enter private information until encryption "
        "is configured and tested."
    )

    if Fernet is None:

        st.error(
            "The cryptography package is missing. "
            "Install cryptography in requirements.txt."
        )

        return

    if get_journal_fernet() is None:

        st.error(
            "Journal encryption key is missing or invalid. "
            "Add JOURNAL_ENCRYPTION_KEY to Streamlit Secrets."
        )

        return

    if not journal_pin_exists(uid):

        st.subheader("Create Your Private PIN")

        st.write(
            "Create a six-digit PIN to lock your journal."
        )

        with st.form("create_journal_pin_form"):

            pin1 = st.text_input(
                "Create six-digit PIN",
                type="password",
                max_chars=6
            )

            pin2 = st.text_input(
                "Confirm PIN",
                type="password",
                max_chars=6
            )

            submitted = st.form_submit_button(
                "Create PIN"
            )

        if submitted:

            if not re.fullmatch(r"\d{6}", pin1):

                st.error(
                    "PIN must contain exactly six digits."
                )

            elif pin1 != pin2:

                st.error("PINs do not match.")

            else:

                set_journal_pin(uid, pin1)

                st.success(
                    "Your journal PIN has been created."
                )

                st.rerun()

        return

    if not journal_is_unlocked(uid):

        st.subheader("🔐 Unlock Private Journal")

        if journal_is_locked(uid):

            st.error(
                "Journal temporarily locked after "
                "repeated incorrect PIN attempts. "
                "Try again after 15 minutes."
            )

            return

        with st.form("unlock_journal_form"):

            entered_pin = st.text_input(
                "Enter your six-digit PIN",
                type="password",
                max_chars=6
            )

            submitted = st.form_submit_button(
                "Unlock Journal"
            )

        if submitted:

            if check_journal_pin(uid, entered_pin):

                unlock_journal(uid)

                st.success("Journal unlocked.")

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN or journal temporarily locked."
                )

        return

    st.success("Private journal unlocked.")

    if st.button("🔒 Lock Journal Now"):

        lock_journal(uid)

        st.rerun()

    st.divider()

    st.subheader("Write a Private Entry")

    with st.form("private_journal_entry_form"):

        title = st.text_input(
            "Entry title"
        )

        mood = st.selectbox(
            "How are you feeling?",
            [
                "Not specified",
                "Calm",
                "Happy",
                "Sad",
                "Anxious",
                "Stressed",
                "Confused",
                "Hopeful",
                "Grateful"
            ]
        )

        body = st.text_area(
            "Your thoughts",
            height=180,
            placeholder="Write your private reflection here..."
        )

        submitted = st.form_submit_button(
            "Save Encrypted Entry"
        )

    if submitted:

        if not title.strip() or not body.strip():

            st.error(
                "Please enter a title and journal text."
            )

        else:

            try:

                encrypted_title = encrypt_journal_text(
                    title.strip()
                )

                encrypted_body = encrypt_journal_text(
                    body.strip()
                )

                encrypted_mood = encrypt_journal_text(
                    mood
                )

                execute(
                    """
                    INSERT INTO journal
                    (
                        user_id,
                        title,
                        body,
                        mood,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        uid,
                        encrypted_title,
                        encrypted_body,
                        encrypted_mood,
                        now()
                    )
                )

                st.success(
                    "Encrypted journal entry saved."
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Could not save encrypted entry: {error}"
                )

    st.divider()

    st.subheader("Your Private Entries")

    entries = get_user_rows(
        "journal",
        uid
    )

    if not entries:

        st.info(
            "You have not created any journal entries yet."
        )

    for entry in entries:

        try:

            entry_title = decrypt_journal_text(
                entry["title"]
            )

            entry_body = decrypt_journal_text(
                entry["body"]
            )

            entry_mood = decrypt_journal_text(
                entry["mood"]
            )

        except ValueError as error:

            st.warning(
                f"Entry #{entry['id']}: {error}"
            )

            continue

        except Exception:

            st.error(
                f"Entry #{entry['id']} could not be opened."
            )

            continue

        with st.expander(
            f"{entry_title} — {entry['created_at']}"
        ):

            st.caption(
                f"Mood: {entry_mood}"
            )

            st.write(entry_body)

            if st.button(
                "Delete Entry",
                key=f"delete_journal_{entry['id']}"
            ):

                execute(
                    """
                    DELETE FROM journal
                    WHERE id=? AND user_id=?
                    """,
                    (
                        entry["id"],
                        uid
                    )
                )

                st.success("Entry deleted.")

                st.rerun()


# =========================================================
# PERSONAL HEALING — TEXT AND VOICE
# =========================================================

def personal_healing_page(user):

    section_title(
        "💙 Personal Healing",
        "A private space to reflect, express emotions and explore your thoughts."
    )

    st.info(
        "Ayna AI can offer supportive conversation and "
        "reflection prompts. It is not a therapist, "
        "medical professional or emergency service."
    )

    if "healing_messages" not in st.session_state:

        st.session_state["healing_messages"] = []

    if "healing_user_id" not in st.session_state:

        st.session_state["healing_user_id"] = user["id"]

    if st.session_state["healing_user_id"] != user["id"]:

        st.session_state["healing_messages"] = []

        st.session_state["healing_user_id"] = user["id"]

    for message in st.session_state["healing_messages"]:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    st.caption(
        "This conversation stays in the current app session "
        "and is not saved as a journal entry."
    )

    prompt = st.chat_input(
        "Share what is on your mind..."
    )

    if prompt:

        st.session_state["healing_messages"].append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):

            st.markdown(prompt)

        healing_instruction = """
        You are Ayna, a compassionate supportive AI
        inside NeuroLens.

        Respond with empathy, patience and respect.
        Help the user name emotions and explore thoughts.
        Use gentle, non-judgmental questions.
        Do not diagnose or claim to provide therapy.
        Do not encourage dependence on AI.
        Encourage trusted human or professional support
        when appropriate.

        If someone may be in immediate danger or at risk
        of self-harm, encourage contacting local emergency
        services and a trusted person immediately.
        """

        with st.chat_message("assistant"):

            with st.spinner("Ayna is listening..."):

                answer = ask_gemini(
                    prompt,
                    healing_instruction
                )

                st.markdown(answer)

        st.session_state["healing_messages"].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.rerun()

    st.divider()

    st.subheader("🎙️ Voice Reflection")

    st.write(
        "You can record a short voice message and ask "
        "Ayna to help you reflect on it."
    )

    audio = st.audio_input(
        "Record your voice"
    )

    if audio:

        st.audio(audio)

        if st.button("Send Voice to Ayna"):

            client = get_gemini_client()

            if client is None:

                st.error(
                    "Gemini AI is not configured."
                )

            else:

                try:

                    audio_part = types.Part.from_bytes(
                        data=audio.getvalue(),
                        mime_type=audio.type or "audio/wav"
                    )

                    voice_instruction = """
                    You are Ayna, a supportive AI assistant.

                    Listen to the supplied audio.
                    First provide a careful transcription
                    of the spoken words, then offer a brief,
                    empathetic reflection.

                    Do not diagnose or claim to provide therapy.
                    If the audio is unclear, say so.
                    """

                    with st.spinner(
                        "Ayna is processing your voice..."
                    ):

                        response = client.models.generate_content(
                            model=MODEL,
                            contents=[
                                voice_instruction,
                                audio_part
                            ]
                        )

                    voice_answer = getattr(
                        response,
                        "text",
                        None
                    )

                    if voice_answer:

                        st.markdown(voice_answer)

                    else:

                        st.warning(
                            "Ayna could not interpret this recording."
                        )

                except Exception as error:

                    st.error(
                        "Voice processing failed. "
                        f"Details: {str(error)[:250]}"
                    )

    st.caption(
        "Voice recordings are processed when you press "
        "Send Voice to Ayna. Avoid recording sensitive "
        "information unless you are comfortable sending "
        "it to the configured AI provider."
    )


# =========================================================
# BRAIN PUZZLE
# =========================================================

def brain_puzzle_page(user):

    section_title(
        "🧩 Brain Puzzle",
        "Challenge your reasoning and pattern recognition."
    )

    puzzle_type = st.selectbox(
        "Choose puzzle difficulty",
        [
            "3 × 3 Number Puzzle",
            "4 × 4 Number Puzzle"
        ]
    )

    if puzzle_type == "3 × 3 Number Puzzle":

        st.subheader("3 × 3 Pattern")

        st.markdown(
            """
            | 2 | 4 | 6 |
            |---|---|---|
            | 3 | 6 | 9 |
            | 4 | 8 | ? |
            """
        )

        answer = st.number_input(
            "What is the missing number?",
            min_value=0,
            max_value=100,
            step=1,
            key="puzzle_3_answer"
        )

        if st.button("Check 3 × 3 Answer"):

            if answer == 12:

                st.success(
                    "Correct! Each row increases by multiples "
                    "of its first number."
                )

                save_activity(
                    user,
                    "Brain Puzzle 3x3",
                    100,
                    "Correct answer: 12"
                )

            else:

                st.error(
                    "Try again. Look at the multiplication pattern."
                )

                save_activity(
                    user,
                    "Brain Puzzle 3x3",
                    0,
                    "Incorrect answer"
                )

    else:

        st.subheader("4 × 4 Pattern")

        st.markdown(
            """
            | 1 | 2 | 3 | 4 |
            |---|---|---|---|
            | 2 | 4 | 6 | 8 |
            | 3 | 6 | 9 | 12 |
            | 4 | 8 | 12 | ? |
            """
        )

        answer = st.number_input(
            "Enter the missing number",
            min_value=0,
            max_value=100,
            step=1,
            key="puzzle_4_answer"
        )

        if st.button("Check 4 × 4 Answer"):

            if answer == 16:

                st.success(
                    "Correct! You identified the pattern."
                )

                save_activity(
                    user,
                    "Brain Puzzle 4x4",
                    100,
                    "Correct answer: 16"
                )

            else:

                st.error(
                    "Try again. Check the row and column pattern."
                )

                save_activity(
                    user,
                    "Brain Puzzle 4x4",
                    0,
                    "Incorrect answer"
                )

    st.caption(
        "These puzzles are for learning and entertainment. "
        "They are not clinical measures of intelligence "
        "or cognitive ability."
    )


# =========================================================
# END OF PART 4
# =========================================================
# =========================================================
# PART 5 — RESEARCH BOOK
# =========================================================

def research_book_page(user):

    uid = user["id"]

    section_title(
        "📚 Research Book",
        "Organize your cognitive neuroscience research and ideas."
    )

    st.subheader("Create Research Note")

    with st.form("research_note_form"):

        title = st.text_input(
            "Research title"
        )

        topic = st.selectbox(
            "Research topic",
            [
                "Consciousness and Awareness",
                "Cognitive Neuroscience",
                "CSTC Circuits",
                "Memory and Learning",
                "Attention and Reward",
                "Emotion and Decision-Making",
                "Neuroplasticity",
                "Addiction and Cognition",
                "AI and Neuroscience",
                "Other"
            ]
        )

        notes = st.text_area(
            "Research notes",
            height=180
        )

        tags = st.text_input(
            "Tags (comma separated)"
        )

        submitted = st.form_submit_button(
            "Save Research Note"
        )

    if submitted:

        if not title.strip() or not notes.strip():

            st.error(
                "Please enter a title and research notes."
            )

        else:

            execute(
                """
                INSERT INTO research
                (
                    user_id,
                    title,
                    topic,
                    notes,
                    tags,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    uid,
                    title.strip(),
                    topic,
                    notes.strip(),
                    tags.strip(),
                    now()
                )
            )

            st.success("Research note saved.")

            st.rerun()

    st.divider()

    st.subheader("Your Research Library")

    entries = get_user_rows(
        "research",
        uid
    )

    if not entries:

        st.info(
            "Your research library is empty."
        )

    for entry in entries:

        with st.expander(
            f"📄 {entry['title']} — {entry['topic']}"
        ):

            st.caption(
                f"Created: {entry['created_at']}"
            )

            if entry["tags"]:

                st.write(
                    f"Tags: {entry['tags']}"
                )

            st.write(entry["notes"])

            if st.button(
                "Delete Research Note",
                key=f"delete_research_{entry['id']}"
            ):

                execute(
                    """
                    DELETE FROM research
                    WHERE id=? AND user_id=?
                    """,
                    (
                        entry["id"],
                        uid
                    )
                )

                st.success("Research note deleted.")

                st.rerun()


# =========================================================
# PART 5 — CONCEPT MAP
# =========================================================

def concept_map_page(user):

    uid = user["id"]

    section_title(
        "🕸️ Concept Map",
        "Connect scientific concepts and build your own knowledge network."
    )

    st.subheader("Add a Concept")

    with st.form("concept_form"):

        concept = st.text_input(
            "Concept name"
        )

        connects_to = st.text_input(
            "Connected concept (optional)"
        )

        explanation = st.text_area(
            "Explain the relationship"
        )

        submitted = st.form_submit_button(
            "Add Concept"
        )

    if submitted:

        if not concept.strip():

            st.error(
                "Please enter a concept name."
            )

        else:

            execute(
                """
                INSERT INTO concepts
                (
                    user_id,
                    concept,
                    connects_to,
                    explanation,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    uid,
                    concept.strip(),
                    connects_to.strip(),
                    explanation.strip(),
                    now()
                )
            )

            st.success("Concept added.")

            st.rerun()

    st.divider()

    st.subheader("Your Knowledge Network")

    concepts = get_user_rows(
        "concepts",
        uid
    )

    if not concepts:

        st.info(
            "Start by adding your first scientific concept."
        )

        return

    for item in concepts:

        with st.expander(
            f"🧠 {item['concept']}"
        ):

            if item["connects_to"]:

                st.write(
                    f"**Connected to:** {item['connects_to']}"
                )

            if item["explanation"]:

                st.write(item["explanation"])

            st.caption(item["created_at"])

            if st.button(
                "Delete Concept",
                key=f"delete_concept_{item['id']}"
            ):

                execute(
                    """
                    DELETE FROM concepts
                    WHERE id=? AND user_id=?
                    """,
                    (
                        item["id"],
                        uid
                    )
                )

                st.rerun()

    st.divider()

    st.subheader("Concept Connections")

    st.caption(
        "This view displays your saved concept relationships."
    )

    for item in concepts:

        if item["connects_to"]:

            st.markdown(
                f"**{item['concept']}** → "
                f"**{item['connects_to']}**"
            )

    try:

        import graphviz

        graph = graphviz.Digraph()

        graph.attr(
            rankdir="LR"
        )

        for item in concepts:

            graph.node(
                item["concept"]
            )

            if item["connects_to"]:

                graph.edge(
                    item["concept"],
                    item["connects_to"]
                )

        st.graphviz_chart(graph)

    except ImportError:

        st.info(
            "Install graphviz to enable the visual concept map."
        )

    except Exception:

        st.info(
            "Some concepts could not be displayed in the graph."
        )


# =========================================================
# PART 5 — VOICE STUDIO
# =========================================================

def voice_studio_page(user):

    section_title(
        "🎙️ Voice Studio",
        "Record your thoughts and explore voice-based reflection."
    )

    st.write(
        """
        Use Voice Studio to record an idea, research thought
        or personal reflection.

        Recordings are not automatically stored in the
        research library.
        """
    )

    audio = st.audio_input(
        "Record a voice message",
        key="voice_studio_recording"
    )

    if audio:

        st.audio(audio)

        st.caption(
            f"Recording size: {len(audio.getvalue())} bytes"
        )

        if st.button(
            "Analyze Recording with Ayna"
        ):

            client = get_gemini_client()

            if client is None:

                st.error(
                    "Gemini AI is not configured."
                )

            else:

                try:

                    audio_part = types.Part.from_bytes(
                        data=audio.getvalue(),
                        mime_type=audio.type or "audio/wav"
                    )

                    instruction = """
                    You are Ayna, the neuroscience assistant
                    inside NeuroLens.

                    Analyze the supplied audio.

                    1. Transcribe the spoken content if possible.
                    2. Summarize the main idea.
                    3. Identify any neuroscience-related concepts.
                    4. Clearly mention uncertainty if the audio
                       is unclear.

                    Do not invent words or scientific facts.
                    """

                    with st.spinner(
                        "Analyzing your recording..."
                    ):

                        response = client.models.generate_content(
                            model=MODEL,
                            contents=[
                                instruction,
                                audio_part
                            ]
                        )

                    result = getattr(
                        response,
                        "text",
                        None
                    )

                    if result:

                        st.subheader("Ayna's Analysis")

                        st.markdown(result)

                    else:

                        st.warning(
                            "No analysis was returned."
                        )

                except Exception as error:

                    st.error(
                        "Audio analysis failed: "
                        f"{str(error)[:250]}"
                    )

    st.divider()

    st.subheader("Write a Voice Reflection")

    reflection = st.text_area(
        "Write your reflection or voice-note summary",
        key="voice_reflection_text"
    )

    if st.button(
        "Save Reflection"
    ):

        if not reflection.strip():

            st.warning(
                "Please write something first."
            )

        else:

            execute(
                """
                INSERT INTO voice_logs
                (
                    user_id,
                    transcript,
                    reflection,
                    emoji,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    "",
                    reflection.strip(),
                    "🎙️",
                    now()
                )
            )

            st.success(
                "Your written reflection has been saved."
            )

            st.rerun()

    st.divider()

    st.subheader("Saved Reflections")

    logs = get_user_rows(
        "voice_logs",
        user["id"]
    )

    if not logs:

        st.info(
            "No saved reflections yet."
        )

    for item in logs:

        with st.expander(
            f"🎙️ Reflection — {item['created_at']}"
        ):

            st.write(item["reflection"])

            if st.button(
                "Delete Reflection",
                key=f"delete_voice_{item['id']}"
            ):

                execute(
                    """
                    DELETE FROM voice_logs
                    WHERE id=? AND user_id=?
                    """,
                    (
                        item["id"],
                        user["id"]
                    )
                )

                st.rerun()


# =========================================================
# PART 5 — PROGRESS DASHBOARD
# =========================================================

def progress_dashboard_page(user):

    uid = user["id"]

    section_title(
        "📊 Progress Dashboard",
        "Review your saved learning activities and research progress."
    )

    activities = get_user_rows(
        "activities",
        uid
    )

    research = get_user_rows(
        "research",
        uid
    )

    concepts = get_user_rows(
        "concepts",
        uid
    )

    journal_entries = get_user_rows(
        "journal",
        uid
    )

    voice_entries = get_user_rows(
        "voice_logs",
        uid
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Activities",
            len(activities)
        )

    with col2:

        st.metric(
            "Research Notes",
            len(research)
        )

    with col3:

        st.metric(
            "Concepts",
            len(concepts)
        )

    col4, col5 = st.columns(2)

    with col4:

        st.metric(
            "Journal Entries",
            len(journal_entries)
        )

    with col5:

        st.metric(
            "Saved Reflections",
            len(voice_entries)
        )

    st.divider()

    st.subheader("Activity History")

    if not activities:

        st.info(
            "Complete a neuroscience lab activity to see your history."
        )

        return

    activity_data = []

    for item in activities:

        activity_data.append(
            {
                "Activity": item["activity"],
                "Score": item["score"],
                "Date": item["created_at"]
            }
        )

    df = pd.DataFrame(activity_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    numeric_scores = pd.to_numeric(
        df["Score"],
        errors="coerce"
    ).dropna()

    if not numeric_scores.empty:

        average_score = float(
            numeric_scores.mean()
        )

        st.metric(
            "Average Recorded Activity Score",
            f"{average_score:.1f}%"
        )

        st.caption(
            "This is an average of saved activity scores, "
            "not a clinical cognitive performance measure."
        )

        st.subheader("Activity Score History")

        chart_df = df.copy()

        chart_df["Score"] = pd.to_numeric(
            chart_df["Score"],
            errors="coerce"
        )

        st.line_chart(
            chart_df.set_index("Date")["Score"]
        )

    st.divider()

    st.subheader("Your Learning Activity")

    activity_counts = (
        df.groupby("Activity")
        .size()
        .reset_index(name="Completed")
    )

    st.bar_chart(
        activity_counts.set_index("Activity")
    )

    st.caption(
        "Progress reflects activity recorded inside NeuroLens. "
        "It does not measure intelligence, brain activity, "
        "or neurological health."
    )


# =========================================================
# END OF PART 5
# =========================================================
# =========================================================
# PART 6 — APPOINTMENTS
# =========================================================

def appointments_page(user):

    uid = user["id"]

    section_title(
        "📅 Appointments",
        "Submit an appointment or consultation request."
    )

    st.info(
        "Submitting a request does not confirm a booking. "
        "The owner must review and update its status."
    )

    with st.form("appointment_form"):

        topic = st.selectbox(
            "Appointment topic",
            [
                "Cognitive Neuroscience Discussion",
                "Research Consultation",
                "AI and Neuroscience",
                "Learning and Memory",
                "Other"
            ]
        )

        preferred_date = st.date_input(
            "Preferred date"
        )

        preferred_time = st.selectbox(
            "Preferred time",
            [
                "Morning",
                "Afternoon",
                "Evening"
            ]
        )

        message = st.text_area(
            "Additional details"
        )

        submitted = st.form_submit_button(
            "Submit Request"
        )

    if submitted:

        execute(
            """
            INSERT INTO appointments
            (
                user_id,
                topic,
                preferred_date,
                preferred_time,
                message,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, 'Pending', ?)
            """,
            (
                uid,
                topic,
                str(preferred_date),
                preferred_time,
                message.strip(),
                now()
            )
        )

        st.success(
            "Your appointment request has been submitted."
        )

        st.rerun()

    st.divider()

    st.subheader("My Appointment Requests")

    requests = get_user_rows(
        "appointments",
        uid
    )

    if not requests:

        st.info("No appointment requests yet.")

    for item in requests:

        with st.expander(
            f"{item['topic']} — {item['status']}"
        ):

            st.write(
                f"**Date:** {item['preferred_date']}"
            )

            st.write(
                f"**Time:** {item['preferred_time']}"
            )

            st.write(
                f"**Message:** {item['message'] or 'None'}"
            )

            st.caption(
                f"Submitted: {item['created_at']}"
            )


# =========================================================
# PART 6 — NEUROSOCIAL
# =========================================================

def neurosocial_page(user):

    uid = user["id"]

    section_title(
        "🌐 NeuroSocial",
        "Share neuroscience ideas and learn with the community."
    )

    st.caption(
        "Do not share private journal entries, passwords "
        "or sensitive personal information here."
    )

    with st.form("create_social_post"):

        post_body = st.text_area(
            "Share a thought, question or research idea",
            max_chars=2000
        )

        submitted = st.form_submit_button(
            "Publish Post"
        )

    if submitted:

        if not post_body.strip():

            st.error("Post cannot be empty.")

        else:

            execute(
                """
                INSERT INTO posts
                (
                    user_id,
                    body,
                    created_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    uid,
                    post_body.strip(),
                    now()
                )
            )

            st.success("Your post has been published.")

            st.rerun()

    st.divider()

    st.subheader("Community Feed")

    posts = query(
        """
        SELECT
            posts.id,
            posts.user_id,
            posts.body,
            posts.created_at,
            users.username
        FROM posts
        JOIN users
            ON users.id = posts.user_id
        WHERE users.is_active=1
        ORDER BY posts.id DESC
        LIMIT 100
        """
    )

    if not posts:

        st.info(
            "No community posts yet. Be the first to share an idea."
        )

    for post in posts:

        with st.container(border=True):

            st.markdown(
                f"**@{post['username']}**"
            )

            st.write(post["body"])

            st.caption(post["created_at"])

            reaction_count = query(
                """
                SELECT COUNT(*) AS total
                FROM reactions
                WHERE post_id=?
                """,
                (post["id"],),
                one=True
            )

            st.caption(
                f"❤️ {reaction_count['total']} reactions"
            )

            existing_reaction = query(
                """
                SELECT id
                FROM reactions
                WHERE post_id=? AND user_id=?
                """,
                (
                    post["id"],
                    uid
                ),
                one=True
            )

            if existing_reaction:

                if st.button(
                    "Remove Reaction",
                    key=f"unlike_{post['id']}"
                ):

                    execute(
                        """
                        DELETE FROM reactions
                        WHERE post_id=? AND user_id=?
                        """,
                        (
                            post["id"],
                            uid
                        )
                    )

                    st.rerun()

            else:

                if st.button(
                    "❤️ React",
                    key=f"like_{post['id']}"
                ):

                    execute(
                        """
                        INSERT OR IGNORE INTO reactions
                        (
                            post_id,
                            user_id,
                            reaction
                        )
                        VALUES (?, ?, 'heart')
                        """,
                        (
                            post["id"],
                            uid
                        )
                    )

                    st.rerun()

            comments = query(
                """
                SELECT
                    comments.id,
                    comments.body,
                    comments.created_at,
                    users.username
                FROM comments
                JOIN users
                    ON users.id=comments.user_id
                WHERE comments.post_id=?
                ORDER BY comments.id ASC
                LIMIT 50
                """,
                (post["id"],)
            )

            if comments:

                st.markdown("**Comments**")

                for comment in comments:

                    st.write(
                        f"@{comment['username']}: "
                        f"{comment['body']}"
                    )

            with st.form(
                f"comment_form_{post['id']}"
            ):

                comment_text = st.text_input(
                    "Write a comment",
                    max_chars=500,
                    key=f"comment_input_{post['id']}"
                )

                comment_submit = st.form_submit_button(
                    "Comment"
                )

            if comment_submit:

                if comment_text.strip():

                    execute(
                        """
                        INSERT INTO comments
                        (
                            post_id,
                            user_id,
                            body,
                            created_at
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            post["id"],
                            uid,
                            comment_text.strip(),
                            now()
                        )
                    )

                    st.rerun()

            if post["user_id"] == uid:

                if st.button(
                    "Delete My Post",
                    key=f"delete_post_{post['id']}"
                ):

                    execute(
                        """
                        DELETE FROM posts
                        WHERE id=? AND user_id=?
                        """,
                        (
                            post["id"],
                            uid
                        )
                    )

                    st.rerun()


# =========================================================
# PART 6 — SETTINGS
# =========================================================

def settings_page(user):

    section_title(
        "⚙️ Settings",
        "Manage your account and connection settings."
    )

    st.subheader("Account Information")

    st.write(
        f"**Username:** @{user['username']}"
    )

    st.write(
        f"**Role:** {user['role'].title()}"
    )

    st.write(
        f"**Email:** {user.get('email') or 'Not provided'}"
    )

    st.divider()

    st.subheader("Password")

    if st.button(
        "Open Change Password"
    ):

        st.session_state["settings_open_password"] = True

    if st.session_state.get(
        "settings_open_password",
        False
    ):

        change_password_page(user)

    st.divider()

    st.subheader("Connection Status")

    if st.button(
        "Test Gemini AI"
    ):

        if get_gemini_client() is None:

            st.error(
                "Gemini AI is not configured."
            )

        else:

            with st.spinner("Testing Gemini..."):

                result = ask_gemini(
                    "Reply with: NeuroLens Gemini connection test successful."
                )

            st.write(result)

    if st.button(
        "Test Supabase"
    ):

        success, message = test_supabase_connection()

        if success:

            st.success(message)

        else:

            st.error(message)

    st.divider()

    st.subheader("Session")

    if st.button(
        "Log Out",
        type="primary"
    ):

        logout()


# =========================================================
# PART 6 — OWNER ACCESS CONTROL
# =========================================================

def require_owner(user):

    if not user:

        st.error("Please log in.")

        return False

    if user["role"] != "owner":

        st.error(
            "Access denied. Owner permission is required."
        )

        return False

    return True


# =========================================================
# PART 6 — OWNER CONTROL CENTER
# =========================================================

def owner_control_center(user):

    if not require_owner(user):
        return

    section_title(
        "👑 Owner Control Center",
        "NeuroLens administration and overview."
    )

    users = query(
        """
        SELECT id, username, role, is_active, created_at
        FROM users
        ORDER BY id DESC
        """
    )

    posts = query(
        "SELECT COUNT(*) AS total FROM posts",
        one=True
    )

    research = query(
        "SELECT COUNT(*) AS total FROM research",
        one=True
    )

    appointments = query(
        "SELECT COUNT(*) AS total FROM appointments",
        one=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Users",
            len(users)
        )

    with col2:

        st.metric(
            "Community Posts",
            posts["total"]
        )

    with col3:

        st.metric(
            "Research Notes",
            research["total"]
        )

    with col4:

        st.metric(
            "Appointments",
            appointments["total"]
        )

    st.divider()

    st.subheader("User Accounts")

    for account in users:

        with st.expander(
            f"@{account['username']} — {account['role']}"
        ):

            st.write(
                f"User ID: {account['id']}"
            )

            st.write(
                f"Account created: {account['created_at']}"
            )

            st.write(
                f"Active: {'Yes' if account['is_active'] else 'No'}"
            )

            if account["role"] != "owner":

                new_status = st.selectbox(
                    "Account status",
                    ["Active", "Inactive"],
                    index=0 if account["is_active"] else 1,
                    key=f"account_status_{account['id']}"
                )

                if st.button(
                    "Update Account Status",
                    key=f"update_account_{account['id']}"
                ):

                    active_value = (
                        1 if new_status == "Active" else 0
                    )

                    execute(
                        """
                        UPDATE users
                        SET is_active=?
                        WHERE id=? AND role!='owner'
                        """,
                        (
                            active_value,
                            account["id"]
                        )
                    )

                    audit_event(
                        user["id"],
                        user["username"],
                        "account_status_changed",
                        "user",
                        account["id"],
                        new_status
                    )

                    st.success("Account status updated.")

                    st.rerun()

    st.divider()

    st.subheader("Appointment Requests")

    requests = query(
        """
        SELECT
            appointments.*,
            users.username
        FROM appointments
        JOIN users
            ON users.id=appointments.user_id
        ORDER BY appointments.id DESC
        LIMIT 100
        """
    )

    if not requests:

        st.info("No appointment requests.")

    for item in requests:

        with st.expander(
            f"@{item['username']} — {item['topic']}"
        ):

            st.write(
                f"Date: {item['preferred_date']}"
            )

            st.write(
                f"Time: {item['preferred_time']}"
            )

            st.write(
                f"Message: {item['message'] or 'None'}"
            )

            new_status = st.selectbox(
                "Request status",
                [
                    "Pending",
                    "Approved",
                    "Declined",
                    "Completed"
                ],
                index=[
                    "Pending",
                    "Approved",
                    "Declined",
                    "Completed"
                ].index(item["status"])
                if item["status"] in [
                    "Pending",
                    "Approved",
                    "Declined",
                    "Completed"
                ] else 0,
                key=f"appointment_status_{item['id']}"
            )

            if st.button(
                "Save Status",
                key=f"save_appointment_{item['id']}"
            ):

                execute(
                    """
                    UPDATE appointments
                    SET status=?
                    WHERE id=?
                    """,
                    (
                        new_status,
                        item["id"]
                    )
                )

                audit_event(
                    user["id"],
                    user["username"],
                    "appointment_status_changed",
                    "appointment",
                    item["id"],
                    new_status
                )

                st.success("Appointment status updated.")

                st.rerun()

    st.divider()

    st.subheader("System Information")

    st.write(
        f"**App:** {APP_NAME}"
    )

    st.write(
        f"**Owner display:** {OWNER}"
    )

    st.write(
        f"**AI model configured:** {MODEL}"
    )

    st.warning(
        "This dashboard does not display private journal "
        "contents. The current SQLite database is local "
        "application storage, not durable multi-user cloud storage."
    )


# =========================================================
# PART 6 — STAFF MANAGEMENT
# =========================================================

def staff_management(user):

    if not require_owner(user):
        return

    section_title(
        "👥 Staff Management",
        "Create and manage staff accounts."
    )

    with st.form("create_staff_form"):

        username = st.text_input(
            "Staff username"
        )

        email = st.text_input(
            "Staff email"
        )

        password = st.text_input(
            "Temporary password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Create Staff Account"
        )

    if submitted:

        username = username.strip().lower()

        if not re.fullmatch(
            r"[a-z0-9_.-]{3,30}",
            username
        ):

            st.error("Invalid username.")

        elif len(password) < 14:

            st.error(
                "Temporary password must have at least 14 characters."
            )

        else:

            try:

                staff_id = execute(
                    """
                    INSERT INTO users
                    (
                        username,
                        email,
                        password_hash,
                        created_at,
                        role,
                        is_active,
                        force_password_change
                    )
                    VALUES (?, ?, ?, ?, 'staff', 1, 1)
                    """,
                    (
                        username,
                        email.strip() or None,
                        hash_password(password),
                        now()
                    )
                )

                audit_event(
                    user["id"],
                    user["username"],
                    "staff_account_created",
                    "user",
                    staff_id
                )

                st.success(
                    "Staff account created. "
                    "The staff member must change the temporary password."
                )

                st.rerun()

            except sqlite3.IntegrityError:

                st.error(
                    "That username is already in use."
                )

    st.divider()

    st.subheader("Existing Staff")

    staff = query(
        """
        SELECT id, username, email, is_active, created_at
        FROM users
        WHERE role='staff'
        ORDER BY id DESC
        """
    )

    if not staff:

        st.info("No staff accounts yet.")

    for member in staff:

        st.write(
            f"**@{member['username']}** — "
            f"{'Active' if member['is_active'] else 'Inactive'}"
        )


# =========================================================
# PART 6 — AUDIT LOGS
# =========================================================

def audit_logs_page(user):

    if not require_owner(user):
        return

    section_title(
        "📋 Audit Logs",
        "Review administrative and account events."
    )

    logs = query(
        """
        SELECT *
        FROM audit_logs
        ORDER BY id DESC
        LIMIT 300
        """
    )

    if not logs:

        st.info("No audit logs available.")

        return

    data = []

    for item in logs:

        data.append(
            {
                "Date": item["created_at"],
                "Username": item["actor_username"],
                "Action": item["action"],
                "Target": item["target_type"],
                "Target ID": item["target_id"],
                "Details": item["details"]
            }
        )

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# END OF PART 6
# =========================================================
# ============================================================
# PART 7 — MAIN APP ROUTER, NAVIGATION & PHOTO STUDIO
# ============================================================


def photo_studio_page(user):
    st.title("📸 Photo Studio")
    st.caption("Upload and enhance images inside NeuroLens.")

    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg"],
        key="photo_studio_upload"
    )

    if uploaded_file is None:
        st.info("Upload an image to start editing.")
        return

    try:
        original_image = Image.open(uploaded_file).convert("RGB")

        st.subheader("Original Image")
        st.image(original_image, use_container_width=True)

        st.divider()
        st.subheader("Image Adjustments")

        brightness = st.slider(
            "Brightness",
            min_value=0.2,
            max_value=2.0,
            value=1.0,
            step=0.1
        )

        contrast = st.slider(
            "Contrast",
            min_value=0.2,
            max_value=2.0,
            value=1.0,
            step=0.1
        )

        sharpness = st.slider(
            "Sharpness",
            min_value=0.0,
            max_value=3.0,
            value=1.0,
            step=0.1
        )

        edited_image = ImageEnhance.Brightness(
            original_image
        ).enhance(brightness)

        edited_image = ImageEnhance.Contrast(
            edited_image
        ).enhance(contrast)

        edited_image = ImageEnhance.Sharpness(
            edited_image
        ).enhance(sharpness)

        st.subheader("Edited Image")
        st.image(edited_image, use_container_width=True)

        image_buffer = io.BytesIO()
        edited_image.save(image_buffer, format="PNG")

        st.download_button(
            label="⬇️ Download Edited Image",
            data=image_buffer.getvalue(),
            file_name="neurolens_edited_image.png",
            mime="image/png",
            use_container_width=True
        )

    except Exception as error:
        st.error(f"Could not process this image: {error}")


# ============================================================
# MAIN NAVIGATION
# ============================================================

def main():

    # Initialize application database
    init_db()

    # Check login
    if not get_user():
        login_screen()
        return

    user = get_user()

    if not user:
        login_screen()
        return

    uid = user.get("id")
    role = str(user.get("role", "member")).lower()

    # --------------------------------------------------------
    # FORCE PASSWORD CHANGE
    # --------------------------------------------------------

    if user.get("force_password_change"):
        st.warning(
            "For account security, please change your temporary password."
        )

        change_password_page(user)
        return

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    st.sidebar.title("🧠 NEUROLENS")

    st.sidebar.caption(
        "Explore cognition, behavior & the brain"
    )

    st.sidebar.divider()

    st.sidebar.write(
        f"Welcome, @{user.get('username', 'user')}"
    )

    st.sidebar.caption(
        f"Account role: {role.title()}"
    )

    st.sidebar.divider()

    # --------------------------------------------------------
    # AVAILABLE PAGES
    # --------------------------------------------------------

    pages = [
        "Home",
        "Brain Explorer",
        "CSTC Circuit Learning",
        "Neuroscience Lab",
        "Brain Puzzle",
        "Ask Ayna AI",
        "Personal Healing",
        "Private Journal",
        "Research Book",
        "Concept Map",
        "Voice Studio",
        "Photo Studio",
        "Progress Dashboard",
        "Appointments",
        "NeuroSocial",
        "Settings"
    ]

    # --------------------------------------------------------
    # OWNER-ONLY PAGES
    # --------------------------------------------------------

    if role == "owner":
        pages.extend([
            "Owner Control Center",
            "Staff Management",
            "Audit Logs"
        ])

    # --------------------------------------------------------
    # PAGE SELECTOR
    # --------------------------------------------------------

    selected_page = st.sidebar.radio(
        "Navigation",
        pages,
        key="neurolens_navigation"
    )

    st.sidebar.divider()

    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):
        logout()
        st.rerun()

    # --------------------------------------------------------
    # PAGE ROUTING
    # --------------------------------------------------------

    if selected_page == "Home":
        home_page(user)

    elif selected_page == "Brain Explorer":
        brain_explorer_page(user)

    elif selected_page == "CSTC Circuit Learning":
        cstc_circuit_page(user)

    elif selected_page == "Neuroscience Lab":
        neuroscience_lab_page(user)

    elif selected_page == "Brain Puzzle":
        brain_puzzle_page(user)

    elif selected_page == "Ask Ayna AI":
        ask_ayna_page(user)

    elif selected_page == "Personal Healing":
        personal_healing_page(user)

    elif selected_page == "Private Journal":
        private_journal_page(user)

    elif selected_page == "Research Book":
        research_book_page(user)

    elif selected_page == "Concept Map":
        concept_map_page(user)

    elif selected_page == "Voice Studio":
        voice_studio_page(user)

    elif selected_page == "Photo Studio":
        photo_studio_page(user)

    elif selected_page == "Progress Dashboard":
        progress_dashboard_page(user)

    elif selected_page == "Appointments":
        appointments_page(user)

    elif selected_page == "NeuroSocial":
        neurosocial_page(user)

    elif selected_page == "Settings":
        settings_page(user)

    # --------------------------------------------------------
    # OWNER PAGES
    # --------------------------------------------------------

    elif selected_page == "Owner Control Center":

        if role == "owner":
            owner_control_center(user)
        else:
            st.error("Access denied.")

    elif selected_page == "Staff Management":

        if role == "owner":
            staff_management(user)
        else:
            st.error("Access denied.")

    elif selected_page == "Audit Logs":

        if role == "owner":
            audit_logs_page(user)
        else:
            st.error("Access denied.")

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    st.divider()

    st.caption(
        "NEUROLENS | Explore cognition, behavior & the brain"
    )

    st.caption(
        "Created by Ayna Jaffri"
    )

    st.caption(
        "Educational neuroscience platform. "
        "Activities are not clinical assessments or diagnoses."
    )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()

# ============================================================
# END OF NEUROLENS APP CODE
# ============================================================
