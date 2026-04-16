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
