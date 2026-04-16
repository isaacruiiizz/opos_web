import os
import json
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends
from database import get_db
from services.gemini import get_gemini
from services.markdown_parser import get_topics

router = APIRouter(tags=["progress"])

_default_notes = str(Path(__file__).parent.parent.parent / "data" / "ApuntsTemari.md")
NOTES_PATH = Path(os.getenv("NOTES_PATH", _default_notes))

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

@router.delete("/api/progress", status_code=204)
async def reset_progress(db=Depends(get_db)):
    await db.execute("DELETE FROM progress")
    await db.execute("DELETE FROM practice_sessions")
    await db.commit()

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
