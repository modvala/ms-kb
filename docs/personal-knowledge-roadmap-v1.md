---
title: "Personal Knowledge System — Roadmap"
document_version: "1.10"
created: "2026-10-09"
language: en
status: superseded
superseded_by: "personal-knowledge-roadmap-v2.md"
requirements_ref: "personal-knowledge-user-stories-v1.md"
requirements_version: "1.11"
design_ref: "personal-knowledge-design-v1.md"
design_version: "1.13"
---

# Personal Knowledge System — Roadmap v1.10

> **Superseded** by [personal-knowledge-roadmap-v2.md](personal-knowledge-roadmap-v2.md) (2026-10-12). This version is kept as the history of the MVP decisions for roadmap stages 0–4.

## 1. Purpose

The roadmap breaks the requirements (user stories v1.7) and the design (v1.6) into sequential development stages. Each stage ends with a working result that can actually be used. No deadlines are given: the project is run by one person, and order matters more than dates.

**MVP goal:** after a long learning conversation in Claude Code, Codex or Cursor, invoke `add-knowledge` and get tidy notes in the local knowledge base; in the next conversation, use `kb-recall` to continue with what has already been learned taken into account.

**MVP scope** (from "MVP decisions"): one user; Python + `uv`; Claude Code, Codex and Cursor clients; one new knowledge base created from scratch; writes only on explicit skill invocation; local vault with its own Git history and a push to a private remote dedicated to it (decided by the stage 4 research, design §12); other cloud copies (Google Drive, snapshot backups), ChatGPT, MCP, subagents, hooks, multiple knowledge bases, multi-device sync and mobile access come after the MVP.

## 2. Stage overview

| Stage | Version | Status | Result | Key US |
|---|---|---|---|---|
| 0. Skeleton and checks | v0.1 | ✅ Done | Package installs from GitHub, `kb --version` works; skills directories verified in all three clients; note schema approved | US-04, US-17, US-23 |
| 1. Knowledge base | v0.2 | ✅ Done | `kb init` / `kb setup` create the vault, configuration and profile; the vault opens in Obsidian | US-01, US-16, US-19 |
| 2. Writing: `add-knowledge` | v0.3 | ✅ Done | Conversation outcomes are saved to the knowledge base (checked in Claude Code; Codex and Cursor in stage 5), with provenance and without duplicates | US-10, US-11, US-12, US-18, US-24 |
| 3. Reading: `kb-recall` | v0.4 | ✅ Done | The agent finds past knowledge on "let's continue", "what did we cover"; the learning profile works | US-07, US-08, US-09, US-15 |
| 4. Updates and data protection | v0.5 | ✅ Done | `kb update` in a single command; the vault's own Git history with a commit per write; `kb sync` pushes to a private remote hourly and on demand; deleted notes are detected by `kb doctor` and returned by `kb restore` | US-13, US-17, US-18, US-20 |
| 5. Stabilization | v1.0 | ⬜ Not done | CI on typical scenarios, provenance queries, documentation; the MVP is ready for daily use | US-12, US-13, US-23 |
| Later | v1.x+ | — | Extensions from the backlog (§4) | US-02, US-03, US-05, US-06, US-14, US-21, US-22 |

Stage status: ⬜ Not done or ✅ Done. A stage is done when all of its "Done when" criteria are met. Update the status in both this table and the stage section.

Stages 2 and 3 are the core of the value. Stages 0–1 prepare for them; stages 4–5 make them convenient and reliable.

## 3. Stages

### Stage 0. Skeleton and checks → v0.1

**Status:** ✅ Done (v0.1.0, 2026-10-09). Results: [note-schema-v0.md](note-schema-v0.md), [clients-v0.md](clients-v0.md); Cursor is checked hands-on in stage 5.

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

**Status:** ✅ Done (v0.3.0, 2026-10-10). Implemented: `kb search`, `kb new`, `kb extend`, `kb validate`, `kb install-skills` (also run by `kb setup`), skills in `kb doctor`, the `add-knowledge` skill. Decided: the CLI writes notes and extends append-only; a plan is shown before extending existing notes (design §9.1, §11). `learning_profile.md` is treated as user data (design §12.4). Checked hands-on in Claude Code (2026-10-10, [clients-v0.md](clients-v0.md) §4); Codex and Cursor are checked together with the other skills in stage 5.

**Goal:** the main MVP scenario (US-24) works end to end.

Work:

- CLI: `kb search` (by type, topics, frontmatter and text); creating and extending notes from templates; **provenance stamped by the CLI**; schema validation; detection of possible duplicates.
- `add-knowledge` skill: collect conversation outcomes → classify by type → search for existing notes → create/extend → report created and changed files (design §11.2).
- Marking what is confirmed vs. what is an assumption; handling contradictions with older notes (US-10).
- `kb install-skills` / installing skills into the chosen clients during `kb setup`; copying with the package version recorded.
- Resolving the open question: whether to show a plan before editing existing notes.
- `learning_profile.md` as user data (design §12.4): it is extended by `kb extend`, but `kb init` treats it as a regenerable file, so after an accidental deletion `kb doctor` suggests `kb init`, which recreates an empty profile and hides the loss. Split the vault files into regenerable and user data: `kb doctor` points to a restore for missing user data, and `kb init` recreates the profile only on a fresh vault or with an explicit flag.

**Done when:** in Claude Code, invoking `add-knowledge` after a learning conversation creates a `learning-session` and creates or extends `concept` notes; frontmatter passes validation; a repeated invocation on the same topic extends rather than duplicates. The same check in Codex and Cursor is deferred to stage 5.

### Stage 3. Reading: `kb-recall` → v0.4

**Status:** ✅ Done (v0.4.0, 2026-10-10). Checked hands-on in Claude Code ([clients-v0.md](clients-v0.md) §4.2); Codex and Cursor in stage 5. Implemented:

- the `kb-recall` skill (read-only; profile first, then 1–3 `kb search` calls and up to about 5 notes);
- the global instruction as a marked block in `~/.claude/CLAUDE.md` and `$CODEX_HOME/AGENTS.md`, written by `kb setup` / `kb install-skills`; Cursor gets text to paste;
- `kb doctor` checks the block and warns about a long profile;
- `add-knowledge` 0.4.0 adds new concepts to `## Known topics`.

Decided: the profile is loaded on demand by `kb-recall`, never automatically (design §10); MVP search is text and metadata.

**Goal:** the next conversation continues the accumulated work.

Work:

- `kb-recall` skill: triggers on "let's continue", "what did we cover", "remind me what was unclear"; searches via `kb search` and reads the notes it finds rather than the whole vault; says explicitly when nothing is found (US-07).
- Learning profile: format, updates via `add-knowledge`, how it is loaded (US-09).
- A global instruction for the three clients, installed by `kb setup` (US-15).
- Search in the MVP is text- and metadata-based, without embeddings (US-08).

**Done when:** in a new conversation, "let's continue studying X" yields an answer grounded in past notes and open questions; a simple question that needs no personal context does not read the knowledge base.

### Stage 4. Updates and data protection → v0.5

**Status:** ✅ Done (v0.5.0, 2026-10-11). The storage research (2026-10-10) is recorded in design §12 v1.12, the implementation decisions in §12.6 v1.13. Implemented:

- the vault's own Git repository with a commit per write and provenance trailers, outside edits in separate commits;
- secrets refused, large files kept out of history;
- `kb history`, `kb restore`, the manifest with deleted/damaged/moved and broken-link checks in `kb doctor` / `kb validate`;
- `kb sync` to a private remote with an hourly LaunchAgent;
- `kb update` and the version warning in `kb where`;
- skills 0.5.0 with the vault rules.

Checked hands-on on the real vault with a private GitHub remote ([clients-v0.md](clients-v0.md) §4.3). Other cloud copies and multi-device sync are in the backlog (§4).

**Goal:** the package is easy to update; the knowledge base has its own change history and an off-machine copy, and accidental deletion of a note is detected and reversible.

Work:

- `kb update`: `uv tool upgrade` + reinstalling skills into all chosen clients in a single command.
- Version consistency checks: `kb doctor` and a warning in the skill before writing.
- **Vault history** (design §12.1):
  - `kb init` makes the vault root its own Git repository (new and existing vaults) and writes `.gitignore` (`.obsidian/workspace*.json`, `.obsidian/cache`, `.trash/`, `.DS_Store`, `kb` temporary files); no nested repository inside a foreign work tree.
  - `kb doctor` warns only when the vault is inside a *foreign* repository, not when the vault root is its own repository (today it warns about any Git work tree).
  - `kb new` / `kb extend` commit after the write: outside changes first in a separate `external:` commit (`git add -A`), then only `kb`'s own paths with `kb: create|extend <path>` and provenance trailers.
  - Git via `subprocess`; Git never blocks a note write (missing `git`, failed commit → warning and stale state); `index.lock` retries without deleting the lock; a lock file serializes `kb` runs.
  - Checks before writing and committing: key-like strings (plus `gitleaks` if installed) refuse the write; files over the size limit are not committed.
  - `kb history [PATH]`: notes' history, including deleted notes.
- **Off-machine copy** (design §12.3):
  - `kb sync`: commit outside edits, then `git push` to the configured remote; never `--force`, non-interactive; a rejected push is reported.
  - Configuration `[kbs.<name>.sync]` with `provider = "git"` and `remote`; `kb setup` offers to set the remote (the user creates the private repository and the key).
  - A LaunchAgent running `kb sync` hourly (`StartCalendarInterval` + `RunAtLoad`), installed by `kb setup` with the user's consent and removable.
- **Data integrity** (design §12.4):
  - A manifest of notes written by `kb` (path, SHA-256, size, mtime, writer) outside the vault, updated after every write.
  - `kb doctor` / `kb validate`: deleted, moved and damaged notes compared with the manifest; broken wiki-links that used to resolve; freshness (last commit and push, LaunchAgent loaded, `git` present).
  - `kb restore PATH [--at REV]`: never overwrites silently (side file + diff when the path is occupied, `--force` saves the current version first, `--dry-run`); a user command, not exposed to skills.
  - Skill rule: never delete, move or rename vault files and never run Git there; only `kb` changes the vault.
- **Documentation:** README sections on history, `kb sync`, restore, recommended Time Machine, choosing a Git host (GitHub Free cannot forbid force-push on private repositories; stronger options) and recommended agent sandbox settings for the vault; the vault `README.md` template no longer says "do not put this folder into Git".
- Record the outcome in the design and requirements (done in design 1.12 and user stories 1.11).

**Done when:** releasing a new version and running `kb update` updates the skills in all clients; after `kb new` / `kb extend` the change is a commit with provenance, and an edit made in Obsidian ends up in a separate commit; `kb sync` pushes to a private remote, by hand and from the LaunchAgent; after a note is accidentally deleted, `kb doctor` reports it and `kb restore` returns it; after the local vault folder is removed entirely, it is recovered from the remote with `git clone`.

### Stage 5. Stabilization → v1.0

**Status:** ⬜ Not done

**Goal:** the MVP is fit for daily use.

Work:

- CI on test data: installation, `init`, skills installation, writing and validating notes, independence from personal data (US-23).
- Hands-on check of all skills (`add-knowledge`, `kb-recall`), the global instruction and `kb update` in Codex and Cursor together, deferred from stages 2–4, plus `kb-recall` with `kb` unavailable in all three clients; results go to [clients-v0.md](clients-v0.md). Includes whether Cursor shows duplicate skills and which environment variables identify Codex and Cursor for `agent` in provenance.
- Provenance queries: `kb search --skill --version`, finding research as of a date (US-12, US-13).
- Versioning policy and release history (changelog), configuration migration path.
- Documentation: installation, updating, first run, restoring deleted notes.

**Done when:** all typical MVP scenarios from the user stories pass manually in Claude Code, Codex and Cursor and in CI; the `v1.0.0` tag is released.

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
| A second cloud copy: `restic`/Kopia snapshots (e.g. to Backblaze B2) or Google Drive via `rclone --backup-dir` | A copy independent of the Git host, optionally encrypted | US-20, design §12.5 |
| MCP wrapper over the core | Access for clients without a shell | design §9.1 |
| ChatGPT | Desktop Work mode or a cloud inbox | design §12.2 |
| Mobile access and multi-device sync | Reading/editing the knowledge base from a phone or a second computer through one two-way mechanism (e.g. Obsidian Sync); Git stays one-way on the Mac | US-20, design §12.5 |
| Stronger vault protection | `kb doctor` checks agents' sandbox and permission settings for the vault; a stable note `id` for move detection; a debounced file watcher to commit outside edits sooner | design §12.4 |
| Multiple knowledge bases | Separate vaults on one installation | US-21 |
| Other users, publishing | Package installation by someone other than the author | US-22 |

## 5. Risks and how to mitigate them

| Risk | Where it shows up | Mitigation |
|---|---|---|
| Clients support skills differently and change their mechanisms | Stages 0, 2 | Verification in stage 0; installation via separate adapters; skills without client-specific features |
| The agent loses early details of a long conversation after context compaction | Stage 2 | Recommend invoking `add-knowledge` before compaction; later, a hook reminder |
| Duplicates and knowledge "smeared" across notes | Stages 2–3 | Search before writing, duplicate checks in the CLI, change report |
| CLI and skills versions diverge | Stage 4 | `kb update` as a single command, `kb doctor`, version check in the skill |
| Local history alone does not survive loss of the computer | Stage 4 | `kb sync` pushes to a private remote; Time Machine as an independent local copy; `kb doctor` warns when the push is stale |
| GitHub Free cannot forbid force-push on a private repository | Stage 4 | `kb` never force-pushes; the remote is one of three copies (local `.git`, Time Machine, remote); stronger hosts documented |
| A secret pasted into a conversation ends up in a note and is pushed | Stage 4 | `kb` refuses key-like strings before writing and before pushing |
| An agent deletes vault files with shell commands, bypassing skill rules | Stage 4 | Recommended sandbox settings documented; history and remote out of the agent's reach; `kb doctor` detects deletions against the manifest |
| A recreated empty file hides lost user data (`learning_profile.md`) | Stage 2 | User-data files are never silently recreated by `kb init` |

## 6. Document history

- **1.0 — 2026-10-09:** first version of the roadmap, based on user stories v1.7 and design v1.6.
- **1.1 — 2026-10-09:** added a completion status for each stage (in the overview table and in each stage section).
- **1.2 — 2026-10-09:** stage 0 done: package `v0.1.0` installs from GitHub, note schema and client paths recorded; references updated to user stories 1.8 and design 1.7.
- **1.3 — 2026-10-09:** stage 1 done: package `v0.2.0` with `kb setup`, `kb init`, `kb doctor` v0 and `kb where`; vault templates with Mermaid and attachment examples; CI smoke test on a temporary vault.
- **1.4 — 2026-10-10:** stage 2: `learning_profile.md` treated as user data. Stage 4: a design decision on sync and data integrity (Git/GitHub and/or Google Drive, design §12.3–§12.4) before implementing `kb sync`, plus detection and restore of deleted notes. Design reference updated to 1.9.
- **1.5 — 2026-10-10:** stage 2 done: package `v0.3.0` with `kb search`, `kb new`, `kb extend`, `kb validate`, `kb install-skills` and the `add-knowledge` skill; `learning_profile.md` as user data; checked hands-on in Claude Code; hands-on checks in Codex and Cursor moved to stage 5, where all skills are checked in those clients together. Design reference updated to 1.10.
- **1.6 — 2026-10-10:** stage 4 renamed "Updates and data protection": cloud sync is no longer a committed result. Stage 4 starts with research on vault storage, split into change history (a separate Git repository for the vault), an off-machine copy (needed or not; private remote vs Google Drive) and multi-device sync (backlog). `kb sync` is implemented only if a remote copy is chosen. MVP scope, risks and backlog updated.
- **1.7 — 2026-10-10:** stage 3 done: package `v0.4.0` with the `kb-recall` skill, the global instruction and the learning profile loaded on demand; checked hands-on in Claude Code. The "`kb` unavailable" check and the Codex/Cursor checks move to stage 5. Design reference updated to 1.11, requirements to 1.10.
- **1.8 — 2026-10-10:** stage 4 storage research done (design §12 v1.12, user stories 1.11). Stage 4 now implements everything Git-related: the vault's own repository with a commit per write, `kb sync` pushing to a private remote hourly and on demand, `kb history`, `kb restore`, the manifest and integrity checks. Other cloud copies (Google Drive, snapshot backups) and multi-device sync moved to the backlog. MVP scope, risks and backlog updated.
- **1.9 — 2026-10-11:** stage 4 done: package `v0.5.0` with the vault's own Git history, `kb sync` to a private remote hourly and on demand, the manifest and integrity checks, `kb history`, `kb restore` and `kb update`; checked hands-on on the real vault. Design reference updated to 1.13.
- **1.10 — 2026-10-12:** superseded by [personal-knowledge-roadmap-v2.md](personal-knowledge-roadmap-v2.md); content unchanged.
