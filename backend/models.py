from pydantic import BaseModel
from typing import Optional


class TopicSummary(BaseModel):
    id: str
    bloc: str
    number: int
    title: str
    overall_pct: float = 0.0


class TopicContent(BaseModel):
    id: str
    title: str
    content: str
    headings: list[dict]


class AnnotationCreate(BaseModel):
    selected_text: str
    color: str = "yellow"
    note: Optional[str] = None
    position_hash: Optional[str] = None


class DrawingUpdate(BaseModel):
    canvas_json: str


class FlashcardCreate(BaseModel):
    pregunta: str
    resposta: str
    exemple: Optional[str] = None


class FlashcardReview(BaseModel):
    knew_it: bool


class PracticeEvaluate(BaseModel):
    topic_id: str
    mode: str
    pregunta: str
    resposta_usuari: str
    resposta_model: Optional[str] = None


class SessionSave(BaseModel):
    topic_id: str
    mode: str
    questions_json: Optional[str] = None
    answers_json: Optional[str] = None
    score: float
    feedback_json: Optional[str] = None


class ConfigSet(BaseModel):
    key: str
    value: str
