import json
from unittest.mock import AsyncMock, patch

SAMPLE_CARDS = [{"terme": f"t{i}", "definicio": f"d{i}", "exemple": ""} for i in range(15)]

def test_get_flashcards_empty(client):
    resp = client.get("/api/topics/general_1/flashcards")
    assert resp.status_code == 200
    assert resp.json() == []

def test_create_flashcard_manual(client):
    payload = {"pregunta": "Que és el Ple?", "resposta": "Òrgan de govern", "exemple": "Aprova pressupostos"}
    resp = client.post("/api/topics/general_1/flashcards", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["origin"] == "manual"
    assert data["leitner_box"] == 1

def test_generate_flashcards_calls_gemini(client):
    import services.gemini as g
    mock_cards = [{"terme": f"t{i}", "definicio": f"d{i}", "exemple": ""} for i in range(15)]
    with patch.object(g.GeminiService, "generate_flashcards",
                      AsyncMock(return_value=mock_cards)):
        resp = client.post("/api/topics/general_1/flashcards/generate")
    assert resp.status_code == 200
    assert len(resp.json()) == 15

def test_review_card_promote(client):
    r = client.post("/api/topics/general_1/flashcards",
                    json={"pregunta": "Q", "resposta": "A"})
    card_id = r.json()["id"]
    resp = client.post(f"/api/flashcards/{card_id}/review", json={"knew_it": True})
    assert resp.status_code == 200
    assert resp.json()["leitner_box"] == 2

def test_review_card_demote(client):
    r = client.post("/api/topics/general_1/flashcards",
                    json={"pregunta": "Q", "resposta": "A"})
    card_id = r.json()["id"]
    # First promote to box 3
    client.post(f"/api/flashcards/{card_id}/review", json={"knew_it": True})
    client.post(f"/api/flashcards/{card_id}/review", json={"knew_it": True})
    # Now demote
    resp = client.post(f"/api/flashcards/{card_id}/review", json={"knew_it": False})
    assert resp.json()["leitner_box"] == 1
