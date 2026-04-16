import os
import re
import json
import time
import logging
from datetime import date
from google import genai
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Usage tracker (module-level, resets per minute and per day)
# ---------------------------------------------------------------------------

class UsageTracker:
    def __init__(self):
        self._reset_minute()
        self._reset_day()

    def _reset_minute(self):
        self._minute_start = time.time()
        self.req_minute = 0
        self.tok_minute = 0

    def _reset_day(self):
        self._day = date.today()
        self.req_day = 0
        self.tok_day = 0

    def record(self, tokens: int = 0):
        if time.time() - self._minute_start >= 60:
            self._reset_minute()
        if date.today() != self._day:
            self._reset_day()
        self.req_minute += 1
        self.tok_minute += tokens
        self.req_day += 1
        self.tok_day += tokens

    def stats(self) -> dict:
        if time.time() - self._minute_start >= 60:
            self._reset_minute()
        if date.today() != self._day:
            self._reset_day()
        return {
            "req_minute": self.req_minute,
            "tok_minute": self.tok_minute,
            "req_day": self.req_day,
            "tok_day": self.tok_day,
            "minute_elapsed_s": int(time.time() - self._minute_start),
        }


# ---------------------------------------------------------------------------
# Module-level model state (read from env, overrideable at runtime from DB)
# ---------------------------------------------------------------------------

_model: str = os.getenv("GEMINI_MODEL", "gemma-3n-e2b-it")
_usage = UsageTracker()


def get_current_model() -> str:
    return _model


def set_current_model(model: str):
    global _model
    _model = model
    logger.info(f"Model canviat a: {model}")


def get_usage_stats() -> dict:
    return _usage.stats()


# ---------------------------------------------------------------------------
# GeminiService
# ---------------------------------------------------------------------------

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        self.client = genai.Client(api_key=api_key)

    @property
    def model(self) -> str:
        return _model

    async def list_models(self) -> list[dict]:
        """List available generative models from the API."""
        try:
            result = []
            async for m in self.client.aio.models.list():
                name = getattr(m, "name", "")
                # Strip "models/" prefix if present
                model_id = name.replace("models/", "") if name.startswith("models/") else name
                if not model_id:
                    continue
                result.append({
                    "id": model_id,
                    "display_name": getattr(m, "display_name", model_id),
                    "description": getattr(m, "description", ""),
                    "input_token_limit": getattr(m, "input_token_limit", None),
                    "output_token_limit": getattr(m, "output_token_limit", None),
                })
            return result
        except Exception as e:
            logger.warning(f"No s'ha pogut llistar models: {e}")
            return []

    async def _generate_json(self, prompt: str) -> dict | list:
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as e:
            msg = str(e).upper()
            etype = type(e).__name__.upper()
            logger.error(f"Error IA [{etype}] model={self.model}: {e}")
            if any(x in msg or x in etype for x in ("429", "RESOURCE_EXHAUSTED", "QUOTA", "RATELIMIT")):
                raise HTTPException(
                    status_code=429,
                    detail="Massa sol·licituds a la IA. Espera 1 minut i torna a intentar-ho."
                )
            if any(x in msg or x in etype for x in ("503", "UNAVAILABLE", "OVERLOADED")):
                raise HTTPException(
                    status_code=503,
                    detail="La IA està saturada temporalment. Torna a intentar-ho en uns segons."
                )
            raise HTTPException(status_code=500, detail=f"Error IA: {e}")

        # Track usage
        usage = getattr(response, "usage_metadata", None)
        total_tokens = getattr(usage, "total_token_count", 0) or 0
        _usage.record(tokens=total_tokens)

        text = response.text.strip()
        text = re.sub(r"^```\w*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="La IA ha retornat una resposta invàlida. Torna a intentar-ho.")

    async def generate_flashcards(self, topic_text: str, topic_name: str) -> list[dict]:
        prompt = (
            "Ets un professor d'oposicions públiques. La teva tasca és generar flashcards.\n"
            "REGLES OBLIGATÒRIES:\n"
            "1. Basa't ÚNICAMENT en el contingut proporcionat. NO inventes informació que no hi sigui.\n"
            "2. Cada terme i definició han d'estar explícitament presents o directament derivats del text.\n"
            "3. L'exemple ha de ser concret i extret del context del contingut.\n"
            "4. Genera EXACTAMENT 15 flashcards, ni més ni menys.\n"
            "5. Respon ÚNICAMENT amb JSON vàlid, sense cap text addicional, sense markdown, sense explicacions.\n"
            "FORMAT DE RESPOSTA (array de exactament 15 objectes):\n"
            '[{"terme": "nom exacte del concepte", "definicio": "definició basada en el text", "exemple": "exemple del text"}]\n'
            f"TEMA: {topic_name}\n"
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_test(self, topic_text: str) -> list[dict]:
        prompt = (
            "La teva tasca és generar preguntes tipus test per a un examen de tècnic C1 d'informàtica.\n"
            "REGLES OBLIGATÒRIES:\n"
            "1. Basa't ÚNICAMENT en el contingut proporcionat. NO inventes informació.\n"
            "2. La resposta correcta ha d'estar clarament justificada pel contingut donat.\n"
            "3. Les opcions incorrectes han de ser plausibles però clarament errònies segons el text.\n"
            "4. Genera EXACTAMENT 10 preguntes, ni més ni menys.\n"
            "5. El camp 'correcta' ha de ser una sola lletra: A, B, C o D.\n"
            "6. L'explicació ha de citar el contingut per justificar la resposta correcta.\n"
            "7. Respon ÚNICAMENT amb JSON vàlid, sense cap text addicional, sense markdown.\n"
            "FORMAT DE RESPOSTA (array de exactament 10 objectes):\n"
            '[{"pregunta": "...", "opcions": {"A":"...","B":"...","C":"...","D":"..."}, '
            '"correcta": "A", "explicacio": "Per que A és correcta segons el text..."}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_breus(self, topic_text: str) -> list[dict]:
        prompt = (
            "La teva tasca és generar preguntes breus per a un examen de tècnic C1 d'informàtica.\n"
            "REGLES OBLIGATÒRIES:\n"
            "1. Basa't ÚNICAMENT en el contingut proporcionat. NO inventes informació.\n"
            "2. Les preguntes han de poder respondre's en 2-4 línies amb la informació del text.\n"
            "3. La resposta model ha de ser precisa i basada exclusivament en el contingut.\n"
            "4. Els criteris d'avaluació han de reflectir els conceptes clau del text.\n"
            "5. Genera EXACTAMENT 5 preguntes, ni més ni menys.\n"
            "6. Respon ÚNICAMENT amb JSON vàlid, sense cap text addicional, sense markdown.\n"
            "FORMAT DE RESPOSTA (array de exactament 5 objectes):\n"
            '[{"pregunta": "...", "resposta_model": "resposta breu basada en el text", "criteris": "conceptes clau que cal mencionar"}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_suposit(self, topic_text: str, topic_name: str) -> dict:
        prompt = (
            "La teva tasca és generar un supòsit pràctic per a un tècnic C1 d'informàtica "
            "en un ajuntament petit.\n"
            "REGLES OBLIGATÒRIES:\n"
            "1. L'enunciat ha d'estar basat DIRECTAMENT en el contingut proporcionat.\n"
            "2. Els punts clau de resposta han d'estar extrets del contingut. NO inventes conceptes.\n"
            "3. El supòsit ha de requerir aplicació raonada del contingut, no memorització.\n"
            "4. El criteri de correcció ha de fer referència a conceptes presents al text.\n"
            "5. Respon ÚNICAMENT amb JSON vàlid, sense cap text addicional, sense markdown.\n"
            "FORMAT DE RESPOSTA (un únic objecte JSON):\n"
            '{"enunciat": "situació pràctica basada en el contingut", '
            '"context": "context de l\'ajuntament relacionat amb el tema", '
            '"punts_clau_resposta": ["concepte del text que cal aplicar", "..."], '
            '"criteri_correccio": "explicació de com puntuar basada en el contingut", '
            '"dificultat": "mitja"}\n'
            f"TEMA: {topic_name}\n"
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_connecta(self, topic_text: str) -> list[dict]:
        prompt = (
            "La teva tasca és generar parells terme-definició per a una activitat de relacionar conceptes.\n"
            "REGLES OBLIGATÒRIES:\n"
            "1. Basa't ÚNICAMENT en el contingut proporcionat. NO inventes termes ni definicions.\n"
            "2. Cada terme ha d'aparèixer explícitament al contingut.\n"
            "3. Cada definició ha de ser la definició real del terme segons el text.\n"
            "4. Genera EXACTAMENT 10 parells, ni més ni menys.\n"
            "5. Respon ÚNICAMENT amb JSON vàlid, sense cap text addicional, sense markdown.\n"
            "FORMAT DE RESPOSTA (array de exactament 10 objectes):\n"
            '[{"terme": "terme del contingut", "definicio": "definició extreta del text"}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_buits(self, topic_text: str) -> list[dict]:
        prompt = (
            "La teva tasca és generar frases amb paraules clau eliminades per a una activitat d'omplir buits.\n"
            "REGLES OBLIGATÒRIES:\n"
            "1. Les frases han de ser COPIADES LITERALMENT del contingut, amb 1-2 paraules substituïdes per ___.\n"
            "2. Les paraules eliminades han de ser termes importants i específics (no articles ni preposicions).\n"
            "3. El camp 'paraules' ha de contenir les paraules exactes que substitueix ___ en ordre.\n"
            "4. El camp 'posicions' indica quina posició ocupa cada ___ a la frase (comptant des de 1).\n"
            "5. Genera EXACTAMENT 8 frases, ni més ni menys.\n"
            "6. Respon ÚNICAMENT amb JSON vàlid, sense cap text addicional, sense markdown.\n"
            "FORMAT DE RESPOSTA (array de exactament 8 objectes):\n"
            '[{"frase": "La ___ és responsable de gestionar...", "paraules": ["Alcaldia"], "posicions": [2]}]\n'
            f"CONTINGUT:\n{topic_text[:2000]}"
        )
        return await self._generate_json(prompt)

    async def evaluate_answer(self, pregunta: str, resposta_usuari: str,
                               resposta_model: str) -> dict:
        prompt = (
            "Ets un corrector estricte d'exàmens de tècnic C1 d'informàtica.\n"
            "REGLES ESTRICTES:\n"
            "1. El camp 'encerts' NOMÉS pot contenir conceptes que l'usuari hagi escrit EXPLÍCITAMENT. "
            "Si un concepte no apareix a la resposta de l'usuari, NO pot ser un encert.\n"
            "2. Si la resposta de l'usuari és buida, no relacionada o massa curta, la puntuació ha de ser 0 o 1.\n"
            "3. La resposta model és referència per al corrector, mai per a l'usuari.\n"
            "4. NO atribuïs a l'usuari coneixements que no ha demostrat escrivint-los.\n"
            "Retorna ÚNICAMENT JSON (sense text addicional):\n"
            '{"puntuacio": 7, "encerts": ["concepte que l\'usuari ha mencionat"], '
            '"mancances": ["concepte que faltava"], "feedback": "...", "puntuacio_justificada": "..."}\n'
            f"PREGUNTA: {pregunta}\n"
            f"RESPOSTA DE L'USUARI (avalua NOMÉS això): {resposta_usuari}\n"
            f"RESPOSTA MODEL (referència del corrector): {resposta_model}"
        )
        return await self._generate_json(prompt)

    async def exam_readiness(self, progress_json: str, gaps_json: str,
                              exam_date: str, today: str, dies: int) -> dict:
        prompt = (
            f"L'examen és el {exam_date}. Avui és {today}. Resten {dies} dies.\n"
            "La teva tasca és fer una valoració realista de la preparació de l'estudiant.\n"
            "REGLES OBLIGATÒRIES:\n"
            "1. Basa't ÚNICAMENT en les dades de progrés proporcionades. NO inventes dades.\n"
            "2. El 'readiness_pct' ha de reflectir la mitjana real de 'overall_pct' de les dades.\n"
            "3. La 'nota_estimada' ha de ser proporcional al readiness_pct (100%=10, 0%=0).\n"
            "4. Els 'temes_prioritaris' han de ser els temes amb overall_pct més baix de les dades.\n"
            "5. Si no hi ha dades de progrés, readiness_pct ha de ser 0 i nota_estimada 0.\n"
            "6. Respon ÚNICAMENT amb JSON vàlid, sense cap text addicional, sense markdown.\n"
            "FORMAT DE RESPOSTA (un únic objecte JSON):\n"
            '{"readiness_pct": 65, "nota_estimada": 6.5, "temes_prioritaris": ["topic_id del tema amb menys progrés"], '
            '"consell_estudi": "consell basat en les dades reals", "temps_recomanat_per_tema": {"topic_id": 30}}\n'
            f"PROGRÉS PER TEMA: {progress_json}\n"
            f"GAPS DEL TEMARI: {gaps_json}"
        )
        return await self._generate_json(prompt)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_gemini: GeminiService | None = None


def get_gemini() -> GeminiService:
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini
