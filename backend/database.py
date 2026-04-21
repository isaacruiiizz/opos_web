import aiosqlite
import os
from contextlib import asynccontextmanager

DB_PATH = os.getenv("DB_PATH", "./opos.db")

_CREATE_TABLES = [
    """CREATE TABLE IF NOT EXISTS progress (
        topic_id TEXT PRIMARY KEY,
        bloc TEXT NOT NULL,
        score_test REAL DEFAULT 0,
        score_breus REAL DEFAULT 0,
        score_suposit REAL DEFAULT 0,
        score_connecta REAL DEFAULT 0,
        score_buits REAL DEFAULT 0,
        tests_done INTEGER DEFAULT 0,
        last_activity TEXT,
        overall_pct REAL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id TEXT NOT NULL,
        selected_text TEXT NOT NULL,
        color TEXT NOT NULL DEFAULT 'yellow',
        note TEXT,
        position_hash TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS drawings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id TEXT NOT NULL UNIQUE,
        canvas_json TEXT NOT NULL DEFAULT '{}',
        updated_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id TEXT NOT NULL,
        pregunta TEXT NOT NULL,
        resposta TEXT NOT NULL,
        exemple TEXT,
        origin TEXT DEFAULT 'auto',
        leitner_box INTEGER DEFAULT 1,
        next_review TEXT DEFAULT (date('now')),
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS practice_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id TEXT NOT NULL,
        mode TEXT NOT NULL,
        questions_json TEXT,
        answers_json TEXT,
        score REAL,
        feedback_json TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS pdf_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id TEXT NOT NULL UNIQUE,
        cobertura TEXT,
        gaps_json TEXT,
        suggeriments_json TEXT,
        analyzed_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS topic_enrichments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id    TEXT NOT NULL,
        section_idx INTEGER NOT NULL,
        type        TEXT NOT NULL,
        data_json   TEXT NOT NULL,
        created_at  TEXT DEFAULT (datetime('now')),
        UNIQUE(topic_id, section_idx)
    )""",
    """CREATE TABLE IF NOT EXISTS topic_summaries (
        topic_id    TEXT PRIMARY KEY,
        summary     TEXT NOT NULL,
        chips_json  TEXT NOT NULL,
        created_at  TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS simulacre_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT DEFAULT (datetime('now')),
        score REAL NOT NULL,
        passed INTEGER NOT NULL,
        time_taken_seconds INTEGER NOT NULL,
        q_test_correct INTEGER DEFAULT 0,
        q_test_total INTEGER DEFAULT 0,
        q_breus_score REAL DEFAULT 0,
        q_breus_total REAL DEFAULT 0,
        q_suposit_score REAL DEFAULT 0,
        q_suposit_total REAL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS simulacre_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        current_round INTEGER NOT NULL DEFAULT 1,
        pending_topics TEXT NOT NULL DEFAULT '[]'
    )""",
    """CREATE TABLE IF NOT EXISTS simulacre_topic_concepts (
        topic_num INTEGER PRIMARY KEY,
        topic_titol TEXT NOT NULL,
        round_number INTEGER NOT NULL DEFAULT 0,
        concepts_used TEXT NOT NULL DEFAULT '[]'
    )""",
]


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        for stmt in _CREATE_TABLES:
            await db.execute(stmt)
        await db.commit()


@asynccontextmanager
async def get_db_ctx():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise
