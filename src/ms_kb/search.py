"""Search by type, topics, frontmatter fields and text; duplicate detection.

No index and no embeddings (US-08): the vault is scanned on every call.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from ms_kb.notes import TYPE_DIRS, Note, NoteError, read_note

SIMILARITY = 0.85


def note_files(vault: Path) -> Iterator[Path]:
    """Markdown files in the type folders, in a stable order."""
    for folder in TYPE_DIRS.values():
        yield from sorted((vault / folder).rglob("*.md"))


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

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "type": self.type,
            "title": self.title,
            "topics": self.topics,
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
    meta = note.meta
    score = 0
    title = str(meta.get("title", "")).casefold()
    aliases = [a.casefold() for a in _strings(meta.get("aliases"))]
    if term in (title, path.stem.casefold(), *aliases):
        score += 20
    elif term in title or term in path.stem.casefold():
        score += 10
    elif any(term in a for a in aliases):
        score += 8
    if any(term.replace(" ", "-") in t.casefold() for t in _strings(meta.get("topics"))):
        score += 5
    score += min(note.body.casefold().count(term), 5)
    return score


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
    topics: list[str] = (),
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
        if any(t not in note_topics for t in topics):
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


def find_duplicates(
    vault: Path, note_type: str, title: str, aliases: list[str], rel_path: Path
) -> tuple[list[str], list[str]]:
    """(exact, similar) relative paths of notes a new note would duplicate.

    Exact: the same file, the same file name in any folder (it would make
    [[links]] ambiguous), or the same title/alias within the type. Similar:
    a close title within the type. Learning sessions are dated and expected to
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
        if keys & theirs:
            exact.append(rel)
        elif any(SequenceMatcher(None, a, b).ratio() >= SIMILARITY for a in keys for b in theirs):
            similar.append(rel)
    if not exact and (vault / rel_path).exists():
        exact.append(rel_path.as_posix())
    return exact, similar
