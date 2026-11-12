
import os
import io
import re
import json
import random
import sqlite3
import hashlib
import hmac
from datetime import datetime
from contextlib import closing

import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

try:
    from supabase import create_client
except Exception:
    create_client = None


# =========================================================
# APP CONFIGURATION
# =========================================================

APP_NAME = "NEUROLENS"
OWNER = "Ayna Jaffri"
DB_PATH = "neurolens.db"

# Current stable Gemini model
MODEL = "gemini-3.8-flash"

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
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    last_login TEXT
);


    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        mood TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS research (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        topic TEXT,
        notes TEXT,
        tags TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity TEXT NOT NULL,
        score REAL,
        details TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS voice_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        transcript TEXT,
        reflection TEXT,
        emoji TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
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
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        reaction TEXT NOT NULL,
        UNIQUE(post_id, user_id),
        FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS concepts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        concept TEXT NOT NULL,
        connects_to TEXT,
        explanation TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
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

        # Safe migration for existing users
        existing_columns = {
            row[1] for row in
            conn.execute("PRAGMA table_info(users)").fetchall()
        }

        migrations = {
            "role": "TEXT NOT NULL DEFAULT 'member'",
            "is_active": "INTEGER NOT NULL DEFAULT 1",
            "force_password_change": "INTEGER NOT NULL DEFAULT 0",
            "failed_login_count": "INTEGER NOT NULL DEFAULT 0",
            "locked_until": "TEXT",
            "last_login": "TEXT"
        }

        for column, definition in migrations.items():
            if column not in existing_columns:
                conn.execute(
                    f"ALTER TABLE users ADD COLUMN {column} {definition}"
                )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"
        )

        conn.commit()
    finally:
        conn.close()


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


def get_user_rows(table, uid):
    allowed = {
        "activities", "journal", "research",
        "voice_logs", "appointments", "concepts"
    }

    if table not in allowed:
        raise ValueError("Invalid database table.")

    return query(
        f"SELECT * FROM {table} WHERE user_id=? ORDER BY id DESC",
        (uid,)
    )


def section_title(title, description=""):
    st.title(title)
    if description:
        st.caption(description)


init_db()


# =========================================================
# PASSWORD AND LOGIN
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

        return hmac.compare_digest(digest, expected_hash)

    except (ValueError, TypeError, AttributeError):
        return False

def get_secret_value(key):
    try:
        value = st.secrets.get(key)
        if value:
            return str(value).strip()
    except Exception:
        pass

    return os.environ.get(key, "").strip()


def bootstrap_owner():
    # Never create a second owner automatically
    existing_owner = query(
        "SELECT id FROM users WHERE role='owner' LIMIT 1",
        one=True
    )

    if existing_owner:
        return

    username = get_secret_value("OWNER_USERNAME").lower()
    email = get_secret_value("OWNER_EMAIL")
    password = get_secret_value("OWNER_PASSWORD")

    # Wait until the owner credentials are configured
    if not username or not password:
        return

    if not re.fullmatch(r"[a-z0-9_.-]{3,30}", username):
        return

    if len(password) < 14:
        return

    try:
        execute(
            """
            INSERT INTO users
            (username, email, password_hash, created_at, role, is_active)
            VALUES (?, ?, ?, ?, 'owner', 1)
            """,
            (username, email, hash_password(password), now())
        )
    except sqlite3.IntegrityError:
        # Do not overwrite or promote an existing account
        return


bootstrap_owner()


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
        (actor_user_id, actor_username, action,
         target_type, target_id, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            actor_user_id,
            actor_username,
            action,
            target_type,
            str(target_id) if target_id is not None else None,
            details,
            now()
        )
    )


def login_is_locked(username):
    row = query(
        "SELECT locked_until FROM login_attempts WHERE username=?",
        (username,),
        one=True
    )

    if not row or not row["locked_until"]:
        return False

    try:
        return datetime.fromisoformat(
            row["locked_until"]
        ) > datetime.fromisoformat(now())
    except (ValueError, TypeError):
        return False


def record_login_failure(username):
    row = query(
        "SELECT failed_count, locked_until "
        "FROM login_attempts WHERE username=?",
        (username,),
        one=True
    )

    current_time = datetime.fromisoformat(now())

    if row:
        locked_until = row["locked_until"]

        # Reset attempts if an earlier lock has expired
        if locked_until:
            try:
                if datetime.fromisoformat(locked_until) <= current_time:
                    failed_count = 0
                else:
                    failed_count = row["failed_count"]
            except (ValueError, TypeError):
                failed_count = 0
        else:
            failed_count = row["failed_count"]
    else:
        failed_count = 0

    failed_count += 1

    lock_time = None

    if failed_count >= 5:
        from datetime import timedelta
        lock_time = (
            current_time + timedelta(minutes=15)
        ).isoformat(timespec="seconds")

    execute(
        """
        INSERT INTO login_attempts
        (username, failed_count, locked_until, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            failed_count=excluded.failed_count,
            locked_until=excluded.locked_until,
            updated_at=excluded.updated_at
        """,
        (username, failed_count, lock_time, now())
    )


def clear_login_failures(username):
    execute(
        "DELETE FROM login_attempts WHERE username=?",
        (username,)
    )


def authenticate_user(username, password, expected_role=None):
    username = username.strip().lower()

    if login_is_locked(username):
        return False, "Too many failed attempts. Try again later."

    row = query(
        "SELECT * FROM users WHERE username=?",
        (username,),
        one=True
    )

    if not row or not verify_password(password, row["password_hash"]):
        record_login_failure(username)
        return False, "Username or password is incorrect."

    if not row["is_active"]:
        return False, "Username or password is incorrect."

    if expected_role and row["role"] != expected_role:
        return False, "Username or password is incorrect."

    clear_login_failures(username)

    execute(
        "UPDATE users SET last_login=? WHERE id=?",
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



def get_user():
    user = st.session_state.get("user")

    if not user:
        return None

    current_time = datetime.now().timestamp()
    last_activity = st.session_state.get("last_activity")

    # Automatic logout after 30 minutes of inactivity
    if last_activity is not None:
        if current_time - last_activity > 1800:
            st.session_state.pop("user", None)
            st.session_state.pop("last_activity", None)
            st.warning("Your session expired. Please log in again.")
            return None

    # Refresh activity time
    st.session_state["last_activity"] = current_time

    # Always verify account status and role from database
    row = query(
        "SELECT id, username, email, role, is_active, "
        "force_password_change FROM users WHERE id=?",
        (user["id"],),
        one=True
    )

    if not row or not row["is_active"]:
        st.session_state.pop("user", None)
        st.session_state.pop("last_activity", None)
        st.warning("Your account is unavailable. Please log in again.")
        return None

    updated_user = {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
        "force_password_change": row["force_password_change"]
    }

    st.session_state["user"] = updated_user

    return updated_user




def auth_screen():
    st.title("🧠 NeuroLens")
    st.caption("Explore cognition, behavior & the brain")

    st.write(
        f"{OWNER} · Independent cognitive neuroscience researcher"
    )

    owner_tab, staff_tab, member_tab, signup_tab = st.tabs(
        ["Owner Login", "Staff Login", "Member Login", "Create Account"]
    )

    def login_form(tab_name, expected_role):
        with st.form(f"{tab_name}_login_form"):
            username = st.text_input(
                "Username",
                key=f"{tab_name}_username"
            ).strip().lower()

            password = st.text_input(
                "Password",
                type="password",
                key=f"{tab_name}_password"
            )

            submit = st.form_submit_button(
                "Log in",
                use_container_width=True
            )

        if submit:
            success, result = authenticate_user(
                username,
                password,
                expected_role
            )

            if success:
                st.session_state["user"] = {
                    "id": result["id"],
                    "username": result["username"],
                    "email": result["email"],
                    "role": result["role"],
                    "force_password_change": result["force_password_change"]
                }

                st.session_state["last_activity"] = (
                    datetime.now().timestamp()
                )

                st.rerun()
            else:
                st.error(result)

    with owner_tab:
        st.caption("Authorized Super Admin access.")
        login_form("owner", "owner")

    with staff_tab:
        st.caption("Authorized NeuroLens team access.")
        login_form("staff", "staff")

    with member_tab:
        st.caption("Sign in to your NeuroLens account.")
        login_form("member", "member")

    with signup_tab:
        with st.form("signup_form"):
            username = st.text_input(
                "Choose username",
                key="signup_username"
            ).strip().lower()

            email = st.text_input(
                "Email (optional)",
                key="signup_email"
            ).strip()

            password = st.text_input(
                "Create password",
                type="password",
                key="signup_password"
            )

            confirm = st.text_input(
                "Confirm password",
                type="password",
                key="signup_confirm"
            )

            submit = st.form_submit_button(
                "Create account",
                use_container_width=True
            )

        if submit:
            if not re.fullmatch(r"[a-z0-9_.-]{3,30}", username):
                st.error("Username must contain 3–30 valid characters.")

            elif len(password) < 10:
                st.error("Use a password with at least 10 characters.")

            elif password != confirm:
                st.error("Passwords do not match.")

            else:
                try:
                    execute(
                        """
                        INSERT INTO users
                        (username, email, password_hash, created_at, role)
                        VALUES (?, ?, ?, ?, 'member')
                        """,
                        (
                            username,
                            email,
                            hash_password(password),
                            now()
                        )
                    )

                    st.success(
                        "Member account created. Please log in."
                    )

                except sqlite3.IntegrityError:
                    st.error("That username is already taken.")


# =========================================================
# GEMINI AI
# =========================================================

def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY", "").strip()


def ai_client():
    key = get_api_key()

    if not key:
        return None

    if genai is None:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


def ai_error_message(exc):
    error = str(exc)
    upper = error.upper()

    if "404" in error or "NOT_FOUND" in upper:
        return (
            "Gemini model was not found. Check that the model is "
            "gemini-3.8-flash and that your API key has access."
        )

    if "429" in error or "RESOURCE_EXHAUSTED" in upper:
        return (
            "Gemini request limit reached. Please wait a little "
            "and try again."
        )

    if "403" in error or "PERMISSION_DENIED" in upper:
        return (
            "Gemini permission denied. Please check your API key "
            "and Google AI Studio access."
        )

    if "401" in error or "UNAUTHENTICATED" in upper:
        return (
            "Gemini API key was rejected. Check GEMINI_API_KEY "
            "in Streamlit Secrets."
        )

    return f"AI request failed: {error}"


def ask_gemini(prompt, system_instruction=None):
    client = ai_client()

    if client is None:
        if not get_api_key():
            return (
                "Ayna AI is not configured. Add GEMINI_API_KEY "
                "to Streamlit Secrets."
            )

        return (
            "The Gemini client could not start. Check that "
            "google-genai is installed in requirements.txt."
        )

    instruction = system_instruction or (
        "You are Ayna, a careful cognitive neuroscience learning "
        "assistant inside NeuroLens. Explain scientific concepts "
        "clearly. Distinguish established evidence from hypotheses. "
        "Do not diagnose medical or mental-health conditions. "
        "Do not claim that simple app tasks measure brain activity."
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=(
                instruction
                + "\n\nUser request:\n"
                + str(prompt)
            )
        )

        answer = getattr(response, "text", None)

        if answer and answer.strip():
            return answer.strip()

        return "Ayna did not receive a text response. Please try again."

    except Exception as exc:
        return ai_error_message(exc)


# =========================================================
# SUPABASE CONNECTION TEST
# =========================================================

@st.cache_resource
def get_supabase_client():
    if create_client is None:
        raise RuntimeError(
            "Supabase package is not installed."
        )

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]

    except Exception as exc:
        raise RuntimeError(
            "Add SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets."
        ) from exc

    if not str(url).strip() or not str(key).strip():
        raise RuntimeError("Supabase URL or key is empty.")

    return create_client(
        str(url).strip(),
        str(key).strip()
    )


def test_supabase_connection():
    try:
        client = get_supabase_client()

        client.table("profiles").select("id").limit(1).execute()

        return True, "Supabase read connection successful."

    except Exception as exc:
        return False, str(exc)


# =========================================================
# SAVE ACTIVITY
# =========================================================

def save_activity(user_id, name, score=None, details=""):
    try:
        execute(
            """
            INSERT INTO activities
            (user_id,activity,score,details,created_at)
            VALUES(?,?,?,?,?)
            """,
            (
                user_id,
                str(name)[:200],
                score,
                str(details)[:2000],
                now()
            )
        )

        st.success("Activity saved to your NeuroLens account.")

        st.caption(
            "Activity saved in the app's SQLite database. "
            "Secure cloud sync is not enabled yet."
        )

        return True

    except Exception as exc:
        st.error(f"Activity could not be saved: {exc}")
        return False


# =========================================================
# BRAIN EXPLORER
# =========================================================

def brain_explorer():
    section_title(
        "🧠 Brain Explorer",
        "Learn about brain regions and systems involved in cognition."
    )

    regions = {
        "Prefrontal cortex": (
            "Planning, working memory, goal-directed behavior "
            "and cognitive control.",
            "Executive control is distributed across interacting networks."
        ),

        "Hippocampus": (
            "Important for forming many kinds of episodic "
            "and relational memories.",
            "Memory also depends on distributed cortical and subcortical systems."
        ),

        "Striatum": (
            "Part of the basal ganglia; involved in action selection, "
            "learning and reward.",
            "Its functions depend on circuit, cell type, task and context."
        ),

        "Anterior cingulate cortex (ACC)": (
            "Involved in monitoring, effort, conflict and adaptive control.",
            "No single region performs one isolated mental function."
        ),

        "Attention networks": (
            "Distributed systems support alerting, orienting "
            "and executive attention.",
            "Attention is dynamic and depends on task and environment."
        ),

        "Reward systems": (
            "Dopamine and connected circuits contribute to learning "
            "and motivation.",
            "Dopamine is not simply a pleasure chemical."
        ),

        "Consciousness": (
            "Research examines wakefulness, awareness "
            "and their neural correlates.",
            "The neural basis of subjective experience remains "
            "an active research question."
        )
    }

    selected = st.selectbox(
        "Choose a topic",
        list(regions.keys())
    )

    st.subheader(selected)
    st.write(regions[selected][0])

    st.info("Research note: " + regions[selected][1])

    question = st.text_input(
        "What would you like to learn?",
        placeholder="e.g. How does working memory involve the PFC?"
    )

    if st.button("Ask Ayna about this brain topic"):
        if question.strip():
            with st.spinner("Ayna is thinking..."):
                answer = ask_gemini(
                    f"Explain '{selected}'. Answer this question: {question}",
                    "You are Ayna, a neuroscience educator. "
                    "Be scientifically accurate and distinguish "
                    "evidence from hypotheses."
                )

            st.markdown(answer)

        else:
            st.warning("Please enter a question.")


# =========================================================
# CSTC CIRCUIT LEARNING
# =========================================================

def cstc_learning():
    section_title(
        "🔁 CSTC Circuit Learning",
        "Cortico-striato-thalamo-cortical loops: a simplified learning model."
    )

    st.markdown("""
    **Direct pathway**

    Cortex → Striatum (D1-enriched) → GPi/SNr inhibition
    → reduced inhibition of thalamus → thalamocortical activity

    **Indirect pathway**

    Cortex → Striatum (D2-enriched) → GPe inhibition
    → STN activity → GPi/SNr output → thalamic inhibition

    **Hyperdirect pathway**

    Cortex → STN → GPi/SNr output

    Dopamine from SNc modulates striatal circuits. This is a simplified
    model of a complex, parallel and interconnected system.
    """)

    pathway = st.radio(
        "Choose a pathway",
        ["Direct", "Indirect", "Hyperdirect"],
        horizontal=True
    )

    descriptions = {
        "Direct": (
            "Often described as facilitating selected actions "
            "through a net reduction in thalamic inhibition."
        ),

        "Indirect": (
            "Often described as helping regulate competing actions "
            "through additional basal-ganglia relays."
        ),

        "Hyperdirect": (
            "Provides a relatively fast cortical route to the STN "
            "and basal-ganglia output nuclei."
        )
    }

    st.info(descriptions[pathway])

    question = st.text_input(
        "Ask a CSTC question",
        key="cstc_question"
    )

    if st.button("Explain this pathway"):
        if question.strip():
            with st.spinner("Ayna is preparing an explanation..."):
                answer = ask_gemini(
                    f"Explain the {pathway} CSTC pathway. "
                    f"Question: {question}",
                    "Explain circuit neuroscience carefully. "
                    "Mention limitations of simplified pathway models."
                )

            st.markdown(answer)

        else:
            st.warning("Please enter a question.")


# =========================================================
# NEUROSCIENCE LAB
# =========================================================

def neuroscience_lab(uid):
    section_title(
        "🧪 Interactive Neuroscience Lab",
        "Educational cognitive tasks, not diagnostic tests."
    )

    game = st.selectbox(
        "Select an activity",
        [
            "Memory Sequence",
            "Attention: Find X",
            "Stroop Control",
            "Decision & Reward",
            "Pattern Reasoning"
        ]
    )

    if game != st.session_state.get("last_lab_game"):
        for key in (
            "memory_target",
            "memory_visible",
            "attention_letters",
            "attention_target",
            "stroop_item"
        ):
            st.session_state.pop(key, None)

        st.session_state.last_lab_game = game

    # MEMORY
    if game == "Memory Sequence":
        if "memory_target" not in st.session_state:
            st.session_state.memory_target = "".join(
                random.choices("123456789", k=6)
            )
            st.session_state.memory_visible = False

        if st.button("Show memory code"):
            st.session_state.memory_visible = True

        if st.session_state.memory_visible:
            st.code(st.session_state.memory_target)

        if st.button("Hide code"):
            st.session_state.memory_visible = False

        answer = st.text_input(
            "Enter the code from memory",
            max_chars=6
        )

        if st.button("Check memory answer"):
            target = st.session_state.memory_target

            score = sum(
                a == b
                for a, b in zip(answer.strip(), target)
            )

            pct = round(100 * score / len(target))

            st.write(
                f"Position matches: {score}/{len(target)} ({pct}%)"
            )

            save_activity(
                uid,
                game,
                pct,
                f"Position matches: {score}/{len(target)}"
            )

            st.session_state.pop("memory_target", None)
            st.session_state.pop("memory_visible", None)

            st.rerun()

    # ATTENTION
    elif game == "Attention: Find X":
        if "attention_letters" not in st.session_state:
            letters = random.choices(
                ["O", "Q", "C", "D"],
                k=35
            )

            target_index = random.randrange(35)
            letters[target_index] = "X"

            st.session_state.attention_letters = letters
            st.session_state.attention_target = target_index

        letters = st.session_state.attention_letters
        target_index = st.session_state.attention_target

        st.write("Find the X. Each letter has a position number.")

        for start in range(0, 35, 7):
            row = letters[start:start + 7]

            cols = st.columns(7)

            for j, letter in enumerate(row):
                position = start + j + 1

                with cols[j]:
                    st.markdown(
                        f"**{position}**",
                        help=f"Position {position}"
                    )
                    st.markdown(f"### {letter}")

        choice = st.number_input(
            "Position of X (1–35)",
            min_value=1,
            max_value=35,
            value=1,
            step=1
        )

        if st.button("Check attention"):
            correct = int(choice) == target_index + 1

            if correct:
                st.success("Correct! You found X.")
            else:
                st.info(
                    f"The X was at position {target_index + 1}."
                )

            save_activity(
                uid,
                game,
                100 if correct else 0,
                f"Selected={int(choice)}; Correct={correct}"
            )

            st.session_state.pop("attention_letters", None)
            st.session_state.pop("attention_target", None)

            st.rerun()

        if st.button("New attention puzzle"):
            st.session_state.pop("attention_letters", None)
            st.session_state.pop("attention_target", None)
            st.rerun()

    # STROOP
    elif game == "Stroop Control":
        words = [
            ("RED", "blue"),
            ("BLUE", "red"),
            ("GREEN", "green"),
            ("YELLOW", "red"),
            ("PURPLE", "blue")
        ]

        if "stroop_item" not in st.session_state:
            st.session_state.stroop_item = random.choice(words)

        word, ink = st.session_state.stroop_item

        st.markdown(
            f"<h2 style='text-align:center;color:{ink}'>{word}</h2>",
            unsafe_allow_html=True
        )

        st.caption(
            "Choose the INK COLOUR, not the written word."
        )

        choice = st.radio(
            "Ink colour",
            ["red", "blue", "green", "yellow", "purple"],
            horizontal=True
        )

        if st.button("Check Stroop answer"):
            correct = choice == ink

            if correct:
                st.success("Correct!")
            else:
                st.info(f"The ink colour was {ink}.")

            save_activity(
                uid,
                game,
                100 if correct else 0,
                f"Selected={choice}; Target={ink}"
            )

            st.session_state.stroop_item = random.choice(words)
            st.rerun()

    # DECISION
    elif game == "Decision & Reward":
        st.write(
            "Choose a smaller immediate reward or a larger delayed reward."
        )

        choice = st.radio(
            "Which would you choose?",
            [
                "Rs 1,000 today",
                "Rs 1,500 after 30 days"
            ]
        )

        reason = st.text_area(
            "Why did you choose it? (optional)"
        )

        if st.button("Save decision reflection"):
            save_activity(
                uid,
                game,
                None,
                f"Choice={choice}; Reflection={reason}"
            )

    # PATTERN
    elif game == "Pattern Reasoning":
        st.write("Complete the pattern: 2 → 4 → 8 → 16 → ?")

        answer = st.number_input(
            "Next number",
            min_value=0,
            value=0,
            step=1
        )

        if st.button("Check pattern"):
            correct = answer == 32

            if correct:
                st.success("Correct! The next number is 32.")
            else:
                st.info("Try doubling the previous number.")

            save_activity(
                uid,
                game,
                100 if correct else 0,
                f"Answer={answer}"
            )


# =========================================================
# BRAIN PUZZLE
# =========================================================

def brain_puzzle(uid):
    section_title(
        "🧩 Brain Puzzle",
        "Sliding-number puzzle for planning and problem-solving."
    )

    size = st.radio(
        "Grid size",
        [3, 4],
        horizontal=True
    )

    key = f"puzzle_{size}"

    if key not in st.session_state:
        board = list(range(1, size * size)) + [0]

        for _ in range(120):
            blank = board.index(0)
            moves = []

            if blank % size > 0:
                moves.append(blank - 1)

            if blank % size < size - 1:
                moves.append(blank + 1)

            if blank >= size:
                moves.append(blank - size)

            if blank < size * (size - 1):
                moves.append(blank + size)

            other = random.choice(moves)

            board[blank], board[other] = (
                board[other],
                board[blank]
            )

        st.session_state[key] = board
        st.session_state[f"{key}_moves"] = 0

    board = st.session_state[key]

    cols = st.columns(size)

    for i, value in enumerate(board):
        with cols[i % size]:
            label = "⬜" if value == 0 else str(value)

            if st.button(
                label,
                key=f"{key}_tile_{i}",
                use_container_width=True
            ):
                blank = board.index(0)

                distance = (
                    abs(blank // size - i // size)
                    + abs(blank % size - i % size)
                )

                if distance == 1:
                    board[blank], board[i] = (
                        board[i],
                        board[blank]
                    )

                    st.session_state[f"{key}_moves"] += 1
                    st.rerun()

    st.caption(
        f"Moves: {st.session_state[f'{key}_moves']}"
    )

    if board == list(range(1, size * size)) + [0]:
        st.success("Puzzle solved!")

        if st.button("Save puzzle result"):
            save_activity(
                uid,
                f"Brain Puzzle {size}x{size}",
                100,
                f"Moves={st.session_state[f'{key}_moves']}"
            )

    if st.button("Shuffle puzzle"):
        st.session_state.pop(key, None)
        st.session_state.pop(f"{key}_moves", None)
        st.rerun()


# =========================================================
# ASK AYNA AI
# =========================================================

def ask_ayna():
    section_title(
        "🤖 Ask Ayna AI",
        "Your AI learning companion for cognition, behavior and neuroscience."
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input(
        "Ask Ayna a neuroscience or research question..."
    )

    if prompt:
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        history = "\n\n".join(
            f"{x['role']}: {x['content']}"
            for x in st.session_state.chat_history[-12:]
        )

        with st.chat_message("assistant"):
            with st.spinner("Ayna is thinking..."):
                answer = ask_gemini(
                    history,
                    """
                    You are Ayna, the AI learning companion inside NeuroLens.

                    Your areas include:
                    - Cognitive neuroscience
                    - Brain and behavior
                    - Consciousness and awareness
                    - Learning and memory
                    - Attention and decision-making
                    - Reward and motivation
                    - CSTC circuits
                    - Research methodology

                    Give clear, structured and scientifically careful answers.
                    Explain uncertainty and distinguish evidence from hypotheses.
                    Do not diagnose medical or mental-health conditions.
                    Do not invent research citations or claim certainty without evidence.
                    """
                )

                st.markdown(answer)

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

    if st.button("Clear Ayna chat"):
        st.session_state.chat_history = []
        st.rerun()


# =========================================================
# VOICE STUDIO
# =========================================================

def voice_studio(uid):
    section_title(
        "🎙️ Voice Studio",
        "Record or upload audio for AI-assisted transcription and reflection."
    )

    st.warning(
        "Audio analysis can be wrong. Any emotion descriptions are tentative, "
        "not a mental-health assessment. Do not upload another person's "
        "private audio without permission."
    )

    audio = None
    mime = "audio/wav"

    if hasattr(st, "audio_input"):
        try:
            audio = st.audio_input("Record your voice")
        except Exception:
            audio = None

    uploaded = st.file_uploader(
        "Or upload audio",
        type=["wav", "mp3", "m4a", "ogg", "webm"],
        key="voice_upload"
    )

    if uploaded is not None:
        audio = uploaded
        mime = uploaded.type or "audio/wav"

    if audio is not None:
        audio_bytes = audio.getvalue()

        st.audio(audio_bytes, format=mime)

        if st.button("Transcribe and analyse audio"):
            client = ai_client()

            if client is None:
                st.error(
                    "Gemini is not configured. Check GEMINI_API_KEY."
                )

            elif types is None:
                st.error(
                    "Google GenAI audio components are unavailable. "
                    "Update google-genai in requirements.txt."
                )

            else:
                try:
                    with st.spinner("Processing audio..."):
                        response = client.models.generate_content(
                            model=MODEL,
                            contents=[
                                types.Part.from_bytes(
                                    data=audio_bytes,
                                    mime_type=mime
                                ),
                                (
                                    "Provide a best-effort transcription "
                                    "and neutral summary of this audio. "
                                    "Clearly label uncertainty. Do not "
                                    "diagnose or infer identity."
                                )
                            ]
                        )

                    result = getattr(response, "text", None)

                    if not result:
                        result = "No text result was returned."

                    st.session_state.voice_result = result

                except Exception as exc:
                    st.error(ai_error_message(exc))

    if st.session_state.get("voice_result"):
        st.subheader("AI audio result")

        transcript = st.text_area(
            "Edit/copy the transcript",
            value=st.session_state.voice_result,
            key="voice_transcript_edit"
        )

        own_mood = st.selectbox(
            "How do YOU feel? (optional)",
            [
                "Prefer not to say",
                "Calm",
                "Happy",
                "Sad",
                "Stressed",
                "Tired",
                "Focused",
                "Unsure"
            ]
        )

        if st.button("Save voice reflection"):
            execute(
                """
                INSERT INTO voice_logs
                (user_id,transcript,reflection,emoji,created_at)
                VALUES(?,?,?,?,?)
                """,
                (
                    uid,
                    transcript,
                    f"Self-reported mood: {own_mood}",
                    "AI suggestions included in result",
                    now()
                )
            )

            st.success("Voice reflection saved.")

            st.session_state.pop("voice_result", None)
            st.session_state.pop("voice_transcript_edit", None)

            st.rerun()

    st.subheader("Saved voice reflections")

    for log in get_user_rows("voice_logs", uid)[:10]:
        with st.expander(log["created_at"]):
            st.write(log["transcript"])
            st.caption(log["reflection"])


# =========================================================
# PRIVATE JOURNAL
# =========================================================

def private_journal(uid):
    section_title(
        "🌿 Private Journal",
        "Personal reflections saved to your account."
    )

    with st.form("journal_form", clear_on_submit=True):
        title = st.text_input(
            "Entry title",
            max_chars=150
        )

        body = st.text_area(
            "Your reflection",
            height=180
        )

        mood = st.selectbox(
            "Optional self-reported mood",
            [
                "Not specified",
                "Calm",
                "Happy",
                "Sad",
                "Stressed",
                "Motivated",
                "Tired",
                "Reflective"
            ]
        )

        submit = st.form_submit_button("Save private entry")

    if submit:
        if title.strip() and body.strip():
            execute(
                """
                INSERT INTO journal
                (user_id,title,body,mood,created_at)
                VALUES(?,?,?,?,?)
                """,
                (
                    uid,
                    title.strip(),
                    body.strip(),
                    mood,
                    now()
                )
            )

            st.success("Journal entry saved.")
            st.rerun()

        else:
            st.error("Add a title and reflection.")

    for entry in get_user_rows("journal", uid):
        with st.expander(
            f"{entry['title']} · {entry['created_at']}"
        ):
            st.caption(
                "Self-reported mood: " + str(entry["mood"])
            )

            st.write(entry["body"])

            if st.button(
                "Delete entry",
                key=f"del_journal_{entry['id']}"
            ):
                execute(
                    "DELETE FROM journal WHERE id=? AND user_id=?",
                    (entry["id"], uid)
                )
                st.rerun()


# =========================================================
# APPOINTMENTS
# =========================================================

def appointments(uid):
    section_title(
        "📅 Appointment Requests",
        "Submit a request; this does not automatically confirm a booking."
    )

    with st.form("appointment_form"):
        topic = st.selectbox(
            "Request type",
            [
                "Neuroscience consultation",
                "Research discussion",
                "Project feedback",
                "Other"
            ]
        )

        date = st.date_input("Preferred date")

        tm = st.selectbox(
            "Preferred time",
            [
                "Morning",
                "Afternoon",
                "Evening",
                "Flexible"
            ]
        )

        message = st.text_area(
            "What would you like to discuss?"
        )

        submit = st.form_submit_button("Submit request")

    if submit:
        execute(
            """
            INSERT INTO appointments
            (user_id,topic,preferred_date,preferred_time,message,status,created_at)
            VALUES(?,?,?,?,?,'Pending',?)
            """,
            (
                uid,
                topic,
                str(date),
                tm,
                message.strip(),
                now()
            )
        )

        st.success(
            "Request saved as Pending. No appointment is confirmed."
        )
        st.rerun()

    st.subheader("Your requests")

    for item in get_user_rows("appointments", uid):
        st.write(
            f"**{item['topic']}** — "
            f"{item['preferred_date']} · {item['preferred_time']}"
        )

        st.caption(
            f"Status: {item['status']} · Submitted {item['created_at']}"
        )


# =========================================================
# NEUROSOCIAL
# =========================================================

def neurosocial(uid, username):
    section_title(
        "🌐 NeuroSocial",
        "Share neuroscience learning notes and discuss ideas respectfully."
    )

    with st.form("post_form", clear_on_submit=True):
        body = st.text_area(
            "Write a post",
            max_chars=3000
        )

        submit = st.form_submit_button("Publish post")

    if submit:
        if body.strip():
            execute(
                """
                INSERT INTO posts(user_id,body,created_at)
                VALUES(?,?,?)
                """,
                (uid, body.strip(), now())
            )

            st.rerun()

        else:
            st.warning("Write something before publishing.")

    posts = query("""
        SELECT posts.*, users.username,
        (SELECT COUNT(*) FROM comments
         WHERE comments.post_id=posts.id) AS comment_count
        FROM posts
        JOIN users ON posts.user_id=users.id
        ORDER BY posts.id DESC
        LIMIT 100
    """)

    for post in posts:
        with st.container(border=True):
            st.caption(
                f"@{post['username']} · {post['created_at']}"
            )

            st.write(post["body"])

            reactions = query(
                """
                SELECT reaction,COUNT(*) AS n
                FROM reactions
                WHERE post_id=?
                GROUP BY reaction
                """,
                (post["id"],)
            )

            st.caption(
                " · ".join(
                    f"{r['reaction']} {r['n']}"
                    for r in reactions
                ) or "No reactions yet"
            )

            reaction = st.selectbox(
                "React",
                ["🧠", "👍", "❤️", "💡"],
                key=f"react_{post['id']}"
            )

            if st.button(
                "Save reaction",
                key=f"save_react_{post['id']}"
            ):
                execute(
                    """
                    INSERT INTO reactions(post_id,user_id,reaction)
                    VALUES(?,?,?)
                    ON CONFLICT(post_id,user_id)
                    DO UPDATE SET reaction=excluded.reaction
                    """,
                    (post["id"], uid, reaction)
                )

                st.rerun()

            with st.expander(
                f"Comments ({post['comment_count']})"
            ):
                comments = query(
                    """
                    SELECT comments.*, users.username
                    FROM comments
                    JOIN users ON comments.user_id=users.id
                    WHERE post_id=?
                    ORDER BY comments.id ASC
                    """,
                    (post["id"],)
                )

                for comment_row in comments:
                    st.write(
                        f"**@{comment_row['username']}**: "
                        f"{comment_row['body']}"
                    )

                comment = st.text_input(
                    "Add comment",
                    key=f"comment_{post['id']}"
                )

                if st.button(
                    "Post comment",
                    key=f"send_comment_{post['id']}"
                ):
                    if comment.strip():
                        execute(
                            """
                            INSERT INTO comments
                            (post_id,user_id,body,created_at)
                            VALUES(?,?,?,?)
                            """,
                            (
                                post["id"],
                                uid,
                                comment.strip()[:1000],
                                now()
                            )
                        )

                        st.rerun()

            if post["user_id"] == uid:
                if st.button(
                    "Delete your post",
                    key=f"delete_post_{post['id']}"
                ):
                    execute(
                        "DELETE FROM comments WHERE post_id=?",
                        (post["id"],)
                    )

                    execute(
                        "DELETE FROM reactions WHERE post_id=?",
                        (post["id"],)
                    )

                    execute(
                        "DELETE FROM posts WHERE id=? AND user_id=?",
                        (post["id"], uid)
                    )

                    st.rerun()


# =========================================================
# RESEARCH BOOK
# =========================================================

def research_book(uid):
    section_title(
        "📚 Research Book",
        "Organize literature notes, ideas, and research questions."
    )

    with st.form("research_form", clear_on_submit=True):
        title = st.text_input("Entry title")
        topic = st.text_input("Topic / research question")
        notes = st.text_area("Notes", height=150)
        tags = st.text_input("Tags (comma-separated)")

        submit = st.form_submit_button("Save research entry")

    if submit:
        if title.strip():
            execute(
                """
                INSERT INTO research
                (user_id,title,topic,notes,tags,created_at)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    uid,
                    title.strip(),
                    topic.strip(),
                    notes.strip(),
                    tags.strip(),
                    now()
                )
            )

            st.success("Research entry saved.")
            st.rerun()

        else:
            st.error("Add an entry title.")

    for item in get_user_rows("research", uid):
        with st.expander(item["title"]):
            st.caption(item["topic"] or "")
            st.write(item["notes"] or "")
            st.caption("Tags: " + (item["tags"] or "None"))

            if st.button(
                "Delete research entry",
                key=f"del_research_{item['id']}"
            ):
                execute(
                    "DELETE FROM research WHERE id=? AND user_id=?",
                    (item["id"], uid)
                )

                st.rerun()


# =========================================================
# CONCEPT MAP
# =========================================================

def concept_map(uid):
    section_title(
        "🕸️ Concept Map",
        "Create a simple map of connections between research concepts."
    )

    with st.form("concept_form", clear_on_submit=True):
        concept = st.text_input("Concept")
        connects = st.text_input("Connects to")
        explanation = st.text_area(
            "Why are these concepts connected?"
        )

        submit = st.form_submit_button("Add concept")

    if submit:
        if concept.strip():
            execute(
                """
                INSERT INTO concepts
                (user_id,concept,connects_to,explanation,created_at)
                VALUES(?,?,?,?,?)
                """,
                (
                    uid,
                    concept.strip(),
                    connects.strip(),
                    explanation.strip(),
                    now()
                )
            )

            st.success("Concept saved.")
            st.rerun()

        else:
            st.warning("Enter a concept name.")

    rows = get_user_rows("concepts", uid)

    if rows:
        df = pd.DataFrame(
            [dict(row) for row in rows]
        )

        st.dataframe(
            df[
                [
                    "concept",
                    "connects_to",
                    "explanation",
                    "created_at"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        try:
            import graphviz

            graph = graphviz.Digraph()

            for row in rows:
                graph.node(row["concept"])

                if (row["connects_to"] or "").strip():
                    graph.edge(
                        row["concept"],
                        row["connects_to"]
                    )

            st.graphviz_chart(graph)

        except Exception:
            st.caption(
                "Graphviz visual is unavailable; "
                "your concepts are still saved."
            )

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Export concept map as CSV",
            csv_data,
            "neurolens_concepts.csv",
            "text/csv"
        )


# =========================================================
# PHOTO STUDIO
# =========================================================

def photo_studio():
    section_title(
        "📸 Photo Studio",
        "Apply simple image filters in your browser session."
    )

    uploaded = st.file_uploader(
        "Upload a photo",
        type=["png", "jpg", "jpeg", "webp"]
    )

    if uploaded:
        try:
            original = Image.open(uploaded).convert("RGB")

            brightness = st.slider(
                "Brightness",
                0.3, 2.0, 1.0, 0.1
            )

            contrast = st.slider(
                "Contrast",
                0.3, 2.0, 1.0, 0.1
            )

            saturation = st.slider(
                "Saturation",
                0.0, 2.0, 1.0, 0.1
            )

            effect = st.selectbox(
                "Filter",
                [
                    "Original",
                    "Grayscale",
                    "Blur",
                    "Sharpen",
                    "Contour"
                ]
            )

            edited = ImageEnhance.Brightness(
                original
            ).enhance(brightness)

            edited = ImageEnhance.Contrast(
                edited
            ).enhance(contrast)

            edited = ImageEnhance.Color(
                edited
            ).enhance(saturation)

            if effect == "Grayscale":
                edited = edited.convert("L").convert("RGB")

            elif effect == "Blur":
                edited = edited.filter(ImageFilter.BLUR)

            elif effect == "Sharpen":
                edited = edited.filter(ImageFilter.SHARPEN)

            elif effect == "Contour":
                edited = edited.filter(ImageFilter.CONTOUR)

            left, right = st.columns(2)

            left.image(
                original,
                caption="Original",
                use_container_width=True
            )

            right.image(
                edited,
                caption="Edited",
                use_container_width=True
            )

            output = io.BytesIO()
            edited.save(output, format="PNG")

            st.download_button(
                "Download edited image",
                output.getvalue(),
                "neurolens_edited.png",
                "image/png"
            )

        except Exception as exc:
            st.error(f"Could not process this image: {exc}")


# =========================================================
# PROGRESS DASHBOARD
# =========================================================

def dashboard(uid):
    section_title(
        "📈 Progress Dashboard",
        "Your saved task history and activity trends."
    )

    activities = get_user_rows("activities", uid)
    journal = get_user_rows("journal", uid)
    research = get_user_rows("research", uid)
    voices = get_user_rows("voice_logs", uid)
    appointment_rows = get_user_rows("appointments", uid)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Activities", len(activities))
    c2.metric("Journal entries", len(journal))
    c3.metric("Research notes", len(research))
    c4.metric("Voice logs", len(voices))

    if activities:
        df = pd.DataFrame(
            [dict(row) for row in activities]
        )

        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce"
        )

        scored = df.dropna(subset=["score"])

        if not scored.empty:
            st.subheader("Recorded task scores")

            st.line_chart(
                scored.set_index("created_at")["score"]
            )

        st.subheader("Recent activity")

        st.dataframe(
            df[
                [
                    "activity",
                    "score",
                    "details",
                    "created_at"
                ]
            ].head(50),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Export activity history",
            df.to_csv(index=False).encode("utf-8"),
            "neurolens_activity.csv",
            "text/csv"
        )

    else:
        st.info(
            "Complete a lab activity to build your progress history."
        )

    if appointment_rows:
        st.write(
            f"Appointment requests: {len(appointment_rows)}"
        )


# =========================================================
# SETTINGS AND PRIVACY
# =========================================================

def settings_page(uid):
    section_title("⚙️ Settings & Privacy")

    user = get_user() or {}

    st.write(
        "**Signed in as:**",
        user.get("username", "Unknown")
    )

    st.write("**App creator:**", OWNER)
    st.write("**Local database:**", DB_PATH)
    st.write("**AI model:**", MODEL)

    st.subheader("AI connection")

    if st.button("Test Ayna AI connection"):
        with st.spinner("Testing Gemini connection..."):
            answer = ask_gemini(
                "Reply with: NeuroLens AI connection successful.",
                "You are Ayna. Give a short connection test response."
            )

        if answer.startswith("AI request failed:") or (
            "not configured" in answer.lower()
        ) or ("could not start" in answer.lower()):
            st.error(answer)
        else:
            st.success("Gemini responded successfully.")
            st.write(answer)

    st.divider()

    st.subheader("Supabase connection")

    st.caption(
        "This checks database read access only. The current login "
        "uses SQLite, not Supabase Auth. Private cloud sync is not "
        "enabled until authentication and ownership policies are "
        "configured securely."
    )

    if st.button("Test Supabase Connection"):
        with st.spinner("Checking Supabase access..."):
            success, message = test_supabase_connection()

        if success:
            st.success(message)
        else:
            st.error(message)

    st.divider()

    st.subheader("Account data")

    entries = [
        dict(row)
        for row in get_user_rows("journal", uid)
    ]

    st.download_button(
        "Download journal JSON",
        json.dumps(
            entries,
            ensure_ascii=False,
            indent=2
        ),
        "neurolens_journal.json",
        "application/json"
    )

    st.divider()

    if st.button("Log out"):
        st.session_state.pop("user", None)
        st.session_state.pop("chat_history", None)
        st.rerun()
def change_password_page(user):
    st.title("🔐 Change Password")

    with st.form("change_password_form"):
        current_password = st.text_input(
            "Current password",
            type="password"
        )

        new_password = st.text_input(
            "New password (minimum 10 characters)",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm new password",
            type="password"
        )

        submit = st.form_submit_button("Update Password")

    if submit:
        row = query(
            "SELECT password_hash FROM users WHERE id=?",
            (user["id"],),
            one=True
        )

        if not row or not verify_password(
            current_password, row["password_hash"]
        ):
            st.error("Current password is incorrect.")

        elif len(new_password) < 10:
            st.error("Password must be at least 10 characters.")

        elif new_password != confirm_password:
            st.error("New passwords do not match.")

        else:
            execute(
                """
                UPDATE users
                SET password_hash=?, force_password_change=0
                WHERE id=?
                """,
                (hash_password(new_password), user["id"])
            )

            st.session_state["user"]["force_password_change"] = 0
            st.success("Password updated successfully.")
            st.rerun()
def require_owner(user):
    if not user or user.get("role") != "owner":
        st.error("Access denied. Owner permission required.")
        st.stop()
# =========================================================
# MAIN ROUTER
# =========================================================

def main():
    if not get_user():
        auth_screen()
        return

    user = get_user()
    uid = user["id"]
    if user.get("force_password_change"):
        st.warning("Please change your password before continuing.")
        change_password_page(user)
        return
    st.sidebar.title("🧠 NEUROLENS")

    st.sidebar.caption(
        "Explore cognition, behavior & the brain"
    )

    st.sidebar.write(
        f"Welcome, @{user['username']}"
    )

    pages = [
        "
    role = user.get("role", "member")

    pages = [
        "
    role = user.get("role", "member")

    pages = [
        "Home",
        "Brain Explorer",
        "CSTC Circuit Learning",
        "Neuroscience Lab",
        "Brain Puzzle",
        "Ask Ayna AI",
        "Voice Studio",
        "Private Journal",
        "Appointments",
        "NeuroSocial",
        "Research Book",
        "Concept Map",
        "Photo Studio",
        "Progress Dashboard",
        "Settings"
    ]

    if role == "owner":
        pages.extend([
            "Owner Control Center",
            "Staff Management",
            "Audit Logs"
        ])

    ]

    if role == "owner":
        pages.extend([
            "Owner Control Center",
            "Staff Management",
            "Audit Logs"
        ])

    ]

    page = st.sidebar.radio(
        "Navigate",
        pages
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "Educational tool — not a diagnostic instrument."
    )

    if page == "Home":
        st.title("🧠 NeuroLens")

        st.subheader(
            "Explore cognition, behavior & the brain"
        )

        st.write(
            "An interactive learning workspace created by "
            "Ayna Jaffri for exploring neuroscience, cognition, "
            "behavior and research."
        )

        a, b, c = st.columns(3)

        a.metric("Learning areas", "Brain + CSTC")
        b.metric("Cognitive tasks", "5")
        c.metric("AI assistant", "Ask Ayna")

        st.markdown("""
        - Learn about brain regions and CSTC pathways.
        - Practice memory, attention, Stroop and decision tasks.
        - Save research ideas and private reflections.
        - Use Gemini-powered AI and supported audio tools.
        """)

        st.caption(
            "Task results describe task performance, not brain activity."
        )

    elif page == "Brain Explorer":
        brain_explorer()

    elif page == "CSTC Circuit Learning":
        cstc_learning()

    elif page == "Neuroscience Lab":
        neuroscience_lab(uid)

    elif page == "Brain Puzzle":
        brain_puzzle(uid)

    elif page == "Ask Ayna AI":
        ask_ayna()

    elif page == "Voice Studio":
        voice_studio(uid)

    elif page == "Private Journal":
        private_journal(uid)

    elif page == "Appointments":
        appointments(uid)

    elif page == "NeuroSocial":
        neurosocial(uid, user["username"])

    elif page == "Research Book":
        research_book(uid)

    elif page == "Concept Map":
        concept_map(uid)

    elif page == "Photo Studio":
        photo_studio()

    elif page == "Progress Dashboard":
        dashboard(uid)

    elif page == "Settings":
        settings_page(uid)


if __name__ == "__main__":
    main()
