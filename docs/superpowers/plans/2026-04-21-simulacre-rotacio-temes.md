# Simulacre Rotació de Temes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redissenyar el mòdul de simulacre perquè generi 15 preguntes (10 test + 3 breus + 2 suposits), roti sistemàticament els temes sense repetir conceptes, i aprofiti Llama 4 Scout (30K TPM) per a prompts de millor qualitat.

**Architecture:** Dues taules SQLite noves (`simulacre_state`, `simulacre_topic_concepts`) gestionen la ronda activa i la blacklist de conceptes. El backend extreu conceptes de les preguntes generades i els guarda immediatament; el save endpoint avança la rotació de temes. El frontend envia `topics_used` al save i mostra el progrés de ronda.

**Tech Stack:** Python/FastAPI, aiosqlite, Groq SDK (llama-4-scout-17b), Vue 3 + Pinia

---

## File Map

| Fitxer | Canvi |
|--------|-------|
| `backend/database.py` | Afegir 2 taules noves a `_CREATE_TABLES` |
| `backend/routers/simulacre.py` | Helpers de ronda, generate ampliat, save ampliat, nou endpoint round-state |
| `backend/services/gemini.py` | Model per defecte, `GROQ_MODELS` actualitzat, prompts nous per generate i evaluate |
| `frontend/src/api/client.js` | Afegir `fetchRoundState`, actualitzar `generateSimulacre` i `saveSimulacre` |
| `frontend/src/stores/simulacre.js` | Guardar `topics_used` + `roundState`, enviar-los al save |
| `frontend/src/components/practice/SimulacreCard.vue` | Text "15 preguntes", prop `roundState` |
| `frontend/src/views/PracticaView.vue` | Carregar i passar `roundState` al SimulacreCard |

---

## Task 1: Afegir taules noves a la DB

**Files:**
- Modify: `backend/database.py`

- [ ] **Step 1: Afegir les dues taules a `_CREATE_TABLES`**

A `backend/database.py`, afegir al final de la llista `_CREATE_TABLES` (abans del tancament `]`):

```python
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
```

- [ ] **Step 2: Verificar que la DB s'inicialitza correctament**

Atura el backend si està en marxa, esborra la DB de test i comprova:

```bash
cd backend
python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
import sqlite3
conn = sqlite3.connect('opos.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print([t[0] for t in tables])
conn.close()
"
```

Expected output (entre d'altres): `['simulacre_state', 'simulacre_topic_concepts']`

- [ ] **Step 3: Commit**

```bash
git add backend/database.py
git commit -m "feat(db): add simulacre_state and simulacre_topic_concepts tables"
```

---

## Task 2: Funció d'extracció de conceptes + test

**Files:**
- Modify: `backend/routers/simulacre.py` (afegir funció utilitària a dalt)
- Create: `backend/tests/test_simulacre_concepts.py`

- [ ] **Step 1: Escriure el test primer (TDD)**

Crear `backend/tests/test_simulacre_concepts.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from routers.simulacre import extract_concepts

def test_extract_basic():
    result = extract_concepts("Configura el servidor DHCP per assignar adreces IP")
    assert "dhcp" in result
    assert "servidor" in result
    assert len(result) <= 3

def test_extract_ignores_stopwords():
    result = extract_concepts("El la els les de que un una")
    assert result == []

def test_extract_short_words_ignored():
    # paraules de menys de 4 lletres s'ignoren
    result = extract_concepts("com fer amb una xarxa")
    assert "xarxa" in result
    assert "fer" not in result

def test_extract_max_3():
    result = extract_concepts("servidor proxy tallafoc encriptació certificat autenticació")
    assert len(result) == 3

def test_extract_no_duplicates():
    result = extract_concepts("servidor servidor servidor proxy")
    assert result.count("servidor") == 1
```

- [ ] **Step 2: Executar per verificar que fallen**

```bash
cd backend
python -m pytest tests/test_simulacre_concepts.py -v
```

Expected: `ImportError` (funció no existeix encara)

- [ ] **Step 3: Implementar `extract_concepts` a `routers/simulacre.py`**

Afegir just sota els imports existents de `backend/routers/simulacre.py`:

```python
import json

_STOPWORDS_CA = {
    "el","la","els","les","de","d","i","a","en","per","amb","que","un","una",
    "uns","unes","es","al","del","dels","és","ha","han","ser","hi","ho",
    "també","però","quan","com","si","no","més","tot","tots","totes","s",
    "aquest","aquesta","aquests","aquestes","seu","seva","seus","seves",
    "cal","pot","van","fer","tenir","estar","voler","poder","haver","anar",
    "e","o","u","ni","sinó","mentre","fins","des","sense","sobre","sota",
    "entre","durant","cada","altre","altres","mateix","mateixa","molt",
    "poc","ara","aquí","allà","qui","on","perquè","respecte","tret",
}

def extract_concepts(enunciat: str, max_words: int = 3) -> list[str]:
    """Extreu fins a max_words paraules significatives d'un enunciat."""
    words = re.findall(r'\b[a-zA-ZàáèéíïóòúüçÀÁÈÉÍÏÓÒÚÜÇ]{4,}\b', enunciat)
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        wl = w.lower()
        if wl not in _STOPWORDS_CA and wl not in seen:
            seen.add(wl)
            result.append(wl)
        if len(result) >= max_words:
            break
    return result
```

Afegir també `import re` i `import json` si no estan (revisa els imports actuals: `re` no hi és, `json` tampoc).

Els imports actuals al fitxer comencen per:
```python
import os
import logging
import random
from datetime import datetime
```

Afegir `import re` i `import json` a continuació.

- [ ] **Step 4: Executar tests per verificar que passen**

```bash
cd backend
python -m pytest tests/test_simulacre_concepts.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/routers/simulacre.py backend/tests/test_simulacre_concepts.py
git commit -m "feat(simulacre): add concept extraction utility with tests"
```

---

## Task 3: Helpers de gestió de ronda al router

**Files:**
- Modify: `backend/routers/simulacre.py`

- [ ] **Step 1: Afegir helpers `_get_or_init_state` i `_commit_concepts`**

Afegir les funcions a `backend/routers/simulacre.py` just sota `extract_concepts`:

```python
async def _get_or_init_state(db, all_topic_nums: list[int]) -> dict:
    """Carrega l'estat de ronda. Si no existeix o pending buit, inicialitza nova ronda."""
    cursor = await db.execute(
        "SELECT current_round, pending_topics FROM simulacre_state WHERE id=1"
    )
    row = await cursor.fetchone()

    if not row:
        pending = all_topic_nums[:]
        await db.execute(
            "INSERT INTO simulacre_state (id, current_round, pending_topics) VALUES (1, 1, ?)",
            (json.dumps(pending),)
        )
        await db.commit()
        return {"current_round": 1, "pending_topics": pending}

    pending = json.loads(row["pending_topics"])
    current_round = row["current_round"]

    if not pending:
        new_round = current_round + 1
        pending = all_topic_nums[:]
        await db.execute(
            "UPDATE simulacre_state SET current_round=?, pending_topics=? WHERE id=1",
            (new_round, json.dumps(pending))
        )
        await db.execute(
            "UPDATE simulacre_topic_concepts SET concepts_used='[]', round_number=?",
            (new_round,)
        )
        await db.commit()
        return {"current_round": new_round, "pending_topics": pending}

    return {"current_round": current_round, "pending_topics": pending}


async def _commit_concepts(db, questions: list[dict], round_number: int) -> None:
    """Extreu conceptes de les preguntes generades i els desa a DB (màx 10 per tema, FIFO)."""
    by_topic: dict[int, dict] = {}
    for q in questions:
        tnum = q.get("tema_num")
        ttitol = q.get("tema_titol", "")
        if tnum is None:
            continue
        if tnum not in by_topic:
            by_topic[tnum] = {"titol": ttitol, "concepts": []}
        by_topic[tnum]["concepts"].extend(extract_concepts(q.get("enunciat", "")))

    for tnum, data in by_topic.items():
        new_concepts = list(dict.fromkeys(data["concepts"]))  # dedup preserving order

        cursor = await db.execute(
            "SELECT concepts_used FROM simulacre_topic_concepts WHERE topic_num=?", (tnum,)
        )
        row = await cursor.fetchone()
        existing = json.loads(row["concepts_used"]) if row else []

        merged = existing + [c for c in new_concepts if c not in existing]
        if len(merged) > 10:
            merged = merged[-10:]  # FIFO: drop oldest

        if row:
            await db.execute(
                "UPDATE simulacre_topic_concepts SET concepts_used=?, round_number=?, topic_titol=? WHERE topic_num=?",
                (json.dumps(merged), round_number, data["titol"], tnum)
            )
        else:
            await db.execute(
                "INSERT INTO simulacre_topic_concepts (topic_num, topic_titol, round_number, concepts_used) VALUES (?,?,?,?)",
                (tnum, data["titol"], round_number, json.dumps(merged))
            )
    await db.commit()
```

- [ ] **Step 2: Verificar que el fitxer s'importa correctament**

```bash
cd backend
python -c "from routers.simulacre import extract_concepts, _get_or_init_state, _commit_concepts; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/routers/simulacre.py
git commit -m "feat(simulacre): add round state helpers and concept commit logic"
```

---

## Task 4: Actualitzar endpoint `POST /api/simulacre/generate`

**Files:**
- Modify: `backend/routers/simulacre.py`

- [ ] **Step 1: Substituir la funció `generate_simulacre` al router**

Substituir la funció `generate_simulacre` existent (línies 47-67) per aquesta nova versió:

```python
@router.post("/api/simulacre/generate")
async def generate_simulacre(db=Depends(get_db)):
    try:
        print("[SIMULACRE] Iniciant generate_simulacre...", flush=True)
        all_temes = _get_importants_temes()
        all_topic_nums = [i + 1 for i in range(len(all_temes))]

        state = await _get_or_init_state(db, all_topic_nums)
        current_round = state["current_round"]
        pending = state["pending_topics"]

        # Seleccionar fins a 10 temes del pendent
        n = min(10, len(pending))
        selected_nums = pending[:n]
        selected_temes = [all_temes[num - 1] for num in selected_nums if 1 <= num <= len(all_temes)]

        # Carregar blacklist de conceptes per als temes seleccionats
        cursor = await db.execute(
            f"SELECT topic_num, concepts_used FROM simulacre_topic_concepts WHERE topic_num IN ({','.join('?' * len(selected_nums))})",
            selected_nums
        )
        rows = await cursor.fetchall()
        concepts_blacklist: dict[int, list[str]] = {
            row["topic_num"]: json.loads(row["concepts_used"]) for row in rows
        }

        seed = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
        questions = await get_gemini().generate_simulacre(
            selected_temes, seed, selected_nums, concepts_blacklist
        )

        # Commit immediat de conceptes
        await _commit_concepts(db, questions, current_round)

        random.shuffle(questions)
        for i, q in enumerate(questions):
            q["id"] = i + 1

        print(f"[SIMULACRE] OK: {len(questions)} preguntes, ronda {current_round}, temes {selected_nums}", flush=True)
        return {
            "questions": questions,
            "total": len(questions),
            "topics_used": selected_nums,
            "round": current_round,
        }
    except HTTPException as e:
        print(f"[SIMULACRE] HTTPException {e.status_code}: {e.detail}", flush=True)
        raise
    except Exception as e:
        import traceback
        print(f"[SIMULACRE] ERROR: {type(e).__name__}: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        raise HTTPException(status_code=500, detail=f"Error intern: {type(e).__name__}: {e}")
```

- [ ] **Step 2: Verificar que el servidor arrenqui sense errors**

```bash
cd backend
python -c "from routers.simulacre import router; print('Router OK')"
```

Expected: `Router OK`

- [ ] **Step 3: Commit**

```bash
git add backend/routers/simulacre.py
git commit -m "feat(simulacre): update generate endpoint with round-based topic selection"
```

---

## Task 5: Actualitzar `POST /api/simulacre/save` i afegir `GET /api/simulacre/round-state`

**Files:**
- Modify: `backend/routers/simulacre.py`

- [ ] **Step 1: Ampliar el model `SaveBody` amb `topics_used`**

Substituir la classe `SaveBody` existent:

```python
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
    topics_used: list[int] = []
```

- [ ] **Step 2: Substituir la funció `save_simulacre` existent**

Substituir la funció `save_simulacre` existent per:

```python
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

    # Avançar rotació de temes
    if body.topics_used:
        cursor = await db.execute(
            "SELECT current_round, pending_topics FROM simulacre_state WHERE id=1"
        )
        row = await cursor.fetchone()
        if row:
            pending = json.loads(row["pending_topics"])
            used_set = set(body.topics_used)
            pending = [t for t in pending if t not in used_set]

            if not pending:
                # Ronda completa: iniciar nova
                all_temes = _get_importants_temes()
                all_topic_nums = [i + 1 for i in range(len(all_temes))]
                new_round = row["current_round"] + 1
                await db.execute(
                    "UPDATE simulacre_state SET current_round=?, pending_topics=? WHERE id=1",
                    (new_round, json.dumps(all_topic_nums))
                )
                await db.execute(
                    "UPDATE simulacre_topic_concepts SET concepts_used='[]', round_number=?",
                    (new_round,)
                )
                print(f"[SIMULACRE] Ronda {row['current_round']} completada! Iniciant ronda {new_round}", flush=True)
            else:
                await db.execute(
                    "UPDATE simulacre_state SET pending_topics=? WHERE id=1",
                    (json.dumps(pending),)
                )

    return {"ok": True}
```

- [ ] **Step 3: Afegir el nou endpoint `GET /api/simulacre/round-state`**

Afegir just sota `save_simulacre` (i abans de `get_last_simulacre`):

```python
@router.get("/api/simulacre/round-state")
async def get_round_state(db=Depends(get_db)):
    all_temes = _get_importants_temes()
    total = len(all_temes)
    cursor = await db.execute(
        "SELECT current_round, pending_topics FROM simulacre_state WHERE id=1"
    )
    row = await cursor.fetchone()
    if not row:
        return {"round": 1, "pending": total, "total": total, "covered": 0}
    pending = json.loads(row["pending_topics"])
    covered = total - len(pending)
    return {
        "round": row["current_round"],
        "pending": len(pending),
        "total": total,
        "covered": covered,
    }
```

- [ ] **Step 4: Verificar imports del router**

```bash
cd backend
python -c "from routers.simulacre import router; print('Router OK')"
```

Expected: `Router OK`

- [ ] **Step 5: Commit**

```bash
git add backend/routers/simulacre.py
git commit -m "feat(simulacre): update save endpoint with topic rotation, add round-state endpoint"
```

---

## Task 6: Actualitzar `gemini.py` — model i `generate_simulacre`

**Files:**
- Modify: `backend/services/gemini.py`

- [ ] **Step 1: Afegir Llama 4 Scout a `GROQ_MODELS` i canviar el model per defecte**

A `backend/services/gemini.py`:

**1a)** Canviar la línia del model per defecte (línia ~60):
```python
_model: str = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
```

**1b)** Afegir Llama 4 Scout al principi de la llista `GROQ_MODELS` (línia ~63), com a primer element:
```python
    {
        "id": "meta-llama/llama-4-scout-17b-16e-instruct",
        "display_name": "Llama 4 Scout 17B",
        "description": "Millor qualitat, 30K TPM - Recomanat per simulacre",
        "rpm": 30, "tpm": 30_000, "rpd": 14_400,
        "input_token_limit": 131_072, "output_token_limit": 8_192,
    },
```

- [ ] **Step 2: Substituir la funció `generate_simulacre` al servei**

Substituir el mètode `generate_simulacre` existent (línies ~370-408):

```python
    async def generate_simulacre(
        self,
        temes: list[dict],
        seed: str,
        selected_topic_nums: list[int],
        concepts_blacklist: dict[int, list[str]],
    ) -> list[dict]:
        """Genera 15 preguntes (10 test + 3 breus + 2 suposits) dels temes seleccionats."""
        temes_text = "\n".join(
            f"{i+1}. {t['titol']}: {t['resum'][:120]}"
            for i, t in enumerate(temes)
        )

        blacklist_lines = []
        for i, num in enumerate(selected_topic_nums):
            concepts = concepts_blacklist.get(num, [])
            if concepts and i < len(temes):
                blacklist_lines.append(f"- {temes[i]['titol']}: {', '.join(concepts)}")
        blacklist_text = (
            "\n".join(blacklist_lines)
            if blacklist_lines
            else "Cap (primer test d'aquests temes)"
        )

        prompt = (
            "Ets un tribunal d'oposicions C1 informàtica d'un ajuntament català petit "
            "(Maçanet de la Selva, ~10.000h). Genera un examen realista de 15 preguntes "
            "en format JSON array.\n\n"
            "DISTRIBUCIÓ OBLIGATÒRIA: exactament 10 test + 3 breu + 2 suposit.\n\n"
            f"TEMES A COBRIR (usa TOTS, reparteix les preguntes entre ells):\n{temes_text}\n\n"
            f"CONCEPTES JA USATS (no repeteixis cap d'aquests per al tema corresponent):\n{blacklist_text}\n\n"
            "REGLES DE QUALITAT:\n"
            "- test: cas pràctic real d'ajuntament, no teoria abstracta. 4 opcions plausibles "
            "(A/B/C/D), una clarament correcta. explicacio: per qué la correcta és correcta "
            "i per qué les altres no.\n"
            "- breu: pregunta que exigeix explicar un procediment o decisió tècnica concreta. "
            "resposta_model de 3-5 frases amb els punts clau. rubrica: llista de 3-4 "
            "conceptes que s'han d'esmentar.\n"
            "- suposit: incident o projecte TIC real a l'ajuntament amb context detallat. "
            "resposta_model estructurada en passos numerats. rubrica: criteris de valoració.\n"
            "- Dificultat: 4 preguntes baixa, 8 mitjana, 3 alta (repartit entre tipus).\n"
            "- Aplica normativa vigent (ENS, RGPD, LOPDGDD, Llei 39/2015) quan sigui rellevant.\n"
            f"- Seed de variació: {seed}\n\n"
            "FORMAT (array JSON de exactament 15 objectes, sense text extra ni markdown):\n"
            '[{"id":1,"tema_num":3,"tema_titol":"...","tipus":"test","punts":0.25,'
            '"dificultat":"mitjana","enunciat":"...","opcions":{"A":"...","B":"...","C":"...","D":"..."},'
            '"correcta":"B","explicacio":"...","penalitza":true},'
            '{"id":2,"tema_num":7,"tema_titol":"...","tipus":"breu","punts":0.5,'
            '"dificultat":"alta","enunciat":"...","opcions":null,"correcta":null,'
            '"resposta_model":"...","rubrica":"Mencionar: X, Y, Z","explicacio":"...","penalitza":false},'
            '{"id":3,"tema_num":12,"tema_titol":"...","tipus":"suposit","punts":1.0,'
            '"dificultat":"alta","enunciat":"...","opcions":null,"correcta":null,'
            '"resposta_model":"...","rubrica":"Valorar: X, Y, Z","explicacio":"...","penalitza":false}]'
        )

        result = await self._generate_json(
            prompt,
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=4000,
        )
        if not isinstance(result, list):
            raise HTTPException(status_code=500, detail="La IA no ha retornat una llista de preguntes.")
        valid = [q for q in result if isinstance(q, dict) and "id" in q and "tipus" in q and "enunciat" in q]
        if len(valid) < 12:
            raise HTTPException(
                status_code=500,
                detail=f"La IA ha retornat massa poques preguntes vàlides ({len(valid)}/15)."
            )
        return valid
```

- [ ] **Step 3: Verificar que el servei s'importa**

```bash
cd backend
python -c "from services.gemini import GeminiService, GROQ_MODELS; print([m['id'] for m in GROQ_MODELS])"
```

Expected: La llista ha de contenir `'meta-llama/llama-4-scout-17b-16e-instruct'` com a primer element.

- [ ] **Step 4: Commit**

```bash
git add backend/services/gemini.py
git commit -m "feat(simulacre): switch to Llama 4 Scout, improve generation prompt"
```

---

## Task 7: Actualitzar `evaluate_simulacre_answers` a `gemini.py`

**Files:**
- Modify: `backend/services/gemini.py`

- [ ] **Step 1: Substituir el mètode `evaluate_simulacre_answers`**

Substituir el mètode `evaluate_simulacre_answers` existent (línies ~410-449):

```python
    async def evaluate_simulacre_answers(self, answers: list[dict]) -> list[dict]:
        """Avalua respostes obertes (breu i suposit) en una sola crida (Llama 4 Scout, 30K TPM)."""
        if not answers:
            return []

        items_text = "\n\n".join(
            f"PREGUNTA {a['id']}: {a['enunciat']}\n"
            f"RÚBRICA: {a['rubrica']}\n"
            f"RESPOSTA MODEL: {a['resposta_model']}\n"
            f"RESPOSTA USUARI: {a['resposta_usuari'][:1500]}"
            for a in answers
        )

        prompt = (
            "Ets un corrector estricte d'oposicions C1 informàtica. Avalua les respostes.\n\n"
            "ESCALA DE FACTORS:\n"
            "- 0.0: absent, en blanc, o completament incorrecte\n"
            "- 0.25: alguns conceptes però amb errors importants o molt incomplet\n"
            "- 0.5: parcial, menciona conceptes clau però falta coherència o algun punt\n"
            "- 0.75: bona resposta amb algun punt menor que falta\n"
            "- 1.0: correcta i completa, menciona tots els conceptes de la rúbrica\n\n"
            "REGLES:\n"
            "- Llegeix la resposta sencera. Valora el que ha escrit, no el que no ha escrit.\n"
            "- Si l'usuari menciona conceptes correctes amb paraules pròpies, reconeix-los.\n"
            "- NO atribueixis coneixements no escrits explícitament per l'usuari.\n"
            "- comentari: 1-2 frases explicant el factor. Màx 30 paraules.\n"
            "- encerts/mancances: màx 3 items cadascun.\n\n"
            f"RESPOSTES A AVALUAR:\n{items_text}\n\n"
            "Respon ÚNICAMENT JSON array (sense text extra):\n"
            '[{"id":1,"factor":0.75,"encerts":["X","Y"],"mancances":["Z"],"comentari":"..."}]'
        )

        result = await self._generate_json(
            prompt,
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=1500,
        )
        if not isinstance(result, list):
            return [
                {"id": a["id"], "factor": 0.0, "encerts": [], "mancances": [], "comentari": "Error d'avaluació"}
                for a in answers
            ]
        return result
```

- [ ] **Step 2: Verificar que el servei s'importa sense errors**

```bash
cd backend
python -c "from services.gemini import GeminiService; g = GeminiService(); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/services/gemini.py
git commit -m "feat(simulacre): improve evaluation prompt with 5-point scale, remove batch delays"
```

---

## Task 8: Frontend — API client i store

**Files:**
- Modify: `frontend/src/api/client.js`
- Modify: `frontend/src/stores/simulacre.js`

- [ ] **Step 1: Afegir `fetchRoundState` i actualitzar `saveSimulacre` a `client.js`**

A `frontend/src/api/client.js`, substituir la línia de `saveSimulacre`:
```javascript
export const saveSimulacre = async (payload) => (await api.post('/simulacre/save', payload)).data
```
Per la mateixa (no cal canvi de signatura, el payload ja accepta camps extra). Afegir al final del fitxer:
```javascript
export const fetchRoundState = async () => (await api.get('/simulacre/round-state')).data
```

- [ ] **Step 2: Actualitzar `simulacre.js` store**

**2a)** Afegir `fetchRoundState` als imports de `client.js` a dalt de `simulacre.js`:

La línia d'imports actual és:
```javascript
import { generateSimulacre, evaluateSimulacre, saveSimulacre, fetchLastSimulacre } from '../api/client.js'
```
Substituir per:
```javascript
import { generateSimulacre, evaluateSimulacre, saveSimulacre, fetchLastSimulacre, fetchRoundState } from '../api/client.js'
```

**2b)** Afegir els nous refs a l'store, just sota `const phase = ref('idle')` (línia ~47):
```javascript
const topicsUsed = ref([])       // temes usats a la generació actual
const roundState = ref(null)     // { round, pending, total, covered }
```

**2c)** A la funció `startGeneration`, dins el bloc `try`, just sota `questions.value = data.questions`:
```javascript
topicsUsed.value = data.topics_used || []
```

**2d)** Afegir la funció `loadRoundState` just sota `loadLastResult`:
```javascript
  async function loadRoundState() {
    try {
      roundState.value = await fetchRoundState()
    } catch {}
  }
```

**2e)** A la crida `saveSimulacre` dins `submitExam` (línia ~208), afegir `topics_used`:

La crida actual és:
```javascript
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
```
Substituir per:
```javascript
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
        topics_used: topicsUsed.value,
      })
```

**2f)** Afegir `topicsUsed`, `roundState` i `loadRoundState` al `return` del store (al final de la funció del store):

La línia return actual acaba amb:
```javascript
    loadLastResult, startGeneration, answerTest, answerOpen,
    tickTimer, submitExam, reEvaluate, reset, persistDraft,
```
Substituir per:
```javascript
    loadLastResult, loadRoundState, startGeneration, answerTest, answerOpen,
    tickTimer, submitExam, reEvaluate, reset, persistDraft,
    topicsUsed, roundState,
```

- [ ] **Step 3: Verificar que el frontend compila sense errors**

```bash
cd frontend
npm run build 2>&1 | tail -20
```

Expected: build sense errors (pot haver warnings menors)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/client.js frontend/src/stores/simulacre.js
git commit -m "feat(simulacre): store topics_used and round state, send topics_used on save"
```

---

## Task 9: Frontend — UI: indicador de ronda i text actualitzat

**Files:**
- Modify: `frontend/src/components/practice/SimulacreCard.vue`
- Modify: `frontend/src/views/PracticaView.vue`

- [ ] **Step 1: Actualitzar `SimulacreCard.vue` — text i prop `roundState`**

**1a)** Afegir la prop `roundState` al `defineProps`:
```javascript
defineProps({
  lastResult: { type: Object, default: null },
  generating: { type: Boolean, default: false },
  hasDraft: { type: Boolean, default: false },
  error: { type: String, default: null },
  roundState: { type: Object, default: null },
})
```

**1b)** Al template, substituir el text estàtic:
```html
<p class="text-xs text-amber-700 dark:text-amber-400">~20 preguntes · 2 hores · Nota /10 · Mínim 5 per aprovar</p>
<p class="text-xs text-amber-600 dark:text-amber-500 mt-0.5">Temes "a tenir en compte" (30 temes)</p>
```
Per:
```html
<p class="text-xs text-amber-700 dark:text-amber-400">15 preguntes · 2 hores · Nota /10 · Mínim 5 per aprovar</p>
<p v-if="roundState" class="text-xs text-amber-600 dark:text-amber-500 mt-0.5">
  Ronda {{ roundState.round }} · {{ roundState.covered }}/{{ roundState.total }} temes coberts
</p>
<p v-else class="text-xs text-amber-600 dark:text-amber-500 mt-0.5">Temes "a tenir en compte"</p>
```

- [ ] **Step 2: Actualitzar `PracticaView.vue` — carregar i passar `roundState`**

**2a)** Afegir import de `onMounted` a les importacions de Vue (si no hi és):

La línia actual:
```javascript
import { ref, computed, watch } from 'vue'
```
Substituir per:
```javascript
import { ref, computed, watch, onMounted } from 'vue'
```

**2b)** Just sota la línia `simulacre.loadLastResult()` (línia ~102), afegir:
```javascript
onMounted(() => {
  simulacre.loadRoundState()
})
```

**2c)** Al template, substituir la línia del component `SimulacreCard`:
```html
    <SimulacreCard
      :last-result="simulacre.lastResult"
      :generating="simulacre.generating"
      :has-draft="hasDraft"
      :error="simulacre.error"
      @start="startSimulacre"
    />
```
Per:
```html
    <SimulacreCard
      :last-result="simulacre.lastResult"
      :generating="simulacre.generating"
      :has-draft="hasDraft"
      :error="simulacre.error"
      :round-state="simulacre.roundState"
      @start="startSimulacre"
    />
```

- [ ] **Step 3: Verificar build final**

```bash
cd frontend
npm run build 2>&1 | tail -20
```

Expected: build net sense errors

- [ ] **Step 4: Commit final**

```bash
git add frontend/src/components/practice/SimulacreCard.vue frontend/src/views/PracticaView.vue
git commit -m "feat(simulacre): show round progress in SimulacreCard, update question count to 15"
```

---

## Verificació manual post-implementació

Una vegada tot implementat, verificar el flux complet:

1. Arrancar backend: `cd backend && uvicorn main:app --reload`
2. Arrancar frontend: `cd frontend && npm run dev`
3. Anar a Pràctica → verificar que SimulacreCard mostra "15 preguntes" i "Ronda 1 · 0/N temes coberts"
4. Iniciar simulacre → verificar que es generen exactament 15 preguntes (10 test + 3 breus + 2 suposits)
5. Completar l'examen i enviar → verificar que el progrés de ronda s'actualitza
6. Iniciar un segon simulacre → verificar que els temes ja coberts no es repeteixen
