"""Obsidian wiki-link resolution, implemented in kb (design §12.4).

A link `[[target|alias]]`, `[[target#heading]]` or `![[embed]]` resolves when
some file matches it: by path suffix when the target has a folder, otherwise by
file name (without `.md` for notes) or by a note's frontmatter `aliases`.
Case is ignored, as in Obsidian on macOS.
"""

import re
from pathlib import Path

from ms_kb.notes import NoteError, parse

LINK = re.compile(r"!?\[\[([^\[\]\n]+?)\]\]")
SKIP_DIRS = {".git", ".obsidian", ".trash"}


def normalize(raw: str) -> str | None:
    target = raw.split("|", 1)[0].split("#", 1)[0].split("^", 1)[0].strip().replace("\\", "/")
    if target.lower().endswith(".md"):
        target = target[:-3]
    return target.lower() or None


def targets(text: str) -> set[str]:
    return {t for raw in LINK.findall(text) if (t := normalize(raw))}


def vault_files(vault: Path) -> list[Path]:
    return [p for p in vault.rglob("*") if p.is_file() and not SKIP_DIRS & set(p.relative_to(vault).parts)]


class Resolver:
    def __init__(self, vault: Path):
        self.paths: set[str] = set()
        self.names: set[str] = set()
        self.aliases: set[str] = set()
        for path in vault_files(vault):
            rel = path.relative_to(vault).as_posix()
            if path.suffix == ".md":
                rel = rel[:-3]
                try:
                    aliases = parse(path.read_text(encoding="utf-8")).meta.get("aliases") or []
                except (NoteError, UnicodeDecodeError, OSError):
                    aliases = []
                self.aliases.update(str(a).lower() for a in aliases if a)
            rel = rel.lower()
            self.paths.add(rel)
            self.names.add(rel.rsplit("/", 1)[-1])

    def resolves(self, target: str) -> bool:
        if "/" in target:
            return any(p == target or p.endswith(f"/{target}") for p in self.paths)
        return target in self.names or target in self.aliases
