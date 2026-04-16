from fastapi import APIRouter, Depends
from models import ConfigSet
from database import get_db

router = APIRouter(tags=["config"])

@router.get("/api/config")
async def get_config(db=Depends(get_db)):
    cursor = await db.execute("SELECT key, value FROM config")
    return {row["key"]: row["value"] for row in await cursor.fetchall()}

@router.post("/api/config")
async def set_config(body: ConfigSet, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO config (key, value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (body.key, body.value)
    )
    await db.commit()
    return {"key": body.key, "value": body.value}
