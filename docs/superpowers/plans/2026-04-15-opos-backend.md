# OPOS Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI backend that parses ApuntsTemari.md, stores all study data in SQLite, and proxies Gemini AI calls for the OPOS C1 study app.

**Architecture:** Single FastAPI app with modular routers (one per domain), async SQLite via aiosqlite, Gemini service wrapper, and a Dockerfile for Docker Compose deployment. Data (SQLite, notes file, PDF) lives in a mounted `/data` volume.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, aiosqlite, google-generativeai, PyMuPDF, python-dotenv, pytest, pytest-asyncio, httpx, Docker

---

## File Structure

```
backend/                           ← working directory for this plan
├── Dockerfile                     # python:3.11-slim, runs uvicorn on :8000
├── main.py                        # App factory, CORS, startup
├── database.py                    # DB init, get_db dependency
├── models.py                      # Pydantic request/response schemas
├── requirements.txt
├── .env.example                   # Template — real .env lives at project root
├── routers/
│   ├── __init__.py
│   ├── topics.py                  # GET /topics, GET /topics/{id}/content
│   ├── annotations.py             # GET/POST /topics/{id}/annotations
│   ├── drawings.py                # GET/POST /topics/{id}/drawings
│   ├── flashcards.py              # Flashcards CRUD + generate + review
│   ├── practice.py                # All 5 practice modes + sessions
│   ├── progress.py                # Global progress + exam readiness
│   ├── pdf.py                     # POST /pdf/analyze
│   └── config.py                  # GET/POST /config
├── services/
│   ├── __init__.py
│   ├── markdown_parser.py         # Parse ApuntsTemari.md → 20 topic dicts
│   ├── gemini.py                  # Gemini API wrapper (all prompts)
│   └── pdf_analyzer.py            # PyMuPDF + gap analysis via Gemini
└── tests/
    ├── conftest.py                # TestClient + in-memory DB fixture
    ├── test_markdown_parser.py
    ├── test_topics.py
    ├── test_annotations.py
    ├── test_flashcards.py
    ├── test_practice.py
    └── test_progress.py
```

**Project root layout (for context — docker-compose.yml lives here):**
```
OPOS/
├── docker-compose.yml
├── .env                    ← GEMINI_API_KEY=... (never committed)
├── data/                   ← volume: opos.db + ApuntsTemari.md + PDF
├── backend/                ← this plan's working directory
└── frontend/               ← separate plan
```

---

## Task 1: Project Setup + Database Schema

**Files:**
- Create: `/opt/opos-api/requirements.txt`
- Create: `/opt/opos-api/.env.example`
- Create: `/opt/opos-api/database.py`
- Create: `/opt/opos-api/tests/conftest.py`
- Test: `/opt/opos-api/tests/test_db.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.30.0
aiosqlite==0.20.0
google-generativeai==0.7.2
pymupdf==1.24.5
python-dotenv==1.0.1
pydantic==2.7.1
httpx==0.27.0
pytest==8.2.1
pytest-asyncio==0.23.7
```

- [ ] **Step 2: Create .env.example**

```
GEMINI_API_KEY=your_key_here
DB_PATH=/opt/opos-api/opos.db
NOTES_PATH=/opt/opos-api/ApuntsTemari.md
PDF_PATH=/opt/opos-api/EdicteC1Maçanet.pdf
```

- [ ] **Step 3: Write the failing DB test**

Create `/opt/opos-api/tests/test_db.py`:
```python
import pytest
import asyncio
import aiosqlite
from database import init_db, DB_PATH

@pytest.mark.asyncio
async def test_init_db_creates_all_tables(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    # Re-import after env change
    import importlib
    import database
    importlib.reload(database)
    await database.init_db()
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in await cursor.fetchall()}
    expected = {"progress", "annotations", "drawings", "flashcards",
                "practice_sessions", "pdf_analysis", "config"}
    assert expected.issubset(tables)
```

- [ ] **Step 4: Run test — expect failure (ImportError)**

```bash
cd /opt/opos-api && python -m pytest tests/test_db.py -v
```
Expected: `ModuleNotFoundError: No module named 'database'`

- [ ] **Step 5: Create database.py**

```python
import aiosqlite
import os
from contextlib import asynccontextmanager

DB_PATH = os.getenv("DB_PATH", "/opt/opos-api/opos.db")

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
        yield db
```

- [ ] **Step 6: Create tests/conftest.py**

```python
import pytest
import pytest_asyncio
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
    asyncio.get_event_loop().run_until_complete(database.init_db())
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 7: Run test — expect pass**

```bash
cd /opt/opos-api && python -m pytest tests/test_db.py -v
```
Expected: `PASSED tests/test_db.py::test_init_db_creates_all_tables`

- [ ] **Step 8: Commit**

```bash
cd /opt/opos-api
git init && git add requirements.txt .env.example database.py tests/conftest.py tests/test_db.py
git commit -m "feat: project setup + SQLite schema with all 7 tables"
```

---

## Task 2: Markdown Parser Service

**Files:**
- Create: `/opt/opos-api/services/__init__.py` (empty)
- Create: `/opt/opos-api/routers/__init__.py` (empty)
- Create: `/opt/opos-api/services/markdown_parser.py`
- Test: `/opt/opos-api/tests/test_markdown_parser.py`

- [ ] **Step 1: Write the failing test**

Create `/opt/opos-api/tests/test_markdown_parser.py`:
```python
from pathlib import Path
from services.markdown_parser import parse_topics, extract_headings

NOTES_FILE = Path("/opt/opos-api/ApuntsTemari.md")

def test_parse_produces_20_topics():
    topics = parse_topics(NOTES_FILE)
    assert len(topics) == 20

def test_general_bloc_has_5_topics():
    topics = parse_topics(NOTES_FILE)
    general = [t for t in topics if t["bloc"] == "general"]
    assert len(general) == 5

def test_especific_bloc_has_15_topics():
    topics = parse_topics(NOTES_FILE)
    especific = [t for t in topics if t["bloc"] == "especific"]
    assert len(especific) == 15

def test_topic_has_required_fields():
    topic = parse_topics(NOTES_FILE)[0]
    assert all(k in topic for k in ("id", "bloc", "number", "title", "content", "headings"))

def test_topic_ids_are_unique():
    topics = parse_topics(NOTES_FILE)
    ids = [t["id"] for t in topics]
    assert len(ids) == len(set(ids))

def test_topic_content_is_not_empty():
    topics = parse_topics(NOTES_FILE)
    for t in topics:
        assert len(t["content"]) > 100, f"Topic {t['id']} has too little content"

def test_extract_headings_returns_level_and_text():
    content = "#### 1. Introducció\n\nText\n\n##### A. Sub\n"
    headings = extract_headings(content)
    assert headings[0]["level"] == 4
    assert headings[0]["text"] == "1. Introducció"
```

- [ ] **Step 2: Run test — expect failure**

```bash
cd /opt/opos-api && python -m pytest tests/test_markdown_parser.py -v
```
Expected: `ModuleNotFoundError: No module named 'services.markdown_parser'`

- [ ] **Step 3: Create services/markdown_parser.py**

```python
import re
from pathlib import Path

def parse_topics(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    topics = []
    current_bloc = None
    current_topic = None
    current_lines: list[str] = []
    counters = {"general": 0, "especific": 0}

    for line in lines:
        if re.match(r"^## Bloc General", line):
            current_bloc = "general"
        elif re.match(r"^## Bloc Específic", line):
            current_bloc = "especific"
        elif re.match(r"^### Tema \d+", line) and current_bloc:
            if current_topic is not None:
                _finalise(current_topic, current_lines)
                topics.append(current_topic)
            counters[current_bloc] += 1
            n = counters[current_bloc]
            title = re.sub(r"^### Tema \d+:\s*", "", line).strip()
            current_topic = {
                "id": f"{current_bloc}_{n}",
                "bloc": current_bloc,
                "number": n,
                "title": title,
            }
            current_lines = []
        elif current_topic is not None:
            current_lines.append(line)

    if current_topic is not None:
        _finalise(current_topic, current_lines)
        topics.append(current_topic)

    return topics

def _finalise(topic: dict, lines: list[str]):
    content = "\n".join(lines).strip()
    topic["content"] = content
    topic["headings"] = extract_headings(content)

def extract_headings(content: str) -> list[dict]:
    headings = []
    for line in content.splitlines():
        m = re.match(r"^(#{2,6})\s+(.+)", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            anchor = re.sub(r"[^\w\s-]", "", text.lower()).strip()
            anchor = re.sub(r"\s+", "-", anchor)
            headings.append({"level": level, "text": text, "anchor": anchor})
    return headings

# Module-level cache so we only parse once per process
_cache: list[dict] | None = None

def get_topics(path: Path) -> list[dict]:
    global _cache
    if _cache is None:
        _cache = parse_topics(path)
    return _cache

def get_topic_by_id(topic_id: str, path: Path) -> dict | None:
    return next((t for t in get_topics(path) if t["id"] == topic_id), None)
```

- [ ] **Step 4: Run test — expect pass**

```bash
cd /opt/opos-api && python -m pytest tests/test_markdown_parser.py -v
```
Expected: 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add services/__init__.py routers/__init__.py services/markdown_parser.py tests/test_markdown_parser.py
git commit -m "feat: markdown parser — splits ApuntsTemari.md into 20 typed topics"
```

---

## Task 3: Topics Router + Main App Skeleton

**Files:**
- Create: `/opt/opos-api/models.py`
- Create: `/opt/opos-api/routers/topics.py`
- Create: `/opt/opos-api/main.py`
- Test: `/opt/opos-api/tests/test_topics.py`

- [ ] **Step 1: Write the failing tests**

Create `/opt/opos-api/tests/test_topics.py`:
```python
def test_get_topics_returns_20(client):
    resp = client.get("/api/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 20

def test_topic_has_progress_field(client):
    resp = client.get("/api/topics")
    topic = resp.json()[0]
    assert "overall_pct" in topic
    assert "id" in topic
    assert "title" in topic
    assert "bloc" in topic

def test_get_topic_content_returns_markdown(client):
    resp = client.get("/api/topics/general_1/content")
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert "headings" in data
    assert len(data["content"]) > 0

def test_get_topic_content_unknown_id_returns_404(client):
    resp = client.get("/api/topics/unknown_99/content")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests — expect failure**

```bash
python -m pytest tests/test_topics.py -v
```
Expected: `ModuleNotFoundError: No module named 'main'` (conftest can't build client)

- [ ] **Step 3: Create models.py**

```python
from pydantic import BaseModel
from typing import Optional

class TopicSummary(BaseModel):
    id: str
    bloc: str
    number: int
    title: str
    overall_pct: float = 0.0

class TopicContent(BaseModel):
    id: str
    title: str
    content: str
    headings: list[dict]

class AnnotationCreate(BaseModel):
    selected_text: str
    color: str = "yellow"
    note: Optional[str] = None
    position_hash: Optional[str] = None

class DrawingUpdate(BaseModel):
    canvas_json: str

class FlashcardCreate(BaseModel):
    pregunta: str
    resposta: str
    exemple: Optional[str] = None

class FlashcardReview(BaseModel):
    knew_it: bool  # True → promote box, False → reset to box 1

class PracticeEvaluate(BaseModel):
    topic_id: str
    mode: str
    pregunta: str
    resposta_usuari: str
    resposta_model: Optional[str] = None

class SessionSave(BaseModel):
    topic_id: str
    mode: str
    questions_json: Optional[str] = None
    answers_json: Optional[str] = None
    score: float
    feedback_json: Optional[str] = None

class ConfigSet(BaseModel):
    key: str
    value: str
```

- [ ] **Step 4: Create routers/topics.py**

```python
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from models import TopicSummary, TopicContent
from services.markdown_parser import get_topics, get_topic_by_id
import aiosqlite
from database import get_db

router = APIRouter(prefix="/api/topics", tags=["topics"])

NOTES_PATH = Path(os.getenv("NOTES_PATH", "/opt/opos-api/ApuntsTemari.md"))

@router.get("", response_model=list[TopicSummary])
async def list_topics(db=Depends(get_db)):
    topics = get_topics(NOTES_PATH)
    # Fetch progress for all topics
    cursor = await db.execute("SELECT topic_id, overall_pct FROM progress")
    progress_map = {row["topic_id"]: row["overall_pct"] for row in await cursor.fetchall()}

    return [
        TopicSummary(
            id=t["id"],
            bloc=t["bloc"],
            number=t["number"],
            title=t["title"],
            overall_pct=progress_map.get(t["id"], 0.0),
        )
        for t in topics
    ]

@router.get("/{topic_id}/content", response_model=TopicContent)
async def get_content(topic_id: str):
    topic = get_topic_by_id(topic_id, NOTES_PATH)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found")
    return TopicContent(
        id=topic["id"],
        title=topic["title"],
        content=topic["content"],
        headings=topic["headings"],
    )
```

- [ ] **Step 5: Create main.py**

```python
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import topics, annotations, drawings, flashcards, practice, progress, pdf, config as config_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="OPOS C1 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Nginx restricts in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(topics.router)
app.include_router(annotations.router)
app.include_router(drawings.router)
app.include_router(flashcards.router)
app.include_router(practice.router)
app.include_router(progress.router)
app.include_router(pdf.router)
app.include_router(config_router.router)
```

Note: main.py imports all routers. Create empty stub files for the others so the import doesn't fail:
```bash
touch routers/annotations.py routers/drawings.py routers/flashcards.py \
      routers/practice.py routers/progress.py routers/pdf.py routers/config.py
```

In each empty stub file, add the minimum:
```python
# routers/annotations.py (and others — same pattern)
from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 6: Run tests — expect pass**

```bash
python -m pytest tests/test_topics.py -v
```
Expected: 4 tests pass.

- [ ] **Step 7: Commit**

```bash
git add models.py routers/topics.py main.py routers/annotations.py routers/drawings.py \
        routers/flashcards.py routers/practice.py routers/progress.py \
        routers/pdf.py routers/config.py tests/test_topics.py
git commit -m "feat: topics router + main app skeleton with stub routers"
```

---

## Task 4: Annotations + Drawings Routers

**Files:**
- Modify: `/opt/opos-api/routers/annotations.py`
- Modify: `/opt/opos-api/routers/drawings.py`
- Test: `/opt/opos-api/tests/test_annotations.py`

- [ ] **Step 1: Write the failing tests**

Create `/opt/opos-api/tests/test_annotations.py`:
```python
def test_get_annotations_empty(client):
    resp = client.get("/api/topics/general_1/annotations")
    assert resp.status_code == 200
    assert resp.json() == []

def test_post_annotation_persists(client):
    payload = {"selected_text": "L'Alcaldessa", "color": "yellow", "note": "Important"}
    resp = client.post("/api/topics/general_1/annotations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] > 0
    assert data["selected_text"] == "L'Alcaldessa"

def test_get_annotations_returns_saved(client):
    payload = {"selected_text": "Ple de l'Ajuntament", "color": "blue"}
    client.post("/api/topics/general_1/annotations", json=payload)
    resp = client.get("/api/topics/general_1/annotations")
    assert len(resp.json()) == 1
    assert resp.json()[0]["selected_text"] == "Ple de l'Ajuntament"

def test_delete_annotation(client):
    r = client.post("/api/topics/general_1/annotations",
                    json={"selected_text": "test", "color": "green"})
    ann_id = r.json()["id"]
    resp = client.delete(f"/api/annotations/{ann_id}")
    assert resp.status_code == 204
    assert client.get("/api/topics/general_1/annotations").json() == []

def test_get_drawing_empty(client):
    resp = client.get("/api/topics/general_1/drawings")
    assert resp.status_code == 200
    assert resp.json()["canvas_json"] == "{}"

def test_post_drawing_persists(client):
    payload = {"canvas_json": '{"objects":[{"type":"path"}]}'}
    resp = client.post("/api/topics/general_1/drawings", json=payload)
    assert resp.status_code == 200
    assert client.get("/api/topics/general_1/drawings").json()["canvas_json"] == payload["canvas_json"]
```

- [ ] **Step 2: Run tests — expect failure**

```bash
python -m pytest tests/test_annotations.py -v
```
Expected: all fail with 404 (stub routers have no routes).

- [ ] **Step 3: Implement routers/annotations.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from models import AnnotationCreate
from database import get_db

router = APIRouter(tags=["annotations"])

@router.get("/api/topics/{topic_id}/annotations")
async def get_annotations(topic_id: str, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT * FROM annotations WHERE topic_id=? ORDER BY created_at",
        (topic_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]

@router.post("/api/topics/{topic_id}/annotations", status_code=201)
async def create_annotation(topic_id: str, body: AnnotationCreate, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO annotations (topic_id, selected_text, color, note, position_hash) "
        "VALUES (?,?,?,?,?)",
        (topic_id, body.selected_text, body.color, body.note, body.position_hash)
    )
    await db.commit()
    row = await (await db.execute(
        "SELECT * FROM annotations WHERE id=?", (cursor.lastrowid,)
    )).fetchone()
    return dict(row)

@router.delete("/api/annotations/{ann_id}", status_code=204)
async def delete_annotation(ann_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM annotations WHERE id=?", (ann_id,))
    await db.commit()
```

- [ ] **Step 4: Implement routers/drawings.py**

```python
from fastapi import APIRouter, Depends
from models import DrawingUpdate
from database import get_db

router = APIRouter(tags=["drawings"])

@router.get("/api/topics/{topic_id}/drawings")
async def get_drawing(topic_id: str, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT canvas_json FROM drawings WHERE topic_id=?", (topic_id,)
    )
    row = await cursor.fetchone()
    return {"canvas_json": row["canvas_json"] if row else "{}"}

@router.post("/api/topics/{topic_id}/drawings")
async def save_drawing(topic_id: str, body: DrawingUpdate, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO drawings (topic_id, canvas_json) VALUES (?,?) "
        "ON CONFLICT(topic_id) DO UPDATE SET canvas_json=excluded.canvas_json, "
        "updated_at=datetime('now')",
        (topic_id, body.canvas_json)
    )
    await db.commit()
    return {"topic_id": topic_id, "canvas_json": body.canvas_json}
```

- [ ] **Step 5: Run tests — expect pass**

```bash
python -m pytest tests/test_annotations.py -v
```
Expected: 6 tests pass.

- [ ] **Step 6: Commit**

```bash
git add routers/annotations.py routers/drawings.py tests/test_annotations.py
git commit -m "feat: annotations (CRUD + delete) and drawings (get/save) routers"
```

---

## Task 5: Gemini Service

**Files:**
- Create: `/opt/opos-api/services/gemini.py`
- Test: `/opt/opos-api/tests/test_gemini.py` (mock-only, no real API calls)

- [ ] **Step 1: Write the failing tests**

Create `/opt/opos-api/tests/test_gemini.py`:
```python
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.fixture
def gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from services import gemini as g
    return g.GeminiService()

@pytest.mark.asyncio
async def test_generate_json_strips_markdown_fences(gemini):
    mock_response = MagicMock()
    mock_response.text = '```json\n[{"a": 1}]\n```'
    with patch.object(gemini.model, "generate_content_async",
                      AsyncMock(return_value=mock_response)):
        result = await gemini._generate_json("test prompt")
    assert result == [{"a": 1}]

@pytest.mark.asyncio
async def test_generate_flashcards_returns_15(gemini):
    cards = [{"terme": f"t{i}", "definicio": f"d{i}", "exemple": ""} for i in range(15)]
    mock_response = MagicMock()
    mock_response.text = json.dumps(cards)
    with patch.object(gemini.model, "generate_content_async",
                      AsyncMock(return_value=mock_response)):
        result = await gemini.generate_flashcards("content", "Tema 1")
    assert len(result) == 15
    assert all("terme" in c for c in result)

@pytest.mark.asyncio
async def test_generate_test_returns_10_questions(gemini):
    questions = [
        {"pregunta": f"Q{i}", "opcions": {"A": "", "B": "", "C": "", "D": ""},
         "correcta": "A", "explicacio": ""}
        for i in range(10)
    ]
    mock_response = MagicMock()
    mock_response.text = json.dumps(questions)
    with patch.object(gemini.model, "generate_content_async",
                      AsyncMock(return_value=mock_response)):
        result = await gemini.generate_test("content")
    assert len(result) == 10

@pytest.mark.asyncio
async def test_evaluate_answer_returns_score(gemini):
    evaluation = {
        "puntuacio": 7,
        "encerts": ["bon punt"],
        "mancances": [],
        "feedback": "Molt bé",
        "puntuacio_justificada": "Resposta completa"
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(evaluation)
    with patch.object(gemini.model, "generate_content_async",
                      AsyncMock(return_value=mock_response)):
        result = await gemini.evaluate_answer("pregunta", "resposta", "model")
    assert result["puntuacio"] == 7
```

- [ ] **Step 2: Run tests — expect failure**

```bash
python -m pytest tests/test_gemini.py -v
```
Expected: `ModuleNotFoundError: No module named 'services.gemini'`

- [ ] **Step 3: Create services/gemini.py**

```python
import os
import re
import json
import google.generativeai as genai

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    async def _generate_json(self, prompt: str) -> dict | list:
        response = await self.model.generate_content_async(prompt)
        text = response.text.strip()
        text = re.sub(r"^```\w*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    async def generate_flashcards(self, topic_text: str, topic_name: str) -> list[dict]:
        prompt = (
            "Ets un professor d'oposicions públiques. Genera exactament 15 flashcards.\n"
            "Retorna ÚNICAMENT JSON (array de 15 objectes, sense cap text addicional):\n"
            '[{"terme": "...", "definicio": "...", "exemple": "..."}]\n'
            f"TEMA: {topic_name}\n"
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_test(self, topic_text: str) -> list[dict]:
        prompt = (
            "Genera 10 preguntes tipus test per a un examen de tècnic C1 d'informàtica.\n"
            "Retorna ÚNICAMENT JSON (array de 10 objectes, sense text addicional):\n"
            '[{"pregunta": "...", "opcions": {"A":"...","B":"...","C":"...","D":"..."}, '
            '"correcta": "A", "explicacio": "..."}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_breus(self, topic_text: str) -> list[dict]:
        prompt = (
            "Genera 5 preguntes breus (resposta en 2-4 línies) per a examen C1 informàtica.\n"
            "Retorna ÚNICAMENT JSON:\n"
            '[{"pregunta": "...", "resposta_model": "...", "criteris": "..."}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_suposit(self, topic_text: str, topic_name: str) -> dict:
        prompt = (
            "Genera un supòsit pràctic realista per a un tècnic C1 d'informàtica "
            "en un ajuntament petit. Ha de requerir aplicació raonada, no memorització.\n"
            "Retorna ÚNICAMENT JSON:\n"
            '{"enunciat": "...", "context": "...", "punts_clau_resposta": ["..."], '
            '"criteri_correccio": "...", "dificultat": "mitja"}\n'
            f"TEMA: {topic_name}\n"
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_connecta(self, topic_text: str) -> list[dict]:
        prompt = (
            "Genera 10 parells terme-definició per a una activitat de relacionar conceptes.\n"
            "Retorna ÚNICAMENT JSON:\n"
            '[{"terme": "...", "definicio": "..."}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_buits(self, topic_text: str) -> list[dict]:
        prompt = (
            "Genera 8 frases clau del contingut amb 1-2 paraules importants substituïdes "
            "per ___. Retorna ÚNICAMENT JSON:\n"
            '[{"frase": "El ___ és responsable de...", "paraules": ["Alcalde"], '
            '"posicions": [1]}]\n'
            f"CONTINGUT:\n{topic_text[:2000]}"
        )
        return await self._generate_json(prompt)

    async def evaluate_answer(self, pregunta: str, resposta_usuari: str,
                               resposta_model: str) -> dict:
        prompt = (
            "Avalua la resposta de l'usuari per a un examen de tècnic C1 informàtica.\n"
            "Puntua de 0 a 10. Retorna ÚNICAMENT JSON:\n"
            '{"puntuacio": 7, "encerts": ["..."], "mancances": ["..."], '
            '"feedback": "...", "puntuacio_justificada": "..."}\n'
            f"PREGUNTA: {pregunta}\n"
            f"RESPOSTA USUARI: {resposta_usuari}\n"
            f"RESPOSTA MODEL: {resposta_model}"
        )
        return await self._generate_json(prompt)

    async def exam_readiness(self, progress_json: str, gaps_json: str,
                              exam_date: str, today: str, dies: int) -> dict:
        prompt = (
            f"L'examen és el {exam_date}. Avui és {today}. Resten {dies} dies.\n"
            "Fes una valoració realista. Retorna ÚNICAMENT JSON:\n"
            '{"readiness_pct": 65, "nota_estimada": 6.5, "temes_prioritaris": ["Tema X"], '
            '"consell_estudi": "...", "temps_recomanat_per_tema": {"tema_id": 30}}\n'
            f"PROGRÉS PER TEMA: {progress_json}\n"
            f"GAPS DEL TEMARI: {gaps_json}"
        )
        return await self._generate_json(prompt)

# Singleton
_gemini: GeminiService | None = None

def get_gemini() -> GeminiService:
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini
```

- [ ] **Step 4: Run tests — expect pass**

```bash
python -m pytest tests/test_gemini.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add services/gemini.py tests/test_gemini.py
git commit -m "feat: Gemini service wrapper with all prompts (flashcards, test, breus, supòsit, connecta, buits, evaluate, readiness)"
```

---

## Task 6: Flashcards Router

**Files:**
- Modify: `/opt/opos-api/routers/flashcards.py`
- Test: `/opt/opos-api/tests/test_flashcards.py`

- [ ] **Step 1: Write the failing tests**

Create `/opt/opos-api/tests/test_flashcards.py`:
```python
import json
from unittest.mock import AsyncMock, patch

SAMPLE_CARDS = [{"terme": f"t{i}", "definicio": f"d{i}", "exemple": ""} for i in range(15)]

def test_get_flashcards_empty(client):
    resp = client.get("/api/topics/general_1/flashcards")
    assert resp.status_code == 200
    assert resp.json() == []

def test_create_flashcard_manual(client):
    payload = {"pregunta": "Que és el Ple?", "resposta": "Òrgan de govern", "exemple": "Aprova pressupostos"}
    resp = client.post("/api/topics/general_1/flashcards", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["origin"] == "manual"
    assert data["leitner_box"] == 1

def test_generate_flashcards_calls_gemini(client):
    import services.gemini as g
    mock_cards = [{"terme": f"t{i}", "definicio": f"d{i}", "exemple": ""} for i in range(15)]
    with patch.object(g.GeminiService, "generate_flashcards",
                      AsyncMock(return_value=mock_cards)):
        resp = client.post("/api/topics/general_1/flashcards/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 15

def test_review_card_promote(client):
    r = client.post("/api/topics/general_1/flashcards",
                    json={"pregunta": "Q", "resposta": "A"})
    card_id = r.json()["id"]
    resp = client.post(f"/api/flashcards/{card_id}/review", json={"knew_it": True})
    assert resp.status_code == 200
    assert resp.json()["leitner_box"] == 2

def test_review_card_demote(client):
    r = client.post("/api/topics/general_1/flashcards",
                    json={"pregunta": "Q", "resposta": "A"})
    card_id = r.json()["id"]
    # First promote to box 3
    client.post(f"/api/flashcards/{card_id}/review", json={"knew_it": True})
    client.post(f"/api/flashcards/{card_id}/review", json={"knew_it": True})
    # Now demote
    resp = client.post(f"/api/flashcards/{card_id}/review", json={"knew_it": False})
    assert resp.json()["leitner_box"] == 1
```

- [ ] **Step 2: Run tests — expect failure**

```bash
python -m pytest tests/test_flashcards.py -v
```
Expected: all fail (stub router has no routes).

- [ ] **Step 3: Implement routers/flashcards.py**

```python
import os
import json
from pathlib import Path
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from models import FlashcardCreate, FlashcardReview
from database import get_db
from services.gemini import get_gemini
from services.markdown_parser import get_topic_by_id

router = APIRouter(tags=["flashcards"])

NOTES_PATH = Path(os.getenv("NOTES_PATH", "/opt/opos-api/ApuntsTemari.md"))

# Leitner next-review intervals in days per box
LEITNER_DAYS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}

@router.get("/api/topics/{topic_id}/flashcards")
async def list_flashcards(topic_id: str, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT * FROM flashcards WHERE topic_id=? ORDER BY leitner_box, next_review",
        (topic_id,)
    )
    return [dict(r) for r in await cursor.fetchall()]

@router.post("/api/topics/{topic_id}/flashcards", status_code=201)
async def create_flashcard(topic_id: str, body: FlashcardCreate, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO flashcards (topic_id, pregunta, resposta, exemple, origin) "
        "VALUES (?,?,?,?,?)",
        (topic_id, body.pregunta, body.resposta, body.exemple, "manual")
    )
    await db.commit()
    row = await (await db.execute(
        "SELECT * FROM flashcards WHERE id=?", (cursor.lastrowid,)
    )).fetchone()
    return dict(row)

@router.post("/api/topics/{topic_id}/flashcards/generate")
async def generate_flashcards(topic_id: str, db=Depends(get_db)):
    topic = get_topic_by_id(topic_id, NOTES_PATH)
    if not topic:
        raise HTTPException(404, detail="Topic not found")
    gemini = get_gemini()
    cards = await gemini.generate_flashcards(topic["content"], topic["title"])
    inserted = []
    for c in cards:
        cursor = await db.execute(
            "INSERT INTO flashcards (topic_id, pregunta, resposta, exemple, origin) "
            "VALUES (?,?,?,?,?)",
            (topic_id, c.get("terme", ""), c.get("definicio", ""),
             c.get("exemple", ""), "auto")
        )
        inserted.append(cursor.lastrowid)
    await db.commit()
    cursor = await db.execute(
        f"SELECT * FROM flashcards WHERE id IN ({','.join('?'*len(inserted))})",
        inserted
    )
    return [dict(r) for r in await cursor.fetchall()]

@router.post("/api/flashcards/{card_id}/review")
async def review_flashcard(card_id: int, body: FlashcardReview, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM flashcards WHERE id=?", (card_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(404, detail="Flashcard not found")
    current_box = row["leitner_box"]
    new_box = min(current_box + 1, 5) if body.knew_it else 1
    days = LEITNER_DAYS[new_box]
    next_review = (date.today() + timedelta(days=days)).isoformat()
    await db.execute(
        "UPDATE flashcards SET leitner_box=?, next_review=? WHERE id=?",
        (new_box, next_review, card_id)
    )
    await db.commit()
    row = await (await db.execute("SELECT * FROM flashcards WHERE id=?", (card_id,))).fetchone()
    return dict(row)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
python -m pytest tests/test_flashcards.py -v
```
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add routers/flashcards.py tests/test_flashcards.py
git commit -m "feat: flashcards router with CRUD, Gemini generation, and Leitner spaced repetition"
```

---

## Task 7: Practice Router

**Files:**
- Modify: `/opt/opos-api/routers/practice.py`
- Test: `/opt/opos-api/tests/test_practice.py`

- [ ] **Step 1: Write the failing tests**

Create `/opt/opos-api/tests/test_practice.py`:
```python
import json
from unittest.mock import AsyncMock, patch
import services.gemini as g

MOCK_TEST_QUESTIONS = [
    {"pregunta": f"Q{i}", "opcions": {"A":"a","B":"b","C":"c","D":"d"},
     "correcta": "A", "explicacio": "x"}
    for i in range(10)
]
MOCK_BREUS = [
    {"pregunta": f"Q{i}", "resposta_model": "resp", "criteris": "crit"}
    for i in range(5)
]
MOCK_SUPOSIT = {
    "enunciat": "Un usuari no pot imprimir",
    "context": "Oficina municipal",
    "punts_clau_resposta": ["Verificar cua d'impressió"],
    "criteri_correccio": "Resolució sistemàtica",
    "dificultat": "mitja"
}
MOCK_CONNECTA = [{"terme": f"T{i}", "definicio": f"D{i}"} for i in range(10)]
MOCK_BUITS = [{"frase": "El ___ és important", "paraules": ["Ple"], "posicions": [1]}
              for _ in range(8)]

def test_generate_test(client):
    with patch.object(g.GeminiService, "generate_test", AsyncMock(return_value=MOCK_TEST_QUESTIONS)):
        resp = client.post("/api/topics/general_1/practice/test/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 10

def test_generate_breus(client):
    with patch.object(g.GeminiService, "generate_breus", AsyncMock(return_value=MOCK_BREUS)):
        resp = client.post("/api/topics/general_1/practice/breus/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 5

def test_generate_suposit(client):
    with patch.object(g.GeminiService, "generate_suposit", AsyncMock(return_value=MOCK_SUPOSIT)):
        resp = client.post("/api/topics/general_1/practice/suposit/generate")
    assert resp.status_code == 200
    assert "enunciat" in resp.json()

def test_generate_connecta(client):
    with patch.object(g.GeminiService, "generate_connecta", AsyncMock(return_value=MOCK_CONNECTA)):
        resp = client.post("/api/topics/general_1/practice/connecta/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 10

def test_generate_buits(client):
    with patch.object(g.GeminiService, "generate_buits", AsyncMock(return_value=MOCK_BUITS)):
        resp = client.post("/api/topics/general_1/practice/buits/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 8

def test_evaluate_answer(client):
    mock_eval = {"puntuacio": 8, "encerts": [], "mancances": [], "feedback": "Bé", "puntuacio_justificada": ""}
    with patch.object(g.GeminiService, "evaluate_answer", AsyncMock(return_value=mock_eval)):
        resp = client.post("/api/practice/evaluate", json={
            "topic_id": "general_1",
            "mode": "breus",
            "pregunta": "Que és el Ple?",
            "resposta_usuari": "És l'òrgan...",
            "resposta_model": "El Ple és..."
        })
    assert resp.status_code == 200
    assert resp.json()["puntuacio"] == 8

def test_save_session_updates_progress(client):
    resp = client.post("/api/practice/sessions", json={
        "topic_id": "general_1",
        "mode": "test",
        "score": 8.5,
        "questions_json": "[]",
        "answers_json": "[]",
        "feedback_json": "{}"
    })
    assert resp.status_code == 201
    # Progress should be initialized
    prog = client.get("/api/progress")
    topic_prog = next((t for t in prog.json()["topics"] if t["topic_id"] == "general_1"), None)
    assert topic_prog is not None
    assert topic_prog["score_test"] == 8.5
```

- [ ] **Step 2: Run tests — expect failure**

```bash
python -m pytest tests/test_practice.py -v
```
Expected: all fail (stub router has no routes).

- [ ] **Step 3: Implement routers/practice.py**

```python
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from models import PracticeEvaluate, SessionSave
from database import get_db
from services.gemini import get_gemini
from services.markdown_parser import get_topic_by_id

router = APIRouter(tags=["practice"])

NOTES_PATH = Path(os.getenv("NOTES_PATH", "/opt/opos-api/ApuntsTemari.md"))

def _get_topic_or_404(topic_id: str):
    topic = get_topic_by_id(topic_id, NOTES_PATH)
    if not topic:
        raise HTTPException(404, detail="Topic not found")
    return topic

@router.post("/api/topics/{topic_id}/practice/test/generate")
async def gen_test(topic_id: str):
    topic = _get_topic_or_404(topic_id)
    return await get_gemini().generate_test(topic["content"])

@router.post("/api/topics/{topic_id}/practice/breus/generate")
async def gen_breus(topic_id: str):
    topic = _get_topic_or_404(topic_id)
    return await get_gemini().generate_breus(topic["content"])

@router.post("/api/topics/{topic_id}/practice/suposit/generate")
async def gen_suposit(topic_id: str):
    topic = _get_topic_or_404(topic_id)
    return await get_gemini().generate_suposit(topic["content"], topic["title"])

@router.post("/api/topics/{topic_id}/practice/connecta/generate")
async def gen_connecta(topic_id: str):
    topic = _get_topic_or_404(topic_id)
    return await get_gemini().generate_connecta(topic["content"])

@router.post("/api/topics/{topic_id}/practice/buits/generate")
async def gen_buits(topic_id: str):
    topic = _get_topic_or_404(topic_id)
    return await get_gemini().generate_buits(topic["content"])

@router.post("/api/practice/evaluate")
async def evaluate(body: PracticeEvaluate):
    return await get_gemini().evaluate_answer(
        body.pregunta, body.resposta_usuari, body.resposta_model or ""
    )

@router.post("/api/practice/sessions", status_code=201)
async def save_session(body: SessionSave, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO practice_sessions (topic_id, mode, questions_json, answers_json, score, feedback_json) "
        "VALUES (?,?,?,?,?,?)",
        (body.topic_id, body.mode, body.questions_json, body.answers_json,
         body.score, body.feedback_json)
    )
    # Upsert progress
    score_col = f"score_{body.mode}" if body.mode in ("test","breus","suposit","connecta","buits") else "score_test"
    # Fetch current topic bloc
    from services.markdown_parser import get_topic_by_id as _get
    topic = _get(body.topic_id, NOTES_PATH)
    bloc = topic["bloc"] if topic else "general"
    await db.execute(
        f"INSERT INTO progress (topic_id, bloc, {score_col}, tests_done, last_activity) "
        f"VALUES (?,?,?,1,datetime('now')) "
        f"ON CONFLICT(topic_id) DO UPDATE SET {score_col}=excluded.{score_col}, "
        f"tests_done=tests_done+1, last_activity=datetime('now')",
        (body.topic_id, bloc, body.score)
    )
    # Recalculate overall_pct (mean of non-zero scores)
    cursor = await db.execute(
        "SELECT score_test, score_breus, score_suposit, score_connecta, score_buits "
        "FROM progress WHERE topic_id=?", (body.topic_id,)
    )
    row = await cursor.fetchone()
    if row:
        scores = [v for v in dict(row).values() if v and v > 0]
        overall = (sum(scores) / len(scores) / 10.0 * 100) if scores else 0.0
        await db.execute(
            "UPDATE progress SET overall_pct=? WHERE topic_id=?",
            (overall, body.topic_id)
        )
    await db.commit()
    return {"status": "saved", "topic_id": body.topic_id, "mode": body.mode, "score": body.score}
```

- [ ] **Step 4: Run tests — expect pass**

```bash
python -m pytest tests/test_practice.py -v
```
Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add routers/practice.py tests/test_practice.py
git commit -m "feat: practice router — all 5 modes, evaluate endpoint, session save with progress update"
```

---

## Task 8: Progress Router

**Files:**
- Modify: `/opt/opos-api/routers/progress.py`
- Test: (covered by test_practice.py for progress data; add readiness test)

- [ ] **Step 1: Write the failing test**

Add to `/opt/opos-api/tests/test_practice.py`:
```python
def test_get_global_progress_structure(client):
    resp = client.get("/api/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_pct" in data
    assert "topics" in data
    assert "general_pct" in data
    assert "especific_pct" in data
```

- [ ] **Step 2: Run test — expect failure**

```bash
python -m pytest tests/test_practice.py::test_get_global_progress_structure -v
```
Expected: 404 (no /api/progress route yet).

- [ ] **Step 3: Implement routers/progress.py**

```python
import os
import json
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends
from database import get_db
from services.gemini import get_gemini
from services.markdown_parser import get_topics

router = APIRouter(tags=["progress"])

NOTES_PATH = Path(os.getenv("NOTES_PATH", "/opt/opos-api/ApuntsTemari.md"))

@router.get("/api/progress")
async def get_progress(db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM progress ORDER BY bloc, topic_id")
    rows = [dict(r) for r in await cursor.fetchall()]

    all_topics = get_topics(NOTES_PATH)
    # Ensure every topic appears, even those with no sessions
    progress_map = {r["topic_id"]: r for r in rows}
    full_list = []
    for t in all_topics:
        p = progress_map.get(t["id"], {
            "topic_id": t["id"], "bloc": t["bloc"],
            "score_test": 0, "score_breus": 0, "score_suposit": 0,
            "score_connecta": 0, "score_buits": 0,
            "tests_done": 0, "last_activity": None, "overall_pct": 0.0
        })
        p["title"] = t["title"]
        full_list.append(p)

    general = [t for t in full_list if t["bloc"] == "general"]
    especific = [t for t in full_list if t["bloc"] == "especific"]

    general_pct = sum(t["overall_pct"] for t in general) / len(general) if general else 0
    especific_pct = sum(t["overall_pct"] for t in especific) / len(especific) if especific else 0
    overall_pct = sum(t["overall_pct"] for t in full_list) / len(full_list) if full_list else 0

    # Last 10 practice sessions
    cursor = await db.execute(
        "SELECT topic_id, mode, score, created_at FROM practice_sessions "
        "ORDER BY created_at DESC LIMIT 10"
    )
    history = [dict(r) for r in await cursor.fetchall()]

    return {
        "overall_pct": round(overall_pct, 1),
        "general_pct": round(general_pct, 1),
        "especific_pct": round(especific_pct, 1),
        "topics": full_list,
        "history": history,
    }

@router.get("/api/progress/exam-readiness")
async def exam_readiness(db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM progress")
    progress_rows = [dict(r) for r in await cursor.fetchall()]

    cursor = await db.execute("SELECT * FROM pdf_analysis")
    gaps_rows = [dict(r) for r in await cursor.fetchall()]

    today = date.today().isoformat()
    exam_date = "2026-04-22"
    dies = (date.fromisoformat(exam_date) - date.today()).days

    result = await get_gemini().exam_readiness(
        json.dumps(progress_rows),
        json.dumps(gaps_rows),
        exam_date, today, dies
    )
    result["exam_date"] = exam_date
    result["dies_restants"] = dies
    return result
```

- [ ] **Step 4: Run test — expect pass**

```bash
python -m pytest tests/test_practice.py -v
```
Expected: all tests pass (including the new progress structure test).

- [ ] **Step 5: Commit**

```bash
git add routers/progress.py tests/test_practice.py
git commit -m "feat: progress router — global stats, per-topic breakdown, history, exam readiness via Gemini"
```

---

## Task 9: PDF Analyzer + Config Router

**Files:**
- Create: `/opt/opos-api/services/pdf_analyzer.py`
- Modify: `/opt/opos-api/routers/pdf.py`
- Modify: `/opt/opos-api/routers/config.py`

- [ ] **Step 1: Write the failing tests**

Add to `/opt/opos-api/tests/test_practice.py`:
```python
def test_get_config_empty(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)

def test_set_config(client):
    resp = client.post("/api/config", json={"key": "theme", "value": "dark"})
    assert resp.status_code == 200
    assert client.get("/api/config").json().get("theme") == "dark"
```

- [ ] **Step 2: Run tests — expect failure**

```bash
python -m pytest tests/test_practice.py::test_get_config_empty -v
```
Expected: 404 (no /api/config route).

- [ ] **Step 3: Create services/pdf_analyzer.py**

```python
import os
import json
from pathlib import Path
import fitz  # PyMuPDF
from services.gemini import get_gemini
from services.markdown_parser import get_topics

PDF_PATH = Path(os.getenv("PDF_PATH", "/opt/opos-api/EdicteC1Maçanet.pdf"))
NOTES_PATH = Path(os.getenv("NOTES_PATH", "/opt/opos-api/ApuntsTemari.md"))

def extract_pdf_text(pdf_path: Path = PDF_PATH) -> str:
    doc = fitz.open(str(pdf_path))
    return "\n".join(page.get_text() for page in doc)

async def analyze_all_topics(db) -> list[dict]:
    pdf_text = extract_pdf_text()
    topics = get_topics(NOTES_PATH)
    results = []
    gemini = get_gemini()

    for topic in topics:
        prompt = (
            "Compara el contingut dels apunts amb el temari oficial del PDF.\n"
            "Retorna ÚNICAMENT JSON:\n"
            '{"cobertura": "completa", "gaps": ["punt no cobert"], "suggeriments": ["estudia X"]}\n'
            f"TEMA: {topic['title']}\n"
            f"APUNTS:\n{topic['content'][:2000]}\n\n"
            f"TEMARI OFICIAL (fragment rellevant):\n{pdf_text[:1500]}"
        )
        analysis = await gemini._generate_json(prompt)
        await db.execute(
            "INSERT INTO pdf_analysis (topic_id, cobertura, gaps_json, suggeriments_json) "
            "VALUES (?,?,?,?) ON CONFLICT(topic_id) DO UPDATE SET "
            "cobertura=excluded.cobertura, gaps_json=excluded.gaps_json, "
            "suggeriments_json=excluded.suggeriments_json, analyzed_at=datetime('now')",
            (topic["id"], analysis.get("cobertura", "parcial"),
             json.dumps(analysis.get("gaps", [])),
             json.dumps(analysis.get("suggeriments", [])))
        )
        results.append({"topic_id": topic["id"], **analysis})

    await db.commit()
    return results
```

- [ ] **Step 4: Implement routers/pdf.py**

```python
from fastapi import APIRouter, Depends
from database import get_db
from services.pdf_analyzer import analyze_all_topics

router = APIRouter(tags=["pdf"])

@router.post("/api/pdf/analyze")
async def run_pdf_analysis(db=Depends(get_db)):
    results = await analyze_all_topics(db)
    return {"analyzed": len(results), "results": results}

@router.get("/api/pdf/analysis")
async def get_pdf_analysis(db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM pdf_analysis ORDER BY topic_id")
    return [dict(r) for r in await cursor.fetchall()]
```

- [ ] **Step 5: Implement routers/config.py**

```python
from fastapi import APIRouter, Depends
from models import ConfigSet
from database import get_db

router = APIRouter(tags=["config"])

@router.get("/api/config")
async def get_config(db=Depends(get_db)):
    cursor = await db.execute("SELECT key, value FROM config")
    return {row["key"]: row["value"] for row in await cursor.fetchall()}

@router.post("/api/config")
async def set_config(body: ConfigSet, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO config (key, value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (body.key, body.value)
    )
    await db.commit()
    return {"key": body.key, "value": body.value}
```

- [ ] **Step 6: Run all tests**

```bash
python -m pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add services/pdf_analyzer.py routers/pdf.py routers/config.py tests/test_practice.py
git commit -m "feat: PDF analyzer (PyMuPDF + Gemini gap analysis) and config router"
```

---

## Task 10: Smoke Test + Health Check

**Files:**
- Modify: `backend/main.py` (add health endpoint, confirm all routers imported)

- [ ] **Step 1: Add health check to main.py**

Add before the router includes:
```python
@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Start server locally for smoke test**

From the `backend/` directory (with venv activated):
```bash
# Windows:
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# Create a local .env for testing (NOT the production one):
# DB_PATH=./opos.db
# NOTES_PATH=../data/ApuntsTemari.md  (or full path)
# PDF_PATH=../data/EdicteC1Maçanet.pdf
# GEMINI_API_KEY=  (leave blank for smoke test — Gemini endpoints will fail but that's OK)

uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- [ ] **Step 3: Smoke test core endpoints**

```bash
curl http://127.0.0.1:8000/api/health
# Expected: {"status":"ok"}

curl http://127.0.0.1:8000/api/topics | python -m json.tool | head -30
# Expected: JSON array with 20 topics

curl "http://127.0.0.1:8000/api/topics/general_1/content" | python -m json.tool | head -10
# Expected: {"id":"general_1","title":"L'Organització Municipal",...}
```

- [ ] **Step 4: Run full test suite**

```bash
python -m pytest tests/ -v --tb=short
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "feat: health check endpoint + verified full backend smoke test"
```

---

## Task 11: Dockerfile

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`

- [ ] **Step 1: Write failing test (build check)**

This task has no pytest tests — the verification is a successful `docker build`. Write it as a manual check.

- [ ] **Step 2: Create backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

# System deps for PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

- [ ] **Step 3: Create backend/.dockerignore**

```
venv/
__pycache__/
*.pyc
*.pyo
.env
opos.db
tests/
.pytest_cache/
```

- [ ] **Step 4: Verify docker build succeeds**

From the `backend/` directory:
```bash
docker build -t opos-backend .
```
Expected: `Successfully built ...` with no errors.

- [ ] **Step 5: Verify container starts**

```bash
docker run --rm \
  -e GEMINI_API_KEY=test \
  -e DB_PATH=/data/opos.db \
  -e NOTES_PATH=/data/ApuntsTemari.md \
  -e PDF_PATH=/data/EdicteC1Maçanet.pdf \
  -p 8000:8000 \
  opos-backend &
sleep 3
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}
docker stop $(docker ps -q --filter ancestor=opos-backend)
```

- [ ] **Step 6: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: Dockerfile for Docker Compose deployment"
```
