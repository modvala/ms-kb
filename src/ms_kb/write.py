"""Creating and extending notes: the only code that writes notes (design §9.1).

Every write is rendered and validated in memory first; nothing is written when
validation fails. Extending only appends to sections and lists, so existing
text is never rewritten (US-10).
"""

import os
from dataclasses import dataclass, field
from datetime import date
from importlib.resources import files
from pathlib import Path

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ms_kb.notes import (
    PROFILE,
    Note,
    append_to_section,
    merge_list,
    note_rel_path,
    parse,
    parse_fragment,
    q,
    render,
    wikilink,
)
from ms_kb.provenance import stamp
from ms_kb.schema import validate
from ms_kb.search import find_duplicates


class WriteError(Exception):
    def __init__(self, messages: list[str]):
        super().__init__("; ".join(messages))
        self.messages = messages


@dataclass
class Result:
    path: Path
    rel: str
    action: str  # created | extended | unchanged
    text: str
    original: str | None = None
    sections: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def today() -> str:
    return date.today().isoformat()


def _template_body(note_type: str, title: str, day: str) -> str:
    text = (files("ms_kb") / "templates" / f"{note_type}.md").read_text(encoding="utf-8")
    return parse(text).body.replace("{{title}}", title).replace("{{date:YYYY-MM-DD}}", day)


def _add_related_links(body: str, links: list[str]) -> str:
    for link in links:
        body, _ = append_to_section(body, "Related", f"- {link}")
    return body


def new_note(
    vault: Path,
    note_type: str,
    title: str,
    topics: list[str],
    *,
    body: str | None = None,
    slug: str | None = None,
    aliases: list[str] = (),
    related: list[str] = (),
    sources: list[str] = (),
    url: str | None = None,
    as_of: str | None = None,
    session_date: str | None = None,
    skill: str | None = None,
    allow_similar: bool = False,
) -> Result:
    day = today()
    if note_type == "learning-session":
        session_date = session_date or day
    rel = note_rel_path(note_type, title, slug, session_date)

    exact, similar = find_duplicates(vault, note_type, title, list(aliases), rel)
    if exact:
        raise WriteError([f"already exists: {', '.join(exact)}; add to it with kb extend"])
    if similar and not allow_similar:
        raise WriteError(
            [
                f"similar notes exist: {', '.join(similar)}; add to one of them with kb extend, "
                "or pass --allow-similar if this is a different topic"
            ]
        )

    links = [wikilink(r) for r in related]
    meta = CommentedMap()
    meta["type"] = note_type
    meta["title"] = q(title)
    if url is not None:
        meta["url"] = q(url)
    if note_type == "research":
        meta["as_of"] = q(as_of or day)
    if note_type == "learning-session":
        meta["session_date"] = q(session_date)
    meta["created"] = q(day)
    meta["updated"] = q(day)
    meta["topics"] = CommentedSeq(topics)
    for key, values in (("related", links), ("sources", list(sources)), ("aliases", list(aliases))):
        if values:
            meta[key] = CommentedSeq(q(v) if v.startswith("[[") else v for v in values)
    warnings = []
    if skill:
        meta["created_by"], warnings = stamp(skill, day)

    if body is None:
        text_body = _template_body(note_type, title, day)
    else:
        text_body = body.strip()
        if not text_body.startswith("# "):
            text_body = f"# {title}\n\n{text_body}"
        text_body = f"\n{text_body}\n"
    note = Note(meta, _add_related_links(text_body, links))

    report = validate(note, rel)
    if report.errors:
        raise WriteError(report.errors)
    return Result(vault / rel, rel.as_posix(), "created", render(note), warnings=warnings + report.warnings)


def resolve_in_vault(vault: Path, path: str) -> Path:
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = vault / target
    target = target.resolve()
    if not target.is_relative_to(vault.resolve()):
        raise WriteError([f"{path} is outside the vault {vault}"])
    if not target.is_file():
        if target == (vault / PROFILE).resolve():
            raise WriteError([f"{PROFILE} is missing; run kb doctor to see how to restore it"])
        raise WriteError([f"{path} not found in the vault; find notes with kb search"])
    return target


def extend_note(
    vault: Path,
    path: str,
    *,
    fragment: str | None = None,
    summary: str | None = None,
    topics: list[str] = (),
    related: list[str] = (),
    sources: list[str] = (),
    skill: str | None = None,
) -> Result:
    vault = vault.resolve()
    target = resolve_in_vault(vault, path)
    rel = target.relative_to(vault).as_posix()
    is_profile = rel == PROFILE
    if skill and not summary:
        raise WriteError(["--summary is required with --skill"])
    if is_profile and (topics or related or sources):
        raise WriteError([f"{PROFILE} takes only section text"])

    original = target.read_text(encoding="utf-8")
    note = parse(original)
    sections, skipped = [], []

    def add(name: str, content: str) -> None:
        new_body, sk = append_to_section(note.body, name, content)
        skipped.extend(sk)
        if new_body != note.body:
            note.body = new_body
            if name not in sections:
                sections.append(name)

    for name, content in parse_fragment(fragment or ""):
        add(name, content)

    lists_changed = False
    links = [wikilink(r) for r in related]
    for key, values in (("topics", list(topics)), ("related", links), ("sources", list(sources))):
        if values and merge_list(note.meta, key, values):
            lists_changed = True
    for link in links:
        add("Related", f"- {link}")

    if not sections and not lists_changed:
        return Result(target, rel, "unchanged", original, original, skipped=skipped)

    day = today()
    note.meta["updated"] = q(day)
    warnings = []
    if skill and not is_profile:
        entry, warnings = stamp(skill, day, summary)
        updates = note.meta.get("updates")
        if updates is None:
            updates = note.meta["updates"] = CommentedSeq()
        updates.append(entry)

    if not is_profile:
        report = validate(note, Path(rel))
        if report.errors:
            raise WriteError([f"{rel}: {e}" for e in report.errors])
        warnings += report.warnings
    return Result(target, rel, "extended", render(note), original, sections, skipped, warnings)


def save(result: Result) -> None:
    """Write a created or extended note; refuse if the file changed meanwhile."""
    if result.action == "unchanged":
        return
    path = result.path
    if result.action == "created":
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as f:
            f.write(result.text)
        return
    if path.read_text(encoding="utf-8") != result.original:
        raise WriteError([f"{result.rel} changed on disk while it was being extended; run the command again"])
    tmp = path.with_name(f".{path.name}.ms-kb-tmp")
    tmp.write_text(result.text, encoding="utf-8")
    os.replace(tmp, path)
