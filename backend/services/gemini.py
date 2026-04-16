import os
import re
import json
from google import genai

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    async def _generate_json(self, prompt: str) -> dict | list:
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        text = response.text.strip()
        text = re.sub(r"^```\w*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    async def generate_flashcards(self, topic_text: str, topic_name: str) -> list[dict]:
        prompt = (
            "Ets un professor d'oposicions públiques. Genera exactament 15 flashcards.\n"
            "Retorna ÚNICAMENT JSON (array de 15 objectes, sense cap text addicional):\n"
            '[{"terme": "...", "definicio": "...", "exemple": "..."}]\n'
            f"TEMA: {topic_name}\n"
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_test(self, topic_text: str) -> list[dict]:
        prompt = (
            "Genera 10 preguntes tipus test per a un examen de tècnic C1 d'informàtica.\n"
            "Retorna ÚNICAMENT JSON (array de 10 objectes, sense text addicional):\n"
            '[{"pregunta": "...", "opcions": {"A":"...","B":"...","C":"...","D":"..."}, '
            '"correcta": "A", "explicacio": "..."}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_breus(self, topic_text: str) -> list[dict]:
        prompt = (
            "Genera 5 preguntes breus (resposta en 2-4 línies) per a examen C1 informàtica.\n"
            "Retorna ÚNICAMENT JSON:\n"
            '[{"pregunta": "...", "resposta_model": "...", "criteris": "..."}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_suposit(self, topic_text: str, topic_name: str) -> dict:
        prompt = (
            "Genera un supòsit pràctic realista per a un tècnic C1 d'informàtica "
            "en un ajuntament petit. Ha de requerir aplicació raonada, no memorització.\n"
            "Retorna ÚNICAMENT JSON:\n"
            '{"enunciat": "...", "context": "...", "punts_clau_resposta": ["..."], '
            '"criteri_correccio": "...", "dificultat": "mitja"}\n'
            f"TEMA: {topic_name}\n"
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_connecta(self, topic_text: str) -> list[dict]:
        prompt = (
            "Genera 10 parells terme-definició per a una activitat de relacionar conceptes.\n"
            "Retorna ÚNICAMENT JSON:\n"
            '[{"terme": "...", "definicio": "..."}]\n'
            f"CONTINGUT:\n{topic_text[:3000]}"
        )
        return await self._generate_json(prompt)

    async def generate_buits(self, topic_text: str) -> list[dict]:
        prompt = (
            "Genera 8 frases clau del contingut amb 1-2 paraules importants substituïdes "
            "per ___. Retorna ÚNICAMENT JSON:\n"
            '[{"frase": "El ___ és responsable de...", "paraules": ["Alcalde"], '
            '"posicions": [1]}]\n'
            f"CONTINGUT:\n{topic_text[:2000]}"
        )
        return await self._generate_json(prompt)

    async def evaluate_answer(self, pregunta: str, resposta_usuari: str,
                               resposta_model: str) -> dict:
        prompt = (
            "Avalua la resposta de l'usuari per a un examen de tècnic C1 informàtica.\n"
            "Puntua de 0 a 10. Retorna ÚNICAMENT JSON:\n"
            '{"puntuacio": 7, "encerts": ["..."], "mancances": ["..."], '
            '"feedback": "...", "puntuacio_justificada": "..."}\n'
            f"PREGUNTA: {pregunta}\n"
            f"RESPOSTA USUARI: {resposta_usuari}\n"
            f"RESPOSTA MODEL: {resposta_model}"
        )
        return await self._generate_json(prompt)

    async def exam_readiness(self, progress_json: str, gaps_json: str,
                              exam_date: str, today: str, dies: int) -> dict:
        prompt = (
            f"L'examen és el {exam_date}. Avui és {today}. Resten {dies} dies.\n"
            "Fes una valoració realista. Retorna ÚNICAMENT JSON:\n"
            '{"readiness_pct": 65, "nota_estimada": 6.5, "temes_prioritaris": ["Tema X"], '
            '"consell_estudi": "...", "temps_recomanat_per_tema": {"tema_id": 30}}\n'
            f"PROGRÉS PER TEMA: {progress_json}\n"
            f"GAPS DEL TEMARI: {gaps_json}"
        )
        return await self._generate_json(prompt)


# Singleton
_gemini: GeminiService | None = None

def get_gemini() -> GeminiService:
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini
