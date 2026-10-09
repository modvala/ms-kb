"""Bundled skills and their installation into the clients (clients-v0 §2, design §4.1)."""

import shutil
import tomllib
from datetime import date
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

import tomli_w
from ruamel.yaml.comments import CommentedMap

from ms_kb import __version__
from ms_kb.config import config_path
from ms_kb.notes import parse, q, read_note, render

class SkillError(Exception):
    pass


CLIENT_DIRS = {
    "claude-code": "~/.claude/skills",
    "codex": "~/.agents/skills",
    "cursor": "~/.cursor/skills",
}


def _skills_root() -> Traversable:
    return files("ms_kb") / "skills"


def bundled_skills() -> list[str]:
    return sorted(p.name for p in _skills_root().iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def bundled_version(skill: str) -> str | None:
    """`metadata.version` of a bundled skill, or None if the package has no such skill."""
    skill_md = _skills_root() / skill / "SKILL.md"
    if not skill_md.is_file():
        return None
    meta = parse(skill_md.read_text(encoding="utf-8")).meta
    return str((meta.get("metadata") or {}).get("version", ""))


def target_dirs(clients: list[str]) -> list[Path]:
    """Skills directories for the enabled clients.

    Cursor also reads ~/.claude/skills and ~/.agents/skills, so it gets its own
    copy only when neither Claude Code nor Codex is enabled.
    """
    dirs = [CLIENT_DIRS[c] for c in ("claude-code", "codex") if c in clients]
    if "cursor" in clients and not dirs:
        dirs.append(CLIENT_DIRS["cursor"])
    return [Path(d).expanduser() for d in dirs]


def installed_path() -> Path:
    """State, not settings: kept next to the configuration (note-schema-v0 §6)."""
    return config_path().parent / "installed.toml"


def load_installed() -> dict[str, dict]:
    path = installed_path()
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8")).get("skills", {})


def save_installed(skills: dict[str, dict]) -> None:
    path = installed_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps({"skills": skills}), encoding="utf-8")


def display(path: Path) -> str:
    try:
        return f"~/{path.relative_to(Path.home()).as_posix()}"
    except ValueError:
        return str(path)


def _copy_tree(src: Traversable, dest: Path) -> None:
    dest.mkdir()
    for item in src.iterdir():
        if item.name == "__pycache__":
            continue
        if item.is_dir():
            _copy_tree(item, dest / item.name)
        else:
            (dest / item.name).write_bytes(item.read_bytes())


def _copy_skill(skill: str, target: Path) -> None:
    """Copy the skill and record the package version in the copy's SKILL.md."""
    tmp = target.with_name(f".{target.name}.ms-kb-tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    _copy_tree(_skills_root() / skill, tmp)
    skill_md = tmp / "SKILL.md"
    note = read_note(skill_md)
    metadata = note.meta.get("metadata")
    if metadata is None:
        metadata = note.meta["metadata"] = CommentedMap()
    metadata["package_version"] = q(__version__)
    skill_md.write_text(render(note), encoding="utf-8")
    if target.exists():
        shutil.rmtree(target)
    tmp.rename(target)


def install_skills(clients: list[str], force: bool = False, dry_run: bool = False) -> tuple[list[tuple[str, str]], int]:
    """Install the bundled skills for `clients`; remove copies that are no longer wanted.

    Only folders recorded in installed.toml are overwritten or removed; another
    folder with the same name is left alone unless `force`. Returns
    ([(action, path)], number of errors).
    """
    installed = load_installed()
    owned = {Path(t).expanduser() for entry in installed.values() for t in entry.get("targets", [])}
    report, errors, state = [], 0, {}
    today = date.today().isoformat()

    for skill in bundled_skills():
        targets = []
        for d in target_dirs(clients):
            target = d / skill
            if target.exists() and target not in owned and not force:
                report.append(("skipped", f"{display(target)} exists and is not managed by ms-kb; use --force"))
                errors += 1
                continue
            report.append(("updated" if target.exists() else "installed", display(target)))
            if not dry_run:
                d.mkdir(parents=True, exist_ok=True)
                _copy_skill(skill, target)
            targets.append(target)
        if targets:
            state[skill] = {
                "version": bundled_version(skill),
                "package_version": __version__,
                "installed": today,
                "targets": [display(t) for t in targets],
            }

    keep = {Path(t).expanduser() for entry in state.values() for t in entry["targets"]}
    for target in sorted(owned - keep):
        if target.exists():
            report.append(("removed", display(target)))
            if not dry_run:
                shutil.rmtree(target)

    if not dry_run:
        save_installed(state)
    return report, errors


def provenance_versions(skill: str) -> tuple[str, str, str | None]:
    """(skill_version, package version that shipped it, warning) for provenance.

    The version comes from installed.toml, i.e. the copy the agent is reading;
    without it, from the bundled skill with a warning.
    """
    bundled = bundled_version(skill)
    if bundled is None:
        raise SkillError(f"unknown skill {skill!r} (bundled: {', '.join(bundled_skills())})")
    entry = load_installed().get(skill)
    if entry is None:
        return bundled, __version__, f"skill {skill!r} is not installed; run kb install-skills"
    version, package = str(entry["version"]), str(entry["package_version"])
    warning = None
    if package != __version__:
        warning = f"installed skill {skill!r} comes from ms-kb {package}, the CLI is {__version__}; run kb install-skills"
    return version, package, warning


def check_installed(clients: list[str]) -> list[tuple[str, str]]:
    """(level, message) per skill and target directory, for kb doctor."""
    result = []
    for d in target_dirs(clients):
        for skill in bundled_skills():
            skill_md = d / skill / "SKILL.md"
            if not skill_md.is_file():
                result.append(("warn", f"skill {skill} not installed in {display(d)}; run kb install-skills"))
                continue
            meta = read_note(skill_md).meta
            package = str((meta.get("metadata") or {}).get("package_version", "?"))
            if package == __version__:
                result.append(("ok", f"skill {skill} {package} in {display(d)}"))
            else:
                result.append(("warn", f"skill {skill} in {display(d)} is from {package}, CLI is {__version__}; run kb install-skills"))
    return result
