from fastapi import APIRouter, Depends
from database import get_db
from services.gemini import get_gemini, get_current_model, set_current_model, get_usage_stats
from pydantic import BaseModel

router = APIRouter(tags=["ai"])

# Known free-tier limits for Groq (RPM / TPM / RPD)
KNOWN_LIMITS: dict[str, dict] = {
    "llama-3.3-70b-versatile": {"rpm": 30, "tpm": 6_000,  "rpd": 14_400, "desc": "Millor qualitat, recomanat"},
    "llama-3.1-70b-versatile": {"rpm": 30, "tpm": 6_000,  "rpd": 14_400, "desc": "Alta qualitat, 128K context"},
    "llama-3.1-8b-instant":    {"rpm": 30, "tpm": 20_000, "rpd": 14_400, "desc": "Ràpid i lleuger"},
    "gemma2-9b-it":            {"rpm": 30, "tpm": 15_000, "rpd": 14_400, "desc": "Google Gemma 2, 8K context"},
    "mixtral-8x7b-32768":      {"rpm": 30, "tpm": 5_000,  "rpd": 14_400, "desc": "Mixtral MoE, 32K context"},
}


class SetModelBody(BaseModel):
    model: str


@router.get("/api/ai/models")
async def list_models():
    """Retorna models disponibles des de l'API + límits coneguts."""
    gemini = get_gemini()
    api_models = await gemini.list_models()

    result = []
    seen = set()

    # Afegeix els models trobats a l'API
    for m in api_models:
        mid = m["id"]
        seen.add(mid)
        limits = KNOWN_LIMITS.get(mid, {})
        result.append({
            "id": mid,
            "display_name": m["display_name"] or mid,
            "description": limits.get("desc", m.get("description", "")),
            "rpm": limits.get("rpm"),
            "tpm": limits.get("tpm"),
            "rpd": limits.get("rpd"),
            "supported": limits.get("supported", True),
            "input_token_limit": m.get("input_token_limit"),
            "output_token_limit": m.get("output_token_limit"),
        })

    # Afegeix models coneguts que no han aparegut a l'API (per si la llista és incompleta)
    for mid, limits in KNOWN_LIMITS.items():
        if mid not in seen:
            result.append({
                "id": mid,
                "display_name": mid,
                "description": limits.get("desc", ""),
                "rpm": limits.get("rpm"),
                "tpm": limits.get("tpm"),
                "rpd": limits.get("rpd"),
                "supported": limits.get("supported", True),
                "input_token_limit": None,
                "output_token_limit": None,
            })

    # Ordena: primer els que tenim a KNOWN_LIMITS, després la resta
    known_ids = list(KNOWN_LIMITS.keys())
    result.sort(key=lambda m: (known_ids.index(m["id"]) if m["id"] in known_ids else 999, m["id"]))
    return result


@router.get("/api/ai/status")
async def get_status():
    """Retorna model actual + estadístiques d'ús."""
    model_id = get_current_model()
    limits = KNOWN_LIMITS.get(model_id, {})
    usage = get_usage_stats()
    return {
        "model": model_id,
        "limits": limits,
        "usage": usage,
    }


@router.post("/api/ai/model")
async def set_model(body: SetModelBody, db=Depends(get_db)):
    """Canvia el model actiu i el guarda a la BD."""
    set_current_model(body.model)
    await db.execute(
        "INSERT INTO config (key, value) VALUES ('gemini_model', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (body.model,)
    )
    return {"model": body.model}
