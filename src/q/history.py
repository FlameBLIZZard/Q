"""Conversation storage in SQLite (~/.q/history.db).

Two tables: `conversations` (one row per chat) and `messages` (one row per turn).
SQLite ships with Python, needs no server, and the file is easy to inspect with
any SQLite viewer, which makes it a good fit for a local tool.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from q import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT,
    model      TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class History:
    def __init__(self, path: Path | None = None):
        path = path or config.history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA)

    def new_conversation(self, model: str) -> int:
        cur = self.db.execute("INSERT INTO conversations (model, created_at) VALUES (?, ?)", (model, _now()))
        self.db.commit()
        return cur.lastrowid

    def add_message(self, conversation_id: int, role: str, content: str) -> None:
        self.db.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, _now()),
        )
        # The first user message becomes the title, so /history is readable.
        if role == "user":
            self.db.execute(
                "UPDATE conversations SET title = ? WHERE id = ? AND title IS NULL",
                (content[:60], conversation_id),
            )
        self.db.commit()

    def messages(self, conversation_id: int) -> list[dict]:
        rows = self.db.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        )
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    def recent(self, limit: int = 10) -> list[sqlite3.Row]:
        return self.db.execute(
            """SELECT c.id, c.title, c.model, c.created_at, COUNT(m.id) AS n
               FROM conversations c LEFT JOIN messages m ON m.conversation_id = c.id
               GROUP BY c.id ORDER BY c.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()

    def close(self) -> None:
        self.db.close()
