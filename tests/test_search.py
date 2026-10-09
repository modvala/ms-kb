from ms_kb.search import field_values, find_duplicates, search
from pathlib import Path


def write(vault, rel, frontmatter, body=""):
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n\n{body}\n")


def make_vault(tmp_path):
    vault = tmp_path / "v"
    write(vault, "concepts/RAG.md", 'type: concept\ntitle: "RAG"\nupdated: "2026-10-01"\ntopics: [rag, retrieval]\n'
          "aliases: [Retrieval-augmented generation]\ncreated_by:\n  skill: add-knowledge\n", "Uses a reranker.")
    write(vault, "concepts/Reranking.md", 'type: concept\ntitle: "Reranking"\nupdated: "2026-10-05"\ntopics: [retrieval]\n',
          "Reorders RAG results.")
    write(vault, "learning-sessions/2026-10-02-rag.md",
          'type: learning-session\ntitle: "RAG session"\nupdated: "2026-10-02"\ntopics: [rag]\n'
          'updates:\n  - skill: add-knowledge\n  - skill: other\n', "We studied RAG and reranking.")
    write(vault, "concepts/broken.md", "type: [unclosed\n")
    (vault / "templates").mkdir()
    (vault / "templates" / "concept.md").write_text("---\ntype: concept\ntitle: RAG\n---\n")
    return vault


def rels(hits):
    return [h.rel for h in hits]


def test_text_ranking_title_first(tmp_path):
    hits = search(make_vault(tmp_path), ["rag"])
    assert rels(hits)[0] == "concepts/RAG.md"
    assert set(rels(hits)) == {"concepts/RAG.md", "concepts/Reranking.md", "learning-sessions/2026-10-02-rag.md"}


def test_terms_are_anded(tmp_path):
    assert rels(search(make_vault(tmp_path), ["rag", "studied"])) == ["learning-sessions/2026-10-02-rag.md"]


def test_alias_match(tmp_path):
    assert rels(search(make_vault(tmp_path), ["augmented"])) == ["concepts/RAG.md"]


def test_type_and_topic_filters(tmp_path):
    vault = make_vault(tmp_path)
    assert rels(search(vault, note_type="learning-session")) == ["learning-sessions/2026-10-02-rag.md"]
    assert rels(search(vault, topics=["retrieval"])) == ["concepts/Reranking.md", "concepts/RAG.md"]
    assert rels(search(vault, topics=["rag", "retrieval"])) == ["concepts/RAG.md"]


def test_field_filter_dotted_and_lists(tmp_path):
    vault = make_vault(tmp_path)
    assert rels(search(vault, fields={"created_by.skill": "add-knowledge"})) == ["concepts/RAG.md"]
    assert rels(search(vault, fields={"updates.skill": "other"})) == ["learning-sessions/2026-10-02-rag.md"]
    assert rels(search(vault, fields={"topics": "retrieval"}, limit=1)) == ["concepts/Reranking.md"]


def test_no_terms_sorted_by_updated(tmp_path):
    assert rels(search(make_vault(tmp_path)))[0] == "concepts/Reranking.md"


def test_field_values():
    meta = {"a": [{"b": 1}, {"b": [2, 3]}], "c": "x"}
    assert field_values(meta, "a.b") == [1, 2, 3]
    assert field_values(meta, "c") == ["x"]
    assert field_values(meta, "missing.key") == []


def test_duplicates(tmp_path):
    vault = make_vault(tmp_path)
    assert find_duplicates(vault, "concept", "rag", [], Path("concepts/rag.md"))[0] == ["concepts/RAG.md"]
    # alias collision within the type
    exact, _ = find_duplicates(vault, "concept", "New", ["retrieval augmented generation"], Path("concepts/New.md"))
    assert exact == ["concepts/RAG.md"]
    # the same file name in another folder makes [[links]] ambiguous
    assert find_duplicates(vault, "source", "Reranking", [], Path("sources/Reranking.md"))[0] == ["concepts/Reranking.md"]
    assert find_duplicates(vault, "concept", "Re-ranking!", [], Path("concepts/Re-ranking.md"))[0] == ["concepts/Reranking.md"]
    assert find_duplicates(vault, "concept", "Rerankings", [], Path("concepts/Rerankings.md")) == ([], ["concepts/Reranking.md"])
    assert find_duplicates(vault, "concept", "Transformers", [], Path("concepts/Transformers.md")) == ([], [])


def test_sessions_only_clash_on_file(tmp_path):
    vault = make_vault(tmp_path)
    rel = Path("learning-sessions/2026-10-02-rag.md")
    assert find_duplicates(vault, "learning-session", "RAG session", [], rel) == ([rel.as_posix()], [])
    assert find_duplicates(vault, "learning-session", "RAG session", [], Path("learning-sessions/2026-10-03-rag.md")) == ([], [])
