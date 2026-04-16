# Apunts Visual Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the notes reader with collapsible sections, a reading progress bar, AI-generated visual components per section (timelines, cards, tables, callouts), and an AI topic summary — all persisted to the DB.

**Architecture:** The backend gains two new DB tables (`topic_enrichments`, `topic_summaries`) and a new router (`/api/ai/enrichments`) with 4 endpoints. Two new Gemini methods are added to `GeminiService`. The frontend replaces `TopicContent.vue` with a set of focused components assembled in `ApuntsView.vue`: a reading progress bar, an AI summary card, and collapsible `SectionBlock` components that can be individually enriched by the AI.

**Tech Stack:** FastAPI + aiosqlite (backend), Vue 3 Composition API + marked.js + Tailwind (frontend), Google Gemini API via `google-genai` SDK.

**Spec:** `docs/superpowers/specs/2026-04-16-apunts-visual-redesign.md`

---

## File Map

**Backend — new/modified:**
- `backend/database.py` — add 2 new `CREATE TABLE IF NOT EXISTS` blocks
- `backend/services/gemini.py` — add `enrich_section()` and `generate_topic_summary()` methods to `GeminiService`
- `backend/routers/enrichment.py` — NEW: 4 endpoints
- `backend/main.py` — register enrichment router
- `backend/models.py` — add `EnrichmentCreate`, `SummaryCreate` Pydantic models
- `backend/tests/test_enrichment.py` — NEW: all enrichment tests

**Frontend — new/modified:**
- `frontend/src/api/client.js` — 4 new API functions
- `frontend/src/components/apunts/enriched/TimelineView.vue` — NEW
- `frontend/src/components/apunts/enriched/ConceptCards.vue` — NEW
- `frontend/src/components/apunts/enriched/ComparisonTable.vue` — NEW
- `frontend/src/components/apunts/enriched/CalloutBoxes.vue` — NEW
- `frontend/src/components/apunts/ProseContent.vue` — NEW (replaces inner rendered markdown)
- `frontend/src/components/apunts/SectionBlock.vue` — NEW (collapsible section with Enriquir button)
- `frontend/src/components/apunts/AISummaryCard.vue` — NEW (topic summary card)
- `frontend/src/components/apunts/ReadingProgressBar.vue` — NEW (scroll-driven 3px bar)
- `frontend/src/views/ApuntsView.vue` — REWRITE to integrate all new components

---

## Task 1: DB Tables for Enrichments

**Files:**
- Modify: `backend/database.py`
- Create: `backend/tests/test_enrichment.py`

- [ ] **Step 1: Add the two new tables to `_CREATE_TABLES` in `database.py`**

Open `backend/database.py`. After the `config` table entry (last item in the `_CREATE_TABLES` list), add two new entries:

```python
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
```

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_enrichment.py`:

```python
import asyncio
import pytest
from fastapi.testclient import TestClient


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
```

- [ ] **Step 3: Run the failing test**

```bash
cd "C:/Users/iruiz/OneDrive - Sa Palomera/OTRAS COSAS/OPOS/backend"
python -m pytest tests/test_enrichment.py::test_enrichments_table_exists -v
```

Expected: FAIL — tables not yet created.

- [ ] **Step 4: Apply the `database.py` edit from Step 1**

The `_CREATE_TABLES` list should now end with the two new tables.

- [ ] **Step 5: Run the test again**

```bash
python -m pytest tests/test_enrichment.py::test_enrichments_table_exists -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/database.py backend/tests/test_enrichment.py
git commit -m "feat: add topic_enrichments and topic_summaries tables"
```

---

## Task 2: Gemini Methods for Section Enrichment

**Files:**
- Modify: `backend/services/gemini.py`
- Modify: `backend/models.py`

- [ ] **Step 1: Add Pydantic models to `models.py`**

Append to `backend/models.py`:

```python
class EnrichmentCreate(BaseModel):
    topic_id: str
    section_idx: int
    section_markdown: str


class SummaryRequest(BaseModel):
    topic_id: str
    topic_content: str
```

- [ ] **Step 2: Add `enrich_section` method to `GeminiService` in `gemini.py`**

Add this method inside `GeminiService`, after `generate_suposit`:

```python
async def enrich_section(self, section_markdown: str) -> dict:
    """Analyse a section and return a visual enrichment JSON."""
    prompt = (
        "Ets un expert en visualització de contingut per a oposicions. "
        "Analitza el text de la secció i genera una representació visual en JSON.\n\n"
        "REGLES:\n"
        "1. Detecta el tipus de contingut:\n"
        "   - Procés amb passos o fases → type: \"timeline\"\n"
        "   - Comparació d'entitats amb atributs → type: \"table\"\n"
        "   - Definicions o conceptes clau → type: \"cards\"\n"
        "   - Lleis, regles, avisos, explicació general → type: \"callouts\"\n"
        "2. Respon ÚNICAMENT amb JSON vàlid, sense text addicional, sense markdown.\n\n"
        "FORMAT PER TIPUS:\n"
        "timeline: {\"type\":\"timeline\",\"data\":[{\"step\":1,\"title\":\"...\",\"desc\":\"...\"}]}\n"
        "table: {\"type\":\"table\",\"data\":{\"headers\":[\"...\"],\"rows\":[[\"...\"]],\"highlight\":[]}}\n"
        "cards: {\"type\":\"cards\",\"data\":[{\"title\":\"...\",\"desc\":\"...\",\"icon\":\"building\"}]}\n"
        "  (icon valors: building, user, file, scale, shield, clock, globe, users, key, flag)\n"
        "callouts: {\"type\":\"callouts\",\"data\":[{\"variant\":\"law\",\"title\":\"...\",\"text\":\"...\"}]}\n"
        "  (variant valors: law=blau, important=groc, exam=verd)\n\n"
        f"SECCIÓ:\n{section_markdown[:2000]}"
    )
    return await self._generate_json(prompt)

async def generate_topic_summary(self, topic_content: str) -> dict:
    """Generate a short summary and concept chips for a topic."""
    prompt = (
        "Ets un expert en preparació d'oposicions. "
        "Llegeix el text del tema i genera un resum visual.\n\n"
        "REGLES:\n"
        "1. El resum ha de tenir 1-2 frases que capturin l'essència del tema.\n"
        "2. Genera entre 3 i 5 chips de conceptes clau.\n"
        "3. Cada chip té: label (text curt, màx 4 paraules) i category.\n"
        "4. Categories de chip:\n"
        "   - concept: concepte principal del tema\n"
        "   - law: referència a una llei o article\n"
        "   - alert: punt important a no oblidar\n"
        "   - exam: molt probable a l'examen\n"
        "5. Respon ÚNICAMENT amb JSON vàlid, sense text addicional.\n\n"
        "FORMAT: {\"summary\":\"...\",\"chips\":[{\"label\":\"...\",\"category\":\"concept\"}]}\n\n"
        f"CONTINGUT DEL TEMA:\n{topic_content[:3000]}"
    )
    return await self._generate_json(prompt)
```

- [ ] **Step 3: Write a failing test for the new methods**

Add to `backend/tests/test_enrichment.py`:

```python
from unittest.mock import AsyncMock, patch


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
```

- [ ] **Step 4: Run the failing tests**

```bash
python -m pytest tests/test_enrichment.py -v -k "not table_exists"
```

Expected: All FAIL — endpoints don't exist yet.

- [ ] **Step 5: Commit the Gemini changes and models**

```bash
git add backend/services/gemini.py backend/models.py backend/tests/test_enrichment.py
git commit -m "feat: add enrich_section and generate_topic_summary to GeminiService"
```

---

## Task 3: Enrichment Router

**Files:**
- Create: `backend/routers/enrichment.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create `backend/routers/enrichment.py`**

```python
import json
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import EnrichmentCreate, SummaryRequest
from services.gemini import get_gemini

router = APIRouter(prefix="/api/ai", tags=["enrichment"])


@router.get("/enrichments/{topic_id}")
async def get_enrichments(topic_id: str, db=Depends(get_db)):
    """Return all persisted enrichments for a topic."""
    cursor = await db.execute(
        "SELECT section_idx, type, data_json FROM topic_enrichments WHERE topic_id=? ORDER BY section_idx",
        (topic_id,)
    )
    rows = await cursor.fetchall()
    return [
        {"section_idx": r["section_idx"], "type": r["type"], "data": json.loads(r["data_json"])}
        for r in rows
    ]


@router.post("/enrich")
async def enrich_section(payload: EnrichmentCreate, db=Depends(get_db), gemini=Depends(get_gemini)):
    """Generate (or return cached) enrichment for a section."""
    # Return cached result if it exists
    cursor = await db.execute(
        "SELECT type, data_json FROM topic_enrichments WHERE topic_id=? AND section_idx=?",
        (payload.topic_id, payload.section_idx)
    )
    existing = await cursor.fetchone()
    if existing:
        return {"type": existing["type"], "data": json.loads(existing["data_json"])}

    # Generate via AI
    result = await gemini.enrich_section(payload.section_markdown)

    # Validate minimal structure
    if "type" not in result or "data" not in result:
        raise HTTPException(status_code=500, detail="La IA ha retornat una estructura invàlida.")

    # Persist
    await db.execute(
        "INSERT OR REPLACE INTO topic_enrichments (topic_id, section_idx, type, data_json) VALUES (?,?,?,?)",
        (payload.topic_id, payload.section_idx, result["type"], json.dumps(result["data"]))
    )
    await db.commit()

    return result


@router.get("/summary/{topic_id}")
async def get_summary(topic_id: str, db=Depends(get_db)):
    """Return cached topic summary, or 404 if not yet generated."""
    cursor = await db.execute(
        "SELECT summary, chips_json FROM topic_summaries WHERE topic_id=?",
        (topic_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Summary not found")
    return {"summary": row["summary"], "chips": json.loads(row["chips_json"])}


@router.post("/topic-summary")
async def generate_summary(payload: SummaryRequest, db=Depends(get_db), gemini=Depends(get_gemini)):
    """Generate (or return cached) topic summary."""
    # Return cached
    cursor = await db.execute(
        "SELECT summary, chips_json FROM topic_summaries WHERE topic_id=?",
        (payload.topic_id,)
    )
    existing = await cursor.fetchone()
    if existing:
        return {"summary": existing["summary"], "chips": json.loads(existing["chips_json"])}

    result = await gemini.generate_topic_summary(payload.topic_content)

    if "summary" not in result or "chips" not in result:
        raise HTTPException(status_code=500, detail="La IA ha retornat una estructura invàlida.")

    await db.execute(
        "INSERT OR REPLACE INTO topic_summaries (topic_id, summary, chips_json) VALUES (?,?,?)",
        (payload.topic_id, result["summary"], json.dumps(result["chips"]))
    )
    await db.commit()

    return result
```

- [ ] **Step 2: Register the router in `main.py`**

Add to `backend/main.py`, after `from routers import ai as ai_router`:

```python
from routers import enrichment as enrichment_router
```

And after `app.include_router(ai_router.router)`:

```python
app.include_router(enrichment_router.router)
```

- [ ] **Step 3: Run the enrichment tests**

```bash
python -m pytest tests/test_enrichment.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/routers/enrichment.py backend/main.py
git commit -m "feat: add enrichment router with GET/POST endpoints for sections and summaries"
```

---

## Task 4: Frontend API Client

**Files:**
- Modify: `frontend/src/api/client.js`

- [ ] **Step 1: Add 4 new exported functions at the end of `client.js`**

```js
export const fetchEnrichments = async (topicId) => (await api.get(`/ai/enrichments/${topicId}`)).data
export const saveEnrichment = async (topicId, sectionIdx, sectionMarkdown) =>
  (await api.post('/ai/enrich', { topic_id: topicId, section_idx: sectionIdx, section_markdown: sectionMarkdown })).data
export const fetchTopicSummary = async (topicId) => (await api.get(`/ai/summary/${topicId}`)).data
export const generateTopicSummary = async (topicId, topicContent) =>
  (await api.post('/ai/topic-summary', { topic_id: topicId, topic_content: topicContent })).data
```

- [ ] **Step 2: Verify the file compiles**

```bash
cd "C:/Users/iruiz/OneDrive - Sa Palomera/OTRAS COSAS/OPOS/frontend"
npm run build 2>&1 | tail -5
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/client.js
git commit -m "feat: add enrichment API client functions"
```

---

## Task 5: Enriched Visual Components

**Files:**
- Create: `frontend/src/components/apunts/enriched/TimelineView.vue`
- Create: `frontend/src/components/apunts/enriched/ConceptCards.vue`
- Create: `frontend/src/components/apunts/enriched/ComparisonTable.vue`
- Create: `frontend/src/components/apunts/enriched/CalloutBoxes.vue`

- [ ] **Step 1: Create `TimelineView.vue`**

```vue
<template>
  <div class="timeline py-1">
    <div v-for="(item, i) in data" :key="i" class="flex gap-3 mb-1">
      <div class="flex flex-col items-center flex-shrink-0">
        <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
             :style="{ background: stepColor(i, data.length) }">
          {{ item.step }}
        </div>
        <div v-if="i < data.length - 1" class="w-0.5 flex-1 min-h-3.5 bg-[var(--color-border)] mt-0.5"></div>
      </div>
      <div class="pb-3">
        <p class="text-sm font-semibold text-[var(--color-text)]">{{ item.title }}</p>
        <p class="text-xs text-gray-500 mt-0.5 leading-snug">{{ item.desc }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Array, required: true } })

function stepColor(i, total) {
  if (i === total - 1) return '#22c55e'
  if (i === 0) return '#3b82f6'
  return '#8b5cf6'
}
</script>
```

- [ ] **Step 2: Create `ConceptCards.vue`**

```vue
<template>
  <div class="grid grid-cols-2 gap-2 mt-1">
    <div v-for="(card, i) in data" :key="i"
         class="bg-[#f5f3ff] border border-[#e0d9f7] rounded-xl p-3 text-center">
      <div class="w-8 h-8 bg-white rounded-lg mx-auto mb-2 flex items-center justify-center shadow-sm">
        <component :is="iconComponent(card.icon)" class="w-4 h-4 text-primary" />
      </div>
      <p class="text-xs font-bold text-primary mb-1">{{ card.title }}</p>
      <p class="text-[0.68rem] text-gray-500 leading-snug">{{ card.desc }}</p>
    </div>
  </div>
</template>

<script setup>
import { h } from 'vue'

defineProps({ data: { type: Array, required: true } })

// Inline SVG icon map — Lucide style, stroke-based
const ICONS = {
  building: 'M3 9h18v13H3zM8 22V12h8v10M3 9V7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2M12 5V2',
  user: 'M12 8m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0M4 20c0-4 3.6-7 8-7s8 3 8 7',
  file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H9H8',
  scale: 'm16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1zM2 16l3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1zM7 21h10M12 3v18M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2',
  shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  clock: 'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zM12 6v6l4 2',
  globe: 'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z',
  users: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
  key: 'M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0 3 3L22 7l-3-3m-3.5 3.5L19 4',
  flag: 'M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22v-7',
}

function iconComponent(name) {
  const d = ICONS[name] || ICONS.file
  return {
    render() {
      return h('svg', {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': '1.8',
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        class: 'w-4 h-4',
      }, d.split('M').filter(Boolean).map(seg =>
        h('path', { d: 'M' + seg })
      ))
    }
  }
}
</script>
```

- [ ] **Step 3: Create `ComparisonTable.vue`**

```vue
<template>
  <div class="overflow-x-auto mt-1">
    <table class="w-full border-collapse text-xs">
      <thead>
        <tr class="bg-[#f5f3ff]">
          <th v-for="h in data.headers" :key="h"
              class="text-left text-primary font-bold px-2.5 py-1.5">{{ h }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in data.rows" :key="i"
            class="border-b border-[var(--color-border)] last:border-0">
          <td v-for="(cell, j) in row" :key="j"
              class="px-2.5 py-1.5"
              :class="cellClass(i, j)">
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({ data: { type: Object, required: true } })

function cellClass(rowIdx, colIdx) {
  // First column always bold
  if (colIdx === 0) return 'font-semibold'
  return ''
}
</script>
```

- [ ] **Step 4: Create `CalloutBoxes.vue`**

```vue
<template>
  <div class="space-y-2 mt-1">
    <div v-for="(box, i) in data" :key="i"
         class="rounded-lg px-3 py-2.5 flex gap-2.5 items-start text-sm leading-relaxed"
         :class="variantClass(box.variant)">
      <span class="flex-shrink-0 mt-0.5">
        <svg v-if="box.variant === 'law'" class="w-4 h-4 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
        </svg>
        <svg v-else-if="box.variant === 'important'" class="w-4 h-4 text-yellow-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
          <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <svg v-else class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
        </svg>
      </span>
      <div>
        <strong v-if="box.title" class="font-semibold">{{ box.title }}:</strong>
        {{ box.text }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Array, required: true } })

function variantClass(variant) {
  if (variant === 'law') return 'bg-blue-50 border-l-[3px] border-blue-400'
  if (variant === 'important') return 'bg-yellow-50 border-l-[3px] border-yellow-400'
  return 'bg-green-50 border-l-[3px] border-green-400'
}
</script>
```

- [ ] **Step 5: Verify no build errors**

```bash
cd "C:/Users/iruiz/OneDrive - Sa Palomera/OTRAS COSAS/OPOS/frontend"
npm run build 2>&1 | tail -5
```

Expected: exit 0, no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/apunts/enriched/
git commit -m "feat: add TimelineView, ConceptCards, ComparisonTable, CalloutBoxes enriched components"
```

---

## Task 6: ProseContent.vue

**Files:**
- Create: `frontend/src/components/apunts/ProseContent.vue`

This component renders a section's markdown to HTML, applying law-reference badges to known acronyms.

- [ ] **Step 1: Create `ProseContent.vue`**

```vue
<template>
  <div class="prose prose-sm dark:prose-invert max-w-none pt-2
              [&_code]:bg-gray-100 dark:[&_code]:bg-gray-800
              [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:p-3
              [&_.law-ref]:inline-block [&_.law-ref]:bg-blue-100 [&_.law-ref]:dark:bg-blue-900/30
              [&_.law-ref]:text-blue-700 [&_.law-ref]:dark:text-blue-300
              [&_.law-ref]:text-[0.7rem] [&_.law-ref]:font-semibold [&_.law-ref]:font-mono
              [&_.law-ref]:px-1.5 [&_.law-ref]:rounded"
       v-html="rendered" />
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  content: { type: String, default: '' }
})

const LAW_REFS = ['LPACAP', 'LRJSP', 'LRBRL', 'LMRLC', 'LOPDGDD', 'LCSP', 'TRLCSP', 'EBEP', 'LOTAI', 'LOTC', 'CE']
const LAW_RE = new RegExp(`\\b(${LAW_REFS.join('|')})\\b`, 'g')

const rendered = computed(() => {
  const html = marked.parse(props.content || '', { breaks: true, gfm: true })
  return html.replace(LAW_RE, '<span class="law-ref">$1</span>')
})
</script>
```

- [ ] **Step 2: Verify build**

```bash
npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/apunts/ProseContent.vue
git commit -m "feat: add ProseContent component with law-ref badge rendering"
```

---

## Task 7: SectionBlock.vue

**Files:**
- Create: `frontend/src/components/apunts/SectionBlock.vue`

- [ ] **Step 1: Create `SectionBlock.vue`**

```vue
<template>
  <div class="border border-[var(--color-border)] rounded-xl overflow-hidden bg-[var(--color-surface)] mb-2.5">
    <!-- Header -->
    <div class="flex items-center justify-between px-3.5 py-3 cursor-pointer select-none hover:bg-[#faf9ff] dark:hover:bg-gray-800/50"
         @click="open = !open">
      <div class="flex items-center gap-2 text-sm font-bold">
        <!-- Number badge -->
        <div class="w-[22px] h-[22px] rounded-[6px] flex items-center justify-center text-white text-[0.68rem] font-bold flex-shrink-0"
             :class="isRead ? 'bg-green-500' : 'bg-primary'">
          <template v-if="isRead">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          </template>
          <template v-else>{{ index + 1 }}</template>
        </div>
        <span :class="isRead ? 'text-gray-500 dark:text-gray-400' : ''">{{ title }}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <!-- Enrich button -->
        <button v-if="!enrichment && !loading" @click.stop="$emit('enrich', index)"
                class="text-[0.68rem] font-semibold px-2.5 py-1 rounded-full
                       border border-[#c4b5fd] bg-[#f5f3ff] text-primary
                       flex items-center gap-1 hover:bg-primary hover:text-white transition-colors">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
          Enriquir
        </button>
        <span v-else-if="loading"
              class="text-[0.68rem] font-semibold px-2.5 py-1 rounded-full
                     border border-[#c4b5fd] bg-[#f5f3ff] text-primary flex items-center gap-1">
          <svg class="animate-spin" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-opacity="0.25"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>
          Generant…
        </span>
        <span v-else-if="enrichment"
              class="text-[0.68rem] font-semibold px-2.5 py-1 rounded-full
                     border border-green-300 bg-green-50 text-green-700 flex items-center gap-1">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          Enriquit
        </span>
        <span v-if="error" class="text-[0.65rem] text-red-500 max-w-[120px] truncate">{{ error }}</span>
        <!-- Chevron -->
        <svg class="w-3.5 h-3.5 text-[#c4b5fd] transition-transform"
             :class="open ? '' : 'rotate-180'"
             viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="18 15 12 9 6 15"/>
        </svg>
      </div>
    </div>

    <!-- Content -->
    <div v-if="open" class="px-3.5 pb-3.5 border-t border-[var(--color-border)]">
      <!-- Enriched badge -->
      <div v-if="enrichment"
           class="inline-flex items-center gap-1.5 text-[0.65rem] font-bold text-primary
                  bg-[#f5f3ff] border border-[#c4b5fd] px-2 py-0.5 rounded-full mt-2 mb-2">
        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
        </svg>
        Generat per IA · {{ typeLabel(enrichment.type) }}
      </div>

      <!-- Enriched visual component -->
      <TimelineView v-if="enrichment?.type === 'timeline'" :data="enrichment.data" />
      <ConceptCards v-else-if="enrichment?.type === 'cards'" :data="enrichment.data" />
      <ComparisonTable v-else-if="enrichment?.type === 'table'" :data="enrichment.data" />
      <CalloutBoxes v-else-if="enrichment?.type === 'callouts'" :data="enrichment.data" />

      <!-- Plain prose (always shown, below enriched component) -->
      <ProseContent :content="markdown" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ProseContent from './ProseContent.vue'
import TimelineView from './enriched/TimelineView.vue'
import ConceptCards from './enriched/ConceptCards.vue'
import ComparisonTable from './enriched/ComparisonTable.vue'
import CalloutBoxes from './enriched/CalloutBoxes.vue'

const props = defineProps({
  index: { type: Number, required: true },
  title: { type: String, required: true },
  markdown: { type: String, required: true },
  enrichment: { type: Object, default: null },   // { type, data }
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  isRead: { type: Boolean, default: false },
})

defineEmits(['enrich'])

const open = ref(true)  // sections start expanded

function typeLabel(type) {
  const map = { timeline: 'Timeline', cards: 'Cards', table: 'Taula comparativa', callouts: 'Callouts' }
  return map[type] || type
}
</script>
```

- [ ] **Step 2: Verify build**

```bash
npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/apunts/SectionBlock.vue
git commit -m "feat: add SectionBlock component with enrichment support"
```

---

## Task 8: AISummaryCard.vue

**Files:**
- Create: `frontend/src/components/apunts/AISummaryCard.vue`

- [ ] **Step 1: Create `AISummaryCard.vue`**

```vue
<template>
  <!-- Loading skeleton -->
  <div v-if="loading"
       class="rounded-2xl border border-[#c4b5fd] bg-gradient-to-br from-[#f5f3ff] to-[#eff6ff] p-4 mb-5 animate-pulse">
    <div class="h-3 bg-purple-200 rounded w-24 mb-3"></div>
    <div class="h-3 bg-purple-100 rounded w-full mb-2"></div>
    <div class="h-3 bg-purple-100 rounded w-4/5"></div>
  </div>

  <!-- Summary card -->
  <div v-else-if="summary"
       class="rounded-2xl border border-[#c4b5fd] bg-gradient-to-br from-[#f5f3ff] to-[#eff6ff] p-4 mb-5">
    <div class="flex items-center justify-between mb-2.5">
      <span class="inline-flex items-center gap-1.5 text-[0.65rem] font-bold text-primary
                   bg-primary/10 px-2 py-0.5 rounded-full tracking-wide">
        <!-- CPU icon -->
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
          <path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/>
        </svg>
        RESUM IA
      </span>
      <span class="text-[0.65rem] text-gray-400">{{ sectionCount }} seccions</span>
    </div>
    <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-3">{{ summary.summary }}</p>
    <div class="flex flex-wrap gap-1.5">
      <span v-for="chip in summary.chips" :key="chip.label"
            class="inline-flex items-center gap-1 text-[0.68rem] font-medium px-2 py-0.5 rounded-full"
            :class="chipClass(chip.category)">
        <component :is="chipIcon(chip.category)" class="w-2.5 h-2.5" />
        {{ chip.label }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { h } from 'vue'

defineProps({
  summary: { type: Object, default: null },   // { summary, chips }
  loading: { type: Boolean, default: false },
  sectionCount: { type: Number, default: 0 },
})

function chipClass(category) {
  const map = {
    concept: 'bg-blue-100 text-blue-700',
    law: 'bg-green-100 text-green-700',
    alert: 'bg-orange-100 text-orange-700',
    exam: 'bg-red-100 text-red-700',
  }
  return map[category] || 'bg-gray-100 text-gray-600'
}

function chipIcon(category) {
  const paths = {
    concept: 'M9 12l2 2 4-4m6 2a10 10 0 1 1-20 0 10 10 0 0 1 20 0z',
    law: 'M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20',
    alert: 'M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z',
    exam: 'm12 2-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z',
  }
  const d = paths[category] || paths.concept
  return {
    render() {
      return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', class: 'w-2.5 h-2.5' }, [
        h('path', { d })
      ])
    }
  }
}
</script>
```

- [ ] **Step 2: Verify build**

```bash
npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/apunts/AISummaryCard.vue
git commit -m "feat: add AISummaryCard component"
```

---

## Task 9: ReadingProgressBar.vue

**Files:**
- Create: `frontend/src/components/apunts/ReadingProgressBar.vue`

- [ ] **Step 1: Create `ReadingProgressBar.vue`**

The parent passes `pct` (0–100). The bar just renders it.

```vue
<template>
  <div class="h-[3px] bg-[var(--color-border)] sticky z-[9]" :style="{ top: topOffset + 'px' }">
    <div class="h-full bg-gradient-to-r from-primary to-blue-400 transition-[width] duration-200"
         :style="{ width: pct + '%' }"></div>
  </div>
</template>

<script setup>
defineProps({
  pct: { type: Number, default: 0 },
  topOffset: { type: Number, default: 45 },
})
</script>
```

- [ ] **Step 2: Verify build**

```bash
npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/apunts/ReadingProgressBar.vue
git commit -m "feat: add ReadingProgressBar component"
```

---

## Task 10: Rewire ApuntsView.vue

**Files:**
- Modify: `frontend/src/views/ApuntsView.vue`

This is the integration task. The view:
1. Parses topic markdown into sections
2. Loads enrichments from DB on topic open
3. Starts background summary generation on first visit
4. Tracks scroll → updates reading progress % + marks sections as read (localStorage)
5. Handles "enrich" events from SectionBlock children

- [ ] **Step 1: Rewrite `ApuntsView.vue` completely**

```vue
<template>
  <div>
    <!-- Sticky header -->
    <div class="sticky top-0 z-30 flex items-center gap-2 px-4 py-2
                bg-[var(--color-surface)] border-b border-[var(--color-border)]">
      <button @click="mode = 'text'"
              :class="mode === 'text' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors flex items-center gap-1.5">
        <!-- book-open icon -->
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
        Text
      </button>
      <button @click="mode = 'draw'"
              :class="mode === 'draw' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors flex items-center gap-1.5">
        <!-- pencil icon -->
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
        </svg>
        Dibuix
      </button>
      <div class="flex-1"></div>
      <span class="text-xs text-gray-400 tabular-nums">{{ readingPct }}% llegit</span>
    </div>

    <!-- Reading progress bar -->
    <ReadingProgressBar :pct="readingPct" :top-offset="headerHeight" />

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-48">
      <span class="text-gray-400 animate-pulse">Carregant tema…</span>
    </div>

    <div v-else class="relative">
      <!-- Text mode -->
      <div :class="mode === 'draw' ? 'pointer-events-none select-none' : ''">
        <AnnotationLayer :topic-id="topics.activeTopicId">
          <div class="px-4 pb-20" ref="contentEl">
            <!-- Topic title -->
            <div class="mb-4 pt-3">
              <p class="text-[0.68rem] font-bold text-gray-400 tracking-widest uppercase mb-1">
                {{ topicData?.id?.replace('_', ' ') }}
              </p>
              <h1 class="text-xl font-extrabold leading-snug">{{ topicData?.title }}</h1>
            </div>

            <!-- AI Summary card -->
            <AISummaryCard
              :summary="summary"
              :loading="summaryLoading"
              :section-count="sections.length" />

            <!-- Section blocks -->
            <SectionBlock
              v-for="section in sections"
              :key="section.index"
              :ref="el => sectionEls[section.index] = el"
              :index="section.index"
              :title="section.title"
              :markdown="section.markdown"
              :enrichment="enrichments[section.index] || null"
              :loading="enrichLoading[section.index] || false"
              :error="enrichErrors[section.index] || null"
              :is-read="readSections.has(section.index)"
              @enrich="handleEnrich" />
          </div>
        </AnnotationLayer>
      </div>

      <!-- Draw mode overlay -->
      <div v-if="mode === 'draw'" class="absolute top-0 left-0 w-full z-10">
        <DrawingCanvas :topic-id="topics.activeTopicId" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useTopicsStore } from '../stores/topics.js'
import {
  fetchTopicContent,
  fetchEnrichments,
  saveEnrichment,
  fetchTopicSummary,
  generateTopicSummary,
} from '../api/client.js'
import AnnotationLayer from '../components/apunts/AnnotationLayer.vue'
import DrawingCanvas from '../components/apunts/DrawingCanvas.vue'
import ReadingProgressBar from '../components/apunts/ReadingProgressBar.vue'
import AISummaryCard from '../components/apunts/AISummaryCard.vue'
import SectionBlock from '../components/apunts/SectionBlock.vue'

// ── state ──────────────────────────────────────────────────────────────────
const topics = useTopicsStore()
const topicData = ref(null)
const loading = ref(false)
const mode = ref('text')
const sections = ref([])
const enrichments = reactive({})   // section_idx → { type, data }
const enrichLoading = reactive({}) // section_idx → bool
const enrichErrors = reactive({})  // section_idx → string
const summary = ref(null)
const summaryLoading = ref(false)
const readSections = ref(new Set())
const readingPct = ref(0)
const contentEl = ref(null)
const sectionEls = reactive({})
const headerHeight = 45  // px — matches the sticky header height

// ── localStorage helpers ───────────────────────────────────────────────────
const READ_KEY = 'opos_sections_read'

function loadReadSections(topicId) {
  try {
    const raw = localStorage.getItem(READ_KEY)
    const store = raw ? JSON.parse(raw) : {}
    readSections.value = new Set(store[topicId] || [])
  } catch { readSections.value = new Set() }
}

function saveReadSection(topicId, idx) {
  try {
    const raw = localStorage.getItem(READ_KEY)
    const store = raw ? JSON.parse(raw) : {}
    if (!store[topicId]) store[topicId] = []
    if (!store[topicId].includes(idx)) store[topicId].push(idx)
    localStorage.setItem(READ_KEY, JSON.stringify(store))
  } catch {}
}

// ── section parser ─────────────────────────────────────────────────────────
function parseSections(markdown) {
  const lines = (markdown || '').split('\n')
  const result = []
  let current = null
  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (current) result.push(current)
      current = { index: result.length, title: line.slice(3).trim(), markdown: '' }
    } else if (current) {
      current.markdown += line + '\n'
    }
  }
  if (current) result.push(current)
  // Fallback: treat whole content as single section if no ## headings
  if (result.length === 0 && markdown) {
    result.push({ index: 0, title: topicData.value?.title || 'Contingut', markdown })
  }
  return result
}

// ── load topic ─────────────────────────────────────────────────────────────
async function loadTopic(id) {
  if (!id) return
  loading.value = true
  summary.value = null
  summaryLoading.value = false
  sections.value = []
  Object.keys(enrichments).forEach(k => delete enrichments[k])
  Object.keys(enrichLoading).forEach(k => delete enrichLoading[k])
  Object.keys(enrichErrors).forEach(k => delete enrichErrors[k])
  readingPct.value = 0

  try {
    topicData.value = await fetchTopicContent(id)
    sections.value = parseSections(topicData.value.content)
    loadReadSections(id)

    // Load persisted enrichments
    const existing = await fetchEnrichments(id)
    existing.forEach(e => { enrichments[e.section_idx] = { type: e.type, data: e.data } })

    // Try to load cached summary, else generate in background
    try {
      summary.value = await fetchTopicSummary(id)
    } catch {
      // 404 → generate in background (fire and forget)
      summaryLoading.value = true
      generateTopicSummary(id, topicData.value.content)
        .then(r => { summary.value = r })
        .catch(() => {})
        .finally(() => { summaryLoading.value = false })
    }
  } finally {
    loading.value = false
  }
}

// ── enrich a section ───────────────────────────────────────────────────────
async function handleEnrich(idx) {
  if (enrichLoading[idx]) return
  const section = sections.value.find(s => s.index === idx)
  if (!section) return

  enrichLoading[idx] = true
  delete enrichErrors[idx]
  try {
    const result = await saveEnrichment(topics.activeTopicId, idx, section.markdown)
    enrichments[idx] = { type: result.type, data: result.data }
  } catch (e) {
    enrichErrors[idx] = e.response?.data?.detail || 'Error generant'
  } finally {
    delete enrichLoading[idx]
  }
}

// ── scroll tracking ────────────────────────────────────────────────────────
function onScroll() {
  const el = document.documentElement
  const scrollable = el.scrollHeight - el.clientHeight
  readingPct.value = scrollable > 0 ? Math.round((el.scrollTop / scrollable) * 100) : 0
}

let observer = null

async function setupObserver() {
  await nextTick()
  if (observer) observer.disconnect()
  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && entry.intersectionRatio >= 0.8) {
        const idx = parseInt(entry.target.dataset.sectionIdx)
        if (!isNaN(idx) && !readSections.value.has(idx)) {
          readSections.value = new Set([...readSections.value, idx])
          saveReadSection(topics.activeTopicId, idx)
        }
      }
    })
  }, { threshold: 0.8 })

  // Observe each section's content div
  Object.entries(sectionEls).forEach(([idx, el]) => {
    if (el?.$el) {
      el.$el.dataset.sectionIdx = idx
      observer.observe(el.$el)
    }
  })
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  if (observer) observer.disconnect()
})

watch(() => topics.activeTopicId, async (id) => {
  await loadTopic(id)
  await setupObserver()
}, { immediate: true })
</script>
```

- [ ] **Step 2: Verify build**

```bash
cd "C:/Users/iruiz/OneDrive - Sa Palomera/OTRAS COSAS/OPOS/frontend"
npm run build 2>&1 | tail -10
```

Expected: exit 0, no errors.

- [ ] **Step 3: Start dev server and open the app**

```bash
npm run dev
```

Open http://localhost:5173, navigate to a topic, verify:
- Header shows book + pencil SVG icons (no emojis)
- Reading progress bar appears below header
- Topic title and bloc info shown
- AI summary card shows loading skeleton, then summary chips
- Sections appear as collapsible blocks with numbered icons
- Sections 1, 2, 3 have "Enriquir" button
- Clicking "Enriquir" shows spinner, then enriched component + "Enriquit" badge
- Scrolling down updates the "% llegit" counter
- Scrolling past a section turns its number badge green

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ApuntsView.vue
git commit -m "feat: rewire ApuntsView with sections, reading progress, AI enrichment, SVG icons"
```

---

## Self-Review

**Spec coverage check:**
- Layer 1 CSS base (sticky header, progress bar, collapsible sections, better prose) → Tasks 9, 10
- Layer 2 AI enrichment per section → Tasks 2, 3, 7
- Layer 3 AI topic summary (background) → Tasks 2, 3, 8
- All 4 enrichment types (timeline, cards, table, callouts) → Task 5
- Law-ref badges → Task 6
- DB persistence → Task 1, 3
- GET enrichments on topic open → Task 3, 10
- Section read tracking → Task 10
- Error handling (rate limit 429, invalid AI response) → Task 3 (router validates; Gemini service raises 429)
- SVG icons, no emojis → Task 10

**No gaps found.** All spec requirements are covered.
