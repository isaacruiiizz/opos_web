import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_db_ctx
from routers import topics, annotations, drawings, flashcards, practice, progress, pdf
from routers import config as config_router
from routers import ai as ai_router
from routers import enrichment as enrichment_router
from routers import simulacre as simulacre_router
from services.gemini import set_current_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Restore saved model from DB (if user changed it via UI)
    try:
        async with get_db_ctx() as db:
            cursor = await db.execute("SELECT value FROM config WHERE key='gemini_model'")
            row = await cursor.fetchone()
            if row:
                set_current_model(row["value"])
    except Exception:
        pass
    yield


app = FastAPI(title="OPOS C1 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.include_router(topics.router)
app.include_router(annotations.router)
app.include_router(drawings.router)
app.include_router(flashcards.router)
app.include_router(practice.router)
app.include_router(progress.router)
app.include_router(pdf.router)
app.include_router(config_router.router)
app.include_router(ai_router.router)
app.include_router(enrichment_router.router)
app.include_router(simulacre_router.router)
