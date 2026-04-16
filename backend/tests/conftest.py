import pytest
import asyncio
import os
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def tmp_db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    return db_file


@pytest.fixture(scope="function")
def client(tmp_db):
    import importlib
    import database
    importlib.reload(database)
    import main
    importlib.reload(main)
    from main import app
    asyncio.run(database.init_db())
    with TestClient(app) as c:
        yield c
