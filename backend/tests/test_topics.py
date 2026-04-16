def test_get_topics_returns_20(client):
    resp = client.get("/api/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 20


def test_topic_has_required_fields(client):
    resp = client.get("/api/topics")
    topic = resp.json()[0]
    assert "overall_pct" in topic
    assert "id" in topic
    assert "title" in topic
    assert "bloc" in topic


def test_get_topic_content_returns_markdown(client):
    resp = client.get("/api/topics/general_1/content")
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert "headings" in data
    assert len(data["content"]) > 0


def test_get_topic_content_unknown_id_returns_404(client):
    resp = client.get("/api/topics/unknown_99/content")
    assert resp.status_code == 404
