# Apunts Visual Redesign — Design Spec

## Summary

The current notes viewer renders markdown as plain, undifferentiated text. Every line looks equally important, long topics are hard to navigate, and the reading experience is visually dull. This spec defines a full visual redesign of the topic reader with two layers: (1) a CSS-only base that immediately improves all topics, and (2) an on-demand AI enrichment system that generates visual components per section and persists them to the database.

---

## Problems Addressed

1. **No visual hierarchy** — everything looks equally important; key facts don't stand out
2. **Loss of orientation** — hard to know where you are inside a long topic
3. **Lists don't aid retention** — relationships between concepts need visual structure, not just bullets
4. **Dull appearance** — plain grey text doesn't invite reading

---

## Decisions Made

| Question | Decision |
|---|---|
| Improvement direction | C — CSS base + selective on-demand AI enrichment |
| Visual components | All 6 (callouts, concept cards, timelines, tables, AI summary, collapsible sections + progress) |
| AI enrichment mode | C — per-section "Enriquir" button, on demand, persisted to DB |

---

## Visual Design

All icons are inline SVG (Lucide style, stroke-based, no emojis). Color palette uses the existing app purple (`#7c3aed`) as primary, with semantic colors for callout types (yellow = important, blue = law, green = exam tip).

Reference mockup: `.superpowers/brainstorm/203-1776347419/content/mockup-topic.html`

---

## Architecture

### Layer 1 — CSS Base (no AI, immediate)

Applied to the existing markdown renderer via improved Tailwind `prose` overrides and a new `TopicReader.vue` component:

- **Sticky header** with topic title, mode toggle buttons (Text / Dibuix), and reading progress percentage
- **Reading progress bar** — thin 3px gradient bar (purple → blue) below the header, width driven by scroll position
- **Collapsible sections** — each `##` heading becomes a collapsible block with a numbered icon (purple square), a chevron, and an "Enriquir" button. Sections marked as read turn the number green with a checkmark icon
- **Better prose** — increased line height, slightly larger body text, `law-ref` inline badges for law citations (e.g. `LPACAP`)

### Layer 2 — AI Enrichment (per section, on demand)

Each section has an "Enriquir" button. When tapped:

1. The frontend sends `POST /api/ai/enrich` with `{ topic_id, section_index, section_markdown }`
2. The backend uses Gemini to analyse the section content and detect its type:
   - **Process / steps** → generates a **Timeline** component
   - **Comparison / entities with attributes** → generates a **Comparison table**
   - **Key concepts / definitions** → generates **Concept cards** (2-column grid)
   - **Rules / laws / exam tips** → generates **Callout boxes** (yellow/blue/green)
   - **Mixed / general** → generates **Callout boxes** + a summary paragraph
3. The backend returns a JSON structure with `type` and `data` fields
4. The frontend replaces the section's markdown with the generated visual component
5. The result is saved to the DB (`topic_enrichments` table keyed by `topic_id + section_index`) so it is never regenerated

When a topic is opened, the frontend calls `GET /api/ai/enrichments/{topic_id}` to load all previously generated enrichments in a single request. Sections with an existing enrichment render the visual component immediately; the "Enriquir" button is shown as "Enriquit" (done state). Sections without an enrichment show the plain markdown and the active "Enriquir" button.

### Layer 3 — AI Topic Summary (auto-generated once)

At the top of each topic, a summary card is shown if one has been previously generated. It contains:
- A 1–2 sentence summary of the topic
- 3–5 concept chips with an icon and label (coloured by category: blue = key concept, green = law reference, orange = exam alert, red = high exam probability)

The summary is generated via `POST /api/ai/topic-summary` and cached in the DB (`topic_summaries` table). It is generated automatically the first time a topic is opened (background, non-blocking).

---

## Components

### New / Modified Frontend Files

| File | Role |
|---|---|
| `frontend/src/views/ApuntsView.vue` | Main topic reader — replaces or wraps current markdown display |
| `frontend/src/components/apunts/TopicHeader.vue` | Sticky header: title, mode buttons, reading % |
| `frontend/src/components/apunts/ReadingProgressBar.vue` | 3px gradient bar driven by scroll |
| `frontend/src/components/apunts/SectionBlock.vue` | Collapsible section with number icon, "Enriquir" button, enriched state |
| `frontend/src/components/apunts/AISummaryCard.vue` | Topic summary card at the top |
| `frontend/src/components/apunts/enriched/TimelineView.vue` | Renders timeline data from AI |
| `frontend/src/components/apunts/enriched/ConceptCards.vue` | 2-column concept card grid |
| `frontend/src/components/apunts/enriched/ComparisonTable.vue` | Comparison table |
| `frontend/src/components/apunts/enriched/CalloutBoxes.vue` | Callout boxes (yellow/blue/green) |
| `frontend/src/components/apunts/ProseContent.vue` | Renders plain markdown with improved CSS (law-ref badges, better lists) |

### New Backend Files

| File | Role |
|---|---|
| `backend/routers/enrichment.py` | `GET /api/ai/enrichments/{topic_id}`, `POST /api/ai/enrich`, `GET /api/ai/summary/{topic_id}`, `POST /api/ai/topic-summary` endpoints |
| `backend/services/enrichment.py` | Gemini prompts + JSON parsing for each enrichment type |
| `backend/models/enrichment.py` | DB models: `TopicEnrichment`, `TopicSummary` |

### DB Schema (new tables)

```sql
-- Per-section enrichments
CREATE TABLE topic_enrichments (
  id         INTEGER PRIMARY KEY,
  topic_id   TEXT NOT NULL,
  section_idx INTEGER NOT NULL,
  type       TEXT NOT NULL,   -- 'timeline' | 'cards' | 'table' | 'callouts'
  data_json  TEXT NOT NULL,   -- JSON blob
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(topic_id, section_idx)
);

-- Per-topic AI summary
CREATE TABLE topic_summaries (
  topic_id   TEXT PRIMARY KEY,
  summary    TEXT NOT NULL,
  chips_json TEXT NOT NULL,   -- JSON array of {label, category}
  created_at TEXT DEFAULT (datetime('now'))
);
```

---

## AI Enrichment JSON Formats

### Timeline
```json
{
  "type": "timeline",
  "data": [
    { "step": 1, "title": "Iniciació", "desc": "A instància de part o d'ofici." },
    { "step": 2, "title": "Instrucció", "desc": "Al·legacions, proves, informes." },
    { "step": 3, "title": "Terminació", "desc": "Resolució motivada o arxivament." }
  ]
}
```

### Concept Cards
```json
{
  "type": "cards",
  "data": [
    { "title": "Administració", "desc": "Inicia, instrueix i resol.", "icon": "building" },
    { "title": "Interessat", "desc": "Qui promou el procediment.", "icon": "user" }
  ]
}
```

Supported icon values: `building`, `user`, `file`, `scale`, `shield`, `clock`, `globe`, `users`, `key`, `flag`

### Comparison Table
```json
{
  "type": "table",
  "data": {
    "headers": ["Forma", "Qui", "Efecte"],
    "rows": [
      ["Resolució", "Administració", "Normal"],
      ["Desistiment", "Interessat", "Abandona l'acció"]
    ],
    "highlight": []
  }
}
```

### Callout Boxes
```json
{
  "type": "callouts",
  "data": [
    { "variant": "law", "title": "Regulació", "text": "Llei 39/2015 (LPACAP)..." },
    { "variant": "important", "title": "Important", "text": "El procediment garanteix..." },
    { "variant": "exam", "title": "Examen", "text": "La LPACAP substitueix les lleis 30/1992..." }
  ]
}
```

Callout variants: `law` (blue), `important` (yellow), `exam` (green)

### Topic Summary Chips
```json
{
  "summary": "El procediment administratiu és...",
  "chips": [
    { "label": "3 fases clau", "category": "concept" },
    { "label": "LPACAP Art. 53", "category": "law" },
    { "label": "Silenci administratiu", "category": "alert" },
    { "label": "Molt probable a l'examen", "category": "exam" }
  ]
}
```

Chip categories: `concept` (blue), `law` (green), `alert` (orange), `exam` (red)

---

## Section Parsing

The existing topic markdown uses `##` headings to delimit sections. The frontend parses the raw markdown into an array of sections before rendering:

```js
// Each section: { index, title, markdown, level }
function parseSections(markdown) {
  const lines = markdown.split('\n')
  const sections = []
  let current = null
  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (current) sections.push(current)
      current = { index: sections.length, title: line.slice(3), markdown: '', level: 2 }
    } else if (current) {
      current.markdown += line + '\n'
    }
  }
  if (current) sections.push(current)
  return sections
}
```

If a topic has no `##` headings, it is treated as a single section.

---

## Reading Progress Tracking

- Progress bar width = `scrollY / (documentHeight - viewportHeight) * 100`
- "Read" state per section: a section is marked read when its bottom edge scrolls past the viewport midpoint
- Read sections are stored in the existing `topic_progress` table (no new DB columns needed — the existing `sections_read` JSON field is used)

---

## Error Handling

- If AI enrichment fails, the section shows a subtle error state with a "Tornar a intentar" link; the original markdown remains visible
- If topic summary generation fails silently (background), no card is shown — no error shown to user
- Rate limit errors from the AI service return HTTP 429; the frontend shows "Límit de IA assolit, torna a intentar en un moment"

---

## What Is NOT in Scope

- No "Visual mode" toggle that replaces the entire topic (option B was rejected)
- No bulk enrichment of all sections at once
- No changes to the markdown source files
- No changes to the practice or exam modes
