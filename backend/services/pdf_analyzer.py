import os
import json
from pathlib import Path
import fitz  # PyMuPDF
from services.gemini import get_gemini
from services.markdown_parser import get_topics

_default_pdf = str(Path(__file__).parent.parent.parent / "data" / "EdicteC1Maçanet.pdf")
_default_notes = str(Path(__file__).parent.parent.parent / "data" / "ApuntsTemari.md")
PDF_PATH = Path(os.getenv("PDF_PATH", _default_pdf))
NOTES_PATH = Path(os.getenv("NOTES_PATH", _default_notes))

def extract_pdf_text(pdf_path: Path = PDF_PATH) -> str:
    doc = fitz.open(str(pdf_path))
    return "\n".join(page.get_text() for page in doc)

async def analyze_all_topics(db) -> list[dict]:
    pdf_text = extract_pdf_text()
    topics = get_topics(NOTES_PATH)
    results = []
    gemini = get_gemini()

    for topic in topics:
        prompt = (
            "Compara el contingut dels apunts amb el temari oficial del PDF.\n"
            "Retorna ÚNICAMENT JSON:\n"
            '{"cobertura": "completa", "gaps": ["punt no cobert"], "suggeriments": ["estudia X"]}\n'
            f"TEMA: {topic['title']}\n"
            f"APUNTS:\n{topic['content'][:2000]}\n\n"
            f"TEMARI OFICIAL (fragment rellevant):\n{pdf_text[:1500]}"
        )
        analysis = await gemini._generate_json(prompt)
        await db.execute(
            "INSERT INTO pdf_analysis (topic_id, cobertura, gaps_json, suggeriments_json) "
            "VALUES (?,?,?,?) ON CONFLICT(topic_id) DO UPDATE SET "
            "cobertura=excluded.cobertura, gaps_json=excluded.gaps_json, "
            "suggeriments_json=excluded.suggeriments_json, analyzed_at=datetime('now')",
            (topic["id"], analysis.get("cobertura", "parcial"),
             json.dumps(analysis.get("gaps", [])),
             json.dumps(analysis.get("suggeriments", [])))
        )
        results.append({"topic_id": topic["id"], **analysis})

    await db.commit()
    return results
