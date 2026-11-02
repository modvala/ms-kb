"""Source cards (design §6.9, §10.1): kb new source, kb search --type source, kb index --sources."""

import io
import json

import pytest

from ms_kb.cli import main
from ms_kb.notes import read_note
from ms_kb.search import norm_url
from ms_kb.schema import validate

CARD = """## Summary
Trade-offs of data systems.

## Key ideas
- Replication lag.

## Illustrations
- Figure 5-3: lag between replicas; shows why reads go stale.

## How it explains
Starts from failures, one running example.

## Use for
- [[Replication]] — for the lag diagram
"""


@pytest.fixture
def kb(monkeypatch):
    def call(*args, stdin=None):
        if stdin is not None:
            monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
        return main(list(args))

    return call


def new_card(kb, title="DDIA", *extra):
    return kb("new", "source", "--title", title, "--summary", "Data systems", "--tag", "distributed/replication",
              "--skill", "add-knowledge", "--body-file", "-", *extra, stdin=CARD)


def test_card_contract(vault, kb):
    assert new_card(kb, "DDIA", "--url", "https://Example.com/book/", "--author", "M. K.", "--published", "2017-03-16") == 0
    note = read_note(vault / "sources" / "DDIA.md")
    assert note.meta["url"] == "https://Example.com/book/"
    assert note.meta["author"] == "M. K." and note.meta["published"] == "2017-03-16"
    assert "topics" not in note.meta and "In my words" not in note.body
    assert validate(note).errors == []


def test_card_with_ref(vault, kb):
    assert new_card(kb, "Book", "--ref", "Kleppmann, O'Reilly, 2017") == 0
    assert read_note(vault / "sources" / "Book.md").meta["ref"] == "Kleppmann, O'Reilly, 2017"


def test_card_needs_exactly_one_of_url_and_ref(vault, kb, capsys):
    assert new_card(kb, "None") == 1
    assert "exactly one" in capsys.readouterr().err
    assert new_card(kb, "Both", "--url", "https://a.example", "--ref", "x") == 1
    assert not list((vault / "sources").glob("*.md"))


def test_card_sections_in_order(vault, kb):
    bad = "## Key ideas\n- x\n\n## Summary\nS.\n"
    assert kb("new", "source", "--title", "T", "--summary", "s", "--tag", "x", "--url", "https://a.example",
              "--body-file", "-", stdin=bad) == 1


@pytest.mark.parametrize("raw, expected", [
    ("HTTPS://Example.COM/a/?utm_source=x&b=1#frag", "https://example.com/a?b=1"),
    ("https://example.com/a", "https://example.com/a"),
    ("https://example.com/Path/", "https://example.com/Path"),
])
def test_norm_url(raw, expected):
    assert norm_url(raw) == expected


def test_duplicates(vault, kb, capsys):
    assert new_card(kb, "Article", "--url", "https://example.com/a", "--alias", "Статья") == 0
    capsys.readouterr()
    assert new_card(kb, "Other name", "--url", "HTTPS://EXAMPLE.com/a/?utm_medium=rss#top") == 1
    assert "sources/Article.md" in capsys.readouterr().err
    assert new_card(kb, "article", "--url", "https://example.com/b") == 1
    assert new_card(kb, "Статья", "--url", "https://example.com/c") == 1
    assert new_card(kb, "Articles", "--url", "https://example.com/d") == 1
    assert new_card(kb, "Articles", "--url", "https://example.com/d", "--allow-similar") == 0


def test_search_finds_cards_by_type_and_url(vault, kb, capsys):
    assert new_card(kb, "Article", "--url", "https://example.com/a") == 0
    assert kb("new", "topic", "--title", "Article topic", "--summary", "s", "--tag", "x", "--body-file", "-",
              stdin="## Summary\nS.\n") == 0
    capsys.readouterr()
    assert kb("search", "article", "--type", "source", "--json") == 0
    [hit] = json.loads(capsys.readouterr().out)
    assert hit["type"] == "source" and hit["title"] == "Article"
    assert kb("search", "article") == 0
    out = capsys.readouterr().out
    assert "[source] Article" in out and "[topic] Article topic" in out
    assert kb("search", "example.com/a", "--json") == 0
    assert [h["title"] for h in json.loads(capsys.readouterr().out)] == ["Article"]


def test_index_sources_counts_linking_topics(vault, kb, capsys):
    assert new_card(kb, "Used", "--url", "https://example.com/u", "--alias", "Использован") == 0
    assert new_card(kb, "Unused", "--url", "https://example.com/n") == 0
    for title in ("One", "Two"):
        assert kb("new", "topic", "--title", title, "--summary", "s", "--tag", "x", "--body-file", "-",
                  stdin="## Summary\nS.\n\n## Sources\n- [[Использован]] — x — checked 2026-10-20\n") == 0
    capsys.readouterr()
    assert kb("index", "--sources") == 0
    out = capsys.readouterr().out
    assert "[[Used]] — Data systems — used by 2 topics" in out
    assert "[[Unused]] — Data systems — not used yet" in out

    assert kb("index", "--sources", "--tag", "distributed", "--json") == 0
    entries = {e["title"]: e["used_by"] for e in json.loads(capsys.readouterr().out)}
    assert entries == {"Unused": 0, "Used": 2}

    assert kb("index") == 0  # plain kb index stays a catalogue of topic pages
    out = capsys.readouterr().out
    assert "[[One]]" in out and "Used" not in out

    assert kb("index", "--tags") == 0
    assert "distributed/replication  2" in capsys.readouterr().out  # cards count in the vocabulary


def test_card_extend_append_only_and_no_rewrite(vault, kb, capsys):
    assert new_card(kb, "Article", "--url", "https://example.com/a") == 0
    assert kb("extend", "sources/Article.md", "--reason", "A new figure", "--body-file", "-",
              stdin="## Illustrations\n- Figure 2\n") == 0
    assert "- Figure 2" in (vault / "sources" / "Article.md").read_text()
    assert kb("rewrite", "sources/Article.md", "--reason", "r", "--body-file", "-", "--dry-run", stdin="## Summary\nS.\n") == 1
    assert kb("link", "sources/Article.md", "Article", "--why", "self") == 1


def test_v1_source_notes_stay_valid(vault):
    path = vault / "sources" / "Old.md"
    path.write_text('---\ntype: source\ntitle: "Old"\nurl: "https://a.example"\ncreated: "2026-01-01"\n'
                    'updated: "2026-01-01"\ntopics: [x]\n---\n\n# Old\n\n## Key takeaways\n- a\n')
    assert main(["validate", "sources/Old.md"]) == 0


def test_malformed_url_does_not_break_later_cards(vault, kb):
    assert new_card(kb, "Odd", "--url", "http://[x") == 0
    assert new_card(kb, "Next", "--url", "https://example.com/n") == 0
    assert new_card(kb, "Again", "--url", "HTTP://[X") == 1


def test_index_sources_leaves_out_v1_notes(vault, kb, capsys):
    (vault / "sources" / "Old.md").write_text(
        '---\ntype: source\ntitle: "Old"\nurl: "https://a.example"\ncreated: "2026-01-01"\n'
        'updated: "2026-01-01"\ntopics: [x]\n---\n\n# Old\n')
    capsys.readouterr()
    assert kb("index", "--sources") == 0
    assert "Old" not in capsys.readouterr().out
