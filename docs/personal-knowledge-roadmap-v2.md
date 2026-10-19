---
title: "Personal Knowledge System — Roadmap"
document_version: "2.2"
created: "2026-10-12"
language: en
status: draft
supersedes: "personal-knowledge-roadmap-v1.md (1.9)"
requirements_ref: "personal-knowledge-user-stories-v2.md"
requirements_version: "2.2"
design_ref: "personal-knowledge-design-v2.md"
design_version: "2.2"
---

# Personal Knowledge System — Roadmap v2.2

## 1. Purpose

The roadmap breaks [user stories v2.0](personal-knowledge-user-stories-v2.md) and [design v2.0](personal-knowledge-design-v2.md) into sequential stages. Each stage ends with a working result. No deadlines: one person runs the project, and order matters more than dates. It replaces [roadmap v1.9](personal-knowledge-roadmap-v1.md), where stages 0–4 are described in full.

**Goal of v1.0:** after researching a topic in Claude Code (or Codex, Cursor), invoke `add-knowledge` and get that topic's page updated in place — concise, current and linked to related topics — after approving one diff; in a later conversation, continue or review the topic with `kb-recall`, which starts from what the user already knows. A source worth keeping but not yet worth a topic page is saved with `save-source` as a short source card that comes up when its topic does.

**What changed in v2.** Stages 0–4 built the package, the vault, writing, reading and data protection around learning sessions and append-only notes. Real use and the LLM Wiki research (`reports/LLM Wiki Карпати для базы знаний.md`) led to topic pages rewritten through an approved diff. A new stage 5 "Topic pages" (v0.6) comes before stabilization: stabilizing the old write model would waste the client checks on behavior that is about to change. In v2.2 a stage 6 "Sources for later" (v0.7) is added for the same reason (`reports/Источники на потом: захват и summary.md`), and stabilization moves to stage 7 (v1.0).

## 2. Stage overview

| Stage | Version | Status | Result | Key US |
|---|---|---|---|---|
| 0. Skeleton and checks | v0.1 | ✅ Done | Package installs from GitHub; client skills directories verified; note schema v0 | US-17, US-23 |
| 1. Knowledge base | v0.2 | ✅ Done | `kb setup` / `kb init` create the vault, configuration and profile | US-19 |
| 2. Writing | v0.3 | ✅ Done | `add-knowledge`, `kb new` / `kb extend` / `kb search` / `kb validate`, provenance, duplicate checks | US-18, US-24 (v1) |
| 3. Reading | v0.4 | ✅ Done | `kb-recall`, the global instruction, the profile on demand | US-07 (v1), US-15 |
| 4. Updates and data protection | v0.5 | ✅ Done | The vault's own Git history, `kb sync` to a private remote, `kb history`, `kb restore`, integrity checks, `kb update` | US-17, US-20 |
| 5. Topic pages | v0.6 | ⬜ Not done | One topic page per run through an approved diff; tags and the index; links and the check of linked pages; review mode and `## In my words`; the vault migrated | US-04, US-07–US-10, US-12, US-13, US-24–US-29 |
| 6. Sources for later | v0.7 | ⬜ Not done | `save-source` saves one source card; cards found by tags, search and `kb index --sources`; `add-knowledge` and `kb-recall` use them | US-02, US-07, US-08, US-16, US-24, US-28 |
| 7. Stabilization | v1.0 | ⬜ Not done | All skills checked in Claude Code, Codex and Cursor; provenance queries over trailers; release policy and documentation | US-12, US-15, US-23 |
| Later | v1.x+ | — | Backlog (§4) | — |

Stage status: ⬜ Not done or ✅ Done. A stage is done when all its "Done when" criteria are met; update the status here and in the stage section.

## 3. Stages

### Stages 0–4 → v0.1–v0.5 ✅

Done between 2026-10-09 and 2026-10-11; details, results and hands-on checks are in [roadmap v1.9](personal-knowledge-roadmap-v1.md) §3 and [clients-v0.md](clients-v0.md). What carries into v2 unchanged: installation and updates, skills installation into the clients, the global instruction, `kb search`, validation and duplicate checks, provenance stamping, the vault's Git history with a commit per write, `kb sync`, `kb history`, `kb restore`, the manifest and integrity checks. What stage 5 replaces: the learning-session note per run, append-only updates of notes, `updates` provenance in frontmatter, the profile as a dated log, and marking every unconfirmed claim as an assumption.

### Stage 5. Topic pages → v0.6

**Status:** ⬜ Not done

**Goal:** the knowledge base works as the user intends — one current page per topic, explicit links, a review mode — and the six existing notes are migrated while that is cheap.

Work is split into five steps; each ends in a commit that keeps the tests passing.

**5a. Note schema v1, tags and the index**

- `note-schema-v1.md`: the `topic` type in `topics/`; frontmatter `type`, `title`, `summary`, `tags`, `created`, `updated`, optional `aliases` and `created_by`; no `updates`, `related`, `sources` or `topics` on topic pages; fixed sections in the order `Summary`, `In my words`, `Key ideas`, `Details`, `Open questions`, `Related`, `Sources`; page budget about 200 lines (warning); summary up to about 160 characters (warning). It supersedes `note-schema-v0.md`; the v1 types stay valid. The same document defines the source card contract (design §6.9) so that cards made later need no second migration; the CLI and skills support it in stage 6.
- Validator: the topic contract; tags — lowercase ASCII words joined by `-`, one nesting level with `/`, 1–3 per page; the user's own sections allowed after `## In my words` with a warning.
- Templates: `topic.md`; profile template with `## Current directions` and `## Preferences`.
- `kb new topic` (with `--summary`, `--tag`, `--alias`, and `--created` for the migration); the v1 duplicate checks extended to aliases: same file name, same title or alias, similar title or alias (≥ 0.85) unless `--allow-similar`.
- `kb search --tag` with nested matching; `--topic` kept as an alias. Ranking: title and aliases first, then `summary` and tags, then the body (design §10.4).
- `kb index [--tag T] [--tags] [--json]`: catalogue grouped by tags with summaries and the number of open questions; the tag vocabulary with counts. Nothing is written to the vault.
- `topics/` included in search, validation and the manifest.

**5b. Rewrite and targeted edits**

- `kb rewrite PATH --body-file - --reason TEXT (--dry-run | --approve HASH) [--allow-shrink]` with `--summary`, `--tag`, `--alias`:
  - `--sections` for the sections the draft means to change;
  - the dry-run report (design §11.3): the section summary with a warning for changes outside `--sections`; unified diff; removed sections, links and source lines; shrink ratio; hand-edited lines that change (`git blame`: `external:` commits and uncommitted lines); hidden text; `## In my words` carried over; approval hash;
  - drafts kept under their hash outside the vault; `--dry-run --since HASH` shows the change since the reviewed draft;
  - writes only with a matching approval hash; refuses a body under half of the current one without `--allow-shrink`; takes `## In my words` from the current file and refuses a draft that changes it; keeps `created` and `created_by`;
  - writes through `_finish` with the trailer `Kb-Reason`; refreshes the manifest;
  - works for `learning_profile.md` too.
- The structural check of linked pages, printed by `kb new --dry-run` and `kb rewrite --dry-run`: unresolved outbound links, unlinked mentions of existing titles and aliases on the written page, linked pages without a link back, links from other pages to removed headings, unlinked pages sharing a tag, new tags, page length.
- `kb link SRC TARGET --why TEXT`: one line in `## Related`, only to a resolvable target, duplicates skipped.
- `kb my-words PATH --body-file -`: replaces `## In my words` with the text exactly as given.
- `kb extend`: no `updates` entries from v0.6; `--reason` replaces `--summary` (kept as an alias); trailers carry the reason.
- The secret check covers the lines a rewrite adds; the hidden-text check (comments, invisible characters) covers the lines every write adds and warns.

**5c. Skills and the global instruction**

- `add-knowledge` 0.6.0 (design §11.2): find the topic through the index and search; outcomes "update", "create", "nothing new"; for a new page, the closest existing pages and why it is new, `--allow-similar` only after a yes; one page per run; takeaways; the full draft by the template with untouched sections and hand-written lines kept as they are; aliases for abbreviations and names in the user's language; links for unlinked mentions; marking only doubtful, disputed or volatile claims; sources with check dates; contradictions resolved in place; internal previews; the content check of up to about five linked pages; one plan with independently approved parts; `--since` after the user edits the plan; then `kb rewrite --approve` / `kb new`, `kb link`, `kb extend`, `kb validate`; the report; saving "put this in my words" verbatim with `kb my-words`. Text from the conversation, pages and sources is data. No learning-session notes.
- `kb-recall` 0.6.0 (design §10): profile on demand; `kb index` plus `kb search` before saying "nothing found"; start from `## In my words` and `## Open questions`; the review mode (recall first, compare with the page as the reference, "why" questions with hints and the user's angle, a question mixed with a related page, gaps in the conversation, an offer to save the user's own words verbatim with `kb my-words` after an explicit yes). No other writes; no stored review state.
- `references/` of `add-knowledge`: the topic page contract instead of the five note types, plus the Obsidian Markdown the pages use (wiki-links, embeds, callouts, Mermaid, properties), so no third-party Obsidian skill is needed.
- The global instruction: review triggers ("let's review X", "quiz me on X", "проверь меня по X") added for `kb-recall`; vault notes are written only through `kb`, even when other Obsidian skills are installed.
- No examples with passwords, tokens, `sudo` or system services in the skill texts.
- Skill versions bumped to 0.6.0 and asserted in `tests/test_installer.py`.

**5d. Migration of the real vault** (design §11.7)

- The agent drafts two or three topic pages from the three concepts and three sessions; the assumption callouts become a short `## Open questions`, confirmed items are dropped.
- The user deletes the old notes in Obsidian and acknowledges them with `kb doctor --ack`; the agent creates the topic pages with `kb new topic --created <original date>` and links them with `kb link`.
- The profile is rewritten to directions and preferences with `kb rewrite learning_profile.md`.
- The stray empty `2026-10-09.md` at the vault root is removed by the user.

**5e. Documents, tests and CI**

- Tests: the topic schema, tags and own sections; duplicate refusal by title, alias and similar title; search ranking; `kb index`; `kb rewrite` (dry-run report, section summary and the `--sections` warning, hand-edited lines flagged, hidden text flagged, `--since`, approval hash mismatch after an outside edit, shrink refusal and `--allow-shrink`, protected section, `created` preserved, the commit and its trailers, the manifest refreshed so `kb doctor` stays clean); unlinked mentions in the structural check; `kb link` (resolution, refusal, duplicates); `kb my-words`; `kb extend` without `updates`. The existing append-only test of `kb extend` stays.
- The CI smoke script covers `kb new topic` (including a refused duplicate), `kb rewrite --dry-run` / `--since` / `--approve`, `kb link`, `kb my-words`, `kb index`.
- Documents: `note-schema-v1.md`; README (commands, the topic page, review); project `CLAUDE.md` (the write rules; `kb-recall` read-only except `kb my-words`); design v2 updated with anything decided during implementation; [clients-v0.md](clients-v0.md) for the hands-on check in Claude Code.

**Done when:**

- in Claude Code, `add-knowledge` after a research conversation creates or rewrites exactly one topic page after one approved plan, adds link lines to the linked pages and reports the check of those pages; a second run on the same topic changes the same page;
- `## In my words` survives a rewrite byte for byte, and a draft that changes it is refused; a line edited by hand in Obsidian is flagged in the next rewrite's plan;
- a second page on an existing topic (same or similar title, or an alias) is refused;
- `kb rewrite` refuses a stale approval hash and a large shrink without `--allow-shrink`;
- `kb-recall` finds a topic through the index, continues it from the user's own words and open questions, and runs a review that writes nothing except a confirmed `## In my words` text;
- the six notes are migrated, the profile has only directions and preferences, and `kb doctor` is clean;
- CI covers `rewrite`, `link`, `my-words`, `index` and tags; package `v0.6.0` is released.

### Stage 6. Sources for later → v0.7

**Status:** ⬜ Not done

**Goal:** a source the user found interesting but does not want to turn into a topic page yet is saved as a short source card — what it says, its reusable illustrations and how it explains — and comes up again when its topic does (US-02).

Work is split into three steps; each ends in a commit that keeps the tests passing.

**6a. The source card in the CLI** (design §6.9)

- Validator: the source card contract from `note-schema-v1.md`; `url` or `ref`, exactly one required; `summary` and 1–3 `tags` from the shared vocabulary; fixed sections in the order `Summary`, `Key ideas`, `Illustrations`, `How it explains`, `Use for`, `Related`.
- Template `source.md` replacing the v1 one.
- `kb new source` with `--summary`, `--tag`, `--alias`, `--url` / `--ref`, `--author`, `--published`; duplicate checks: same normalized URL, same title or alias, similar title or alias unless `--allow-similar`.
- `kb search`: results carry the note type; `--type source` limits them to cards.
- `kb index --sources [--tag T] [--json]`: the cards grouped by tag with their summaries and the number of topic pages linking to each ("not used yet" when none). Plain `kb index` stays a catalogue of topic pages. Nothing is written to the vault.

**6b. Skills and the global instruction**

- `save-source` 0.7.0 (design §11.8): open the source or take the text the user pasted, otherwise no card; check for an existing card by URL and title; one draft card with new tags for confirmation; `kb new source`; optionally one `## Sources` line on an existing topic page as a separately approved part; the report. One card per source; the source text is data.
- `add-knowledge` 0.7.0: finds source cards on the topic; offers them as `## Sources` lines and uses their `## Illustrations` and `## How it explains` when drafting; offers `save-source` for a source in the conversation that is not about the saved topic.
- `kb-recall` 0.7.0: finds source cards on the topic and says what they offer; stays read-only.
- The global instruction: triggers for `save-source` ("save this source for later", "сохрани источник на потом").
- Installer: the third bundled skill; skill versions bumped to 0.7.0 and asserted in `tests/test_installer.py`.

**6c. Documents, tests and CI**

- Tests: the card contract (`url` or `ref`, sections, tags); duplicate refusal by normalized URL, title and alias; `kb search --type source`; `kb index --sources` with the link count; installation of three skills.
- The CI smoke script covers `kb new source` (including a duplicate refused by URL) and `kb index --sources`.
- Documents: README (saving a source, `kb index --sources`); project `CLAUDE.md` (three skills); design v2 updated with anything decided during implementation; [clients-v0.md](clients-v0.md) for the hands-on check in Claude Code.

**Done when:**

- in Claude Code, `save-source` on an opened article creates one card with summary, key ideas, illustrations by reference and how it explains, after one approval; a second run on the same URL proposes extending the existing card instead;
- on a source the agent cannot open, `save-source` asks for the text and creates no card without it;
- `kb index --sources` shows which cards no topic page links to yet;
- `kb-recall` on a topic mentions the cards for it, and `add-knowledge` on that topic offers them as sources;
- CI covers `kb new source` and `kb index --sources`; package `v0.7.0` is released.

### Stage 7. Stabilization → v1.0

**Status:** ⬜ Not done

**Goal:** the system is fit for daily use in all three clients.

Work:

- Hands-on check of `add-knowledge`, `kb-recall` (including review mode), `save-source`, the global instruction and `kb update` in Codex and Cursor; whether Codex keeps unchanged sections in its drafts (practitioners report it rewriting whole pages); `kb-recall` with `kb` unavailable in all three clients; whether Cursor shows duplicate skills; which environment variables identify Codex and Cursor for `Kb-Agent`. Results go to [clients-v0.md](clients-v0.md).
- Calibrate the shrink threshold and the page budget on the real rewrites made so far.
- Provenance queries over commit trailers: `kb history --skill --version`, changes of a page by reason.
- CI on typical scenarios with test data only (US-23).
- Versioning policy, release history (changelog), the configuration and note-schema migration path.
- Documentation: installation, updating, first run, writing and reviewing topics, restoring deleted pages.

**Done when:** the typical scenarios of the user stories pass by hand in Claude Code, Codex and Cursor and in CI; the `v1.0.0` tag is released.

## 4. Backlog

### 4.1. Later

Ordered roughly by closeness to the current value.

| Direction | What it gives | When |
|---|---|---|
| Read-only structure report in `kb doctor`: orphan pages, links to pages that never existed (with the closest title), pages over budget, missing `summary`, files outside the type folders, near-duplicate titles | A cheap overview without any model or edits | Right after stage 7, or when the base passes a few dozen pages |
| `kb related PATH`: suggested related pages with reasons (shared links, pages citing both, shared tags) | Finding neighbours when search is not enough | When neighbours become hard to find |
| `kb rename`, `kb merge`, `kb unlink` with backlink updates, aliases as redirects, a stable note `id` | Fixing duplicate topics and renames safely | At the first duplicate topic |
| An Obsidian Web Clipper template for source cards, shipped in `templates/` for import: the card's properties, no `{{content}}` | Capturing a source from the browser in one click, without an agent (no skill provenance) | When the card contract has settled after stage 6 |
| Regenerable Obsidian Bases files (topic catalogue, pages with open questions) | An index view for the human in Obsidian | Any time |
| Rebuildable SQLite FTS5 cache outside the vault behind `kb search` | Faster, better-ranked full-text search | Hundreds of pages |
| Optional search backend (qmd, multilingual embeddings) behind `kb search` | Better retrieval on mixed Russian/English text and paraphrases | When ranked text search starts missing pages |
| Duplicate detection by embeddings | Catches the same topic under different names and languages | When the index check by the skill stops being enough |
| Explicit "keep" markers that `kb rewrite` refuses to change | A hard guarantee for hand-written lines | If the hand-edit flags prove too weak |
| Reminder before context compaction (a hook that only reminds, never writes) | Fewer lost details in long conversations | When it becomes a problem |
| Spaced repetition with state outside the vault | Scheduled reviews without commits | Only if the user wants it |
| A second cloud copy: `restic`/Kopia snapshots or Google Drive via `rclone --backup-dir` | A copy independent of the Git host | When privacy or host independence matters (US-20, design §12.5) |
| Mobile access and multi-device sync through one two-way mechanism | Reading and editing from a phone | US-20 target |
| Stronger vault protection: `kb doctor` checks the agents' sandbox settings; a debounced watcher commits outside edits sooner | Less reliance on guidance | design §12.4 |

### 4.2. Frozen

Kept as possible directions, not planned: separate `research` / `project` notes and the `research` skill (US-03, US-06); `kb attach` for copying a source's images into the vault (illustrations are referenced and described, design §6.9); the source registry and external integrations (US-14); multiple knowledge bases (US-21); other users (US-22); a "librarian" subagent; an MCP wrapper; ChatGPT.

### 4.3. Not doing

`log.md`; a raw-source folder; an index file written by the model or committed; automatic saving of `kb-recall` answers; edits cascading across many pages; checking the whole vault with the model; claim registries, numeric confidence, review dates and status tags; vector search at the current size; typed link vocabularies; hooks that capture sessions; writing through the Obsidian CLI; Dataview. Reasons: design §14.1.

## 5. Risks and how to mitigate them

| Risk | Where it shows up | Mitigation |
|---|---|---|
| Repeated rewrites drift and lose correct details | Stage 5 and after | One page per run with the user reading the diff; untouched sections kept as they are; the report of removed sections, links and sources; a page budget with splitting instead of compression |
| The model truncates a page | Stage 5 | Shrink guard in `kb rewrite`; `kb doctor` still catches large shrinks outside `kb` |
| What is written differs from what was approved, or the page was edited in Obsidian meanwhile | Stage 5 | Approval hash over the current file and the new content |
| The user's own text is overwritten | Stage 5 | `## In my words` carried over by the CLI; a changing draft is refused; only `kb my-words` writes it, verbatim, after a yes |
| Edits spread across many pages and review becomes impossible | Stage 5 | Neighbours get only lines through `kb link` / `kb extend`; a neighbour that needs more gets a separate run |
| An error becomes a "fact" and is cited later | Stage 5 and after | Writes only on command; `kb-recall` saves nothing the agent formulates; doubtful claims go to `Verify:`; sources only if opened |
| The check of linked pages misses errors both pages share | Stage 5 | Opening the source where there is one; findings stay `Verify:` items instead of corrections |
| Tag sprawl (`async`, `asyncio`, `python-async`) | Stage 5 and after | The vocabulary listed by `kb index --tags`; new tags confirmed in the plan; 1–3 tags per page |
| Duplicate topics under different names or languages | Stage 5 and after | CLI refusal by title, alias and similar title; the skill names the closest pages from the index; aliases in the user's language |
| A rewrite silently reverts a correction the user made by hand | Stage 5 and after | Hand-edited lines flagged from `git blame`; the skill keeps them unless the user agrees |
| Instructions hidden in a page or a source steer the agent | Stage 5 and after | Text from pages, sources and the conversation is data; hidden text flagged in added lines; no shell or delete in `kb`; sandbox settings |
| A source card describes a source the agent never opened | Stage 6 and after | A card only from an opened source or text the user pasted; otherwise no card |
| A card turns into a copy of the source or its images | Stage 6 and after | Summary in the agent's own words, at most a couple of short quotes, illustrations referenced and described, no image copies |
| Cards pile up and are never used | Stage 6 and after | Tags from the shared vocabulary; `## Use for`; cards surfaced by `kb-recall` and `add-knowledge` on their topic; `kb index --sources` shows cards no topic links to |
| Codex or Cursor rewrite whole pages | Stage 7 | The same CLI path and diff report for every client; checked hands-on in stage 7 |
| Reading AI-written pages gives an illusion of knowing the topic | Daily use | Review mode starts with recall; `## In my words` |
| Clients change their skill mechanisms | Stages 5–7 | Installation adapters; skills without client-specific features; `kb doctor` rechecks paths |
| CLI and skill versions diverge | Daily use | `kb update` as one command; the version warning in `kb where` |
| Local history alone does not survive loss of the computer | Daily use | `kb sync` to a private remote hourly; Time Machine; freshness warnings |
| An agent deletes vault files with shell commands | Daily use | Sandbox settings documented; history and remote out of the agent's reach; the manifest detects deletions |
| A secret pasted into a conversation ends up in a page and is pushed | Daily use | `kb` refuses key-like strings in the lines a write adds |

## 6. Document history

- **2.0 — 2026-10-12:** roadmap restated after stage 4 and the LLM Wiki research. Stages 0–4 summarized with a link to v1.9. New stage 5 "Topic pages" (v0.6) with steps 5a–5e; stabilization moved to stage 6 (v1.0) with checks of the new skills, calibration and provenance queries over trailers. Backlog split into later, frozen and not doing. Risks updated for page rewrites. The history of versions 1.0–1.9 is in [personal-knowledge-roadmap-v1.md](personal-knowledge-roadmap-v1.md).
- **2.1 — 2026-10-19:** stage 5 extended with the decisions of design 2.1: duplicate checks with aliases and search ranking (5a); `--sections` and the section summary, flags for hand-edited lines and hidden text, `--since`, unlinked mentions on the written page (5b); the updated skill flows, the page as the reference in review, `kb my-words` from both skills, the skills' own format reference and the write rule with other Obsidian skills (5c); tests and "done when" (5e). Backlog: FTS5 cache, embedding duplicates, "keep" markers. Risks: duplicates, reverted hand edits, hidden instructions.
- **2.2 — 2026-10-19:** sources for later, decided by the user after `reports/Источники на потом: захват и summary.md`. New stage 6 "Sources for later" (v0.7) with steps 6a–6c: the source card in the CLI (`url` or `ref`, duplicates by normalized URL, `kb search --type source`, `kb index --sources` with the count of linking topic pages), the `save-source` skill, `add-knowledge` and `kb-recall` using the cards. Step 5a defines the card contract in `note-schema-v1.md`. Stabilization moves to stage 7 (v1.0) and checks `save-source` too. Backlog: a Web Clipper template (later); `kb attach` frozen; `source` notes and `save-source` leave the frozen list. Risks: cards from unopened sources, copies, unused cards.
