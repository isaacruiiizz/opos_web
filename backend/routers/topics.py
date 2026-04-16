import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from models import TopicSummary, TopicContent
from services.markdown_parser import get_topics, get_topic_by_id
from database import get_db

router = APIRouter(prefix="/api/topics", tags=["topics"])

# __file__ is backend/routers/topics.py → parent.parent.parent is OPOS/
_default_notes = str(Path(__file__).parent.parent.parent / "data" / "ApuntsTemari.md")
NOTES_PATH = Path(os.getenv("NOTES_PATH", _default_notes))


@router.get("", response_model=list[TopicSummary])
async def list_topics(db=Depends(get_db)):
    topics = get_topics(NOTES_PATH)
    cursor = await db.execute("SELECT topic_id, overall_pct FROM progress")
    progress_map = {row["topic_id"]: row["overall_pct"] for row in await cursor.fetchall()}

    return [
        TopicSummary(
            id=t["id"],
            bloc=t["bloc"],
            number=t["number"],
            title=t["title"],
            overall_pct=progress_map.get(t["id"], 0.0),
        )
        for t in topics
    ]


@router.get("/{topic_id}/content", response_model=TopicContent)
async def get_content(topic_id: str):
    topic = get_topic_by_id(topic_id, NOTES_PATH)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found")
    return TopicContent(
        id=topic["id"],
        title=topic["title"],
        content=topic["content"],
        headings=topic["headings"],
    )
