import io
import subprocess

from ms_kb import history
from ms_kb.cli import main

KEY = "AKIA" + "ABCDEFGHIJKLMNOP"


def git(vault, *args):
    return subprocess.run(["git", "-C", str(vault), *args], capture_output=True, text=True, check=True).stdout


def subjects(vault):
    return git(vault, "log", "--format=%s").splitlines()


def run_new(monkeypatch, title="RAG", body="## Explanation\nRetrieval plus generation.\n", *extra):
    monkeypatch.setattr("sys.stdin", io.StringIO(body))
    return main(["new", "concept", "--title", title, "--topic", "rag", "--body-file", "-", *extra])


def test_init_creates_own_repository(vault):
    assert (vault / ".git").is_dir()
    assert ".trash/" in (vault / ".gitignore").read_text()
    assert subjects(vault) == ["kb: init vault"]
    assert git(vault, "status", "--porcelain") == ""


def test_init_is_idempotent(vault, capsys):
    assert main(["init"]) == 0
    assert "History: own repository" in capsys.readouterr().out
    assert subjects(vault) == ["kb: init vault"]


def test_no_nested_repository_in_foreign_work_tree(tmp_path, capsys):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert main(["setup", "--vault", str(tmp_path / "vault"), "--yes", "--no-skills"]) == 0
    assert "no nested repository created" in capsys.readouterr().out
    assert not (tmp_path / "vault" / ".git").exists()


def test_new_commits_with_trailers(vault, monkeypatch):
    monkeypatch.setenv("CLAUDECODE", "1")
    assert run_new(monkeypatch, "RAG", "## Explanation\nText.\n", "--skill", "add-knowledge") == 0
    message = git(vault, "log", "-1", "--format=%B")
    assert message.startswith("kb: create concepts/RAG.md")
    assert "Kb-Skill: add-knowledge" in message
    assert "Kb-Skill-Version: " in message
    assert "Kb-Version: " in message
    assert "Kb-Agent: claude-code" in message
    assert git(vault, "status", "--porcelain") == ""


def test_outside_edit_gets_its_own_commit(vault, monkeypatch):
    assert run_new(monkeypatch) == 0
    (vault / "concepts" / "Other.md").write_text("an edit in Obsidian\n")
    assert main(["extend", "concepts/RAG.md", "--topic", "llm"]) == 0
    assert subjects(vault)[:2] == ["kb: extend concepts/RAG.md", "external: 1 file changed outside kb"]
    assert git(vault, "show", "--name-only", "--format=", "HEAD").split() == ["concepts/RAG.md"]


def test_half_staged_user_change_stays_out_of_kb_commit(vault, monkeypatch):
    assert run_new(monkeypatch) == 0
    profile = vault / "learning_profile.md"
    # An edit made between the external commit and the kb commit is not swept in.
    original = history.commit_external

    def edit_after(v, subject=None):
        result = original(v, subject)
        profile.write_text(profile.read_text() + "\nunsaved thought\n")
        return result

    monkeypatch.setattr(history, "commit_external", edit_after)
    assert main(["extend", "concepts/RAG.md", "--topic", "llm"]) == 0
    assert git(vault, "show", "--name-only", "--format=", "HEAD").split() == ["concepts/RAG.md"]
    assert "learning_profile.md" in git(vault, "status", "--porcelain")


def test_secret_and_large_outside_files_are_not_committed(vault, monkeypatch, capsys):
    monkeypatch.setattr(history, "SIZE_LIMIT", 100)
    (vault / "concepts" / "Leak.md").write_text(f"key {KEY}\n")
    (vault / "attachments" / "big.bin").write_bytes(b"x" * 200)
    (vault / "concepts" / "Fine.md").write_text("fine\n")
    assert run_new(monkeypatch) == 0
    err = capsys.readouterr().err
    assert "not committed: concepts/Leak.md: looks like it contains a secret (AWS access key, line 1)" in err
    assert "not committed: attachments/big.bin: larger than" in err
    tracked = git(vault, "ls-files").split()
    assert "concepts/Fine.md" in tracked
    assert "concepts/Leak.md" not in tracked and "attachments/big.bin" not in tracked


def test_write_without_git_still_writes(vault, monkeypatch, capsys):
    monkeypatch.setattr(history, "git_available", lambda: False)
    assert run_new(monkeypatch) == 0
    assert (vault / "concepts" / "RAG.md").is_file()
    assert "no Git history yet" in capsys.readouterr().err


def test_failed_commit_is_a_warning(vault, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise history.GitError("git commit: boom")

    monkeypatch.setattr(history, "commit_write", fail)
    assert run_new(monkeypatch) == 0
    assert (vault / "concepts" / "RAG.md").is_file()
    assert "written but not committed: git commit: boom" in capsys.readouterr().err
    from ms_kb import vaultstate

    assert vaultstate.load("main")["git"]["last_error"] == "git commit: boom"


def test_history_of_a_note_and_deleted_files(vault, monkeypatch, capsys):
    assert run_new(monkeypatch, "RAG", "## Explanation\nText.\n", "--skill", "add-knowledge") == 0
    (vault / "concepts" / "RAG.md").unlink()
    history.commit_external(vault)
    capsys.readouterr()

    assert main(["history", "concepts/RAG.md"]) == 0
    out = capsys.readouterr().out
    assert "kb: create concepts/RAG.md  [add-knowledge]" in out
    assert "external: 1 file changed outside kb" in out

    assert main(["history", "--deleted"]) == 0
    out = capsys.readouterr().out
    assert "D    concepts/RAG.md" in out
    assert "kb restore" in out


def test_profile_commit_carries_skill(vault, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("## Recently studied\n- 2026-10-11 — [[x]]\n"))
    assert main(["extend", "learning_profile.md", "--skill", "add-knowledge", "--body-file", "-"]) == 0
    message = git(vault, "log", "-1", "--format=%B")
    assert message.startswith("kb: extend learning_profile.md")
    assert "Kb-Skill: add-knowledge" in message
    assert "updates:" not in (vault / "learning_profile.md").read_text()
