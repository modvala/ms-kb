import io
import shutil

from ms_kb import integrity, vaultstate
from ms_kb.cli import main
from ms_kb.links import Resolver, normalize, targets


def new(monkeypatch, title, body="## Explanation\nSome text that is long enough to matter.\n", *extra):
    monkeypatch.setattr("sys.stdin", io.StringIO(body))
    assert main(["new", "concept", "--title", title, "--topic", "t", "--body-file", "-", *extra]) == 0


def doctor(capsys, *args):
    capsys.readouterr()
    code = main(["doctor", *args])
    return code, capsys.readouterr().out


def test_write_records_manifest(vault, monkeypatch):
    new(monkeypatch, "RAG")
    entry = vaultstate.load("main")["notes"]["concepts/RAG.md"]
    assert entry["writer"] == "kb create"
    assert entry["title"] == "RAG"
    assert len(entry["sha256"]) == 64


def test_manifest_seeded_from_existing_notes(vault, capsys):
    (vault / "concepts" / "Manual.md").write_text("---\ntitle: Manual\n---\n# Manual\n")
    code, out = doctor(capsys)
    assert code == 0
    assert "manifest started with 2 notes" in out
    assert set(vaultstate.load("main")["notes"]) == {"concepts/Manual.md", "learning_profile.md"}


def test_deleted_note_is_an_error_until_restored_or_acked(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG")
    (vault / "concepts" / "RAG.md").unlink()
    code, out = doctor(capsys)
    assert code == 1
    assert "error concepts/RAG.md was deleted; bring it back with kb restore concepts/RAG.md" in out

    code, out = doctor(capsys, "--ack", "concepts/RAG.md")
    assert code == 0
    assert "deletion accepted" in out
    assert "was deleted" not in doctor(capsys)[1]


def test_trash_hint(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG")
    (vault / ".trash").mkdir()
    shutil.move(vault / "concepts" / "RAG.md", vault / ".trash" / "RAG.md")
    assert "(a copy is in Obsidian's .trash/)" in doctor(capsys)[1]


def test_outside_edit_is_normal(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG")
    path = vault / "concepts" / "RAG.md"
    path.write_text(path.read_text() + "\nMore from Obsidian.\n")
    code, out = doctor(capsys)
    assert code == 0
    assert vaultstate.load("main")["notes"]["concepts/RAG.md"]["writer"] == "external"


def test_damaged_note(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG", "## Explanation\n" + "A long explanation line.\n" * 20)
    (vault / "concepts" / "RAG.md").write_text("---\ntitle: RAG\n---\n# RAG\n")
    code, out = doctor(capsys)
    assert code == 1
    assert "concepts/RAG.md looks damaged: the file shrank" in out
    assert doctor(capsys, "--ack", "concepts/RAG.md")[0] == 0


def test_empty_note_is_damaged(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG")
    (vault / "concepts" / "RAG.md").write_text("")
    assert "the file is empty" in doctor(capsys)[1]


def test_moved_note_is_followed(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG")
    (vault / "concepts" / "ml").mkdir()
    shutil.move(vault / "concepts" / "RAG.md", vault / "concepts" / "ml" / "RAG.md")
    code, out = doctor(capsys)
    assert code == 0
    assert "concepts/RAG.md moved to concepts/ml/RAG.md" in out
    notes = vaultstate.load("main")["notes"]
    assert "concepts/ml/RAG.md" in notes and "concepts/RAG.md" not in notes


def test_renamed_and_edited_note_is_found_by_title(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG")
    old = vault / "concepts" / "RAG.md"
    (vault / "concepts" / "Retrieval.md").write_text(old.read_text() + "\nedited\n")
    old.unlink()
    assert "concepts/RAG.md moved to concepts/Retrieval.md" in doctor(capsys)[1]


def test_broken_link_only_after_it_resolved(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG", "## Explanation\nSee [[Vectors]] and [[Not Yet Written]].\n")
    new(monkeypatch, "Vectors")
    code, out = doctor(capsys)
    assert "no longer resolves" not in out
    (vault / "concepts" / "Vectors.md").unlink()
    code, out = doctor(capsys, "--ack", "concepts/Vectors.md")
    assert "warn  [[vectors]] no longer resolves (in concepts/RAG.md)" in out
    assert "not yet written" not in out


def test_restored_copies_are_reported_and_not_notes(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG")
    (vault / "concepts" / "RAG.restored-20261010-120000.md").write_text("old\n")
    out = doctor(capsys)[1]
    assert "concepts/RAG.restored-20261010-120000.md is a restored copy" in out
    assert "concepts/RAG.restored-20261010-120000.md" not in vaultstate.load("main")["notes"]


def test_validate_reports_deletions(vault, monkeypatch, capsys):
    new(monkeypatch, "RAG")
    (vault / "concepts" / "RAG.md").unlink()
    capsys.readouterr()
    assert main(["validate"]) == 1
    assert "concepts/RAG.md: error: concepts/RAG.md was deleted" in capsys.readouterr().out


def test_link_parsing():
    assert targets("[[A]] ![[img.png]] [[B|alias]] [[C#Head]] [[folder/D.md]] [[#local]]") == {
        "a", "img.png", "b", "c", "folder/d"}
    assert normalize("  X  ") == "x"


def test_resolver(tmp_path):
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "RAG.md").write_text('---\naliases: ["Retrieval"]\n---\n')
    (tmp_path / "attachments").mkdir()
    (tmp_path / "attachments" / "fig.png").write_bytes(b"")
    r = Resolver(tmp_path)
    assert all(r.resolves(t) for t in ("rag", "concepts/rag", "retrieval", "fig.png"))
    assert not r.resolves("other") and not r.resolves("sources/rag")


def test_is_restored_copy(tmp_path):
    assert integrity.is_restored_copy(tmp_path / "RAG.restored-20261010-120000.md")
    assert not integrity.is_restored_copy(tmp_path / "RAG.md")
