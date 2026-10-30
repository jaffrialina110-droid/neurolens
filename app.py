
import os
import io
import re
import json
import time
import uuid
import random
import sqlite3
import hashlib
import hmac
from datetime import datetime
from pathlib import Path

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


# ---------- NEUROLENS SUPABASE CONNECTION ----------

SUPABASE_IMPORT_ERROR = None

try:
    from supabase import create_client
except Exception as exc:
    create_client = None
    SUPABASE_IMPORT_ERROR = repr(exc)


@st.cache_resource
def get_supabase_client():
    """Create and reuse the Supabase client."""
    if create_client is None:
        raise RuntimeError(
            f"Supabase import failed: {SUPABASE_IMPORT_ERROR}"
        )

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception as exc:
        raise RuntimeError(
            f"Could not read Supabase Secrets: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    if not str(url).strip() or not str(key).strip():
        raise RuntimeError(
            "SUPABASE_URL or SUPABASE_KEY is empty."
        )
        
    try:
        return create_client(
            str(url).strip(),
            str(key).strip()
        )
    except Exception as exc:
        raise RuntimeError(
            f"Supabase client initialization failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc


def test_supabase_connection():
    try:
        client = get_supabase_client()
        client.table("profiles").select("id").limit(1).execute()
        return True, "Supabase database access successful."
    except Exception as exc:
        return False, str(exc)

# ---------- SUPABASE PROFILE SYNC ----------

def supabase_profile_id(username):
    """Find or create a profile in Supabase."""
    try:
        client = get_supabase_client()
        username = str(username).strip().lower()

        if not username:
            return None, "Username is missing."

        result = (
            client.table("profiles")
            .select("id")
            .eq("username", username)
            .limit(1)
            .execute()
        )

        if result.data:
            return str(result.data[0]["id"]), "Profile found."

        profile_id = str(uuid.uuid4())

        client.table("profiles").insert({
            "id": profile_id,
            "username": username,
            "display_name": username,
            "bio": "",
            "avatar_url": ""
        }).execute()

        return profile_id, "Profile created successfully."

    except Exception as exc:
        return None, f"Supabase profile sync failed: {exc}"

    

# ---------- APP CONFIGURATION ----------

APP_NAME = "NEUROLENS"
OWNER = "Ayna Jaffri"
DB_PATH = "neurolens.db"
MODEL = "gemini-2.5-flash"
APP_NAME = "NEUROLENS"
OWNER = "Ayna Jaffri"
DB_PATH = "neurolens.db"
MODEL = "gemini-2.5-flash"

st.set_page_config(
    page_title="NeuroLens | Explore the Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- DATABASE ----------

def db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
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
    """
    with db() as con:
        con.executescript(schema)

init_db()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def query(sql, params=(), one=False):
    with db() as con:
        cur = con.execute(sql, params)
        rows = cur.fetchall()
    if one:
        return rows[0] if rows else None
    return rows

def execute(sql, params=()):
    with db() as con:
        cur = con.execute(sql, params)
        return cur.lastrowid

# ---------- SECURITY / LOGIN ----------

def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 310000
    )
    return salt.hex() + ":" + digest.hex()

def verify_password(password, stored):
    try:
        salt_hex, _ = stored.split(":")
        return hmac.compare_digest(hash_password(
            password, bytes.fromhex(salt_hex)
        ), stored)
    except (ValueError, TypeError):
        return False

def get_user():
    return st.session_state.get("user")

def auth_screen():
    st.title("🧠 NeuroLens")
    st.caption("Explore cognition, behavior & the brain")
    st.write("Ayna Jaffri · Independent cognitive neuroscience researcher")

    login_tab, signup_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username").strip().lower()
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log in", use_container_width=True)
        if submit:
            row = query(
                "SELECT * FROM users WHERE username=?",
                (username,), one=True
            )
            if row and verify_password(password, row["password_hash"]):
                st.session_state.user = {
                    "id": row["id"], "username": row["username"]
                }
                st.rerun()
            else:
                st.error("Username or password is incorrect.")

    with signup_tab:
        with st.form("signup_form"):
            username = st.text_input("Choose username").strip().lower()
            email = st.text_input("Email (optional)").strip()
            password = st.text_input("Create password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submit = st.form_submit_button(
                "Create account", use_container_width=True
            )
        if submit:
            if not re.fullmatch(r"[a-z0-9_.-]{3,30}", username):
                st.error("Username: 3–30 characters; use letters, numbers, _ . -")
            elif len(password) < 10:
                st.error("Use a password with at least 10 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    execute(
                        "INSERT INTO users(username,email,password_hash,created_at) "
                        "VALUES(?,?,?,?)",
                        (username, email, hash_password(password), now())
                    )
                    st.success("Account created. Log in to continue.")
                except sqlite3.IntegrityError:
                    st.error("That username is already taken.")

# ---------- GEMINI AI ----------

def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")

def ai_client():
    key = get_api_key()
    if not key or genai is None:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception:
        return None

def ask_gemini(prompt, system_instruction=None):
    client = ai_client()
    if client is None:
        return (
            "Gemini is not configured. Add GEMINI_API_KEY in "
            "Streamlit Secrets, then restart the app."
        )
    try:
        full_prompt = (
            (system_instruction or
             "You are Ayna, a careful neuroscience learning assistant. "
             "Explain uncertainty, do not diagnose, and distinguish "
             "scientific evidence from hypotheses.") +
            "\n\nUser request:\n" + prompt
        )
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
        )
        return response.text or "No text response was returned."
    except Exception as exc:
        return "Gemini request failed: " + str(exc)

# ---------- SHARED HELPERS ----------

def save_activity(user_id, name, score=None, details=""):
    # Save in local database first
    execute(
        "INSERT INTO activities(user_id,activity,score,details,created_at) "
        "VALUES(?,?,?,?,?)",
        (user_id, name, score, details[:2000], now())
    )

    try:
        user = get_user()

        if not user:
            st.warning("Please log in first.")
            return

        profile_id, message = supabase_profile_id(
            user.get("username", "")
        )

        if not profile_id:
            st.error(message)
            return

        client = get_supabase_client()

        client.table("lab_results").insert({
            "user_id": profile_id,
            "experiment_type": str(name)[:200],
            "equipment": "NeuroLens",
            "character_type": "User",
            "score": score,
            "accuracy": None,
            "reaction_time": None,
            "result_data": {"details": str(details)[:2000]},
            "is_simulated": True
        }).execute()

        st.success("Activity synced to Supabase!")

    except Exception as exc:
        st.error(f"Supabase sync failed: {exc}")

def section_title(title, description=""):
    st.title(title)
    if description:
        st.caption(description)

def get_user_rows(table, user_id, order="created_at DESC"):
    allowed = {
        "journal", "research", "activities", "voice_logs",
        "appointments", "posts", "concepts"
    }
    if table not in allowed:
        return []
    return query(
        f"SELECT * FROM {table} WHERE user_id=? ORDER BY {order}",
        (user_id,)
    )

# ---------- BRAIN EXPLORER ----------

def brain_explorer():
    section_title(
        "🧠 Brain Explorer",
        "Learn about brain regions and the systems involved in cognition."
    )
    regions = {
        "Prefrontal cortex": (
            "Planning, working memory, goal-directed behavior and cognitive control.",
            "Executive control is distributed across interacting networks."
        ),
        "Hippocampus": (
            "Important for forming many kinds of episodic and relational memories.",
            "Memory also depends on distributed cortical and subcortical systems."
        ),
        "Striatum": (
            "Part of the basal ganglia; involved in action selection, learning and reward.",
            "Its functions depend on circuit, cell type, task and context."
        ),
        "Anterior cingulate cortex (ACC)": (
            "Involved in monitoring, effort, conflict and adaptive control.",
            "No single region performs one isolated mental function."
        ),
        "Attention networks": (
            "Distributed systems support alerting, orienting and executive attention.",
            "Attention is dynamic and depends on task and environment."
        ),
        "Reward systems": (
            "Dopamine and connected circuits contribute to learning and motivation.",
            "Dopamine is not simply a 'pleasure chemical'."
        ),
        "Consciousness": (
            "Research examines wakefulness, awareness and their neural correlates.",
            "The neural basis of subjective experience remains an active research question."
        ),
    }
    selected = st.selectbox("Choose a topic", list(regions))
    st.subheader(selected)
    st.write(regions[selected][0])
    st.info("Research note: " + regions[selected][1])
    st.markdown("### Explore a research question")
    q = st.text_input(
        "What would you like to learn?",
        placeholder="e.g. How does working memory involve the PFC?"
    )
    if st.button("Ask Ayna about this brain topic"):
        if q.strip():
            answer = ask_gemini(
                f"Explain the topic '{selected}'. Answer this question: {q}",
                "You are Ayna, a neuroscience educator. Use accurate, "
                "accessible explanations and distinguish evidence from hypotheses."
            )
            st.write(answer)

# ---------- CSTC CIRCUIT LEARNING ----------

def cstc_learning():
    section_title(
        "🔁 CSTC Circuit Learning",
        "Cortico-striato-thalamo-cortical loops: a simplified learning model."
    )
    st.markdown("""
    **Simplified direct pathway**

    Cortex → Striatum (D1-enriched pathway) → GPi/SNr inhibition
    → reduced inhibition of thalamus → thalamocortical activity

    **Simplified indirect pathway**

    Cortex → Striatum (D2-enriched pathway) → GPe inhibition
    → STN activity → GPi/SNr output → thalamic inhibition

    **Hyperdirect pathway**

    Cortex → STN → GPi/SNr output

    Dopamine from SNc modulates striatal circuits. These diagrams simplify
    a complex, parallel and interconnected system; they are not a complete
    anatomical model.
    """)
    pathway = st.radio(
        "Choose a pathway to study",
        ["Direct", "Indirect", "Hyperdirect"],
        horizontal=True
    )
    descriptions = {
        "Direct": "Often described as facilitating selected actions through a net reduction in thalamic inhibition.",
        "Indirect": "Often described as helping regulate or suppress competing actions through additional basal-ganglia relays.",
        "Hyperdirect": "Provides a relatively fast cortical route to the STN and basal-ganglia output nuclei."
    }
    st.info(descriptions[pathway])
    question = st.text_input("Ask a CSTC question")
    if st.button("Explain this pathway"):
        if question.strip():
            st.write(ask_gemini(
                f"Explain the {pathway} pathway of CSTC circuits. "
                f"Question: {question}",
                "Explain circuit neuroscience carefully. Mention limitations "
                "of simplified direct/indirect pathway models."
            ))

# ---------- LAB GAMES ----------

def neuroscience_lab(uid):
    section_title(
        "🧪 Interactive Neuroscience Lab",
        "Practice cognitive tasks. These activities are educational, not diagnostic."
    )
    game = st.selectbox(
        "Select an activity",
        ["Memory Sequence", "Attention: Find X", "Stroop Control",
         "Decision & Reward", "Pattern Reasoning"]
    )

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
            st.caption("Study it, then hide it before answering.")
        if st.button("Hide code"):
            st.session_state.memory_visible = False
        answer = st.text_input("Enter the code from memory")
        if st.button("Check memory answer"):
            target = st.session_state.memory_target
            score = sum(a == b for a, b in zip(answer, target))
            pct = round(100 * score / len(target)) if target else 0
            st.write(f"Position matches: {score}/{len(target)} ({pct}%)")
            save_activity(uid, game, pct, f"Position matches: {score}/{len(target)}")
            st.session_state.memory_target = "".join(
                random.choices("123456789", k=6)
            )
            st.session_state.memory_visible = False
            st.rerun()

    elif game == "Attention: Find X":
        letters = random.choices(["O", "Q", "C", "D"], k=35)
        target_index = random.randrange(len(letters))
        letters[target_index] = "X"
        st.write("Find the X:")
        st.markdown(" ".join(f"`{x}`" for x in letters))
        choice = st.number_input(
            "Position of X (1–36)", min_value=1, max_value=36, value=1
        )
        if st.button("Check attention"):
            correct = int(choice) == target_index + 1
            st.success("Correct!" if correct else f"Not quite. X was at position {target_index + 1}.")
            save_activity(uid, game, 100 if correct else 0, f"Correct={correct}")

    elif game == "Stroop Control":
        words = [
            ("RED", "blue"), ("BLUE", "red"), ("GREEN", "green"),
            ("YELLOW", "red"), ("PURPLE", "blue")
        ]
        if "stroop_item" not in st.session_state:
            st.session_state.stroop_item = random.choice(words)
        word, ink = st.session_state.stroop_item
        st.markdown(
            f"<h2 style='text-align:center;color:{ink}'>{word}</h2>",
            unsafe_allow_html=True
        )
        st.caption("Choose the INK COLOUR, not the written word.")
        choice = st.radio(
            "Ink colour",
            ["red", "blue", "green", "yellow", "purple"],
            horizontal=True
        )
        if st.button("Check Stroop answer"):
            correct = choice == ink
            st.success("Correct!" if correct else f"The ink colour was {ink}.")
            save_activity(uid, game, 100 if correct else 0, f"Selected={choice}; target={ink}")
            st.session_state.stroop_item = random.choice(words)

    elif game == "Decision & Reward":
        st.write("Choose between a smaller immediate reward and a larger delayed reward.")
        choice = st.radio(
            "Which would you choose?",
            ["Rs 1,000 today", "Rs 1,500 after 30 days"],
        )
        reason = st.text_area("Why did you choose it? (optional)")
        if st.button("Save decision reflection"):
            save_activity(uid, game, None, f"Choice={choice}; Reflection={reason}")
            st.success("Reflection saved. One choice does not define your personality.")

    elif game == "Pattern Reasoning":
        st.write("Complete the pattern: 2 → 4 → 8 → 16 → ?")
        answer = st.number_input("Next number", min_value=0, value=0)
        if st.button("Check pattern"):
            correct = answer == 32
            st.success("Correct!" if correct else "Try doubling the previous number.")
            save_activity(uid, game, 100 if correct else 0, f"Answer={answer}")

# ---------- BRAIN PUZZLE ----------

def brain_puzzle(uid):
    section_title("🧩 Brain Puzzle", "Sliding-number puzzle for planning and problem-solving.")
    size = st.radio("Grid size", [3, 4], horizontal=True)
    key = f"puzzle_{size}"
    if key not in st.session_state:
        board = list(range(1, size * size)) + [0]
        for _ in range(120):
            blank = board.index(0)
            moves = []
            if blank % size > 0: moves.append(blank - 1)
            if blank % size < size - 1: moves.append(blank + 1)
            if blank >= size: moves.append(blank - size)
            if blank < size * (size - 1): moves.append(blank + size)
            other = random.choice(moves)
            board[blank], board[other] = board[other], board[blank]
        st.session_state[key] = board
        st.session_state[f"{key}_moves"] = 0

    board = st.session_state[key]
    cols = st.columns(size)
    for i, value in enumerate(board):
        with cols[i % size]:
            label = "⬜" if value == 0 else str(value)
            if st.button(label, key=f"{key}_tile_{i}", use_container_width=True):
                blank = board.index(0)
                if abs(blank // size - i // size) + abs(blank % size - i % size) == 1:
                    board[blank], board[i] = board[i], board[blank]
                    st.session_state[f"{key}_moves"] += 1
                    st.rerun()
    st.caption(f"Moves: {st.session_state[f'{key}_moves']}")
    if board == list(range(1, size * size)) + [0]:
        st.success("Puzzle solved!")
        if st.button("Save puzzle result"):
            save_activity(uid, f"Brain Puzzle {size}x{size}", 100,
                          f"Moves={st.session_state[f'{key}_moves']}")
    if st.button("Shuffle puzzle"):
        del st.session_state[key]
        st.rerun()

# ---------- ASK AYNA ----------

def ask_ayna():
    section_title("🤖 Ask Ayna AI", "Your AI learning companion for cognition, behavior and neuroscience.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    prompt = st.chat_input("Ask Ayna a neuroscience or research question...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        history = "\n".join(
            f"{x['role']}: {x['content']}"
            for x in st.session_state.chat_history[-12:]
        )
        with st.chat_message("assistant"):
            with st.spinner("Ayna is thinking..."):
                answer = ask_gemini(
                    history,
                    "You are Ayna, an AI assistant inside NeuroLens. "
                    "Help with neuroscience, research design, cognition and "
                    "learning. Do not diagnose or claim certainty where evidence "
                    "is limited. Never claim an activity measures brain signals."
                )
                st.markdown(answer)
        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer}
        )

# ---------- VOICE STUDIO ----------

def voice_studio(uid):
    section_title(
        "🎙️ Voice Studio",
        "Record or upload audio for AI-assisted transcription and reflection."
    )
    st.warning(
        "Audio analysis can be wrong. Emotion labels are tentative, not a "
        "mental-health assessment. Do not upload other people's private audio "
        "without their permission."
    )
    audio = None
    mime = "audio/wav"
    if hasattr(st, "audio_input"):
        try:
            audio = st.audio_input("Record your voice")
        except Exception:
            pass
    uploaded = st.file_uploader(
        "Or upload audio", type=["wav", "mp3", "m4a", "ogg", "webm"]
    )
    if uploaded is not None:
        audio = uploaded
        mime = uploaded.type or "audio/wav"

    if audio is not None:
        audio_bytes = audio.getvalue()
        st.audio(audio_bytes, format=mime)
        if st.button("Transcribe and analyse audio", type="primary"):
            client = ai_client()
            if client is None:
                st.error("Gemini API is not configured.")
            else:
                try:
                    mime = getattr(audio, "type", None) or mime
                    with st.spinner("Processing audio..."):
                        response = client.models.generate_content(
                            model=MODEL,
                            contents=[
                                types.Part.from_bytes(
                                    data=audio_bytes, mime_type=mime
                                ),
                                (
                                    "If this audio format is supported, provide: "
                                    "1) best-effort verbatim transcription, "
                                    "2) a short neutral summary, "
                                    "3) possible expressive tone only if supported "
                                    "by the audio, clearly label uncertainty, "
                                    "4) 3 suitable emojis. Do not diagnose, infer "
                                    "identity, or claim to know internal feelings. "
                                    "If audio cannot be processed, say so."
                                )
                            ]
                        )
                    result = response.text or "No result returned."
                    st.subheader("AI audio result")
                    st.write(result)
                    transcript = st.text_area(
                        "Edit/copy the transcript if needed",
                        value=result,
                        key="voice_transcript_edit"
                    )
                    own_mood = st.selectbox(
                        "How do YOU feel? (optional)",
                        ["Prefer not to say", "Calm", "Happy", "Sad",
                         "Stressed", "Tired", "Focused", "Unsure"]
                    )
                    if st.button("Save voice reflection"):
                        execute(
                            "INSERT INTO voice_logs(user_id,transcript,reflection,emoji,created_at) "
                            "VALUES(?,?,?,?,?)",
                            (uid, transcript, f"Self-reported mood: {own_mood}",
                             "AI suggestions included in result", now())
                        )
                        st.success("Voice reflection saved.")
                except Exception as exc:
                    st.error(
                        "Audio processing failed. The selected Gemini model "
                        "may not support this audio format. Details: " + str(exc)
                    )

    st.subheader("Saved voice reflections")
    logs = get_user_rows("voice_logs", uid)
    for log in logs[:10]:
        with st.expander(log["created_at"]):
            st.write(log["transcript"])
            st.caption(log["reflection"])

# ---------- PRIVATE JOURNAL ----------

def private_journal(uid):
    section_title("🌿 Private Journal", "Personal reflections saved to your account.")
    with st.form("journal_form", clear_on_submit=True):
        title = st.text_input("Entry title", max_chars=150)
        body = st.text_area("Your reflection", height=180)
        mood = st.selectbox(
            "Optional self-reported mood",
            ["Not specified", "Calm", "Happy", "Sad", "Stressed",
             "Motivated", "Tired", "Reflective"]
        )
        submit = st.form_submit_button("Save private entry")
    if submit:
        if title.strip() and body.strip():
            execute(
                "INSERT INTO journal(user_id,title,body,mood,created_at) VALUES(?,?,?,?,?)",
                (uid, title.strip(), body.strip(), mood, now())
            )
            st.success("Journal entry saved.")
            st.rerun()
        else:
            st.error("Add a title and reflection.")
    for entry in get_user_rows("journal", uid):
        with st.expander(f"{entry['title']} · {entry['created_at']}"):
            st.caption("Self-reported mood: " + str(entry["mood"]))
            st.write(entry["body"])
            if st.button("Delete entry", key=f"del_journal_{entry['id']}"):
                execute("DELETE FROM journal WHERE id=? AND user_id=?",
                        (entry["id"], uid))
                st.rerun()

# ---------- APPOINTMENTS ----------

def appointments(uid):
    section_title("📅 Appointment Requests", "Submit a request; this does not automatically confirm a booking.")
    with st.form("appointment_form"):
        topic = st.selectbox(
            "Request type",
            ["Neuroscience consultation", "Research discussion",
             "Project feedback", "Other"]
        )
        date = st.date_input("Preferred date")
        tm = st.selectbox(
            "Preferred time",
            ["Morning", "Afternoon", "Evening", "Flexible"]
        )
        message = st.text_area("What would you like to discuss?")
        submit = st.form_submit_button("Submit request")
    if submit:
        execute(
            "INSERT INTO appointments(user_id,topic,preferred_date,preferred_time,message,status,created_at) "
            "VALUES(?,?,?,?,?,'Pending',?)",
            (uid, topic, str(date), tm, message.strip(), now())
        )
        st.success("Request saved as Pending. No appointment is confirmed yet.")
    st.subheader("Your requests")
    for a in get_user_rows("appointments", uid):
        st.write(f"**{a['topic']}** — {a['preferred_date']} · {a['preferred_time']}")
        st.caption(f"Status: {a['status']} · Submitted {a['created_at']}")

# ---------- NEUROSOCIAL ----------

def neurosocial(uid, username):
    section_title("🌐 NeuroSocial", "Share neuroscience learning notes and discuss ideas respectfully.")
    with st.form("post_form", clear_on_submit=True):
        body = st.text_area("Write a post", max_chars=3000)
        submit = st.form_submit_button("Publish post")
    if submit:
        if body.strip():
            execute(
                "INSERT INTO posts(user_id,body,created_at) VALUES(?,?,?)",
                (uid, body.strip(), now())
            )
            st.rerun()

    posts = query("""
        SELECT posts.*, users.username,
        (SELECT COUNT(*) FROM comments WHERE comments.post_id=posts.id) AS comment_count
        FROM posts JOIN users ON posts.user_id=users.id
        ORDER BY posts.id DESC LIMIT 100
    """)
    for post in posts:
        with st.container(border=True):
            st.caption(f"@{post['username']} · {post['created_at']}")
            st.write(post["body"])
            reactions = query(
                "SELECT reaction,COUNT(*) AS n FROM reactions WHERE post_id=? GROUP BY reaction",
                (post["id"],)
            )
            st.caption(" · ".join(f"{r['reaction']} {r['n']}" for r in reactions) or "No reactions yet")
            reaction = st.selectbox(
                "React", ["🧠", "👍", "❤️", "💡"],
                key=f"react_{post['id']}"
            )
            if st.button("Save reaction", key=f"save_react_{post['id']}"):
                execute(
                    "INSERT INTO reactions(post_id,user_id,reaction) VALUES(?,?,?) "
                    "ON CONFLICT(post_id,user_id) DO UPDATE SET reaction=excluded.reaction",
                    (post["id"], uid, reaction)
                )
                st.rerun()
            with st.expander(f"Comments ({post['comment_count']})"):
                comments = query("""
                    SELECT comments.*, users.username
                    FROM comments JOIN users ON comments.user_id=users.id
                    WHERE post_id=? ORDER BY comments.id ASC
                """, (post["id"],))
                for c in comments:
                    st.write(f"**@{c['username']}**: {c['body']}")
                comment = st.text_input("Add comment", key=f"comment_{post['id']}")
                if st.button("Post comment", key=f"send_comment_{post['id']}"):
                    if comment.strip():
                        execute(
                            "INSERT INTO comments(post_id,user_id,body,created_at) VALUES(?,?,?,?)",
                            (post["id"], uid, comment.strip()[:1000], now())
                        )
                        st.rerun()
            if post["user_id"] == uid:
                if st.button("Delete your post", key=f"delete_post_{post['id']}"):
                    execute("DELETE FROM comments WHERE post_id=?", (post["id"],))
                    execute("DELETE FROM reactions WHERE post_id=?", (post["id"],))
                    execute("DELETE FROM posts WHERE id=? AND user_id=?", (post["id"], uid))
                    st.rerun()

# ---------- RESEARCH BOOK ----------

def research_book(uid):
    section_title("📚 Research Book", "Organize literature notes, ideas, and research questions.")
    with st.form("research_form", clear_on_submit=True):
        title = st.text_input("Entry title")
        topic = st.text_input("Topic / research question")
        notes = st.text_area("Notes", height=150)
        tags = st.text_input("Tags (comma-separated)")
        submit = st.form_submit_button("Save research entry")
    if submit:
        if title.strip():
            execute(
                "INSERT INTO research(user_id,title,topic,notes,tags,created_at) VALUES(?,?,?,?,?,?)",
                (uid, title.strip(), topic, notes, tags, now())
            )
            st.success("Research entry saved.")
            st.rerun()
    entries = get_user_rows("research", uid)
    for item in entries:
        with st.expander(item["title"]):
            st.caption(item["topic"] or "")
            st.write(item["notes"] or "")
            st.caption("Tags: " + (item["tags"] or "None"))
            if st.button("Delete research entry", key=f"del_research_{item['id']}"):
                execute("DELETE FROM research WHERE id=? AND user_id=?",
                        (item["id"], uid))
                st.rerun()

# ---------- CONCEPT MAP ----------

def concept_map(uid):
    section_title("🕸️ Concept Map", "Create a simple map of connections between research concepts.")
    with st.form("concept_form", clear_on_submit=True):
        concept = st.text_input("Concept")
        connects = st.text_input("Connects to")
        explanation = st.text_area("Why are these concepts connected?")
        submit = st.form_submit_button("Add concept")
    if submit:
        if concept.strip():
            execute(
                "INSERT INTO concepts(user_id,concept,connects_to,explanation,created_at) VALUES(?,?,?,?,?)",
                (uid, concept.strip(), connects.strip(), explanation.strip(), now())
            )
            st.rerun()
    rows = get_user_rows("concepts", uid)
    if rows:
        df = pd.DataFrame([dict(x) for x in rows])
        st.dataframe(
            df[["concept", "connects_to", "explanation", "created_at"]],
            use_container_width=True,
            hide_index=True
        )
        try:
            import graphviz
            graph = graphviz.Digraph()
            for row in rows:
                graph.node(row["concept"])
                if row["connects_to"].strip():
                    graph.edge(row["concept"], row["connects_to"])
            st.graphviz_chart(graph)
        except Exception:
            st.caption("Install Graphviz to render the visual concept map.")
        if st.button("Export concept map as CSV"):
            st.download_button(
                "Download CSV",
                df.to_csv(index=False).encode("utf-8"),
                "neurolens_concepts.csv",
                "text/csv"
            )

# ---------- PHOTO STUDIO ----------

def photo_studio():
    section_title("📸 Photo Studio", "Apply simple image filters in your browser session.")
    uploaded = st.file_uploader(
        "Upload a photo", type=["png", "jpg", "jpeg", "webp"]
    )
    if uploaded:
        try:
            original = Image.open(uploaded).convert("RGB")
            brightness = st.slider("Brightness", 0.3, 2.0, 1.0, 0.1)
            contrast = st.slider("Contrast", 0.3, 2.0, 1.0, 0.1)
            saturation = st.slider("Saturation", 0.0, 2.0, 1.0, 0.1)
            effect = st.selectbox(
                "Filter",
                ["Original", "Grayscale", "Blur", "Sharpen", "Contour"]
            )
            edited = ImageEnhance.Brightness(original).enhance(brightness)
            edited = ImageEnhance.Contrast(edited).enhance(contrast)
            edited = ImageEnhance.Color(edited).enhance(saturation)
            filters = {
                "Grayscale": ImageFilter.Color3DLUT if False else None,
                "Blur": ImageFilter.BLUR,
                "Sharpen": ImageFilter.SHARPEN,
                "Contour": ImageFilter.CONTOUR
            }
            if effect == "Grayscale":
                edited = edited.convert("L").convert("RGB")
            elif effect in filters and filters[effect] is not None:
                edited = edited.filter(filters[effect])
            left, right = st.columns(2)
            left.image(original, caption="Original", use_container_width=True)
            right.image(edited, caption="Edited", use_container_width=True)
            output = io.BytesIO()
            edited.save(output, format="PNG")
            st.download_button(
                "Download edited image",
                output.getvalue(),
                "neurolens_edited.png",
                "image/png"
            )
        except Exception as exc:
            st.error("Could not process this image: " + str(exc))

# ---------- PROGRESS DASHBOARD ----------

def dashboard(uid):
    section_title("📈 Progress Dashboard", "Your saved task history and activity trends.")
    activities = get_user_rows("activities", uid)
    journal = get_user_rows("journal", uid)
    research = get_user_rows("research", uid)
    voices = get_user_rows("voice_logs", uid)
    appointments_list = get_user_rows("appointments", uid)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Activities", len(activities))
    c2.metric("Journal entries", len(journal))
    c3.metric("Research notes", len(research))
    c4.metric("Voice logs", len(voices))
    if activities:
        df = pd.DataFrame([dict(a) for a in activities])
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        scored = df.dropna(subset=["score"])
        if not scored.empty:
            st.subheader("Recorded task scores")
            st.line_chart(scored.set_index("created_at")["score"])
        st.subheader("Recent activity")
        st.dataframe(
            df[["activity", "score", "details", "created_at"]].head(50),
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
        st.info("Complete a lab activity to begin building your progress history.")
    if appointments_list:
        st.subheader("Appointment request summary")
        st.write(f"{len(appointments_list)} request(s) submitted.")


# ---------- APP SETTINGS ----------

def settings_page(uid):
    section_title("⚙️ Settings & Privacy")

    user = st.session_state.get("user", {})
    st.write("**Signed in as:**", user.get("username", "Unknown"))
    st.write("**App creator:**", OWNER)
    st.write("**Local database:**", DB_PATH)

    st.subheader("Supabase Connection")

    if st.button("Test Supabase Connection", type="primary"):
        with st.spinner("Checking Supabase access..."):
            success, message = test_supabase_connection()

        if success:
            st.success(message)
        else:
            st.error(message)

    st.caption(
        "This tests read access to the existing profiles table. "
        "It does not migrate SQLite data or connect every app feature."
    )

    st.divider()
    st.subheader("Account data")

    if st.button("Export my journal as JSON"):
        entries = [
            dict(x) for x in get_user_rows("journal", uid)
        ]
        st.download_button(
            "Download journal JSON",
            json.dumps(entries, ensure_ascii=False, indent=2),
            "neurolens_journal.json",
            "application/json",
        )

    st.divider()

    if st.button("Log out"):
        st.session_state.pop("user", None)
        st.rerun()


# ---------- MAIN ROUTER ----------

def main():
    if not get_user():
        auth_screen()
        return

    user = get_user()
    uid = user["id"]
    st.sidebar.title("🧠 NEUROLENS")
    st.sidebar.caption("Explore cognition, behavior & the brain")
    st.sidebar.write(f"Welcome, @{user['username']}")
    pages = [
        "Home", "Brain Explorer", "CSTC Circuit Learning",
        "Neuroscience Lab", "Brain Puzzle", "Ask Ayna AI",
        "Voice Studio", "Private Journal", "Appointments",
        "NeuroSocial", "Research Book", "Concept Map",
        "Photo Studio", "Progress Dashboard", "Settings"
    ]
    page = st.sidebar.radio("Navigate", pages)
    st.sidebar.divider()
    st.sidebar.caption("Educational tool — not a diagnostic instrument.")

    if page == "Home":
        st.title("🧠 NeuroLens")
        st.subheader("Explore cognition, behavior & the brain")
        st.write(
            "An interactive learning workspace created by Ayna Jaffri "
            "for exploring neuroscience, cognition, behavior and research."
        )
        st.markdown("### Explore your workspace")
        c1, c2, c3 = st.columns(3)
        c1.metric("Learning areas", "Brain + CSTC")
        c2.metric("Cognitive tasks", "5")
        c3.metric("AI assistant", "Ask Ayna")
        st.markdown("""
        - Learn about brain regions and CSTC pathways.
        - Practice memory, attention, Stroop and decision tasks.
        - Save research ideas and private reflections.
        - Use Gemini-powered AI and supported audio tools.
        """)
        st.caption("Task results describe task performance, not brain activity.")
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

main()
