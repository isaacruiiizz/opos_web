import json
from unittest.mock import AsyncMock, patch
import services.gemini as g

MOCK_TEST_QUESTIONS = [
    {"pregunta": f"Q{i}", "opcions": {"A":"a","B":"b","C":"c","D":"d"},
     "correcta": "A", "explicacio": "x"}
    for i in range(10)
]
MOCK_BREUS = [
    {"pregunta": f"Q{i}", "resposta_model": "resp", "criteris": "crit"}
    for i in range(5)
]
MOCK_SUPOSIT = {
    "enunciat": "Un usuari no pot imprimir",
    "context": "Oficina municipal",
    "punts_clau_resposta": ["Verificar cua d'impressió"],
    "criteri_correccio": "Resolució sistemàtica",
    "dificultat": "mitja"
}
MOCK_CONNECTA = [{"terme": f"T{i}", "definicio": f"D{i}"} for i in range(10)]
MOCK_BUITS = [{"frase": "El ___ és important", "paraules": ["Ple"], "posicions": [1]}
              for _ in range(8)]

def test_generate_test(client):
    with patch.object(g.GeminiService, "generate_test", AsyncMock(return_value=MOCK_TEST_QUESTIONS)):
        resp = client.post("/api/topics/general_1/practice/test/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 10

def test_generate_breus(client):
    with patch.object(g.GeminiService, "generate_breus", AsyncMock(return_value=MOCK_BREUS)):
        resp = client.post("/api/topics/general_1/practice/breus/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 5

def test_generate_suposit(client):
    with patch.object(g.GeminiService, "generate_suposit", AsyncMock(return_value=MOCK_SUPOSIT)):
        resp = client.post("/api/topics/general_1/practice/suposit/generate")
    assert resp.status_code == 200
    assert "enunciat" in resp.json()

def test_generate_connecta(client):
    with patch.object(g.GeminiService, "generate_connecta", AsyncMock(return_value=MOCK_CONNECTA)):
        resp = client.post("/api/topics/general_1/practice/connecta/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 10

def test_generate_buits(client):
    with patch.object(g.GeminiService, "generate_buits", AsyncMock(return_value=MOCK_BUITS)):
        resp = client.post("/api/topics/general_1/practice/buits/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 8

def test_evaluate_answer(client):
    mock_eval = {"puntuacio": 8, "encerts": [], "mancances": [], "feedback": "Bé", "puntuacio_justificada": ""}
    with patch.object(g.GeminiService, "evaluate_answer", AsyncMock(return_value=mock_eval)):
        resp = client.post("/api/practice/evaluate", json={
            "topic_id": "general_1",
            "mode": "breus",
            "pregunta": "Que és el Ple?",
            "resposta_usuari": "És l'òrgan...",
            "resposta_model": "El Ple és..."
        })
    assert resp.status_code == 200
    assert resp.json()["puntuacio"] == 8

def test_save_session_updates_progress(client):
    resp = client.post("/api/practice/sessions", json={
        "topic_id": "general_1",
        "mode": "test",
        "score": 8.5,
        "questions_json": "[]",
        "answers_json": "[]",
        "feedback_json": "{}"
    })
    assert resp.status_code == 201
    # Progress should be initialized
    prog = client.get("/api/progress")
    topic_prog = next((t for t in prog.json()["topics"] if t["topic_id"] == "general_1"), None)
    assert topic_prog is not None
    assert topic_prog["score_test"] == 8.5

def test_get_global_progress_structure(client):
    resp = client.get("/api/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_pct" in data
    assert "topics" in data
    assert "general_pct" in data
    assert "especific_pct" in data

def test_get_config_empty(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)

def test_set_config(client):
    resp = client.post("/api/config", json={"key": "theme", "value": "dark"})
    assert resp.status_code == 200
    assert client.get("/api/config").json().get("theme") == "dark"
