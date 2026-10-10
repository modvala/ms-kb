"""The global instruction (clients-v0 §2.4, design §9.1).

A short block between `<!-- ms-kb:begin … -->` and `<!-- ms-kb:end -->` in the
user-level instruction files of Claude Code and Codex. Only the block is ever
written or removed; the rest of the file is the user's. Cursor keeps User
Rules in its settings, so its text is printed for pasting.
"""

import os
import re
from datetime import date
from importlib.resources import files
from pathlib import Path

from ms_kb import __version__
from ms_kb.installer import display, load_state, save_state

END = "<!-- ms-kb:end -->"
_BLOCK = re.compile(r"^<!-- ms-kb:begin(?: (\S+))? -->\n.*?^<!-- ms-kb:end -->\n?", re.S | re.M)


def instruction_text() -> str:
    return (files("ms_kb") / "global-instruction.md").read_text(encoding="utf-8")


def block() -> str:
    return f"<!-- ms-kb:begin {__version__} -->\n{instruction_text().strip()}\n{END}\n"


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser()


def client_files() -> dict[str, Path]:
    """Instruction file per client that has one on disk."""
    return {
        "claude-code": Path("~/.claude/CLAUDE.md").expanduser(),
        "codex": codex_home() / "AGENTS.md",
    }


def target_files(clients: list[str]) -> list[Path]:
    return [path for client, path in client_files().items() if client in clients]


def block_version(text: str) -> str | None:
    """Version on the begin marker, "" if it has none, None without a block."""
    match = _BLOCK.search(text)
    return None if match is None else (match.group(1) or "")


def apply_block(text: str, new: str | None) -> str:
    """Replace or append the block, or remove it when `new` is None."""
    match = _BLOCK.search(text)
    if match is None:
        if new is None or not text:
            return new or text
        return text + ("\n" if text.endswith("\n") else "\n\n") + new
    before, after = text[: match.start()], text[match.end() :]
    if new is None and not after and before.endswith("\n\n"):
        before = before[:-1]  # the blank line added together with the block
    return before + (new or "") + after


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def install_instructions(clients: list[str], dry_run: bool = False) -> list[tuple[str, str]]:
    """Write the block for `clients`; remove it where a client is no longer enabled.

    Returns [(action, path)] with actions installed / updated / unchanged / removed.
    """
    state = load_state()
    recorded = {Path(t).expanduser() for t in state.get("instructions", {}).get("targets", [])}
    wanted = target_files(clients)
    report = []

    for path in wanted:
        old = _read(path)
        new = apply_block(old, block())
        if new == old:
            report.append(("unchanged", display(path)))
            continue
        report.append(("updated" if block_version(old) is not None else "installed", display(path)))
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new, encoding="utf-8")

    for path in sorted((recorded | set(client_files().values())) - set(wanted)):
        old = _read(path)
        if block_version(old) is None:
            continue
        report.append(("removed", display(path)))
        if not dry_run:
            path.write_text(apply_block(old, None), encoding="utf-8")

    if not dry_run:
        state["instructions"] = {
            "package_version": __version__,
            "installed": date.today().isoformat(),
            "targets": [display(p) for p in wanted],
        }
        save_state(state)
    return report


def check_instructions(clients: list[str]) -> list[tuple[str, str]]:
    """(level, message) per instruction file, for kb doctor."""
    result = []
    for path in target_files(clients):
        version = block_version(_read(path))
        if version is None:
            result.append(("warn", f"global instruction not installed in {display(path)}; run kb install-skills"))
        elif version != __version__:
            result.append(("warn", f"global instruction in {display(path)} is from {version or '?'}, "
                                   f"CLI is {__version__}; run kb install-skills"))
        else:
            result.append(("ok", f"global instruction {version} in {display(path)}"))
    override = codex_home() / "AGENTS.override.md"
    if "codex" in clients and override.exists():
        result.append(("warn", f"{display(override)} takes precedence over AGENTS.md; "
                               f"copy the ms-kb block into it (kb install-skills --print-instruction)"))
    return result
