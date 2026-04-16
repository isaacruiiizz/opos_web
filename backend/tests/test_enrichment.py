import asyncio
import pytest


def test_enrichments_table_exists(tmp_db):
    import importlib
    import database
    importlib.reload(database)
    asyncio.run(database.init_db())
    import aiosqlite

    async def check():
        async with aiosqlite.connect(tmp_db) as db:
            cur = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='topic_enrichments'"
            )
            row = await cur.fetchone()
            assert row is not None, "topic_enrichments table missing"
            cur2 = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='topic_summaries'"
            )
            row2 = await cur2.fetchone()
            assert row2 is not None, "topic_summaries table missing"

    asyncio.run(check())
