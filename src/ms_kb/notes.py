"""Notes: frontmatter, file names and body sections (note-schema-v0 §1–§4)."""

import re
import unicodedata
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

TYPE_DIRS = {
    "concept": "concepts",
    "source": "sources",
    "research": "research",
    "learning-session": "learning-sessions",
    "project": "projects",
}
NOTE_TYPES = tuple(TYPE_DIRS)
PROFILE = "learning_profile.md"

_FRONTMATTER = re.compile(r"\A---\n(.*?)^---[ \t]*\n?", re.S | re.M)
_FORBIDDEN = re.compile(r'[/\\:*?"<>|#^\[\]]')
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class NoteError(Exception):
    pass


def _yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def q(value: str) -> DoubleQuotedScalarString:
    """A string that is written in double quotes, like the dates in the templates."""
    return DoubleQuotedScalarString(value)


@dataclass
class Note:
    meta: CommentedMap
    body: str


def parse(text: str) -> Note:
    match = _FRONTMATTER.match(text)
    if not match:
        return Note(CommentedMap(), text)
    try:
        meta = _yaml().load(match.group(1)) or CommentedMap()
    except YAMLError as e:
        raise NoteError(f"invalid frontmatter: {e}") from None
    if not isinstance(meta, dict):
        raise NoteError("frontmatter is not a mapping")
    return Note(meta, text[match.end() :])


def render(note: Note) -> str:
    buf = StringIO()
    _yaml().dump(note.meta, buf)
    return f"---\n{buf.getvalue()}---\n{note.body}"


def read_note(path: Path) -> Note:
    return parse(path.read_text(encoding="utf-8"))


# --- file names -------------------------------------------------------------


def file_title(title: str) -> str:
    """The title with characters that are not allowed in file names removed."""
    return re.sub(r"\s+", " ", _FORBIDDEN.sub("", title)).strip().strip(".")


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "-".join(re.findall(r"[a-z0-9]+", ascii_text.lower()))


def note_rel_path(note_type: str, title: str, slug: str | None = None, session_date: str | None = None) -> Path:
    """Path of a new note relative to the vault (note-schema-v0 §4)."""
    folder = Path(TYPE_DIRS[note_type])
    if note_type in ("research", "learning-session"):
        if slug is None:
            slug = slugify(title)
            if not slug:
                raise NoteError(f"cannot build an ASCII slug from {title!r}; pass --slug")
        elif not SLUG.fullmatch(slug):
            raise NoteError(f"slug {slug!r} is not lowercase ASCII words joined by '-'")
        name = f"{session_date}-{slug}" if note_type == "learning-session" else slug
    else:
        name = file_title(title)
        if not name:
            raise NoteError(f"title {title!r} gives an empty file name")
    return folder / f"{name}.md"


# --- frontmatter lists ------------------------------------------------------


def wikilink(name: str) -> str:
    name = name.strip()
    return name if name.startswith("[[") else f"[[{name}]]"


def merge_list(meta: CommentedMap, key: str, values: list[str]) -> list[str]:
    """Append values missing from meta[key]; returns the values actually added."""
    current = meta.get(key)
    if current is None:
        current = CommentedSeq()
        # Keep lists above the provenance blocks, as in new notes.
        keys = list(meta)
        at = next((i for i, k in enumerate(keys) if k in ("created_by", "updates")), len(keys))
        meta.insert(at, key, current)
    elif not isinstance(current, list):
        raise NoteError(f"{key!r} is not a list")
    present = {str(v) for v in current}
    added = []
    for value in values:
        if value not in present:
            current.append(q(value) if value.startswith("[[") else value)
            present.add(value)
            added.append(value)
    return added


# --- body sections ----------------------------------------------------------

_HEADING = re.compile(r"^(#{1,2}) +(.+?)\s*#*\s*$")
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line index, level, name) of `#` and `##` headings outside code fences."""
    result, fence = [], None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else (fence or marker)
            continue
        if fence is None and (m := _HEADING.match(line.rstrip("\n"))):
            result.append((i, len(m.group(1)), m.group(2)))
    return result


def section_names(body: str) -> list[str]:
    return [name for _, level, name in _headings(body.splitlines()) if level == 2]


def _section_span(lines: list[str], name: str) -> tuple[int, int] | None:
    """Line range (heading, end) of the `## name` section; end is exclusive."""
    heads = _headings(lines)
    for n, (i, level, title) in enumerate(heads):
        if level == 2 and title.casefold() == name.casefold():
            end = next((j for j, _, _ in heads[n + 1 :]), len(lines))
            return i, end
    return None


def _is_bullet(line: str) -> bool:
    return bool(_BULLET.match(line))


def append_to_section(body: str, name: str, text: str) -> tuple[str, list[str]]:
    """Append `text` to the end of the `## name` section, creating it if missing.

    Bullet lines already present in the section are skipped. Returns the new body
    and the skipped lines; the body is unchanged when nothing is left to add.
    """
    lines = body.splitlines()
    span = _section_span(lines, name)
    existing = {l.strip() for l in lines[span[0] + 1 : span[1]]} if span else set()

    new, skipped = [], []
    for line in text.strip("\n").splitlines():
        if _is_bullet(line) and line.strip() in existing:
            skipped.append(line.strip())
        else:
            new.append(line.rstrip())
    while new and not new[-1].strip():
        new.pop()
    if not any(l.strip() for l in new):
        return body, skipped

    if span is None:
        related = _section_span(lines, "Related") if name.casefold() != "related" else None
        at = related[0] if related else len(lines)
        head = lines[:at]
        while head and not head[-1].strip():
            head.pop()
        block = ["", f"## {name}", "", *new, ""]
        lines = head + block + lines[at:]
    else:
        start, end = span
        content = lines[start + 1 : end]
        while content and not content[-1].strip():
            content.pop()
        last = next((l for l in reversed(content) if l.strip()), None)
        gap = [] if last and _is_bullet(last) and _is_bullet(new[0]) else [""]
        if not content:
            gap = [""]
        tail = [""] if end < len(lines) else []
        lines = lines[: start + 1] + content + gap + new + tail + lines[end:]
    return "\n".join(lines).rstrip("\n") + "\n", skipped


def parse_fragment(text: str) -> list[tuple[str, str]]:
    """Split a Markdown fragment into (section name, content) by `## ` headings."""
    lines = text.strip("\n").splitlines()
    heads = [(i, name) for i, level, name in _headings(lines) if level == 2]
    if any(level == 1 for _, level, _ in _headings(lines)):
        raise NoteError("the fragment must not contain a '# ' title; use '## Section' headings")
    first = heads[0][0] if heads else len(lines)
    if any(l.strip() for l in lines[:first]):
        raise NoteError("text before the first '## Section' heading; every block must start with '## Section'")
    result = []
    for n, (i, name) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        result.append((name, "\n".join(lines[i + 1 : end]).strip("\n")))
    return result
