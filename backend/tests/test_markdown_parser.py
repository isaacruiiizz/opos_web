from pathlib import Path
from services.markdown_parser import parse_topics, extract_headings

NOTES_FILE = Path(__file__).parent.parent.parent / "data" / "ApuntsTemari.md"


def test_parse_produces_20_topics():
    topics = parse_topics(NOTES_FILE)
    assert len(topics) == 20


def test_general_bloc_has_5_topics():
    topics = parse_topics(NOTES_FILE)
    general = [t for t in topics if t["bloc"] == "general"]
    assert len(general) == 5


def test_especific_bloc_has_15_topics():
    topics = parse_topics(NOTES_FILE)
    especific = [t for t in topics if t["bloc"] == "especific"]
    assert len(especific) == 15


def test_topic_has_required_fields():
    topic = parse_topics(NOTES_FILE)[0]
    assert all(k in topic for k in ("id", "bloc", "number", "title", "content", "headings"))


def test_topic_ids_are_unique():
    topics = parse_topics(NOTES_FILE)
    ids = [t["id"] for t in topics]
    assert len(ids) == len(set(ids))


def test_topic_content_is_not_empty():
    topics = parse_topics(NOTES_FILE)
    for t in topics:
        assert len(t["content"]) > 100, f"Topic {t['id']} has too little content"


def test_extract_headings_returns_level_and_text():
    content = "#### 1. Introducció\n\nText\n\n##### A. Sub\n"
    headings = extract_headings(content)
    assert headings[0]["level"] == 4
    assert headings[0]["text"] == "1. Introducció"
