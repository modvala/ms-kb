import argparse
import difflib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from ms_kb import __version__
from ms_kb.config import (
    KNOWN_CLIENTS,
    SCHEMA_VERSION,
    Config,
    ConfigError,
    KbConfig,
    SyncConfig,
    config_path,
    load_config,
    save_config,
)
from ms_kb.notes import NOTE_TYPES, PROFILE, NoteError, read_note
from ms_kb.schema import validate
from ms_kb.search import note_files, search
from ms_kb.installer import SkillError, check_installed, install_skills, outdated_skills
from ms_kb.instructions import check_instructions, install_instructions, instruction_text
from ms_kb import history, integrity, schedule, vaultstate
from ms_kb.history import GitError
from ms_kb.provenance import REPO_URL, trailers
from ms_kb.secretscan import find_secrets
from ms_kb.vault import check_vault, has_notes, init_vault
from ms_kb.write import WriteError, extend_note, new_note, save

DEFAULT_KB = "main"
DEFAULT_VAULT = "~/Knowledge/main"
PROFILE_MAX_LINES = 150  # note-schema-v0 §5


def _error(message: str) -> int:
    print(f"kb: error: {message}", file=sys.stderr)
    return 1


def _warn(message: str) -> None:
    print(f"kb: warning: {message}", file=sys.stderr)


def _kb() -> tuple[str, Path, KbConfig]:
    """(name, resolved vault path, settings) of the default knowledge base."""
    cfg = load_config()
    if cfg is None:
        raise ConfigError("no configuration; run kb setup")
    kb = cfg.default()
    if not kb.vault.is_dir():
        raise ConfigError(f"vault not found at {kb.vault}; run kb init")
    return cfg.default_kb, kb.vault.resolve(), kb


def _vault() -> Path:
    return _kb()[1]


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


PROFILE_HINT = (
    "user data: restore it from a backup (Obsidian File recovery, Time Machine); "
    "kb init --new-profile starts an empty one"
)


def _init_kb(
    cfg: Config | None, name: str, vault: str, clients: list[str] | None = None, new_profile: bool = False
) -> Config:
    """Create the vault structure and record it in the configuration.

    The learning profile is user data: it is created on a new vault (not yet
    configured and without notes) or with `new_profile`, never silently
    recreated on a vault that is already in use (design §12.4).
    """
    path = Path(vault).expanduser()
    known = cfg is not None and any(_same_path(kb.vault_path, vault) for kb in cfg.kbs.values())
    fresh = not known and not (path.is_dir() and has_notes(path))
    for rel, status in init_vault(path, user_files=fresh or new_profile):
        hint = f" ({PROFILE_HINT})" if status == "missing" else ""
        print(f"  {status:8} {rel}{hint}")
    _init_history(path.resolve())
    if cfg is None:
        cfg = Config(default_kb=name)
    old = cfg.kbs.get(name)
    sync = old.sync if old and _same_path(old.vault_path, vault) else None
    cfg.kbs[name] = KbConfig(vault_path=vault, sync=sync)
    if clients is not None:
        cfg.clients = clients
    print(f"Configuration: {save_config(cfg)}")
    return cfg


def _report_excluded(excluded: list[tuple[str, str]], level: str = "warning") -> None:
    for rel, reason in excluded:
        print(f"kb: {level}: not committed: {rel}: {reason}", file=sys.stderr)


def _init_history(vault: Path) -> None:
    """Make the vault its own Git repository (design §12.1); never fails the init."""
    try:
        status, message, commit = history.ensure_repo(vault)
    except GitError as e:
        _warn(f"history: {e}")
        return
    print(f"History: {message}" + (f" ({commit.rev})" if commit.rev else ""))
    _report_excluded(commit.excluded)


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
    _init_kb(cfg, name, vault, new_profile=args.new_profile)
    return 0


def _ask(prompt: str, default: str) -> str:
    try:
        answer = input(f"{prompt} [{default}]: " if default else f"{prompt}: ").strip()
    except EOFError:
        answer = ""
    return answer or default


def _confirm(prompt: str, default: bool) -> bool:
    answer = _ask(f"{prompt} ({'Y/n' if default else 'y/N'})", "").lower()
    return default if not answer else answer.startswith("y")


def _setup_copy(cfg: Config, name: str, args: argparse.Namespace) -> int:
    """The off-machine copy (design §12.3): the remote and the hourly schedule."""
    kb = cfg.kbs[name]
    vault = kb.vault.resolve()
    if history.repo_status(vault)[0] != "own":
        print("Off-machine copy: skipped (the vault has no Git repository of its own)")
        return 0
    remote = kb.sync.remote if kb.sync else "origin"
    current = history.remote_url(vault, remote)
    url = args.remote
    if url is None and not args.no_remote and not args.yes:
        url = _ask("Remote URL for an off-machine copy, a private repository (empty to skip)", current or "")
    if url and not args.no_remote:
        if url != current:
            history.set_remote(vault, remote, url)
        if kb.sync is None:
            kb.sync = SyncConfig(remote=remote)
            save_config(cfg)
        print(f"Off-machine copy: {remote} -> {url} (push with kb sync)")
    elif kb.sync:
        print(f"Off-machine copy: {remote} -> {current or '(remote not set in the vault repository)'}")
    else:
        print("Off-machine copy: none (set a private remote later with kb setup --remote URL)")

    if kb.sync is None or not schedule.supported():
        return 0
    want = args.schedule
    if want is None and not args.yes:
        want = _confirm("Run kb sync hourly in the background (a LaunchAgent)?", True)
    try:
        if want:
            for line in schedule.install():
                print(f"Schedule: {line}")
        elif want is False and schedule.installed():
            for line in schedule.remove():
                print(f"Schedule: {line}")
    except (RuntimeError, OSError) as e:
        _warn(f"schedule: {e}")
        return 1
    return 0


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
    cfg = _init_kb(cfg, name, vault, clients)
    copy_errors = _setup_copy(cfg, name, args)

    print()
    print(f"Clients: {', '.join(clients) or 'none'}")
    errors = 0
    if args.no_skills:
        print("Skills: not installed (--no-skills); run kb install-skills later")
    else:
        errors = _install_skills(clients, force=False, dry_run=False, instructions=not args.no_instructions)
    print("Next steps:")
    print(f"  - Obsidian: Open folder as vault -> {Path(vault).expanduser()}")
    print("  - Check the setup: kb doctor")
    return 1 if errors or copy_errors else 0


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
        missing, lost = check_vault(vault)
        if missing:
            report("error", f"missing in vault: {', '.join(missing)}; run kb init")
        for rel in lost:
            report("error", f"{rel} is missing ({PROFILE_HINT})")
        profile = vault / PROFILE
        if profile.is_file() and (n := len(profile.read_text(encoding="utf-8").splitlines())) > PROFILE_MAX_LINES:
            report("warn", f"{PROFILE} has {n} lines (target under {PROFILE_MAX_LINES}); trim it in Obsidian")
        if not missing and not lost:
            report("ok", "vault structure complete")
        status, root = history.repo_status(vault)
        if status == "own":
            report("ok", "history: the vault is its own Git repository")
        elif status == "foreign":
            report("warn", f"history: the vault is inside the Git repository {root}; "
                           "move it out so it gets its own history")
        elif status == "none":
            report("warn", "history: the vault has no Git repository; run kb init")
        else:
            report("error", "history: git not found; install it with xcode-select --install")
        _doctor_integrity(cfg.default_kb, vault.resolve(), args.ack, report)
        if status == "own":
            _doctor_copy(cfg.default_kb, vault.resolve(), kb, report)

    unknown = [c for c in cfg.clients if c not in KNOWN_CLIENTS]
    if unknown:
        report("error", f"unknown clients in configuration: {', '.join(unknown)}")
    else:
        report("ok", f"clients: {', '.join(cfg.clients) or 'none'}")
        for level, message in check_installed(cfg.clients) + check_instructions(cfg.clients):
            report(level, message)

    return 1 if errors else 0


def _integrity(name: str, vault: Path, ack: list[str] = ()) -> tuple[list[str], list[integrity.Finding]]:
    """Acknowledge `ack` paths, then check the vault against the manifest and save it."""
    with vaultstate.lock(name):
        state = vaultstate.load(name)
        acked = [integrity.acknowledge(state, vault, _rel_arg(vault, a)) for a in ack]
        findings = integrity.check(vault, state)
        vaultstate.save(name, state)
    return acked, findings


def _doctor_integrity(name: str, vault: Path, ack: list[str], report) -> None:
    acked, findings = _integrity(name, vault, ack)
    for message in acked:
        report("ok", message)
    for f in findings:
        report(f.level, f.message)
    if not any(f.level == "error" for f in findings):
        state = vaultstate.load(name)
        report("ok", f"integrity: {len(state['notes'])} note(s) tracked, none deleted or damaged")


STALE_PUSH_HOURS = 24


def _age_hours(stamp: str | None) -> float | None:
    if not stamp:
        return None
    return (datetime.now(timezone.utc) - datetime.fromisoformat(stamp)).total_seconds() / 3600


def _doctor_copy(name: str, vault: Path, kb: KbConfig, report) -> None:
    """Freshness of history and of the off-machine copy (design §12.4)."""
    git_state = vaultstate.load(name)["git"]
    if pending := history.pending(vault):
        report("info", f"{len(pending)} file(s) changed outside kb; committed on the next write or kb sync")
    if error := git_state.get("last_error"):
        report("warn", f"last Git error ({git_state.get('last_error_at', '?')}): {error}")
    if kb.sync is None:
        report("warn", "no off-machine copy: set a private remote with kb setup --remote URL")
    elif (url := history.remote_url(vault, kb.sync.remote)) is None:
        report("error", f"remote {kb.sync.remote!r} is not set in the vault repository; run kb setup --remote URL")
    else:
        last = git_state.get("last_push")
        count = history.unpushed(vault, kb.sync.remote)
        age = _age_hours(last)
        when = f"last push {last}" if last else "never pushed"
        if count and (age is None or age > STALE_PUSH_HOURS):
            report("warn", f"{count} commit(s) not pushed to {url}, {when}; run kb sync")
        elif count:
            report("info", f"{count} commit(s) waiting for the next kb sync to {url}")
        else:
            report("ok", f"remote {kb.sync.remote} ({url}) up to date, {when}")
        if schedule.supported():
            if not schedule.installed():
                report("warn", "hourly kb sync is not scheduled; run kb sync --schedule on")
            elif not schedule.loaded():
                report("warn", "the kb sync LaunchAgent is not loaded; run kb sync --schedule on")
            else:
                report("ok", "hourly kb sync scheduled")
    if schedule.supported():
        latest = schedule.time_machine_latest()
        report("info", f"Time Machine: {f'last backup {latest}' if latest else 'last backup unknown'}")


def cmd_sync(args: argparse.Namespace) -> int:
    if args.schedule:
        return _cmd_schedule(args.schedule)
    name, vault, kb = _kb()

    def say(message: str) -> None:
        if not args.quiet:
            print(message)

    def problem(message: str) -> None:
        stamp = f"{vaultstate.now()} " if args.quiet else ""
        print(f"{stamp}kb sync: error: {message}", file=sys.stderr)

    if history.repo_status(vault)[0] != "own":
        problem("the vault has no Git repository of its own; run kb init")
        return 1
    failed = False
    with vaultstate.lock(name):
        state = vaultstate.load(name)
        try:
            commit = history.commit_external(vault)
        except GitError as e:
            problem(str(e))
            vaultstate.git_failed(state, str(e))
            vaultstate.save(name, state)
            return 1
        if commit.committed:
            vaultstate.git_ok(state, "last_commit", commit.rev)
            say(f"committed {len(commit.files)} file(s) changed outside kb ({commit.rev})")
        for rel, reason in commit.excluded:
            problem(f"not committed, so not pushed: {rel}: {reason}")
            failed = True
        if kb.sync is None:
            say("no remote configured; set a private remote with kb setup --remote URL")
        else:
            try:
                say(history.push(vault, kb.sync.remote))
                vaultstate.git_ok(state, "last_push")
            except GitError as e:
                problem(f"{e}; local commits are kept for the next kb sync")
                vaultstate.git_failed(state, str(e))
                failed = True
        vaultstate.save(name, state)
    return 1 if failed else 0


def _cmd_schedule(action: str) -> int:
    try:
        lines = {"on": schedule.install, "off": schedule.remove, "status": schedule.status}[action]()
    except (RuntimeError, OSError) as e:
        return _error(str(e))
    for line in lines:
        print(line)
    return 0


def cmd_where(args: argparse.Namespace) -> int:
    try:
        cfg = load_config()
        if cfg is None:
            return _error("no configuration; run kb setup")
        print(cfg.default().vault)
    except ConfigError as e:
        return _error(str(e))
    if old := outdated_skills(cfg.clients):
        _warn(f"installed skills come from ms-kb {', '.join(old)}, the CLI is {__version__}; run kb update")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Upgrade the package, then let the new kb reinstall skills and instructions (US-17)."""
    uv = shutil.which("uv")
    if uv is None:
        return _error("uv not found; update by hand: uv tool upgrade ms-kb && kb install-skills")
    if args.ref:
        cmd = [uv, "tool", "install", "--force", f"git+{REPO_URL}@{args.ref}"]
    else:
        cmd = [uv, "tool", "upgrade", "ms-kb"]
    print(f"Running: {' '.join(cmd)}", flush=True)
    if subprocess.run(cmd).returncode != 0:
        return _error("the package update failed; nothing else was changed")
    bin_dir = subprocess.run([uv, "tool", "dir", "--bin"], capture_output=True, text=True).stdout.strip()
    kb = Path(bin_dir) / "kb"
    if not kb.is_file():
        return _error(f"{kb} not found after the update; run kb install-skills by hand")
    new = subprocess.run([str(kb), "--version"], capture_output=True, text=True).stdout.strip()
    print(f"kb {__version__} -> {new.removeprefix('kb ') or '?'}", flush=True)
    # This process still runs the old package: the new kb installs its own skills.
    errors = subprocess.run([str(kb), "install-skills"]).returncode
    if schedule.installed():
        errors |= subprocess.run([str(kb), "sync", "--schedule", "on"]).returncode
    return 1 if errors else 0


def _install_skills(clients: list[str], force: bool, dry_run: bool, instructions: bool = True) -> int:
    """Skills and, unless `instructions` is false, the global instruction."""
    report, errors = install_skills(clients, force=force, dry_run=dry_run)
    prefix = "would be " if dry_run else ""
    print("Skills:" if report else "Skills: nothing to install")
    for action, path in report:
        print(f"  {prefix}{action:9} {path}")
    if not instructions:
        print("Global instruction: skipped (--no-instructions)")
        return errors
    report = install_instructions(clients, dry_run=dry_run)
    print("Global instruction:" if report else "Global instruction: no instruction files for these clients")
    for action, path in report:
        print(f"  {prefix if action != 'unchanged' else ''}{action:9} {path}")
    if "cursor" in clients and not dry_run:
        print("  Cursor keeps User Rules in its settings: paste the text below into")
        print("  Settings -> Rules -> User Rules (kb install-skills --print-instruction shows it again).")
        print()
        print(instruction_text())
    return errors


def cmd_install_skills(args: argparse.Namespace) -> int:
    if args.print_instruction:
        print(instruction_text(), end="")
        return 0
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
    return 1 if _install_skills(clients, args.force, args.dry_run, not args.no_instructions) else 0


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


def _check_secrets(result, allow: bool) -> None:
    """Refuse key-like strings in what this write adds (design §12.1)."""
    if allow or result.action == "unchanged":
        return
    found = find_secrets(result.text, result.original)
    if found:
        raise WriteError(
            [f"{result.rel}: {f'line {n}: ' if n else ''}looks like a secret ({kind}); notes must not contain secrets"
             for n, kind in found]
            + ["remove it and run the command again (if it is not a secret, the user can pass --allow-secret-like)"]
        )


def _commit(vault: Path, state: dict, rels: list[str], subject: str, extra: dict | None = None,
            skill: str | None = None) -> None:
    """Commit kb's own write; a Git problem is a warning, never a failed write (design §12.1)."""
    try:
        status, _ = history.repo_status(vault)
        if status != "own":
            if status != "foreign":
                _warn("the vault has no Git history yet; run kb init")
            return
        commit = history.commit_write(vault, rels, subject, trailers(skill) | (extra or {}))
        vaultstate.git_ok(state, "last_commit", commit.rev)
    except GitError as e:
        _warn(f"written but not committed: {e}")
        vaultstate.git_failed(state, str(e))


def _commit_external(vault: Path, state: dict) -> list[tuple[str, str]]:
    """Commit outside edits before kb writes; returns the files left out."""
    try:
        if history.repo_status(vault)[0] != "own":
            return []
        commit = history.commit_external(vault)
        if commit.committed:
            vaultstate.git_ok(state, "last_commit", commit.rev)
        return commit.excluded
    except GitError as e:
        _warn(f"outside edits not committed: {e}")
        vaultstate.git_failed(state, str(e))
        return []


def _finish(result, dry_run: bool, skill: str | None = None, allow_secret: bool = False) -> int:
    for w in result.warnings:
        _warn(w)
    if result.skipped:
        print(f"  skipped {len(result.skipped)} line(s) already present")
    if result.action == "unchanged":
        print(f"unchanged {result.rel}")
        return 0
    _check_secrets(result, allow_secret)
    if dry_run:
        print(f"would be {result.action} {result.rel}")
        print(result.text, end="")
        return 0
    name, vault, _ = _kb()
    with vaultstate.lock(name):
        state = vaultstate.load(name)
        _report_excluded(_commit_external(vault, state))
        save(result)
        verb = "create" if result.action == "created" else "extend"
        _commit(vault, state, [result.rel], f"kb: {verb} {result.rel}", skill=skill)
        vaultstate.record(state, vault, result.rel, f"kb {verb}")
        vaultstate.save(name, state)
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
    return _finish(result, args.dry_run, args.skill, args.allow_secret_like)


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
    return _finish(result, args.dry_run, args.skill, args.allow_secret_like)


def _note_arg(vault: Path, arg: str) -> Path:
    """A note path as printed by kb new/extend (vault-relative) or a path from the current folder."""
    path = Path(arg).expanduser()
    if not path.is_absolute() and ((vault / path).exists() or not path.exists()):
        path = vault / path
    return path.resolve()


def cmd_validate(args: argparse.Namespace) -> int:
    name, vault, _ = _kb()
    paths = [_note_arg(vault, p) for p in args.paths] or list(note_files(vault))
    errors = warnings = checked = 0
    for path in paths:
        try:
            rel = path.relative_to(vault)
        except ValueError:
            rel = None
        shown = rel.as_posix() if rel else str(path)
        if rel and (rel.as_posix() == PROFILE or rel.parts[0] == "templates"):
            print(f"{shown}: skipped: not a note")
            continue
        checked += 1
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
    if not args.paths:
        for f in _integrity(name, vault)[1]:
            if f.level in ("warn", "error"):
                print(f"{f.rel or '-'}: {f.level}: {f.message}")
                errors += f.level == "error"
                warnings += f.level == "warn"
    print(f"{checked} note(s), {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


def _rel_arg(vault: Path, arg: str) -> str:
    path = _note_arg(vault, arg)
    try:
        return path.relative_to(vault).as_posix()
    except ValueError:
        raise ConfigError(f"{arg} is outside the vault {vault}") from None


def cmd_history(args: argparse.Namespace) -> int:
    _, vault, _ = _kb()
    if history.repo_status(vault)[0] != "own":
        return _error("the vault has no Git history; run kb init")
    rel = _rel_arg(vault, args.path) if args.path else None
    entries = history.log(vault, rel, args.deleted, args.limit)
    if not entries:
        print("No history." if not args.deleted else "No deleted files in the history.")
    for e in entries:
        skill = f"  [{e.skill}]" if e.skill else ""
        print(f"{e.rev}  {e.date}  {e.subject}{skill}")
        if args.deleted or not rel:
            for status, path in e.files:
                print(f"    {status:4} {path}")
    if args.deleted and entries:
        print("Restore one with: kb restore PATH")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    name, vault, _ = _kb()
    if history.repo_status(vault)[0] != "own":
        return _error("the vault has no Git history; run kb init")
    rel = _rel_arg(vault, args.path)
    with vaultstate.lock(name):
        state = vaultstate.load(name)
        try:
            rev = history.short(vault, args.at or history.last_version(vault, rel))
            data = history.show(vault, rev, rel)
        except GitError as e:
            return _error(f"{e}; list deleted notes with kb history --deleted")
        target = vault / rel
        current = target.read_bytes() if target.is_file() else None
        if current == data:
            print(f"unchanged {rel} (same as {rev})")
            return 0
        dest = target
        if current is not None and not args.force:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            dest = target.with_name(f"{target.stem}.restored-{stamp}{target.suffix}")
        dest_rel = dest.relative_to(vault).as_posix()
        prefix = "would be " if args.dry_run else ""
        if current is None:
            print(f"{prefix}restored {rel} from {rev}")
        elif args.force:
            print(f"{prefix}replaced {rel} with the version from {rev} (the current one is kept in the history)")
        else:
            print(f"{prefix}written {dest_rel}: {rel} exists and differs from {rev}; merge what you need")
        if current is not None:
            _print_diff(current, data, f"{rel} (current)", f"{rel} ({rev})")
        if args.dry_run:
            return 0
        if args.force:
            _report_excluded(_commit_external(vault, state))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        _commit(vault, state, [dest_rel], f"kb: restore {rel} from {rev}", {"Restored-From": rev})
        if dest == target:
            vaultstate.record(state, vault, rel, "kb restore")
        vaultstate.save(name, state)
    return 0


def _print_diff(old: bytes, new: bytes, old_name: str, new_name: str) -> None:
    try:
        a, b = old.decode("utf-8"), new.decode("utf-8")
    except UnicodeDecodeError:
        print("  (binary file: no diff)")
        return
    sys.stdout.writelines(difflib.unified_diff(a.splitlines(True), b.splitlines(True), old_name, new_name))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kb", description="Personal knowledge base tools")
    parser.add_argument("--version", action="version", version=f"kb {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("setup", help="first-run setup: vault path and clients")
    p.add_argument("--vault", help=f"vault folder (default: {DEFAULT_VAULT})")
    p.add_argument("--clients", help=f"comma-separated: {','.join(KNOWN_CLIENTS)}")
    p.add_argument("--yes", action="store_true", help="accept defaults without prompting")
    p.add_argument("--no-skills", action="store_true",
                   help="do not install skills or the global instruction into the clients")
    p.add_argument("--no-instructions", action="store_true",
                   help="do not add the ms-kb block to ~/.claude/CLAUDE.md and ~/.codex/AGENTS.md")
    p.add_argument("--remote", metavar="URL", help="a private Git repository that kb sync pushes the vault to")
    p.add_argument("--no-remote", action="store_true", help="do not ask for a remote")
    p.add_argument("--schedule", action=argparse.BooleanOptionalAction, default=None,
                   help="run kb sync hourly with a LaunchAgent (macOS; asked when a remote is set)")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("init", help="create the vault structure; never overwrites files")
    p.add_argument("path", nargs="?", help="vault folder (default: the configured one)")
    p.add_argument("--name", help=f"knowledge base name (default: default_kb or {DEFAULT_KB!r})")
    p.add_argument("--new-profile", action="store_true",
                   help="create an empty learning_profile.md if it is missing in a vault already in use")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("doctor", help="check the configuration and the vault")
    p.add_argument("--ack", action="append", default=[], metavar="PATH",
                   help="accept a reported deletion or damage of PATH as intentional; repeatable")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("update", help="update the package, then the skills and instructions in all clients")
    p.add_argument("--ref", help="install this tag or branch (e.g. v0.5.0) instead of the latest version")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("where", help="print the vault path")
    p.set_defaults(func=cmd_where)

    p = sub.add_parser("install-skills", help="install the bundled skills and the global instruction into the clients")
    p.add_argument("--clients", help="comma-separated (default: the configured clients)")
    p.add_argument("--force", action="store_true", help="replace skill folders not installed by ms-kb")
    p.add_argument("--dry-run", action="store_true", help="show what would change")
    p.add_argument("--no-instructions", action="store_true",
                   help="do not add the ms-kb block to ~/.claude/CLAUDE.md and ~/.codex/AGENTS.md")
    p.add_argument("--print-instruction", action="store_true",
                   help="print the global instruction text (to paste into Cursor User Rules) and exit")
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
    p.add_argument("--allow-secret-like", action="store_true",
                   help="write even if the text looks like it contains a key or token (for the user, not skills)")
    p.add_argument("--dry-run", action="store_true", help="print the note instead of writing it")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("extend", help="append to sections of an existing note")
    p.add_argument("path", help="note path, absolute or relative to the vault")
    p.add_argument("--body-file", metavar="FILE",
                   help="'## Section' blocks appended to those sections; - reads stdin")
    p.add_argument("--summary", help="one line on what changed (required with --skill, except for learning_profile.md)")
    p.add_argument("--topic", action="append", default=[])
    p.add_argument("--related", action="append", default=[])
    p.add_argument("--source", action="append", default=[])
    p.add_argument("--skill", help="add an updates entry for this skill, e.g. add-knowledge")
    p.add_argument("--allow-secret-like", action="store_true",
                   help="write even if the text looks like it contains a key or token (for the user, not skills)")
    p.add_argument("--dry-run", action="store_true", help="print the result instead of writing it")
    p.set_defaults(func=cmd_extend)

    p = sub.add_parser("validate", help="check notes against the schema")
    p.add_argument("paths", nargs="*", help="notes to check (default: the whole vault)")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("history", help="the vault's change history (Git), including deleted notes")
    p.add_argument("path", nargs="?", help="a note, also a deleted one (default: all changes)")
    p.add_argument("--deleted", action="store_true", help="only commits that deleted files")
    p.add_argument("--limit", type=int, default=20, help="maximum commits (default 20, 0 = all)")
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("sync", help="commit outside edits and push the vault to its private remote")
    p.add_argument("--quiet", action="store_true", help="print only problems (used by the LaunchAgent)")
    p.add_argument("--schedule", choices=("on", "off", "status"),
                   help="install, remove or show the hourly LaunchAgent instead of syncing")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("restore", help="bring a note back from the vault's history; never overwrites silently")
    p.add_argument("path", help="vault-relative path, as kb doctor or kb history --deleted print it")
    p.add_argument("--at", metavar="REV", help="the version to restore (default: the last one committed)")
    p.add_argument("--force", action="store_true",
                   help="replace the current file (it is committed to the history first)")
    p.add_argument("--dry-run", action="store_true", help="show what would happen")
    p.set_defaults(func=cmd_restore)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except (ConfigError, NoteError, SkillError, GitError) as e:
        return _error(str(e))
    except WriteError as e:
        for message in e.messages:
            _error(message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
