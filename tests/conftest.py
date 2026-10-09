import pytest


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Never touch the real ~/.config/ms-kb during tests."""
    path = tmp_path / "config" / "config.toml"
    monkeypatch.setenv("KB_CONFIG", str(path))
    return path


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Never touch the real ~/.claude, ~/.agents or ~/.cursor during tests."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAUDECODE", raising=False)
    return home


@pytest.fixture
def vault(tmp_path):
    """A configured vault with skills installed for Claude Code and Codex."""
    from ms_kb.cli import main

    path = tmp_path / "vault"
    assert main(["setup", "--vault", str(path), "--clients", "claude-code,codex", "--yes"]) == 0
    return path.resolve()
