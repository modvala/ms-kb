"""The vault's own Git repository: a commit per kb write (design §12.1).

Git is called through `subprocess`. Every failure is a `GitError` that callers
turn into a warning: Git never blocks a note write. Commits are
non-interactive (no signing, no hooks) because `kb sync` also runs from a
LaunchAgent.
"""

import os
import subprocess
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ms_kb.secretscan import find_secrets

SIZE_LIMIT = 50 * 1024 * 1024  # below GitHub's 100 MiB hard limit
SCAN_LIMIT = 5 * 1024 * 1024  # larger files are not scanned for secrets
TIMEOUT = 60
PUSH_TIMEOUT = 120
LOCK_RETRIES = 3
FALLBACK_IDENTITY = ("kb", "kb@localhost")


class GitError(Exception):
    pass


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
    return env


@lru_cache
def git_available() -> bool:
    """`git` runs. On macOS /usr/bin/git is a shim that fails without the Command Line Tools."""
    try:
        return subprocess.run(["git", "--version"], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@lru_cache
def _identity(vault: Path) -> tuple[str, ...]:
    """`-c` options for a committer identity when none is configured."""
    try:
        r = subprocess.run(["git", "-C", str(vault), "config", "--get", "user.email"],
                           capture_output=True, text=True, env=_env(), timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return ()
    if r.returncode == 0 and r.stdout.strip():
        return ()
    name, email = FALLBACK_IDENTITY
    return ("-c", f"user.name={name}", "-c", f"user.email={email}")


def run(vault: Path, *args: str, timeout: int = TIMEOUT, binary: bool = False) -> subprocess.CompletedProcess:
    """Run git in `vault`; retry briefly while another process holds index.lock (never delete it)."""
    cmd = ["git", "-C", str(vault), "-c", "commit.gpgsign=false", "-c", "core.quotepath=false",
           *_identity(vault), *args]
    for attempt in range(LOCK_RETRIES + 1):
        try:
            r = subprocess.run(cmd, capture_output=True, text=not binary, env=_env(), timeout=timeout)
        except FileNotFoundError:
            raise GitError("git not found") from None
        except subprocess.TimeoutExpired:
            raise GitError(f"git {args[0]} timed out after {timeout}s") from None
        r.subcommand = args[0]
        stderr = r.stderr if not binary else r.stderr.decode(errors="replace")
        if r.returncode == 0 or "index.lock" not in stderr or attempt == LOCK_RETRIES:
            return r
        time.sleep(0.2 * 2**attempt)
    return r


def check(r: subprocess.CompletedProcess) -> subprocess.CompletedProcess:
    if r.returncode != 0:
        err = r.stderr if isinstance(r.stderr, str) else r.stderr.decode(errors="replace")
        lines = [line for line in (err or r.stdout or "").strip().splitlines() if line.strip()]
        raise GitError(f"git {r.subcommand}: {lines[-1] if lines else f'exit code {r.returncode}'}")
    return r


def _zsplit(out: str) -> list[str]:
    return [p for p in out.split("\0") if p]


# --- repository -------------------------------------------------------------


def repo_status(vault: Path) -> tuple[str, Path | None]:
    """("own" | "foreign" | "none" | "nogit", repository root)."""
    if not git_available():
        return "nogit", None
    r = run(vault, "rev-parse", "--show-toplevel")
    if r.returncode != 0:
        return "none", None
    root = Path(r.stdout.strip()).resolve()
    return ("own" if root == vault.resolve() else "foreign"), root


@dataclass
class Commit:
    committed: bool = False
    rev: str | None = None
    files: list[str] = field(default_factory=list)
    excluded: list[tuple[str, str]] = field(default_factory=list)  # (path, reason)


def ensure_repo(vault: Path) -> tuple[str, str, Commit]:
    """Make the vault root its own repository unless it is inside a foreign one.

    Returns (status, message, initial commit).
    """
    status, root = repo_status(vault)
    if status == "nogit":
        return status, "git not found; history is off (install it: xcode-select --install)", Commit()
    if status == "foreign":
        return status, f"vault is inside the Git repository {root}; no nested repository created", Commit()
    if status == "own":
        return status, "own repository", Commit()
    check(run(vault, "init", "-q", "-b", "main"))
    return "created", "created repository", commit_external(vault, "kb: init vault")


def exclusion(path: Path) -> str | None:
    """Why an outside file must not be committed, or None."""
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > SIZE_LIMIT:
        return f"larger than {SIZE_LIMIT // (1024 * 1024)} MB"
    if size > SCAN_LIMIT:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if found := find_secrets(text):
        line, kind = found[0]
        return f"looks like it contains a secret ({kind}{f', line {line}' if line else ''})"
    return None


def commit_external(vault: Path, subject: str | None = None) -> Commit:
    """Commit changes made outside kb (design §12.1), except too large files and secrets."""
    status = check(run(vault, "status", "--porcelain", "-z", "--untracked-files=all"))
    if not status.stdout:
        return Commit()
    check(run(vault, "add", "-A"))
    added = _zsplit(check(run(vault, "diff", "--cached", "--name-only", "-z", "--diff-filter=d")).stdout)
    excluded = [(rel, reason) for rel in added if (reason := exclusion(vault / rel))]
    if excluded:
        check(run(vault, "reset", "-q", "--", *(rel for rel, _ in excluded)))
    files = _zsplit(check(run(vault, "diff", "--cached", "--name-only", "-z")).stdout)
    if not files:
        return Commit(excluded=excluded)
    subject = subject or f"external: {len(files)} file{'s' if len(files) != 1 else ''} changed outside kb"
    listing = "\n".join(files[:20] + ([f"… and {len(files) - 20} more"] if len(files) > 20 else []))
    check(run(vault, "commit", "-q", "--no-verify", "-m", subject, "-m", listing))
    return Commit(True, head(vault), files, excluded)


def commit_write(vault: Path, rels: list[str], subject: str, trailers: dict[str, str]) -> Commit:
    """Commit only kb's own paths, with provenance trailers."""
    check(run(vault, "add", "--", *rels))
    if not check(run(vault, "diff", "--cached", "--name-only", "--", *rels)).stdout.strip():
        return Commit()
    message = [subject]
    if trailers:
        message.append("\n".join(f"{k}: {v}" for k, v in trailers.items()))
    args = [a for part in message for a in ("-m", part)]
    check(run(vault, "commit", "-q", "--no-verify", *args, "--", *rels))
    return Commit(True, head(vault), list(rels))


def head(vault: Path) -> str | None:
    r = run(vault, "rev-parse", "--short", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else None


def branch(vault: Path) -> str:
    return check(run(vault, "symbolic-ref", "--short", "HEAD")).stdout.strip()


def pending(vault: Path) -> list[str]:
    """Paths changed in the work tree and not committed yet."""
    out = check(run(vault, "status", "--porcelain", "-z", "--untracked-files=all")).stdout
    return [entry[3:] for entry in _zsplit(out) if len(entry) > 3]


# --- reading history ----------------------------------------------------------


@dataclass
class LogEntry:
    rev: str
    date: str
    subject: str
    skill: str
    files: list[tuple[str, str]]  # (status, path)


def log(vault: Path, path: str | None = None, deleted: bool = False, limit: int = 20) -> list[LogEntry]:
    args = ["log", "--date=short", "--name-status",
            "--format=%x1e%h%x1f%ad%x1f%s%x1f%(trailers:key=Kb-Skill,valueonly,separator=%x2C)"]
    if limit:
        args.append(f"-n{limit}")
    if deleted:
        args.append("--diff-filter=D")
    if path:
        args += ["--follow", "--", path]
    r = run(vault, *args)
    if r.returncode != 0:
        if "does not have any commits" in r.stderr:
            return []
        check(r)
    entries = []
    for record in r.stdout.split("\x1e")[1:]:
        head_line, _, rest = record.partition("\n")
        rev, date, subject, skill = (head_line.split("\x1f") + ["", "", "", ""])[:4]
        files = []
        for line in rest.splitlines():
            if line.strip():
                status, _, name = line.partition("\t")
                files.append((status, name.replace("\t", " -> ")))
        entries.append(LogEntry(rev, date, subject, skill.strip(), files))
    return entries


def show(vault: Path, rev: str, rel: str) -> bytes:
    return check(run(vault, "show", f"{rev}:{rel}", binary=True)).stdout


def last_version(vault: Path, rel: str) -> str:
    """The revision holding the last committed version of `rel`, also after it was deleted."""
    if run(vault, "cat-file", "-e", f"HEAD:{rel}").returncode == 0:
        return "HEAD"
    rev = check(run(vault, "rev-list", "-n1", "HEAD", "--", rel)).stdout.strip()
    if not rev:
        raise GitError(f"{rel} is not in the vault's history")
    return f"{rev}^"


def short(vault: Path, rev: str) -> str:
    return check(run(vault, "rev-parse", "--short", rev)).stdout.strip()


# --- pushing ------------------------------------------------------------------


def remote_url(vault: Path, remote: str) -> str | None:
    r = run(vault, "remote", "get-url", remote)
    return r.stdout.strip() if r.returncode == 0 else None


def set_remote(vault: Path, remote: str, url: str) -> None:
    action = "set-url" if remote_url(vault, remote) is not None else "add"
    check(run(vault, "remote", action, remote, url))


def unpushed(vault: Path, remote: str) -> int | None:
    """Commits on the current branch that the remote does not have (None if unknown)."""
    try:
        ref = f"refs/remotes/{remote}/{branch(vault)}"
    except GitError:
        return None
    if run(vault, "rev-parse", "--verify", "-q", ref).returncode != 0:
        r = run(vault, "rev-list", "--count", "HEAD")
    else:
        r = run(vault, "rev-list", "--count", f"{ref}..HEAD")
    return int(r.stdout.strip()) if r.returncode == 0 else None


def push(vault: Path, remote: str) -> str:
    """Push the current branch; never forced. Returns git's summary, raises GitError."""
    name = branch(vault)
    r = run(vault, "push", "--porcelain", "-u", remote, f"HEAD:refs/heads/{name}", timeout=PUSH_TIMEOUT)
    out = f"{r.stdout}\n{r.stderr}"
    if r.returncode != 0:
        if "[rejected]" in out or "non-fast-forward" in out or "fetch first" in out:
            raise GitError(f"push to {remote} rejected: the remote has commits that are not here; "
                           "kb never force-pushes (inspect with: git -C <vault> fetch && git log ..FETCH_HEAD)")
        check(r)
    return "up to date" if "[up to date]" in out else f"pushed {name} to {remote}"
