"""NeuroSocial friendship and safety primitives.

All actions are scoped to authenticated user IDs supplied by the app layer.
This module does not expose private messages or journal content.
"""
from datetime import datetime, timezone
import secrets


def _now():
    return datetime.now(timezone.utc).isoformat()


def initialize_neurosocial(connection):
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS social_privacy (
        user_id TEXT PRIMARY KEY,
        allow_friend_requests INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS friend_requests (
        id TEXT PRIMARY KEY,
        sender_id TEXT NOT NULL,
        recipient_id TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','accepted','declined','removed')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(sender_id, recipient_id),
        CHECK(sender_id != recipient_id),
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(recipient_id) REFERENCES users(id)
    );
    CREATE INDEX IF NOT EXISTS idx_friend_requests_recipient
        ON friend_requests(recipient_id, status);
    CREATE INDEX IF NOT EXISTS idx_friend_requests_sender
        ON friend_requests(sender_id, status);
    CREATE TABLE IF NOT EXISTS social_blocks (
        blocker_id TEXT NOT NULL,
        blocked_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY(blocker_id, blocked_id),
        CHECK(blocker_id != blocked_id),
        FOREIGN KEY(blocker_id) REFERENCES users(id),
        FOREIGN KEY(blocked_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS social_reports (
        id TEXT PRIMARY KEY,
        reporter_id TEXT NOT NULL,
        reported_user_id TEXT NOT NULL,
        category TEXT NOT NULL,
        details TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        CHECK(reporter_id != reported_user_id),
        FOREIGN KEY(reporter_id) REFERENCES users(id),
        FOREIGN KEY(reported_user_id) REFERENCES users(id)
    );
    """)
    connection.commit()


def set_friend_request_privacy(connection, user_id, allow):
    if not user_id:
        return False
    connection.execute(
        """INSERT INTO social_privacy(user_id, allow_friend_requests, updated_at)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
             allow_friend_requests=excluded.allow_friend_requests,
             updated_at=excluded.updated_at""",
        (str(user_id), 1 if allow else 0, _now()),
    )
    connection.commit()
    return True


def send_friend_request(connection, sender_id, recipient_id):
    sender_id, recipient_id = str(sender_id or ""), str(recipient_id or "")
    if not sender_id or not recipient_id or sender_id == recipient_id:
        return "invalid"
    users = connection.execute(
        "SELECT id FROM users WHERE id IN (?, ?) AND active = 1",
        (sender_id, recipient_id),
    ).fetchall()
    if len(users) != 2:
        return "unavailable"
    blocked = connection.execute(
        """SELECT 1 FROM social_blocks
           WHERE (blocker_id=? AND blocked_id=?)
              OR (blocker_id=? AND blocked_id=?) LIMIT 1""",
        (sender_id, recipient_id, recipient_id, sender_id),
    ).fetchone()
    if blocked:
        return "unavailable"
    privacy = connection.execute(
        "SELECT allow_friend_requests FROM social_privacy WHERE user_id=?",
        (recipient_id,),
    ).fetchone()
    if privacy and not privacy[0]:
        return "not_accepting"
    reverse = connection.execute(
        """SELECT status FROM friend_requests
           WHERE sender_id=? AND recipient_id=?""",
        (recipient_id, sender_id),
    ).fetchone()
    if reverse and reverse[0] == "accepted":
        return "already_friends"
    if reverse and reverse[0] == "pending":
        return "incoming_pending"
    existing = connection.execute(
        "SELECT id, status FROM friend_requests WHERE sender_id=? AND recipient_id=?",
        (sender_id, recipient_id),
    ).fetchone()
    if existing and existing[1] == "pending":
        return "already_pending"
    if existing and existing[1] == "accepted":
        return "already_friends"
    now = _now()
    if existing:
        connection.execute(
            "UPDATE friend_requests SET status='pending', created_at=?, updated_at=? WHERE id=?",
            (now, now, existing[0]),
        )
    else:
        connection.execute(
            """INSERT INTO friend_requests
               (id,sender_id,recipient_id,status,created_at,updated_at)
               VALUES (?,?,?,'pending',?,?)""",
            (secrets.token_hex(16), sender_id, recipient_id, now, now),
        )
    connection.commit()
    return "sent"


def respond_to_friend_request(connection, recipient_id, request_id, accept):
    recipient_id = str(recipient_id or "")
    if not recipient_id or not request_id:
        return False
    status = "accepted" if accept else "declined"
    cursor = connection.execute(
        """UPDATE friend_requests SET status=?, updated_at=?
           WHERE id=? AND recipient_id=? AND status='pending'""",
        (status, _now(), str(request_id), recipient_id),
    )
    connection.commit()
    return cursor.rowcount == 1


def list_friend_requests(connection, user_id, direction="incoming"):
    column = "recipient_id" if direction == "incoming" else "sender_id"
    if direction not in ("incoming", "outgoing") or not user_id:
        return []
    rows = connection.execute(
        f"""SELECT r.id, r.sender_id, r.recipient_id, r.created_at,
                   u.username, u.display_name
            FROM friend_requests r
            JOIN users u ON u.id = {"r.sender_id" if direction == "incoming" else "r.recipient_id"}
            WHERE r.{column}=? AND r.status='pending'
            ORDER BY r.created_at DESC""",
        (str(user_id),),
    ).fetchall()
    return [dict(row) for row in rows]


def list_friends(connection, user_id):
    if not user_id:
        return []
    rows = connection.execute(
        """SELECT u.id, u.username, u.display_name
           FROM friend_requests r
           JOIN users u ON u.id =
             CASE WHEN r.sender_id=? THEN r.recipient_id ELSE r.sender_id END
           WHERE (r.sender_id=? OR r.recipient_id=?)
             AND r.status='accepted' AND u.active=1
             AND NOT EXISTS (
               SELECT 1 FROM social_blocks b
               WHERE (b.blocker_id=? AND b.blocked_id=u.id)
                  OR (b.blocker_id=u.id AND b.blocked_id=?)
             )
           ORDER BY u.display_name COLLATE NOCASE""",
        (str(user_id), str(user_id), str(user_id), str(user_id), str(user_id)),
    ).fetchall()
    return [dict(row) for row in rows]


def search_people(connection, user_id, query, limit=30):
    query = (query or "").strip()
    if not user_id or len(query) < 2:
        return []
    pattern = "%" + query.replace("%", "").replace("_", "") + "%"
    rows = connection.execute(
        """SELECT u.id, u.username, u.display_name
           FROM users u
           LEFT JOIN social_privacy p ON p.user_id=u.id
           WHERE u.active=1 AND u.id != ?
             AND (u.username LIKE ? OR u.display_name LIKE ?)
             AND COALESCE(p.allow_friend_requests,1)=1
             AND NOT EXISTS (
               SELECT 1 FROM social_blocks b
               WHERE (b.blocker_id=? AND b.blocked_id=u.id)
                  OR (b.blocker_id=u.id AND b.blocked_id=?)
             )
           ORDER BY u.display_name COLLATE NOCASE LIMIT ?""",
        (str(user_id), pattern, pattern, str(user_id), str(user_id), min(max(int(limit),1),50)),
    ).fetchall()
    return [dict(row) for row in rows]


def remove_friend(connection, user_id, friend_id):
    cursor = connection.execute(
        """UPDATE friend_requests SET status='removed', updated_at=?
           WHERE status='accepted'
             AND ((sender_id=? AND recipient_id=?) OR (sender_id=? AND recipient_id=?))""",
        (_now(), str(user_id), str(friend_id), str(friend_id), str(user_id)),
    )
    connection.commit()
    return cursor.rowcount == 1


def block_user(connection, blocker_id, blocked_id):
    blocker_id, blocked_id = str(blocker_id or ""), str(blocked_id or "")
    if not blocker_id or not blocked_id or blocker_id == blocked_id:
        return False
    exists = connection.execute(
        "SELECT 1 FROM users WHERE id=? AND active=1", (blocked_id,)
    ).fetchone()
    if not exists:
        return False
    connection.execute(
        "INSERT OR IGNORE INTO social_blocks(blocker_id,blocked_id,created_at) VALUES (?,?,?)",
        (blocker_id, blocked_id, _now()),
    )
    connection.execute(
        """UPDATE friend_requests SET status='removed', updated_at=?
           WHERE status IN ('pending','accepted')
             AND ((sender_id=? AND recipient_id=?) OR (sender_id=? AND recipient_id=?))""",
        (_now(), blocker_id, blocked_id, blocked_id, blocker_id),
    )
    connection.commit()
    return True


def unblock_user(connection, blocker_id, blocked_id):
    cursor = connection.execute(
        "DELETE FROM social_blocks WHERE blocker_id=? AND blocked_id=?",
        (str(blocker_id), str(blocked_id)),
    )
    connection.commit()
    return cursor.rowcount == 1


def report_user(connection, reporter_id, reported_id, category, details=""):
    allowed = {"harassment", "spam", "impersonation", "inappropriate_content", "other"}
    reporter_id, reported_id = str(reporter_id or ""), str(reported_id or "")
    category = str(category or "")
    if not reporter_id or not reported_id or reporter_id == reported_id or category not in allowed:
        return False
    exists = connection.execute(
        "SELECT 1 FROM users WHERE id=? AND active=1", (reported_id,)
    ).fetchone()
    if not exists:
        return False
    connection.execute(
        """INSERT INTO social_reports
           (id,reporter_id,reported_user_id,category,details,created_at)
           VALUES (?,?,?,?,?,?)""",
        (secrets.token_hex(16), reporter_id, reported_id, category, (details or "")[:1000], _now()),
    )
    connection.commit()
    return True
