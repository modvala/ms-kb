"""Provenance stamped by the CLI, not written by the model (note-schema-v0 §3, US-12)."""

import os
import re

from ruamel.yaml.comments import CommentedMap

from ms_kb import __version__
from ms_kb.installer import provenance_versions
from ms_kb.notes import q

REPO_URL = "https://github.com/modvala/ms-kb"

# Environment variables that identify the client running the shell, verified
# hands-on (clients-v0 §3). Unverified clients are left out: `agent` is
# omitted rather than guessed.
AGENT_ENV = {"claude-code": ("CLAUDECODE", "1")}


def is_release(version: str) -> bool:
    return re.fullmatch(r"\d+(\.\d+)*", version) is not None


def skill_ref(skill: str, package_version: str) -> str:
    """Link to SKILL.md at the release tag; development builds link to main."""
    ref = f"v{package_version}" if is_release(package_version) else "main"
    return f"{REPO_URL}/blob/{ref}/src/ms_kb/skills/{skill}/SKILL.md"


def detect_agent(env=None) -> str | None:
    env = os.environ if env is None else env
    for agent, (var, value) in AGENT_ENV.items():
        if env.get(var) == value:
            return agent
    return None


def stamp(skill: str, day: str, summary: str | None = None) -> tuple[CommentedMap, list[str]]:
    """A `created_by` entry, or an `updates` entry when `summary` is given."""
    skill_version, package, warning = provenance_versions(skill)
    entry = CommentedMap()
    if summary is not None:
        entry["date"] = q(day)
    entry["skill"] = skill
    entry["skill_version"] = q(skill_version)
    entry["package_version"] = q(__version__)
    entry["skill_ref"] = q(skill_ref(skill, package))
    if summary is None:
        entry["date"] = q(day)
    if agent := detect_agent():
        entry["agent"] = agent
    if summary is not None:
        entry["summary"] = q(summary)
    return entry, [warning] if warning else []
