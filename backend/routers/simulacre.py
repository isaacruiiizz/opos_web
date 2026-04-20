import os
import logging
import random
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from services.gemini import get_gemini
from services.markdown_parser import get_topics, extract_flash_check

logger = logging.getLogger(__name__)

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
        temes = _get_importants_temes()
        logger.info(f"Generant simulacre amb {len(temes)} temes importants")
        seed = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
        questions = await get_gemini().generate_simulacre(temes, seed)
        random.shuffle(questions)
        for i, q in enumerate(questions):
            q["id"] = i + 1
        logger.info(f"Simulacre generat: {len(questions)} preguntes")
        return {"questions": questions, "total": len(questions)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperat generant simulacre: {type(e).__name__}: {e}", exc_info=True)
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
