from fastapi import APIRouter, Depends, HTTPException
from models import AnnotationCreate
from database import get_db

router = APIRouter(tags=["annotations"])

@router.get("/api/topics/{topic_id}/annotations")
async def get_annotations(topic_id: str, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT * FROM annotations WHERE topic_id=? ORDER BY created_at",
        (topic_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]

@router.post("/api/topics/{topic_id}/annotations", status_code=201)
async def create_annotation(topic_id: str, body: AnnotationCreate, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO annotations (topic_id, selected_text, color, note, position_hash) "
        "VALUES (?,?,?,?,?)",
        (topic_id, body.selected_text, body.color, body.note, body.position_hash)
    )
    await db.commit()
    row = await (await db.execute(
        "SELECT * FROM annotations WHERE id=?", (cursor.lastrowid,)
    )).fetchone()
    return dict(row)

@router.delete("/api/annotations/{ann_id}", status_code=204)
async def delete_annotation(ann_id: int, db=Depends(get_db)):
    cursor = await db.execute("DELETE FROM annotations WHERE id=?", (ann_id,))
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Annotation not found")
