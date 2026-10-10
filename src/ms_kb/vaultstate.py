"""Per-vault state kept outside the vault, next to installed.toml (design §12.4).

`vault-<kb>.json` holds the manifest of notes (path -> sha256, size, mtime,
title, writer), the wiki-link targets that resolved at the last check, and
the last Git commit, push and error.
`<kb>.lock` serializes kb runs on one vault.
"""

import fcntl
import hashlib
import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from ms_kb.config import ConfigError, config_path
from ms_kb.notes import NoteError, parse

LOCK_TIMEOUT = 30


def state_path(name: str) -> Path:
    return config_path().parent / f"vault-{name}.json"


def empty() -> dict:
    return {"notes": {}, "links": [], "git": {}}


def load(name: str) -> dict:
    path = state_path(name)
    if not path.exists():
        return empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty()
    return empty() | data


def save(name: str, state: dict) -> None:
    path = state_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


@contextmanager
def lock(name: str):
    """Exclusive lock for one kb run on this vault."""
    path = config_path().parent / f"{name}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        deadline = time.monotonic() + LOCK_TIMEOUT
        while True:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    raise ConfigError(f"another kb command is working on {name!r}; try again") from None
                time.sleep(0.2)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fingerprint(path: Path) -> dict:
    data = path.read_bytes()
    st = path.stat()
    entry = {"sha256": hashlib.sha256(data).hexdigest(), "size": st.st_size, "mtime": int(st.st_mtime)}
    try:
        title = parse(data.decode("utf-8")).meta.get("title")
    except (UnicodeDecodeError, NoteError):
        title = None
    if title:
        entry["title"] = str(title)
    return entry


def record(state: dict, vault: Path, rel: str, writer: str) -> None:
    """Remember a note as it is now on disk (hash after the write)."""
    state["notes"][rel] = fingerprint(vault / rel) | {"writer": writer}


def git_ok(state: dict, field: str, rev: str | None = None) -> None:
    state["git"][field] = now()
    if rev:
        state["git"]["last_rev"] = rev
    state["git"].pop("last_error", None)


def git_failed(state: dict, message: str) -> None:
    state["git"]["last_error"] = message
    state["git"]["last_error_at"] = now()
