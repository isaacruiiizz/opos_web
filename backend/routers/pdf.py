from fastapi import APIRouter, Depends
from database import get_db
from services.pdf_analyzer import analyze_all_topics

router = APIRouter(tags=["pdf"])

@router.post("/api/pdf/analyze")
async def run_pdf_analysis(db=Depends(get_db)):
    results = await analyze_all_topics(db)
    return {"analyzed": len(results), "results": results}

@router.get("/api/pdf/analysis")
async def get_pdf_analysis(db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM pdf_analysis ORDER BY topic_id")
    return [dict(r) for r in await cursor.fetchall()]
