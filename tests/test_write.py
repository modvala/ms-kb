import io
from datetime import date

import pytest

from ms_kb import __version__
from ms_kb.cli import main
from ms_kb.notes import read_note

TODAY = date.today().isoformat()


def run(*args, stdin=None, monkeypatch=None):
    if stdin is not None:
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    return main(list(args))


@pytest.fixture
def kb(monkeypatch):
    def call(*args, stdin=None):
        return run(*args, stdin=stdin, monkeypatch=monkeypatch)

    return call


def new_rag(kb):
    body = "## Explanation\nRetrieval plus generation.\n\n## Limitations\n- Depends on the retriever.\n"
    return kb("new", "concept", "--title", "RAG", "--topic", "rag", "--source", "https://example.com",
              "--skill", "add-knowledge", "--body-file", "-", stdin=body)


def test_new_stamps_provenance(vault, kb, capsys):
    assert new_rag(kb) == 0
    assert "created concepts/RAG.md" in capsys.readouterr().out
    note = read_note(vault / "concepts" / "RAG.md")
    prov = note.meta["created_by"]
    assert prov["skill"] == "add-knowledge"
    assert prov["skill_version"] == "0.3.0"
    assert prov["package_version"] == __version__
    assert prov["date"] == TODAY
    assert "agent" not in prov
    assert prov["skill_ref"].endswith("/src/ms_kb/skills/add-knowledge/SKILL.md")
    assert note.body.startswith("\n# RAG\n\n## Explanation")
    assert main(["validate"]) == 0


def test_new_records_agent_from_environment(vault, kb, monkeypatch):
    monkeypatch.setenv("CLAUDECODE", "1")
    assert new_rag(kb) == 0
    assert read_note(vault / "concepts" / "RAG.md").meta["created_by"]["agent"] == "claude-code"


def test_new_without_skill_has_no_provenance_and_uses_template(vault, kb):
    assert kb("new", "concept", "--title", "Transformers", "--topic", "transformers") == 0
    note = read_note(vault / "concepts" / "Transformers.md")
    assert "created_by" not in note.meta
    assert "## Explanation" in note.body and "{{title}}" not in note.body


def test_new_learning_session_links_related(vault, kb):
    assert kb("new", "learning-session", "--title", "Изучение RAG", "--slug", "rag-basics", "--topic", "rag",
              "--related", "RAG", "--skill", "add-knowledge", "--body-file", "-", stdin="## Conclusions\n- ok\n") == 0
    note = read_note(vault / "learning-sessions" / f"{TODAY}-rag-basics.md")
    assert note.meta["session_date"] == TODAY
    assert list(note.meta["related"]) == ["[[RAG]]"]
    assert note.body.rstrip().endswith("## Related\n\n- [[RAG]]")


def test_new_exact_duplicate_is_refused(vault, kb, capsys):
    assert new_rag(kb) == 0
    assert kb("new", "concept", "--title", "rag", "--topic", "rag") == 1
    assert "kb extend" in capsys.readouterr().err


def test_new_similar_needs_allow_similar(vault, kb):
    assert kb("new", "concept", "--title", "Reranking", "--topic", "rag") == 0
    assert kb("new", "concept", "--title", "Rerankings", "--topic", "rag") == 1
    assert kb("new", "concept", "--title", "Rerankings", "--topic", "rag", "--allow-similar") == 0


def test_new_invalid_writes_nothing(vault, kb, capsys):
    assert kb("new", "concept", "--title", "X", "--topic", "Not A Slug") == 1
    assert "kebab-case" in capsys.readouterr().err
    assert kb("new", "source", "--title", "Article", "--topic", "rag") == 1  # --url missing
    assert not list((vault / "concepts").iterdir())
    assert not list((vault / "sources").iterdir())


def test_new_dry_run(vault, kb, capsys):
    assert kb("new", "research", "--title", "Agent memory", "--topic", "agent-memory",
              "--source", "https://a.example", "--dry-run") == 0
    out = capsys.readouterr().out
    assert "would be created research/agent-memory.md" in out
    assert f'as_of: "{TODAY}"' in out
    assert not (vault / "research" / "agent-memory.md").exists()


def test_extend_appends_and_stamps_update(vault, kb, capsys):
    new_rag(kb)
    before = (vault / "concepts" / "RAG.md").read_text()
    fragment = "## Limitations\n- Depends on the retriever.\n- Long contexts dilute attention.\n\n## Insights\nReranking helps.\n"
    assert kb("extend", "concepts/RAG.md", "--summary", "Added limits", "--topic", "retrieval",
              "--related", "Reranking", "--skill", "add-knowledge", "--body-file", "-", stdin=fragment) == 0
    out = capsys.readouterr().out
    assert "skipped 1 line(s)" in out
    assert "extended concepts/RAG.md (sections: Limitations, Insights, Related)" in out

    text = (vault / "concepts" / "RAG.md").read_text()
    note = read_note(vault / "concepts" / "RAG.md")
    assert text.count("Depends on the retriever") == 1
    assert "- Depends on the retriever.\n- Long contexts dilute attention." in text
    assert list(note.meta["topics"]) == ["rag", "retrieval"]
    assert list(note.meta["related"]) == ["[[Reranking]]"]
    assert note.meta["created_by"]["date"] == TODAY
    [update] = note.meta["updates"]
    assert update["summary"] == "Added limits"
    assert update["skill"] == "add-knowledge"
    # the old text is still there, line for line
    old_body = before.split("---\n", 2)[2]
    assert all(line in text for line in old_body.splitlines())
    assert main(["validate"]) == 0


def test_extend_twice_is_unchanged(vault, kb, capsys):
    new_rag(kb)
    args = ("extend", "concepts/RAG.md", "--summary", "s", "--skill", "add-knowledge", "--body-file", "-")
    assert kb(*args, stdin="## Insights\n- a\n") == 0
    text = (vault / "concepts" / "RAG.md").read_text()
    assert kb(*args, stdin="## Insights\n- a\n") == 0
    assert "unchanged concepts/RAG.md" in capsys.readouterr().out
    assert (vault / "concepts" / "RAG.md").read_text() == text


def test_extend_hand_written_note_gets_no_created_by(vault, kb):
    path = vault / "concepts" / "Mine.md"
    path.write_text('---\ntype: concept\ntitle: "Mine"\ncreated: 2026-01-01\nupdated: 2026-01-01\ntopics: [x]\n---\n\n# Mine\n')
    assert kb("extend", str(path), "--summary", "s", "--skill", "add-knowledge", "--body-file", "-",
              stdin="## Insights\n- new\n") == 0
    note = read_note(path)
    assert "created_by" not in note.meta
    assert len(note.meta["updates"]) == 1
    assert "created: 2026-01-01" in path.read_text()


def test_extend_requires_summary_with_skill(vault, kb, capsys):
    new_rag(kb)
    assert kb("extend", "concepts/RAG.md", "--skill", "add-knowledge", "--body-file", "-", stdin="## A\n- x\n") == 1
    assert "--summary" in capsys.readouterr().err


def test_extend_refuses_paths_outside_vault(vault, kb, tmp_path, capsys):
    outside = tmp_path / "outside.md"
    outside.write_text("---\ntype: concept\n---\n")
    assert kb("extend", str(outside), "--body-file", "-", stdin="## A\n- x\n") == 1
    assert kb("extend", "../outside.md", "--body-file", "-", stdin="## A\n- x\n") == 1
    assert kb("extend", "concepts/Missing.md", "--body-file", "-", stdin="## A\n- x\n") == 1
    assert "outside the vault" in capsys.readouterr().err


def test_extend_rejects_text_outside_sections(vault, kb):
    new_rag(kb)
    assert kb("extend", "concepts/RAG.md", "--body-file", "-", stdin="loose text\n") == 1


def test_extend_invalid_result_writes_nothing(vault, kb):
    new_rag(kb)
    before = (vault / "concepts" / "RAG.md").read_text()
    assert kb("extend", "concepts/RAG.md", "--topic", "Bad Topic") == 1
    assert (vault / "concepts" / "RAG.md").read_text() == before


def test_extend_dry_run(vault, kb, capsys):
    new_rag(kb)
    before = (vault / "concepts" / "RAG.md").read_text()
    assert kb("extend", "concepts/RAG.md", "--dry-run", "--body-file", "-", stdin="## Insights\n- x\n") == 0
    assert "would be extended concepts/RAG.md" in capsys.readouterr().out
    assert (vault / "concepts" / "RAG.md").read_text() == before


def test_extend_learning_profile(vault, kb):
    fragment = f"## Recently studied\n- {TODAY} — [[s]]\n"
    assert kb("extend", "learning_profile.md", "--body-file", "-", stdin=fragment) == 0
    text = (vault / "learning_profile.md").read_text()
    assert f"## Recently studied\n\n- {TODAY} — [[s]]\n\n## Open questions" in text
    assert "updates" not in text
    assert kb("extend", "learning_profile.md", "--topic", "x") == 1


def test_extend_needs_something_to_add(vault, kb):
    new_rag(kb)
    assert kb("extend", "concepts/RAG.md") == 1


def test_validate_reports_errors(vault, kb, capsys):
    (vault / "concepts" / "Bad.md").write_text("---\ntype: concept\n---\n")
    (vault / "concepts" / "Broken.md").write_text("---\ntype: [x\n---\n")
    assert main(["validate"]) == 1
    out = capsys.readouterr().out
    assert "concepts/Bad.md: error: title is missing" in out
    assert "concepts/Broken.md: error: invalid frontmatter" in out


def test_search_cli(vault, kb, capsys):
    new_rag(kb)
    capsys.readouterr()
    assert main(["search", "retrieval", "--json"]) == 0
    out = capsys.readouterr().out
    assert f'"path": "{vault / "concepts" / "RAG.md"}"' in out
    assert main(["search", "nothing-like-this"]) == 0
    assert "No notes found." in capsys.readouterr().out
    assert main(["search", "--field", "broken"]) == 1


def test_commands_need_config():
    assert main(["search", "x"]) == 1
    assert main(["validate"]) == 1
