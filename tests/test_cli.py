import shutil

import pytest

from ms_kb import __version__
from ms_kb.cli import main
from ms_kb.config import load_config


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"kb {__version__}"


def test_no_args_prints_help(capsys):
    assert main([]) == 0
    assert "usage: kb" in capsys.readouterr().out


def setup_vault(tmp_path, *extra):
    vault = tmp_path / "vault"
    assert main(["setup", "--vault", str(vault), "--yes", *extra]) == 0
    return vault


def test_setup_creates_config_and_vault(tmp_path, isolated_config):
    vault = setup_vault(tmp_path, "--clients", "claude-code,codex")
    cfg = load_config()
    assert cfg.default_kb == "main"
    assert cfg.default().vault == vault.resolve()
    assert cfg.clients == ["claude-code", "codex"]
    assert (vault / "learning_profile.md").is_file()


def test_setup_defaults_to_all_clients(tmp_path):
    setup_vault(tmp_path)
    assert load_config().clients == ["claude-code", "codex", "cursor"]


def test_setup_rejects_unknown_client(tmp_path):
    assert main(["setup", "--vault", str(tmp_path / "v"), "--clients", "vim", "--yes"]) == 1
    assert load_config() is None


def test_setup_prompts(tmp_path, monkeypatch):
    answers = iter([str(tmp_path / "prompted"), "cursor"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["setup"]) == 0
    cfg = load_config()
    assert cfg.default().vault == (tmp_path / "prompted").resolve()
    assert cfg.clients == ["cursor"]


def test_setup_again_is_safe(tmp_path):
    vault = setup_vault(tmp_path)
    (vault / "learning_profile.md").write_text("mine")
    setup_vault(tmp_path)
    assert (vault / "learning_profile.md").read_text() == "mine"


def test_init_again_uses_configured_vault(tmp_path, capsys):
    setup_vault(tmp_path)
    capsys.readouterr()
    assert main(["init"]) == 0
    assert "created" not in capsys.readouterr().out


def test_init_without_config_or_path_fails():
    assert main(["init"]) == 1


def test_init_new_vault_creates_config(tmp_path):
    assert main(["init", str(tmp_path / "v")]) == 0
    cfg = load_config()
    assert cfg.default_kb == "main"
    assert cfg.clients == []


def test_init_conflicting_path_fails(tmp_path):
    setup_vault(tmp_path)
    assert main(["init", str(tmp_path / "other")]) == 1
    assert not (tmp_path / "other").exists()


def test_init_second_kb_by_name(tmp_path):
    vault = setup_vault(tmp_path)
    assert main(["init", str(tmp_path / "work"), "--name", "work"]) == 0
    cfg = load_config()
    assert cfg.default_kb == "main"
    assert cfg.default().vault == vault.resolve()
    assert set(cfg.kbs) == {"main", "work"}


def test_doctor_healthy(tmp_path, capsys):
    setup_vault(tmp_path)
    assert main(["doctor"]) == 0
    assert "error" not in capsys.readouterr().out


def test_doctor_without_config(capsys):
    assert main(["doctor"]) == 1
    assert "kb setup" in capsys.readouterr().out


def test_doctor_missing_vault(tmp_path):
    vault = setup_vault(tmp_path)
    shutil.rmtree(vault)
    assert main(["doctor"]) == 1


def test_doctor_incomplete_vault(tmp_path, capsys):
    vault = setup_vault(tmp_path)
    (vault / "README.md").unlink()
    assert main(["doctor"]) == 1
    assert "README.md" in capsys.readouterr().out


def test_doctor_warns_about_git(tmp_path, capsys):
    (tmp_path / ".git").mkdir()
    setup_vault(tmp_path)
    assert main(["doctor"]) == 0
    assert "warn" in capsys.readouterr().out


def test_where(tmp_path, capsys):
    vault = setup_vault(tmp_path)
    capsys.readouterr()
    assert main(["where"]) == 0
    assert capsys.readouterr().out.strip() == str(vault.resolve())


def test_where_without_config():
    assert main(["where"]) == 1


def test_bad_config_reports_error(isolated_config, capsys):
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text("schema_version = 9\ndefault_kb = 'main'\n")
    assert main(["where"]) == 1
    assert main(["init"]) == 1
    assert "schema_version" in capsys.readouterr().err
