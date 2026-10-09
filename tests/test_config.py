from pathlib import Path

import pytest

from ms_kb.config import Config, ConfigError, KbConfig, config_path, load_config, save_config


def test_round_trip(isolated_config):
    cfg = Config(default_kb="main", kbs={"main": KbConfig("~/Knowledge/main")}, clients=["codex"])
    assert save_config(cfg) == isolated_config
    assert load_config() == cfg


def test_missing_config_is_none():
    assert load_config() is None


def test_kb_config_env_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("KB_CONFIG", str(tmp_path / "explicit.toml"))
    assert config_path() == tmp_path / "explicit.toml"


def test_xdg_config_home(tmp_path, monkeypatch):
    monkeypatch.delenv("KB_CONFIG")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert config_path() == tmp_path / "xdg" / "ms-kb" / "config.toml"


def test_default_location(tmp_path, monkeypatch):
    monkeypatch.delenv("KB_CONFIG")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert config_path() == tmp_path / ".config" / "ms-kb" / "config.toml"


def test_tilde_expanded(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert KbConfig("~/Knowledge/main").vault == tmp_path / "Knowledge" / "main"


@pytest.mark.parametrize(
    "text",
    [
        'schema_version = 2\ndefault_kb = "main"\n',
        'default_kb = "main"\n',
        "schema_version = 1\n",
        'schema_version = 1\ndefault_kb = "main"\n[kbs.main]\n',
        "not toml = = =",
    ],
)
def test_invalid_config(isolated_config, text):
    isolated_config.parent.mkdir(parents=True)
    isolated_config.write_text(text)
    with pytest.raises(ConfigError):
        load_config()


def test_default_kb_must_exist():
    with pytest.raises(ConfigError):
        Config(default_kb="main").default()
