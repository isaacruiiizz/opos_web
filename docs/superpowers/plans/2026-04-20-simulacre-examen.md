# Simulacre d'Examen — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afegir un mode "Simulacre d'Examen" a la pestanya Pràctica que genera 40 preguntes mixtes dels 30 temes "importants", amb cronòmetre de 2h, nota /10 i avaluació estricta per IA.

**Architecture:** Un nou router FastAPI (`simulacre.py`) exposa 4 endpoints. La generació fa una sola crida a Groq amb els Flash-Check compactes dels 30 temes (respectant el límit de 6K TPM). L'avaluació de respostes obertes es fa en 1 o 2 lots seqüencials. El frontend té un store Pinia dedicat i 3 nous components Vue.

**Tech Stack:** Python FastAPI + aiosqlite + AsyncGroq | Vue 3 + Pinia + Tailwind CSS + axios

---

## Fitxers nous i modificats

| Fitxer | Acció |
|---|---|
| `backend/services/markdown_parser.py` | Modificar: afegir `extract_flash_check()` |
| `backend/services/gemini.py` | Modificar: afegir `generate_simulacre()` i `evaluate_simulacre_answers()` |
| `backend/database.py` | Modificar: afegir taula `simulacre_results` a `_CREATE_TABLES` |
| `backend/routers/simulacre.py` | Crear: 4 endpoints |
| `backend/main.py` | Modificar: registrar el nou router |
| `frontend/src/api/client.js` | Modificar: afegir 4 funcions API |
| `frontend/src/stores/simulacre.js` | Crear: estat del simulacre |
| `frontend/src/components/practice/SimulacreCard.vue` | Crear: targeta d'inici |
| `frontend/src/views/SimulacreView.vue` | Crear: pantalla completa d'examen |
| `frontend/src/components/practice/SimulacreResults.vue` | Crear: pantalla de resultats |
| `frontend/src/views/PracticaView.vue` | Modificar: afegir SimulacreCard a dalt |
| `frontend/src/router/index.js` | Modificar: afegir ruta `/simulacre` |

---

## Task 1: Extractor de Flash-Check al parser

**Files:**
- Modify: `backend/services/markdown_parser.py`

- [ ] **Step 1: Afegir `extract_flash_check` a markdown_parser.py**

Afegir al final de `backend/services/markdown_parser.py` (després de la funció `get_topic_by_id`):

```python
def extract_flash_check(content: str) -> str:
    """Extreu el text del bloc 'Resum de conceptes clau (Flash-Check)' d'un tema.
    Si no existeix, retorna les primeres 300 chars del contingut."""
    lines = content.splitlines()
    in_flash = False
    result = []
    for line in lines:
        if re.match(r"^#{1,6}\s.*[Ff]lash", line):
            in_flash = True
            continue
        if in_flash:
            if re.match(r"^#{1,6}\s", line):
                break
            result.append(line)
    if result:
        return " ".join(" ".join(result).split())[:400]
    return " ".join(content.split())[:300]
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/markdown_parser.py
git commit -m "feat(backend): add extract_flash_check helper to markdown_parser"
```

---

## Task 2: Taula simulacre_results a la base de dades

**Files:**
- Modify: `backend/database.py`

- [ ] **Step 1: Afegir la nova taula a `_CREATE_TABLES`**

A `backend/database.py`, afegir aquest element a la llista `_CREATE_TABLES` (després de l'últim element, abans del `]`):

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/database.py
git commit -m "feat(db): add simulacre_results table"
```

---

## Task 3: Mètodes IA per al simulacre (gemini.py)

**Files:**
- Modify: `backend/services/gemini.py`

- [ ] **Step 1: Afegir `generate_simulacre` a la classe `GeminiService`**

Afegir després del mètode `generate_buits` (línia ~347):

```python
    async def generate_simulacre(self, temes: list[dict], seed: str) -> list[dict]:
        """Genera 40 preguntes mixtes dels 30 temes importants.
        `temes` és una llista de {"titol": str, "resum": str}
        Dissenyat per mantenir-se dins del límit de 6K TPM de Groq."""
        temes_text = "\n".join(
            f"{i+1}. {t['titol']}: {t['resum']}"
            for i, t in enumerate(temes)
        )
        prompt = (
            "Ets un tribunal d'oposicions públiques per a tècnic C1 d'informàtica en un ajuntament català.\n"
            "La teva tasca és generar EXACTAMENT 40 preguntes d'examen barrejant tres tipus.\n\n"
            "REGLES OBLIGATÒRIES:\n"
            "1. Les preguntes han de cobrir la majoria dels 30 temes (no repeteixis el mateix tema més de 2 vegades).\n"
            "2. INVENTA preguntes que vagin MÉS ENLLÀ dels apunts: aplica els conceptes a situacions reals "
            "d'un ajuntament petit com Maçanet de la Selva. No reprodueixis literalment els apunts.\n"
            "3. Les respostes alternatives han de tenir 3 distractors plausibles (no obviament incorrectes).\n"
            "4. Les preguntes breus requereixen 2-4 frases per respondre correctament.\n"
            "5. Els supòsits pràctics plantegen un cas real concret (incidència TIC, tràmit, decisió tècnica).\n"
            "6. Distribueix: 15-22 tipo test (test), 12-18 respostes breus (breu), 2-5 supòsits (suposit). Total = 40.\n"
            "7. Penalització tipo test: -1/3 punts per resposta incorrecta (indica-ho al camp 'penalitza': true).\n"
            f"8. Usa seed '{seed}' per garantir variació respecte de tests anteriors.\n"
            "9. Respon ÚNICAMENT amb JSON vàlid, sense text addicional, sense markdown.\n\n"
            "FORMAT DE RESPOSTA (array de exactament 40 objectes):\n"
            "[\n"
            "  {\"id\":1,\"tema_num\":3,\"tema_titol\":\"Interoperabilitat\","
            "\"tipus\":\"test\",\"dificultat\":\"mitjana\",\"punts\":0.25,"
            "\"enunciat\":\"...\","
            "\"opcions\":{\"A\":\"...\",\"B\":\"...\",\"C\":\"...\",\"D\":\"...\"},"
            "\"correcta\":\"B\",\"explicacio\":\"...\",\"penalitza\":true},\n"
            "  {\"id\":2,\"tema_num\":7,\"tema_titol\":\"Obligats i notificació\","
            "\"tipus\":\"breu\",\"dificultat\":\"alta\",\"punts\":0.5,"
            "\"enunciat\":\"...\","
            "\"opcions\":null,\"correcta\":null,"
            "\"resposta_model\":\"...\",\"rubrica\":\"Mencionar: X, Y, Z\","
            "\"explicacio\":\"...\",\"penalitza\":false},\n"
            "  {\"id\":3,\"tema_num\":22,\"tema_titol\":\"Cas Pràctic - Diagnòstic d'Errors\","
            "\"tipus\":\"suposit\",\"dificultat\":\"alta\",\"punts\":1.0,"
            "\"enunciat\":\"L'alcaldessa et truca: cap ordinador de l'ajuntament pot imprimir...\","
            "\"opcions\":null,\"correcta\":null,"
            "\"resposta_model\":\"...\",\"rubrica\":\"Valorar: diagnòstic sistemàtic, eines, comunicació\","
            "\"explicacio\":\"...\",\"penalitza\":false}\n"
            "]\n\n"
            f"LLISTA DE 30 TEMES (títol: resum clau):\n{temes_text}"
        )
        result = await self._generate_json(prompt)
        if not isinstance(result, list):
            raise HTTPException(status_code=500, detail="La IA no ha retornat una llista de preguntes.")
        # Valida estructura mínima
        valid = []
        for q in result:
            if isinstance(q, dict) and "id" in q and "tipus" in q and "enunciat" in q:
                valid.append(q)
        if len(valid) < 20:
            raise HTTPException(status_code=500, detail=f"La IA ha retornat massa poques preguntes vàlides ({len(valid)}/40).")
        return valid

    async def evaluate_simulacre_answers(self, answers: list[dict]) -> list[dict]:
        """Avalua respostes obertes (breu i suposit).
        `answers` és una llista de {"id": int, "enunciat": str, "resposta_usuari": str,
                                     "resposta_model": str, "rubrica": str, "punts": float}
        Si hi ha >10 respostes, fa 2 crides seqüencials amb 15s de delay per respectar 6K TPM."""
        if not answers:
            return []

        async def _evaluate_batch(batch: list[dict]) -> list[dict]:
            items_text = "\n\n".join(
                f"PREGUNTA {a['id']}: {a['enunciat']}\n"
                f"RÚBRICA: {a['rubrica']}\n"
                f"RESPOSTA MODEL: {a['resposta_model']}\n"
                f"RESPOSTA USUARI: {a['resposta_usuari']}"
                for a in batch
            )
            prompt = (
                "Ets un corrector estricte d'oposicions públiques per a tècnic C1 d'informàtica.\n"
                "Avalua CADASCUNA de les respostes de l'usuari seguint la rúbrica.\n\n"
                "CRITERIS D'AVALUACIÓ:\n"
                "- 0.0: Resposta absent, incorrecta o completament fora de tema.\n"
                "- 0.5: Resposta parcial. Menciona alguns conceptes clau però li falten elements essencials.\n"
                "- 1.0: Resposta correcta. Menciona els conceptes clau de la rúbrica amb coherència.\n"
                "NO atribueixis a l'usuari conceptes que no hagi escrit explícitament.\n"
                "Si la resposta és buida o d'1-2 paraules genèriques, la puntuació és 0.0.\n\n"
                "Respon ÚNICAMENT amb JSON vàlid, sense text addicional:\n"
                "[{\"id\":1,\"factor\":0.5,\"encerts\":[\"concepte mencionat\"],"
                "\"mancances\":[\"concepte que faltava\"],\"comentari\":\"...\"}]\n\n"
                f"RESPOSTES A AVALUAR:\n{items_text}"
            )
            result = await self._generate_json(prompt)
            if not isinstance(result, list):
                return [{"id": a["id"], "factor": 0.0, "encerts": [], "mancances": [], "comentari": "Error d'avaluació"} for a in batch]
            return result

        if len(answers) <= 10:
            return await _evaluate_batch(answers)

        # Dos lots seqüencials amb delay per respectar 6K TPM
        lot1 = answers[:10]
        lot2 = answers[10:]
        results1 = await _evaluate_batch(lot1)
        await asyncio.sleep(15)
        results2 = await _evaluate_batch(lot2)
        return results1 + results2
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/gemini.py
git commit -m "feat(ai): add generate_simulacre and evaluate_simulacre_answers methods"
```

---

## Task 4: Router del simulacre

**Files:**
- Create: `backend/routers/simulacre.py`

- [ ] **Step 1: Crear `backend/routers/simulacre.py`**

```python
import os
import random
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from services.gemini import get_gemini
from services.markdown_parser import get_topics, extract_flash_check

router = APIRouter(tags=["simulacre"])

_default_notes = str(Path(__file__).parent.parent.parent / "data" / "ApuntsTemari.md")
NOTES_PATH = Path(os.getenv("NOTES_PATH", _default_notes))


def _get_importants_temes() -> list[dict]:
    all_topics = get_topics(NOTES_PATH)
    importants = [t for t in all_topics if t["bloc"] == "importants"]
    if not importants:
        raise HTTPException(404, detail="No s'han trobat els temes 'importants'.")
    return [
        {"titol": t["title"], "resum": extract_flash_check(t["content"])}
        for t in importants
    ]


class EvaluateBody(BaseModel):
    answers: list[dict]


class SaveBody(BaseModel):
    score: float
    passed: bool
    time_taken_seconds: int
    q_test_correct: int
    q_test_total: int
    q_breus_score: float
    q_breus_total: float
    q_suposit_score: float
    q_suposit_total: float


@router.post("/api/simulacre/generate")
async def generate_simulacre():
    temes = _get_importants_temes()
    seed = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
    questions = await get_gemini().generate_simulacre(temes, seed)
    # Barreja les preguntes i reassigna ids
    random.shuffle(questions)
    for i, q in enumerate(questions):
        q["id"] = i + 1
    return {"questions": questions, "total": len(questions)}


@router.post("/api/simulacre/evaluate")
async def evaluate_simulacre(body: EvaluateBody):
    if not body.answers:
        return {"evaluations": []}
    evaluations = await get_gemini().evaluate_simulacre_answers(body.answers)
    return {"evaluations": evaluations}


@router.post("/api/simulacre/save")
async def save_simulacre(body: SaveBody, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO simulacre_results "
        "(score, passed, time_taken_seconds, q_test_correct, q_test_total, "
        "q_breus_score, q_breus_total, q_suposit_score, q_suposit_total) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (body.score, int(body.passed), body.time_taken_seconds,
         body.q_test_correct, body.q_test_total,
         body.q_breus_score, body.q_breus_total,
         body.q_suposit_score, body.q_suposit_total)
    )
    return {"ok": True}


@router.get("/api/simulacre/last")
async def get_last_simulacre(db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT * FROM simulacre_results ORDER BY id DESC LIMIT 1"
    )
    row = await cursor.fetchone()
    if not row:
        return None
    return dict(row)
```

- [ ] **Step 2: Commit**

```bash
git add backend/routers/simulacre.py
git commit -m "feat(backend): add simulacre router with generate/evaluate/save/last endpoints"
```

---

## Task 5: Registrar el router a main.py

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Importar i registrar el router**

A `backend/main.py`, afegir la importació al bloc d'imports (línia ~11):

```python
from routers import simulacre as simulacre_router
```

I afegir la línia de registre al final dels `app.include_router(...)` (després de l'últim):

```python
app.include_router(simulacre_router.router)
```

- [ ] **Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat(backend): register simulacre router in main"
```

---

## Task 6: API calls al client.js

**Files:**
- Modify: `frontend/src/api/client.js`

- [ ] **Step 1: Afegir les 4 funcions al final de `client.js`**

```javascript
export const generateSimulacre = async () => (await api.post('/simulacre/generate')).data
export const evaluateSimulacre = async (answers) => (await api.post('/simulacre/evaluate', { answers })).data
export const saveSimulacre = async (payload) => (await api.post('/simulacre/save', payload)).data
export const fetchLastSimulacre = async () => (await api.get('/simulacre/last')).data
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/client.js
git commit -m "feat(frontend): add simulacre API client functions"
```

---

## Task 7: Store Pinia del simulacre

**Files:**
- Create: `frontend/src/stores/simulacre.js`

- [ ] **Step 1: Crear `frontend/src/stores/simulacre.js`**

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { generateSimulacre, evaluateSimulacre, saveSimulacre, fetchLastSimulacre } from '../api/client.js'

const STORAGE_KEY = 'opos_simulacre_v1'

function loadDraft() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

function saveDraft(data) {
  try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data)) } catch {}
}

function clearDraft() {
  try { sessionStorage.removeItem(STORAGE_KEY) } catch {}
}

export const useSimulacreStore = defineStore('simulacre', () => {
  const questions = ref([])
  const answers = ref({})        // { questionId: { value, correct, points_earned } }
  const timeRemaining = ref(7200) // 2h en segons
  const generating = ref(false)
  const evaluating = ref(false)
  const error = ref(null)
  const results = ref(null)      // resultat final un cop avaluat
  const lastResult = ref(null)   // últim resultat desat a BD
  const phase = ref('idle')      // 'idle' | 'exam' | 'evaluating' | 'results'

  const totalQuestions = computed(() => questions.value.length)
  const answeredCount = computed(() => Object.keys(answers.value).length)
  const testQuestions = computed(() => questions.value.filter(q => q.tipus === 'test'))
  const openQuestions = computed(() => questions.value.filter(q => q.tipus !== 'test'))

  async function loadLastResult() {
    try {
      lastResult.value = await fetchLastSimulacre()
    } catch {}
  }

  async function startGeneration() {
    // Comprova si hi ha un examen en curs desat
    const draft = loadDraft()
    if (draft && draft.questions && draft.timeRemaining > 0) {
      questions.value = draft.questions
      answers.value = draft.answers || {}
      timeRemaining.value = draft.timeRemaining
      phase.value = 'exam'
      return
    }

    generating.value = true
    error.value = null
    try {
      const data = await generateSimulacre()
      questions.value = data.questions
      answers.value = {}
      timeRemaining.value = 7200
      phase.value = 'exam'
      persistDraft()
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error generant el simulacre. Torna a intentar-ho.'
    } finally {
      generating.value = false
    }
  }

  function answerTest(questionId, optionKey) {
    const q = questions.value.find(q => q.id === questionId)
    if (!q || answers.value[questionId]) return // no es pot canviar
    const correct = optionKey === q.correcta
    const points_earned = correct ? q.punts : (q.penalitza ? -(q.punts / 3) : 0)
    answers.value = {
      ...answers.value,
      [questionId]: { value: optionKey, correct, points_earned }
    }
    persistDraft()
  }

  function answerOpen(questionId, text) {
    answers.value = {
      ...answers.value,
      [questionId]: { value: text, correct: null, points_earned: null }
    }
    persistDraft()
  }

  function persistDraft() {
    saveDraft({
      questions: questions.value,
      answers: answers.value,
      timeRemaining: timeRemaining.value,
    })
  }

  function tickTimer() {
    if (timeRemaining.value > 0) {
      timeRemaining.value--
      if (timeRemaining.value % 30 === 0) persistDraft() // guarda cada 30s
    }
  }

  async function submitExam() {
    phase.value = 'evaluating'
    evaluating.value = true
    error.value = null

    // Calcula punts de tipo test
    let testCorrect = 0
    let testTotal = 0
    let testPoints = 0
    let testMaxPoints = 0

    for (const q of testQuestions.value) {
      const ans = answers.value[q.id]
      testTotal++
      testMaxPoints += q.punts
      if (ans) {
        testPoints += ans.points_earned
        if (ans.correct) testCorrect++
      }
    }

    // Prepara respostes obertes per avaluar
    const openAnswers = openQuestions.value.map(q => ({
      id: q.id,
      enunciat: q.enunciat,
      resposta_usuari: answers.value[q.id]?.value || '',
      resposta_model: q.resposta_model || '',
      rubrica: q.rubrica || '',
      punts: q.punts,
    }))

    let evaluations = []
    try {
      const data = await evaluateSimulacre(openAnswers)
      evaluations = data.evaluations || []
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error avaluant les respostes. Torna a intentar-ho.'
      phase.value = 'exam'
      evaluating.value = false
      return
    }

    // Calcula punts de respostes obertes
    let breusScore = 0
    let breusTotal = 0
    let supositScore = 0
    let supositTotal = 0

    const evalMap = {}
    for (const ev of evaluations) evalMap[ev.id] = ev

    for (const q of openQuestions.value) {
      const ev = evalMap[q.id]
      const factor = ev ? ev.factor : 0
      const earned = q.punts * factor
      if (q.tipus === 'breu') {
        breusScore += earned
        breusTotal += q.punts
      } else {
        supositScore += earned
        supositTotal += q.punts
      }
      // Actualitza answers amb la puntuació real
      if (answers.value[q.id]) {
        answers.value[q.id].points_earned = earned
        answers.value[q.id].evaluation = ev
      }
    }

    const totalEarned = testPoints + breusScore + supositScore
    const totalMax = testMaxPoints + breusTotal + supositTotal
    const score = totalMax > 0 ? Math.round((totalEarned / totalMax) * 100) / 10 : 0
    const passed = score >= 5.0
    const timeTaken = 7200 - timeRemaining.value

    results.value = {
      score,
      passed,
      timeTaken,
      testCorrect,
      testTotal,
      breusScore: Math.round(breusScore * 100) / 100,
      breusTotal: Math.round(breusTotal * 100) / 100,
      supositScore: Math.round(supositScore * 100) / 100,
      supositTotal: Math.round(supositTotal * 100) / 100,
      questions: questions.value,
      answers: answers.value,
    }

    // Desa a BD
    try {
      await saveSimulacre({
        score,
        passed,
        time_taken_seconds: timeTaken,
        q_test_correct: testCorrect,
        q_test_total: testTotal,
        q_breus_score: breusScore,
        q_breus_total: breusTotal,
        q_suposit_score: supositScore,
        q_suposit_total: supositTotal,
      })
      lastResult.value = { score, passed, date: new Date().toISOString() }
    } catch {}

    clearDraft()
    phase.value = 'results'
    evaluating.value = false
  }

  function reset() {
    questions.value = []
    answers.value = {}
    timeRemaining.value = 7200
    results.value = null
    error.value = null
    phase.value = 'idle'
    clearDraft()
  }

  return {
    questions, answers, timeRemaining, generating, evaluating, error,
    results, lastResult, phase,
    totalQuestions, answeredCount, testQuestions, openQuestions,
    loadLastResult, startGeneration, answerTest, answerOpen,
    tickTimer, submitExam, reset, persistDraft,
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/stores/simulacre.js
git commit -m "feat(store): add simulacre Pinia store with timer, answers and evaluation logic"
```

---

## Task 8: SimulacreCard.vue — Targeta d'inici

**Files:**
- Create: `frontend/src/components/practice/SimulacreCard.vue`

- [ ] **Step 1: Crear `frontend/src/components/practice/SimulacreCard.vue`**

```vue
<template>
  <div class="mx-4 mt-4 mb-2 rounded-xl border-2 border-amber-400 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-500 p-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <span class="text-lg">🎯</span>
          <h2 class="font-bold text-amber-900 dark:text-amber-300 text-sm">Simulacre d'Examen Oficial</h2>
        </div>
        <p class="text-xs text-amber-700 dark:text-amber-400">40 preguntes · 2 hores · Nota /10 · Mínim 5 per aprovar</p>
        <p class="text-xs text-amber-600 dark:text-amber-500 mt-0.5">Temes "a tenir en compte" (30 temes)</p>
      </div>

      <div v-if="lastResult" class="text-right shrink-0">
        <div class="text-sm font-bold" :class="lastResult.passed ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'">
          {{ lastResult.score?.toFixed(1) }}/10
        </div>
        <div class="text-xs" :class="lastResult.passed ? 'text-green-600' : 'text-red-500'">
          {{ lastResult.passed ? '✓ Aprovat' : '✗ Suspès' }}
        </div>
      </div>
    </div>

    <div v-if="hasDraft" class="mt-3 p-2 bg-amber-100 dark:bg-amber-900/40 rounded-lg text-xs text-amber-800 dark:text-amber-300">
      ⚠️ Tens un examen en curs desat. En iniciar, el reprendràs.
    </div>

    <button
      @click="$emit('start')"
      :disabled="generating"
      class="mt-3 w-full py-2.5 rounded-lg font-semibold text-sm transition-all"
      :class="generating
        ? 'bg-amber-200 dark:bg-amber-900 text-amber-500 cursor-not-allowed'
        : 'bg-amber-500 hover:bg-amber-600 text-white active:scale-95'"
    >
      <span v-if="generating" class="flex items-center justify-center gap-2">
        <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        Generant preguntes…
      </span>
      <span v-else>{{ hasDraft ? 'Reprendre Simulacre' : 'Iniciar Simulacre' }}</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  lastResult: { type: Object, default: null },
  generating: { type: Boolean, default: false },
  hasDraft: { type: Boolean, default: false },
})
defineEmits(['start'])
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/practice/SimulacreCard.vue
git commit -m "feat(ui): add SimulacreCard component"
```

---

## Task 9: SimulacreView.vue — Pantalla d'examen

**Files:**
- Create: `frontend/src/views/SimulacreView.vue`

- [ ] **Step 1: Crear `frontend/src/views/SimulacreView.vue`**

```vue
<template>
  <div class="flex flex-col h-screen bg-[var(--color-bg)]">
    <!-- Navbar fixa d'examen -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] shrink-0">
      <div class="text-sm font-medium text-[var(--color-text)]">
        Pregunta <span class="font-bold text-primary">{{ currentIdx + 1 }}</span>/{{ simulacre.totalQuestions }}
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs px-2 py-0.5 rounded-full font-mono font-bold"
              :class="timeRemaining < 900 ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400' : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'">
          ⏱ {{ formattedTime }}
        </span>
        <button @click="showIndex = true" class="text-xs text-primary underline">Índex</button>
      </div>
    </div>

    <!-- Pregunta actual -->
    <div class="flex-1 overflow-y-auto px-4 py-4">
      <div v-if="currentQ">
        <!-- Capçalera de la pregunta -->
        <div class="flex items-center gap-2 mb-3">
          <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                :class="{
                  'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300': currentQ.tipus === 'test',
                  'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300': currentQ.tipus === 'breu',
                  'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300': currentQ.tipus === 'suposit',
                }">
            {{ { test: 'Tipus test', breu: 'Resposta breu', suposit: 'Supòsit pràctic' }[currentQ.tipus] }}
          </span>
          <span class="text-xs text-[var(--color-text-muted)]">{{ currentQ.tema_titol }} · {{ currentQ.punts }} pts</span>
          <span class="text-xs px-1.5 py-0.5 rounded text-[var(--color-text-muted)]"
                :class="{
                  'bg-green-50 dark:bg-green-900/20': currentQ.dificultat === 'baixa',
                  'bg-yellow-50 dark:bg-yellow-900/20': currentQ.dificultat === 'mitjana',
                  'bg-red-50 dark:bg-red-900/20': currentQ.dificultat === 'alta',
                }">
            {{ currentQ.dificultat }}
          </span>
        </div>

        <!-- Enunciat -->
        <p class="text-sm font-medium text-[var(--color-text)] mb-4 leading-relaxed">{{ currentQ.enunciat }}</p>

        <!-- Opcions tipus test -->
        <div v-if="currentQ.tipus === 'test'" class="space-y-2">
          <button v-for="(text, key) in currentQ.opcions" :key="key"
                  @click="answerTest(key)"
                  :disabled="!!currentAnswer"
                  class="w-full text-left px-4 py-3 rounded-lg border text-sm transition-all"
                  :class="getOptionClass(key)">
            <span class="font-bold mr-2">{{ key }})</span>{{ text }}
          </button>

          <!-- Explicació post-resposta -->
          <div v-if="currentAnswer" class="mt-3 p-3 rounded-lg text-xs"
               :class="currentAnswer.correct ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300' : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300'">
            <span class="font-bold">{{ currentAnswer.correct ? '✓ Correcte!' : '✗ Incorrecte.' }}</span>
            {{ currentQ.explicacio }}
          </div>
        </div>

        <!-- Resposta breu o supòsit -->
        <div v-else>
          <textarea
            :value="currentAnswer?.value || ''"
            @input="answerOpen($event.target.value)"
            :placeholder="currentQ.tipus === 'suposit' ? 'Descriu el teu procediment de diagnòstic i resolució…' : 'Escriu la teva resposta…'"
            class="w-full h-36 px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] resize-none focus:outline-none focus:border-primary"
          />
          <p class="text-xs text-[var(--color-text-muted)] mt-1">Resposta guardada automàticament</p>
        </div>
      </div>
    </div>

    <!-- Botons de navegació -->
    <div class="shrink-0 px-4 py-3 border-t border-[var(--color-border)] bg-[var(--color-surface)] flex gap-2">
      <button @click="prev" :disabled="currentIdx === 0"
              class="flex-1 py-2.5 rounded-lg text-sm font-medium border border-[var(--color-border)] disabled:opacity-40 active:scale-95 transition-all">
        ← Anterior
      </button>
      <button v-if="currentIdx < simulacre.totalQuestions - 1" @click="next"
              class="flex-1 py-2.5 rounded-lg text-sm font-medium bg-primary text-white active:scale-95 transition-all">
        Següent →
      </button>
      <button v-else @click="confirmSubmit"
              class="flex-1 py-2.5 rounded-lg text-sm font-bold bg-amber-500 text-white active:scale-95 transition-all">
        Finalitzar
      </button>
    </div>

    <!-- Modal índex de preguntes -->
    <div v-if="showIndex" class="fixed inset-0 bg-black/50 z-50 flex items-end" @click.self="showIndex = false">
      <div class="bg-[var(--color-surface)] w-full rounded-t-2xl p-4 max-h-[60vh] overflow-y-auto">
        <h3 class="font-bold text-sm mb-3 text-[var(--color-text)]">Índex de preguntes</h3>
        <div class="grid grid-cols-8 gap-1.5">
          <button v-for="q in simulacre.questions" :key="q.id"
                  @click="goTo(q.id - 1); showIndex = false"
                  class="aspect-square rounded text-xs font-medium flex items-center justify-center transition-all"
                  :class="getIndexClass(q)">
            {{ q.id }}
          </button>
        </div>
        <div class="flex gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
          <span><span class="inline-block w-3 h-3 rounded bg-green-400 mr-1"></span>Correcta</span>
          <span><span class="inline-block w-3 h-3 rounded bg-red-400 mr-1"></span>Incorrecta</span>
          <span><span class="inline-block w-3 h-3 rounded bg-blue-400 mr-1"></span>Resposta</span>
          <span><span class="inline-block w-3 h-3 rounded bg-gray-200 dark:bg-gray-700 mr-1"></span>Pendent</span>
        </div>
      </div>
    </div>

    <!-- Modal confirmació finalitzar -->
    <div v-if="showConfirm" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center px-6">
      <div class="bg-[var(--color-surface)] rounded-2xl p-6 w-full max-w-sm">
        <h3 class="font-bold text-base mb-2 text-[var(--color-text)]">Finalitzar examen?</h3>
        <p class="text-sm text-[var(--color-text-muted)] mb-4">
          Has respost {{ simulacre.answeredCount }}/{{ simulacre.totalQuestions }} preguntes.
          <span v-if="simulacre.answeredCount < simulacre.totalQuestions" class="text-amber-600 font-medium">
            {{ simulacre.totalQuestions - simulacre.answeredCount }} preguntes sense respondre.
          </span>
        </p>
        <div class="flex gap-3">
          <button @click="showConfirm = false" class="flex-1 py-2.5 rounded-lg border text-sm font-medium border-[var(--color-border)]">Cancel·la</button>
          <button @click="doSubmit" class="flex-1 py-2.5 rounded-lg bg-amber-500 text-white text-sm font-bold">Enviar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulacreStore } from '../stores/simulacre.js'

const router = useRouter()
const simulacre = useSimulacreStore()

const currentIdx = ref(0)
const showIndex = ref(false)
const showConfirm = ref(false)
let timerInterval = null

const currentQ = computed(() => simulacre.questions[currentIdx.value] || null)
const currentAnswer = computed(() => currentQ.value ? simulacre.answers[currentQ.value.id] : null)
const timeRemaining = computed(() => simulacre.timeRemaining)

const formattedTime = computed(() => {
  const t = simulacre.timeRemaining
  const h = Math.floor(t / 3600)
  const m = Math.floor((t % 3600) / 60)
  const s = t % 60
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

onMounted(() => {
  if (simulacre.phase !== 'exam') {
    router.replace('/practica')
    return
  }
  timerInterval = setInterval(() => {
    simulacre.tickTimer()
    if (simulacre.timeRemaining === 0) {
      clearInterval(timerInterval)
      doSubmit()
    }
  }, 1000)
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})

function prev() { if (currentIdx.value > 0) currentIdx.value-- }
function next() { if (currentIdx.value < simulacre.totalQuestions - 1) currentIdx.value++ }
function goTo(idx) { currentIdx.value = idx }

function answerTest(key) {
  if (!currentQ.value || simulacre.answers[currentQ.value.id]) return
  simulacre.answerTest(currentQ.value.id, key)
}

function answerOpen(text) {
  if (!currentQ.value) return
  simulacre.answerOpen(currentQ.value.id, text)
}

function confirmSubmit() { showConfirm.value = true }

async function doSubmit() {
  showConfirm.value = false
  if (timerInterval) clearInterval(timerInterval)
  await simulacre.submitExam()
  if (simulacre.phase === 'results') {
    router.push('/simulacre/resultats')
  }
}

function getOptionClass(key) {
  const ans = currentAnswer.value
  if (!ans) {
    return 'border-[var(--color-border)] hover:border-primary hover:bg-primary/5 active:scale-98'
  }
  if (key === currentQ.value.correcta) return 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300'
  if (key === ans.value && !ans.correct) return 'border-red-400 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300'
  return 'border-[var(--color-border)] opacity-50'
}

function getIndexClass(q) {
  const ans = simulacre.answers[q.id]
  if (!ans) return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
  if (q.tipus === 'test') {
    return ans.correct ? 'bg-green-400 text-white' : 'bg-red-400 text-white'
  }
  return ans.value ? 'bg-blue-400 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600'
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/SimulacreView.vue
git commit -m "feat(ui): add SimulacreView exam screen with timer and question navigation"
```

---

## Task 10: SimulacreResults.vue — Pantalla de resultats

**Files:**
- Create: `frontend/src/components/practice/SimulacreResults.vue`

- [ ] **Step 1: Crear `frontend/src/components/practice/SimulacreResults.vue`**

Crear el fitxer `frontend/src/components/practice/SimulacreResults.vue`:

```vue
<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <!-- Resultat principal -->
    <div class="text-center mb-6">
      <div class="text-5xl font-bold mb-1"
           :class="results.passed ? 'text-green-500' : 'text-red-500'">
        {{ results.score.toFixed(1) }}
        <span class="text-2xl text-[var(--color-text-muted)]">/10</span>
      </div>
      <div class="text-lg font-semibold mb-2"
           :class="results.passed ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'">
        {{ results.passed ? '✓ APROVAT' : '✗ SUSPÈS' }}
      </div>
      <div class="text-sm text-[var(--color-text-muted)]">Temps: {{ formattedTime }}</div>

      <!-- Barra de progrés -->
      <div class="mt-3 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div class="h-full rounded-full transition-all duration-1000"
             :class="results.passed ? 'bg-green-500' : 'bg-red-500'"
             :style="{ width: `${Math.min(results.score * 10, 100)}%` }" />
      </div>
      <div class="flex justify-between text-xs text-[var(--color-text-muted)] mt-1">
        <span>0</span>
        <span class="font-medium text-amber-600">5 (mínim)</span>
        <span>10</span>
      </div>
    </div>

    <!-- Desglossament -->
    <div class="space-y-2 mb-6">
      <div class="flex items-center justify-between p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
        <span class="text-sm font-medium text-blue-800 dark:text-blue-300">🔵 Tipo test</span>
        <span class="text-sm font-bold text-blue-800 dark:text-blue-300">
          {{ results.testCorrect }}/{{ results.testTotal }} correctes
        </span>
      </div>
      <div class="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
        <span class="text-sm font-medium text-green-800 dark:text-green-300">🟢 Respostes breus</span>
        <span class="text-sm font-bold text-green-800 dark:text-green-300">
          {{ results.breusScore }}/{{ results.breusTotal }} punts
        </span>
      </div>
      <div class="flex items-center justify-between p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
        <span class="text-sm font-medium text-purple-800 dark:text-purple-300">🟣 Supòsits pràctics</span>
        <span class="text-sm font-bold text-purple-800 dark:text-purple-300">
          {{ results.supositScore }}/{{ results.supositTotal }} punts
        </span>
      </div>
    </div>

    <!-- Botons principals -->
    <div class="flex gap-3 mb-6">
      <button @click="showDetail = !showDetail"
              class="flex-1 py-2.5 rounded-lg border text-sm font-medium border-[var(--color-border)] text-[var(--color-text)]">
        {{ showDetail ? 'Amaga' : 'Veure' }} correcció
      </button>
      <button @click="$emit('new-exam')"
              class="flex-1 py-2.5 rounded-lg bg-amber-500 text-white text-sm font-bold">
        Nou simulacre
      </button>
    </div>

    <!-- Correcció detallada -->
    <div v-if="showDetail" class="space-y-4">
      <h3 class="font-bold text-sm text-[var(--color-text)]">Correcció detallada</h3>
      <div v-for="q in results.questions" :key="q.id" class="rounded-lg border border-[var(--color-border)] overflow-hidden">
        <div class="px-3 py-2 text-xs font-medium flex items-center gap-2"
             :class="getQuestionHeaderClass(q)">
          <span>P{{ q.id }}.</span>
          <span class="opacity-70">{{ q.tema_titol }}</span>
          <span class="ml-auto">{{ getQuestionScore(q) }}</span>
        </div>
        <div class="px-3 py-2">
          <p class="text-xs text-[var(--color-text)] mb-2">{{ q.enunciat }}</p>

          <!-- Tipo test -->
          <template v-if="q.tipus === 'test'">
            <div class="text-xs">
              <span class="font-medium">Resposta correcta: </span>
              <span class="text-green-600 dark:text-green-400 font-bold">{{ q.correcta }}) {{ q.opcions?.[q.correcta] }}</span>
            </div>
            <div v-if="results.answers[q.id]?.value !== q.correcta && results.answers[q.id]" class="text-xs mt-1">
              <span class="font-medium">La teva resposta: </span>
              <span class="text-red-500">{{ results.answers[q.id].value }}) {{ q.opcions?.[results.answers[q.id].value] }}</span>
            </div>
          </template>

          <!-- Breu / Supòsit -->
          <template v-else>
            <div class="text-xs mb-1">
              <span class="font-medium">La teva resposta: </span>
              <span class="italic text-[var(--color-text-muted)]">
                {{ results.answers[q.id]?.value || '(sense resposta)' }}
              </span>
            </div>
            <div v-if="results.answers[q.id]?.evaluation" class="text-xs mt-1 p-2 rounded bg-gray-50 dark:bg-gray-800">
              <div class="font-medium mb-0.5">Comentari IA:</div>
              {{ results.answers[q.id].evaluation.comentari }}
              <div v-if="results.answers[q.id].evaluation.mancances?.length" class="mt-1 text-amber-600 dark:text-amber-400">
                Faltava mencionar: {{ results.answers[q.id].evaluation.mancances.join(', ') }}
              </div>
            </div>
          </template>

          <p class="text-xs text-[var(--color-text-muted)] mt-1 italic">{{ q.explicacio }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ results: { type: Object, required: true } })
defineEmits(['new-exam'])

const showDetail = ref(false)

const formattedTime = computed(() => {
  const t = props.results.timeTaken
  const h = Math.floor(t / 3600)
  const m = Math.floor((t % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
})

function getQuestionHeaderClass(q) {
  const ans = props.results.answers[q.id]
  if (!ans) return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
  if (q.tipus === 'test') {
    return ans.correct
      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
  }
  const factor = ans.evaluation?.factor ?? 0
  if (factor >= 1) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
  if (factor >= 0.5) return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
  return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
}

function getQuestionScore(q) {
  const ans = props.results.answers[q.id]
  if (!ans) return '—'
  const earned = ans.points_earned ?? 0
  return `${earned >= 0 ? '+' : ''}${earned.toFixed(2)} pts`
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/practice/SimulacreResults.vue
git commit -m "feat(ui): add SimulacreResults component with detailed correction"
```

---

## Task 11: Vista de resultats i router

**Files:**
- Create: `frontend/src/views/SimulacreResultsView.vue`
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: Crear `frontend/src/views/SimulacreResultsView.vue`**

```vue
<template>
  <div>
    <div v-if="simulacre.phase === 'evaluating'" class="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <svg class="animate-spin h-10 w-10 text-amber-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
      <p class="text-sm text-[var(--color-text-muted)]">Avaluant respostes amb IA…</p>
    </div>
    <div v-else-if="simulacre.results">
      <SimulacreResults :results="simulacre.results" @new-exam="startNew" />
    </div>
    <div v-else class="text-center py-12 text-[var(--color-text-muted)] text-sm">
      No hi ha cap resultat. <router-link to="/practica" class="text-primary underline">Torna a Pràctica</router-link>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useSimulacreStore } from '../stores/simulacre.js'
import SimulacreResults from '../components/practice/SimulacreResults.vue'

const router = useRouter()
const simulacre = useSimulacreStore()

function startNew() {
  simulacre.reset()
  router.push('/practica')
}
</script>
```

- [ ] **Step 2: Afegir les rutes a `frontend/src/router/index.js`**

Substituir el contingut de `frontend/src/router/index.js`:

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/apunts' },
  { path: '/apunts', component: () => import('../views/ApuntsView.vue') },
  { path: '/flash', component: () => import('../views/FlashcardsView.vue') },
  { path: '/practica', component: () => import('../views/PracticaView.vue') },
  { path: '/simulacre', component: () => import('../views/SimulacreView.vue') },
  { path: '/simulacre/resultats', component: () => import('../views/SimulacreResultsView.vue') },
  { path: '/progres', component: () => import('../views/ProgresView.vue') },
  { path: '/config', component: () => import('../views/SettingsView.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/SimulacreResultsView.vue frontend/src/router/index.js
git commit -m "feat(router): add /simulacre and /simulacre/resultats routes"
```

---

## Task 12: Integrar SimulacreCard a PracticaView

**Files:**
- Modify: `frontend/src/views/PracticaView.vue`

- [ ] **Step 1: Modificar `frontend/src/views/PracticaView.vue`**

Substituir el contingut complet del fitxer:

```vue
<template>
  <div>
    <!-- Simulacre d'Examen (sempre a dalt, independent del tema) -->
    <SimulacreCard
      :last-result="simulacre.lastResult"
      :generating="simulacre.generating"
      :has-draft="hasDraft"
      @start="startSimulacre"
    />

    <!-- Divisor -->
    <div class="flex items-center gap-3 px-4 py-2">
      <div class="flex-1 h-px bg-[var(--color-border)]"></div>
      <span class="text-xs text-[var(--color-text-muted)] font-medium">Pràctica per tema</span>
      <div class="flex-1 h-px bg-[var(--color-border)]"></div>
    </div>

    <!-- Selector de tema -->
    <div class="overflow-x-auto flex gap-2 px-4 py-2 border-b border-[var(--color-border)]">
      <button v-for="t in topics.topics" :key="t.id"
              @click="activeTopic = t.id"
              :class="activeTopic === t.id ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap">
        T{{ t.number }}
      </button>
    </div>

    <ModeSelector v-if="!activeMode"
                  :progress="modeProgress"
                  :generating="modeGenerating"
                  :ready="modeReady"
                  :errors="modeErrors"
                  @select="startMode" />
    <TestMode v-else-if="activeMode === 'test' && questions.length"
              :questions="questions" :topic-id="activeTopic"
              @done="finishSession" @cancel="cancelMode" />
    <BreusMode v-else-if="activeMode === 'breus' && questions.length"
               :questions="questions" :topic-id="activeTopic"
               @done="finishSession" @cancel="cancelMode" />
    <SupositMode v-else-if="activeMode === 'suposit' && suposit"
                 :suposit="suposit" :topic-id="activeTopic"
                 @done="finishSession" @cancel="cancelMode" />
    <ConnectaMode v-else-if="activeMode === 'connecta' && questions.length"
                  :pairs="questions" :topic-id="activeTopic"
                  @done="finishSession" @cancel="cancelMode" />
    <BuitsMode v-else-if="activeMode === 'buits' && questions.length"
               :sentences="questions" :topic-id="activeTopic"
               @done="finishSession" @cancel="cancelMode" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTopicsStore } from '../stores/topics.js'
import { usePracticeStore } from '../stores/practice.js'
import { useSimulacreStore } from '../stores/simulacre.js'
import { saveSession } from '../api/client.js'
import SimulacreCard from '../components/practice/SimulacreCard.vue'
import ModeSelector from '../components/practice/ModeSelector.vue'
import TestMode from '../components/practice/TestMode.vue'
import BreusMode from '../components/practice/BreusMode.vue'
import SupositMode from '../components/practice/SupositMode.vue'
import ConnectaMode from '../components/practice/ConnectaMode.vue'
import BuitsMode from '../components/practice/BuitsMode.vue'

const MODES = ['test', 'breus', 'suposit', 'connecta', 'buits']

const router = useRouter()
const topics = useTopicsStore()
const practice = usePracticeStore()
const simulacre = useSimulacreStore()

const activeTopic = ref(topics.activeTopicId)
const activeMode = ref(null)
const questions = ref([])
const suposit = ref(null)

const hasDraft = computed(() => {
  try {
    const raw = sessionStorage.getItem('opos_simulacre_v1')
    if (!raw) return false
    const draft = JSON.parse(raw)
    return !!(draft?.questions?.length && draft?.timeRemaining > 0)
  } catch { return false }
})

const modeGenerating = computed(() => {
  return Object.fromEntries(MODES.map(m => [m, practice.isGenerating(activeTopic.value, m)]))
})
const modeReady = computed(() => {
  return Object.fromEntries(MODES.map(m => [m, practice.isReady(activeTopic.value, m)]))
})
const modeProgress = computed(() => practice.getProgress(activeTopic.value))
const modeErrors = computed(() => {
  return Object.fromEntries(
    MODES.map(m => [m, practice.getError(activeTopic.value, m)]).filter(([, v]) => v)
  )
})

// Carrega l'últim resultat del simulacre en muntar la vista
simulacre.loadLastResult()

async function startSimulacre() {
  await simulacre.startGeneration()
  if (simulacre.phase === 'exam') {
    router.push('/simulacre')
  }
}

async function startMode(mode) {
  await practice.requestNotifications()
  practice.clearError(activeTopic.value, mode)

  const content = practice.getContent(activeTopic.value, mode)
  if (content) {
    practice.markSeen(activeTopic.value, mode)
    activeMode.value = mode
    if (mode === 'suposit') suposit.value = content
    else questions.value = content
    return
  }

  if (practice.isGenerating(activeTopic.value, mode)) return

  practice.generate(activeTopic.value, mode)
}

function cancelMode(progressObj) {
  practice.setProgress(activeTopic.value, activeMode.value, progressObj)
  activeMode.value = null
}

async function finishSession(score) {
  const mode = activeMode.value
  practice.clearContent(activeTopic.value, mode)
  practice.clearProgress(activeTopic.value, mode)
  await saveSession({
    topic_id: activeTopic.value,
    mode,
    score,
    questions_json: JSON.stringify(questions.value),
    answers_json: '[]',
    feedback_json: '{}',
  })
  topics.updateTopicProgress(activeTopic.value, score * 10)
  activeMode.value = null
  questions.value = []
  suposit.value = null
}

watch(activeTopic, () => {
  activeMode.value = null
  questions.value = []
  suposit.value = null
})
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/PracticaView.vue
git commit -m "feat(ui): integrate SimulacreCard into PracticaView with draft detection"
```

---

## Verificació final

- [ ] **Reinicia el backend i comprova que no hi ha errors d'importació**

```bash
cd backend && python -m uvicorn main:app --reload
# Esperat: INFO: Application startup complete.
```

- [ ] **Comprova que la taula s'ha creat a la BD**

```bash
cd backend && python -c "import asyncio, aiosqlite; asyncio.run(asyncio.coroutine(lambda: None)())"
# O obre opos.db amb sqlite3 i comprova: .tables → ha d'aparèixer simulacre_results
```

- [ ] **Comprova que l'endpoint de generació respon**

```bash
curl -X POST http://localhost:8000/api/simulacre/generate
# Esperat: {"questions": [...], "total": N}
```

- [ ] **Comprova el frontend: la targeta SimulacreCard apareix a Pràctica**

Obre l'app al navegador → pestanya Pràctica → ha d'apareixer la targeta ambre a dalt.

- [ ] **Commit final de verificació**

```bash
git add -A
git status  # Comprova que no hi ha fitxers inesperats
git log --oneline -8
```
