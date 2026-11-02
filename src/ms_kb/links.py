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


def self_names(rel: str, meta) -> set[str]:
    """The link targets that point to the note at `rel`: path, file name, title and aliases."""
    stem = rel.removesuffix(".md").lower()
    names = {stem, stem.rsplit("/", 1)[-1]}
    names |= {str(a).lower() for a in (meta.get("aliases") or []) if a}
    return names


class Resolver:
    def __init__(self, vault: Path):
        self.paths: dict[str, Path] = {}
        self.names: dict[str, Path] = {}
        self.aliases: dict[str, Path] = {}
        for path in vault_files(vault):
            rel = path.relative_to(vault).as_posix()
            if path.suffix == ".md":
                rel = rel[:-3]
                try:
                    aliases = parse(path.read_text(encoding="utf-8")).meta.get("aliases") or []
                except (NoteError, UnicodeDecodeError, OSError):
                    aliases = []
                for a in aliases:
                    if a:
                        self.aliases.setdefault(str(a).lower(), path)
            rel = rel.lower()
            self.paths[rel] = path
            self.names.setdefault(rel.rsplit("/", 1)[-1], path)

    def find(self, target: str) -> Path | None:
        """The file a normalized target points to."""
        if "/" in target:
            return next((path for p, path in self.paths.items() if p == target or p.endswith(f"/{target}")), None)
        return self.names.get(target) or self.aliases.get(target)

    def resolves(self, target: str) -> bool:
        return self.find(target) is not None
