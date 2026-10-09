---
title: "Personal Knowledge System — Note Schema, Vault Structure and Configuration v0"
document_version: "0.2"
created: "2026-10-09"
language: en
status: approved_for_mvp
design_ref: "personal-knowledge-design-v1.md"
design_version: "1.7"
---

# Note schema, vault structure and configuration v0

This document records the decisions made in roadmap stage 0. It closes open questions 4 (folder structure and metadata schema) and 12 (configuration format) from the user stories. It refines design §5–§7 and §4.2. Schema validation in the CLI (stage 2) checks exactly what is written here.

Version 0 means it can still change before v1.0. Any change to it is recorded in §7 and in the release history.

## 1. Frontmatter: common fields

All notes are Markdown files with YAML frontmatter. Dates are `YYYY-MM-DD` strings in quotes. The validator also accepts unquoted dates (`created: 2026-10-09`), because Obsidian Properties writes them that way.

| Field | Required | Format | Purpose |
|---|---|---|---|
| `type` | yes | one of `concept`, `source`, `research`, `learning-session`, `project` | The purpose of the note |
| `title` | yes | string | A readable title; usually matches the file name |
| `created` | yes | `"YYYY-MM-DD"` | Creation date |
| `updated` | yes | `"YYYY-MM-DD"` | Date of the last content change |
| `topics` | yes, ≥ 1 | list of kebab-case slugs (`agent-memory`) | Search and topical grouping |
| `related` | no | list of `"[[Note]]"` | Links to related notes |
| `sources` | no | list of URLs and/or `"[[source-note]]"` | Basis of the content |
| `aliases` | no | list of strings | Native Obsidian property: alternative names for links |
| `created_by` | only for notes produced by a skill | see §3 | Provenance of creation |
| `updates` | no | see §3 | Provenance of later changes made by a skill |

Unknown fields are allowed: the validator reports them as a warning, not an error. The user can add their own fields in Obsidian.

## 2. Fields per type

| Type | Extra fields | Recommended body sections |
|---|---|---|
| `concept` | — | Explanation; Diagram (Mermaid, if useful); Limitations; Insights; Related |
| `source` | `url` (required) | Summary; Key takeaways; Why I saved it; Source; Related |
| `research` | `as_of` (required, `"YYYY-MM-DD"` — the date the comparison applies to); `sources` (required, ≥ 1) | Question and scope; Comparison; Findings; Limitations and open questions; Sources; Related |
| `learning-session` | `session_date` (required, `"YYYY-MM-DD"`) | Topics; Conclusions; Assumptions (not confirmed); Open questions; Related |
| `project` | `external_context` (optional map: `github.repo`, `github.issue`, `notion.project`, ...) | Goal; Decisions and reasons; Knowledge gained; Insights; External links |

**`insight` is not a sixth type.** An observation from practice goes in an `## Insights` section of a `concept` or `project` note. If it needs to be found separately, the note gets the `insight` topic. This follows US-04 and keeps the number of types small.

## 3. Provenance

Provenance is **stamped by the CLI**, not written by the model: the values come from the installed package (design §9.1, US-12). It is present only on notes created or changed through a skill. Notes written by hand have no `created_by` and nobody invents one for them.

```yaml
created_by:
  skill: add-knowledge
  skill_version: "0.3.0"
  package_version: "0.3.0"
  skill_ref: "https://github.com/modvala/ms-kb/blob/v0.3.0/src/ms_kb/skills/add-knowledge/SKILL.md"
  date: "2026-10-09"
  agent: claude-code        # optional: only if the value is known reliably
updates:
  - date: "2026-11-02"
    skill: add-knowledge
    skill_version: "0.4.0"
    package_version: "0.4.0"
    skill_ref: "https://github.com/modvala/ms-kb/blob/v0.4.0/src/ms_kb/skills/add-knowledge/SKILL.md"
    summary: "Extended with the reranking section"
```

| Field | Required | Meaning |
|---|---|---|
| `skill` | yes | Skill name (matches `name` in `SKILL.md`) |
| `skill_version` | yes | Version of the skill's rules, from the skill's `metadata.version` |
| `package_version` | yes | Version of the `ms-kb` package that wrote the note |
| `skill_ref` | yes | Link to the exact `SKILL.md` at the release tag |
| `date` | yes | Date of the operation |
| `agent` | no | `claude-code`, `codex` or `cursor`, if known |
| `summary` | only in `updates` | One line on what changed |

**Exact rules (design §7):** `skill_ref` points to the file at a Git release tag. Tags are not moved, so the link always shows the rules that were used. No separate snapshots are kept. A development build (version with `.dev`) writes a link to `main` and the validator flags it as a warning.

`updates` only grows: entries are added, never rewritten. The original `created_by` is never changed.

## 4. File names and vault structure

```
<vault>/
  concepts/            # concept — <Title>.md, e.g. RAG.md
  sources/             # source — <Title>.md
  research/            # research — <slug>.md, the date is in as_of
  learning-sessions/   # learning-session — YYYY-MM-DD-<slug>.md
  projects/            # project — <Title>.md
  attachments/         # images, PDFs; referenced as ![[file.png]]
  templates/           # copies of the package templates for Obsidian's Templates core plugin
  learning_profile.md  # the brief learning profile (§5)
  README.md            # what this folder is and that it is managed by ms-kb
```

- Title-based names (`concepts/RAG.md`) make `[[RAG]]` work in Obsidian without paths. Characters not allowed in file names (`/ \ : * ? " < > |`, `#`, `^`, `[`, `]`) are removed from the title when the file name is built; the full title stays in `title`.
- A slug is lowercase ASCII words joined by `-`. `kb new` builds it from the title; when the title gives no ASCII words (for example a Cyrillic title), `--slug` is required.
- The folder matches the type, but the type is defined by `type`, not by the folder (design §5.1). The validator warns if they disagree.
- `templates/` is overwritten only by an explicit command (stage 1: `kb init` creates it and does not touch existing files).
- `.obsidian/` is created by Obsidian itself; the package does not write to it.

## 5. Learning profile

`learning_profile.md` is a short file (target: under ~150 lines) with links to detailed notes. It has no `type` and is not validated as a note. It is **user data**: `kb init` creates it only for a new vault and never silently recreates it on a vault in use (design §12.4); `kb init --new-profile` starts an empty one on request.

```markdown
---
title: "Learning profile"
updated: "2026-10-09"
---

# Learning profile

## Current directions
- [[RAG]] — retrieval quality and reranking

## Known topics
- [[Transformers]] — attention, positional encoding

## Recently studied
- 2026-10-09 — [[2026-10-09-mcp-basics]]

## Open questions
- How does reranking interact with chunk size? — from [[2026-10-09-rag-session]]
```

How the profile is loaded (always or on demand) is decided in stage 3.

## 6. User configuration

**Format:** TOML. Reading uses `tomllib` from the Python standard library; writing (stage 1) adds `tomli-w`.

**Location:** `$XDG_CONFIG_HOME/ms-kb/config.toml`, i.e. `~/.config/ms-kb/config.toml` by default, on macOS and Linux alike. The `KB_CONFIG` environment variable overrides the path (used by tests and CI). The configuration is outside the vault and outside the repository; the repository ships only an example.

```toml
schema_version = 1
default_kb = "main"

[kbs.main]
vault_path = "~/Knowledge/main"

[clients]
enabled = ["claude-code", "codex", "cursor"]

# Stage 4:
# [kbs.main.sync]
# provider = "rclone"
# remote = "gdrive:kb-backup/main"
```

- `schema_version` is the configuration schema version (design §7), independent of the package version. A change requires a migration path.
- The MVP uses one knowledge base (`default_kb`), but the `[kbs.<name>]` shape already allows several (US-21) without a migration.
- `vault_path` may use `~`; the CLI expands it.
- The list of skills installed by the CLI and their versions is kept separately, in `~/.config/ms-kb/installed.toml` (stage 2). It is state, not settings.
- **Skills never read this file.** They call the CLI (for example, `kb where` in stage 1, `kb search` in stage 2). The file format stays internal to the CLI, and skills do not depend on the current working folder (US-18).

## 7. Validation and writing (stage 2)

Notes are written only by the CLI (design §9.1):

- `kb new TYPE --title … --topic …` builds the frontmatter, takes the body from stdin/a file (or the type template), stamps `created_by` when `--skill` is given, validates and writes.
- `kb extend PATH` appends `## Section` blocks to the matching sections (a missing section is created before `## Related`), skips bullet lines already present in the section, merges `topics`/`related`/`sources` without duplicates, sets `updated` and, with `--skill`, appends an `updates` entry. Existing text is never rewritten. `learning_profile.md` can be extended too; it gets no provenance.
- `kb validate [PATH…]` checks notes (by default every note in the type folders).

**Duplicates.** `kb new` refuses to create a note when the vault already has the same file, a note with the same file name in any folder (it would make `[[links]]` ambiguous), or a note of the same type with the same title or alias. Comparison ignores case, spaces and punctuation. A title similar to an existing one of the same type (similarity ≥ 0.85) is refused unless `--allow-similar` is passed. Learning sessions are dated and expected to repeat topics, so only the file itself counts for them.

**Skill versions.** `skill_version` comes from `~/.config/ms-kb/installed.toml`, i.e. from the skill copy the agent reads; `skill_ref` points to the tag of the package that installed it. `agent` is set only from environment variables verified for the client ([clients-v0.md](clients-v0.md) §2).

Errors (the note is not written):

- `type` missing or not one of the five values
- a required common or per-type field is missing
- a date is not `YYYY-MM-DD`
- `topics` is empty or contains something other than kebab-case slugs
- `created_by` or an `updates` entry is missing a required field

Warnings:

- unknown fields
- the folder does not match `type`
- `skill_ref` does not point to a release tag

## 8. Document history

- **0.1 — 2026-10-09:** first version, roadmap stage 0.
- **0.2 — 2026-10-09:** roadmap stage 2: unquoted dates accepted; slug rule for non-ASCII titles; §7 describes the writing commands, duplicate rules and where skill versions come from; the learning profile is user data (§5).
