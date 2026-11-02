"""The report behind the diff gate of `kb rewrite` (design §11.3).

The approval rests on what this report shows, so it is a safety property
(design §12.4): what changes, what disappears, what was written by hand.
"""

import difflib
import hashlib
from pathlib import Path

from ms_kb import history, pagecheck
from ms_kb.history import GitError
from ms_kb.links import targets
from ms_kb.notes import MY_WORDS, PROFILE, parse, section_text, split_sections
from ms_kb.secretscan import find_hidden

SHRINK_LIMIT = 0.5  # the same as integrity.DAMAGE_RATIO; provisional (design §11.3)


def approval_hash(rel: str, original: str, new: str) -> str:
    """Path, current file and new content: any change to one of them needs a new review (design §12.6)."""
    current = hashlib.sha256(original.encode("utf-8")).hexdigest()
    return hashlib.sha256("\0".join((rel, current, new)).encode("utf-8")).hexdigest()[:12]


def shrink_ratio(result) -> float:
    old = len(parse(result.original).body.strip().encode("utf-8"))
    new = len(parse(result.text).body.strip().encode("utf-8"))
    return new / old if old else 1.0


def _diff(old: str, new: str, old_name: str, new_name: str) -> list[str]:
    return [line.rstrip("\n") for line in difflib.unified_diff(
        old.splitlines(True), new.splitlines(True), old_name, new_name)]


def _counts(old: str, new: str) -> tuple[int, int]:
    lines = list(difflib.ndiff(old.splitlines(), new.splitlines()))
    return sum(l.startswith("+ ") for l in lines), sum(l.startswith("- ") for l in lines)


def _section_lines(old_body: str, new_body: str, declared: str | None) -> list[str]:
    old, new = split_sections(old_body), split_sections(new_body)
    table, changed = [], []
    for name in [*new, *(n for n in old if n not in new)]:
        if not name:
            continue
        if name not in old:
            state = "new"
        elif name not in new:
            state = "removed"
        else:
            added, removed = _counts(old[name], new[name])
            state = f"+{added} -{removed}" if added or removed else "unchanged"
        if state != "unchanged":
            changed.append(name)
        table.append(f"  {name}: {state}")
    lines = []
    if declared is not None:
        wanted = {s.strip().casefold() for s in declared.split(",") if s.strip()}
        outside = [n for n in changed if n.casefold() not in wanted and n != MY_WORDS]
        if outside:
            lines.append(f"WARNING: changes outside --sections: {', '.join(outside)}")
    return lines + ["sections:", *table]


def _removed(old_body: str, new_body: str, ratio: float, allow_shrink: bool) -> list[str]:
    old, new = split_sections(old_body), split_sections(new_body)
    lines = ["what disappears:"]
    if gone := [n for n in old if n and n not in new]:
        lines.append(f"  sections: {', '.join(gone)}")
    if links := sorted(targets(old_body) - targets(new_body)):
        lines.append(f"  links: {', '.join(f'[[{t}]]' for t in links)}")
    kept = set((section_text(new_body, "Sources") or "").splitlines())
    if sources := [l for l in (section_text(old_body, "Sources") or "").splitlines() if l.strip() and l not in kept]:
        lines += ["  source lines:", *(f"    {l}" for l in sources)]
    size = f"  body size: {ratio:.0%} of the current one"
    if ratio < SHRINK_LIMIT:
        size += ("; allowed with --allow-shrink" if allow_shrink
                 else f"; below {SHRINK_LIMIT:.0%}: the write is refused unless the user passes --allow-shrink")
    return lines + [size]


def _hand_edited(vault: Path, result) -> list[str]:
    if history.repo_status(vault)[0] != "own":
        return ["hand-edited lines: unknown (the vault has no Git repository of its own)"]
    try:
        edited = history.hand_edited(vault, result.rel)
    except GitError as e:
        return [f"hand-edited lines: unknown ({e})"]
    kept = set(result.text.splitlines())
    changing = [(edited[l], l) for l in result.original.splitlines()
                if l.strip() and l in edited and l not in kept and not l.startswith("updated:")]
    if not changing:
        return ["hand-edited lines that change: none"]
    return ["hand-edited lines that change:", *(f"  {when}: {line}" for when, line in changing)]


def build(vault: Path, result, key: str, sections: str | None, allow_shrink: bool,
          since: str | None = None, since_text: str | None = None) -> str:
    old_body = parse(result.original).body
    new_body = parse(result.text).body
    is_profile = result.rel == PROFILE
    lines = [f"rewrite of {result.rel}", f"reason: {result.reason}", ""]
    if since:
        lines.append(f"since the reviewed draft {since}:")
        if since_text is None:
            lines.append("  that draft is no longer kept; read the full diff below")
        else:
            lines += _diff(since_text, result.text, f"draft {since}", "this draft") or ["  no change"]
        lines.append("")
    lines += _section_lines(old_body, new_body, sections)
    lines += ["", "diff:", *_diff(result.original, result.text, f"{result.rel} (current)", f"{result.rel} (new)")]
    lines += ["", *_removed(old_body, new_body, shrink_ratio(result), allow_shrink)]
    lines += ["", *_hand_edited(vault, result), ""]
    hidden = find_hidden(result.text, result.original)
    lines += ["hidden text in added lines:", *(f"  line {n}: {l}" for n, l in hidden)] if hidden \
        else ["hidden text in added lines: none"]
    if not is_profile:
        state = "empty" if not section_text(new_body, MY_WORDS) else "carried over unchanged"
        lines += ["", f"## {MY_WORDS}: {state}", ""]
        lines += pagecheck.check(vault, result.rel, result.text, old_body)
    lines += ["", f"approval hash: {key}"]
    return "\n".join(lines)
