import re
from pathlib import Path


def parse_topics(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    topics = []
    current_bloc = None
    current_topic = None
    current_lines: list[str] = []
    counters = {"general": 0, "especific": 0, "importants": 0}

    for line in lines:
        if re.match(r"^## Bloc General", line):
            current_bloc = "general"
        elif re.match(r"^## Bloc Específic", line):
            current_bloc = "especific"
        elif re.match(r"^## Temes a tenir en compte", line):
            current_bloc = "importants"
        elif re.match(r"^### Tema \d+", line) and current_bloc:
            if current_topic is not None:
                _finalise(current_topic, current_lines)
                topics.append(current_topic)
            counters[current_bloc] += 1
            n = counters[current_bloc]
            title = re.sub(r"^### Tema \d+:?\s*", "", line).strip()
            current_topic = {
                "id": f"{current_bloc}_{n}",
                "bloc": current_bloc,
                "number": n,
                "title": title,
            }
            current_lines = []
        elif current_topic is not None:
            current_lines.append(line)

    if current_topic is not None:
        _finalise(current_topic, current_lines)
        topics.append(current_topic)

    return topics


def _finalise(topic: dict, lines: list[str]):
    content = "\n".join(lines).strip()
    topic["content"] = content
    topic["headings"] = extract_headings(content)


def extract_headings(content: str) -> list[dict]:
    headings = []
    for line in content.splitlines():
        m = re.match(r"^(#{2,6})\s+(.+)", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            anchor = re.sub(r"[^\w\s-]", "", text.lower()).strip()
            anchor = re.sub(r"\s+", "-", anchor)
            headings.append({"level": level, "text": text, "anchor": anchor})
    return headings


# Module-level cache keyed on resolved path — parse once per path per process
_cache: dict[Path, list[dict]] = {}


def get_topics(path: Path) -> list[dict]:
    key = path.resolve()
    mtime = key.stat().st_mtime if key.exists() else 0
    if key not in _cache or _cache[key][0] != mtime:
        _cache[key] = (mtime, parse_topics(path))
    return _cache[key][1]


def get_topic_by_id(topic_id: str, path: Path) -> dict | None:
    return next((t for t in get_topics(path) if t["id"] == topic_id), None)


def invalidate_cache(path: Path | None = None):
    if path:
        _cache.pop(path.resolve(), None)
    else:
        _cache.clear()


def extract_flash_check(content: str) -> str:
    """Extreu el text del bloc 'Resum de conceptes clau (Flash-Check)' d'un tema.
    Si no existeix, retorna les primeres 300 chars del contingut."""
    lines = content.splitlines()
    in_flash = False
    result = []
    for line in lines:
        if re.match(r"^#{1,6}\s.*[Ff]lash", line):
            in_flash = True
            continue
        if in_flash:
            if re.match(r"^#{1,6}\s", line):
                break
            result.append(line)
    if result:
        return " ".join(" ".join(result).split())[:400]
    return " ".join(content.split())[:300]
