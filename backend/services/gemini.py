import os
import re
import json
import time
import asyncio
import logging
from datetime import date
from groq import AsyncGroq
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
# Module-level model state
# ---------------------------------------------------------------------------

_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
_usage = UsageTracker()

GROQ_MODELS = [
    {
        "id": "llama-3.3-70b-versatile",
        "display_name": "Llama 3.3 70B",
        "description": "Millor qualitat, recomanat",
        "rpm": 30, "tpm": 6_000, "rpd": 14_400,
        "input_token_limit": 128_000, "output_token_limit": 32_768,
    },
    {
        "id": "llama-3.1-70b-versatile",
        "display_name": "Llama 3.1 70B",
        "description": "Alta qualitat, 128K context",
        "rpm": 30, "tpm": 6_000, "rpd": 14_400,
        "input_token_limit": 128_000, "output_token_limit": 32_768,
    },
    {
        "id": "llama-3.1-8b-instant",
        "display_name": "Llama 3.1 8B",
        "description": "Ràpid i lleuger",
        "rpm": 30, "tpm": 20_000, "rpd": 14_400,
        "input_token_limit": 128_000, "output_token_limit": 8_000,
    },
    {
        "id": "gemma2-9b-it",
        "display_name": "Gemma 2 9B",
        "description": "Google Gemma 2, 8K context",
        "rpm": 30, "tpm": 15_000, "rpd": 14_400,
        "input_token_limit": 8_192, "output_token_limit": 8_192,
    },
    {
        "id": "mixtral-8x7b-32768",
        "display_name": "Mixtral 8x7B",
        "description": "Mixtral MoE, 32K context",
        "rpm": 30, "tpm": 5_000, "rpd": 14_400,
        "input_token_limit": 32_768, "output_token_limit": 32_768,
    },
]


def get_current_model() -> str:
    return _model


def set_current_model(model: str):
    global _model
    _model = model
    logger.info(f"Model canviat a: {model}")


def get_usage_stats() -> dict:
    return _usage.stats()


# ---------------------------------------------------------------------------
# GeminiService (nom mantingut per compatibilitat amb la resta de routers)
# ---------------------------------------------------------------------------

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        self.client = AsyncGroq(api_key=api_key)

    @property
    def model(self) -> str:
        return _model

    async def list_models(self) -> list[dict]:
        return GROQ_MODELS

    _FALLBACK_MODEL = "llama-3.1-8b-instant"

    async def _call_model(self, model: str, prompt: str, max_tokens: int = 4096):
        return await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )

    async def _generate_json(self, prompt: str, model: str | None = None, max_tokens: int = 4096) -> dict | list:
        primary = model or self.model
        response = None

        # ── Try primary model up to 3 times ──────────────────────────────────
        for attempt in range(3):
            try:
                response = await self._call_model(primary, prompt, max_tokens=max_tokens)
                break
            except Exception as e:
                msg = str(e).upper()
                etype = type(e).__name__.upper()
                logger.error(f"Error IA [{etype}] attempt={attempt+1} model={primary}: {e}")

                if any(x in msg or x in etype for x in ("429", "RATE_LIMIT", "RATELIMIT")):
                    raise HTTPException(status_code=429,
                        detail="Massa sol·licituds a la IA. Espera 1 minut i torna a intentar-ho.")
                if any(x in msg or x in etype for x in ("404", "NOT_FOUND", "MODEL_NOT_FOUND")):
                    raise HTTPException(status_code=400,
                        detail=f"El model '{primary}' no existeix. Canvia el model a Config.")

                # 500/503 — retry with backoff
                if attempt < 2:
                    wait = 3 * (attempt + 1)
                    logger.warning(f"Error transitori, reintentant en {wait}s…")
                    await asyncio.sleep(wait)
                    continue

                # All retries exhausted — try fallback
                if primary != self._FALLBACK_MODEL:
                    logger.warning(f"Model {primary} ha fallat 3 cops. Provant fallback {self._FALLBACK_MODEL}…")
                    try:
                        response = await self._call_model(self._FALLBACK_MODEL, prompt, max_tokens=max_tokens)
                        logger.info(f"Fallback {self._FALLBACK_MODEL} OK")
                    except Exception as fe:
                        logger.error(f"Fallback també ha fallat: {fe}")
                        raise HTTPException(status_code=503,
                            detail=f"El model '{primary}' no respon. Canvia el model a Config → Model d'IA.")
                else:
                    raise HTTPException(status_code=503,
                        detail="La IA ha fallat repetidament. Torna a intentar-ho en uns moments.")

        usage = getattr(response, "usage", None)
        total_tokens = getattr(usage, "total_tokens", 0) or 0
        _usage.record(tokens=total_tokens)

        text = response.choices[0].message.content.strip()
        text = re.sub(r"^```\w*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as je:
            print(f"[JSON ERROR] pos={je.pos} msg={je.msg}", flush=True)
            print(f"[JSON RAW] {repr(text[:500])}", flush=True)
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
            "2. La resposta correcta ha d'estat clarament justificada pel contingut donat.\n"
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

    async def enrich_section(self, section_markdown: str) -> dict:
        if not section_markdown or not section_markdown.strip():
            raise HTTPException(status_code=400, detail="La secció està buida.")
        prompt = (
            "Ets un expert en visualització de contingut per a oposicions. "
            "Analitza el text i tria el tipus visual que millor representa el contingut.\n\n"
            "CRITERIS DE SELECCIÓ (llegeix-los amb cura, NO uses timeline per defecte):\n\n"
            "→ \"timeline\" NOMÉS si hi ha un procés seqüencial amb fases o passos OBLIGATÒRIAMENT "
            "ordenats (ex: fases d'un procediment administratiu, etapes d'un expedient). "
            "Una llista de conceptes o punts NO és una timeline.\n\n"
            "→ \"table\" si el contingut compara 2 o més entitats en les mateixes dimensions "
            "(ex: òrgan A vs òrgan B amb competències, terminis, característiques). "
            "Mínim 2 columnes i 2 files.\n\n"
            "→ \"cards\" si el contingut defineix o descriu múltiples conceptes, òrgans, actors, "
            "drets o principis independents (ex: principis de la llei, òrgans d'un ajuntament, "
            "tipus de resolucions, drets dels interessats). Genera entre 3 i 8 cards.\n\n"
            "→ \"callouts\" si el contingut és un text explicatiu, normativa, article de llei, "
            "principis generals o conceptes que no encaixen als altres tipus. "
            "Usa variant law per a articles/lleis, important per a conceptes clau, exam per a "
            "punts freqüents d'examen.\n\n"
            "Respon ÚNICAMENT amb JSON vàlid, sense text addicional, sense markdown.\n\n"
            "FORMAT PER TIPUS:\n"
            "timeline: {\"type\":\"timeline\",\"data\":[{\"step\":1,\"title\":\"...\",\"desc\":\"...\"}]}\n"
            "table: {\"type\":\"table\",\"data\":{\"headers\":[\"Concepte\",\"Detall\"],\"rows\":[[\"...\",\"...\"]],\"highlight\":[]}}\n"
            "cards: {\"type\":\"cards\",\"data\":[{\"title\":\"...\",\"desc\":\"...\",\"icon\":\"building\"}]}\n"
            "  (icons: building, user, file, scale, shield, clock, globe, users, key, flag)\n"
            "callouts: {\"type\":\"callouts\",\"data\":[{\"variant\":\"law\",\"title\":\"...\",\"text\":\"...\"}]}\n"
            "  (variants: law=blau, important=groc, exam=verd)\n\n"
            f"SECCIÓ:\n{section_markdown[:2000]}"
        )
        return await self._generate_json(prompt)

    async def generate_topic_summary(self, topic_content: str) -> dict:
        prompt = (
            "Ets un expert en preparació d'oposicions. "
            "Llegeix el text del tema i genera un resum visual.\n\n"
            "REGLES:\n"
            "1. El resum ha de tenir 1-2 frases que capturin l'essència del tema.\n"
            "2. Genera entre 3 i 5 chips de conceptes clau.\n"
            "3. Cada chip té: label (text curt, màx 4 paraules) i category.\n"
            "4. Categories de chip:\n"
            "   - concept: concepte principal del tema\n"
            "   - law: referència a una llei o article\n"
            "   - alert: punt important a no oblidar\n"
            "   - exam: molt probable a l'examen\n"
            "5. Respon ÚNICAMENT amb JSON vàlid, sense text addicional.\n\n"
            "FORMAT: {\"summary\":\"...\",\"chips\":[{\"label\":\"...\",\"category\":\"concept\"}]}\n\n"
            f"CONTINGUT DEL TEMA:\n{topic_content[:3000]}"
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

    async def generate_simulacre(self, temes: list[dict], seed: str) -> list[dict]:
        """Genera 40 preguntes mixtes dels 30 temes importants.
        Dissenyat per mantenir-se dins del límit de 6K TPM de Groq."""
        temes_text = "\n".join(
            f"{i+1}. {t['titol']}: {t['resum']}"
            for i, t in enumerate(temes)
        )
        prompt = (
            "Tribunal oposicions C1 informàtica ajuntament català. Genera array JSON de 25 preguntes.\n"
            f"Seed variació: {seed}\n"
            "REGLES:\n"
            "- Cobreix la majoria de temes, màx 2 preguntes per tema.\n"
            "- Aplica conceptes a situacions reals d'ajuntament petit (Maçanet de la Selva).\n"
            "- Distribució: 12 test + 10 breu + 3 suposit = 25 total.\n"
            "- test: 4 opcions A/B/C/D, penalitza:-1/3, punts:0.25.\n"
            "- breu: resposta 2-4 frases, punts:0.5.\n"
            "- suposit: cas real TIC, punts:1.0.\n"
            "Respon ÚNICAMENT JSON vàlid:\n"
            "[{\"id\":1,\"tema_num\":3,\"tema_titol\":\"...\",\"tipus\":\"test\","
            "\"punts\":0.25,\"enunciat\":\"...\","
            "\"opcions\":{\"A\":\"...\",\"B\":\"...\",\"C\":\"...\",\"D\":\"..\"},"
            "\"correcta\":\"B\",\"explicacio\":\"...\",\"penalitza\":true},"
            "{\"id\":2,\"tema_num\":7,\"tema_titol\":\"...\",\"tipus\":\"breu\","
            "\"punts\":0.5,\"enunciat\":\"...\",\"opcions\":null,\"correcta\":null,"
            "\"resposta_model\":\"...\",\"rubrica\":\"Mencionar: X,Y\","
            "\"explicacio\":\"...\",\"penalitza\":false},"
            "{\"id\":3,\"tema_num\":22,\"tema_titol\":\"...\",\"tipus\":\"suposit\","
            "\"punts\":1.0,\"enunciat\":\"...\",\"opcions\":null,\"correcta\":null,"
            "\"resposta_model\":\"...\",\"rubrica\":\"Valorar: X,Y\","
            "\"explicacio\":\"...\",\"penalitza\":false}]\n"
            f"TEMES:\n{temes_text}"
        )
        result = await self._generate_json(prompt, model="llama-3.1-8b-instant", max_tokens=4200)
        if not isinstance(result, list):
            raise HTTPException(status_code=500, detail="La IA no ha retornat una llista de preguntes.")
        valid = [q for q in result if isinstance(q, dict) and "id" in q and "tipus" in q and "enunciat" in q]
        if len(valid) < 15:
            raise HTTPException(status_code=500, detail=f"La IA ha retornat massa poques preguntes vàlides ({len(valid)}/25).")
        return valid

    async def evaluate_simulacre_answers(self, answers: list[dict]) -> list[dict]:
        """Avalua respostes obertes (breu i suposit).
        Si hi ha >10 respostes, fa 2 crides seqüencials amb 15s de delay per respectar 6K TPM."""
        if not answers:
            return []

        async def _evaluate_batch(batch: list[dict]) -> list[dict]:
            items_text = "\n\n".join(
                f"PREGUNTA {a['id']}: {a['enunciat']}\n"
                f"RÚBRICA: {a['rubrica']}\n"
                f"RESPOSTA MODEL: {a['resposta_model']}\n"
                f"RESPOSTA USUARI: {a['resposta_usuari']}"
                for a in batch
            )
            prompt = (
                "Ets un corrector estricte d'oposicions públiques per a tècnic C1 d'informàtica.\n"
                "Avalua CADASCUNA de les respostes de l'usuari seguint la rúbrica.\n\n"
                "CRITERIS D'AVALUACIÓ:\n"
                "- 0.0: Resposta absent, incorrecta o completament fora de tema.\n"
                "- 0.5: Resposta parcial. Menciona alguns conceptes clau però li falten elements essencials.\n"
                "- 1.0: Resposta correcta. Menciona els conceptes clau de la rúbrica amb coherència.\n"
                "NO atribueixis a l'usuari conceptes que no hagi escrit explícitament.\n"
                "Si la resposta és buida o d'1-2 paraules genèriques, la puntuació és 0.0.\n\n"
                "Respon ÚNICAMENT amb JSON vàlid, sense text addicional:\n"
                "[{\"id\":1,\"factor\":0.5,\"encerts\":[\"concepte mencionat\"],"
                "\"mancances\":[\"concepte que faltava\"],\"comentari\":\"...\"}]\n\n"
                f"RESPOSTES A AVALUAR:\n{items_text}"
            )
            result = await self._generate_json(prompt)
            if not isinstance(result, list):
                return [{"id": a["id"], "factor": 0.0, "encerts": [], "mancances": [], "comentari": "Error d'avaluació"} for a in batch]
            return result

        if len(answers) <= 10:
            return await _evaluate_batch(answers)

        lot1 = answers[:10]
        lot2 = answers[10:]
        results1 = await _evaluate_batch(lot1)
        await asyncio.sleep(15)
        results2 = await _evaluate_batch(lot2)
        return results1 + results2

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
