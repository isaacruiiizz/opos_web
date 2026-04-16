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

_default_notes = str(Path(__file__).parent.parent.parent / "data" / "ApuntsTemari.md")
NOTES_PATH = Path(os.getenv("NOTES_PATH", _default_notes))

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

@router.delete("/api/flashcards", status_code=204)
async def clear_all_flashcards(db=Depends(get_db)):
    """Esborra totes les targetes flash."""
    await db.execute("DELETE FROM flashcards")


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
