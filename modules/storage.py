
"""NeuroLens shared SQLite database foundation."""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("NEUROLENS_DB", "neurolens.sqlite3")


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            email TEXT NOT NULL COLLATE NOCASE UNIQUE,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            bio TEXT NOT NULL DEFAULT '',
            is_public INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            emoji TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(post_id, user_id),
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            appointment_type TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            preferred_time TEXT NOT NULL,
            purpose TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            details TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS research_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)


def log_activity(user_id, activity_type, points=0, details=""):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO activity_log
               (user_id, activity_type, points, details)
               VALUES (?, ?, ?, ?)""",
            (user_id, activity_type, points, details),
        )


def get_user_by_id(user_id):
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, username, email, display_name, created_at
               FROM users WHERE id = ?""",
            (user_id,),
        ).fetchone()

def _require_user_id(user_id):
    """Reject ambiguous IDs before applying a user-scoped data query."""
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("A positive authenticated Phase 1 user ID is required.")
    return user_id


def get_posts_for_user(user_id):
    """Return only posts owned by the supplied authenticated Phase 1 user ID."""
    user_id = _require_user_id(user_id)
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, user_id, content, created_at
               FROM posts WHERE user_id = ? ORDER BY id""",
            (user_id,),
        ).fetchall()


def get_activity_for_user(user_id):
    """Return only activity rows owned by the supplied authenticated Phase 1 user ID."""
    user_id = _require_user_id(user_id)
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, user_id, activity_type, points, details, created_at
               FROM activity_log WHERE user_id = ? ORDER BY id""",
            (user_id,),
        ).fetchall()



def get_profile_for_user(user_id):
    """Return the profile belonging only to the supplied Phase 1 user ID."""
    user_id = _require_user_id(user_id)
    with get_connection() as conn:
        return conn.execute(
            """SELECT user_id, bio, is_public
               FROM user_profiles WHERE user_id = ?""",
            (user_id,),
        ).fetchone()


def get_comments_for_user(user_id):
    """Return comments authored only by the supplied Phase 1 user ID."""
    user_id = _require_user_id(user_id)
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, post_id, user_id, content, created_at
               FROM comments WHERE user_id = ? ORDER BY id""",
            (user_id,),
        ).fetchall()


def get_reactions_for_user(user_id):
    """Return reactions created only by the supplied Phase 1 user ID."""
    user_id = _require_user_id(user_id)
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, post_id, user_id, emoji, created_at
               FROM reactions WHERE user_id = ? ORDER BY id""",
            (user_id,),
        ).fetchall()


def get_appointments_for_user(user_id):
    """Return appointment requests belonging only to the supplied user ID."""
    user_id = _require_user_id(user_id)
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, user_id, appointment_type, preferred_date,
                      preferred_time, purpose, status, created_at
               FROM appointments WHERE user_id = ? ORDER BY id""",
            (user_id,),
        ).fetchall()


def get_research_notes_for_user(user_id):
    """Return research notes belonging only to the supplied user ID."""
    user_id = _require_user_id(user_id)
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, user_id, title, content, created_at
               FROM research_notes WHERE user_id = ? ORDER BY id""",
            (user_id,),
        ).fetchall()
