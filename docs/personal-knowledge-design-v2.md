---
title: "Personal Knowledge System — Design & Contracts"
document_version: "2.2"
created: "2026-10-12"
updated: "2026-10-19"
language: en
status: discussion_baseline
supersedes: "personal-knowledge-design-v1.md (1.13)"
requirements_ref: "personal-knowledge-user-stories-v2.md"
requirements_version: "2.2"
---

# Personal Knowledge System — Design & Contracts v2.2

## 1. Purpose and status

This document describes the architecture of ms-kb: the content model, the CLI and skills, how the agent reads and writes, provenance, delivery and storage. It implements [user stories v2.0](personal-knowledge-user-stories-v2.md) and replaces [design v1.13](personal-knowledge-design-v1.md).

What changes in v2: the content model moves from learning sessions and append-only notes to **topic pages** that are rewritten in place through an approved diff (§5, §6, §11), with a generated index, tags, explicit links, a check of linked pages when writing, a review mode and a protected `## In my words` section. What stays: delivery (§4), the split between CLI and skills (§9.1), storage, history and data protection (§12), with the trust boundary of §12.4 revised for rewrites.

Status of the parts: everything marked **v0.6** is planned for roadmap stage 5 and everything marked **v0.7** (source cards, §6.9, §11.8) for stage 6; neither is implemented yet; the rest is implemented in package v0.5.0. Field names, command names and limits marked as provisional may change when stage 5 is implemented; the final note schema goes to `note-schema-v1.md`.

Background: the LLM Wiki research (`reports/LLM Wiki Карпати для базы знаний.md`, 2026-10-12) compared the pattern of Andrej Karpathy's gist and about 15 community implementations with ms-kb. ms-kb takes the core of the pattern (pages compiled by the agent and kept current, a generated index, explicit links, checks) and leaves out the agent's autonomy (raw-source folders, `log.md`, cascades of edits across 10–15 pages, automatic filing of answers).

## 2. Key decisions

1. **Obsidian is the canonical store of knowledge.** Notes are Markdown with YAML frontmatter, readable without Obsidian.
2. **One topic, one page, kept current.** The unit of knowledge is a topic page (`topic`). A research session rewrites the page into its best current form; it does not append a log to it. A source worth keeping for later gets a short **source card** (v0.7, §6.9): a summary, not a topic page and not a copy.
3. **One rewritten page per run.** `add-knowledge` changes one topic page. Neighbouring pages receive only targeted lines: a link in `## Related` or an item in `## Open questions`.
4. **The user approves every change of an existing page.** The CLI prints the diff and what it removes; the write needs an approval hash of exactly that diff (§11.3).
5. **Git is the log and the safety net.** Every `kb` write is a commit with provenance trailers; any earlier version can be restored (§12).
6. **The agent writes the page; the user owns `## In my words`.** The section holds the user's text verbatim and is never changed by a rewrite (§6.2, §11.6).
7. **The index is generated, not written.** `kb index` builds the catalogue from frontmatter `summary` and `tags` (§10.1).
8. **Checks are local to the write.** When a page is written, the CLI and the agent check the pages it links to; nothing else is read or changed. There is no check of the whole vault by the model (§11.4).
9. **Review means recall first.** `kb-recall` has a review mode that asks the user before showing the page (§10.3).
10. **Everything that can be checked by code is done by the CLI; everything that needs understanding of text is done by a skill** (§9.1).
11. **The package and the knowledge base are independent**; skills are installed into the user scope of Claude Code, Codex and Cursor (§4).
12. **The vault is local, with its own Git history and a push to a private remote** (§12).

Central principle: **Obsidian stores knowledge, not the world.**

### 2.1. Scope decisions

- One user, one knowledge base. The configuration allows several knowledge bases (`[kbs.<name>]`), but only the default is used.
- Python + `uv`; installation from GitHub; `kb setup` and `kb update`.
- Clients: Claude Code (primary), Codex, Cursor. They read notes directly and change them only through `kb`. ChatGPT is out of scope (§12.2).
- Writes happen only on explicit command: `add-knowledge`, `save-source` (v0.7, §11.8), or a `## In my words` text the user confirmed (in either skill, §11.6).
- Not planned: source registry and external integrations, separate research/project notes, other users, multiple knowledge bases, MCP.

### 2.2. What a vault is

An Obsidian vault is an ordinary folder with Markdown files and attachments. On first open Obsidian creates `.obsidian/` with its settings. There is no database: notes can be read and edited without Obsidian. `kb init` creates the folder structure, templates, the profile and the vault's own Git repository. Obsidian is not required for the package and agents to work; it adds clickable `[[wiki-links]]`, the graph view, tags, Canvas and rendering of Mermaid and attachments.

## 3. Components and their boundaries

| Component | Responsibility | Not its job |
|---|---|---|
| Package repository | Source code, skills, templates, documentation, versions, CI | Personal knowledge |
| `kb` CLI | Locating the vault, search, index, writing notes, diffs and guards, validation, provenance, Git history, sync, restore, skills installation | Understanding text |
| Skills | Turning a conversation into a topic page, choosing the page, wording, checking linked pages for content, recall and review, summarizing a source into a source card | Writing files directly |
| Global instruction | Telling the agent the knowledge base exists and which skills apply | Loading the profile or notes |
| Vault | Topic pages, source cards, attachments, the profile | Trackers, raw copies of sources |
| Vault history and remote | The vault's own Git repository and its private remote (§12) | Two-way sync between devices |
| AI client | Running the skills and the CLI | Access to the vault without `kb` for writes |

```mermaid
flowchart TD
    A["AI client: Claude Code / Codex / Cursor"] --> S["Skills: add-knowledge, kb-recall, save-source"]
    S --> K["kb CLI"]
    K --> V["Vault: topic pages, source cards, profile"]
    K -- "commit per write" --> H["The vault's own Git repository"]
    H -- "kb sync: push" --> Y["Private remote of this vault"]
    U["User in Obsidian"] --> V
```

## 4. Package and knowledge base instances

### 4.1. Package delivery

The package is a Python project installed with `uv` as a tool with the `kb` CLI. It has two parts: the CLI for deterministic operations and skills (`SKILL.md`) with rules for the agent. The CLI installs the skills into the clients; client plugins are not used.

| Action | Commands | What happens |
|---|---|---|
| First install | `uv tool install git+https://github.com/<owner>/<repo>`, then `kb setup` | The CLI is installed; `setup` asks which clients to install skills into and creates or connects the vault |
| Update | `kb update` | Runs `uv tool upgrade`, then the new `kb` reinstalls skills, the global instruction and the schedule |
| Check | `kb doctor` | Shows the CLI and skills versions, the vault state and what to do |
| Specific version / rollback | `kb update --ref vX.Y.Z` | Installs the chosen tag |

Skills installation decisions:

- **Skills are copied, not linked**, so new skills arrive, removed ones are cleaned up and nothing breaks when the `uv` environment changes.
- **The CLI manages only its own skills**, recorded in `installed.toml`.
- **The package version is written into the skill copy**; if the skill and CLI versions diverge, `kb where` warns and `add-knowledge` asks before writing.
- User skills directories ([clients-v0.md](clients-v0.md)): `~/.claude/skills/` for Claude Code and `~/.agents/skills/` for Codex; Cursor reads both.

### 4.2. A knowledge base instance

An instance is a vault plus its configuration. The configuration is TOML at `~/.config/ms-kb/config.toml` (`KB_CONFIG` overrides it), outside the vault and the repository:

```toml
schema_version = 1
default_kb = "main"

[kbs.main]
vault_path = "~/Knowledge/main"

[kbs.main.sync]
provider = "git"
remote = "origin"

[clients]
enabled = ["claude-code", "codex", "cursor"]
```

State, not settings, is kept next to it: `installed.toml` (skills, instructions, schedule), `vault-<kb>.json` (the manifest and the last commit and push) and `<kb>.lock`. Skills never read these files; they call `kb`.

### 4.3. Another user

Not planned (US-22). The package contains nothing personal, so another user could install it and create their own vault; this is not documented or tested beyond the README.

## 5. Content model

### 5.1. Note types

| Type | Status | Purpose |
|---|---|---|
| `topic` | **v0.6, the main type skills create** | One page per topic, kept current |
| `source` | **v0.7, the source card** (§6.9), created by `save-source` | A summary of one source kept for later: what it says, the illustrations worth reusing, how it explains; replaces the v1 `source` contract |
| `concept`, `research`, `learning-session`, `project` | Legacy (v1) | Still valid and readable; skills do not create them; the existing notes are migrated (§11.7) |

A topic is whatever the user would look up by name: "Python concurrency models", "Global Interpreter Lock", "RAG". Granularity follows use: a topic gets its own page when the user would want to read or review it on its own; a page that grows past its budget is split (§6.5). A broad page that mostly links to narrower ones works as a hub.

**One page per topic is enforced twice** (v2.1), because duplicate topics are the most common failure reported by practitioners:

- **By the CLI.** `kb new topic` keeps the v1 duplicate checks and extends them to aliases: it refuses a page when a note with the same file name exists in any folder, or a topic with the same title or alias (ignoring case, spaces and punctuation), and it refuses a title similar to an existing title or alias (similarity ≥ 0.85) unless `--allow-similar` is passed.
- **By the skill.** Before proposing a new page, `add-knowledge` reads `kb index` and names in the plan the closest existing pages and why the topic is new; string similarity does not catch "Python concurrency models" vs "Конкурентность в Python". The skill passes `--allow-similar` only after the user's yes.
- **Aliases** carry the other names of a topic: abbreviations (`GIL`) and names in the user's language (`Мультипроцессинг`). The skill adds them when it creates or rewrites a page, so search, links and the duplicate check work across languages.

Similarity by embeddings is in the backlog; it is not needed at the current size.

### 5.2. Links

- Links between topics are `[[wiki-links]]` in the page body. Each line in `## Related` says how the topics relate: `- [[Target]] — <relation>`.
- Links are stored once, in the body. The frontmatter `related` list of v1 is not used for topic pages; Obsidian Bases can still filter by `file.links`.
- A link is written only to a page that exists or to one of its `aliases`; `kb` resolves it with the same rules as Obsidian (shortest path, aliases) and refuses unresolved targets.
- Links inside the text (`[[Target]]` in a sentence) are allowed; `## Related` lists the connections worth navigating and reviewing.
- **Unlinked mentions on the written page** (v2.1): when a page is written, the CLI reports titles and aliases of existing pages that the page mentions without a link (§11.4), and the skill turns the useful ones into links on that page. Only the written page changes; the pages it now links to then get the usual back-link suggestion. Mentions of the page on other pages are not searched.
- Typed link vocabularies (`depends_on`, `contrasts_with` as data) are not used: the phrase carries the meaning.

### 5.3. Tags

- Topic pages use Obsidian's native `tags` property (replacing v1 `topics`): lowercase ASCII words joined by `-`, nested at most one level with `/` (`python`, `python/concurrency`, `ml/rag`).
- 1–3 tags per page; more is a validation warning.
- The vocabulary is the set of tags already used in the vault. `kb index --tags` lists it with page counts. A new tag is reported by `kb new` / `kb rewrite`; the skill puts it into the plan for the user's confirmation and otherwise reuses an existing tag.
- Tags serve three purposes: grouping the index, filtering search (`kb search --tag python` matches nested tags), and suggesting links (pages that share a tag but are not linked are reported by the neighbour check, §11.4).
- Tags say what a page is about. Status tags (`to-verify`, `reviewed`) are not used: they are tracking, and every status change would be a commit.
- Source cards (v0.7, §6.9) use the same `tags`, the same rules and the same vocabulary, so a topic and the cards for it share tags and `kb index --tags` counts both.

## 6. Topic page contract (v0.6)

### 6.1. Frontmatter

```yaml
---
type: topic
title: "Python concurrency models"
summary: "How threads, processes and asyncio differ in Python and how to choose between them"
tags:
  - python/concurrency
created: "2026-10-10"
updated: "2026-10-12"
aliases: []
created_by:
  skill: add-knowledge
  skill_version: "0.6.0"
  package_version: "0.6.0"
  skill_ref: "https://github.com/modvala/ms-kb/blob/v0.6.0/src/ms_kb/skills/add-knowledge/SKILL.md"
  date: "2026-10-10"
  agent: claude-code
---
```

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | `topic` |
| `title` | yes | The topic name; the file is `topics/<Title>.md` |
| `summary` | yes | One line, up to about 160 characters; the line `kb index` shows |
| `tags` | yes, 1–3 | §5.3 |
| `created` / `updated` | yes | `"YYYY-MM-DD"`; `created` never changes |
| `aliases` | no | Other names; links to them resolve to this page |
| `created_by` | only when created by a skill | Stamped by the CLI at creation and never changed (§7) |

Not used on topic pages: `updates` (provenance of changes is in Git, §7), `related` (links live in the body), `sources` (sources live in `## Sources`), `topics` (replaced by `tags`).

### 6.2. Sections

Headings are fixed and in English so that the CLI and the skills can find them; the content is in the user's language.

| Section | Content | Who writes it |
|---|---|---|
| `## Summary` | 2–5 sentences: what the topic is and the main conclusion | Agent |
| `## In my words` | The user's own formulation, verbatim; may be empty | **User only** (§11.6) |
| `## Key ideas` | 3–7 bullets worth remembering | Agent |
| `## Details` | Explanation, tables, Mermaid diagrams, examples, comparisons with "as of" dates | Agent |
| `## Open questions` | Unresolved questions; `Verify: …` items; unresolved contradictions with both versions | Agent; neighbour lines through `kb extend` |
| `## Related` | `- [[Page]] — relation` | Agent; neighbour lines through `kb link` |
| `## Sources` | `- <link or title> — what it supports — checked YYYY-MM-DD` | Agent |

Sections may be empty except `## Summary`. The fixed sections keep this order; `kb rewrite` refuses a draft without `## Summary` or with the fixed sections out of order.

**Own sections** (v2.1). The user may add sections of their own in Obsidian (for example `## Code`). They are allowed anywhere after `## In my words`, the validator reports them as a warning, and a rewrite carries them over like any other section: the agent may update them, and lines the user wrote by hand are flagged in the preview (§11.3). Only `## In my words` is protected outright.

### 6.3. Example

```markdown
# Python concurrency models

## Summary
Python offers threads, processes and asyncio. Because of the GIL, threads and asyncio help with waiting on I/O, and processes give real parallelism for CPU-bound pure Python. The choice follows the kind of load.

## In my words
Если программа в основном ждёт — потоки или asyncio, если считает — процессы.

## Key ideas
- The load decides: waiting on I/O or using the CPU.
- asyncio scales to many connections but needs async libraries.
- `ThreadPoolExecutor` and `ProcessPoolExecutor` share an interface.

## Details
| Approach | Module | For | Essence |
|---|---|---|---|
| Threads | `threading` | I/O-bound | Shared memory; the GIL is released on I/O |
| Processes | `multiprocessing` | CPU-bound | Separate interpreters, real parallelism |

## Open questions
- Verify: the default start method on Linux in 3.14 is `forkserver`.

## Related
- [[Global Interpreter Lock]] — why threads do not speed up CPU-bound code
- [[Concurrency vs parallelism]] — the distinction this choice rests on

## Sources
- https://docs.python.org/3/library/threading.html — threads still fit I/O-bound work — checked 2026-10-10
```

### 6.4. Sources, verification and contradictions

- **Mark only what is doubtful.** Established explanations are written as plain text. A claim goes to `## Open questions` as `Verify: …` only when it is doubtful, disputed, or volatile (versions, defaults, dates, limits) and was not checked in the conversation. This replaces v1's rule of marking every claim not backed by an opened source, which filled pages with callouts.
- **Sources are documents that were actually opened.** A statement made in the conversation, by the agent or by the user, is not a source. A source not opened in the conversation is never summarized.
- **A source line may point to a source card** (v0.7): `- [[<Card title>]] — what it supports — checked YYYY-MM-DD`, where the date is the card's `created` unless the source was opened again. The card stands for the source only for what the card says; a claim beyond it needs the source opened.
- **Volatile values** are written with "as of YYYY-MM" or not copied into prose at all.
- **Contradictions are resolved in place.** The new text replaces the old; the reason appears in the diff report and in the commit (`Kb-Reason`). A contradiction that cannot be resolved stays in `## Open questions` with both versions.

### 6.5. Size and splitting

The page budget is about 200 lines (provisional). Above it, `kb` warns in the preview and the skill proposes moving a subtopic to its own page, linked from this one, in a separate run. Compression is not the answer to growth: repeated condensing loses detail.

### 6.6. Visual content

Text — Markdown; processes and architectures — Mermaid in `## Details`; images — files in `attachments/` embedded as `![[file.png]]`, with their meaning explained in text; an overview of a large area — Canvas. Excalidraw is optional. Illustrations of a source are referenced and described on its source card, not copied (§6.9).

### 6.7. The learning profile

`learning_profile.md` is a short file with two sections:

```markdown
## Current directions
- Python concurrency, then distributed task queues

## Preferences
- Explain with code first
- Answer in Russian
```

It has no dated history, no list of known topics (the index replaces it) and no open questions (they are on topic pages). It is user data: `kb init` never recreates it on a vault in use, and changes go through an approved diff (`kb rewrite learning_profile.md`). `kb-recall` reads it on demand; nothing loads it automatically.

### 6.8. Vault structure

```
<vault>/
  topics/              # topic pages: <Title>.md (v0.6)
  sources/             # source cards: <Title>.md (v0.7, §6.9)
  attachments/         # images, PDFs
  templates/           # copies of the package templates for Obsidian's Templates plugin
  learning_profile.md  # directions and preferences (§6.7)
  README.md            # what this folder is
  .gitignore           # Obsidian's churn and kb temporary files
  .git/                # the vault's own history (§12.1)
  concepts/ research/ learning-sessions/ projects/   # v1 types; empty after migration
```

### 6.9. Source card contract (v0.7)

A source card keeps one source the user found worth keeping but does not want to turn into a topic page yet: what it says, the illustrations worth reusing and how it explains its subject, so that when a related topic comes up the source, its illustrations or its style can be used. It is a literature note in the Zettelkasten sense — brief, in the agent's own words, separate from the topic pages — not a copy (`reports/Источники на потом: захват и summary.md`). Topic pages stay the only place of current knowledge; a card is material for them.

**Frontmatter**

```yaml
---
type: source
title: "Designing Data-Intensive Applications"
summary: "Data systems explained through trade-offs; the clearest diagrams of replication lag"
ref: "Martin Kleppmann, O'Reilly, 2017"
author: "Martin Kleppmann"
published: "2017-03-16"
tags:
  - distributed/replication
created: "2026-10-20"
updated: "2026-10-20"
aliases: []
created_by: {…}
---
```

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | `source` |
| `title` | yes | The source's name; the file is `sources/<Title>.md` |
| `summary` | yes | One line, up to about 160 characters: what the source is and why it is worth keeping |
| `url` / `ref` | exactly one | `url` for a web source; `ref` (author, title, edition, ISBN or a local path) for a book, a local PDF or a talk |
| `author`, `published` | no | As given by the source |
| `tags` | yes, 1–3 | The shared vocabulary (§5.3) |
| `created` / `updated` | yes | As on topic pages |
| `aliases` | no | Other names, for example the source's name in the user's language |
| `created_by` | only when created by a skill | Stamped by the CLI (§7) |

There is no status field: whether a card is used is computed (below).

**Sections**, fixed and in English, in this order; the content is in the user's language:

| Section | Content |
|---|---|
| `## Summary` | 3–6 sentences in the agent's own words; required |
| `## Key ideas` | 3–7 bullets |
| `## Illustrations` | One bullet per figure, diagram or example worth reusing: where it is (figure N, page, URL anchor, timestamp), what it shows, why it works; optionally the idea redrawn in Mermaid |
| `## How it explains` | The style: order of the explanation, the running example, analogies, level, what it does well or badly |
| `## Use for` | Topics and questions it may serve: `- [[Topic]] — for …`, or plain text when the page does not exist yet |
| `## Related` | `- [[Page]] — relation` |

Rules:

- **Opened or pasted.** A card is made only from a source the agent opened in the conversation or from text the user pasted (paywalled pages, videos, books). Otherwise no card is created (§6.4).
- **No copy.** No full text; at most one or two short quotes per card, with attribution (provisional limit). Images are referenced and described, never copied into the vault: binary files stay in Git history forever, and copies of other people's images would be pushed to the remote (§12.3). Copying with a `kb attach` command is frozen (roadmap §4.2).
- **One card per source.** A book or a course has one card; later runs add to it with `kb extend` (append-only), for example a line in `## Illustrations` or `## Use for`.
- **Duplicates.** `kb new source` refuses a card with the same normalized URL (lowercase scheme and host, no fragment, no trailing slash, no `utm_*` parameters; provisional), the same title or alias, or a similar title (≥ 0.85) unless `--allow-similar`.
- **"Not used yet" is computed.** A card that no topic page links to is shown as "not used yet" by `kb index --sources` (§10.1). Linking it from a topic page is what makes it used; nothing changes on the card, so no status commit is needed and §5.3 holds.
- **No `## In my words`.** The summary is already in the agent's own words; the user's formulation belongs on topic pages (§6.2).
- The v1 `source` notes (`url` required, `topics`, `updates`) remain readable; the vault holds none, so there is nothing to migrate.

## 7. Provenance and versions

Provenance answers: which skill and which version processed the material, when, with which package, and why it changed.

- **Creation** is stamped by the CLI into `created_by` (skill, skill version, package version, `skill_ref` to `SKILL.md` at the release tag, date, agent when known). It never changes.
- **Every write**, including the creation, is a Git commit whose trailers carry `Kb-Skill`, `Kb-Skill-Version`, `Kb-Version`, `Kb-Agent` (when known) and, from v0.6, `Kb-Reason` (one line on why the page changed). `kb history PATH` shows them.
- From v0.6 `kb` writes no `updates` entries into frontmatter. Existing `updates` blocks on legacy notes are left as they are; migrated pages drop them.
- Selecting changes by skill and version is done over the trailers (`kb history --skill --version`, roadmap stage 7).
- Values that are not known reliably (for example the agent in Codex or Cursor) are not invented.

| Version | What it denotes |
|---|---|
| Package version | A release of the CLI, skills and templates |
| Skill version | The rules of a skill (`metadata.version` in `SKILL.md`) |
| Note schema version | The page contract (`note-schema-v0.md`, then `note-schema-v1.md` in v0.6) |
| Configuration schema version | `schema_version` in `config.toml` |
| Page history | The Git history of the page |
| Document version | The state of these documents |

Provenance makes the rules and the change traceable; it does not make an LLM answer reproducible.

## 8. Source registry

Frozen (US-14). The principle stays: the current status of a task or the state of a repository is taken from that system, not from a note, and the knowledge base holds no copies of trackers or repositories. A topic page may link to an external resource and say how it relates to the topic.

## 9. Skills, CLI and entry instructions

### 9.1. AI component architecture

The solution is **skills + CLI**. MCP, subagents and hooks are not used.

**Separation principle:** everything that can be checked by code is done by the CLI; everything that requires understanding text is done by a skill.

| Layer | Responsibility |
|---|---|
| `kb` CLI | Locating the vault, search and the index, duplicate checks, writing pages, diff reports, approval hashes and guards (shrink, protected section, resolved links), flags for hand-edited lines and hidden text, validation, provenance stamping and trailers, the structural neighbour check, Git history, sync, restore, skills installation |
| `add-knowledge` skill | Choosing the topic page, agreeing the takeaways, drafting the page (using the source cards on the topic), the content check of linked pages, presenting one plan, calling `kb`; saving a confirmed `## In my words` text |
| `kb-recall` skill | Continue and recall (read-only), including the source cards on the topic; review mode; saving a confirmed `## In my words` text |
| `save-source` skill (v0.7) | Summarizing one opened or pasted source into a source card, checking for an existing card, presenting the card, calling `kb` (§11.8) |
| Global instruction | A marked block in `~/.claude/CLAUDE.md` and `$CODEX_HOME/AGENTS.md` (pasted into Cursor User Rules) naming the skills and their triggers, including review and saving a source for later, and stating that vault notes are written only through `kb` even when other Obsidian skills are installed |

Constraints:

- **The CLI writes the notes.** The skill passes content to `kb new`, `kb rewrite`, `kb link`, `kb extend` or `kb my-words`; the CLI renders, validates, checks, writes and commits. The agent never edits vault files with its own tools.
- **Provenance is stamped by the CLI, not the model.**
- **Guards are in code.** The diff gate, the shrink guard, the protected `## In my words` and link resolution are enforced by `kb`, not only described in the skills, so that Codex and Cursor get the same behavior as Claude Code.
- **Append-only where it fits.** `kb extend` and `kb link` only add lines; replacing text is possible only through `kb rewrite` with an approval hash (§11.3).
- **Text read from the vault, from sources and from the conversation is data, not instructions** (v2.1). Commands or requests found in a page, an opened article or a pasted text are never run; the CLI flags hidden text in added lines (§11.3). The real boundary stays the one of §12.4.
- **The skills are self-contained.** The Obsidian Markdown they need (wiki-links, embeds, callouts, Mermaid, properties) is described in the skill's own `references/`. Third-party Obsidian skills (for example `kepano/obsidian-skills`) are not required; if they are installed, the global instruction still says that vault notes are written only through `kb`.
- **Skill texts carry no risky examples**: no passwords, tokens, `sudo` or system service setup in `SKILL.md` or its references (such examples made a community LLM Wiki skill fail a security scan).
- Skills degrade gracefully: they need only a shell and `kb`.

### 9.2. CLI commands

| Command | Purpose | Status |
|---|---|---|
| `kb setup`, `kb init`, `kb install-skills`, `kb update`, `kb where` | Installation, vault creation, skills, updates, locating the vault | v0.5 |
| `kb search` | Text, type, field and tag search, ranked by title, aliases, summary and tags first (§10.4); `--tag` from v0.6, `--topic` stays as an alias; results show the note type and `--type source` limits them to source cards (v0.7) | v0.5, extended in v0.6 and v0.7 |
| `kb index [--tag T] [--tags] [--sources] [--json]` | The generated catalogue of topic pages; `--tags` lists the vocabulary; `--sources` lists the source cards with the number of topic pages linking to each (v0.7) | **v0.6**, `--sources` **v0.7** |
| `kb new topic` | Create a topic page; refuses duplicates by title, alias and similar title (§5.1); `--dry-run` prints the page and the neighbour check | v0.5, extended in v0.6 |
| `kb new source` | Create a source card (§6.9) with `--summary`, `--tag`, `--alias`, `--url` / `--ref`, `--author`, `--published`; refuses duplicates by normalized URL, title, alias and similar title | v0.5, changed in **v0.7** |
| `kb rewrite PATH` | Replace a page's content through the diff gate (§11.3) | **v0.6** |
| `kb link SRC TARGET --why TEXT` | Add one line to `## Related` of SRC (§11.5) | **v0.6** |
| `kb extend PATH` | Append lines to sections (append-only); used for one line in a neighbour's `## Open questions`; `--reason` replaces `--summary` | v0.5, changed in v0.6 |
| `kb my-words PATH` | Replace `## In my words` with the user's verbatim text (§11.6) | **v0.6** |
| `kb validate`, `kb doctor` | Schema, integrity, links, freshness | v0.5 |
| `kb history`, `kb restore`, `kb sync` | History, restore, push (§12) | v0.5 |

Option names are provisional. `kb restore` and `kb sync` remain user commands that skills never run.

## 10. Reading: index, recall and review

### 10.1. The index

`kb index` prints the catalogue of topic pages grouped by tag (nested tags as a tree), one line per page: `[[Title]] — summary (N open questions)`. `--tag T` limits it to an area, `--json` gives a machine-readable form, `--tags` lists the tag vocabulary with page counts.

**Source cards** (v0.7) are listed separately, so topics do not drown among sources: `kb index --sources [--tag T]` prints the cards grouped by tag, one line each: `[[Title]] — summary — used by N topics`, or `— not used yet` when no topic page links to the card. The count comes from the link index; nothing is stored on the card. Plain `kb index` lists only topic pages.

The index is generated from frontmatter on every call, so it never drifts from the pages. It is not written into the vault: a committed `index.md` linking every page would turn the graph into a star around one node and make agents walk through it. A regenerable Obsidian Bases view for the human may be added later (roadmap backlog).

### 10.2. `kb-recall`: continue and recall

1. `kb where` (on failure: say the base is unavailable and answer from the conversation only).
2. Read the profile (directions, preferences) when the request needs personal context.
3. `kb index` (or `--tag`) and `kb search` with the topic and its synonyms; from v0.7 also `kb index --sources --tag <tag>` and `kb search --type source` for source cards on the topic. "Nothing found" is said only after both came back empty.
4. Read the topic page and, if needed, up to about three linked pages. Never the whole vault.
5. Answer from the user's current understanding: `## In my words` and `## Open questions` first, then the rest. Separate what comes from the page from new explanation. Name the source cards on the topic and what they offer (an illustration, a way of explaining); read a card when the user wants it.
6. Write nothing, except a `## In my words` text the user confirmed (§11.6).

| Request | What is read |
|---|---|
| "Let's continue X" | Profile, page of X, its open questions |
| "What do I know about X?" | Index and search, page of X |
| "Which topics do I have in ML?" | `kb index --tag ml` |
| "Which sources did I save on RAG?" | `kb index --sources --tag ml/rag`, `kb search "RAG" --type source` |
| "What is 15 × 18?" | Nothing |

### 10.3. Review mode

Triggered by "let's review X", "quiz me on X", "проверь меня по X". Grounded in the testing effect (retrieval with feedback beats rereading), the generation effect and interleaving (research report, 2026-10-12).

1. Find the page of X. Do not show it.
2. Ask the user to tell what they remember about X.
3. Compare with `## Key ideas` and `## Details`: what matched, what is missing, what is wrong. **The page is the reference.** If the agent's own knowledge disagrees with the page, it says so as a finding and suggests recording it as a `Verify:` item through `add-knowledge`; it does not correct the user against the page on the fly.
4. Ask 2–4 "why / what if / when not" questions built from the key ideas and open questions; give a hint before the answer. If the user names an angle ("quiz me on when not to use it"), the questions follow it: generated questions are better when the learner sets the angle.
5. Ask 1–2 questions that mix X with a page from its `## Related` (interleaving needs those links).
6. List the gaps in the conversation. Do not write them; the user may run `add-knowledge` to record them.
7. Invite the user to put the topic in two or three sentences of their own. Show the exact text; after an explicit yes, save it with `kb my-words` (§11.6).

No review schedule or state is stored. If spaced repetition is ever wanted, its state lives outside the vault, next to `vault-<kb>.json`, so that reviews do not create commits.

`kb-recall` remains read-only for everything the agent formulates. The single exception, `kb my-words`, writes only the user's own verbatim text after an explicit yes, so no agent claim can enter the base through review.

### 10.4. Search (v2.1)

Search improves in steps, each taken only when the previous one stops being enough:

1. **v0.6:** `kb search` ranks matches in the title and `aliases` first, then `summary` and tags, then the body. With aliases in the user's language this is the main way to find a topic across Russian and English. No index is kept.
2. **Later:** a rebuildable SQLite FTS5 cache outside the vault, next to `vault-<kb>.json`, for faster and better-ranked full-text search on hundreds of pages. It is derived state and is never committed.
3. **Later, optional:** qmd (hybrid keyword and vector search with local models, about 2 GB) as a backend behind `kb search`, with a multilingual embedding model; never a required dependency.

Source cards (v0.7) are ranked by the same rules; results show the note type, so a topic page and a card on the same subject are told apart, and `--type source` or `--type topic` narrows the search.

Whatever the backend, skills call only `kb search` and `kb index`.

## 11. Writing

### 11.1. Logical operations

| Operation | Meaning | Command |
|---|---|---|
| Search | Find pages by text, tag, metadata | `kb search`, `kb index` |
| Read | Read a page | file read |
| Create | Create a topic page or a source card (v0.7) | `kb new topic`, `kb new source` |
| Rewrite | Replace a page's content through the diff gate | `kb rewrite` |
| Add a line | Append a link or an open question to a neighbour | `kb link`, `kb extend` |
| Save own words | Replace `## In my words` with the user's text | `kb my-words` |
| Init, sync, restore | Vault creation, push, restore (user commands) | `kb init`, `kb sync`, `kb restore` |

There is no delete, move or rename command. Deleting and moving pages is done by the user in Obsidian; `kb doctor` detects it (§12.4).

### 11.2. `add-knowledge`: one research session → one topic page

**Write policy:** writing happens only when the user invokes the skill; the invocation is permission to prepare a change, and the plan's yes is permission to write it.

1. **Check.** `kb where`; on a version mismatch, ask before writing.
2. **Find the topic.** `kb index` and `kb search` with synonyms and aliases. Outcome: update page X, create a new page, or **nothing new to save** — then write nothing and say so. For a new page, note the closest existing pages and why the topic is new (§5.1). From v0.7 also find the source cards on the topic (`kb search --type source`, `kb index --sources --tag`).
3. **One page.** If the conversation covered several topics, ask which one to save, or do separate runs.
4. **Takeaways.** Show the 3–5 main takeaways and ask what to stress or drop, unless the user already said what to save.
5. **Draft.** Write the full page by the template (§6.2). For an existing page, change the sections the session concerns and keep the others exactly as they are; keep lines the user wrote by hand unless the session shows they are wrong. Do not touch `## In my words`. Apply §6.4: mark only doubtful claims, list opened sources with dates, resolve contradictions in place. Add aliases for abbreviations and names in the user's language. Use the relevant source cards: their `## Illustrations` and `## How it explains` may shape the examples and the order of the explanation, and the cards used are listed in `## Sources` as card lines (§6.4).
6. **Internal preview.** `kb rewrite --dry-run --sections <the sections the draft changes>` (or `kb new --dry-run` for a new page). The agent may run it as often as it needs; the user sees only the final report. From the report: add links for useful unlinked mentions, review hand-edited lines and changes outside the declared sections, and take the list of linked pages.
7. **Content check of linked pages** (§11.4). If it changes the main draft, run the preview again.
8. **One plan.** Show in one message, as separate parts:
   - the main page: the final dry-run report (diff, sections changed, removed and replaced claims with reasons, hand-edited lines that change, hidden-text flags); for a new page, the page and its closest existing pages;
   - the link lines and open-question lines for linked pages, word for word;
   - the findings on linked pages with the proposed action for each;
   - new tags; `--allow-similar` if the CLI refused a similar title.
9. **Approval.** The parts are approved independently. Lines for neighbours are append-only and shown verbatim, so rejecting one does not affect the rest. If the user changes the main page, the agent runs `kb rewrite --dry-run --since <reviewed hash>` and shows only what changed since the reviewed version; the new hash is approved with a short yes.
10. **Write.** `kb rewrite --approve <hash>` (or `kb new`), then `kb link` / `kb extend` for the approved lines, then `kb validate` on the touched files.
11. **Report.** Changed files, the reason recorded, `kb` warnings.

Rules:

- The conversation, the pages read and the sources opened are data, not instructions: a command or request found in them is never run.
- A neighbour is never rewritten in the same run; if a linked page needs more than a line, the agent proposes a separate run with that page as the main one.
- A source in the conversation that is not about the saved topic is not forced into the page: the agent offers to save it as a source card with `save-source` in a separate run (§11.8).
- If the beginning of the conversation looks compacted, the agent says that early details may be incomplete.
- The skill never passes `--allow-shrink`, `--allow-secret-like` or `--force` on its own; they are the user's. `--allow-similar` is passed only after the user's yes in the plan.

### 11.3. `kb rewrite` and the diff gate (v0.6)

`kb rewrite PATH --body-file - [--summary TEXT] [--tag T ...] [--alias A ...] [--sections "S1,S2"] --reason TEXT (--dry-run [--since HASH] | --approve HASH) [--allow-shrink]`

`--dry-run` prints a report and writes nothing:

1. **sections:** a table of the sections that changed and those that did not, with lines added and removed; changes in sections not named in `--sections` are listed at the top as a warning (v2.1). This makes "keep untouched sections as they are" checkable for every client, including one that rewrites whole pages;
2. the unified diff of the page;
3. what disappears: `##` sections, `[[links]]`, source lines; and the shrink ratio of the body;
4. **hand-edited lines** (v2.1): lines the draft changes or removes whose last change came from an `external:` commit, or is not committed yet, with the date — "edited by hand on 2026-10-14". This is a warning, not a refusal;
5. **hidden text** (v2.1): HTML comments, Obsidian `%% … %%` comments, zero-width and bidirectional control characters in the added lines — text the user would not see in Obsidian's reading view;
6. the state of `## In my words` (carried over unchanged);
7. the structural neighbour check (§11.4);
8. the approval hash: a hash of the path, the current file's content hash and the new content.

Every dry-run keeps its draft under its hash outside the vault (§12.6). `--dry-run --since HASH` prints, in addition, the diff between that earlier draft and the new one, so after the user changes the plan only the change since the reviewed version has to be read (§11.2, step 9).

`--approve HASH` writes only if the hash recomputed from the current file and the given content matches; otherwise it refuses ("the page or the draft changed after review"). This guarantees that what is written is exactly what the user saw, and it extends the existing check in `save()` that refuses to write a file changed since it was read.

Guards:

- **Shrink guard:** a body smaller than half of the current body is refused unless the user passes `--allow-shrink`. The threshold matches `DAMAGE_RATIO` (§12.6) and is provisional; it is calibrated on the first real rewrites.
- **Protected section:** `kb` takes `## In my words` from the current file and puts it into the new content; a draft whose `## In my words` differs is refused.
- **Schema:** the result is validated (§6.1, §6.2); `created` and `created_by` are preserved; `updated` is set.
- **Secrets and the lock:** as for every write (§12.1, §12.6).

The write goes through the same path as every write (`_finish`): lock, commit of outside edits, write, commit `kb: rewrite <path>` with provenance trailers and `Kb-Reason`, manifest update. Because the manifest is refreshed, an approved rewrite is never reported as damage; a large shrink made outside `kb` still is (§12.4).

`kb rewrite learning_profile.md` uses the same gate for the profile (no provenance block, the reason goes to the commit).

### 11.4. Checking linked pages

The check covers the page being written and the pages it links to — one step, no neighbours of neighbours. Pages that are not linked are not read or changed.

**Structural part (CLI, in every `--dry-run` of `kb new` and `kb rewrite`):**

- outbound links that do not resolve;
- **unlinked mentions** (v2.1): titles and aliases of existing pages that this page mentions without a link — whole-word, case-insensitive matches outside headings, code and existing links, at least three characters, the longest match first — proposed as links on this page;
- linked pages that do not link back — candidates for `kb link`;
- links from other pages to headings that the rewrite removes (`[[Page#Heading]]`), found from the link index without reading those pages in the conversation;
- pages that share a tag with this page but are not linked (a few, as suggestions);
- new tags; the page length against the budget.

**Content part (skill):**

- read each linked page — at most about five, those the session's facts concern first; list the rest without reading them;
- compare with the outcome of the session: contradictions, outdated facts (versions, APIs), points the session refines;
- put each finding into the plan with one of three actions for the user to choose: leave it; add one line to the neighbour's `## Open questions` (`kb extend`), for example `- Verify: … — differs from [[Python concurrency models]]`; or update the neighbour in a separate run.

Limit: the same model checks what it may have written, so it finds disagreements between pages better than errors both pages share. Where a claim has a source, the agent may open the source; otherwise the finding stays a `Verify:` item, not a correction.

The read-only structural checks of the whole vault in `kb doctor` (deleted, damaged, moved notes, links that stopped resolving) stay as they are: they change nothing and use no model.

### 11.5. Targeted edits of neighbours

- `kb link SRC TARGET --why TEXT` appends `- [[TARGET]] — TEXT` to `## Related` of SRC. TARGET must resolve (a page or an alias); a link to the same target already in the section is skipped. Only that line and `updated` change; the commit carries the trailers.
- `kb extend PATH --body-file -` appends lines to named sections and stays append-only; for topic pages the skills use it only for `## Open questions` lines and, from `save-source`, one `## Sources` line pointing to a new card (§11.8); for source cards, to add lines to their sections. From v0.6 it writes no `updates` entry; `--reason` (formerly `--summary`) goes to the commit.

### 11.6. Writing `## In my words`

`kb my-words PATH --body-file -` replaces the content of `## In my words` with the given text exactly as given (only the trailing newline is normalized) and commits `kb: my-words <path>`. It refuses if the page does not exist.

Both skills may call it (v2.1): `kb-recall` at the end of a review, `add-knowledge` when the user says "put this in my words: …" during or after a session. The rules are the same.

Rules for the skills:

- The text is the user's, verbatim: no rewording, no fixing of typos, no translation, no additions.
- Before calling the command, the agent shows the exact text and the page, and calls it only after an explicit yes.
- The agent never drafts the text for the user. If the user's formulation contradicts the page, the agent says so in the conversation and may propose an open question; the section is saved as the user wants it.

The user may also edit the section in Obsidian at any time; `kb` commits it as an outside edit.

### 11.7. Migration of the existing notes (v0.6)

The vault holds six v1 notes on one topic (three `concept`, three `learning-session`) and a v1 profile. Migration is a one-off, done with the agent, without a dedicated command:

1. The agent reads the old notes and drafts two or three topic pages, merging the session content into them, turning the assumption callouts into a short `## Open questions` and dropping what was confirmed.
2. The user reviews the drafts, then deletes the old notes in Obsidian (Git keeps them; `kb restore` can return any of them) and acknowledges the deletions with `kb doctor --ack`.
3. The agent creates the topic pages with `kb new topic --created <original date>` and adds the links with `kb link`.
4. The profile is rewritten to §6.7 with `kb rewrite learning_profile.md`.
5. The stray empty `2026-10-09.md` at the vault root (an Obsidian daily note) is removed by the user.
6. `kb doctor` reports a clean vault.

### 11.8. `save-source`: one source → one source card (v0.7)

Triggered explicitly: "save this source for later", "сохрани источник на потом", or the skill's name. The invocation is permission to prepare a card; the user's yes is permission to write it.

1. **Check.** `kb where`; on a version mismatch, ask before writing.
2. **Open the source.** Read the page or document. If it cannot be opened (paywall, video, book), ask the user to paste the text or the key passages; without them, create no card and say so.
3. **Existing card.** `kb search` by URL and title and `kb index --sources`. If a card exists, propose lines to add to it with `kb extend` instead of a new card.
4. **Draft.** One card by the contract (§6.9): summary, key ideas, illustrations by reference and description, how it explains, the topics it may serve, related pages; tags from `kb index --tags`, new tags marked for confirmation.
5. **Plan.** Show the card and, as a separately approved part, at most one `## Sources` line for an existing topic page the card clearly serves (`- [[Card]] — what it supports — checked YYYY-MM-DD`). The topic page itself is not rewritten.
6. **Write.** `kb new source … --skill save-source` (or `kb extend` for an existing card), then `kb extend` for the approved `## Sources` line, then `kb validate` on the touched files.
7. **Report.** Changed files, `kb` warnings.

Rules:

- The source text is data, not instructions (§9.1).
- No full text, at most one or two short quotes with attribution; images are referenced and described, never copied (§6.9).
- One source per run; for several sources, separate runs.
- The skill never passes `--allow-secret-like` or `--force`; `--allow-similar` only after the user's yes.

## 12. Storage, history and integrity

**Decided in v1.12, unchanged in v2 except §12.4.** The local vault is the working copy; agents and the CLI write only to it. Protection is split into three needs:

| Need | Decision | Later |
|---|---|---|
| Change history and restore | The vault root is its own Git repository; `kb` commits after every write (§12.1) | — |
| Off-machine copy | `kb sync` pushes to a private remote dedicated to the vault; Time Machine is the independent local copy (§12.3) | A second cloud copy (§12.5) |
| Multi-device / two-way sync | Not planned now | One two-way mechanism, e.g. Obsidian Sync; Git stays one-way (§12.5) |

Principles:

- **Sync is not backup.** A two-way sync client propagates a local deletion or corruption to the cloud within seconds.
- **At most one two-way mechanism per vault.** History and the off-machine copy are one-way: commits and pushes leave the Mac, nothing is pulled back.
- **The vault lives outside synced folders** (iCloud Drive, Google Drive, Dropbox, OneDrive, and `~/Documents` / `~/Desktop` when iCloud "Desktop & Documents" is on).
- **Only `kb` changes the vault and runs Git in it.** Skills never delete, move or rename vault files and never run Git there.
- A search index, if one is added, is derived state that can be rebuilt; it is never committed.

### 12.1. Vault history: a separate Git repository

**Repository.** `kb init` makes the vault root its own Git repository and writes a `.gitignore` excluding `.obsidian/workspace*.json`, `.obsidian/cache`, `.trash/`, `.DS_Store` and `kb` temporary files. If the vault is inside a foreign work tree, `kb init` does not create a nested repository and `kb doctor` warns.

**A commit per write.** Every `kb` write (`new`, `rewrite`, `link`, `extend`, `my-words`, `restore`):

1. commits changes made outside `kb` first, separately (`external: N files changed outside kb`), so a half-finished user edit never ends up in an agent's commit;
2. writes and commits **only its own paths**, with the subject `kb: <operation> <path>` and trailers `Kb-Skill`, `Kb-Skill-Version`, `Kb-Version`, `Kb-Agent` (when known) and `Kb-Reason` (v0.6).

The history is both the page history (US-13) and the provenance log (US-12). Since `kb` has no delete command, any deletion in the history happened outside `kb`.

**Edits outside `kb`** when `kb` is not called are committed by `kb sync` on its schedule (§12.3).

**Implementation rules:** Git through `subprocess`; **Git never blocks a note write** (a missing `git` or a failed commit is a warning, and the state is marked stale); `.git/index.lock` held by another process is retried, never deleted; `kb` serializes its own runs with a lock file; files over about 50 MB are not committed; content with key-like strings is refused (§12.6).

**Reading history.** `kb history [PATH]` wraps `git log`, including deleted notes; `kb restore` returns a note from history (§12.4).

### 12.2. ChatGPT — out of scope

ChatGPT is not a client. Notes on possible future paths (the ChatGPT desktop app working with local folders, a cloud inbox, a custom MCP) are kept in [design v1.13 §12.2](personal-knowledge-design-v1.md).

### 12.3. Off-machine copy: push to a private remote

**Why.** Local Git history does not survive deleting the vault folder with `.git` or losing the disk; Time Machine's local snapshots live on the same disk. The off-machine copy covers loss of the computer.

**Mechanism.** `kb sync` commits outside edits (§12.1) and runs `git push` to the configured remote: never with `--force` (a rejected push is reported), non-interactively (`GIT_TERMINAL_PROMPT=0`, SSH `BatchMode=yes`). Authentication is the user's (an SSH key or a deploy key); `kb` stores no credentials.

**Triggering.** Pushes never run synchronously with a write. A LaunchAgent installed by `kb setup` with the user's consent runs `kb sync` hourly (`StartCalendarInterval` plus `RunAtLoad`); `kb sync` can also be run by hand. Without a network, commits accumulate and the next run pushes them.

**Host choice is the user's.** Any Git host works. On GitHub Free, protected branches are not available for private repositories, so a force-push cannot be forbidden; this is accepted because the remote is one of three copies (local `.git`, Time Machine, the remote). Stronger options (GitLab Free protected branches, GitHub Pro without bypass, a bare repository with `receive.denyNonFastForwards`) are documented, not required.

**Privacy.** The host sees the plaintext. Encryption on top of Git is not used; if privacy becomes more important, the path is an encrypted snapshot backup (§12.5).

**Time Machine** is the recommended independent local copy; `kb doctor` shows the last backup time as information.

### 12.4. Data integrity and the trust boundary (revised in v2)

Files fall into two classes:

| Class | Files | If deleted |
|---|---|---|
| Regenerable | Folders, `templates/*.md`, `README.md`, `.gitignore` | `kb doctor` reports them; `kb init` recreates them |
| User data | All notes and `learning_profile.md` | Restore only from history or a backup |

**The trust boundary** is the OS sandbox, `kb` itself and copies the agent cannot reach — not the skill text. In v1 part of the argument was that `kb` could only append. In v2 `kb` can replace a page, so the boundary is restated:

- `kb` has no delete, move or rename command;
- `kb link`, `kb extend` only add lines;
- `kb rewrite` replaces a page only with an approval hash of the exact diff the user saw, refuses to shrink a page below half without the user's `--allow-shrink`, never changes `## In my words`, and flags lines written by hand and hidden text before the user approves;
- `kb my-words` writes only the text passed to it, into one section;
- every write is a commit, and the history and the remote are out of the agent's reach.

The protection therefore moves from "code that cannot remove text" to "a human who approves a precise diff". This makes the quality of the `kb rewrite --dry-run` report — what disappears, how much the page shrinks, which links are lost — a safety property, designed with the same care as the secret check.

**Prevent.**

- Skills forbid deleting, moving or renaming vault files, any change outside `kb` and running Git in the vault. This is guidance, not protection.
- Text permission rules are not a security boundary. The documentation recommends: keep the vault outside every agent's working directories; in Claude Code deny `Edit(<vault>/**)`, add the vault to the sandbox's `denyWrite` and let only `kb` run outside the sandbox; in Codex use `workspace-write` without the vault in `writable_roots`; in Cursor enable File-Deletion and External-File Protection. `kb setup` does not change these settings silently.

**Detect.**

- A **manifest** of notes outside the vault (path → SHA-256, size, mtime, title, last writer), updated after every `kb` write; notes created outside `kb` are added when first seen.
- `kb doctor` / `kb validate` classify differences: *changed outside `kb`* (normal), *moved*, *deleted* (reported until acknowledged with `kb doctor --ack PATH`), *damaged* (empty, frontmatter lost, or shrunk below half of the manifest size by an outside edit).
- **Broken wiki-links**: a link that used to resolve and no longer does is an alarm.
- **Freshness**: `kb doctor` warns when `git` is missing, when commits are unpushed for over 24 hours, when the LaunchAgent is not loaded.

**Recover.** `kb restore PATH [--at REV]` returns a note from history and never overwrites silently: a free path gets the note back; an occupied path gets `<name>.restored-<timestamp>.md` and a diff; `--force` overwrites after saving the current version; `--dry-run` shows what would happen. If the local repository is lost, the vault is cloned from the remote.

### 12.5. Later: other cloud copies and multi-device sync

- **A second cloud copy**, independent of the Git host: an encrypted snapshot backup (`restic` or Kopia, e.g. to Backblaze B2), or Google Drive via `rclone --backup-dir` (heavier to set up since 2026).
- **Multi-device and phone access**: one two-way mechanism (Obsidian Sync for iOS, Syncthing for Android); Git stays one-way history on the Mac. Conflict rules are decided then.

### 12.6. Implementation decisions

- **Secret patterns.** AWS keys, GitHub tokens, `sk-…` API keys, Stripe live keys, Slack tokens, Google API keys, private key blocks; `gitleaks stdin` in addition when installed. Only the lines a write adds are checked (for `kb rewrite`: the lines the diff adds).
- **Override.** `--allow-secret-like` is for the user only; skills never pass it.
- **Outside edits with a secret or over 50 MB** are left out of the `external:` commit and reported.
- **Non-interactive Git.** `GIT_TERMINAL_PROMPT=0`, SSH `BatchMode=yes`, `commit.gpgsign=false`, `--no-verify`; commits fall back to `kb <kb@localhost>` without a configured `user.email`.
- **State files** next to `installed.toml`: `vault-<kb>.json` and `<kb>.lock`; the LaunchAgent in `installed.toml` under `[schedule]`.
- **Damaged vs changed.** `DAMAGE_RATIO = 0.5`: a note is damaged when it is empty, its frontmatter no longer parses or disappeared, or it shrank below half of the manifest size outside `kb`. `kb rewrite` refreshes the manifest, so an approved rewrite is never damage.
- **Freshness.** Unpushed commits older than 24 hours, an unloaded LaunchAgent, a failed last Git operation.
- **Version check before writing.** `kb where` warns when the installed skills come from another package version; `add-knowledge` then asks before writing.
- **Approval hash (v0.6).** Provisional: SHA-256 over the vault-relative path, the SHA-256 of the current file and the new content; the first 12 hex characters are shown and accepted.
- **Drafts of dry-runs (v0.6).** Kept under their hash in `drafts-<kb>/` next to `vault-<kb>.json`, outside the vault, for `--since`; removed after the write and pruned after 7 days.
- **Hand-edited lines (v0.6).** Found with `git blame --porcelain` on the current file: a line whose last commit subject starts with `external:`, or that is not committed yet, counts as written by hand. Matching is by line, so a line the draft moves or rewords may be missed; the flag is a warning. If the warnings prove too weak, explicit "keep" markers are the backlog option.
- **Hidden text (v0.6).** Checked in the lines every write adds (`new`, `rewrite`, `link`, `extend`, `my-words`): `<!-- … -->`, `%% … %%`, U+200B–U+200F, U+202A–U+202E, U+2060–U+2064, U+2066–U+2069, U+FEFF. A warning in the dry-run report and in the command output, not a refusal.

## 13. Versions, CI and maintenance

A release has a version and a Git tag; the package version, skill versions, the note schema version and the configuration schema version are distinct. CI (Ubuntu and macOS) runs the tests, builds the wheel, installs it with `uv tool install` and smoke-tests the CLI on a temporary vault with a local bare remote; from v0.6 the smoke test covers `kb new topic` (including a refused duplicate), `kb rewrite` (dry-run, `--since`, approve, shrink refusal, protected section, a hand-edited line flagged), `kb link`, `kb my-words` and `kb index`; from v0.7 it covers `kb new source` (including a duplicate refused by URL) and `kb index --sources`. Updating the package never overwrites user notes; changes to the note schema or the configuration come with a migration path. CD is not required.

## 14. Open decisions and boundaries

| Area | Settled | Still open |
|---|---|---|
| Content model | Topic pages; fixed sections plus the user's own; `## In my words` second; tags 1–3, one nesting level; duplicates refused by title, alias and similar title, plus the skill's check against the index; source cards (v0.7) with `url` or `ref`, illustrations by reference, one card per source, "not used yet" computed from links | Page budget and summary length (calibrate); embedding-based duplicate detection (backlog); the quote limit and URL normalization of source cards; a Web Clipper template (backlog) |
| Writing | One page per run, approved diff with a section summary, hand-edited lines and hidden text flagged, independent approval of the plan's parts, neighbours get only lines, CLI guards | Shrink threshold (calibrate); "keep" markers if the hand-edit flags prove too weak |
| Checks | The written page and its linked pages only; unlinked mentions on the written page; structural part in the CLI, content part in the skill | — |
| Reading | Generated index plus search; profile on demand; review mode without stored state, the page as the reference | Whether spaced repetition is wanted |
| Search | Ranked text, alias, tag and metadata search without an index (§10.4) | When to add the FTS5 cache and qmd |
| Provenance | `created_by` at creation; trailers on every commit | Trailer queries in stage 7 |
| Delivery | `uv tool install` + `kb setup`, `kb update`, skills copied into clients | Release process, CD |
| History and copy | Own Git repository, push to a private remote hourly, Time Machine | Git host; second copy and multi-device later |
| Clients | Claude Code checked hands-on | Codex and Cursor checks; Cursor duplicates; agent detection |

### 14.1. Not doing

| What | Why |
|---|---|
| `log.md` | Git with trailers is the log; no per-day history is wanted |
| A raw-source folder and drift checks of sources | The source is the conversation or an opened document; copies of articles are excluded; a source card holds a summary, not a copy (§6.9) |
| A "to read" / "processed" status or an inbox for sources | Tracking and a queue that needs moving or deleting notes; "not used yet" is computed from links (§6.9) |
| An `index.md` written by the model or committed | It drifts from the pages and turns the graph into a star; the CLI generates the index |
| Automatic saving of answers from `kb-recall` | The main loop that turns an error into a "fact" |
| Edits cascading across many pages | One rewritten page per run keeps review possible |
| Checking the whole vault with the model | Checks are local to the written page and its links |
| Claim registries, numeric confidence, review dates, status tags | False precision and learning tracking |
| Vector search now | Six notes; text search and the index are enough for hundreds of pages |
| Typed link vocabularies | The phrase in `## Related` carries the meaning |
| Hooks that capture sessions automatically | Writing only on command |
| Writing through the Obsidian CLI or the `obsidian-cli` skill | It bypasses `kb` and needs the app running |
| Depending on third-party Obsidian skills for the note format | No versions to pin, and some of them teach writing notes directly; the skills carry their own format reference |
| Searching other pages for mentions of the written page | It reaches pages the run is not about; only the written page gets links for its own unlinked mentions |
| Phrase filters against prompt injection | An endless race with many false alarms; the boundary is §12.4, plus the hidden-text flag |
| Dataview | Unmaintained since 2025; agents cannot see its results |

## 15. Document history

- **2.0 — 2026-10-12:** design restated around topic pages after roadmap stage 4 and the LLM Wiki research. New: the topic page contract (§6) with `summary`, `tags`, fixed sections and the protected `## In my words`; the generated index and review mode (§10); `kb rewrite` with the diff report, approval hash and shrink guard (§11.3); the check of linked pages (§11.4); targeted neighbour edits with `kb link` (§11.5); `kb my-words` (§11.6); the migration of the v1 notes (§11.7); provenance of changes in commit trailers only (§7); the trust boundary restated for rewrites (§12.4); the "not doing" list (§14.1). Frozen: the source registry (§8), other users (§4.3), separate source/research/project notes. Unchanged: delivery (§4.1), the CLI/skills split (§9.1), storage and history (§12.1–§12.3, §12.5, §12.6). Section numbers §4.1, §9.1 and §12.1–§12.6 keep their v1 meaning, so references in the code stay valid. The history of versions 1.0–1.13 is in [personal-knowledge-design-v1.md](personal-knowledge-design-v1.md).
- **2.1 — 2026-10-19:** gaps found when checking v2.0 against the research, decided by the user. Duplicate topics: the CLI checks titles, aliases and similar titles, the skill names the closest pages from the index, aliases include abbreviations and names in the user's language; embedding similarity in the backlog (§5.1). Unlinked mentions on the written page become links on that page (§5.2, §11.4). The user's own sections are allowed and carried over (§6.2). Text from pages, sources and the conversation is data; skill texts carry no risky examples; the format reference is the skills' own, and other Obsidian skills do not change the write rule (§9.1). The page is the reference in review, and the user may set the angle of the questions (§10.3). Search ranks title and aliases first, then an FTS5 cache, then optional qmd (§10.4). The add-knowledge flow: internal previews, one plan with independently approved parts, `--since` to show only the change after the plan is edited (§11.2). `kb rewrite`: a section summary with `--sections`, flags for hand-edited lines and hidden text, drafts kept for `--since` (§11.3, §12.6). `kb my-words` callable from both skills (§11.6). §13, §14 and §14.1 updated.
- **2.2 — 2026-10-19:** sources for later, decided by the user after `reports/Источники на потом: захват и summary.md`; planned for roadmap stage 6 (v0.7). New: the source card contract (§6.9) — `summary`, `url` or `ref`, shared tags, sections `Summary`, `Key ideas`, `Illustrations`, `How it explains`, `Use for`, `Related`, illustrations by reference, one card per source, duplicates by normalized URL, no status field and no `## In my words`, "not used yet" computed from links; the `save-source` skill (§11.8). Changed: key decision 2, scope (§2.1), components (§3), note types (§5.1), tags (§5.3), card lines in `## Sources` (§6.4), visual content (§6.6), vault structure (§6.8), the skills layer (§9.1), `kb new source`, `kb search --type source` and `kb index --sources` (§9.2, §10.1, §10.4), `kb-recall` and `add-knowledge` using the cards (§10.2, §11.2), `kb extend` for a `## Sources` line (§11.5), CI (§13), §14 and §14.1. Trailer queries move to roadmap stage 7.
