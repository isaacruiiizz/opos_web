import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from models import PracticeEvaluate, SessionSave
from database import get_db
from services.gemini import get_gemini
from services.markdown_parser import get_topic_by_id

_PROGRESS_UPSERT = {
    "score_test": (
        "INSERT INTO progress (topic_id, bloc, score_test, tests_done, last_activity) "
        "VALUES (?,?,?,1,datetime('now')) "
        "ON CONFLICT(topic_id) DO UPDATE SET score_test=excluded.score_test, "
        "tests_done=tests_done+1, last_activity=datetime('now')"
    ),
    "score_breus": (
        "INSERT INTO progress (topic_id, bloc, score_breus, tests_done, last_activity) "
        "VALUES (?,?,?,1,datetime('now')) "
        "ON CONFLICT(topic_id) DO UPDATE SET score_breus=excluded.score_breus, "
        "tests_done=tests_done+1, last_activity=datetime('now')"
    ),
    "score_suposit": (
        "INSERT INTO progress (topic_id, bloc, score_suposit, tests_done, last_activity) "
        "VALUES (?,?,?,1,datetime('now')) "
        "ON CONFLICT(topic_id) DO UPDATE SET score_suposit=excluded.score_suposit, "
        "tests_done=tests_done+1, last_activity=datetime('now')"
    ),
    "score_connecta": (
        "INSERT INTO progress (topic_id, bloc, score_connecta, tests_done, last_activity) "
        "VALUES (?,?,?,1,datetime('now')) "
        "ON CONFLICT(topic_id) DO UPDATE SET score_connecta=excluded.score_connecta, "
        "tests_done=tests_done+1, last_activity=datetime('now')"
    ),
    "score_buits": (
        "INSERT INTO progress (topic_id, bloc, score_buits, tests_done, last_activity) "
        "VALUES (?,?,?,1,datetime('now')) "
        "ON CONFLICT(topic_id) DO UPDATE SET score_buits=excluded.score_buits, "
        "tests_done=tests_done+1, last_activity=datetime('now')"
    ),
}

_MODE_TO_COL = {
    "test": "score_test", "breus": "score_breus", "suposit": "score_suposit",
    "connecta": "score_connecta", "buits": "score_buits",
}

router = APIRouter(tags=["practice"])

_default_notes = str(Path(__file__).parent.parent.parent / "data" / "ApuntsTemari.md")
NOTES_PATH = Path(os.getenv("NOTES_PATH", _default_notes))

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
    score_col = _MODE_TO_COL.get(body.mode, "score_test")
    sql = _PROGRESS_UPSERT[score_col]
    # Fetch current topic bloc
    from services.markdown_parser import get_topic_by_id as _get
    topic = _get(body.topic_id, NOTES_PATH)
    bloc = topic["bloc"] if topic else "general"
    await db.execute(sql, (body.topic_id, bloc, body.score))
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
