---
title: "Personal Knowledge System — Note Schema, Vault Structure and Configuration v1"
document_version: "1.0"
created: "2026-11-02"
language: en
status: approved_for_v0.7
supersedes: "note-schema-v0.md (0.5)"
design_ref: "personal-knowledge-design-v2.md"
design_version: "2.3"
---

# Note schema, vault structure and configuration v1

The contract the CLI checks. It replaces [note-schema-v0.md](note-schema-v0.md), which stays the reference for the v1 note types (`concept`, `research`, `learning-session`, `project`, and `source` notes with `topics`): they remain valid and readable, and skills no longer create them. The reasons behind this contract are in design §5–§7.

Any change here is recorded in §8 and in the [release history](../CHANGELOG.md), with a migration path ([releases.md](releases.md)).

## 1. Frontmatter

Dates are `"YYYY-MM-DD"` strings; unquoted dates, which Obsidian Properties writes, are accepted.

**Topic page** (`type: topic`):

| Field | Required | Format |
|---|---|---|
| `type` | yes | `topic` |
| `title` | yes | string; the file is `topics/<Title>.md` |
| `summary` | yes | one line; over about 160 characters is a warning |
| `tags` | yes, 1–3 | §2; more than 3 is a warning |
| `created`, `updated` | yes | date; `created` never changes |
| `aliases` | no | list of strings; links to them resolve to this page |
| `created_by` | only when created by a skill | §3 |

`updates`, `related`, `sources` and `topics` are not used: any other field is a warning.

**Source card** (`type: source` with `tags`): the same fields, plus exactly one of `url` and `ref`, and optional `author` and `published` (date). The file is `sources/<Title>.md`. A `source` note with `topics` and no `tags` is a v1 note and follows note-schema-v0.

## 2. Tags and sections

**Tags:** lowercase ASCII words joined by `-`, with at most one nesting level through `/`: `python`, `python/concurrency`, `ml/rag`. Anything else is an error. `kb search --tag python` and `kb index --tag python` match nested tags.

**Topic page sections**, in this order: `Summary`, `In my words`, `Key ideas`, `Details`, `Open questions`, `Related`, `Sources`.

**Source card sections**, in this order: `Summary`, `Key ideas`, `Illustrations`, `How it explains`, `Use for`, `Related`.

Rules for both:

- `## Summary` is required and not empty. Every other section may be empty or absent.
- Fixed sections out of order, or a section appearing twice, is an error.
- Other sections are a warning. On a topic page they are allowed only after `## In my words`, which comes right after `## Summary`.
- A topic page over about 200 lines is a warning.

## 3. Provenance

`created_by` is stamped by the CLI at creation with `--skill` and never changes: `skill`, `skill_version`, `package_version`, `skill_ref` (`SKILL.md` at the release tag), `date`, and `agent` when detected. Hand-written notes have none.

Every write is a commit with the trailers `Kb-Skill`, `Kb-Skill-Version`, `Kb-Version`, `Kb-Agent` (when known) and `Kb-Reason`: required for `kb rewrite`, and for `kb extend` with `--skill`; from `--reason` on `kb new`; made from `--why` by `kb link`; fixed for `kb my-words`. `kb` writes no `updates` entries; existing ones on v1 notes stay and are still validated. Query them with `kb history --skill S --version V --reason TEXT`.

## 4. File names and vault structure

As in design §6.8. `topics/` and `sources/` hold pages named after the title, without the characters `/\:*?"<>|#^[]`. `kb init` creates missing folders and templates and never overwrites.

## 5. Learning profile

`learning_profile.md` has `## Current directions` and `## Preferences`, with `title` and `updated` in its frontmatter. It is user data (design §12.4). `kb rewrite learning_profile.md` changes it through the same gate, and `kb extend` still appends to it. `kb doctor` warns above 150 lines. Older sections stay until the user rewrites the profile.

## 6. User configuration

Unchanged: see [note-schema-v0.md §6](note-schema-v0.md). New state next to the configuration: `drafts-<kb>/`, the drafts kept for `kb rewrite --since`.

## 7. Validation and writing

Notes are written only by the CLI (design §9.1).

| Command | Works on | Refuses |
|---|---|---|
| `kb new topic` | new page | no `--body-file`; a duplicate (below); text in `## In my words`; `--topic`, `--related`, `--source`, `--url` |
| `kb new source` | new card | no `--body-file`; a duplicate (below); not exactly one of `url` and `ref`; `--topic`, `--related`, `--source` |
| `kb rewrite` | topic page, profile | anything else; a draft with frontmatter; a draft changing `## In my words`; without `--approve` the matching hash; a body under half of the current one without `--allow-shrink` |
| `kb link` | any note but the profile | a target that does not resolve; a link to itself |
| `kb extend` | any note | on pages: `--topic`, `--related`, `--source` and a `## In my words` block; with `--skill`: no `--reason`, except for the profile |
| `kb my-words` | topic page | an empty text; a `#` or `##` heading or an open code fence in the text |

A missing section is created in its fixed place. Links that do not resolve are refused by `kb link` and reported by the dry-runs of `kb new` and `kb rewrite`: a draft may name a page to create next.

**Duplicates.** Refused: the same file name in any folder; the same title or alias within the type (ignoring case, spaces and punctuation); for a card, the same normalized URL (lowercase scheme and host, no fragment, no trailing slash, no `utm_*` parameters). A title or alias with similarity ≥ 0.85 within the type is refused unless `--allow-similar`.

**Added lines.** Every write refuses key-like strings (`--allow-secret-like` is the user's), including in the reason, and warns about hidden text (design §12.6).

## 8. Document history

- **1.0 — 2026-11-02:** first version, roadmap stages 5 and 6: topic pages, tags, source cards, provenance of changes in trailers, the commands that write.
