"""Vault structure (note-schema-v0 §4): create what is missing, never overwrite."""

from datetime import date
from importlib.resources import files
from pathlib import Path

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
    """Relative path in the vault -> content to write if the file is missing."""
    today = date.today().isoformat()
    result = {f"templates/{t}.md": _template(f"{t}.md") for t in NOTE_TEMPLATES}
    result["learning_profile.md"] = _template("learning_profile.md").replace("{{date:YYYY-MM-DD}}", today)
    result["README.md"] = _template("vault-README.md")
    return result


def init_vault(path: Path) -> list[tuple[str, str]]:
    """Create the vault structure in `path`. Returns (relative path, "created" | "exists")."""
    report = []
    path.mkdir(parents=True, exist_ok=True)
    for d in VAULT_DIRS:
        target = path / d
        report.append((f"{d}/", "exists" if target.is_dir() else "created"))
        target.mkdir(exist_ok=True)
    for rel, content in _vault_files().items():
        target = path / rel
        if target.exists():
            report.append((rel, "exists"))
            continue
        target.write_text(content, encoding="utf-8")
        report.append((rel, "created"))
    return report


def check_vault(path: Path) -> list[str]:
    """Relative paths of the expected structure that are missing in `path`."""
    missing = [f"{d}/" for d in VAULT_DIRS if not (path / d).is_dir()]
    missing += [rel for rel in _vault_files() if not (path / rel).exists()]
    return missing


def git_work_tree(path: Path) -> Path | None:
    """The enclosing Git work tree of `path`, if any."""
    for p in [path, *path.parents]:
        if (p / ".git").exists():
            return p
    return None
