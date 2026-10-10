import pytest


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Never touch the real ~/.config/ms-kb during tests."""
    path = tmp_path / "config" / "config.toml"
    monkeypatch.setenv("KB_CONFIG", str(path))
    return path


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Never touch the real ~/.claude, ~/.agents, ~/.codex or ~/.cursor during tests."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    return home


@pytest.fixture(autouse=True)
def isolated_git(tmp_path, monkeypatch):
    """Never read the user's Git configuration (signing, hooks, identity)."""
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def vault(tmp_path):
    """A configured vault with skills installed for Claude Code and Codex."""
    from ms_kb.cli import main

    path = tmp_path / "vault"
    assert main(["setup", "--vault", str(path), "--clients", "claude-code,codex", "--yes"]) == 0
    return path.resolve()


@pytest.fixture(autouse=True)
def fake_launchd(monkeypatch):
    """Record launchctl calls instead of touching the real launchd; no Time Machine lookups."""
    import subprocess

    from ms_kb import schedule

    calls = []
    loaded = set()

    def launchctl(*args):
        calls.append(args)
        if args[0] == "bootstrap":
            loaded.add(schedule.LABEL)
        elif args[0] == "bootout":
            loaded.discard(schedule.LABEL)
        code = 0 if args[0] != "print" or schedule.LABEL in loaded else 113
        return subprocess.CompletedProcess(["launchctl", *args], code, "", "")

    monkeypatch.setattr(schedule, "launchctl", launchctl)
    monkeypatch.setattr(schedule, "time_machine_latest", lambda: None)
    return calls
