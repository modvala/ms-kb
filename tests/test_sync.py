import io
import plistlib
import subprocess

import pytest

from ms_kb import schedule, vaultstate
from ms_kb.cli import main
from ms_kb.config import load_config


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout


@pytest.fixture
def remote(tmp_path):
    path = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(path)], check=True)
    return path


@pytest.fixture
def synced(tmp_path, remote):
    vault = tmp_path / "vault"
    assert main(["setup", "--vault", str(vault), "--yes", "--no-skills", "--remote", str(remote),
                 "--no-schedule"]) == 0
    return vault.resolve()


def new(monkeypatch, title="RAG"):
    monkeypatch.setattr("sys.stdin", io.StringIO("## Explanation\nText.\n"))
    assert main(["new", "concept", "--title", title, "--topic", "t", "--body-file", "-"]) == 0


def test_setup_records_remote(synced, remote):
    sync = load_config().default().sync
    assert (sync.provider, sync.remote) == ("git", "origin")
    assert git(synced, "remote", "get-url", "origin").strip() == str(remote)


def test_setup_again_keeps_sync(synced, tmp_path):
    assert main(["setup", "--vault", str(tmp_path / "vault"), "--yes", "--no-skills"]) == 0
    assert load_config().default().sync is not None


def test_sync_commits_and_pushes(synced, remote, monkeypatch, capsys, tmp_path):
    new(monkeypatch)
    (synced / "concepts" / "Obsidian.md").write_text("edited in Obsidian\n")
    capsys.readouterr()
    assert main(["sync"]) == 0
    out = capsys.readouterr().out
    assert "committed 1 file(s) changed outside kb" in out
    assert "pushed main to origin" in out
    assert git(remote, "log", "--format=%s", "main").splitlines()[:2] == [
        "external: 1 file changed outside kb", "kb: create concepts/RAG.md"]
    assert vaultstate.load("main")["git"]["last_push"]

    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(remote), str(clone)], check=True)
    assert (clone / "concepts" / "RAG.md").is_file()

    capsys.readouterr()
    assert main(["sync"]) == 0
    assert "up to date" in capsys.readouterr().out


def test_sync_quiet_prints_nothing_on_success(synced, capsys):
    capsys.readouterr()
    assert main(["sync", "--quiet"]) == 0
    assert capsys.readouterr() == ("", "")


def test_sync_without_remote(vault, capsys):
    capsys.readouterr()
    assert main(["sync"]) == 0
    assert "no remote configured" in capsys.readouterr().out


def test_rejected_push_is_never_forced(synced, remote, monkeypatch, capsys, tmp_path):
    assert main(["sync"]) == 0
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True)
    (other / "x.md").write_text("from elsewhere\n")
    git(other, "add", "x.md")
    git(other, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "elsewhere")
    git(other, "push", "-q", "origin", "main")

    new(monkeypatch)
    capsys.readouterr()
    assert main(["sync"]) == 1
    assert "rejected: the remote has commits that are not here; kb never force-pushes" in capsys.readouterr().err
    assert git(remote, "log", "-1", "--format=%s", "main").strip() == "elsewhere"
    assert "rejected" in vaultstate.load("main")["git"]["last_error"]


def test_unreachable_remote_keeps_commits(synced, tmp_path, monkeypatch, capsys):
    git(synced, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    new(monkeypatch)
    capsys.readouterr()
    assert main(["sync"]) == 1
    assert "local commits are kept for the next kb sync" in capsys.readouterr().err
    assert "kb: create concepts/RAG.md" in git(synced, "log", "--format=%s")


def test_excluded_files_fail_sync_but_push_the_rest(synced, remote, capsys):
    (synced / "concepts" / "Leak.md").write_text("AKIA" + "ABCDEFGHIJKLMNOP\n")
    (synced / "concepts" / "Fine.md").write_text("fine\n")
    capsys.readouterr()
    assert main(["sync"]) == 1
    assert "not committed, so not pushed: concepts/Leak.md" in capsys.readouterr().err
    files = git(remote, "ls-tree", "-r", "--name-only", "main").split()
    assert "concepts/Fine.md" in files and "concepts/Leak.md" not in files


def test_doctor_reports_copy(synced, monkeypatch, capsys):
    monkeypatch.setattr(schedule, "supported", lambda: True)
    new(monkeypatch)
    capsys.readouterr()
    main(["doctor"])
    out = capsys.readouterr().out
    assert "commit(s) not pushed" in out and "never pushed" in out
    assert "hourly kb sync is not scheduled" in out
    assert main(["sync"]) == 0
    capsys.readouterr()
    main(["doctor"])
    assert "up to date, last push" in capsys.readouterr().out


def test_doctor_without_remote_warns(vault, capsys):
    capsys.readouterr()
    main(["doctor"])
    assert "no off-machine copy" in capsys.readouterr().out


def test_schedule_install_and_remove(synced, monkeypatch, fake_launchd, capsys):
    monkeypatch.setattr(schedule, "supported", lambda: True)
    monkeypatch.setattr(schedule, "kb_executable", lambda: "/opt/kb/bin/kb")
    capsys.readouterr()
    assert main(["sync", "--schedule", "on"]) == 0
    assert "installed ~/Library/LaunchAgents/io.github.modvala.ms-kb.sync.plist" in capsys.readouterr().out
    data = plistlib.loads(schedule.plist_path().read_bytes())
    assert data["ProgramArguments"] == ["/opt/kb/bin/kb", "sync", "--quiet"]
    assert data["StartCalendarInterval"] == {"Minute": 0} and data["RunAtLoad"] is True
    assert data["EnvironmentVariables"]["KB_CONFIG"].endswith("config.toml")
    assert data["EnvironmentVariables"]["PATH"].startswith("/opt/kb/bin:")
    assert fake_launchd[-1][0] == "bootstrap"

    assert main(["sync", "--schedule", "status"]) == 0
    assert "schedule: loaded" in capsys.readouterr().out

    assert main(["sync", "--schedule", "off"]) == 0
    assert not schedule.plist_path().exists()
    assert fake_launchd[-1][0] == "bootout"


def test_setup_asks_for_schedule(tmp_path, remote, monkeypatch):
    monkeypatch.setattr(schedule, "supported", lambda: True)
    answers = iter([str(tmp_path / "v"), "claude-code", str(remote), ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["setup", "--no-skills"]) == 0
    assert schedule.installed()


def test_schedule_unsupported(vault, monkeypatch, capsys):
    monkeypatch.setattr(schedule, "supported", lambda: False)
    assert main(["sync", "--schedule", "on"]) == 1
    assert "macOS only" in capsys.readouterr().err


def test_unknown_provider(isolated_config):
    from ms_kb.config import ConfigError

    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text('schema_version = 1\ndefault_kb = "main"\n[kbs.main]\nvault_path = "/v"\n'
                               '[kbs.main.sync]\nprovider = "gdrive"\n')
    with pytest.raises(ConfigError, match="not supported"):
        load_config()
