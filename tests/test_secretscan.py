import io

from ms_kb.cli import main
from ms_kb.secretscan import find_secrets

AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
GITHUB = "ghp_" + "a" * 36
ANTHROPIC = "sk-ant-api03-" + "b" * 40


def test_patterns():
    text = f"aws {AWS}\nplain line\ngh {GITHUB}\n{ANTHROPIC}\n-----BEGIN OPENSSH PRIVATE KEY-----\n"
    kinds = find_secrets(text, use_gitleaks=False)
    assert kinds == [(1, "AWS access key"), (3, "GitHub token"), (4, "API secret key (sk-…)"), (5, "private key")]


def test_ordinary_text_passes():
    assert find_secrets("sk-learn is a library; task-123; AKIA is a prefix\n", use_gitleaks=False) == []


def test_only_added_lines_are_checked():
    original = f"old {AWS}\n"
    assert find_secrets(original + "new line\n", original, use_gitleaks=False) == []
    assert find_secrets(original + f"{GITHUB}\n", original, use_gitleaks=False) == [(2, "GitHub token")]


def test_new_refuses_secret(vault, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(f"## Explanation\nMy key is {AWS}.\n"))
    assert main(["new", "concept", "--title", "Keys", "--topic", "aws", "--body-file", "-"]) == 1
    err = capsys.readouterr().err
    assert "looks like a secret (AWS access key); notes must not contain secrets" in err
    assert "--allow-secret-like" in err
    assert not (vault / "concepts" / "Keys.md").exists()


def test_override_by_user(vault, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(f"## Explanation\nExample format: {AWS}\n"))
    assert main(["new", "concept", "--title", "Keys", "--topic", "aws", "--body-file", "-",
                 "--allow-secret-like"]) == 0
    assert (vault / "concepts" / "Keys.md").is_file()


def test_extend_refuses_added_secret_only(vault, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(f"## Explanation\nFormat: {AWS}\n"))
    assert main(["new", "concept", "--title", "Keys", "--topic", "aws", "--body-file", "-",
                 "--allow-secret-like"]) == 0
    monkeypatch.setattr("sys.stdin", io.StringIO("## Insights\n- Rotate keys.\n"))
    assert main(["extend", "concepts/Keys.md", "--body-file", "-"]) == 0
    monkeypatch.setattr("sys.stdin", io.StringIO(f"## Insights\n- {GITHUB}\n"))
    assert main(["extend", "concepts/Keys.md", "--body-file", "-"]) == 1
