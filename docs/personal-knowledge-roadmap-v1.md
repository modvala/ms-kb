---
title: "Personal Knowledge System — Roadmap"
document_version: "1.3"
created: "2026-10-09"
language: en
status: draft
requirements_ref: "personal-knowledge-user-stories-v1.md"
requirements_version: "1.8"
design_ref: "personal-knowledge-design-v1.md"
design_version: "1.7"
---

# Personal Knowledge System — Roadmap v1.3

## 1. Purpose

The roadmap breaks the requirements (user stories v1.7) and the design (v1.6) into sequential development stages. Each stage ends with a working result that can actually be used. No deadlines are given: the project is run by one person, and order matters more than dates.

**MVP goal:** after a long learning conversation in Claude Code, Codex or Cursor, invoke `add-knowledge` and get tidy notes in the local knowledge base; in the next conversation, use `kb-recall` to continue with what has already been learned taken into account.

**MVP scope** (from "MVP decisions"): one user; Python + `uv`; Claude Code, Codex and Cursor clients; one new knowledge base created from scratch; writes only on explicit skill invocation; local vault, copied to Google Drive by a separate command; ChatGPT, MCP, subagents, hooks, multiple knowledge bases and mobile access come after the MVP.

## 2. Stage overview

| Stage | Version | Status | Result | Key US |
|---|---|---|---|---|
| 0. Skeleton and checks | v0.1 | ✅ Done | Package installs from GitHub, `kb --version` works; skills directories verified in all three clients; note schema approved | US-04, US-17, US-23 |
| 1. Knowledge base | v0.2 | ✅ Done | `kb init` / `kb setup` create the vault, configuration and profile; the vault opens in Obsidian | US-01, US-16, US-19 |
| 2. Writing: `add-knowledge` | v0.3 | ⬜ Not done | Conversation outcomes are saved to the knowledge base in all three clients, with provenance and without duplicates | US-10, US-11, US-12, US-18, US-24 |
| 3. Reading: `kb-recall` | v0.4 | ⬜ Not done | The agent finds past knowledge on "let's continue", "what did we cover"; the learning profile works | US-07, US-08, US-09, US-15 |
| 4. Updates and cloud copy | v0.5 | ⬜ Not done | `kb update` in a single command; `kb sync` copies the vault to Google Drive | US-17, US-18, US-20 |
| 5. Stabilization | v1.0 | ⬜ Not done | CI on typical scenarios, provenance queries, documentation; the MVP is ready for daily use | US-12, US-13, US-23 |
| Later | v1.x+ | — | Extensions from the backlog (§4) | US-02, US-03, US-05, US-06, US-14, US-21, US-22 |

Stage status: ⬜ Not done or ✅ Done. A stage is done when all of its "Done when" criteria are met. Update the status in both this table and the stage section.

Stages 2 and 3 are the core of the value. Stages 0–1 prepare for them; stages 4–5 make them convenient and reliable.

## 3. Stages

### Stage 0. Skeleton and checks → v0.1

**Status:** ✅ Done (v0.1.0, 2026-10-09). Results: [note-schema-v0.md](note-schema-v0.md), [clients-v0.md](clients-v0.md); Cursor is checked hands-on in stage 2.

**Goal:** remove technical unknowns before writing the main logic.

Work:

- Package repository on GitHub: a `uv` project, the `kb` CLI entry point, `pytest`, minimal CI (build, tests, install via `uv tool install`).
- Client verification: where Claude Code, Codex and Cursor look for user skills and global instructions; the `SKILL.md` format; how a skill is invoked manually in each client.
- Note schema v0: required and optional frontmatter fields for the five types, the `created_by` / `updates` format, a decision on `insight`.
- Vault structure v0: directories, templates, `learning_profile.md`.
- User configuration format and its location (outside the vault and outside the repository).

Open questions closed: folder structure and metadata schema (US, question 4); skills directories in the clients (question 10); configuration format (question 12).

**Done when:** `uv tool install git+https://github.com/<owner>/<repo>` installs the package and `kb --version` shows the version; there is a short document with the note schema and a table of paths for the three clients.

### Stage 1. Knowledge base → v0.2

**Status:** ✅ Done (v0.2.0, 2026-10-09). Commands: `kb setup`, `kb init`, `kb doctor`, `kb where`; templates use Obsidian Templates placeholders (`{{title}}`, `{{date:YYYY-MM-DD}}`); config example in `examples/config.example.toml`.

**Goal:** the knowledge base itself, which the agents will work with, comes into existence.

Work:

- `kb init`: creates the vault in the chosen folder (structure, templates, learning profile) and an entry in the configuration. Does not overwrite existing files.
- `kb setup`: first-run setup wizard — vault path, choice of clients (skills installation arrives in stage 2).
- `kb doctor` v0: checks the configuration and that the vault exists.
- Note templates with Mermaid and attachment examples (US-16).

**Done when:** after `kb setup` the folder opens in Obsidian via "Open folder as vault", templates and the profile are in place; running `kb init` again breaks nothing.

### Stage 2. Writing: `add-knowledge` → v0.3

**Status:** ⬜ Not done

**Goal:** the main MVP scenario (US-24) works end to end.

Work:

- CLI: `kb search` (by type, topics, frontmatter and text); creating and extending notes from templates; **provenance stamped by the CLI**; schema validation; detection of possible duplicates.
- `add-knowledge` skill: collect conversation outcomes → classify by type → search for existing notes → create/extend → report created and changed files (design §11.2).
- Marking what is confirmed vs. what is an assumption; handling contradictions with older notes (US-10).
- `kb install-skills` / installing skills into the chosen clients during `kb setup`; copying with the package version recorded.
- Resolving the open question: whether to show a plan before editing existing notes.

**Done when:** in each of the three clients, invoking `add-knowledge` after a learning conversation creates a `learning-session` and creates or extends `concept` notes; frontmatter passes validation; a repeated invocation on the same topic extends rather than duplicates.

### Stage 3. Reading: `kb-recall` → v0.4

**Status:** ⬜ Not done

**Goal:** the next conversation continues the accumulated work.

Work:

- `kb-recall` skill: triggers on "let's continue", "what did we cover", "remind me what was unclear"; searches via `kb search` and reads the notes it finds rather than the whole vault; says explicitly when nothing is found (US-07).
- Learning profile: format, updates via `add-knowledge`, how it is loaded (US-09).
- A global instruction for the three clients, installed by `kb setup` (US-15).
- Search in the MVP is text- and metadata-based, without embeddings (US-08).

**Done when:** in a new conversation, "let's continue studying X" yields an answer grounded in past notes and open questions; a simple question that needs no personal context does not read the knowledge base.

### Stage 4. Updates and cloud copy → v0.5

**Status:** ⬜ Not done

**Goal:** the package is easy to update, and the knowledge base is protected from accidental deletion.

Work:

- `kb update`: `uv tool upgrade` + reinstalling skills into all chosen clients in a single command.
- Version consistency checks: `kb doctor` and a warning in the skill before writing.
- `kb sync` via `rclone`: one-way copy of the vault to Google Drive with an archive of old versions (design §12.1); one-time authorization setup.
- Decision: run `kb sync` manually, on a schedule, or after `add-knowledge`.

**Done when:** releasing a new version and running `kb update` updates the skills in all clients; after a note is accidentally deleted, it can be restored from Google Drive.

### Stage 5. Stabilization → v1.0

**Status:** ⬜ Not done

**Goal:** the MVP is fit for daily use.

Work:

- CI on test data: installation, `init`, skills installation, writing and validating notes, independence from personal data (US-23).
- Provenance queries: `kb search --skill --version`, finding research as of a date (US-12, US-13).
- Versioning policy and release history (changelog), configuration migration path.
- Documentation: installation, updating, first run, restoring from the cloud copy.

**Done when:** all typical MVP scenarios from the user stories pass manually and in CI; the `v1.0.0` tag is released.

## 4. After the MVP (backlog)

The order is approximate: items at the top are closer to the current value.

| Direction | What it gives | US / design |
|---|---|---|
| `save-source` and `research` skills | Dedicated scenarios for articles and dated comparisons | US-02, US-03 |
| Revision under new rules | Updating notes with a new skill with distinguishable provenance | US-13 |
| Source registry and supporting sources (Notion, GitHub, Web) | Combining knowledge with current status and code | US-05, US-06, US-14 |
| Hook reminder before context compaction | Fewer losses in long conversations | design §9.1, §11.2 |
| "Librarian" subagent | Searching a large vault without cluttering the context | design §9.1 |
| Semantic/hybrid search | Better retrieval on a large knowledge base | US-08 |
| Note change history, `kb backup` snapshots | More reliable restore and revision | US-13, design §12.1 |
| MCP wrapper over the core | Access for clients without a shell | design §9.1 |
| ChatGPT | Desktop Work mode or a cloud inbox | design §12.2 |
| Mobile access | Reading/editing the knowledge base from a phone | US-20 |
| Multiple knowledge bases | Separate vaults on one installation | US-21 |
| Other users, publishing | Package installation by someone other than the author | US-22 |

## 5. Risks and how to mitigate them

| Risk | Where it shows up | Mitigation |
|---|---|---|
| Clients support skills differently and change their mechanisms | Stages 0, 2 | Verification in stage 0; installation via separate adapters; skills without client-specific features |
| The agent loses early details of a long conversation after context compaction | Stage 2 | Recommend invoking `add-knowledge` before compaction; later, a hook reminder |
| Duplicates and knowledge "smeared" across notes | Stages 2–3 | Search before writing, duplicate checks in the CLI, change report |
| CLI and skills versions diverge | Stage 4 | `kb update` as a single command, `kb doctor`, version check in the skill |
| The cloud copy does not protect against everything | Stage 4 | One-way sync with a version archive; snapshots are in the backlog |

## 6. Document history

- **1.0 — 2026-10-09:** first version of the roadmap, based on user stories v1.7 and design v1.6.
- **1.1 — 2026-10-09:** added a completion status for each stage (in the overview table and in each stage section).
- **1.2 — 2026-10-09:** stage 0 done: package `v0.1.0` installs from GitHub, note schema and client paths recorded; references updated to user stories 1.8 and design 1.7.
- **1.3 — 2026-10-09:** stage 1 done: package `v0.2.0` with `kb setup`, `kb init`, `kb doctor` v0 and `kb where`; vault templates with Mermaid and attachment examples; CI smoke test on a temporary vault.
