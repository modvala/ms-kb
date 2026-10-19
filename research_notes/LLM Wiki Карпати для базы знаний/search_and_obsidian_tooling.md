# Search and Obsidian tooling for an LLM-maintained Markdown wiki (as of 2026-10-12)

Scope: qmd, the official Obsidian CLI, kepano/obsidian-skills, Obsidian Bases and Dataview, Web Clipper and defuddle, link-graph maintenance tools, and lightweight Python hybrid search. For each: what it does, install/invocation, maturity/limits, and how it could plug into (or replace parts of) the Python `kb` CLI used by agents in Claude Code, Codex and Cursor. Sources were checked on 2026-10-12. "Inferences" are my reasoning, not source claims.

## 1. qmd (Tobi Lütke's local Markdown search engine)

### Takeaway
qmd is a mature-ish (v2.x, MIT, Node/Bun) on-device search engine over Markdown: BM25 via SQLite FTS5, vector search via sqlite-vec, and a hybrid `query` mode with LLM query expansion, RRF fusion and LLM reranking, all on local GGUF models (~2 GB download). It has a CLI with JSON/files output and an MCP server, so `kb` could shell out to it as an optional backend, but it should not be a hard dependency: it adds a Node runtime, ~2 GB of models, a separate index that must be refreshed after each write, and it knows nothing about Obsidian wikilinks.

### Cited Findings
**What it is, licence, version**
- Describes itself as "An on-device search engine for everything you need to remember", for Markdown notes, meeting transcripts and docs; combines BM25, vector semantic search and LLM reranking, run locally through node-llama-cpp with GGUF models; licence MIT — [tobi/qmd README](https://github.com/tobi/qmd)
- Latest tagged release 2.8.3 (2026-08-16), with an "Unreleased" section above it; 2.0.0 (2026-03-10) introduced a stable SDK API (`QMDStore`) and rebuilt the MCP server on it; 2.5.0 (2026-05-19) added `qmd doctor`; 2.1.0 (2026-04-05) added AST chunking for code and `qmd bench` — [qmd CHANGELOG](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)
- No changelog entries are labelled breaking, but several need action: 2.8.3 made MCP HTTP sessionless and requires approval for project-local update commands; 2.5.3 turned on `get` line numbers by default; the Unreleased changes require `qmd embed -f` on downgrade and a restart of an already-running `qmd mcp` — [qmd CHANGELOG](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)
- Karpathy's "LLM Wiki" gist (created 2026-04-04) recommends qmd for larger wikis as "a local search engine for markdown files with hybrid BM25/vector search and LLM re-ranking" and says you can also vibe-code a simple search script when needed — [Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

**Search modes**
- `qmd search`: BM25 full-text via SQLite FTS5, no LLM. `qmd vsearch`: vector-only. `qmd query` (alias `deep-search`): hybrid with query expansion into typed sub-queries (`lex` goes to BM25, `vec`/`hyde` go to vectors; the original query gets double weight), Reciprocal Rank Fusion with k=60 (rank #1 gets +0.05, ranks #2–3 get +0.02), LLM rerank of the top 30, then a position-aware blend (75/25 for ranks 1–3, 60/40 for ranks 4–10, 40/60 for ranks 11+) — [tobi/qmd README](https://github.com/tobi/qmd)
- Chunking: ~900-token chunks with 15% overlap, break points scored by Markdown structure (H1 = 100 … H6 = 50, code fence = 80, horizontal rule = 60, blank line = 20); code fences stay intact; Markdown always uses regex chunking — [tobi/qmd README](https://github.com/tobi/qmd)

**Local models and resources**
- Default models: embeddings `embeddinggemma-300M-Q8_0` (~300 MB), reranker `qwen3-reranker-0.6b-q8_0` (~640 MB), query expansion `qmd-query-expansion-1.7B-q4_k_m` (fine-tuned, ~1.1 GB); downloaded on first use to `~/.cache/qmd/models/`; about 2 GB of downloads in total; Qwen3-Embedding-0.6B is named as a multilingual option; changing the embedding model requires `qmd embed -f` — [tobi/qmd README](https://github.com/tobi/qmd)
- GPU selection via `QMD_LLAMA_GPU` (`metal`, `vulkan`, `cuda`); `QMD_FORCE_CPU=1` or `--no-gpu` forces CPU; `--no-rerank` is faster on CPU; models stay loaded, and embedding/rerank contexts are disposed after 5 minutes idle (about 1 s to reload) — [tobi/qmd README](https://github.com/tobi/qmd)
- macOS fixes in the changelog: Metal exit-crash mitigation (2.5.3), a Metal finalizer abort in `qmd query --json` (2.5.0), a Metal residency workaround on by default on Darwin (2.8.3); the embedding context pool is now sized from model weights so an 8 GB GPU is not exhausted (2.8.3) — [qmd CHANGELOG](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)
- Third-party reports (not maintainer benchmarks): running as an HTTP daemon keeps models loaded at ~2 GB RAM with ~2–3 s queries; without the daemon the first query has a ~19 s cold start — [Hermes Agent qmd skill docs, via search snippet](https://hermes-agent.nousresearch.com/docs/user-guide/skills/optional/research/research-qmd). On a 2 vCPU / 4 GB no-GPU cloud VM, BM25 returned in milliseconds but the vector and rerank layers were impractical — [hackyourway Substack](https://hackyourway.substack.com/p/qmd-memory-search)

**Install and CLI**
- Install: `npm install -g @tobilu/qmd` or `bun install -g @tobilu/qmd` (or `npx`/`bunx` one-offs); needs Node.js >= 22 or Bun >= 1.0.0; on macOS `brew install sqlite` for extension support — [tobi/qmd README](https://github.com/tobi/qmd)
- Collections: `qmd collection add ~/notes --name notes [--mask "**/*.md"]`, `list/show/remove/rename/include/exclude`, `qmd collection update-cmd notes 'git pull --rebase'` (runs before `qmd update`); context descriptions: `qmd context add qmd://notes "Personal notes and ideas"` — [tobi/qmd README](https://github.com/tobi/qmd)
- Indexing: `qmd update` (re-scan), `qmd embed` / `qmd embed -f`; `qmd status`, `qmd doctor`, `qmd cleanup` — [tobi/qmd README](https://github.com/tobi/qmd)
- Retrieval: `qmd get notes/meeting.md:50 -l 100`, `qmd get "#abc123"` (docid), `qmd multi-get "journals/2025-05*.md"` (default `--max-bytes` 64 KB); search flags include `-n`, `-c/--collection`, `--min-score`, `--full`, `--explain`, `--filter <json>`, `--no-rerank`, `--full-path`, and `--format cli|json|csv|md|xml|files`; non-TTY output is plain paths and respects `NO_COLOR` — [tobi/qmd README](https://github.com/tobi/qmd)
- `qmd bench <fixture>` measures precision, recall, MRR and F1 across backends — [tobi/qmd README](https://github.com/tobi/qmd)

**Index location and config**
- Index at `~/.cache/qmd/index.sqlite` (FTS5, sqlite-vec `vectors_by_collection`, an `llm_cache` table); config at `~/.config/qmd/index.yml` (override with `XDG_CONFIG_HOME` or `QMD_CONFIG_DIR`); `--index <name>` selects a named index; `qmd init` creates a project-local `.qmd/index.yml` and `index.sqlite`, and checked-in configs with out-of-tree paths, update commands or custom models need `qmd trust` — [tobi/qmd README](https://github.com/tobi/qmd)

**MCP server**
- `qmd mcp` (stdio, launched per client) or `qmd mcp --http [--daemon]` (default `localhost:8181`; `POST /mcp`, `POST /query`, `POST /metadata`, `GET /health`); tools `query` (typed lex/vec/hyde sub-queries, `limit`, `minScore`, `rerank`, `filter`), `get`, `multi_get`, `status`, `metadata`; non-loopback Origin and mismatched Host get 403; the endpoints are unauthenticated — [tobi/qmd README](https://github.com/tobi/qmd)
- Claude Code: `claude plugin marketplace add tobi/qmd` then `claude plugin install qmd@qmd`, or manual MCP config `"command": "qmd", "args": ["mcp"]` — [tobi/qmd README](https://github.com/tobi/qmd)

**Obsidian and frontmatter**
- The README and changelog do not mention Obsidian or wikilinks — [tobi/qmd README](https://github.com/tobi/qmd); [qmd CHANGELOG](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)
- Frontmatter is indexed as ordinary searchable text. Typed metadata filtering is opt-in through a namespaced `qmd.metadata` frontmatter block (strings, numbers, booleans, flat arrays) with a JSON filter AST (`eq`, `in`, `all`, `gte`, `prefix`, `exists`); this is in the "Unreleased" section, not 2.8.3 — [tobi/qmd README](https://github.com/tobi/qmd); [qmd CHANGELOG](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)

### Inferences
- **Shelling out is feasible.** `kb search --backend qmd` could call `qmd query "<q>" -c <kb-collection> --format json -n 10` (or `--format files`) and map results back to vault paths with `--full-path`, after a one-time `qmd collection add <vault> --name <kb> --mask "**/*.md"`. Detect it with `shutil.which("qmd")` and fall back to the built-in scan when it is missing.
- **The index goes stale between writes.** qmd keeps its own SQLite index outside the vault, so after each `kb new`/`kb extend` something must run `qmd update` (cheap) and `qmd embed` (slower). Options: call `qmd update && qmd embed` after `commit_write` without blocking the write, or run it from the hourly `kb sync` LaunchAgent. Otherwise hybrid results can miss the newest page, which is exactly the one an agent checks for duplicates.
- **Use it as an optional backend, not a replacement.** It adds a second runtime (Node >= 22 or Bun), ~2 GB of models, ~2 GB resident RAM when warm, and cold starts of tens of seconds; Codex and Cursor sessions may not tolerate a 19 s first query. Duplicate detection at write time (`search.find_duplicates`) should stay deterministic and in-process; qmd fits recall/exploration better (`kb-recall`).
- **Not frontmatter-aware unless notes change.** kb's typed fields (type, status, dates) are not filterable in qmd unless kb also writes a `qmd.metadata` block, which would pollute the schema. kb's own filters should stay in Python and qmd should only do ranking.
- **Multilingual.** If notes are mostly Russian, the default `embeddinggemma-300M` and the English-trained query-expansion model may underperform; the README's multilingual alternative is Qwen3-Embedding-0.6B (set in `index.yml` or `QMD_EMBED_MODEL`, then `qmd embed -f`). This has not been benchmarked here; `qmd bench` could check it on the user's own notes.
- **MCP versus CLI.** For agents, exposing qmd's MCP server directly would bypass `kb` and its rules (e.g. kb-recall's read-only discipline is fine, but agents could then read paths kb would not suggest). Wrapping it behind `kb search` keeps one interface across the three clients.

### Gaps
- No official resource benchmarks (RAM/latency) for Apple Silicon Macs; the ~2 GB and ~19 s figures come from third-party docs and were read only via a search snippet.
- GitHub star count and npm download numbers for qmd were not captured.
- No source evaluated qmd's quality on non-English (e.g. Russian) Markdown or with the fine-tuned query-expansion model on non-English queries.
- No source states whether qmd follows `[[wikilinks]]` or uses link structure in ranking; the docs suggest it does not.

## 2. Official Obsidian CLI (desktop 1.12+)

### Takeaway
The official CLI (shipped in 1.12, public in 1.12.4 on 2026-02-27; the help page now asks for installer 1.12.7+) exposes Obsidian's own metadata cache: search, backlinks, links, unresolved, orphans, deadends, properties, aliases, tags, Bases queries, daily notes, and create/append/move/rename. It is a remote control for the running desktop app, not a headless tool: if Obsidian is closed, the first command launches it. Early versions had silent wrong/empty results. For `kb`, which must work without Obsidian, it can at most be an optional read-only cross-check, never a write path.

### Cited Findings
**Release and setup**
- The 1.12 series began with 1.12.0 on 2026-02-10; 1.12.1 (2026-02-10) notes that `vault=` must be the first argument; 1.12.3 (2026-02-23) fixed the CLI hanging on longer content; the public release that introduced the CLI was 1.12.4 (2026-02-27) — [Obsidian changelog 1.12.4](https://obsidian.md/changelog/2026-02-27-desktop-v1.12.4/); [1.12.1](https://obsidian.md/changelog/2026-02-10-desktop-v1.12.1/); [1.12.3](https://obsidian.md/changelog/2026-02-23-desktop-v1.12.3)
- Enable via Settings → General → Command line interface, then register. On macOS this creates a symlink `/usr/local/bin/obsidian` → `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli` (admin rights needed). Requires the 1.12 installer; the page says to upgrade to 1.12.7 or later — [Obsidian Help: CLI](https://obsidian.md/help/cli)
- Usage: `obsidian <command> param=value flag`; running `obsidian` alone opens a TUI; `vault=<name>` must be first; `file=` resolves like a wikilink, `path=` is an exact vault path, and the default is the active file; multiline content uses `\n`/`\t` escapes — [Obsidian Help: CLI](https://obsidian.md/help/cli)

**Commands relevant to kb**
- Search: `search query=<text> [path=] [limit=] [format=text|json] [total] [case]`; `search:context` gives grep-style `path:line: text` — [Obsidian Help: CLI](https://obsidian.md/help/cli)
- Links: `backlinks [file|path] [counts] [total] [format=json|tsv|csv]`, `links` (outgoing), `unresolved [total] [counts] [verbose] [format=json|tsv|csv]`, `orphans` (no incoming links), `deadends` (no outgoing links) — [Obsidian Help: CLI](https://obsidian.md/help/cli)
- Properties/aliases/tags: `properties [...] [format=yaml|json|tsv]`, `property:set name= value= [type=text|list|number|checkbox|date|datetime]`, `property:read`, `property:remove`, `aliases`, `tags [sort=count] [counts] [format=json|tsv|csv]`, `tag name=<tag>` — [Obsidian Help: CLI](https://obsidian.md/help/cli)
- Notes: `create [name|path] [content] [template] [overwrite] [open]`, `read`, `append`, `prepend` (after frontmatter), `move ... to=`, `rename ... name=` (update links if the vault setting is on), `delete` (trash unless `permanent`); daily notes: `daily`, `daily:path`, `daily:read`, `daily:append`, `daily:prepend` — [Obsidian Help: CLI](https://obsidian.md/help/cli)
- Bases and outline: `bases`, `base:views`, `base:query [view=] [format=json|csv|tsv|md|paths]` (default json), `base:create`; `outline [format=tree|md|json]`; also `tasks`, `templates`, `wordcount`, `eval code=<js>` (arbitrary JS in the app) and `dev:*` commands — [Obsidian Help: CLI](https://obsidian.md/help/cli)

**Running app, headless**
- Obsidian must be running; if it is not, the first command launches it; the CLI connects to the running instance; the help page describes no headless mode — [Obsidian Help: CLI](https://obsidian.md/help/cli)
- "Obsidian Headless" (npm `obsidian-headless`, `ob login`, Node 22+, open beta) is a separate client for Sync and Publish only, not for search, links or properties — [Obsidian Help: Headless](https://obsidian.md/help/headless)
- Community users run the GUI under Xvfb on Linux servers (unsupported); one report describes a GPU crash loop and stale singleton lock files after a forced shutdown that made Obsidian exit silently with status 0 — [Obsidian forum: headless on Ubuntu](https://forum.obsidian.md/t/running-obsidian-headlessly-on-ubuntu-for-ai-agent-workflows-xvfb-systemd-setup/112741)

**Reliability reports**
- On 2026-02-13 a community tester ran 57 scenarios against CLI 1.12 and found 13 where the command reported success but returned wrong or empty data. Examples: `tasks todo` → 0 results (scoped to a nonexistent active file; workaround `tasks all todo`), `tags counts` → "No tags found" (workaround `tags all counts`), `properties format=json` returned YAML, and `create name= content=` opened the GUI (workaround `silent`). A reply said that on 1.12.1 these cases now print explicit errors such as "Error: No active file". A bug report (#111168) was filed; no staff reply is visible — [Obsidian forum: 13 silent failures](https://forum.obsidian.md/t/open-source-agent-skill-for-obsidian-cli-prevents-13-silent-failures/111169)
- On 1.12.4, `base:query` reportedly returned no row data while `format=md` showed the columns — [Obsidian forum: base:query yields no results](https://forum.obsidian.md/t/obsidian-base-query-yields-no-results/111796)
- kepano's own `obsidian-cli` skill states "Requires Obsidian to be open" and recommends `silent` so that files do not open — [obsidian-cli SKILL.md](https://github.com/kepano/obsidian-skills/blob/main/skills/obsidian-cli/SKILL.md)

### Inferences
- **Not a dependency for kb.** Obsidian is optional for ms-kb, agents in Codex/Cursor may run when Obsidian is closed, and a `kb` command that silently launches a GUI app is a bad side effect. There is also no headless mode on macOS.
- **No writes through it.** `create/append/property:set/move` would bypass `write.py` validation, provenance stamping and the per-write git commit. The skills must keep saying "only `kb` touches the vault"; if users install kepano's `obsidian-cli` skill alongside, agents may be tempted to write via `obsidian create`, which `kb` cannot see until its next `commit_external`.
- **Possible optional use: cross-check.** When `obsidian` is on PATH and the app is running with the same vault, `kb doctor --obsidian` could compare kb's own link resolution with `obsidian unresolved format=json` / `orphans` / `backlinks`. Obsidian is the authority on how its own resolver treats aliases and shortest-path links, so differences point to kb resolver bugs. Detecting "running" without launching it is not documented (e.g. checking for the process first is my assumption).
- **Rename/move with link updates** is the one capability kb lacks that the CLI does well (`rename`/`move` update internal links if the vault setting is on). If kb ever needs topic consolidation (merging pages), it should implement link rewriting itself rather than depend on the CLI.
- Because results have been silently empty in some versions, any optional integration should treat empty output as "unknown", not "no backlinks".

### Gaps
- The 1.12.5–1.12.7 and any 1.13 changelog entries were not read, so it is unknown which silent-failure cases have been fixed by October 2026. A search summary suggested that 1.12.2 changed CLI defaults to silent and replaced the `all` flag with `active`; I did not open that changelog entry to verify.
- No documented way to query the CLI without it launching Obsidian, and no performance data on large vaults (one tester validated an 18,876-file vault but gave no timings).

## 3. kepano/obsidian-skills (Steph Ango)

### Takeaway
An MIT-licensed collection of six Agent Skills (obsidian-markdown, obsidian-bases, json-canvas, obsidian-cli, defuddle, knap), very popular (~49k stars) but unversioned (no releases). It installs as a Claude Code plugin, by copying into `~/.codex/skills`, or via `npx skills add`; nothing Cursor-specific is documented. Its `obsidian-markdown` skill is a good, compact syntax reference for Obsidian Flavored Markdown that could complement kb's own note-format reference. It cannot replace kb's reference, because it says nothing about kb's schema, provenance or "write only via kb" rule, and its `obsidian-cli` skill invites direct vault writes.

### Cited Findings
- Six skills in `skills/`: **obsidian-markdown** (Obsidian Flavored Markdown: wikilinks, embeds, callouts, properties), **obsidian-bases** (.base files: views, filters, formulas, summaries), **json-canvas** (.canvas files: nodes, edges, groups), **obsidian-cli** (vault interaction via the Obsidian CLI, plus plugin/theme development), **defuddle** (clean Markdown from web pages to save tokens), **knap** (renders Markdown templates from JSON or CSV data, including batch file generation); licence MIT; 49.4k stars, 3.5k forks, 49 commits on `main`, no releases or version numbers — [kepano/obsidian-skills README](https://github.com/kepano/obsidian-skills); [skills/ directory](https://github.com/kepano/obsidian-skills/tree/main/skills)
- Install: Claude Code `/plugin marketplace add kepano/obsidian-skills` then `/plugin install obsidian@obsidian-skills`, or copy into a `/.claude` folder at the vault root; Codex: copy `skills/` into `~/.codex/skills`; OpenCode: clone the whole repo into `~/.opencode/skills/obsidian-skills`; any agent: `npx skills add git@github.com:kepano/obsidian-skills.git`; no Cursor-specific instructions, but the skills follow the Agent Skills specification — [kepano/obsidian-skills README](https://github.com/kepano/obsidian-skills)
- `obsidian-markdown/SKILL.md`: 196 lines (~5.2 KB), no `version` field. It covers wikilinks (display text, heading and block links), block IDs `^id`, embeds (notes, sections, images with width, PDF pages), callouts (13 types, foldable), properties (`tags`, `aliases`, `cssclasses`), nested tags, comments, `==highlights==`, LaTeX, Mermaid (with links to notes) and footnotes, plus `references/PROPERTIES.md`, `EMBEDS.md`, `CALLOUTS.md`. It tells agents to use `[[wikilinks]]` for vault notes (Obsidian tracks renames) and `[text](url)` only for external URLs, and to add frontmatter with title, tags and aliases — [obsidian-markdown SKILL.md](https://github.com/kepano/obsidian-skills/blob/main/skills/obsidian-markdown/SKILL.md)
- `obsidian-cli/SKILL.md`: 106 lines; "Requires Obsidian to be open"; teaches `read`, `create` (with `template`, `silent`), `append`, `search`, `daily:*`, `property:set`, `tasks`, `tags`, `backlinks`, and a plugin-dev loop (`plugin:reload`, `dev:errors`, `dev:screenshot`/`dev:dom`, `dev:console`); no warnings about silent failures — [obsidian-cli SKILL.md](https://github.com/kepano/obsidian-skills/blob/main/skills/obsidian-cli/SKILL.md)
- `defuddle/SKILL.md`: tells agents to `npm install -g defuddle` if missing, to use `defuddle parse <url> --md` (always `--md`), `-o file.md` and `-p title|description|domain`, and recommends defuddle over WebFetch for standard web pages to cut tokens — [defuddle SKILL.md](https://github.com/kepano/obsidian-skills/blob/main/skills/defuddle/SKILL.md)

### Inferences
- **Complement, do not bundle wholesale.** kb's own note-format reference should keep the schema-specific rules (required fields, note types, provenance written by the CLI, one consolidated page per topic). For OFM syntax (block refs, heading links, callouts, embeds) it could point to or vendor parts of `obsidian-markdown` (MIT allows this with the licence notice) instead of re-documenting syntax.
- **Conflicts to manage if a user also installs these skills:** (a) `obsidian-markdown` tells agents to add `title/tags/aliases` frontmatter themselves, which may clash with kb's schema validation and CLI-stamped fields; (b) `obsidian-cli` teaches direct `create/append/property:set` writes, bypassing kb. kb's skills should say explicitly that, inside the kb vault, notes are written only through `kb new`/`kb extend` even if other Obsidian skills are installed.
- `obsidian-bases` is directly reusable if kb generates `.base` overview files (section 4). `defuddle` overlaps with any "save a web source" flow (section 5). `json-canvas` and `knap` are not relevant to a text-first wiki.
- Unversioned skills (no releases, no `version` field) are hard to pin; if kb references them, it should record the commit SHA it relies on.

### Gaps
- The contents of `obsidian-bases`, `json-canvas` and `knap` SKILL.md files were not read in full; `knap` looks recent and its purpose is known only from the README one-liner.
- Date of the latest commit was not visible.

## 4. Obsidian Bases and Dataview as index/overview pages

### Takeaway
Both compute views over frontmatter at render time inside Obsidian; neither writes results into Markdown. A `.base` file or a Dataview block is plain-text *query definition* that agents can read, but agents (and `kb`) cannot see the *results* without Obsidian (Bases via `obsidian base:query` only with the app running). They are good human dashboards (topic catalogue, pages needing verification, stale pages) but cannot replace an agent-readable index; `kb` should compute the index itself and can optionally also emit `.base` files for humans.

### Cited Findings
**Bases**
- Bases is a core plugin for database-like views of notes; "All the data in Obsidian Bases is stored in your local Markdown files and their properties"; view types table, list, cards, kanban, map (plugins can add more); views are saved as a `.base` file or embedded in a code block in a note — [Obsidian Help: Bases](https://obsidian.md/help/bases)
- Introduced as an early beta in 1.9.0 (2025-05-21); 1.9.1 (2025-05-22) renamed built-in functions from snake_case to camelCase, breaking existing filters/formulas; public release in 1.9.10 (2025-08-18), which also dropped the singular `tag`/`alias`/`cssclass` properties (plural forms must hold lists) — [1.9.0](https://obsidian.md/changelog/2025-05-21-desktop-v1.9.0); [1.9.1](https://obsidian.md/changelog/2025-05-22-desktop-v1.9.1); [1.9.10](https://obsidian.md/changelog/2025-08-18-desktop-v1.9.10)
- `.base` is YAML with `filters` (`and`/`or`/`not`), `formulas`, `properties` (display names), `summaries`, `views` (`type`, `name`, `limit`, `groupBy`, `order`, view-level `filters`). Functions include `file.hasTag()`, `file.inFolder()`, `file.hasLink()`, `file.links`, `file.embeds`, `file.backlinks` (described as "performance heavy"), and date arithmetic such as `file.mtime > now() - "1 week"`; `file.backlinks` and `file.properties` do not auto-refresh on vault changes; when embedded, `this` refers to the embedding note — [Obsidian Help: Bases syntax](https://obsidian.md/help/bases/syntax)
- Results can be pulled from the terminal with `obsidian base:query [view=] format=json|csv|tsv|md|paths`, which needs the running app — [Obsidian Help: CLI](https://obsidian.md/help/cli); one user reported no row data on 1.12.4 — [Obsidian forum](https://forum.obsidian.md/t/obsidian-base-query-yields-no-results/111796)

**Dataview**
- Dataview is "a live index and query engine"; query via DQL (`LIST`/`TABLE` etc.), inline DQL and DataviewJS; it is "meant for displaying and calculating data" and does not edit notes (except toggling tasks); only indexed data (frontmatter, inline fields, tags, tasks) can be queried; implicit fields include `file.inlinks`; claims to scale to "hundreds of thousands of annotated notes" — [Dataview docs](https://blacksmithgu.github.io/obsidian-dataview/)
- Last Dataview update listed as 2025-03-15 (Obsidian Stats snapshot, July 2026) — [Obsidian Stats: Dataview](https://www.moritzjung.dev/obsidian-stats/plugins/dataview/). Its intended successor Datacore is described as "a work-in-progress re-imagining of Dataview", latest listed version 0.1.29 — [Obsidian Stats: Datacore](https://www.obsidianstats.com/plugins/datacore)
- Dataview Serializer 3.0 (published 2026-09-07, requires Obsidian 1.13) writes Dataview results into notes as plain Markdown so they stay readable where Dataview is not running; a recent bug in "once and eject" mode replaced a failed `dataviewjs` query with empty output, deleting the query and previous output silently (now fixed) — [dsebastien: Dataview Serializer 3.0](https://www.dsebastien.net/dataview-serializer-3-0-a-settings-screen-you-can-search-and-a-bug-that-could-eat-a-query/)
- Karpathy mentions Dataview for dynamic tables when the LLM adds YAML frontmatter, but his design still has the LLM maintain `index.md` (one line per page with a link and summary) and read it first when answering — [Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

### Inferences
- **Pros of computed views (Bases/Dataview):** never stale or contradicted by the LLM, no extra commits on every write, zero tokens to maintain, and good human UX in Obsidian (sorting, grouping, kanban of `status`). Bases is a core plugin (no community-plugin dependency) and its YAML is easy for kb to generate.
- **Cons for agents:** results exist only inside Obsidian; an agent reading `Topics.base` sees filters, not the list of topics; `kb-recall` in Codex/Cursor without Obsidian gets nothing. The Bases syntax has already broken once (1.9.1 rename). Dataview's development has slowed (no update since March 2025) and DataviewJS is executable code inside notes.
- **Recommended split for kb:** (1) `kb` computes agent-facing overviews on demand, e.g. `kb list --type concept`, `kb list --needs-verification`, `kb list --stale 180d`, or a generated `index.md`-like catalogue printed to stdout, from the same frontmatter it already validates. This is deterministic, has no LLM drift and needs no Obsidian. (2) Optionally `kb init` writes a few `.base` files (topic catalogue, needs verification, stale, orphans via `file.backlinks`) as *regenerable* files for humans browsing in Obsidian, matching kb's regenerable-vs-user-data split. (3) Avoid an LLM-maintained `index.md` committed on every write unless it is generated by `kb` rather than edited by the model.
- If a persisted plain-text index is wanted (for grep or GitHub browsing), kb generating it itself is safer than Dataview Serializer-style "serialize the query output", given that plugin's recent data-loss bug.

### Gaps
- The Bases functions page (full list, including any `file.backlinks` cost numbers) and the current Bases plugin API status were not read.
- No source compared token cost or answer quality for agents using a generated index versus search.
- Dataview's maintainer has not been found stating a formal maintenance-mode decision; only the update gap is documented.

## 5. Web Clipper (templates, Interpreter) and defuddle CLI

### Takeaway
defuddle (MIT, "very much a work in progress", Node) is the extraction engine built for Obsidian Web Clipper. Its CLI (`npx defuddle parse <url> --md|--json [-o] [-p]`) turns a URL or HTML into clean Markdown with metadata (title, author, published, schema.org) and can prepend YAML frontmatter. Web Clipper adds browser-side templates (variables, CSS selectors, schema.org, triggers) and an optional LLM "Interpreter" (Anthropic/OpenAI/Ollama). For `kb`, defuddle is the realistic automation hook (an optional `--from-url` for source notes or a skill instruction); Web Clipper is a human-in-the-browser path.

### Cited Findings
**defuddle**
- Extracts main content and returns cleaned HTML or Markdown, removing comments, sidebars, headers and footers; built for Obsidian Web Clipper but runs anywhere and can replace Mozilla Readability; README warns "Beware! Defuddle is very much a work in progress!"; licence MIT; ~9.7k stars, 434 forks, 61 open issues — [kepano/defuddle](https://github.com/kepano/defuddle)
- CLI: `npm install -g defuddle` or `npx defuddle parse <source>` (file, URL or stdin HTML); flags `--markdown/-m`, `--json/-j`, `--property/-p <name>`, `--output/-o <file>`, `--frontmatter/-f` (prepend YAML frontmatter), `--lang/-l`, `--user-agent/-u`, `--debug` — [kepano/defuddle](https://github.com/kepano/defuddle)
- Output fields: `title`, `author`, `published`, `content`, `wordCount`, `description`, `domain`, `site`, `language`, `favicon`, `image`, `metaTags`, `schemaOrgData`, `parseTime`. Normalizes footnotes, strips code line numbers while keeping the language, converts MathJax/KaTeX to MathML (LaTeX conversion in the full bundle), converts GitHub/Bootstrap alerts and Obsidian callouts to Obsidian-style callouts — [kepano/defuddle](https://github.com/kepano/defuddle)
- For X/Twitter articles, `parseAsync()` may call the third-party FxTwitter API when the local HTML has no usable content (disable with `useAsync: false`); no Python port is mentioned — [kepano/defuddle](https://github.com/kepano/defuddle)

**Web Clipper**
- Template variables: `{{content}}` (Markdown of article, highlights or selection), `{{contentHtml}}`, `{{title}}`, `{{url}}`, `{{author}}`, `{{published}}`, `{{description}}`, `{{site}}`, `{{domain}}`, `{{fullHtml}}`, `{{highlights}}`, `{{selection}}`, `{{date}}`, `{{words}}`; selector variables `{{selector:css?attr}}`, `{{selectorHtml:css}}`; schema.org variables `{{schema:@Type:key}}`; meta variables; variables work in note names, locations, properties and content; templates can trigger automatically on schema.org data — [Obsidian Help: Web Clipper variables](https://obsidian.md/help/web-clipper/variables)
- Interpreter: prompt variables like `{{"a summary of the page"}}` (with filters such as `|blockquote`) sent to a model in one request; presets for Anthropic, OpenAI, Ollama (local, needs `OLLAMA_ORIGINS` to allow the extension, default 2048-token context can silently give irrelevant results) and others; context defaults to the whole page HTML, narrowable with selectors — [Obsidian Help: Web Clipper Interpreter](https://obsidian.md/help/web-clipper/interpreter)
- Karpathy uses Web Clipper to get articles into a `raw/` sources folder and recommends a fixed attachment folder plus "Download attachments for current file" so the LLM can reference local images — [Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

### Inferences
- **kb integration options, cheapest first:** (a) skill-only: `add-knowledge` tells the agent "for a web source, run `npx defuddle parse <url> --md` (or use WebFetch), then summarize into `kb new source ...`", with no Python dependency; (b) optional `kb new source --from-url <url>` that shells out to `defuddle parse <url> --json` when it is on PATH and fills `title/author/published/url` provenance fields from JSON, keeping body text short (one consolidated page per topic suggests storing a summary plus link, not the full clipped article).
- Full-text clips conflict with the "one concise page per topic" goal and inflate search noise; if raw clips are kept, they belong in a separate raw/sources folder excluded from default `kb search`, as in Karpathy's raw/wiki split.
- Web Clipper templates are useful for the human (clip → a `source` note with kb-compatible frontmatter), but files created by the extension arrive outside `kb`, so kb's `commit_external` would commit them and `kb validate` should flag schema gaps rather than block.
- defuddle is Node-only; Python alternatives (e.g. trafilatura, readability-lxml) exist but were not researched here.

### Gaps
- Latest defuddle version and date were not obtained (npm page returned 403); release cadence unknown.
- Web Clipper's documentation does not say on the pages read that `{{content}}` is produced by defuddle (the defuddle README says it was built for Web Clipper).
- No documented way to run Web Clipper templates headlessly or from the CLI.

## 6. Link maintenance: backlinks, unresolved links, orphans, aliases, link suggestions, related pages

### Takeaway
Obsidian itself (core backlinks pane, unlinked mentions, the CLI's `backlinks/unresolved/orphans/deadends/aliases`) is the reference implementation, but it needs the app. Plugins add auto-linking (Virtual Linker family, Link Unlinked Mentions, Note Linker), graph-based "related notes" (Graph Analysis: co-citations, Jaccard, Adamic-Adar; Atomic Insights) and embeddings (Smart Connections, local model, no agent API). For a Python CLI the best option is to keep computing the link graph itself (it already resolves links for integrity checks) and add cheap, explainable "related pages" scores. Python libraries such as obsidiantools exist but are alpha and heavy.

### Cited Findings
**Python libraries / agent-side tools**
- obsidiantools 0.11.0 (2025-07-08), BSD-3, PyPI status "3 - Alpha", Python >= 3.9; builds a networkx graph of the vault, `backlinks_index`/`get_backlinks()`, `isolated_notes`, `nonexistent_notes`, front matter and tags; depends on pandas, numpy, networkx, markdown, beautifulsoup4, lxml, etc.; uses Obsidian's "shortest path when possible" link approach so the graph may differ from the app; some wikilink syntax is not well supported; untested outside Latin-script languages — [obsidiantools on PyPI](https://pypi.org/project/obsidiantools/)
- Basic Memory (AGPL-3.0, Python 3.12+, `uv tool install basic-memory --prerelease=allow`, v0.23): Markdown files plus a local SQLite index; `[[wikilinks]]` become typed relations; hybrid full-text + vector search with FastEmbed embeddings and an optional local reranker (`jinaai/jina-reranker-v1-tiny-en`, off by default); MCP tools include `search_notes`, `build_context` (graph traversal), `recent_activity`, `schema_validate`; `doctor` checks file/DB consistency; works with Obsidian with no setup — [basicmachines-co/basic-memory](https://github.com/basicmachines-co/basic-memory)
- Karpathy's "lint" pass looks for contradictions, stale claims, orphan pages with no inbound links, missing cross-references and missing concept pages; "A single source might touch 10-15 wiki pages" — [Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

**Obsidian CLI link commands** (app required): `backlinks`, `links`, `unresolved`, `orphans` (no incoming), `deadends` (no outgoing), `aliases`, with json/tsv/csv output — [Obsidian Help: CLI](https://obsidian.md/help/cli)

**Auto-linking plugins (Obsidian-side)**
- Virtual Linker / Glossary: shows virtual links for text matching other notes' titles or aliases without changing files (not in graph or reference counts); ~31k downloads — [community.obsidian.md: Virtual Linker](https://community.obsidian.md/plugins/virtual-linker). Forks: Virtual Autolink (can convert virtual links to real ones) — [Virtual Autolink](https://community.obsidian.md/plugins/virtual-autolink); FakeLink, which says the original is no longer actively maintained and broke after 2025 API changes — [FakeLink](https://community.obsidian.md/plugins/fakelink)
- Link Unlinked Mentions: bulk-links unlinked mentions of the active note and its aliases, with a dry-run preview, skipping frontmatter, code and existing wikilinks; irreversible without backup; not reviewed by Obsidian staff — [Link Unlinked Mentions](https://community.obsidian.md/plugins/link-unlinked-mentions). Link Plus: vault-wide unlinked mentions to wikilinks in batch — [Link Plus](https://community.obsidian.md/plugins/link-plus). Note Linker: lists references to other note names/aliases for the user to approve — [AlexW00/obsidian-note-linker](https://github.com/AlexW00/obsidian-note-linker). Heading Linker: stemming-based linking of glossary headings for six languages — [Heading Linker](https://community.obsidian.md/plugins/heading-linker)

**Related-notes plugins**
- Graph Analysis (SkepticMystic & Emile): co-citations (how often two notes are cited together, weighted by proximity), Jaccard similarity on link neighbourhoods, link prediction with Adamic-Adar and Common Neighbours, community detection; ignore tag `#nograph` — [skepticmystic/graph-analysis](https://github.com/skepticmystic/graph-analysis)
- Atomic Insights: ranks related notes with the Adamic-Adar index (shared links to rarely-linked pages count more than shared links to hubs) plus optional metadata/time signals; not reviewed by Obsidian staff — [Atomic Insights](https://community.obsidian.md/plugins/atomic-insights)
- Smart Connections v4: Connections view of semantically related notes and a Lookup view; ships a local embedding model (not named in the README); stores data in `.smart-env/` (exclude from third-party sync); source-available "Smart Plugins License"; Pro adds inline/footer connections and "Connections in Bases"; no agent API or MCP is mentioned, only "Send to Smart Context" (copy for chat tools) — [brianpetro/obsidian-smart-connections](https://github.com/brianpetro/obsidian-smart-connections)

### Inferences
- **Keep the link graph in kb (pure Python).** kb already resolves links for integrity checks. Extending it to a `kb links <note>` / `kb doctor` report of backlinks, unresolved links (with closest existing title/alias as a suggestion), orphans and dead ends is a small regex/frontmatter job and avoids obsidiantools' alpha status and pandas/lxml weight. The resolver should mirror Obsidian: match by file name (case-insensitive), then `aliases` from frontmatter, and handle `[[Note#Heading]]`, `[[Note^block]]`, `[[Note|text]]`, and embeds `![[...]]`; Obsidian CLI `unresolved` can validate the implementation in tests or manually.
- **"Related pages" for an agent, cheapest first:** (1) direct links both ways; (2) co-citation (pages linked from the same page) and Adamic-Adar over the link graph, which down-weights hubs such as `index.md` (per Atomic Insights' rationale); (3) shared tags with Jaccard; (4) BM25/title-term overlap using kb's own search; (5) embeddings only via an optional backend (qmd `vsearch`). A `kb related <note> --json` that returns candidates *with reasons* ("shares tags x,y; co-cited by Z") fits `add-knowledge` (link the new page to related topics) and `kb-recall`.
- **Unlinked mentions as suggestions, not edits.** Given that kb's `extend` only appends and never rewrites text, auto-linking plugins' in-place rewriting conflicts with kb's design. kb can instead *report* unlinked mentions of titles/aliases (Note Linker style) and let the agent append a "Related" list entry via `kb extend`.
- Smart Connections' `.smart-env/` should be excluded from kb's git commits and secret/size scans if users install it; it offers no API kb could call.
- Basic Memory is the closest existing Python analogue (Markdown + SQLite index + wikilink relations + MCP + `doctor`), useful as a design reference; its AGPL licence makes code reuse in kb unattractive.

### Gaps
- Obsidian's exact link-resolution rules (shortest path, duplicate names in different folders, alias precedence) were not fetched from the official help; tests against `obsidian unresolved` would settle them.
- Current maintenance status/compatibility of Graph Analysis and Note Linker with Obsidian 1.12–1.13 was not verified.
- Smart Connections' default embedding model name and storage format are not documented in the README.

## 7. Lightweight Python options for local hybrid search, and when a vault needs them

### Takeaway
The natural Python stack mirrors qmd's: SQLite FTS5 (BM25, in the stdlib `sqlite3` when compiled in) plus sqlite-vec for vectors, fused with RRF. Alternatives are tantivy-py (Rust BM25 engine) and LanceDB (embedded vector + FTS with built-in RRF). sqlite-vec is still pre-v1 (v0.1.10-alpha) and cannot be loaded by macOS's system Python. Per Karpathy, an index file plus plain scanning works up to roughly 100 sources / hundreds of pages; a personal "one page per topic" vault will likely stay in a range where a no-index scan is fast, so an FTS5 cache is the first step if needed and vectors are an optional extra.

### Cited Findings
**SQLite FTS5 + sqlite-vec**
- sqlite-vec: "pre-v1, so expect breaking changes!"; Apache-2.0/MIT; ~8.2k stars, 159 open issues; sponsored by Mozilla Builders, Fly.io, Turso and others; the repo contains DiskANN/IVF source files and an ANN benchmark folder, but the README shows only vec0 KNN — [asg017/sqlite-vec](https://github.com/asg017/sqlite-vec)
- Python: `pip install sqlite-vec`, `db.enable_load_extension(True)`, `sqlite_vec.load(db)`, `serialize_float32()` or NumPy float32 arrays; docs reference v0.1.10-alpha.4; SQLite >= 3.41 recommended. On macOS the bundled SQLite lacks extension support, so the system Python fails with `'sqlite3.Connection' object has no attribute 'enable_load_extension'`; the docs suggest Homebrew Python; `pysqlite3` is another option — [sqlite-vec Python docs](https://alexgarcia.xyz/sqlite-vec/python.html)
- Hybrid FTS5 + sqlite-vec with RRF in a single SQL query (CTEs for KNN and BM25 ranks, then fusion) was shown by Alex Garcia and covered by Simon Willison in October 2024 — [Simon Willison](https://feeds.simonwillison.net/2024/Oct/4/hybrid-full-text-search-and-vector-search-with-sqlite)
- An arXiv paper, "SQLite is Enough. Lexical, Semantic, and Hybrid Search with scrydb", presents a Python library using FTS5 and sqlite-vec with fusion/reranking, evaluated on IR benchmarks (seen via search snippet only) — [arXiv 2608.24060](https://arxiv.org/pdf/2608.24060)
- litesearch (PyPI 0.0.x) keeps documents in SQLite, combines FTS5 with usearch vectors, and exposes `rrf_merge()` — [litesearch on PyPI](https://pypi.org/project/litesearch/0.0.35/)
- qmd itself uses this stack (FTS5 + sqlite-vec in one SQLite file) — [tobi/qmd README](https://github.com/tobi/qmd)

**Other engines**
- tantivy-py: Python bindings for the Rust full-text engine Tantivy, `pip install tantivy` (builds from source with Rust if no wheel), MIT, ~431 stars — [quickwit-oss/tantivy-py](https://github.com/quickwit-oss/tantivy-py)
- LanceDB: hybrid search runs vector and full-text queries and merges with a reranker, `RRFReranker()` by default (model-free); needs `table.create_fts_index("text")`; model-based rerankers are Python-only — [LanceDB docs: hybrid search](https://docs.lancedb.com/search/hybrid-search/); [LanceDB docs: RRF](https://docs.lancedb.com/reranking/rrf)
- Basic Memory does hybrid search in Python with a SQLite index and FastEmbed embeddings — [basic-memory](https://github.com/basicmachines-co/basic-memory)

**Scale thresholds**
- Karpathy: the LLM-maintained index file "works surprisingly well at moderate scale (~100 sources, ~hundreds of pages)" without embedding-based RAG; past that he suggests qmd or a custom search script; he gives no exact threshold — [Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Dataview claims its in-memory index scales to "hundreds of thousands of annotated notes" — [Dataview docs](https://blacksmithgu.github.io/obsidian-dataview/)

### Inferences
- **Scale estimate (my arithmetic, not sourced):** 1,000 consolidated pages × ~800 words ≈ 0.8 M words ≈ 5–6 MB of text; a Python scan with simple scoring over that is well under a second on an Apple Silicon Mac, so kb's no-index search should remain adequate into the low thousands of pages. The pressure point is *recall quality* (synonyms, cross-language queries, paraphrases), not speed; that is what vectors or qmd add.
- **Upgrade path for kb, in order:** (1) keep the scan, add BM25-style scoring and title/alias/tag boosts; (2) if latency or ranking needs it, add an FTS5 cache (stdlib `sqlite3`, rebuildable from files, stored next to `vault-<kb>.json`, never committed to the vault), refreshed incrementally from the manifest's sha256s; (3) optional vectors via qmd shell-out rather than embedding models inside kb. That keeps kb's install light (`uv tool install`, no torch/ONNX, no 2 GB models) and avoids the macOS `enable_load_extension` trap.
- **If vectors ever go in-process:** sqlite-vec is the smallest dependency but is pre-v1 and needs an SQLite build that allows extensions; uv's managed CPython may or may not allow `enable_load_extension` (unverified, see Gaps). LanceDB is a heavier but more complete embedded option; tantivy-py only replaces BM25.
- **Cross-tool summary for kb:**
  - qmd: optional search backend through shell-out (`--format json`), refreshed after writes or by `kb sync`. Never required.
  - Obsidian CLI: no dependency; at most an optional cross-check of link resolution when the app is running. No writes.
  - kepano/obsidian-skills: reference for OFM syntax (and Bases YAML); kb's skills must override its write paths.
  - Bases: optional regenerable `.base` dashboards for humans; agent-facing lists computed by `kb`. Dataview: avoid (stalled, results invisible to agents).
  - defuddle: optional URL → Markdown for source notes, via a skill instruction or `--from-url`; Web Clipper stays a human path.
  - Link graph and related pages: implement in kb (Python, explainable scores); plugins remain human-side extras.

### Gaps
- Whether python-build-standalone (the CPython builds uv installs) supports `sqlite3.Connection.enable_load_extension` on macOS was not verified; this decides whether sqlite-vec works under `uv tool install`.
- No source gives empirical page/word thresholds at which grep/scan-based agent search degrades versus BM25 or hybrid on personal notes; the numbers above are estimates.
- LanceDB and tantivy-py versions and macOS arm64 wheel availability were not confirmed.
