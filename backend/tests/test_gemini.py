import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.fixture
def gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from services import gemini as g
    return g.GeminiService()

@pytest.mark.asyncio
async def test_generate_json_strips_markdown_fences(gemini):
    mock_response = MagicMock()
    mock_response.text = '```json\n[{"a": 1}]\n```'
    mock_response.usage_metadata = None
    with patch.object(gemini.client.aio.models, "generate_content",
                      AsyncMock(return_value=mock_response)):
        result = await gemini._generate_json("test prompt")
    assert result == [{"a": 1}]

@pytest.mark.asyncio
async def test_generate_flashcards_returns_15(gemini):
    cards = [{"terme": f"t{i}", "definicio": f"d{i}", "exemple": ""} for i in range(15)]
    mock_response = MagicMock()
    mock_response.text = json.dumps(cards)
    mock_response.usage_metadata = None
    with patch.object(gemini.client.aio.models, "generate_content",
                      AsyncMock(return_value=mock_response)):
        result = await gemini.generate_flashcards("content", "Tema 1")
    assert len(result) == 15
    assert all("terme" in c for c in result)

@pytest.mark.asyncio
async def test_generate_test_returns_10_questions(gemini):
    questions = [
        {"pregunta": f"Q{i}", "opcions": {"A": "", "B": "", "C": "", "D": ""},
         "correcta": "A", "explicacio": ""}
        for i in range(10)
    ]
    mock_response = MagicMock()
    mock_response.text = json.dumps(questions)
    mock_response.usage_metadata = None
    with patch.object(gemini.client.aio.models, "generate_content",
                      AsyncMock(return_value=mock_response)):
        result = await gemini.generate_test("content")
    assert len(result) == 10

@pytest.mark.asyncio
async def test_evaluate_answer_returns_score(gemini):
    evaluation = {
        "puntuacio": 7,
        "encerts": ["bon punt"],
        "mancances": [],
        "feedback": "Molt bé",
        "puntuacio_justificada": "Resposta completa"
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(evaluation)
    mock_response.usage_metadata = None
    with patch.object(gemini.client.aio.models, "generate_content",
                      AsyncMock(return_value=mock_response)):
        result = await gemini.evaluate_answer("pregunta", "resposta", "model")
    assert result["puntuacio"] == 7
