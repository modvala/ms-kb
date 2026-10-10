import tomllib

from ms_kb import __version__
from ms_kb.cli import main
from ms_kb.installer import installed_path
from ms_kb.instructions import END, apply_block, block, block_version, instruction_text


def claude_md(home):
    return home / ".claude" / "CLAUDE.md"


def agents_md(home):
    return home / ".codex" / "AGENTS.md"


def test_apply_block_creates_appends_replaces_removes():
    new = block()
    assert apply_block("", new) == new
    mine = "# My rules\n- be brief\n"
    added = apply_block(mine, new)
    assert added == mine + "\n" + new
    assert apply_block(added, new) == added
    old = added.replace(f"ms-kb:begin {__version__}", "ms-kb:begin 0.0.1").replace("knowledge base", "kb")
    assert apply_block(old, new) == added
    assert apply_block(added, None) == mine
    assert apply_block(mine, None) == mine
    assert apply_block("no newline", new) == "no newline\n\n" + new


def test_block_in_the_middle_keeps_both_sides():
    text = "top\n\n" + block() + "\nbottom\n"
    assert apply_block(text, None) == "top\n\n\nbottom\n"
    assert apply_block(text, block()) == text


def test_block_version():
    assert block_version(block()) == __version__
    assert block_version("<!-- ms-kb:begin -->\nx\n" + END + "\n") == ""
    assert block_version("nothing") is None


def test_setup_installs_instruction(vault, isolated_home):
    for path in (claude_md(isolated_home), agents_md(isolated_home)):
        text = path.read_text()
        assert text == block()
        assert "kb-recall" in text and "add-knowledge" in text
    state = tomllib.loads(installed_path().read_text())
    assert state["instructions"]["targets"] == ["~/.claude/CLAUDE.md", "~/.codex/AGENTS.md"]
    assert set(state["skills"]) == {"add-knowledge", "kb-recall"}


def test_existing_content_is_preserved(tmp_path, isolated_home, capsys):
    path = claude_md(isolated_home)
    path.parent.mkdir()
    mine = "# My global rules\n\nAlways answer in English.\n"
    path.write_text(mine)
    assert main(["install-skills", "--clients", "claude-code"]) == 0
    assert path.read_text() == mine + "\n" + block()
    assert "installed ~/.claude/CLAUDE.md" in capsys.readouterr().out

    assert main(["install-skills", "--clients", "claude-code"]) == 0
    assert path.read_text().count("ms-kb:begin") == 1
    assert "unchanged ~/.claude/CLAUDE.md" in capsys.readouterr().out

    assert main(["install-skills", "--clients", "codex"]) == 0
    assert path.read_text() == mine
    assert "removed   ~/.claude/CLAUDE.md" in capsys.readouterr().out


def test_codex_home_is_respected(tmp_path, isolated_home, monkeypatch):
    codex = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex))
    assert main(["install-skills", "--clients", "codex"]) == 0
    assert (codex / "AGENTS.md").read_text() == block()
    assert not agents_md(isolated_home).exists()

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "moved"))
    assert main(["install-skills", "--clients", "codex"]) == 0
    assert (codex / "AGENTS.md").read_text() == ""  # the old copy is cleaned up via installed.toml


def test_no_instructions_and_dry_run_write_nothing(tmp_path, isolated_home, capsys):
    assert main(["install-skills", "--clients", "claude-code", "--dry-run"]) == 0
    assert "would be installed ~/.claude/CLAUDE.md" in capsys.readouterr().out
    assert not claude_md(isolated_home).exists()

    assert main(["install-skills", "--clients", "claude-code", "--no-instructions"]) == 0
    assert not claude_md(isolated_home).exists()
    assert "instructions" not in tomllib.loads(installed_path().read_text())

    assert main(["setup", "--vault", str(tmp_path / "v"), "--yes", "--clients", "codex", "--no-instructions"]) == 0
    assert not agents_md(isolated_home).exists()


def test_cursor_gets_text_to_paste(tmp_path, isolated_home, capsys):
    assert main(["setup", "--vault", str(tmp_path / "v"), "--clients", "cursor", "--yes"]) == 0
    out = capsys.readouterr().out
    assert "Settings -> Rules -> User Rules" in out
    assert instruction_text() in out
    assert not claude_md(isolated_home).exists()
    assert not agents_md(isolated_home).exists()


def test_print_instruction(capsys):
    assert main(["install-skills", "--print-instruction"]) == 0
    assert capsys.readouterr().out == instruction_text()


def test_doctor_reports_instructions(vault, isolated_home, capsys):
    capsys.readouterr()
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert f"ok    global instruction {__version__} in ~/.claude/CLAUDE.md" in out
    assert f"ok    global instruction {__version__} in ~/.codex/AGENTS.md" in out

    path = claude_md(isolated_home)
    path.write_text(path.read_text().replace(f"begin {__version__}", "begin 0.0.1"))
    agents_md(isolated_home).write_text("mine\n")
    (isolated_home / ".codex" / "AGENTS.override.md").write_text("override\n")
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "warn  global instruction in ~/.claude/CLAUDE.md is from 0.0.1" in out
    assert "warn  global instruction not installed in ~/.codex/AGENTS.md" in out
    assert "warn  ~/.codex/AGENTS.override.md takes precedence" in out


def test_doctor_warns_about_long_profile(vault, capsys):
    profile = vault / "learning_profile.md"
    profile.write_text(profile.read_text() + "- line\n" * 200)
    capsys.readouterr()
    assert main(["doctor"]) == 0
    assert "warn  learning_profile.md has" in capsys.readouterr().out
