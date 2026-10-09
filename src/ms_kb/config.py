"""User configuration: ~/.config/ms-kb/config.toml (note-schema-v0 §6)."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import tomli_w

SCHEMA_VERSION = 1
KNOWN_CLIENTS = ("claude-code", "codex", "cursor")


class ConfigError(Exception):
    pass


@dataclass
class KbConfig:
    vault_path: str

    @property
    def vault(self) -> Path:
        return Path(self.vault_path).expanduser()


@dataclass
class Config:
    default_kb: str
    kbs: dict[str, KbConfig] = field(default_factory=dict)
    clients: list[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def default(self) -> KbConfig:
        try:
            return self.kbs[self.default_kb]
        except KeyError:
            raise ConfigError(f"default_kb {self.default_kb!r} is not defined in [kbs]") from None


def config_path() -> Path:
    if env := os.environ.get("KB_CONFIG"):
        return Path(env).expanduser()
    base = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return Path(base).expanduser() / "ms-kb" / "config.toml"


def load_config(path: Path | None = None) -> Config | None:
    path = path or config_path()
    if not path.exists():
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}") from None

    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ConfigError(f"{path}: unsupported schema_version {version!r}, expected {SCHEMA_VERSION}")
    if "default_kb" not in data:
        raise ConfigError(f"{path}: default_kb is missing")

    kbs = {}
    for name, kb in data.get("kbs", {}).items():
        if "vault_path" not in kb:
            raise ConfigError(f"{path}: [kbs.{name}] has no vault_path")
        kbs[name] = KbConfig(vault_path=kb["vault_path"])

    return Config(
        default_kb=data["default_kb"],
        kbs=kbs,
        clients=list(data.get("clients", {}).get("enabled", [])),
        schema_version=version,
    )


def save_config(cfg: Config, path: Path | None = None) -> Path:
    path = path or config_path()
    data = {
        "schema_version": cfg.schema_version,
        "default_kb": cfg.default_kb,
        "kbs": {name: {"vault_path": kb.vault_path} for name, kb in cfg.kbs.items()},
        "clients": {"enabled": cfg.clients},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps(data), encoding="utf-8")
    return path
