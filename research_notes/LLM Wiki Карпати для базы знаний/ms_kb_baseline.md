# ms-kb baseline for mapping Karpathy's "LLM Wiki" pattern (state as of 2026-10-12, package v0.5.0)

Scope: what the `kb` CLI, its skills and docs do today; which rules conflict with or support the user's target workflow (after a research session with an agent, **rewrite/consolidate one topic page** and make **targeted link edits on neighbouring pages**; no "what I studied on which day" history; clients Claude Code, Codex and Cursor). The real vault at `~/Knowledge/main` was only read.

Method and citation conventions:
- Code and doc references are `path:line` relative to the repository `/Users/sergeimodvala/Documents/Projects/ms-kb` (for example `src/ms_kb/write.py:148-209`). Vault references are `~/Knowledge/main/<path>:line`. State files are in `~/.config/ms-kb/`.
- Vault numbers come from reading the files directly and from a read-only Python script in the session scratchpad (byte counts, frontmatter share, link counts, line similarity via `difflib`). The vault's commit list was read from the file `.git/logs/HEAD`; `git` was not run and nothing was written.
- The LLM Wiki pattern is cited from [Karpathy's gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), fetched 2026-10-12 through a summarizing fetch tool. The quotes below are short phrases reported by that tool, not checked word for word.

## 1. What ms-kb does today, and which LLM-Wiki operation each CLI command corresponds to

### Takeaway
ms-kb v0.5.0 is a deterministic Python CLI (`kb`, 13 commands) plus two agent skills: `add-knowledge` ingests from the current conversation and `kb-recall` handles queries. A seven-line global instruction tells the agent that the base exists. Only three commands work on note content as wiki operations: `new` and `extend` (ingest) and `search` (query). `validate` and `doctor` are structural lint. The other eight are infrastructure (setup, install, update, history, backup, restore). `restore` also writes notes, but only as a user-run safety net. Every write goes through one guarded path: secret scan, lock, commit of outside edits, write, a commit of only that file with provenance trailers, then a manifest update. `extend` is append-only by design.

### Cited Findings
- Separation principle: "everything that can be checked by code is done by the CLI; everything that requires understanding text is done by a skill (LLM)". Skills plus CLI, no MCP, subagents or hooks in the MVP. — [docs/personal-knowledge-design-v1.md:479-490](docs/personal-knowledge-design-v1.md)
- Stages 0–4 are done (v0.1–v0.5). Stage 5 (stabilization, v1.0) is not. — [docs/personal-knowledge-roadmap-v1.md:25-33](docs/personal-knowledge-roadmap-v1.md)
- The CLI parser defines exactly 13 subcommands. — [src/ms_kb/cli.py:779-893](src/ms_kb/cli.py) (confirmed by `uv run kb --help`)

| Command | What it does | Code | LLM-Wiki operation |
|---|---|---|---|
| `setup` | First-run wizard: vault path, clients, `init`, private remote, hourly LaunchAgent, installs skills and the global instruction | `cli.py:206-243`, `cli.py:164-203` | none (bootstraps the "schema" layer and infrastructure) |
| `init` | Creates missing folders, templates, README and `.gitignore`, never overwriting; the profile only for a new vault; makes the vault root its own Git repo | `cli.py:86-148`, `vault.py:49-71`, `history.py:113-126` | none (scaffolding) |
| `doctor` | Checks the config, vault structure and profile length (>150 lines warns), the Git repo, integrity against the manifest (deleted, damaged, moved, links that stopped resolving, leftover restored copies), push freshness and skill/instruction versions. `--ack PATH` accepts a deletion or damage | `cli.py:246-331`, `integrity.py:68-121` | **lint**, structural only |
| `update` | `uv tool upgrade`, then the new `kb` reinstalls skills, instructions and the schedule | `cli.py:446-468` | none |
| `where` | Prints the vault path and warns when installed skills come from another version; the first step of both skills | `cli.py:433-443` | none (skill entry check) |
| `install-skills` | Copies bundled skills to `~/.claude/skills` and `~/.agents/skills` and writes the marked block into `~/.claude/CLAUDE.md` and `$CODEX_HOME/AGENTS.md` | `cli.py:471-507`, `installer.py:21-54` | none (distributes the "schema" layer) |
| `search` | AND-ed text terms plus `--type`, `--topic` and `--field KEY=VALUE` (dotted paths). No index: the type folders are scanned on every call. Ranked by score, then `updated`; `--json` output | `cli.py:520-536`, `search.py:1-4`, `search.py:105-143` | **query** (retrieval); also the de-duplication check before ingest |
| `new` | Creates a note: builds the frontmatter, stamps `created_by` with `--skill`, refuses exact and similar duplicates, validates, writes and commits | `cli.py:618-635`, `write.py:66-131` | **ingest** (create a page) |
| `extend` | Appends `## Section` blocks, skips bullets already present, merges `topics`/`related`/`sources`, sets `updated` and appends an `updates` provenance entry. Never rewrites | `cli.py:638-652`, `write.py:148-209`, `notes.py:173-213` | **ingest** (append-only revision) |
| `validate` | Schema check (errors block writes, warnings do not). With no paths it also runs the integrity check | `cli.py:663-696`, `schema.py:70-117` | **lint**, schema and structure |
| `history` | Wraps `git log`, including deleted files, and shows the `Kb-Skill` trailer | `cli.py:707-723`, `history.py:208-232` | the read side of a `log.md` (git is the log) |
| `sync` | Commits outside edits and pushes to the private remote, never forced; `--schedule on/off/status` | `cli.py:377-430`, `history.py:279-289` | none (backup) |
| `restore` | Brings a note back from Git; writes a side file if the path is taken, `--force` replaces it, `--dry-run`; a user command, not exposed to skills | `cli.py:726-767` | none (safety net) |

- The single write path `_finish`: the secret check on added lines, then the vault lock, commit of outside edits, `save()`, commit of only the written path (`kb: create|extend <path>` with trailers), and finally `vaultstate.record` (the manifest hash after the write). — [src/ms_kb/cli.py:591-615](src/ms_kb/cli.py)
- `save()` uses optimistic concurrency: an extend is refused if the file changed on disk after it was read. It writes through a temporary file and `os.replace`. — [src/ms_kb/write.py:212-226](src/ms_kb/write.py)
- Provenance is stamped by the CLI, not the model: skill, skill_version (from `installed.toml`), package_version, skill_ref (the SKILL.md URL at the release tag), date, and `agent` only when `CLAUDECODE=1`. The same data goes into Git trailers (`Kb-Skill`, `Kb-Skill-Version`, `Kb-Version`, `Kb-Agent`). — [src/ms_kb/provenance.py:17](src/ms_kb/provenance.py), [src/ms_kb/provenance.py:38-66](src/ms_kb/provenance.py), [src/ms_kb/history.py:168-178](src/ms_kb/history.py)
- Five note types, each in its own folder (`concepts/`, `sources/`, `research/`, `learning-sessions/`, `projects/`). Required fields: `type`, `title`, `created`, `updated` and `topics` (kebab-case ASCII), plus `url` (source), `as_of` and `sources` (research), and `session_date` (learning-session). — [src/ms_kb/notes.py:14-26](src/ms_kb/notes.py), [src/ms_kb/schema.py:11-23](src/ms_kb/schema.py), [docs/note-schema-v0.md:17-46](docs/note-schema-v0.md)
- The `add-knowledge` skill (v0.5.0, 175 lines): `kb where` → collect and mark each point confirmed or assumption → classify ("Exactly one **`learning-session`** per run") → `kb search` before writing → contradiction and assumption callouts → a plan gate before extending existing notes → write via `kb new`/`kb extend` → extend `learning_profile.md` → `kb validate` and report. — [src/ms_kb/skills/add-knowledge/SKILL.md:25-174](src/ms_kb/skills/add-knowledge/SKILL.md)
- The `kb-recall` skill (read-only, 84 lines): `kb where` → read the profile → 1–3 `kb search --json` → read up to about 5 notes → answer, keeping assumptions marked. It never saves and may suggest `add-knowledge`. — [src/ms_kb/skills/kb-recall/SKILL.md:16-84](src/ms_kb/skills/kb-recall/SKILL.md)
- The global instruction is 7 lines: use `kb-recall` for continuing or recalling, `add-knowledge` only on request, change the vault only through `kb`. — [src/ms_kb/global-instruction.md:1-7](src/ms_kb/global-instruction.md)
- CI runs pytest (187 test functions across `tests/`) and a smoke script: `setup/init/doctor/new/extend/search/validate/sync/restore/history` on a temporary vault with a local bare remote. — [.github/workflows/ci.yml:23-68](.github/workflows/ci.yml)

### Inferences
- In Karpathy's terms, **ingest** = `add-knowledge` + `kb new`/`kb extend`, **query** = `kb-recall` + `kb search`, **lint** = `kb validate`/`kb doctor`, but only structural lint. No command or skill does semantic lint: contradictions, stale claims, orphans, missing pages or cross-references.
- ms-kb's "schema layer" is spread across `SKILL.md`, `references/note-types.md`, `global-instruction.md`, `docs/note-schema-v0.md` and the validator. It is versioned and released with the package. In Karpathy's pattern the schema is a CLAUDE.md/AGENTS.md that "the human and LLM refine together" inside the wiki ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). Here the user can change the rules only by releasing a new package version.
- The ingest source in ms-kb is the **current conversation**, not a file. Nothing like the "raw sources" layer exists.

### Gaps
- Codex and Cursor have not been checked hands-on for any skill; those rows are "pending". — [docs/clients-v0.md:85-93](docs/clients-v0.md)

## 2. Which current rules block "rewrite one topic page + targeted link edits on neighbours"

### Takeaway
The main blocker is the **append-only invariant**. It is enforced in `write.py`/`notes.py`, asserted in tests and written into at least five docs. It is also named as part of the data-protection trust boundary ("`kb` itself (it can only append)"), so removing it needs a replacement safeguard. Next come four skill and doc rules: "exactly one learning-session per run", the profile as a dated, append-only log, "contradictions as appended callouts, never reword old text", and frontmatter provenance whose `updates` list only grows. Some rules help: the plan gate (can become a diff gate), duplicate checks, confirmed/assumption marking and aliases. The "damaged" heuristic is not triggered by a rewrite made **through `kb`**, because every kb write refreshes the manifest. It is triggered by a rewrite made **outside `kb`** that shrinks a note below 50% of its manifest size. Merging or deleting pages triggers "deleted" errors and broken-link warnings.

### Cited Findings

**(a) Append-only `kb extend`. Blocks the rewrite.**
- Module docstring: "Extending only appends to sections and lists, so existing text is never rewritten (US-10)." — [src/ms_kb/write.py:1-6](src/ms_kb/write.py)
- `extend_note` has no replace path. It only calls `append_to_section` for each fragment section and for each `--related` link, and `merge_list` for frontmatter lists. — [src/ms_kb/write.py:170-189](src/ms_kb/write.py)
- `append_to_section` only inserts lines at the end of a section, or creates the section before `## Related`. Bullets that are exact duplicates are skipped, and no line is ever removed or changed. — [src/ms_kb/notes.py:173-213](src/ms_kb/notes.py)
- `parse_fragment` refuses a `# Title` and any text before the first `## Section`, so a whole page body cannot be passed to `extend`. — [src/ms_kb/notes.py:216-229](src/ms_kb/notes.py)
- A test asserts that every old line survives an extend ("the old text is still there, line for line"). — [tests/test_write.py:121-123](tests/test_write.py)
- Docs that state the invariant: design §9.1 "`kb extend` only appends to sections and lists, so existing text is never rewritten. The agent does not edit note files with its own tools." — [docs/personal-knowledge-design-v1.md:497](docs/personal-knowledge-design-v1.md); design §12.4 "The CLI has no delete command and extends append-only" — [docs/personal-knowledge-design-v1.md:672](docs/personal-knowledge-design-v1.md); design §14 rows "Writing" and "Data integrity" — [docs/personal-knowledge-design-v1.md:733-735](docs/personal-knowledge-design-v1.md); note-schema §7 "Existing text is never rewritten." — [docs/note-schema-v0.md:171](docs/note-schema-v0.md); README "appends '## Section' blocks, never rewrites" — [README.md:88](README.md); project CLAUDE.md "`extend` only appends to `##` sections and lists — existing text is never rewritten" (`CLAUDE.md`, Write bullet).
- Append-only is part of the security argument: "The trust boundary is not the skill text but the OS sandbox, `kb` itself (it can only append) and copies the agent cannot reach." — [docs/personal-knowledge-design-v1.md:668](docs/personal-knowledge-design-v1.md)
- Real effect in the vault: `Python concurrency models` now contradicts itself. A `[!note] Подтверждено` callout says the assumption "`asyncio` — конкурентность без параллелизма" was confirmed, while the original `[!question] Assumption` callout in `## Limitations` still lists it as unconfirmed, because `extend` cannot touch the old callout. — `~/Knowledge/main/concepts/Python concurrency models.md:69-70` vs `:86`

**(b) No delete, merge or rename.**
- "The CLI has no delete command" — [docs/personal-knowledge-design-v1.md:607](docs/personal-knowledge-design-v1.md), [docs/personal-knowledge-design-v1.md:672](docs/personal-knowledge-design-v1.md). Skills must "Never delete, move or rename vault files, and never change them with anything but `kb new` / `kb extend`." — [src/ms_kb/skills/add-knowledge/SKILL.md:18-21](src/ms_kb/skills/add-knowledge/SKILL.md); global instruction — [src/ms_kb/global-instruction.md:7](src/ms_kb/global-instruction.md)
- So consolidating several concept pages into one topic page, or folding the session notes into it, is impossible through `kb` today.

**(c) Contradiction rule. Blocks in-place consolidation.**
- "If new material contradicts an existing note, do not remove or reword the old text. Append a callout … and add an open question about it to the session note." — [src/ms_kb/skills/add-knowledge/SKILL.md:77-83](src/ms_kb/skills/add-knowledge/SKILL.md); callout formats — [src/ms_kb/skills/add-knowledge/references/note-types.md:21-29](src/ms_kb/skills/add-knowledge/references/note-types.md)
- The source requirement is softer: "Contradictions with an older note are flagged; an update does not erase the basis of the previous conclusion without explanation." — [docs/personal-knowledge-user-stories-v1.md:167](docs/personal-knowledge-user-stories-v1.md). An in-place rewrite that states its reason would satisfy this wording; the skill's stricter rule would not.

**(d) "Exactly one learning-session per run". Conflicts with "no study-history".**
- [src/ms_kb/skills/add-knowledge/SKILL.md:56](src/ms_kb/skills/add-knowledge/SKILL.md) ("Exactly one **`learning-session`** per run"), [src/ms_kb/skills/add-knowledge/SKILL.md:101](src/ms_kb/skills/add-knowledge/SKILL.md) ("Create the session first"), [src/ms_kb/skills/add-knowledge/references/note-types.md:7](src/ms_kb/skills/add-knowledge/references/note-types.md); US-24 "the conversation summary — `learning-session`" — [docs/personal-knowledge-user-stories-v1.md:179](docs/personal-knowledge-user-stories-v1.md); design §11.2 — [docs/personal-knowledge-design-v1.md:562](docs/personal-knowledge-design-v1.md); README — [README.md:27](README.md); the stage 2 "Done when" — [docs/personal-knowledge-roadmap-v1.md:89](docs/personal-knowledge-roadmap-v1.md).
- Duplicate checks deliberately exempt sessions ("dated and expected to repeat topics"), so sessions pile up by design. — [src/ms_kb/search.py:160-165](src/ms_kb/search.py), [docs/note-schema-v0.md:174](docs/note-schema-v0.md)

**(e) Learning profile as a dated, append-only log. Conflicts.**
- Sections `## Current directions`, `## Known topics`, `## Recently studied` (dated) and `## Open questions`; "The file stays append-only for `kb`; trimming it is up to the user". — [docs/note-schema-v0.md:107-132](docs/note-schema-v0.md); design §10 "it stays append-only user data" — [docs/personal-knowledge-design-v1.md:515](docs/personal-knowledge-design-v1.md)
- The skill appends `- <YYYY-MM-DD> — [[session]]` to `## Recently studied` on every run. — [src/ms_kb/skills/add-knowledge/SKILL.md:148-163](src/ms_kb/skills/add-knowledge/SKILL.md)
- `extend` on the profile accepts only section text (no links, topics or sources) and records no provenance. — [src/ms_kb/write.py:162-166](src/ms_kb/write.py), [src/ms_kb/write.py:197-208](src/ms_kb/write.py). `kb doctor` warns above 150 lines. — [src/ms_kb/cli.py:36](src/ms_kb/cli.py), [src/ms_kb/cli.py:283-285](src/ms_kb/cli.py)
- The profile is user data that `kb init` never silently recreates. — [src/ms_kb/vault.py:37-42](src/ms_kb/vault.py), [src/ms_kb/cli.py:86-101](src/ms_kb/cli.py)
- Real effect: the open question "когда to_thread, а когда run_in_executor" is still listed as open (`~/Knowledge/main/learning_profile.md:22`), although session 3 took it up (`learning-sessions/2026-10-11-python-concurrency-choice.md:28`, `:42-43`). Append-only has no way to close a question.

**(f) Frontmatter provenance (`created_by` / `updates`). Adds friction to rewrites and link edits.**
- "`updates` only grows: entries are added, never rewritten. The original `created_by` is never changed." — [docs/note-schema-v0.md:81](docs/note-schema-v0.md)
- With `--skill`, `extend` requires `--summary` and appends an `updates` entry of 6–7 lines (date, skill, skill_version, package_version, skill_ref, agent, summary). — [src/ms_kb/write.py:163-164](src/ms_kb/write.py), [src/ms_kb/write.py:197-202](src/ms_kb/write.py), [src/ms_kb/provenance.py:38-54](src/ms_kb/provenance.py). A link-only edit on a neighbour made with `--skill add-knowledge` therefore adds a full provenance entry to that neighbour.
- The same provenance is already in each commit's trailers. — [src/ms_kb/provenance.py:57-66](src/ms_kb/provenance.py), [src/ms_kb/cli.py:560-573](src/ms_kb/cli.py)
- Requirement behind it: US-12 (select notes by skill and version "without manually reading each note"; the original provenance distinguishable from the update provenance). — [docs/personal-knowledge-user-stories-v1.md:202-213](docs/personal-knowledge-user-stories-v1.md)
- In the vault, provenance is 7.5% of all note bytes and 11% (949 of 8951 bytes) of the most-updated page after two updates (see §4).

**(g) Plan gate. Usable, not a blocker.**
- "If you are going to extend at least one existing note, first show a short plan and **wait for the user's yes**". New-only runs skip it. — [src/ms_kb/skills/add-knowledge/SKILL.md:86-95](src/ms_kb/skills/add-knowledge/SKILL.md); design §11 — [docs/personal-knowledge-design-v1.md:537](docs/personal-knowledge-design-v1.md); decided in user stories v1.9 — [docs/personal-knowledge-user-stories-v1.md:417](docs/personal-knowledge-user-stories-v1.md)
- Karpathy also prefers to be involved during ingest: read the summaries, check the updates, guide emphasis. — [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

**(h) Confirmed/assumption marking. Supportive.**
- Each point is marked **confirmed** (a source opened in the conversation, a test or run, or the user's agreement) or **assumption**. Assumptions never go into concepts as fact. — [src/ms_kb/skills/add-knowledge/SKILL.md:43-48](src/ms_kb/skills/add-knowledge/SKILL.md), [src/ms_kb/skills/add-knowledge/SKILL.md:84](src/ms_kb/skills/add-knowledge/SKILL.md); US-24 — [docs/personal-knowledge-user-stories-v1.md:181](docs/personal-knowledge-user-stories-v1.md); US-09 — [docs/personal-knowledge-user-stories-v1.md:155](docs/personal-knowledge-user-stories-v1.md)

**(i) Duplicate checks. Supportive.**
- `kb new` refuses: the same file; the same file name in any folder (it would make `[[links]]` ambiguous); the same normalized title or alias within the type; and a similar title (`SequenceMatcher` ratio ≥ 0.85) unless `--allow-similar`. — [src/ms_kb/search.py:14](src/ms_kb/search.py), [src/ms_kb/search.py:149-186](src/ms_kb/search.py), [src/ms_kb/write.py:88-97](src/ms_kb/write.py)

**(j) Integrity "damaged" heuristic. Does not fire on kb rewrites, fires on outside rewrites.**
- `DAMAGE_RATIO = 0.5`. A tracked file is "damaged" when it is empty, smaller than half its manifest size, has frontmatter that no longer parses, or lost its frontmatter. The result is level `error` with hints `kb restore … --force` or `kb doctor --ack`. — [src/ms_kb/integrity.py:19](src/ms_kb/integrity.py), [src/ms_kb/integrity.py:41-54](src/ms_kb/integrity.py), [src/ms_kb/integrity.py:87-92](src/ms_kb/integrity.py); design §12.6 — [docs/personal-knowledge-design-v1.md:707](docs/personal-knowledge-design-v1.md); test — [tests/test_integrity.py:65-71](tests/test_integrity.py)
- The check runs only in `kb doctor` and in `kb validate` without paths, against the manifest. — [src/ms_kb/cli.py:298](src/ms_kb/cli.py), [src/ms_kb/cli.py:313-320](src/ms_kb/cli.py), [src/ms_kb/cli.py:689-694](src/ms_kb/cli.py)
- After every kb write, `_finish` re-records the manifest (hash and size after the write). — [src/ms_kb/cli.py:611](src/ms_kb/cli.py), [src/ms_kb/vaultstate.py:88-90](src/ms_kb/vaultstate.py). Any other change that does not look damaged is treated as a normal outside edit and refreshes the manifest. — [src/ms_kb/integrity.py:93](src/ms_kb/integrity.py)
- Consequence: a consolidating rewrite done through a future `kb` command would never be flagged, because the manifest already holds the new size. A rewrite done outside `kb` (by an agent with its own file tools, or by the user in Obsidian) that leaves less than half the bytes is reported as `damaged` (an error, exit code 1) until it is `--ack`ed. Example: the biggest page is 8951 bytes, so it would be flagged below 4476 bytes.
- Deleting a page outside `kb` (for example, after folding sessions into a topic page) gives one `deleted` error per file until `--ack`. — [src/ms_kb/integrity.py:95-106](src/ms_kb/integrity.py). Every link to that page then becomes a `[[target]] no longer resolves` warning, because the integrity check flags links that resolved before. — [src/ms_kb/integrity.py:110-114](src/ms_kb/integrity.py). Move detection matches by content hash, then by frontmatter `title`. — [src/ms_kb/integrity.py:95-100](src/ms_kb/integrity.py)

**(k) Neutral or helpful for targeted link edits.**
- `kb extend NEIGHBOUR --related TOPIC` already does an additive link edit. It adds `"[[TOPIC]]"` to frontmatter `related` (above the provenance blocks) and `- [[TOPIC]]` under `## Related`, and touches nothing else. — [src/ms_kb/write.py:183-189](src/ms_kb/write.py), [src/ms_kb/notes.py:114-132](src/ms_kb/notes.py). It cannot remove or rename a link, add an inline link inside prose, or change `title`.
- The secret scan checks only lines that are not already in the original, so a rewrite would be scanned on its changed lines. — [src/ms_kb/secretscan.py:35-47](src/ms_kb/secretscan.py)

### Inferences
- To allow "rewrite one page", the minimum change is a new write path through `_finish`, for example `kb rewrite PATH --body-file -` or `kb new --replace`. It would keep `created`/`created_by`, set `updated`, validate, scan for secrets, check `save()` concurrency, commit `kb: rewrite <path>` with trailers and record the manifest. Because append-only was part of the protection argument, the replacement needs its own guards: a diff in `--dry-run`, a report of removed `##` headings and removed `[[links]]`, a warning (or refusal without a flag) when the body shrinks below about 50% (the same ratio as the damage check, catching an LLM that truncates a page), and Git history as the undo.
- For "targeted link edits", the additive case already works (`extend --related`). Missing pieces: link removal, rename with backlink update, and merge with an alias redirect. Aliases are resolved by `links.Resolver` ([src/ms_kb/links.py:46-54](src/ms_kb/links.py)), so a merged page that gains the old title as an alias keeps old links resolving. Link edits should not require `--summary` or add a frontmatter `updates` entry; a commit trailer is enough.
- A rewrite-per-session workflow plus frontmatter `updates` that only grow would make the provenance block grow linearly with sessions. Moving provenance to Git trailers only (already written) and keeping at most `created_by` would remove the bloat, but US-12/US-13 and note-schema §3 must change.
- The plan gate fits the new workflow as "show the diff of the topic page plus the list of neighbour link edits, wait for yes". As written, it fires for every extend of an existing note, link-only edits included.

### Gaps
- No rewrite of real data was tried, so whether a typical consolidation shrinks a page below 50% is an estimate, not a measurement.
- Whether the user wants to keep `created_by` in frontmatter (for example for Obsidian Properties, Dataview or Bases queries) is not recorded anywhere.

## 3. What already exists that an LLM Wiki needs, and what is missing

### Takeaway
The pattern's safety and plumbing already exist: a Git repo with a commit per write and provenance trailers, restore, link resolution with aliases, detection of links that stopped resolving, validation, duplicate detection, a write lock and optimistic concurrency, and text and metadata search. Missing are the wiki-specific operations: an index/catalogue page, page rewrite, link removal/rename/merge, semantic lint (orphans, unlinked mentions, dangling links to pages that never existed, contradictions, stale claims), a lint skill, and filing query answers back. There is no raw-source layer, and the requirements explicitly avoid one. Git already covers `log.md`, and the user does not need a study log.

### Cited Findings
- LLM Wiki pattern, for reference ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)):
  - Three layers: **raw sources** (curated and immutable; the LLM reads them and never modifies them), **the wiki** (LLM-owned markdown pages: summaries, entity and concept pages, overview), **the schema** (CLAUDE.md/AGENTS.md describing structure and workflows, refined jointly).
  - **Ingest:** a summary page, an index update, relevant pages revised in place, a log entry. One source may touch "10-15 wiki pages".
  - **Query:** the LLM finds pages and synthesizes a cited answer; "good answers can be filed back into the wiki as new pages".
  - **Lint:** contradictions, stale claims, orphan pages, missing concept pages, missing cross-references, data gaps.
  - `index.md` is a catalogue (a link and a one-line summary per page), updated on every ingest and read first on queries. `log.md` is "an append-only record of what happened and when".
  - The wiki is "just a git repo of markdown files". Obsidian is the browsing IDE. The index is enough at small scale; at larger scale a search tool such as qmd.

Already present (with code):

| LLM-Wiki need | ms-kb today | Where |
|---|---|---|
| Search/retrieval | AND text terms, type, topic and dotted-field filters, title/alias/topic/body scoring, `--json`, no index | `src/ms_kb/search.py:79-143` |
| Link resolution | Obsidian rules: path suffix, file name, frontmatter `aliases`, case-insensitive; `[[a\|b]]`, `#heading` and `^block` handled | `src/ms_kb/links.py:1-54` |
| Broken-link detection | Only links that resolved at the last check and no longer do; known link targets stored in `vault-<kb>.json` | `src/ms_kb/integrity.py:110-135`, `src/ms_kb/vaultstate.py:1-7` |
| History/log | A commit per write (`kb: create\|extend <path>` plus trailers); outside edits as separate `external:` commits; `kb history` incl. deleted files | `src/ms_kb/history.py:149-178`, `src/ms_kb/history.py:208-232` |
| Undo | `kb restore` with a side file or `--force`, never silent | `src/ms_kb/cli.py:726-767` |
| Validation | Errors and warnings per type; unknown fields only warn | `src/ms_kb/schema.py:70-117` |
| Duplicate detection | Exact and similar titles and aliases, file-name clashes | `src/ms_kb/search.py:149-186` |
| Safe concurrent writes | Vault lock (`flock`, 30 s) and `save()` refusing if the file changed on disk | `src/ms_kb/vaultstate.py:50-68`, `src/ms_kb/write.py:222-223` |
| Off-machine copy | `kb sync` push, hourly LaunchAgent | `src/ms_kb/cli.py:377-420` |
| Additive cross-links | `--related` writes both frontmatter and `## Related` | `src/ms_kb/write.py:99-126`, `src/ms_kb/write.py:183-189` |
| Backlink lookup (partial) | `kb search --field "related=[[Note]]"`: frontmatter `related` only, not links in the body | `src/ms_kb/skills/kb-recall/SKILL.md:51`, `src/ms_kb/search.py:58-70` |
| Closest thing to `index.md` | Profile `## Known topics` (a concept link plus one line), filled by add-knowledge ≥ 0.4.0 for newly created concepts only | `docs/note-schema-v0.md:122-123`, `src/ms_kb/skills/add-knowledge/SKILL.md:150-163` |
| Human-side graph | The vault has Obsidian core plugins graph, backlink, outgoing-link, canvas and bases enabled | `~/Knowledge/main/.obsidian/core-plugins.json` |

Missing:
- **Index/catalogue page.** Nothing generates or maintains one. A root `index.md` would also be invisible to kb: `note_files` scans only the five type folders ([src/ms_kb/search.py:20-23](src/ms_kb/search.py)), the integrity manifest tracks only type folders plus the profile ([src/ms_kb/integrity.py:34-38](src/ms_kb/integrity.py)), and `validate` skips non-notes ([src/ms_kb/cli.py:673-675](src/ms_kb/cli.py)). There is no one-line `summary` frontmatter field to build an index from; an unknown field would only warn ([src/ms_kb/schema.py:108-111](src/ms_kb/schema.py)).
- **Rewrite/replace page command.** See §2(a).
- **Link-only edits beyond adding:** remove a link, rename a target and update backlinks, merge pages, delete a page. No delete command exists by design. — [docs/personal-knowledge-design-v1.md:607](docs/personal-knowledge-design-v1.md)
- **Semantic and graph lint.** No orphan detection (pages with no inbound links), no unlinked-mention detection (a title or alias in prose without `[[ ]]`), no report of dangling links to pages that never existed (only links that resolved before are flagged, [src/ms_kb/integrity.py:111](src/ms_kb/integrity.py)), no contradiction, stale-claim or duplicate-content checks, no page-size budget (the only size rule is the profile's 150 lines). Files outside the type folders are not checked at all.
- **A lint skill.** Only `add-knowledge` and `kb-recall` are bundled (`src/ms_kb/skills/`), and the user-stories backlog names no lint skill ([docs/personal-knowledge-roadmap-v1.md:173-187](docs/personal-knowledge-roadmap-v1.md)).
- **Raw-source folder.** None in the vault layout ([docs/note-schema-v0.md:85-98](docs/note-schema-v0.md)). The requirements exclude it by default: "The full content of an article, document or website is not copied by default" ([docs/personal-knowledge-user-stories-v1.md:68](docs/personal-knowledge-user-stories-v1.md)) and "Obsidian stores knowledge, not the world" ([docs/personal-knowledge-design-v1.md:36](docs/personal-knowledge-design-v1.md)). The conversation, the actual source, is ephemeral. Context compaction is flagged as a limitation ([docs/personal-knowledge-design-v1.md:567](docs/personal-knowledge-design-v1.md), [src/ms_kb/skills/add-knowledge/SKILL.md:50](src/ms_kb/skills/add-knowledge/SKILL.md)).
- **Filing query answers back.** `kb-recall` never writes and only suggests `add-knowledge` ([src/ms_kb/skills/kb-recall/SKILL.md:82-84](src/ms_kb/skills/kb-recall/SKILL.md)), consistent with the "write only on explicit command" policy ([docs/personal-knowledge-design-v1.md:537](docs/personal-knowledge-design-v1.md)).
- **`log.md`.** None, but `git log` with `Kb-Skill` trailers plays this role ([src/ms_kb/history.py:210](src/ms_kb/history.py)), and the user does not need a study-by-date log.

### Inferences
- Under the user's intent the natural mapping is: the conversation as an ephemeral raw source (no raw folder), topic pages as the wiki, the skills plus note schema plus global instruction as the schema layer, `index.md` (or a renamed profile) as the entry point `kb-recall` reads first, and Git as the log.
- The index could be generated deterministically by the CLI from frontmatter (`title`, a new one-line `summary`, `topics`) instead of being hand-maintained by the LLM. That follows the design's split between code and LLM ([docs/personal-knowledge-design-v1.md:481](docs/personal-knowledge-design-v1.md)) and can never drift.
- Graph lint (orphans, dangling and unlinked mentions, duplicate titles, oversize pages, files outside type folders) is code-checkable and belongs in `kb lint`/`kb doctor`. Contradictions, stale claims and missing pages need a `kb-lint` skill that proposes edits behind the plan gate.

### Gaps
- The rest of the gist page (characters after 100,000, mostly comments) was not read. The pattern summary relies on the fetch tool's extraction of the main text.

## 4. The user's real vault at `~/Knowledge/main`

### Takeaway
The vault is tiny: 6 notes plus the profile, 32.5 KB, one topic cluster (Python concurrency). Learning-session logs are half the notes and 46% of the bytes. About 16% of bytes is frontmatter, and 7.5% is provenance. Sessions and concepts overlap visibly: the same rules, lists and assumptions appear in both. Assumptions are heavy: 21 bullets in sessions plus 4 callouts in concepts. Prose is mostly Russian under English headings and English concept titles. The profile is a dated log with empty `Known topics` and `Current directions` and stale open questions. Migrating to a topic-page model now would be cheap.

### Cited Findings
- Files: 3 concepts, 3 learning sessions, the profile, `README.md`, 5 templates, `.gitignore`, `.obsidian/`, and a stray **0-byte `2026-10-09.md` at the vault root** (dated 2026-10-09 19:44; the Obsidian daily-notes core plugin is enabled in `.obsidian/core-plugins.json`). `research/`, `sources/`, `projects/` and `attachments/` are empty. — directory listing of `~/Knowledge/main`
- Per-note numbers. Script counts; "fm" is the frontmatter including `---`, "prov" is the `created_by`/`updates` block, "links" counts `[[ ]]` occurrences, "assump" is `[!question] Assumption` callouts (c) and `## Assumptions (not confirmed)` bullets (b), "cyr%" is the Cyrillic share of letters in the body:

| Note | Lines | Bytes | fm % | prov % | Links | Assump | cyr % | Manifest writer |
|---|---|---|---|---|---|---|---|---|
| `concepts/Concurrency vs parallelism.md` | 67 | 3243 | 19 | 7 | 7 | 0c | 69 | seed |
| `concepts/Global Interpreter Lock.md` | 65 | 3991 | 26 | 15 | 8 | 1c | 71 | kb restore |
| `concepts/Python concurrency models.md` | 109 | 8951 | 17 | 11 | 14 | 3c | 61 | kb extend |
| `learning-sessions/2026-10-10-python-concurrency.md` | 57 | 4059 | 15 | 6 | 4 | 6b | 65 | seed |
| `learning-sessions/2026-10-10-threading-vs-asyncio.md` | 58 | 4846 | 15 | 5 | 9 | 5b | 70 | external |
| `learning-sessions/2026-10-11-python-concurrency-choice.md` | 62 | 6118 | 10 | 4 | 11 | 10b | 61 | kb create |
| `learning_profile.md` | 24 | 1320 | 4 | 0 | 8 | — | 43 | kb extend |
| **Total** | 442 | 32528 | **15.9** | **7.5** | 61 | 4c / 21b | — | — |

  Sources: the files themselves; writers from `~/.config/ms-kb/vault-main.json`.
- Share by type: sessions 15,023 bytes (46%), concepts 16,185 (50%), profile 1,320 (4%).
- All six notes have exactly `topics: [python, concurrency]` (or reversed): one topic cluster. — the frontmatter of each note
- Every `related` link is stored twice, in frontmatter `related` and as a bullet under `## Related`, because `--related` writes both ([src/ms_kb/write.py:99-126](src/ms_kb/write.py)). Counts: 22 frontmatter links, 22 `## Related` bullets, 9 inline prose links in notes plus 8 in the profile.
- Link graph: the three concepts link each other (a clique) and each concept links to 1–2 sessions. Inbound links: GIL 5, Python concurrency models 5, Concurrency vs parallelism 4, sessions 5/5/2. No broken links; the manifest's resolved targets are the six notes. — script count; `~/.config/ms-kb/vault-main.json` (`links`)
- Provenance: 6 `created_by` blocks, 3 `updates` entries (GIL 1, PCM 2). The latest update and session 3 carry `skill_version: "0.5.0"` with `package_version: "0.4.0"` and a `skill_ref` at `v0.4.0`, an internally inconsistent stamp from a skill/CLI mismatch during stage 4 testing. — `~/Knowledge/main/concepts/Python concurrency models.md:35-41`, `~/Knowledge/main/learning-sessions/2026-10-11-python-concurrency-choice.md:15-21`
- Duplication between sessions and concepts (examples):
  - The "Правило выбора в 3 шага" (3-step choice rule) appears in session 3 (`2026-10-11-python-concurrency-choice.md:33-36`) and as a single bullet in `Python concurrency models.md:98`. An earlier form is also in session 1 (`2026-10-10-python-concurrency.md:40`) and in the concept's Mermaid diagram (`Python concurrency models.md:72-82`).
  - "Ни один из подходов не устарел…" (none of the approaches is obsolete): session 3 `:37` vs concept `:99` (line similarity 0.81). Interchangeability: session 3 `:38` vs concept `:100`. The ThreadPool/ProcessPool one-line swap: session 3 `:39` vs concept `:101`.
  - The list of deprecated APIs: session 3 assumption `:50` vs concept assumption callout `:92`.
  - GIL facts: session 1 conclusions `:34-39` vs `Global Interpreter Lock.md:38-47`. The assumption "не все C-расширения совместимы с free-threaded" (not all C extensions support free-threading) appears three times: `Global Interpreter Lock.md:54`, session 1 `:47`, session 3 `:51`.
  - "Потоки «легковесны» только по сравнению с процессами" (threads are "lightweight" only compared with processes): session 2 `:43` vs concept `:97`.
  - Script result: 10 of 57 long (≥ 40 characters) session lines have a counterpart with similarity ≥ 0.5 in a concept page. One match is a false positive (a "Продолжение [[…]]" line), and multi-line rules collapsed into one bullet are not caught, so this is a rough lower bound.
- Internal staleness caused by append-only: see §2(a) (`Python concurrency models.md:69-70` vs `:86`) and §2(e) (the profile's open question at `:22`).
- Confirmation marking: inline "(подтверждено: …)" ("confirmed: …") markers appear 5× in PCM, 6× in session 1, 6× in session 2, 1× in GIL, and 0× in session 3. There is one non-standard `[!note] Подтверждено` callout and no `[!warning] Contradiction` callouts. — script count
- Language: body text is 61–71% Cyrillic letters per note. All `##` headings are English, from the templates (`Explanation`, `Limitations`, `Insights`, `Topics`, `Conclusions`, …), except one appended `### threading против asyncio`. Concept titles are English; session titles are Russian. Topics and session slugs are ASCII, as the schema requires. — the files; [src/ms_kb/schema.py:92-96](src/ms_kb/schema.py), [src/ms_kb/notes.py:88-103](src/ms_kb/notes.py)
- Profile (`~/Knowledge/main/learning_profile.md:1-24`): 24 lines. `## Current directions` and `## Known topics` are empty (the concepts were created by add-knowledge 0.3.0, before 0.4.0 added the Known-topics rule, [docs/personal-knowledge-roadmap-v1.md:98](docs/personal-knowledge-roadmap-v1.md)). `## Recently studied` has 3 dated session links. `## Open questions` has 5, one of them already addressed (§2(e)), and one open question from session 2 (`2026-10-10-threading-vs-asyncio.md:51`) never reached the profile.
- History since the vault became a Git repo (2026-10-11): 5 HEAD entries. `kb: init vault`, then one add-knowledge run producing three commits (`create learning-sessions/2026-10-11-…`, `extend concepts/Python concurrency models.md`, `extend learning_profile.md`), then `external: 1 file changed outside kb`. — `~/Knowledge/main/.git/logs/HEAD` (read as a file); hands-on log at [docs/clients-v0.md:95-109](docs/clients-v0.md)
- The GIL note's manifest writer is `kb restore`, left over from the stage 4 deletion and restore test. — `~/.config/ms-kb/vault-main.json`; [docs/clients-v0.md:105](docs/clients-v0.md)

### Inferences
- Under the new intent the cluster would become one consolidated topic page ("Python concurrency", today's `Python concurrency models` already acts as the hub). `Global Interpreter Lock` and `Concurrency vs parallelism` would stay either as linked neighbour pages or as sections. The three sessions would be folded in and then removed or archived. With 6 notes, a one-off migration is cheap now and gets more expensive with every add-knowledge run, since each run adds a session and 1–3 commits.
- The concept→session links (each concept lists 1–2 session notes in `related`) would turn into "no longer resolves" warnings if the sessions are deleted (§2(j)). A migration would have to remove those links in the same step.
- The 21 session assumption bullets and 4 concept callouts largely repeat each other. A rewrite could collapse them into one `## Open questions / unverified` section per topic page and drop the ones later confirmed (for example, the asyncio claim).
- Mixed language is a design choice to settle: English template headings over Russian prose. The `kb-recall` skill locates sections by English heading names ([src/ms_kb/skills/kb-recall/SKILL.md:55-59](src/ms_kb/skills/kb-recall/SKILL.md)).

### Gaps
- Whether the root `2026-10-09.md` was committed in `kb: init vault` was not checked, because that would need `git`.
- Whether Obsidian Sync is actually in use is unknown: `"sync": true` in `core-plugins.json` only shows the core plugin is enabled.

## 5. Which user stories and roadmap items would need to change, be dropped or be frozen

### Takeaway
The infrastructure stories (US-17–US-23, and US-20 in particular, whose history and restore make rewrites acceptable) are unaffected. The stories that define the write model must change: US-04 (types), US-09 (profile), US-10 (extend without repeating, contradictions), US-12/US-13 (provenance, revision) and US-24 (distribution across types, one learning-session). US-02/US-03 (sources, dated research) are better frozen as optional. In the roadmap: superseded stage 2/3 "done when" criteria, a stage 5 item on provenance queries to freeze or re-base on Git, backlog items to freeze, and new items for rewrite, link edits, index, lint and migration.

### Cited Findings

| US | Current text (key line) | Under the new intent | Verdict |
|---|---|---|---|
| US-01 | One store of knowledge in Obsidian — [user-stories:49-58](docs/personal-knowledge-user-stories-v1.md) | Unchanged | keep |
| US-02 | Source note = link + short summary; full content not copied — [:60-70](docs/personal-knowledge-user-stories-v1.md) | The ingest source is the conversation; a raw-source layer is not needed. Source notes become optional | keep, freeze its skill (backlog "save-source") |
| US-03 | Research with a date, "not presented as timeless" — [:72-82](docs/personal-knowledge-user-stories-v1.md) | Topic pages are timeless, rewritten consolidations. A dated comparison either becomes a dated section of a topic page or stays an optional `research` type | change or freeze |
| US-04 | Five base types incl. `learning-session` — [:84-94](docs/personal-knowledge-user-stories-v1.md) | A topic page type (or `concept` renamed), possibly `source`/`project`; `learning-session` dropped from the write path | change |
| US-05/06/14 | External systems, source registry — [:96-118](docs/personal-knowledge-user-stories-v1.md), [:230-241](docs/personal-knowledge-user-stories-v1.md) | Not affected | freeze (already backlog) |
| US-07 | Continue learning: "takes previous discussions and remaining questions into account" — [:122-132](docs/personal-knowledge-user-stories-v1.md) | Read the index, then the topic page and its open questions, not session history | change (retrieval path); keep the criteria |
| US-08 | Selective search and reading — [:134-144](docs/personal-knowledge-user-stories-v1.md) | Add an index-first step; semantic search stays post-MVP (the gist: an index is enough at small scale) | keep |
| US-09 | Profile with "recently studied material", recorded vs assumed — [:146-156](docs/personal-knowledge-user-stories-v1.md) | Drop "recently studied" (no study history). Open questions move onto topic pages or become editable. The profile becomes or merges with the index | change |
| US-10 | "extends it … without repeating"; "Contradictions … flagged; an update does not erase the basis … without explanation"; "learning session summary" — [:158-169](docs/personal-knowledge-user-stories-v1.md) | Consolidate in place; contradictions resolved with an explanation (in the page or the commit); no session summary; keep write-on-command (:169) and "index reflects new content" (:168) | change substantially |
| US-11 | Rules via skills; "rules for finding existing notes, extending them and merging without duplication" — [:189-200](docs/personal-knowledge-user-stories-v1.md) | Supports the change; add a lint skill | keep and extend |
| US-12 | Provenance in notes; select by skill/version "without manually reading each note"; original vs update distinguishable — [:202-213](docs/personal-knowledge-user-stories-v1.md) | Satisfiable through Git trailers (`kb history` already parses `Kb-Skill`). Frontmatter `updates` would bloat on rewrites | change (where provenance lives) |
| US-13 | Revise materials; "does not change the original creation date"; history = vault Git — [:215-226](docs/personal-knowledge-user-stories-v1.md) | Revision becomes the normal path; keep `created`; Git history stays | change (simplifies) |
| US-15 | Shared rules for different agents — [:243-254](docs/personal-knowledge-user-stories-v1.md) | Unchanged; the new skills must stay portable | keep |
| US-16 | Visual notes; "Canvas … for an overview of a large topic"; graph — [:258-269](docs/personal-knowledge-user-stories-v1.md) | Supports the index and explicit links | keep |
| US-17–US-19, US-21–US-23 | Package, skills scope, separate vault, multiple KBs, other users, CI — [:273-384](docs/personal-knowledge-user-stories-v1.md) | Not affected | keep (US-21/22 stay post-MVP) |
| US-20 | Own history, restore, off-machine copy — [:320-340](docs/personal-knowledge-user-stories-v1.md) | The safety net that makes in-place rewrites acceptable | keep |
| US-24 | Distribute across types, "conversation summary — `learning-session`"; mark assumptions; provenance; list changed files; whole or part of the conversation — [:171-185](docs/personal-knowledge-user-stories-v1.md) | One topic page rewritten plus targeted neighbour link edits; keep assumption marking, the file report and partial saves; provenance through Git | change substantially |

- Rows in the "typical scenarios" table that change: "Compile this conversation…" (`add-knowledge` creating/extending), "Let's continue studying RAG", "Which notes were created by the old skill?" and "Update the research with the new skill". — [docs/personal-knowledge-user-stories-v1.md:390](docs/personal-knowledge-user-stories-v1.md), [:393](docs/personal-knowledge-user-stories-v1.md), [:396-397](docs/personal-knowledge-user-stories-v1.md)
- Roadmap:
  - Stage 2 "Done when … creates a `learning-session` and creates or extends `concept` notes … a repeated invocation … extends rather than duplicates" is superseded by "rewrites the topic page". — [docs/personal-knowledge-roadmap-v1.md:89](docs/personal-knowledge-roadmap-v1.md)
  - Stage 3: `kb-recall` reads the profile first, and `add-knowledge` 0.4.0 adds concepts to `## Known topics`. Both move to index-first. — [docs/personal-knowledge-roadmap-v1.md:95-100](docs/personal-knowledge-roadmap-v1.md)
  - Stage 5: keep CI and the Codex/Cursor hands-on checks. "Provenance queries: `kb search --skill --version`, finding research as of a date (US-12, US-13)" should be frozen or re-based on Git trailers. — [docs/personal-knowledge-roadmap-v1.md:159-165](docs/personal-knowledge-roadmap-v1.md)
  - Backlog: "`save-source` and `research` skills" freeze; "Revision under new rules" is subsumed by rewrite; "Librarian subagent" and "Semantic/hybrid search" freeze (vault of 6 notes); "Hook reminder before context compaction" keep (it still protects the ephemeral source); "Stronger vault protection … a stable note `id` for move detection" becomes relevant for rename and merge. — [docs/personal-knowledge-roadmap-v1.md:173-187](docs/personal-knowledge-roadmap-v1.md)
  - The risk "Duplicates and knowledge 'smeared' across notes" is what the new workflow addresses directly. — [docs/personal-knowledge-roadmap-v1.md:195](docs/personal-knowledge-roadmap-v1.md)
- Design sections that state the old model and would need edits: §5.1 types ([:161-173](docs/personal-knowledge-design-v1.md)), §6.4 ([:312-316](docs/personal-knowledge-design-v1.md)), §9.1 "The CLI writes the notes … append" ([:497](docs/personal-knowledge-design-v1.md)), §10 profile ([:515](docs/personal-knowledge-design-v1.md)), §11 write policy and plan ([:519-539](docs/personal-knowledge-design-v1.md)), §11.1 "Update/merge" ([:550](docs/personal-knowledge-design-v1.md); already allows "revise" in principle), §11.2 add-knowledge ([:557-569](docs/personal-knowledge-design-v1.md)), §12.4 trust boundary and "no delete" ([:668-672](docs/personal-knowledge-design-v1.md)), §12.6 damaged-vs-changed ([:707](docs/personal-knowledge-design-v1.md)), §14 rows ([:733-735](docs/personal-knowledge-design-v1.md)). Also note-schema §2/§3/§5/§7 ([docs/note-schema-v0.md:36-46](docs/note-schema-v0.md), [:48-81](docs/note-schema-v0.md), [:107-132](docs/note-schema-v0.md), [:166-192](docs/note-schema-v0.md)), README ([README.md:25-31](README.md), [README.md:88](README.md)) and the project CLAUDE.md "Write" bullet.

### Inferences
- New roadmap items implied by the intent (none exist today): (1) note-schema v1 with a topic page type, an optional one-line `summary`, and provenance in Git; (2) `kb rewrite` (or `new --replace`) with diff, shrink and lost-links guards; (3) link edits: unlink, rename with backlinks, merge with an alias redirect, and `kb delete` or archive (a reversal of design §12.4 "no delete"); (4) a generated `index.md` read first by `kb-recall`; (5) `kb lint` (orphans, dangling and unlinked mentions, oversize pages, files outside type folders) plus a `kb-lint` skill for semantic checks; (6) rewriting `add-knowledge` around "one topic page + neighbour links" and retiring `learning-session`; (7) a one-off migration of the existing 6 notes; (8) updated CI smoke and tests (for example, `tests/test_write.py:121-123` asserts append-only).
- Docs need version bumps and changelog entries per the project convention: each doc has a `document_version`, and stages end with a release commit.

### Gaps
- The user's decisions about `research`, `source` and `project` types, and about where open questions live (topic page vs index or profile), are not recorded. The verdicts for US-02, US-03 and US-09 are therefore conditional.
- Whether frontmatter provenance must stay for Obsidian-side queries (Bases is enabled in the vault) is unknown.
