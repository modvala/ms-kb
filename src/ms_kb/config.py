"""User configuration: ~/.config/ms-kb/config.toml (note-schema-v0 §6)."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import tomli_w

SCHEMA_VERSION = 1
KNOWN_CLIENTS = ("claude-code", "codex", "cursor")
SYNC_PROVIDERS = ("git",)


class ConfigError(Exception):
    pass


@dataclass
class SyncConfig:
    """Off-machine copy of the vault (design §12.3): a remote of its own Git repository."""

    provider: str = "git"
    remote: str = "origin"


@dataclass
class KbConfig:
    vault_path: str
    sync: SyncConfig | None = None

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
        sync = None
        if "sync" in kb:
            sync = SyncConfig(**{k: kb["sync"][k] for k in ("provider", "remote") if k in kb["sync"]})
            if sync.provider not in SYNC_PROVIDERS:
                raise ConfigError(f"{path}: [kbs.{name}.sync] provider {sync.provider!r} is not supported "
                                  f"(supported: {', '.join(SYNC_PROVIDERS)})")
        kbs[name] = KbConfig(vault_path=kb["vault_path"], sync=sync)

    return Config(
        default_kb=data["default_kb"],
        kbs=kbs,
        clients=list(data.get("clients", {}).get("enabled", [])),
        schema_version=version,
    )


def _kb_data(kb: KbConfig) -> dict:
    data = {"vault_path": kb.vault_path}
    if kb.sync is not None:
        data["sync"] = {"provider": kb.sync.provider, "remote": kb.sync.remote}
    return data


def save_config(cfg: Config, path: Path | None = None) -> Path:
    path = path or config_path()
    data = {
        "schema_version": cfg.schema_version,
        "default_kb": cfg.default_kb,
        "kbs": {name: _kb_data(kb) for name, kb in cfg.kbs.items()},
        "clients": {"enabled": cfg.clients},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps(data), encoding="utf-8")
    return path
