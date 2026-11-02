"""The structural check of a written page and the pages it links to (design §11.4).

Reports only; nothing is changed. Pages that are not linked are read just to
find titles, tags and links, never shown or edited.
"""

import re
from pathlib import Path

from ms_kb.catalogue import tag_counts
from ms_kb.links import LINK, Resolver, normalize, self_names, targets
from ms_kb.notes import MY_WORDS, meta_list, parse
from ms_kb.schema import PAGE_BUDGET
from ms_kb.search import iter_notes

_MASK = re.compile(r"!?\[\[[^\]]*\]\]|\[[^\]]*\]\([^)]*\)|`[^`]*`|https?://\S+")
_ANY_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
MIN_MENTION = 3
MAX_SHARED_TAG = 5


def _prose(body: str) -> str:
    """The text in which a mention could become a link: no headings, code, links or the user's own section."""
    kept, fence, own = [], None, False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else (fence or marker)
            continue
        if fence:
            continue
        if line.startswith("## "):
            own = line[3:].strip() == MY_WORDS
        if own or line.startswith("#"):
            continue
        kept.append(_MASK.sub(" ", line))
    return "\n".join(kept)


def _unlinked_mentions(body: str, others: list[tuple[str, list[str], set[str]]], linked: set[str]) -> list[str]:
    """Titles mentioned without a link, the longest name first so a short one cannot claim its words."""
    names = [(name, title) for title, aliases, keys in others if not keys & linked
             for name in [title, *aliases] if len(name) >= MIN_MENTION]
    text = _prose(body)
    found = []
    for name, title in sorted(names, key=lambda pair: -len(pair[0])):
        pattern = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)", re.I)
        if pattern.search(text):
            text = pattern.sub(" ", text)
            if title not in found:
                found.append(title)
    return found


def headings(body: str) -> set[str]:
    result, fence = set(), None
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else (fence or marker)
        elif not fence and (m := _ANY_HEADING.match(line)):
            result.add(m.group(1).casefold())
    return result


def check(vault: Path, rel: str, text: str, old_body: str | None = None) -> list[str]:
    """Report lines for the page at `rel` with the content `text`."""
    note = parse(text)
    meta = note.meta
    me = self_names(rel, meta)
    linked = targets(note.body)
    resolver = Resolver(vault)
    self_path = (vault / rel).resolve()

    others, by_path = [], {}
    for path, other in iter_notes(vault):
        if path.resolve() == self_path:
            continue
        other_rel = path.relative_to(vault).as_posix()
        title = str(other.meta.get("title", path.stem))
        others.append((title, meta_list(other.meta, "aliases"), self_names(other_rel, other.meta)))
        by_path[path.resolve()] = (title, other, other_rel)

    lines = []
    unresolved = sorted(t for t in linked if not resolver.resolves(t) and t not in me)
    if unresolved:
        lines.append(f"  links that do not resolve: {', '.join(f'[[{t}]]' for t in unresolved)}")

    if mentions := _unlinked_mentions(note.body, others, linked):
        lines.append("  unlinked mentions, candidates for links on this page: "
                     + ", ".join(f"[[{t}]]" for t in mentions))

    linked_paths = {p.resolve() for t in linked if (p := resolver.find(t))} - {self_path}
    no_back = sorted(by_path[p][0] for p in linked_paths
                     if p in by_path and not targets(by_path[p][1].body) & me)
    if no_back:
        lines.append(f"  linked pages without a link back (kb link): {', '.join(no_back)}")

    if old_body is not None and (removed := headings(old_body) - headings(note.body)):
        broken = []
        for path, (title, other, other_rel) in by_path.items():
            for raw in LINK.findall(other.body):
                target, _, heading = raw.split("|", 1)[0].partition("#")
                if heading and normalize(target) in me and heading.strip().casefold() in removed:
                    broken.append(f"{other_rel} -> #{heading.strip()}")
        if broken:
            lines.append(f"  links from other pages to headings this removes: {', '.join(sorted(broken))}")

    tags = meta_list(meta, "tags")
    shared = sorted(by_path[p][0] for p in by_path if p not in linked_paths
                    and set(tags) & set(meta_list(by_path[p][1].meta, "tags")))
    if shared:
        lines.append(f"  pages sharing a tag, not linked: {', '.join(shared[:MAX_SHARED_TAG])}")

    known = tag_counts(vault)  # the page on disk counts, so its current tags are not new
    new_tags = [t for t in tags if t not in known]
    if new_tags:
        lines.append(f"  new tags, to confirm: {', '.join(new_tags)}")

    if meta.get("type") == "topic":
        length = len(text.splitlines())
        hint = "; consider moving a subtopic out" if length > PAGE_BUDGET else ""
        lines.append(f"  page length: {length} lines, budget about {PAGE_BUDGET}{hint}")
    return ["structural check:", *(lines or ["  nothing to report"])]
