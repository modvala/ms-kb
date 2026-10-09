import pytest

from ms_kb.notes import (
    Note,
    NoteError,
    append_to_section,
    file_title,
    merge_list,
    note_rel_path,
    parse,
    parse_fragment,
    render,
    slugify,
)

NOTE = """---
type: concept
title: "RAG"   # my comment
created: 2026-10-01
updated: "2026-10-01"
topics: [rag]
custom: keep me
---

# RAG

## Explanation

Text.

```python
## not a heading
```

## Insights

- one

## Related
"""


def test_round_trip_is_lossless():
    assert render(parse(NOTE)) == NOTE


def test_no_frontmatter():
    note = parse("# Just text\n")
    assert dict(note.meta) == {}
    assert note.body == "# Just text\n"


def test_invalid_frontmatter():
    with pytest.raises(NoteError):
        parse("---\ntype: [unclosed\n---\n")


def test_merge_list_keeps_order_and_skips_present():
    note = parse(NOTE)
    assert merge_list(note.meta, "topics", ["rag", "retrieval"]) == ["retrieval"]
    assert list(note.meta["topics"]) == ["rag", "retrieval"]
    assert merge_list(note.meta, "related", ["[[A]]"]) == ["[[A]]"]
    assert '"[[A]]"' in render(note)


def test_merge_list_inserts_above_provenance():
    note = parse('---\ntype: concept\ncreated_by:\n  skill: x\n---\n')
    merge_list(note.meta, "related", ["[[A]]"])
    assert list(note.meta) == ["type", "related", "created_by"]


@pytest.mark.parametrize(
    "title,expected",
    [("RAG", "RAG"), ("RAG: basics?", "RAG basics"), ('a/b\\c*"d"<e>|#^[f]', "abcdef"), ("  x  y. ", "x y")],
)
def test_file_title(title, expected):
    assert file_title(title) == expected


def test_slugify():
    assert slugify("MCP Basics & Tools") == "mcp-basics-tools"
    assert slugify("Café crème") == "cafe-creme"
    assert slugify("Изучение") == ""


def test_note_rel_path():
    assert note_rel_path("concept", "RAG").as_posix() == "concepts/RAG.md"
    assert note_rel_path("research", "Agent memory").as_posix() == "research/agent-memory.md"
    path = note_rel_path("learning-session", "MCP basics", session_date="2026-10-09")
    assert path.as_posix() == "learning-sessions/2026-10-09-mcp-basics.md"
    assert note_rel_path("research", "Изучение", slug="memory").as_posix() == "research/memory.md"


def test_note_rel_path_needs_ascii_slug():
    with pytest.raises(NoteError, match="--slug"):
        note_rel_path("learning-session", "Изучение", session_date="2026-10-09")
    with pytest.raises(NoteError):
        note_rel_path("research", "x", slug="Not A Slug")
    with pytest.raises(NoteError):
        note_rel_path("concept", "???")


def test_append_to_existing_section_continues_list():
    body = parse(NOTE).body
    new, skipped = append_to_section(body, "insights", "- one\n- two")
    assert skipped == ["- one"]
    assert "- one\n- two\n\n## Related" in new
    assert new.count("- one") == 1


def test_append_paragraph_gets_blank_line():
    new, _ = append_to_section(parse(NOTE).body, "Explanation", "More.")
    assert "Text.\n\n```python\n## not a heading\n```\n\nMore.\n\n## Insights" in new


def test_append_ignores_headings_in_code_fences():
    new, _ = append_to_section(parse(NOTE).body, "not a heading", "x")
    assert new.count("## not a heading") == 2  # a real section was created


def test_append_creates_section_before_related():
    new, _ = append_to_section(parse(NOTE).body, "Limitations", "- slow")
    assert "- one\n\n## Limitations\n\n- slow\n\n## Related" in new


def test_append_creates_related_at_end():
    new, _ = append_to_section("\n# T\n\n## A\n\ntext\n", "Related", "- [[X]]")
    assert new.endswith("text\n\n## Related\n\n- [[X]]\n")


def test_append_only_duplicates_leaves_body_unchanged():
    body = parse(NOTE).body
    assert append_to_section(body, "Insights", "- one\n") == (body, ["- one"])


def test_parse_fragment():
    assert parse_fragment("\n## A\n- x\n\n## B\ntext\n") == [("A", "- x"), ("B", "text")]
    assert parse_fragment("") == []
    with pytest.raises(NoteError, match="before the first"):
        parse_fragment("intro\n## A\nx")
    with pytest.raises(NoteError, match="title"):
        parse_fragment("# Title\n## A\nx")


def test_note_dataclass_render():
    assert render(Note(parse("---\na: 1\n---\n").meta, "\nbody\n")) == "---\na: 1\n---\n\nbody\n"
