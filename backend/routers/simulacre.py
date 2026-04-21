import os
import logging
import random
import re
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from services.gemini import get_gemini
from services.markdown_parser import get_topics, extract_flash_check

logger = logging.getLogger(__name__)

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
    words = re.findall(r'[a-zA-ZàáèéíïóòúüçÀÁÈÉÍÏÓÒÚÜÇ·]{4,}', enunciat)
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
    try:
        print("[SIMULACRE] Iniciant generate_simulacre...", flush=True)
        temes = _get_importants_temes()
        print(f"[SIMULACRE] {len(temes)} temes importants trobats", flush=True)
        seed = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
        questions = await get_gemini().generate_simulacre(temes, seed)
        random.shuffle(questions)
        for i, q in enumerate(questions):
            q["id"] = i + 1
        print(f"[SIMULACRE] OK: {len(questions)} preguntes", flush=True)
        return {"questions": questions, "total": len(questions)}
    except HTTPException as e:
        print(f"[SIMULACRE] HTTPException {e.status_code}: {e.detail}", flush=True)
        raise
    except Exception as e:
        import traceback
        print(f"[SIMULACRE] ERROR: {type(e).__name__}: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        raise HTTPException(status_code=500, detail=f"Error intern: {type(e).__name__}: {e}")


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
