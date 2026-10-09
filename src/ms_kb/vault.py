"""Vault structure (note-schema-v0 §4): create what is missing, never overwrite.

Regenerable files (folders, templates, README) are recreated freely; user data
(the learning profile) only on a new vault or on request (design §12.4).
"""

from datetime import date
from importlib.resources import files
from pathlib import Path

from ms_kb.notes import PROFILE

VAULT_DIRS = (
    "concepts",
    "sources",
    "research",
    "learning-sessions",
    "projects",
    "attachments",
    "templates",
)
NOTE_TEMPLATES = ("concept", "source", "research", "learning-session", "project")


def _template(name: str) -> str:
    return (files("ms_kb") / "templates" / name).read_text(encoding="utf-8")


def _vault_files() -> dict[str, str]:
    """Regenerable files: relative path in the vault -> content to write if missing."""
    result = {f"templates/{t}.md": _template(f"{t}.md") for t in NOTE_TEMPLATES}
    result["README.md"] = _template("vault-README.md")
    return result


def _user_files() -> dict[str, str]:
    """User data created once on a new vault (design §12.4). Once written, only
    the user and `kb extend` change it, so a missing copy is a loss to restore,
    not a file to regenerate."""
    today = date.today().isoformat()
    return {PROFILE: _template("learning_profile.md").replace("{{date:YYYY-MM-DD}}", today)}


def has_notes(path: Path) -> bool:
    return any(next((path / d).rglob("*.md"), None) for d in VAULT_DIRS if d not in ("attachments", "templates"))


def init_vault(path: Path, user_files: bool = True) -> list[tuple[str, str]]:
    """Create the vault structure in `path`, never overwriting a file.

    Returns (relative path, "created" | "exists" | "missing"); "missing" is a
    user-data file that was not recreated because `user_files` is false.
    """
    report = []
    path.mkdir(parents=True, exist_ok=True)
    for d in VAULT_DIRS:
        target = path / d
        report.append((f"{d}/", "exists" if target.is_dir() else "created"))
        target.mkdir(exist_ok=True)
    files = _vault_files() | _user_files()
    for rel, content in files.items():
        target = path / rel
        if target.exists():
            report.append((rel, "exists"))
        elif rel in _user_files() and not user_files:
            report.append((rel, "missing"))
        else:
            target.write_text(content, encoding="utf-8")
            report.append((rel, "created"))
    return report


def check_vault(path: Path) -> tuple[list[str], list[str]]:
    """(missing regenerable paths, missing user-data files) of the expected structure."""
    missing = [f"{d}/" for d in VAULT_DIRS if not (path / d).is_dir()]
    missing += [rel for rel in _vault_files() if not (path / rel).exists()]
    lost = [rel for rel in _user_files() if not (path / rel).exists()]
    return missing, lost


def git_work_tree(path: Path) -> Path | None:
    """The enclosing Git work tree of `path`, if any."""
    for p in [path, *path.parents]:
        if (p / ".git").exists():
            return p
    return None
