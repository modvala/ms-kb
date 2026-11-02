"""`kb index`: the catalogue generated from frontmatter on every call (design §10.1).

Nothing is written to the vault, so the index cannot drift from the pages.
"""

from dataclasses import dataclass, field
from pathlib import Path

from ms_kb.links import LINK, Resolver, normalize
from ms_kb.notes import is_bullet, meta_list, section_text
from ms_kb.schema import is_page
from ms_kb.search import iter_notes, tag_matches

NO_TAG = "(no tag)"


@dataclass
class Entry:
    path: Path
    title: str
    summary: str
    tags: list[str] = field(default_factory=list)
    open_questions: int = 0
    used_by: int = 0
    kind: str = "topic"

    def as_dict(self) -> dict:
        result = {"path": str(self.path), "title": self.title, "summary": self.summary, "tags": self.tags}
        if self.kind == "source":
            return result | {"used_by": self.used_by}
        return result | {"open_questions": self.open_questions}

    def line(self) -> str:
        if self.kind == "source":
            count = f"used by {self.used_by} topic{'s' if self.used_by != 1 else ''}"
            return f"[[{self.title}]] — {self.summary} — {count if self.used_by else 'not used yet'}"
        n = self.open_questions
        return f"[[{self.title}]] — {self.summary} ({n} open question{'s' if n != 1 else ''})"


def _open_questions(body: str) -> int:
    lines = [l for l in (section_text(body, "Open questions") or "").splitlines() if l.strip()]
    top = [l for l in lines if is_bullet(l) and not l.startswith((" ", "\t"))]
    return len(top) or (1 if lines else 0)


def _link_counts(vault: Path) -> dict[Path, int]:
    """Topic pages linking to each file; a page counts once per target."""
    resolver = Resolver(vault)
    counts: dict[Path, int] = {}
    for _, note in iter_notes(vault):
        if note.meta.get("type") != "topic":
            continue
        found = {path.resolve() for raw in LINK.findall(note.body)
                 if (t := normalize(raw)) and (path := resolver.find(t))}
        for path in found:
            counts[path] = counts.get(path, 0) + 1
    return counts


def entries(vault: Path, kind: str, tag: str | None = None) -> list[Entry]:
    counts = _link_counts(vault) if kind == "source" else {}
    result = []
    for path, note in iter_notes(vault):
        meta = note.meta
        if meta.get("type") != kind or not is_page(meta):
            continue
        tags = meta_list(meta, "tags")
        if tag and not any(tag_matches(tag, t) for t in tags):
            continue
        result.append(Entry(path, str(meta.get("title", path.stem)), str(meta.get("summary", "")), tags,
                            _open_questions(note.body), counts.get(path.resolve(), 0), kind))
    return sorted(result, key=lambda e: e.title.casefold())


def render(items: list[Entry], tag: str | None = None) -> list[str]:
    """Grouped by tag; nested tags as a tree under their parent, a page once under each of its tags."""
    groups: dict[str, list[Entry]] = {}
    for entry in items:
        wanted = [t for t in entry.tags if not tag or tag_matches(tag, t)]
        for t in wanted or [NO_TAG]:
            groups.setdefault(t, []).append(entry)
    for t in list(groups):
        if "/" in t:
            groups.setdefault(t.split("/", 1)[0], [])
    lines = []
    for t in sorted(groups, key=lambda name: (name == NO_TAG, name.split("/"))):
        indent = "  " if "/" in t else ""
        lines.append(f"{indent}{t}")
        lines += [f"{indent}  {entry.line()}" for entry in groups[t]]
    return lines


def tag_counts(vault: Path) -> dict[str, int]:
    """The vocabulary: tags in use on topic pages and source cards, with counts (design §5.3)."""
    counts: dict[str, int] = {}
    for _, note in iter_notes(vault):
        for t in meta_list(note.meta, "tags"):
            counts[t] = counts.get(t, 0) + 1
    return dict(sorted(counts.items()))
