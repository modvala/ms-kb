import argparse
import json
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
from ms_kb.notes import NOTE_TYPES, NoteError, read_note
from ms_kb.schema import validate
from ms_kb.search import note_files, search
from ms_kb.installer import SkillError, check_installed, install_skills
from ms_kb.vault import check_vault, git_work_tree, init_vault
from ms_kb.write import WriteError, extend_note, new_note, save

DEFAULT_KB = "main"
DEFAULT_VAULT = "~/Knowledge/main"


def _error(message: str) -> int:
    print(f"kb: error: {message}", file=sys.stderr)
    return 1


def _warn(message: str) -> None:
    print(f"kb: warning: {message}", file=sys.stderr)


def _vault() -> Path:
    cfg = load_config()
    if cfg is None:
        raise ConfigError("no configuration; run kb setup")
    vault = cfg.default().vault
    if not vault.is_dir():
        raise ConfigError(f"vault not found at {vault}; run kb init")
    return vault.resolve()


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
    print(f"Clients: {', '.join(clients) or 'none'}")
    errors = 0
    if args.no_skills:
        print("Skills: not installed (--no-skills); run kb install-skills later")
    else:
        errors = _install_skills(clients, force=False, dry_run=False)
    print("Next steps:")
    print(f"  - Obsidian: Open folder as vault -> {Path(vault).expanduser()}")
    print("  - Check the setup: kb doctor")
    return 1 if errors else 0


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
        for level, message in check_installed(cfg.clients):
            report(level, message)

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


def _install_skills(clients: list[str], force: bool, dry_run: bool) -> int:
    report, errors = install_skills(clients, force=force, dry_run=dry_run)
    prefix = "would be " if dry_run else ""
    print("Skills:" if report else "Skills: nothing to install")
    for action, path in report:
        print(f"  {prefix}{action:9} {path}")
    return errors


def cmd_install_skills(args: argparse.Namespace) -> int:
    if args.clients is not None:
        try:
            clients = _parse_clients(args.clients)
        except ValueError as e:
            return _error(str(e))
    else:
        cfg = load_config()
        if cfg is None:
            return _error("no configuration; run kb setup or pass --clients")
        clients = cfg.clients
    return 1 if _install_skills(clients, args.force, args.dry_run) else 0


def _parse_fields(values: list[str]) -> dict[str, str]:
    fields = {}
    for item in values:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise ValueError(f"--field expects KEY=VALUE, got {item!r}")
        fields[key] = value
    return fields


def cmd_search(args: argparse.Namespace) -> int:
    try:
        fields = _parse_fields(args.field)
    except ValueError as e:
        return _error(str(e))
    hits = search(_vault(), args.terms, args.type, args.topic, fields, args.limit)
    if args.json:
        print(json.dumps([h.as_dict() for h in hits], ensure_ascii=False, indent=2))
        return 0
    if not hits:
        print("No notes found.")
    for h in hits:
        topics = f"  ({', '.join(h.topics)})" if h.topics else ""
        print(f"{h.path}  [{h.type}] {h.title}{topics}")
        if h.snippet:
            print(f"    {h.snippet}")
    return 0


def _read_body(path: str | None) -> str | None:
    if path is None:
        return None
    if path == "-":
        return sys.stdin.read()
    return Path(path).expanduser().read_text(encoding="utf-8")


def _finish(result, dry_run: bool) -> int:
    for w in result.warnings:
        _warn(w)
    if result.skipped:
        print(f"  skipped {len(result.skipped)} line(s) already present")
    if result.action == "unchanged":
        print(f"unchanged {result.rel}")
        return 0
    if dry_run:
        print(f"would be {result.action} {result.rel}")
        print(result.text, end="")
        return 0
    save(result)
    sections = f" (sections: {', '.join(result.sections)})" if result.sections else ""
    print(f"{result.action} {result.rel}{sections}")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    result = new_note(
        _vault(),
        args.type,
        args.title,
        args.topic,
        body=_read_body(args.body_file),
        slug=args.slug,
        aliases=args.alias,
        related=args.related,
        sources=args.source,
        url=args.url,
        as_of=args.as_of,
        session_date=args.session_date,
        skill=args.skill,
        allow_similar=args.allow_similar,
    )
    return _finish(result, args.dry_run)


def cmd_extend(args: argparse.Namespace) -> int:
    body = _read_body(args.body_file)
    if body is None and not (args.topic or args.related or args.source):
        return _error("nothing to add: pass --body-file, --topic, --related or --source")
    result = extend_note(
        _vault(),
        args.path,
        fragment=body,
        summary=args.summary,
        topics=args.topic,
        related=args.related,
        sources=args.source,
        skill=args.skill,
    )
    return _finish(result, args.dry_run)


def cmd_validate(args: argparse.Namespace) -> int:
    vault = _vault()
    paths = [Path(p).expanduser().resolve() for p in args.paths] or list(note_files(vault))
    errors = warnings = 0
    for path in paths:
        try:
            rel = path.relative_to(vault)
        except ValueError:
            rel = None
        shown = rel.as_posix() if rel else str(path)
        try:
            report = validate(read_note(path), rel)
        except (OSError, NoteError) as e:
            print(f"{shown}: error: {e}")
            errors += 1
            continue
        for e in report.errors:
            print(f"{shown}: error: {e}")
        for w in report.warnings:
            print(f"{shown}: warn: {w}")
        errors += len(report.errors)
        warnings += len(report.warnings)
    print(f"{len(paths)} note(s), {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kb", description="Personal knowledge base tools")
    parser.add_argument("--version", action="version", version=f"kb {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("setup", help="first-run setup: vault path and clients")
    p.add_argument("--vault", help=f"vault folder (default: {DEFAULT_VAULT})")
    p.add_argument("--clients", help=f"comma-separated: {','.join(KNOWN_CLIENTS)}")
    p.add_argument("--yes", action="store_true", help="accept defaults without prompting")
    p.add_argument("--no-skills", action="store_true", help="do not install skills into the clients")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("init", help="create the vault structure; never overwrites files")
    p.add_argument("path", nargs="?", help="vault folder (default: the configured one)")
    p.add_argument("--name", help=f"knowledge base name (default: default_kb or {DEFAULT_KB!r})")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("doctor", help="check the configuration and the vault")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("where", help="print the vault path")
    p.set_defaults(func=cmd_where)

    p = sub.add_parser("install-skills", help="install the bundled skills into the clients")
    p.add_argument("--clients", help="comma-separated (default: the configured clients)")
    p.add_argument("--force", action="store_true", help="replace skill folders not installed by ms-kb")
    p.add_argument("--dry-run", action="store_true", help="show what would change")
    p.set_defaults(func=cmd_install_skills)

    p = sub.add_parser("search", help="find notes by text, type, topics and fields")
    p.add_argument("terms", nargs="*", help="words that must all occur (title, aliases, topics or text)")
    p.add_argument("--type", choices=NOTE_TYPES)
    p.add_argument("--topic", action="append", default=[], help="required topic; repeatable")
    p.add_argument("--field", action="append", default=[], metavar="KEY=VALUE",
                   help="frontmatter match, dotted keys allowed (created_by.skill=add-knowledge); repeatable")
    p.add_argument("--limit", type=int, default=20, help="maximum results (default 20, 0 = all)")
    p.add_argument("--json", action="store_true", help="JSON output with absolute paths")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("new", help="create a note; refuses duplicates")
    p.add_argument("type", choices=NOTE_TYPES)
    p.add_argument("--title", required=True)
    p.add_argument("--topic", action="append", default=[], help="kebab-case topic; repeatable, at least one")
    p.add_argument("--slug", help="file name slug for research and learning-session notes")
    p.add_argument("--alias", action="append", default=[])
    p.add_argument("--related", action="append", default=[], help="note name or [[link]]; repeatable")
    p.add_argument("--source", action="append", default=[], help="URL or [[source-note]]; repeatable")
    p.add_argument("--url", help="source URL (source notes)")
    p.add_argument("--as-of", help="YYYY-MM-DD the comparison applies to (research; default today)")
    p.add_argument("--session-date", help="YYYY-MM-DD (learning-session; default today)")
    p.add_argument("--body-file", metavar="FILE", help="Markdown body; - reads stdin (default: the type template)")
    p.add_argument("--skill", help="stamp provenance for this skill, e.g. add-knowledge")
    p.add_argument("--allow-similar", action="store_true", help="create even if notes with similar titles exist")
    p.add_argument("--dry-run", action="store_true", help="print the note instead of writing it")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("extend", help="append to sections of an existing note")
    p.add_argument("path", help="note path, absolute or relative to the vault")
    p.add_argument("--body-file", metavar="FILE",
                   help="'## Section' blocks appended to those sections; - reads stdin")
    p.add_argument("--summary", help="one line on what changed (required with --skill)")
    p.add_argument("--topic", action="append", default=[])
    p.add_argument("--related", action="append", default=[])
    p.add_argument("--source", action="append", default=[])
    p.add_argument("--skill", help="add an updates entry for this skill, e.g. add-knowledge")
    p.add_argument("--dry-run", action="store_true", help="print the result instead of writing it")
    p.set_defaults(func=cmd_extend)

    p = sub.add_parser("validate", help="check notes against the schema")
    p.add_argument("paths", nargs="*", help="notes to check (default: the whole vault)")
    p.set_defaults(func=cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except (ConfigError, NoteError, SkillError) as e:
        return _error(str(e))
    except WriteError as e:
        for message in e.messages:
            _error(message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
