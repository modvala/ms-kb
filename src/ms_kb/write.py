"""Creating and changing notes: the only code that writes notes (design §9.1).

Every write is rendered and validated in memory first; nothing is written when
validation fails. `kb extend` and `kb link` only append; replacing text is
possible only through `rewrite_note`, behind the approval hash the CLI checks
(design §11.3), and `my_words_note`, which holds the user's own text (design §11.6).
"""

import os
from dataclasses import dataclass, field
from datetime import date
from importlib.resources import files
from pathlib import Path

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ms_kb.links import LINK, Resolver, normalize
from ms_kb.notes import (
    MY_WORDS,
    PROFILE,
    SOURCE_SECTIONS,
    TOPIC_SECTIONS,
    Note,
    append_to_section,
    has_heading,
    merge_list,
    note_rel_path,
    parse,
    parse_fragment,
    q,
    render,
    replace_section,
    section_text,
    wikilink,
)
from ms_kb.provenance import skill_warnings, stamp
from ms_kb.schema import is_page, validate
from ms_kb.search import find_duplicates


class WriteError(Exception):
    def __init__(self, messages: list[str]):
        super().__init__("; ".join(messages))
        self.messages = messages


@dataclass
class Result:
    path: Path
    rel: str
    action: str  # created | extended | rewritten | linked | my-words | unchanged
    text: str
    original: str | None = None
    sections: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reason: str | None = None


PAGE_TYPES = ("topic", "source")


def _order(meta) -> tuple[str, ...]:
    """The fixed sections of a topic page or a source card; v1 notes have none."""
    if not is_page(meta):
        return ()
    return TOPIC_SECTIONS if meta.get("type") == "topic" else SOURCE_SECTIONS


def one_line(text: str | None) -> str | None:
    return " ".join(text.split()) if text else None


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
    topics: list[str] = (),
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
    summary: str | None = None,
    tags: list[str] = (),
    created: str | None = None,
    ref: str | None = None,
    author: str | None = None,
    published: str | None = None,
) -> Result:
    is_new_page = note_type in PAGE_TYPES
    if is_new_page and (topics or related or sources):
        raise WriteError(["topic pages and source cards use --tag; links and sources go in the body"])
    if not is_new_page and (summary or tags or ref or author or published):
        raise WriteError([f"--summary, --tag, --ref, --author and --published do not apply to {note_type} notes"])
    if note_type == "topic" and url:
        raise WriteError(["--url applies to source cards; a topic page lists sources under ## Sources"])
    if note_type != "source" and (ref or author or published):
        raise WriteError(["--ref, --author and --published apply to source cards"])

    day = today()
    if note_type == "learning-session":
        session_date = session_date or day
    rel = note_rel_path(note_type, title, slug, session_date)

    exact, similar = find_duplicates(vault, note_type, title, list(aliases), rel, url)
    update = {"topic": "update it with kb rewrite", "source": "add to it with kb extend"}.get(
        note_type, "add to it with kb extend")
    if exact:
        raise WriteError([f"already exists: {', '.join(exact)}; {update}"])
    if similar and not allow_similar:
        raise WriteError(
            [
                f"similar notes exist: {', '.join(similar)}; update one of them instead, "
                "or pass --allow-similar if this is a different topic"
            ]
        )

    links = [wikilink(r) for r in related]
    meta = CommentedMap()
    meta["type"] = note_type
    meta["title"] = q(title)
    if is_new_page:
        meta["summary"] = q(summary or "")
    for key, value in (("url", url), ("ref", ref), ("author", author), ("published", published)):
        if value is not None:
            meta[key] = q(value)
    if is_new_page:
        meta["tags"] = CommentedSeq(tags)
    if note_type == "research":
        meta["as_of"] = q(as_of or day)
    if note_type == "learning-session":
        meta["session_date"] = q(session_date)
    meta["created"] = q(created or day)
    meta["updated"] = q(day)
    if is_new_page:
        if aliases:
            meta["aliases"] = CommentedSeq(aliases)
    else:
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
    if note_type == "topic":
        if (section_text(text_body, MY_WORDS) or "").strip():
            raise WriteError([f"## {MY_WORDS} holds only the user's text: create the page without it, "
                              "then save the text with kb my-words"])
        text_body = replace_section(text_body, MY_WORDS, "", TOPIC_SECTIONS)
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
    reason: str | None = None,
    topics: list[str] = (),
    related: list[str] = (),
    sources: list[str] = (),
    skill: str | None = None,
) -> Result:
    vault = vault.resolve()
    target = resolve_in_vault(vault, path)
    rel = target.relative_to(vault).as_posix()
    is_profile = rel == PROFILE
    if skill and not reason and not is_profile:
        raise WriteError(["--reason is required with --skill"])
    if is_profile and (topics or related or sources):
        raise WriteError([f"{PROFILE} takes only section text"])

    original = target.read_text(encoding="utf-8")
    note = parse(original)
    order = _order(note.meta)
    if order and (topics or related or sources):
        raise WriteError(["topic pages and source cards take only section text; add links with kb link"])
    sections, skipped = [], []

    def add(name: str, content: str) -> None:
        new_body, sk = append_to_section(note.body, name, content, order)
        skipped.extend(sk)
        if new_body != note.body:
            note.body = new_body
            if name not in sections:
                sections.append(name)

    for name, content in parse_fragment(fragment or ""):
        if order and name.casefold() == MY_WORDS.casefold():
            raise WriteError([f"## {MY_WORDS} changes only through kb my-words"])
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

    note.meta["updated"] = q(today())
    warnings = skill_warnings(skill)
    if not is_profile:
        report = validate(note, Path(rel))
        if report.errors:
            raise WriteError([f"{rel}: {e}" for e in report.errors])
        warnings += report.warnings
    return Result(target, rel, "extended", render(note), original, sections, skipped, warnings, one_line(reason))


def rewrite_note(
    vault: Path,
    path: str,
    body: str,
    *,
    reason: str,
    summary: str | None = None,
    tags: list[str] = (),
    aliases: list[str] = (),
    skill: str | None = None,
) -> Result:
    """The page with a new body, as the approval hash will cover it (design §11.3).

    Only topic pages and the profile are rewritten: source cards and v1 notes stay append-only.
    """
    vault = vault.resolve()
    target = resolve_in_vault(vault, path)
    rel = target.relative_to(vault).as_posix()
    is_profile = rel == PROFILE
    original = target.read_text(encoding="utf-8")
    note = parse(original)
    if not is_profile and note.meta.get("type") != "topic":
        raise WriteError([f"{rel}: kb rewrite works on topic pages and {PROFILE}; "
                          f"this is a {note.meta.get('type', 'file without a type')}"])
    if is_profile and (summary or tags or aliases):
        raise WriteError([f"{PROFILE} takes only a body"])
    if not one_line(reason):
        raise WriteError(["--reason is empty: say why the page changes"])
    text = body.strip()
    if not text:
        raise WriteError(["the draft is empty"])
    if parse(text).meta:
        raise WriteError(["the draft must be the page body without frontmatter; pass --summary, --tag and --alias"])
    title = note.meta.get("title")
    if title and not text.startswith("# "):
        text = f"# {title}\n\n{text}"
    new_body = f"\n{text}\n"
    if not is_profile:
        current = section_text(note.body, MY_WORDS) or ""
        if section_text(new_body, MY_WORDS) not in (None, current):
            raise WriteError([f"the draft changes ## {MY_WORDS}, which holds only the user's text; "
                              f"leave it out or keep it as it is (kb my-words saves the user's text)"])
        new_body = replace_section(new_body, MY_WORDS, current, TOPIC_SECTIONS)

    meta = note.meta
    changed = new_body != note.body
    if summary is not None and summary != meta.get("summary"):
        meta["summary"] = q(summary)
        changed = True
    for key, values in (("tags", tags), ("aliases", aliases)):
        if values and list(values) != list(meta.get(key) or []):
            meta[key] = CommentedSeq(values)
            changed = True
    if not changed:
        return Result(target, rel, "unchanged", original, original)
    note.body = new_body
    meta["updated"] = q(today())
    warnings = skill_warnings(skill)
    if not is_profile:
        report = validate(note, Path(rel))
        if report.errors:
            raise WriteError([f"{rel}: {e}" for e in report.errors])
        warnings += report.warnings
    return Result(target, rel, "rewritten", render(note), original, warnings=warnings, reason=one_line(reason))


def link_note(vault: Path, src: str, target: str, why: str, skill: str | None = None) -> Result:
    """One `- [[TARGET]] — why` line in `## Related` of SRC (design §11.5)."""
    vault = vault.resolve()
    path = resolve_in_vault(vault, src)
    rel = path.relative_to(vault).as_posix()
    if rel == PROFILE:
        raise WriteError([f"{PROFILE} holds directions and preferences, not links"])
    why = one_line(why)
    if not why:
        raise WriteError(["--why is empty: say how the pages relate"])
    name = target.strip().removeprefix("[[").removesuffix("]]").strip()
    resolver = Resolver(vault)
    goal = normalize(name)
    found = resolver.find(goal) if goal else None
    if found is None:
        raise WriteError([f"[[{name}]] does not resolve to a page or an alias; find pages with kb index"])
    if found.resolve() == path:
        raise WriteError([f"[[{name}]] is {rel} itself"])

    original = path.read_text(encoding="utf-8")
    note = parse(original)
    line = f"- [[{name}]] — {why}"
    for raw in LINK.findall(section_text(note.body, "Related") or ""):
        known = normalize(raw)
        if known and (other := resolver.find(known)) and other.resolve() == found.resolve():
            return Result(path, rel, "unchanged", original, original, skipped=[line])
    note.body, _ = append_to_section(note.body, "Related", line, _order(note.meta))
    note.meta["updated"] = q(today())
    report = validate(note, Path(rel))
    if report.errors:
        raise WriteError([f"{rel}: {e}" for e in report.errors])
    return Result(path, rel, "linked", render(note), original, ["Related"],
                  warnings=skill_warnings(skill) + report.warnings)


def my_words_note(vault: Path, path: str, text: str, skill: str | None = None) -> Result:
    """Replace `## In my words` with the text exactly as given (design §11.6)."""
    vault = vault.resolve()
    target = resolve_in_vault(vault, path)
    rel = target.relative_to(vault).as_posix()
    original = target.read_text(encoding="utf-8")
    note = parse(original)
    if note.meta.get("type") != "topic":
        raise WriteError([f"{rel}: only topic pages have ## {MY_WORDS}"])
    text = text.rstrip("\n")
    if not text.strip():
        raise WriteError(["the text is empty; to clear the section, edit it in Obsidian"])
    if has_heading(text):
        raise WriteError(["the text contains a '#' or '##' heading, which would split the section"])
    new_body = replace_section(note.body, MY_WORDS, text, TOPIC_SECTIONS)
    if new_body == note.body:
        return Result(target, rel, "unchanged", original, original)
    note.body = new_body
    note.meta["updated"] = q(today())
    report = validate(note, Path(rel))
    if report.errors:
        raise WriteError([f"{rel}: {e}" for e in report.errors])
    return Result(target, rel, "my-words", render(note), original, [MY_WORDS],
                  warnings=skill_warnings(skill) + report.warnings)


def save(result: Result) -> None:
    """Write the result; refuse if the file changed meanwhile."""
    if result.action == "unchanged":
        return
    path = result.path
    if result.action == "created":
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as f:
            f.write(result.text)
        return
    if path.read_text(encoding="utf-8") != result.original:
        raise WriteError([f"{result.rel} changed on disk while it was being written; run the command again"])
    tmp = path.with_name(f".{path.name}.ms-kb-tmp")
    tmp.write_text(result.text, encoding="utf-8")
    os.replace(tmp, path)
