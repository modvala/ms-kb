from pathlib import PurePath

import pytest

from ms_kb.notes import parse
from ms_kb.schema import is_date, validate

PROV = """  skill: add-knowledge
  skill_version: "0.3.0"
  package_version: "0.3.0"
  skill_ref: "https://github.com/modvala/ms-kb/blob/v0.3.0/src/ms_kb/skills/add-knowledge/SKILL.md"
  date: "2026-10-09"
"""


def check(frontmatter: str, rel: str | None = "concepts/x.md"):
    return validate(parse(f"---\n{frontmatter}---\n"), PurePath(rel) if rel else None)


VALID = 'type: concept\ntitle: "X"\ncreated: "2026-10-09"\nupdated: "2026-10-09"\ntopics: [rag]\n'


def test_valid_concept():
    report = check(VALID)
    assert report.errors == [] and report.warnings == []


def test_unquoted_dates_from_obsidian_are_valid():
    assert check(VALID.replace('"2026-10-09"', "2026-10-09")).errors == []


@pytest.mark.parametrize("value,ok", [("2026-10-09", True), ("2026-13-01", False), ("09.10.2026", False), (5, False)])
def test_is_date(value, ok):
    assert is_date(value) is ok


def test_type_missing_or_unknown():
    assert check('title: "X"\n').errors == ["type is missing"]
    assert "not one of" in check("type: insight\n").errors[0]


def test_required_fields():
    errors = check("type: concept\ntopics: []\n").errors
    assert "title is missing" in errors
    assert "created is missing" in errors
    assert "topics is empty" in errors


@pytest.mark.parametrize(
    "note_type,rel,missing",
    [
        ("source", "sources/x.md", ["url"]),
        ("research", "research/x.md", ["as_of", "sources"]),
        ("learning-session", "learning-sessions/x.md", ["session_date"]),
    ],
)
def test_type_required_fields(note_type, rel, missing):
    errors = check(VALID.replace("concept", note_type), rel).errors
    assert errors == [f"{f} is missing" for f in missing]


def test_bad_date():
    assert check(VALID.replace('updated: "2026-10-09"', 'updated: "yesterday"')).errors == [
        "updated is not YYYY-MM-DD: 'yesterday'"
    ]


def test_topics_must_be_slugs():
    assert "kebab-case" in check(VALID.replace("[rag]", "[RAG, agent memory]")).errors[0]


def test_provenance_complete():
    assert check(VALID + "created_by:\n" + PROV).errors == []


def test_provenance_missing_field():
    errors = check(VALID + "created_by:\n" + PROV.replace("  skill_version: \"0.3.0\"\n", "")).errors
    assert errors == ["created_by is missing skill_version"]


def test_updates_need_summary():
    updates = "updates:\n  - " + PROV.strip().replace("\n", "\n  ") + "\n"
    errors = check(VALID + updates).errors
    assert errors == ["updates[0] is missing summary"]


def test_warnings():
    fm = VALID + "mood: happy\ncreated_by:\n" + PROV.replace("blob/v0.3.0", "blob/main")
    report = check(fm, "sources/x.md")
    assert report.errors == []
    assert len(report.warnings) == 3
    assert "unknown fields: mood" in report.warnings
    assert any("release tag" in w for w in report.warnings)
    assert any("belongs in concepts/" in w for w in report.warnings)


def test_vault_root_is_wrong_folder():
    assert "the vault root" in check(VALID, "x.md").warnings[0]


def test_type_specific_fields_are_known():
    fm = VALID.replace("concept", "project") + "external_context:\n  github.repo: a/b\n"
    assert check(fm, "projects/x.md").warnings == []
