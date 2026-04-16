def test_get_annotations_empty(client):
    resp = client.get("/api/topics/general_1/annotations")
    assert resp.status_code == 200
    assert resp.json() == []

def test_post_annotation_persists(client):
    payload = {"selected_text": "L'Alcaldessa", "color": "yellow", "note": "Important"}
    resp = client.post("/api/topics/general_1/annotations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] > 0
    assert data["selected_text"] == "L'Alcaldessa"

def test_get_annotations_returns_saved(client):
    payload = {"selected_text": "Ple de l'Ajuntament", "color": "blue"}
    client.post("/api/topics/general_1/annotations", json=payload)
    resp = client.get("/api/topics/general_1/annotations")
    assert len(resp.json()) == 1
    assert resp.json()[0]["selected_text"] == "Ple de l'Ajuntament"

def test_delete_annotation(client):
    r = client.post("/api/topics/general_1/annotations",
                    json={"selected_text": "test", "color": "green"})
    ann_id = r.json()["id"]
    resp = client.delete(f"/api/annotations/{ann_id}")
    assert resp.status_code == 204
    assert client.get("/api/topics/general_1/annotations").json() == []

def test_get_drawing_empty(client):
    resp = client.get("/api/topics/general_1/drawings")
    assert resp.status_code == 200
    assert resp.json()["canvas_json"] == "{}"

def test_post_drawing_persists(client):
    payload = {"canvas_json": '{"objects":[{"type":"path"}]}'}
    resp = client.post("/api/topics/general_1/drawings", json=payload)
    assert resp.status_code == 200
    assert client.get("/api/topics/general_1/drawings").json()["canvas_json"] == payload["canvas_json"]

def test_delete_nonexistent_annotation(client):
    resp = client.delete("/api/annotations/99999")
    assert resp.status_code == 404
