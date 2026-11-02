"""Note validation (note-schema-v1 §7): errors block a write, warnings do not."""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import PurePath

from ms_kb.config import KNOWN_CLIENTS
from ms_kb.notes import MY_WORDS, SLUG, SOURCE_SECTIONS, TOPIC_SECTIONS, TYPE_DIRS, Note, section_names, section_text

COMMON_REQUIRED = ("type", "title", "created", "updated", "topics")
COMMON_OPTIONAL = ("related", "sources", "aliases", "created_by", "updates")
TYPE_REQUIRED = {
    "topic": (),
    "concept": (),
    "source": ("url",),
    "research": ("as_of", "sources"),
    "learning-session": ("session_date",),
    "project": (),
}
TYPE_OPTIONAL = {"project": ("external_context",)}
DATE_FIELDS = ("created", "updated", "as_of", "session_date")
LIST_FIELDS = ("topics", "related", "sources", "aliases")
PROVENANCE_REQUIRED = ("skill", "skill_version", "package_version", "skill_ref", "date")
TAG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)?")
MAX_TAGS = 3
SUMMARY_MAX = 160  # provisional (design §14)
PAGE_BUDGET = 200  # lines; provisional (design §6.5)
PAGE_REQUIRED = ("type", "title", "summary", "tags", "created", "updated")
PAGE_OPTIONAL = {
    "topic": ("aliases", "created_by"),
    "source": ("url", "ref", "author", "published", "aliases", "created_by"),
}
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_RELEASE_REF = re.compile(r"/blob/v\d[^/]*/")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def is_date(value) -> bool:
    """`"YYYY-MM-DD"` strings, and the unquoted dates Obsidian Properties writes."""
    if isinstance(value, datetime):
        return False
    if isinstance(value, date):
        return True
    if isinstance(value, str) and _DATE.fullmatch(value):
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    return False


def _missing(value) -> bool:
    return value is None or (isinstance(value, (str, list, dict)) and not value)


def _check_provenance(entry, where: str, required: tuple[str, ...], report: Report) -> None:
    if not isinstance(entry, dict):
        report.errors.append(f"{where} is not a mapping")
        return
    for key in required:
        if _missing(entry.get(key)):
            report.errors.append(f"{where} is missing {key}")
    if "date" in entry and not _missing(entry["date"]) and not is_date(entry["date"]):
        report.errors.append(f"{where}.date is not YYYY-MM-DD: {entry['date']!r}")
    agent = entry.get("agent")
    if agent is not None and agent not in KNOWN_CLIENTS:
        report.warnings.append(f"{where}.agent {agent!r} is not one of {', '.join(KNOWN_CLIENTS)}")
    ref = entry.get("skill_ref")
    if isinstance(ref, str) and ref and not _RELEASE_REF.search(ref):
        report.warnings.append(f"{where}.skill_ref does not point to a release tag: {ref}")


def is_page(meta) -> bool:
    """A topic page or a source card; v1 `source` notes have `topics` and no `tags` (design §6.9)."""
    kind = meta.get("type")
    return kind == "topic" or (kind == "source" and not ("topics" in meta and "tags" not in meta))


def _check_sections(note: Note, fixed: tuple[str, ...], report: Report) -> None:
    names = section_names(note.body)
    if not (section_text(note.body, "Summary") or "").strip():
        report.errors.append("## Summary is missing or empty")
    present = [n for n in names if n in fixed]
    if present != sorted(present, key=fixed.index):
        report.errors.append(f"sections are out of order: {', '.join(present)} (expected {', '.join(fixed)})")
    for name in {n for n in names if names.count(n) > 1}:
        report.errors.append(f"section ## {name} appears more than once")
    own = [n for n in names if n not in fixed]
    if own:
        report.warnings.append(f"sections outside the contract: {', '.join(own)}")
    if MY_WORDS in fixed:
        head = names[: names.index(MY_WORDS)] if MY_WORDS in names else []
        if any(n != "Summary" for n in head):
            report.errors.append(f"## {MY_WORDS} must come right after ## Summary")


def _validate_page(note: Note, report: Report) -> None:
    """The topic page and source card contracts (design §6, §6.9)."""
    meta = note.meta
    kind = meta["type"]
    for key in PAGE_REQUIRED:
        if _missing(meta.get(key)):
            report.errors.append(f"{key} is missing" if key not in meta else f"{key} is empty")
    for key in ("created", "updated", "published"):
        if not _missing(meta.get(key)) and not is_date(meta[key]):
            report.errors.append(f"{key} is not YYYY-MM-DD: {meta[key]!r}")
    if "aliases" in meta and meta["aliases"] is not None and not isinstance(meta["aliases"], list):
        report.errors.append("aliases is not a list")
    tags = meta.get("tags")
    if tags is not None and not isinstance(tags, list):
        report.errors.append("tags is not a list")
    elif tags:
        bad = [t for t in tags if not (isinstance(t, str) and TAG.fullmatch(t))]
        if bad:
            report.errors.append(
                f"tags must be lowercase ASCII words joined by '-', with at most one '/': {', '.join(map(str, bad))}"
            )
        if len(tags) > MAX_TAGS:
            report.warnings.append(f"{len(tags)} tags (at most {MAX_TAGS})")
    summary = meta.get("summary")
    if isinstance(summary, str) and len(summary) > SUMMARY_MAX:
        report.warnings.append(f"summary has {len(summary)} characters (about {SUMMARY_MAX} at most)")
    if kind == "source" and bool(meta.get("url")) == bool(meta.get("ref")):
        report.errors.append("a source card needs exactly one of url and ref")
    if "created_by" in meta:
        _check_provenance(meta["created_by"], "created_by", PROVENANCE_REQUIRED, report)
    _check_sections(note, TOPIC_SECTIONS if kind == "topic" else SOURCE_SECTIONS, report)
    if kind == "topic" and (n := len(note.body.splitlines())) > PAGE_BUDGET:
        report.warnings.append(f"the page has {n} lines (budget about {PAGE_BUDGET}); consider moving a subtopic out")
    unknown = [k for k in meta if k not in PAGE_REQUIRED + PAGE_OPTIONAL[kind]]
    if unknown:
        report.warnings.append(f"unknown fields: {', '.join(map(str, unknown))}")


def validate(note: Note, rel_path: PurePath | None = None) -> Report:
    report = Report()
    meta = note.meta
    note_type = meta.get("type")
    if note_type is None:
        report.errors.append("type is missing")
        return report
    if note_type not in TYPE_DIRS:
        report.errors.append(f"type {note_type!r} is not one of {', '.join(TYPE_DIRS)}")
        return report

    if is_page(meta):
        _validate_page(note, report)
        _check_folder(note_type, rel_path, report)
        return report

    for key in COMMON_REQUIRED + TYPE_REQUIRED[note_type]:
        if _missing(meta.get(key)):
            report.errors.append(f"{key} is missing" if key not in meta else f"{key} is empty")

    for key in DATE_FIELDS:
        if not _missing(meta.get(key)) and not is_date(meta[key]):
            report.errors.append(f"{key} is not YYYY-MM-DD: {meta[key]!r}")

    for key in LIST_FIELDS:
        if key in meta and meta[key] is not None and not isinstance(meta[key], list):
            report.errors.append(f"{key} is not a list")
    topics = meta.get("topics")
    if isinstance(topics, list):
        bad = [t for t in topics if not (isinstance(t, str) and SLUG.fullmatch(t))]
        if bad:
            report.errors.append(f"topics must be kebab-case slugs: {', '.join(map(str, bad))}")

    if "created_by" in meta:
        _check_provenance(meta["created_by"], "created_by", PROVENANCE_REQUIRED, report)
    updates = meta.get("updates")
    if updates is not None:
        if not isinstance(updates, list):
            report.errors.append("updates is not a list")
        else:
            for i, entry in enumerate(updates):
                _check_provenance(entry, f"updates[{i}]", PROVENANCE_REQUIRED + ("summary",), report)

    known = set(COMMON_REQUIRED + COMMON_OPTIONAL + TYPE_REQUIRED[note_type] + TYPE_OPTIONAL.get(note_type, ()))
    unknown = [k for k in meta if k not in known]
    if unknown:
        report.warnings.append(f"unknown fields: {', '.join(map(str, unknown))}")

    _check_folder(note_type, rel_path, report)
    return report


def _check_folder(note_type: str, rel_path: PurePath | None, report: Report) -> None:
    if rel_path is not None:
        folder = rel_path.parts[0] + "/" if len(rel_path.parts) > 1 else "the vault root"
        if folder != TYPE_DIRS[note_type] + "/":
            report.warnings.append(f"type {note_type!r} belongs in {TYPE_DIRS[note_type]}/, not {folder}")
