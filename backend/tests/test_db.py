import pytest
import aiosqlite
import database


async def test_init_db_creates_all_tables(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    import importlib
    importlib.reload(database)
    await database.init_db()
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in await cursor.fetchall()}
    expected = {"progress", "annotations", "drawings", "flashcards",
                "practice_sessions", "pdf_analysis", "config"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"
