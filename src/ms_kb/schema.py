"""Note validation (note-schema-v0 §7): errors block a write, warnings do not."""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import PurePath

from ms_kb.config import KNOWN_CLIENTS
from ms_kb.notes import SLUG, TYPE_DIRS, Note

COMMON_REQUIRED = ("type", "title", "created", "updated", "topics")
COMMON_OPTIONAL = ("related", "sources", "aliases", "created_by", "updates")
TYPE_REQUIRED = {
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

    if rel_path is not None:
        folder = rel_path.parts[0] + "/" if len(rel_path.parts) > 1 else "the vault root"
        if folder != TYPE_DIRS[note_type] + "/":
            report.warnings.append(f"type {note_type!r} belongs in {TYPE_DIRS[note_type]}/, not {folder}")
    return report
