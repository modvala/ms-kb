"""Search by type, tags, frontmatter fields and text; duplicate detection.

No index and no embeddings (US-08): the vault is scanned on every call.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ms_kb.notes import TYPE_DIRS, Note, NoteError, read_note

SIMILARITY = 0.85


RESTORED_COPY = re.compile(r"\.restored-\d{8}-\d{6}\.md$")


def note_files(vault: Path) -> Iterator[Path]:
    """Markdown files in the type folders, in a stable order; kb restore side copies are left out."""
    for folder in TYPE_DIRS.values():
        yield from (p for p in sorted((vault / folder).rglob("*.md")) if not RESTORED_COPY.search(p.name))


def iter_notes(vault: Path) -> Iterator[tuple[Path, Note]]:
    """(path, note) for every parsable note; files with broken frontmatter are skipped."""
    for path in note_files(vault):
        try:
            yield path, read_note(path)
        except (NoteError, UnicodeDecodeError):
            continue


@dataclass
class Hit:
    path: Path
    rel: str
    type: str
    title: str
    topics: list[str]
    updated: str
    score: int
    snippet: str
    tags: list[str] = field(default_factory=list)
    summary: str = ""

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "type": self.type,
            "title": self.title,
            "topics": self.topics,
            "tags": self.tags,
            "summary": self.summary,
            "updated": self.updated,
            "score": self.score,
            "snippet": self.snippet,
        }


def field_values(meta, dotted: str) -> list:
    """Leaf values at a dotted path; lists along the way are flattened."""
    values = [meta]
    for key in dotted.split("."):
        nxt = []
        for v in values:
            items = v if isinstance(v, list) else [v]
            nxt += [i[key] for i in items if isinstance(i, dict) and key in i]
        values = nxt
    flat = []
    for v in values:
        flat += v if isinstance(v, list) else [v]
    return flat


def _strings(value) -> list[str]:
    if value is None:
        return []
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def _score(term: str, path: Path, note: Note) -> int:
    """Title and aliases outrank summary and tags, which outrank the body (design §10.4)."""
    meta = note.meta
    score = 0
    title = str(meta.get("title", "")).casefold()
    aliases = [a.casefold() for a in _strings(meta.get("aliases"))]
    if term in (title, path.stem.casefold(), *aliases):
        score += 100
    elif term in title or term in path.stem.casefold():
        score += 50
    elif any(term in a for a in aliases):
        score += 40
    if term in str(meta.get("summary", "")).casefold():
        score += 6
    labels = _strings(meta.get("tags")) + _strings(meta.get("topics"))
    if any(term.replace(" ", "-") in t.casefold() for t in labels):
        score += 6
    if any(term in str(meta.get(key, "")).casefold() for key in ("url", "ref", "author")):
        score += 6
    score += min(note.body.casefold().count(term), 5)
    return score


def tag_matches(wanted: str, tag: str) -> bool:
    """`python` matches `python` and `python/concurrency` (design §5.3)."""
    return tag == wanted or tag.startswith(f"{wanted}/")


def _snippet(body: str, terms: list[str]) -> str:
    lines = [l.strip() for l in body.splitlines() if l.strip() and not l.lstrip().startswith(("#", "<!--"))]
    for term in terms:
        for line in lines:
            if term in line.casefold():
                return line[:160]
    return lines[0][:160] if lines else ""


def search(
    vault: Path,
    terms: list[str] = (),
    note_type: str | None = None,
    tags: list[str] = (),
    fields: dict[str, str] | None = None,
    limit: int | None = None,
) -> list[Hit]:
    terms = [t.casefold() for t in terms if t.strip()]
    hits = []
    for path, note in iter_notes(vault):
        meta = note.meta
        if note_type and meta.get("type") != note_type:
            continue
        note_topics = _strings(meta.get("topics"))
        note_tags = _strings(meta.get("tags"))
        if any(not any(tag_matches(t, have) for have in note_tags + note_topics) for t in tags):
            continue
        if fields and any(v not in map(str, field_values(meta, k)) for k, v in fields.items()):
            continue
        scores = [_score(t, path, note) for t in terms]
        if any(s == 0 for s in scores):
            continue
        hits.append(
            Hit(
                path=path,
                rel=path.relative_to(vault).as_posix(),
                type=str(meta.get("type", "")),
                title=str(meta.get("title", path.stem)),
                topics=note_topics,
                updated=str(meta.get("updated", "")),
                score=sum(scores),
                snippet=_snippet(note.body, terms),
                tags=note_tags,
                summary=str(meta.get("summary", "")),
            )
        )
    # Stable sorts: best score first, then the most recently updated, then by path.
    hits.sort(key=lambda h: h.rel)
    hits.sort(key=lambda h: h.updated, reverse=True)
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit] if limit else hits


# --- duplicates -------------------------------------------------------------


def norm(text: str) -> str:
    return "".join(ch for ch in text.casefold() if ch.isalnum())


def norm_url(url: str) -> str:
    """Lowercase scheme and host, no fragment, trailing slash or `utm_*` parameters (design §6.9)."""
    try:
        parts = urlsplit(url.strip())
    except ValueError:  # malformed, say an unclosed IPv6 bracket: compare it as text
        return url.strip().lower()
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                       if not k.lower().startswith("utm_")])
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


def find_duplicates(
    vault: Path, note_type: str, title: str, aliases: list[str], rel_path: Path, url: str | None = None
) -> tuple[list[str], list[str]]:
    """(exact, similar) relative paths of notes a new note would duplicate.

    Exact: the same file, the same file name in any folder (it would make
    [[links]] ambiguous), the same title/alias within the type or, for a source
    card, the same normalized URL. Similar: a close title or alias within the
    type. Learning sessions are dated and expected to
    repeat a topic, so only the file itself counts for them.
    """
    exact, similar = [], []
    if note_type == "learning-session":
        return ([rel_path.as_posix()] if (vault / rel_path).exists() else []), similar

    stem = norm(rel_path.stem)
    keys = {norm(title)} | {norm(a) for a in aliases}
    keys.discard("")
    for path, note in iter_notes(vault):
        rel = path.relative_to(vault).as_posix()
        meta = note.meta
        if norm(path.stem) == stem:
            exact.append(rel)
            continue
        if meta.get("type") != note_type:
            continue
        theirs = {norm(str(meta.get("title", "")))} | {norm(a) for a in _strings(meta.get("aliases"))}
        theirs.discard("")
        same_url = url and meta.get("url") and norm_url(url) == norm_url(str(meta["url"]))
        if same_url or keys & theirs:
            exact.append(rel)
        elif any(SequenceMatcher(None, a, b).ratio() >= SIMILARITY for a in keys for b in theirs):
            similar.append(rel)
    if not exact and (vault / rel_path).exists():
        exact.append(rel_path.as_posix())
    return exact, similar
