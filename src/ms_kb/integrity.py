"""Deleted, moved and damaged notes and broken links, against the manifest (design §12.4).

The manifest (in vaultstate) says which notes must exist; Git and Time
Machine say where to bring them back from. Every note in the type folders and
the learning profile is tracked, whoever wrote it.
"""

import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from ms_kb.links import Resolver, targets
from ms_kb.notes import PROFILE, NoteError, parse
from ms_kb.search import note_files
from ms_kb.vaultstate import fingerprint, record

RESTORED = re.compile(r"\.restored-\d{8}-\d{6}(\.[^.]+)?$")
DAMAGE_RATIO = 0.5


@dataclass
class Finding:
    level: str  # ok | info | warn | error
    kind: str  # seeded | changed | moved | added | damaged | deleted | link | leftover
    rel: str
    message: str


def is_restored_copy(path: Path) -> bool:
    return RESTORED.search(path.name) is not None


def tracked_files(vault: Path) -> list[str]:
    rels = [p.relative_to(vault).as_posix() for p in note_files(vault)]
    if (vault / PROFILE).is_file():
        rels.append(PROFILE)
    return rels


def damage(path: Path, now: dict, before: dict) -> str | None:
    """Why the file looks damaged rather than edited, or None."""
    if now["size"] == 0:
        return "the file is empty"
    if now["size"] < before["size"] * DAMAGE_RATIO:
        return f"the file shrank from {before['size']} to {now['size']} bytes"
    try:
        text = path.read_text(encoding="utf-8")
        meta = parse(text).meta
    except (UnicodeDecodeError, NoteError) as e:
        return f"the frontmatter no longer parses ({e})"
    if before.get("title") and not meta:
        return "the frontmatter is gone"
    return None


def acknowledge(state: dict, vault: Path, rel: str) -> str:
    """Accept the current state of `rel` as intentional."""
    notes = state["notes"]
    if (vault / rel).is_file():
        record(state, vault, rel, "acknowledged")
        return f"{rel}: current version accepted"
    if notes.pop(rel, None) is None:
        return f"{rel}: not in the manifest"
    return f"{rel}: deletion accepted; it is no longer reported"


def check(vault: Path, state: dict) -> list[Finding]:
    """Compare the vault with the manifest and update the manifest for normal changes."""
    notes = state["notes"]
    current = tracked_files(vault)
    if not notes:
        for rel in current:
            record(state, vault, rel, "seed")
        state["links"] = sorted(_resolved_links(vault, current)[0])
        return [Finding("info", "seeded", "", f"manifest started with {len(current)} notes")]

    findings = []
    new = {rel: fingerprint(vault / rel) for rel in current if rel not in notes}
    for rel, before in sorted(notes.items()):
        path = vault / rel
        arg = shlex.quote(rel)  # paths in hints must paste into a shell as they are
        if path.is_file():
            now = fingerprint(path)
            if now["sha256"] == before["sha256"]:
                continue
            if reason := damage(path, now, before):
                findings.append(Finding("error", "damaged", rel,
                                        f"{rel} looks damaged: {reason}; compare with kb history {arg}, "
                                        f"bring it back with kb restore {arg} --force, "
                                        f"or accept it with kb doctor --ack {arg}"))
                continue
            notes[rel] = now | {"writer": "external"}
            continue
        moved = next((r for r, fp in new.items() if fp["sha256"] == before["sha256"]), None)
        if moved is None and before.get("title"):
            moved = next((r for r, fp in new.items() if fp.get("title") == before["title"]), None)
        if moved:
            notes[moved] = new.pop(moved) | {"writer": notes.pop(rel).get("writer", "external")}
            findings.append(Finding("info", "moved", rel, f"{rel} moved to {moved}"))
            continue
        trash = vault / ".trash" / path.name
        where = " (a copy is in Obsidian's .trash/)" if trash.is_file() else ""
        findings.append(Finding("error", "deleted", rel,
                                f"{rel} was deleted{where}; bring it back with kb restore {arg}, "
                                f"or accept the deletion with kb doctor --ack {arg}"))
    for rel, fp in new.items():
        notes[rel] = fp | {"writer": "external"}

    resolved, used = _resolved_links(vault, current)
    for target in sorted(set(state.get("links", [])) & set(used) - resolved):
        where = ", ".join(sorted(used[target])[:3])
        findings.append(Finding("warn", "link", where, f"[[{target}]] no longer resolves (in {where})"))
    state["links"] = sorted(resolved)

    for path in sorted(vault.rglob("*.restored-*")):
        if is_restored_copy(path) and ".trash" not in path.relative_to(vault).parts:
            rel = path.relative_to(vault).as_posix()
            findings.append(Finding("warn", "leftover", rel,
                                    f"{rel} is a restored copy; merge what you need and delete it"))
    return findings


def _resolved_links(vault: Path, rels: list[str]) -> tuple[set[str], dict[str, set[str]]]:
    """(link targets that resolve, target -> notes using it)."""
    used: dict[str, set[str]] = {}
    for rel in rels:
        try:
            text = (vault / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for target in targets(text):
            used.setdefault(target, set()).add(rel)
    resolver = Resolver(vault)
    return {t for t in used if resolver.resolves(t)}, used
