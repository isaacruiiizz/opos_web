from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from services.pdf_analyzer import analyze_all_topics, PDF_PATH

router = APIRouter(tags=["pdf"])

@router.get("/api/pdf/status")
async def pdf_status():
    """Comprova si el fitxer PDF existeix."""
    return {"exists": PDF_PATH.exists(), "path": str(PDF_PATH)}

@router.post("/api/pdf/analyze")
async def run_pdf_analysis(db=Depends(get_db)):
    if not PDF_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Fitxer PDF no trobat: {PDF_PATH}. Puja el fitxer al directori /data del servidor."
        )
    results = await analyze_all_topics(db)
    return {"analyzed": len(results), "results": results}

@router.get("/api/pdf/analysis")
async def get_pdf_analysis(db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM pdf_analysis ORDER BY topic_id")
    return [dict(r) for r in await cursor.fetchall()]
