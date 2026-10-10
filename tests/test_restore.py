import io
import subprocess

from ms_kb import vaultstate
from ms_kb.cli import main


def git(vault, *args):
    return subprocess.run(["git", "-C", str(vault), *args], capture_output=True, text=True, check=True).stdout


def new(monkeypatch, title="RAG", body="## Explanation\nOriginal text.\n"):
    monkeypatch.setattr("sys.stdin", io.StringIO(body))
    assert main(["new", "concept", "--title", title, "--topic", "t", "--body-file", "-"]) == 0


def test_restore_deleted_note(vault, monkeypatch, capsys):
    new(monkeypatch)
    path = vault / "concepts" / "RAG.md"
    original = path.read_text()
    path.unlink()
    capsys.readouterr()
    assert main(["restore", "concepts/RAG.md"]) == 0
    assert "restored concepts/RAG.md from" in capsys.readouterr().out
    assert path.read_text() == original
    # The deletion was never committed, so the restored file matches HEAD again.
    assert git(vault, "status", "--porcelain") == ""
    assert vaultstate.load("main")["notes"]["concepts/RAG.md"]["writer"] == "kb restore"
    assert main(["doctor"]) == 0


def test_restore_after_deletion_was_committed(vault, monkeypatch):
    new(monkeypatch)
    path = vault / "concepts" / "RAG.md"
    original = path.read_text()
    path.unlink()
    new(monkeypatch, "Other")  # commits the deletion as an outside change
    assert "D\tconcepts/RAG.md" in git(vault, "log", "--name-status", "--format=")
    assert main(["restore", "concepts/RAG.md"]) == 0
    assert path.read_text() == original
    message = git(vault, "log", "-1", "--format=%B")
    assert message.startswith("kb: restore concepts/RAG.md from ")
    assert "Restored-From: " in message


def test_occupied_path_gets_side_file_and_diff(vault, monkeypatch, capsys):
    new(monkeypatch)
    path = vault / "concepts" / "RAG.md"
    path.write_text(path.read_text().replace("Original", "Changed"))
    capsys.readouterr()
    assert main(["restore", "concepts/RAG.md", "--at", "HEAD"]) == 0
    out = capsys.readouterr().out
    assert "exists and differs" in out
    assert "-Changed text." in out and "+Original text." in out
    assert "Changed" in path.read_text()
    side = list((vault / "concepts").glob("RAG.restored-*.md"))
    assert len(side) == 1 and "Original" in side[0].read_text()


def test_identical_is_unchanged(vault, monkeypatch, capsys):
    new(monkeypatch)
    capsys.readouterr()
    assert main(["restore", "concepts/RAG.md"]) == 0
    assert "unchanged concepts/RAG.md" in capsys.readouterr().out


def test_force_saves_current_version_first(vault, monkeypatch):
    new(monkeypatch)
    path = vault / "concepts" / "RAG.md"
    first = git(vault, "rev-parse", "--short", "HEAD").strip()
    path.write_text(path.read_text().replace("Original", "Changed"))
    assert main(["restore", "concepts/RAG.md", "--at", first, "--force"]) == 0
    assert "Original" in path.read_text()
    subjects = git(vault, "log", "--format=%s", "-2").splitlines()
    assert subjects[0].startswith("kb: restore concepts/RAG.md")
    assert subjects[1] == "external: 1 file changed outside kb"
    assert "Changed" in git(vault, "show", "HEAD~1:concepts/RAG.md")


def test_dry_run_writes_nothing(vault, monkeypatch, capsys):
    new(monkeypatch)
    path = vault / "concepts" / "RAG.md"
    path.unlink()
    capsys.readouterr()
    assert main(["restore", "concepts/RAG.md", "--dry-run"]) == 0
    assert "would be restored concepts/RAG.md" in capsys.readouterr().out
    assert not path.exists()


def test_unknown_path(vault, capsys):
    assert main(["restore", "concepts/Nope.md"]) == 1
    assert "not in the vault's history" in capsys.readouterr().err
