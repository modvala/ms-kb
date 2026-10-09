import tomllib

from ms_kb import __version__
from ms_kb.cli import main
from ms_kb.notes import read_note
from ms_kb.installer import bundled_skills, installed_path, target_dirs


def skill_dir(home, client_dir, name="add-knowledge"):
    return home / client_dir / "skills" / name


def test_bundled_skills():
    assert "add-knowledge" in bundled_skills()


def test_target_dirs(isolated_home):
    claude, agents, cursor = (isolated_home / d / "skills" for d in (".claude", ".agents", ".cursor"))
    assert target_dirs(["claude-code", "codex", "cursor"]) == [claude, agents]
    assert target_dirs(["cursor", "codex"]) == [agents]
    assert target_dirs(["cursor"]) == [cursor]
    assert target_dirs([]) == []


def test_setup_installs_skills(vault, isolated_home):
    for d in (".claude", ".agents"):
        meta = read_note(skill_dir(isolated_home, d) / "SKILL.md").meta
        assert meta["name"] == "add-knowledge"
        assert meta["metadata"]["package_version"] == __version__
        assert (skill_dir(isolated_home, d) / "references" / "note-types.md").is_file()
    state = tomllib.loads(installed_path().read_text())["skills"]["add-knowledge"]
    assert state["version"] == "0.3.0"
    assert state["package_version"] == __version__
    assert state["targets"] == ["~/.claude/skills/add-knowledge", "~/.agents/skills/add-knowledge"]


def test_setup_no_skills(tmp_path, isolated_home):
    assert main(["setup", "--vault", str(tmp_path / "v"), "--yes", "--no-skills"]) == 0
    assert not (isolated_home / ".claude").exists()


def test_reinstall_and_remove_disabled_client(vault, isolated_home):
    assert main(["install-skills", "--clients", "claude-code"]) == 0
    assert skill_dir(isolated_home, ".claude").is_dir()
    assert not skill_dir(isolated_home, ".agents").exists()
    assert (isolated_home / ".agents" / "skills").is_dir()  # the client's folder itself stays


def test_cursor_only_gets_own_copy(tmp_path, isolated_home):
    assert main(["setup", "--vault", str(tmp_path / "v"), "--clients", "cursor", "--yes"]) == 0
    assert skill_dir(isolated_home, ".cursor").is_dir()
    assert not (isolated_home / ".claude").exists()


def test_foreign_folder_is_not_touched(tmp_path, isolated_home, capsys):
    foreign = skill_dir(isolated_home, ".claude")
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("mine")
    assert main(["install-skills", "--clients", "claude-code,codex"]) == 1
    assert "not managed by ms-kb" in capsys.readouterr().out
    assert (foreign / "SKILL.md").read_text() == "mine"
    assert skill_dir(isolated_home, ".agents").is_dir()
    assert main(["install-skills", "--clients", "claude-code", "--force"]) == 0
    assert (foreign / "SKILL.md").read_text() != "mine"


def test_other_skills_are_left_alone(vault, isolated_home):
    other = skill_dir(isolated_home, ".claude", "someone-else")
    other.mkdir()
    assert main(["install-skills", "--clients", "codex"]) == 0
    assert other.is_dir()


def test_dry_run_changes_nothing(tmp_path, isolated_home, capsys):
    assert main(["install-skills", "--clients", "claude-code", "--dry-run"]) == 0
    assert "would be installed" in capsys.readouterr().out
    assert not (isolated_home / ".claude").exists()
    assert not installed_path().exists()


def test_install_skills_needs_clients():
    assert main(["install-skills"]) == 1


def test_doctor_reports_skills(vault, isolated_home, capsys):
    capsys.readouterr()
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert f"ok    skill add-knowledge {__version__} in ~/.claude/skills" in out

    skill_md = skill_dir(isolated_home, ".agents") / "SKILL.md"
    skill_md.write_text(skill_md.read_text().replace(f'package_version: "{__version__}"', 'package_version: "0.0.1"'))
    assert main(["doctor"]) == 0
    assert "warn  skill add-knowledge in ~/.agents/skills is from 0.0.1" in capsys.readouterr().out


def test_provenance_warns_when_skill_not_installed(tmp_path, capsys, monkeypatch):
    import io

    assert main(["setup", "--vault", str(tmp_path / "v"), "--yes", "--no-skills"]) == 0
    monkeypatch.setattr("sys.stdin", io.StringIO("## Explanation\nx\n"))
    assert main(["new", "concept", "--title", "X", "--topic", "x", "--skill", "add-knowledge", "--body-file", "-"]) == 0
    assert "run kb install-skills" in capsys.readouterr().err
    assert main(["new", "concept", "--title", "Y", "--topic", "x", "--skill", "nope"]) == 1
