"""
core/db.py - All persistence in one place.

Design decision worth understanding: this uses SQLAlchemy Core (not the
heavier ORM layer) so the SAME code works against:
  - local SQLite (default - zero setup, good for testing)
  - Supabase/Postgres (set DATABASE_URL in .env - required for a public
    Streamlit Community Cloud deployment, whose local disk does NOT
    persist between restarts)

No vector database here on purpose. v3's ChromaDB + HuggingFace embeddings
setup added a ~90MB model download and real complexity, but was never
actually wired up. For a first working version, "memories" are stored as
plain text facts and the LLM sees the last N of them as context - simple,
zero extra dependencies, upgradeable to real vector search later if you
find plain recall isn't good enough.
"""
import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Boolean, ForeignKey
)

DB_URL = os.getenv("DATABASE_URL") or "sqlite:///data/elder.db"

if DB_URL.startswith("sqlite"):
    os.makedirs("data", exist_ok=True)

engine = create_engine(DB_URL, pool_pre_ping=True)
metadata = MetaData()

chat_sessions = Table(
    "chat_sessions", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(120)),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("updated_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

chat_history = Table(
    "chat_history", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Integer, ForeignKey("chat_sessions.id"), nullable=True),
    Column("role", String(20), nullable=False),
    Column("content", String, nullable=False),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

reminders = Table(
    "reminders", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("text", String, nullable=False),
    Column("remind_at", String(50)),
    Column("done", Boolean, default=False),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

memories = Table(
    "memories", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("fact", String, nullable=False),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

memoir_entries = Table(
    "memoir_entries", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("topic", String(200)),
    Column("story", String, nullable=False),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

game_scores = Table(
    "game_scores", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("game_name", String(50)),
    Column("correct", Boolean),
    Column("played_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)


def init_db():
    metadata.create_all(engine)


# ---------- Chat sessions ----------
def create_session(title: str = "New conversation") -> int:
    with engine.begin() as conn:
        result = conn.execute(chat_sessions.insert().values(title=title))
        return result.inserted_primary_key[0]


def get_sessions(limit: int = 20):
    """Most recently active conversations first."""
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, title, created_at, updated_at "
                "FROM chat_sessions ORDER BY updated_at DESC LIMIT :lim"
            ),
            {"lim": limit},
        ).fetchall()
    return rows


def touch_session(session_id: int):
    with engine.begin() as conn:
        conn.execute(
            chat_sessions.update()
            .where(chat_sessions.c.id == session_id)
            .values(updated_at=datetime.now(timezone.utc))
        )


def set_session_title(session_id: int, title: str):
    with engine.begin() as conn:
        conn.execute(
            chat_sessions.update()
            .where(chat_sessions.c.id == session_id)
            .values(title=title[:120])
        )


def delete_session(session_id: int):
    with engine.begin() as conn:
        conn.execute(chat_history.delete().where(chat_history.c.session_id == session_id))
        conn.execute(chat_sessions.delete().where(chat_sessions.c.id == session_id))


# ---------- Chat messages (scoped to a session) ----------
def save_message(session_id: int, role: str, content: str):
    with engine.begin() as conn:
        conn.execute(
            chat_history.insert().values(session_id=session_id, role=role, content=content)
        )
    touch_session(session_id)


def get_session_messages(session_id: int, limit: int = 30) -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT role, content FROM chat_history "
                "WHERE session_id = :sid ORDER BY id DESC LIMIT :lim"
            ),
            {"sid": session_id, "lim": limit},
        ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def get_recent_messages(limit: int = 20) -> list[dict]:
    """Most recent messages ACROSS ALL sessions - used by Family Bridge's
    mood summary and the Memories page's fact extraction, where we want
    a general recent picture, not one specific conversation."""
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT role, content FROM chat_history ORDER BY id DESC LIMIT :lim"),
            {"lim": limit},
        ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


# ---------- Reminders ----------
def add_reminder(text_: str, remind_at: str = ""):
    with engine.begin() as conn:
        conn.execute(reminders.insert().values(text=text_, remind_at=remind_at, done=False))


def get_reminders(include_done: bool = True):
    with engine.begin() as conn:
        q = "SELECT id, text, remind_at, done, created_at FROM reminders ORDER BY id DESC"
        rows = conn.execute(text(q)).fetchall()
    if not include_done:
        rows = [r for r in rows if not r[3]]
    return rows


def mark_reminder_done(reminder_id: int):
    with engine.begin() as conn:
        conn.execute(
            reminders.update().where(reminders.c.id == reminder_id).values(done=True)
        )


# ---------- Memories (facts) ----------
def save_fact(fact: str):
    with engine.begin() as conn:
        conn.execute(memories.insert().values(fact=fact))


def get_facts(limit: int = 50):
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT fact, created_at FROM memories ORDER BY id DESC LIMIT :lim"),
            {"lim": limit},
        ).fetchall()
    return rows


# ---------- Memoir ----------
def save_memoir_entry(topic: str, story: str):
    with engine.begin() as conn:
        conn.execute(memoir_entries.insert().values(topic=topic, story=story))


def get_memoir_entries():
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT topic, story, created_at FROM memoir_entries ORDER BY id DESC")
        ).fetchall()
    return rows


# ---------- Games ----------
def save_game_result(game_name: str, correct: bool):
    with engine.begin() as conn:
        conn.execute(game_scores.insert().values(game_name=game_name, correct=correct))


def get_game_stats(game_name: str):
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT correct FROM game_scores WHERE game_name = :g"),
            {"g": game_name},
        ).fetchall()
    total = len(rows)
    correct = sum(1 for r in rows if r[0])
    return correct, total
