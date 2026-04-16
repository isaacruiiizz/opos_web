import json
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import EnrichmentCreate, SummaryRequest
from services.gemini import get_gemini

router = APIRouter(prefix="/api/ai", tags=["enrichment"])


@router.get("/enrichments/{topic_id}")
async def get_enrichments(topic_id: str, db=Depends(get_db)):
    """Return all persisted enrichments for a topic."""
    cursor = await db.execute(
        "SELECT section_idx, type, data_json FROM topic_enrichments WHERE topic_id=? ORDER BY section_idx",
        (topic_id,)
    )
    rows = await cursor.fetchall()
    return [
        {"section_idx": r["section_idx"], "type": r["type"], "data": json.loads(r["data_json"])}
        for r in rows
    ]


@router.post("/enrich")
async def enrich_section(payload: EnrichmentCreate, db=Depends(get_db), gemini=Depends(get_gemini)):
    """Generate (or return cached) enrichment for a section."""
    # Return cached result if it exists
    cursor = await db.execute(
        "SELECT type, data_json FROM topic_enrichments WHERE topic_id=? AND section_idx=?",
        (payload.topic_id, payload.section_idx)
    )
    existing = await cursor.fetchone()
    if existing:
        return {"type": existing["type"], "data": json.loads(existing["data_json"])}

    # Generate via AI
    result = await gemini.enrich_section(payload.section_markdown)

    # Validate minimal structure
    if "type" not in result or "data" not in result:
        raise HTTPException(status_code=500, detail="La IA ha retornat una estructura invàlida.")

    # Persist
    await db.execute(
        "INSERT OR REPLACE INTO topic_enrichments (topic_id, section_idx, type, data_json) VALUES (?,?,?,?)",
        (payload.topic_id, payload.section_idx, result["type"], json.dumps(result["data"]))
    )
    await db.commit()

    return result


@router.get("/summary/{topic_id}")
async def get_summary(topic_id: str, db=Depends(get_db)):
    """Return cached topic summary, or 404 if not yet generated."""
    cursor = await db.execute(
        "SELECT summary, chips_json FROM topic_summaries WHERE topic_id=?",
        (topic_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Summary not found")
    return {"summary": row["summary"], "chips": json.loads(row["chips_json"])}


@router.post("/topic-summary")
async def generate_summary(payload: SummaryRequest, db=Depends(get_db), gemini=Depends(get_gemini)):
    """Generate (or return cached) topic summary."""
    # Return cached
    cursor = await db.execute(
        "SELECT summary, chips_json FROM topic_summaries WHERE topic_id=?",
        (payload.topic_id,)
    )
    existing = await cursor.fetchone()
    if existing:
        return {"summary": existing["summary"], "chips": json.loads(existing["chips_json"])}

    result = await gemini.generate_topic_summary(payload.topic_content)

    if "summary" not in result or "chips" not in result:
        raise HTTPException(status_code=500, detail="La IA ha retornat una estructura invàlida.")

    await db.execute(
        "INSERT OR REPLACE INTO topic_summaries (topic_id, summary, chips_json) VALUES (?,?,?)",
        (payload.topic_id, result["summary"], json.dumps(result["chips"]))
    )
    await db.commit()

    return result
