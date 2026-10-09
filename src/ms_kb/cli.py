import argparse
import sys
from pathlib import Path

from ms_kb import __version__
from ms_kb.config import (
    KNOWN_CLIENTS,
    SCHEMA_VERSION,
    Config,
    ConfigError,
    KbConfig,
    config_path,
    load_config,
    save_config,
)
from ms_kb.vault import check_vault, git_work_tree, init_vault

DEFAULT_KB = "main"
DEFAULT_VAULT = "~/Knowledge/main"


def _error(message: str) -> int:
    print(f"kb: error: {message}", file=sys.stderr)
    return 1


def _normalize(vault: str) -> str:
    """Keep `~` as typed; make other paths absolute."""
    return vault if vault.startswith("~") else str(Path(vault).resolve())


def _same_path(a: str, b: str) -> bool:
    return Path(a).expanduser().resolve() == Path(b).expanduser().resolve()


def _parse_clients(value: str) -> list[str]:
    clients = [c.strip() for c in value.split(",") if c.strip()]
    unknown = [c for c in clients if c not in KNOWN_CLIENTS]
    if unknown:
        raise ValueError(f"unknown clients: {', '.join(unknown)} (known: {', '.join(KNOWN_CLIENTS)})")
    return clients


def _init_kb(cfg: Config | None, name: str, vault: str, clients: list[str] | None = None) -> None:
    """Create the vault structure and record it in the configuration."""
    for rel, status in init_vault(Path(vault).expanduser()):
        print(f"  {status:8} {rel}")
    if cfg is None:
        cfg = Config(default_kb=name)
    cfg.kbs[name] = KbConfig(vault_path=vault)
    if clients is not None:
        cfg.clients = clients
    print(f"Configuration: {save_config(cfg)}")


def cmd_init(args: argparse.Namespace) -> int:
    cfg = load_config()
    name = args.name or (cfg.default_kb if cfg else DEFAULT_KB)
    existing = cfg.kbs.get(name) if cfg else None

    if args.path is None:
        if existing is None:
            return _error(f"no vault configured for {name!r}; pass a path: kb init PATH")
        vault = existing.vault_path
    else:
        vault = _normalize(args.path)
        if existing and not _same_path(existing.vault_path, vault):
            return _error(
                f"{name!r} already points to {existing.vault_path}; "
                f"use another --name or change the vault with kb setup"
            )

    print(f"Vault {name!r}: {Path(vault).expanduser()}")
    _init_kb(cfg, name, vault)
    return 0


def _ask(prompt: str, default: str) -> str:
    try:
        answer = input(f"{prompt} [{default}]: ").strip()
    except EOFError:
        answer = ""
    return answer or default


def cmd_setup(args: argparse.Namespace) -> int:
    cfg = load_config()
    name = cfg.default_kb if cfg else DEFAULT_KB
    current = cfg.kbs.get(name) if cfg else None

    vault = args.vault
    if vault is None:
        default = current.vault_path if current else DEFAULT_VAULT
        vault = default if args.yes else _ask("Vault folder", default)
    vault = _normalize(vault)

    clients_arg = args.clients
    if clients_arg is None:
        default = ",".join(cfg.clients if cfg and cfg.clients else KNOWN_CLIENTS)
        clients_arg = default if args.yes else _ask(f"Clients ({', '.join(KNOWN_CLIENTS)})", default)
    try:
        clients = _parse_clients(clients_arg)
    except ValueError as e:
        return _error(str(e))

    if current and not _same_path(current.vault_path, vault):
        print(f"Note: {name!r} now points to {vault}; the old vault {current.vault_path} is left untouched.")

    print(f"Vault {name!r}: {Path(vault).expanduser()}")
    _init_kb(cfg, name, vault, clients)

    print()
    print(f"Clients: {', '.join(clients) or 'none'} (skills installation arrives in v0.3)")
    print("Next steps:")
    print(f"  - Obsidian: Open folder as vault -> {Path(vault).expanduser()}")
    print("  - Check the setup: kb doctor")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    errors = 0

    def report(level: str, message: str) -> None:
        nonlocal errors
        errors += level == "error"
        print(f"  {level:5} {message}")

    path = config_path()
    print(f"kb {__version__}")
    print(f"Configuration: {path}")
    try:
        cfg = load_config(path)
    except ConfigError as e:
        report("error", str(e))
        return 1
    if cfg is None:
        report("error", "configuration not found; run kb setup")
        return 1
    report("ok", f"schema_version {SCHEMA_VERSION}")

    try:
        kb = cfg.default()
    except ConfigError as e:
        report("error", str(e))
        return 1

    vault = kb.vault
    if not vault.is_dir():
        report("error", f"vault {cfg.default_kb!r} not found at {vault}; run kb init {kb.vault_path}")
    else:
        report("ok", f"vault {cfg.default_kb!r} at {vault}")
        missing = check_vault(vault)
        if missing:
            report("error", f"missing in vault: {', '.join(missing)}; run kb init")
        else:
            report("ok", "vault structure complete")
        if repo := git_work_tree(vault):
            report("warn", f"vault is inside a Git work tree ({repo}); keep the vault out of Git")

    unknown = [c for c in cfg.clients if c not in KNOWN_CLIENTS]
    if unknown:
        report("error", f"unknown clients in configuration: {', '.join(unknown)}")
    else:
        report("ok", f"clients: {', '.join(cfg.clients) or 'none'}")

    return 1 if errors else 0


def cmd_where(args: argparse.Namespace) -> int:
    try:
        cfg = load_config()
        if cfg is None:
            return _error("no configuration; run kb setup")
        print(cfg.default().vault)
    except ConfigError as e:
        return _error(str(e))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kb", description="Personal knowledge base tools")
    parser.add_argument("--version", action="version", version=f"kb {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("setup", help="first-run setup: vault path and clients")
    p.add_argument("--vault", help=f"vault folder (default: {DEFAULT_VAULT})")
    p.add_argument("--clients", help=f"comma-separated: {','.join(KNOWN_CLIENTS)}")
    p.add_argument("--yes", action="store_true", help="accept defaults without prompting")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("init", help="create the vault structure; never overwrites files")
    p.add_argument("path", nargs="?", help="vault folder (default: the configured one)")
    p.add_argument("--name", help=f"knowledge base name (default: default_kb or {DEFAULT_KB!r})")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("doctor", help="check the configuration and the vault")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("where", help="print the vault path")
    p.set_defaults(func=cmd_where)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except ConfigError as e:
        return _error(str(e))


if __name__ == "__main__":
    raise SystemExit(main())
