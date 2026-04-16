import asyncio
import pytest
from unittest.mock import AsyncMock, patch


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


def test_enrich_section_timeline(client):
    import services.gemini as g
    mock_result = {
        "type": "timeline",
        "data": [
            {"step": 1, "title": "Iniciació", "desc": "A instància de part"},
            {"step": 2, "title": "Instrucció", "desc": "Al·legacions i informes"},
            {"step": 3, "title": "Terminació", "desc": "Resolució motivada"},
        ]
    }
    with patch.object(g.GeminiService, "enrich_section", AsyncMock(return_value=mock_result)):
        resp = client.post("/api/ai/enrich", json={
            "topic_id": "general_1",
            "section_idx": 0,
            "section_markdown": "## Fases\n1. Iniciació\n2. Instrucció\n3. Terminació"
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "timeline"
    assert len(data["data"]) == 3


def test_enrich_section_persisted(client):
    import services.gemini as g
    mock_result = {"type": "callouts", "data": [{"variant": "law", "title": "Llei", "text": "LPACAP"}]}
    with patch.object(g.GeminiService, "enrich_section", AsyncMock(return_value=mock_result)):
        client.post("/api/ai/enrich", json={
            "topic_id": "general_1", "section_idx": 2,
            "section_markdown": "La LPACAP regula..."
        })
    # Second call should return cached result without calling Gemini
    with patch.object(g.GeminiService, "enrich_section", AsyncMock(return_value={})) as mock_ai:
        resp = client.post("/api/ai/enrich", json={
            "topic_id": "general_1", "section_idx": 2,
            "section_markdown": "La LPACAP regula..."
        })
        mock_ai.assert_not_called()
    assert resp.status_code == 200
    assert resp.json()["type"] == "callouts"


def test_get_enrichments_empty(client):
    resp = client.get("/api/ai/enrichments/general_1")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_enrichments_after_save(client):
    import services.gemini as g
    mock_result = {"type": "cards", "data": [{"title": "Ple", "desc": "Òrgan", "icon": "building"}]}
    with patch.object(g.GeminiService, "enrich_section", AsyncMock(return_value=mock_result)):
        client.post("/api/ai/enrich", json={
            "topic_id": "general_2", "section_idx": 1,
            "section_markdown": "El Ple Municipal..."
        })
    resp = client.get("/api/ai/enrichments/general_2")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["section_idx"] == 1
    assert rows[0]["type"] == "cards"


def test_generate_summary(client):
    import services.gemini as g
    mock_result = {
        "summary": "El procediment administratiu té 3 fases.",
        "chips": [{"label": "3 fases", "category": "concept"}, {"label": "LPACAP", "category": "law"}]
    }
    with patch.object(g.GeminiService, "generate_topic_summary", AsyncMock(return_value=mock_result)):
        resp = client.post("/api/ai/topic-summary", json={
            "topic_id": "general_1",
            "topic_content": "## Fases\nIniciació, Instrucció, Terminació..."
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert len(data["chips"]) == 2


def test_get_summary_not_found(client):
    resp = client.get("/api/ai/summary/general_99")
    assert resp.status_code == 404


def test_get_summary_after_generate(client):
    import services.gemini as g
    mock_result = {
        "summary": "Tema sobre seguretat.",
        "chips": [{"label": "Confidencialitat", "category": "concept"}]
    }
    with patch.object(g.GeminiService, "generate_topic_summary", AsyncMock(return_value=mock_result)):
        client.post("/api/ai/topic-summary", json={
            "topic_id": "general_5", "topic_content": "Seguretat..."
        })
    resp = client.get("/api/ai/summary/general_5")
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Tema sobre seguretat."
