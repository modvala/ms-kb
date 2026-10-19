# Community implementations and extensions of Karpathy's "LLM Wiki" pattern (April–October 2026)

Research date: 2026-10-12. Star counts and dates come from the GitHub API on that day unless marked otherwise. "Secondary" marks claims I saw only in search-result summaries or third-party aggregators and could not open in full.

Baseline, so that "beyond the gist" is well defined. The gist (created 2026-04-04, one revision) specifies three layers: immutable raw sources, an LLM-owned wiki, and a schema file (CLAUDE.md/AGENTS.md). It has three operations: ingest (discuss takeaways, write a summary page, update entity/concept pages, update index, append to log; one source may touch "10-15 wiki pages"), query (answers with citations; good answers "can be filed back into the wiki"), and lint (contradictions, stale claims, orphans, missing concept pages, missing cross-references, data gaps). It defines `index.md` as a catalog (link + one-line summary + optional metadata) and `log.md` as append-only with `## [date] op | title` headings. Page types are summaries, entities, concepts, comparisons, overview and synthesis. Tools mentioned are Obsidian, Web Clipper, qmd, Marp, Dataview, git and matplotlib. The index is said to work at "~100 sources, ~hundreds of pages". The gist leaves layout, page formats and tooling open ("intentionally abstract") — [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## 1. Which implementations exist and are notable?

### Takeaway
There are many implementations. Four that matter most for a Claude Code–first personal KB are AgriciDaniel/claude-obsidian (15.5k★), Ar9av/obsidian-wiki (3.6k★), Astro-Han/karpathy-llm-wiki (2.5k★) and nvk/llm-wiki (1.4k★). Two smaller Claude Code plugins have well-thought-out designs: kfchou/wiki-skills (189★) and ussumant/llm-wiki-compiler (327★). The two named in the brief are pedronauck's `karpathy-kb` (25 installs on skills.sh, migrated in mid-April into the `compozy/kb` Go CLI) and Hermes' `llm-wiki` (bundled in a 253k★ agent repo, flagged by Snyk on Tessl). The top-starred repos overall (nashsu/llm_wiki, TencentDB-Agent-Memory) are standalone apps or team-memory platforms, not Claude Code skills.

### Cited Findings

**Claude Code / Agent Skills implementations (most relevant)**
- **AgriciDaniel/claude-obsidian**: 15,476★, 1,539 forks, created 2026-04-07, last push 2026-09-10. A Claude Code plugin with 15 skills (`wiki`, `save`, `wiki-ingest`, `wiki-query`, `wiki-lint`, `autoresearch`, `canvas`, `defuddle`, `wiki-fold`, `wiki-mode`, `wiki-retrieve`, `wiki-cli`, `obsidian-markdown`, `obsidian-bases`, `think`) plus a Python core CLI (`scripts/claude-obsidian.py`). Codex, OpenCode, Gemini, Cursor and Windsurf are supported through skill links — [repo](https://github.com/AgriciDaniel/claude-obsidian)
- **Ar9av/obsidian-wiki**: 3,550★, created 2026-04-06, last push 2026-10-10. A pip-installable CLI (`obsidian-wiki`) plus 39 markdown skills. Also a Claude Code plugin (`/plugin marketplace add Ar9av/obsidian-wiki`), which ships the skills only, without the hooks or CLI. Supports Claude Code, Codex, Cursor, Windsurf, Gemini CLI and others — [repo](https://github.com/Ar9av/obsidian-wiki). Also listed as an `llm-wiki` skill on [claudemarketplaces.com](https://claudemarketplaces.com/skills/ar9av/obsidian-wiki/llm-wiki)
- **Astro-Han/karpathy-llm-wiki**: 2,472★, created 2026-04-05, last push 2026-07-23. A single Agent Skills skill (SKILL.md + references + one Python script), installed with `npx add-skill`. Targets Claude Code, Cursor, Codex and OpenCode — [repo](https://github.com/Astro-Han/karpathy-llm-wiki). [skillsllm.com](https://skillsllm.com/skill/karpathy-llm-wiki) listed it at 2.4k★ (secondary).
- **nvk/llm-wiki**: 1,408★, created 2026-04-04, last push 2026-10-02, at v0.25.0. A native Claude Code plugin (`claude plugin install wiki@llm-wiki`) and a Codex marketplace plugin. Also ships OpenCode and Pi presets. Has its own site, llm-wiki.net — [repo](https://github.com/nvk/llm-wiki)
- **NicholasSpisak/second-brain**: 738★, created 2026-04-06. The last push was 2026-04-07, so the repo is effectively frozen. Four skills installed with `npx skills add` (`/second-brain` wizard, `-ingest`, `-query`, `-lint`) — [repo](https://github.com/NicholasSpisak/second-brain)
- **ussumant/llm-wiki-compiler**: 327★, created 2026-04-04, last push 2026-08-21. A Claude Code plugin with Codex metadata that compiles sources into topic-based articles. Has a codebase mode since v2.0 — [repo](https://github.com/ussumant/llm-wiki-compiler)
- **kfchou/wiki-skills**: 189★, created 2026-04-05, last push 2026-07-03. A Claude Code plugin marketplace with 7 skills (`wiki-init`, `-ingest`, `-query`, `-lint`, `-update`, `-audit`, `-merge`) plus uv-run helper scripts — [repo](https://github.com/kfchou/wiki-skills)
- **SamurAIGPT/llm-wiki-agent**: 3,616★. The repo was created in 2023 and repurposed; last push 2026-10-12. A clone-and-run template (CLAUDE.md + `.claude/commands/`, AGENTS.md, GEMINI.md) — [repo](https://github.com/SamurAIGPT/llm-wiki-agent)
- **toolboxmd/karpathy-wiki**: 105★, last push 2026-10-09. A Codex/Claude Code plugin with SessionStart/Stop hooks, a detached background ingest worker and a macOS LaunchAgent scheduler — [repo](https://github.com/toolboxmd/karpathy-wiki). Also on [skills.sh](https://www.skills.sh/toolboxmd/karpathy-wiki) as 6 skills (secondary).
- **IssacW228/student-llm-wiki**: 177★, created 2026-06-01. Learning-oriented: course slides go in, out come concept pages, Feynman review, exam-prep questions and confidence tracking. Ships `.claude/skills`, `.claude-plugin`, `.cursor/rules` and AGENTS.md — [repo](https://github.com/IssacW228/student-llm-wiki)
- **Pratiyush/llm-wiki**: 397★. Turns Claude Code/Codex/Cursor/Gemini session transcripts into a wiki and a static site with `llms.txt` exports — [repo](https://github.com/Pratiyush/llm-wiki)
- Other GitHub repos named in the pattern's style, with their stars: [sdyckjq-lab/llm-wiki-skill](https://github.com/sdyckjq-lab/llm-wiki-skill) 2,535★ (Chinese, multi-platform skill); [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki) 1,681★ (upload documents, Claude writes the wiki over MCP); [swarmclawai/swarmvault](https://github.com/swarmclawai/swarmvault) 714★; [kytmanov/obsidian-llm-wiki-local](https://github.com/kytmanov/obsidian-llm-wiki-local) 835★ (Ollama, local only); [shannhk/llm-wikid](https://github.com/shannhk/llm-wikid) 421★; [tonbistudio/llm-wiki](https://github.com/tonbistudio/llm-wiki) 265★; [win4r/llm-wiki-claude-skill](https://github.com/win4r/llm-wiki-claude-skill) 13★ (a single SKILL.md with ingest/query/lint/compile).
- Curated list: [gavischneider/awesome-llm-wiki](https://github.com/gavischneider/awesome-llm-wiki), 218★, created 2026-05-19, with sections for skills, compilers, MCP servers, case studies and evaluations.

**The two skills named in the brief**
- **pedronauck `karpathy-kb`**: on skills.sh it shows 25 installs, first seen 2026-04-04, audits "Gen Agent Trust Hub: Pass, Socket: Pass, Snyk: Warn". Its repo `pedronauck/skills` has 635★ — [skills.sh](https://skills.sh/pedronauck/skills/karpathy-kb). The skill was removed from the repo on 2026-04-13 by commit "migrate karpathy-kb skill". The README now says it is "Migrated to kodebase-go/skills/kb … Unified with the `kb` CLI skill" — [commit](https://github.com/pedronauck/skills/commit/7d26772136149ce554b64c9feb49bc456f3a2fce). That repo now resolves to **compozy/kb**: 110★, created 2026-04-09, last push 2026-09-25, "a single-binary Go CLI for building and maintaining topic-based knowledge bases in the Karpathy KB pattern" — [compozy/kb](https://github.com/compozy/kb). The skills.sh page still serves the old skill and says nothing about the migration.
- **NousResearch/hermes-agent `llm-wiki`**: at `skills/research/llm-wiki/SKILL.md`, frontmatter `version: 2.1.0`, MIT, author "Hermes Agent". The hosting repo has 252,991★. The file's last change was 2026-08-08 ("standards sweep") — [SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)

**Non-Claude-Code or adjacent (for context only)**
- [nashsu/llm_wiki](https://github.com/nashsu/llm_wiki): 20,532★. A cross-platform desktop app that builds the wiki from documents.
- [TencentCloud/TencentDB-Agent-Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory): 27,948★. A team memory hub in which "LLM-Wiki" is one of four memory assets.
- [inkeep/open-knowledge](https://github.com/inkeep/open-knowledge): 4,540★. "AI-native markdown IDE and LLM wiki".
- [atomicstrata/llm-wiki-compiler](https://github.com/atomicstrata/llm-wiki-compiler): 2,180★. A Node CLI and SDK called `llmwiki` (formerly `atomicmemory/llm-wiki-compiler`) with an MCP server, a review queue and OKF export.

**Plugin directories**
- [claudepluginhub.com](https://www.claudepluginhub.com/plugins/praneybehl-llm-wiki) lists a `praneybehl-llm-wiki` Claude Code plugin, but `github.com/praneybehl/llm-wiki` returned 404 on 2026-10-12.
- [mcpmarket.com](https://mcpmarket.com/tools/skills/karpathy-style-llm-wiki) lists a "Create Wiki" skill that scaffolds a three-layer workspace inside a project repo (secondary).

**Popularity of the source idea**
- The gist reportedly has about 16M views and 1,061 comments — [Omid Sayfun, 2026-08-17](https://omiid.me/notebook/66/i-read-all-1-061-comments-on-karpathy-s-llm-wiki-gist)

### Inferences
- The ecosystem split into three styles. **Prompt-only skills**: Astro-Han, Hermes, second-brain, SamurAIGPT. **Skills plus a deterministic CLI or scripts**: claude-obsidian, Ar9av, kfchou, compozy/kb, toolboxmd. **Standalone apps and compilers**: nashsu, atomicstrata, lucasastorian. ms-kb already belongs to the second group (a `kb` CLI plus skills). The closest structural peers are kfchou/wiki-skills (git-native, generated index, commit-time gates), compozy/kb (a Go `kb` CLI, the successor of pedronauck's skill) and claude-obsidian (Python core, transactions, hooks).
- Star counts track marketing reach (desktop apps, "second brain" branding) more than design quality. Several small repos (kfchou 189★, ussumant 327★, student-llm-wiki 177★) hold the most transferable ideas.

### Gaps
- Install counts were visible only on skills.sh, and only for `karpathy-kb` (25). No install or usage numbers were available for the Hermes skill or for the plugin marketplaces.
- I found no Hacker News thread. One secondary source claims a Karpathy "idea file" HN post got 76 points and 20 comments, but I could not verify it ([PromptZone](https://www.promptzone.com/noemi_patel/llm-idea-file-karpathys-example-1871)). Searches surfaced no Reddit threads (r/ObsidianMD, r/ClaudeAI, r/LocalLLaMA). Community discussion seems concentrated in the gist comments, Medium/Substack and Chinese/Korean outlets.
- The publication date is reported inconsistently. The gist page shows 2026-04-04. A blog says an X post on April 3 came first ([yu-wenhao](https://yu-wenhao.com/zh-TW/blog/karpathy-zettelkasten-comparison/)). Yatesweb says "April 2, 2026" ([yatesweb](https://www.yatesweb.com/adding-quality-control-to-andrej-karpathys-llm-wiki/)).

## 2. How the notable implementations work

### Takeaway
Almost all of them keep the gist's raw/wiki/schema split, index.md, log.md and ingest/query/lint. They differ in four ways:
- **What is deterministic.** Some use only prompts. Others use scripts or a CLI for the index, lint, links and commits.
- **How existing text is changed.** Options are silent rewrite, diff-and-approve, or Status blocks that keep the old claim.
- **Whether the index and log are written by hand or generated.** Generated options are frontmatter → index and git → log.
- **How pages are chosen.** Options are orientation reads, search-before-create, triage dispositions and cascade sweeps.

### Cited Findings

**pedronauck `karpathy-kb` (last version before migration; prompts plus 2 scripts)**
- Layout: one top-level folder per topic, each with `raw/{articles,bookmarks,github}`, `wiki/{concepts,index}`, `outputs/{briefings,queries,diagrams,reports}`, `bases/`, a topic `log.md` and a topic `CLAUDE.md` (symlinked to AGENTS.md) that acts as the schema. All topics share one vault — [SKILL.md](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)
- It adds a fourth phase, giving "ingest → compile → query → lint". `scripts/new-topic.sh` scaffolds a topic. `scripts/lint-wiki.py` reports dead wikilinks, orphans and missing source files. Lint reports are saved as dated files in `outputs/reports/` — [SKILL.md](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)
- Each topic has three index pages: Dashboard (counts plus Obsidian Base embeds), Concept Index (alphabetical, one-line summaries) and Source Index (source → article backlinks). The topic `CLAUDE.md` keeps a "current articles" list — [SKILL.md](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)
- Compile flow:
  - Before drafting, it shows the user 3–5 takeaways and any contradictions, then asks "Anything specific to emphasize or de-emphasize?"
  - Target length is 3000–4000 words with 10–30 wikilinks.
  - A mandatory "backlink audit" greps all articles for the new title and adds `[[New Article]]` at the first mention ("the step most commonly skipped").
  - Sources: [SKILL.md](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md); [compilation-guide](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/references/compilation-guide.md)
- Updating an existing article:
  - Each change is proposed as **Current / Proposed / Reason / Source**, with confirmation per page ("Do not batch-apply changes").
  - Then a **contradiction sweep** (grep every article for the contradicted claim) and a **downstream check** (grep `[[Article]]` inbound links and ask whether each linking page's assertions change).
  - Source: [compilation-guide](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/references/compilation-guide.md)
- Split and new-page rules:
  - Split when an article passes 4000 words, an H2 section passes 1000 words, or other articles want to link to a sub-section.
  - Write a new article when 3+ articles have dead links to the concept or queries keep re-synthesizing the same material.
  - Extend instead when the sub-topic would be under 500 words.
  - Source: [compilation-guide](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/references/compilation-guide.md)
- Query: read the Concept Index first and never answer from general knowledge. Follow at most one hop of wikilinks. Always save answers to `outputs/queries/<date> <slug>.md` with `informed_by:`. "Promote" durable answers into `wiki/concepts/`. Search with qmd once a topic has about 20+ sources, otherwise use grep and the index — [SKILL.md](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)
- Log ops are `ingest|compile|query|lint|promote|split`. Git and log.md "coexist: git records *what changed*, `log.md` records *what the knowledge base did*" — [SKILL.md](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)
- Successor `compozy/kb` (Go CLI):
  - Commands: `kb topic new`, `kb ingest url|file|youtube|…`, `kb classify`, `kb link` ("Write typed relations and backlinks"), `kb find --explain`, `kb review` queues, `kb lint --save` ("never calls a model"), `kb search` via qmd.
  - "Nothing is deleted": gated sources move to `raw/_quarantine/` and can be restored byte for byte.
  - A "decision model" called through an OpenRouter key gates and classifies sources. The agent still writes the articles.
  - Sources: [SKILL.md](https://github.com/compozy/kb/blob/main/skills/kb/SKILL.md); [README](https://github.com/compozy/kb)

**Hermes `llm-wiki` (prompts only)**
- Layout: `SCHEMA.md`, `index.md`, `log.md`, `raw/{articles,papers,transcripts,assets}`, `entities/`, `concepts/`, `comparisons/`, `queries/`. The location comes from `WIKI_PATH` (default `~/wiki`) — [SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
- Orientation is required "every session": read SCHEMA.md, index.md and the last 20–30 log entries before any operation, "to prevent duplicate pages". With 100+ pages, also search before creating — [SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
- Frontmatter: `title, created, updated, type, tags, sources`, plus optional `confidence: high|medium|low`, `contested: true` and `contradictions: [slug]`. Raw files carry `source_url, ingested, sha256` to detect drift on re-ingest. Pages synthesizing 3+ sources get paragraph-level provenance markers `^[raw/articles/x.md]` — [SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
- Rules:
  - Create a page only when the entity is in 2+ sources or central to one.
  - At least 2 outbound wikilinks per page.
  - Tags must come from a taxonomy declared in SCHEMA.md first.
  - Split pages over ~200 lines ("readable in 30 seconds").
  - Archive superseded pages to `_archive/` and replace inbound links with plain text "(archived)".
  - "Ask before mass-updating — if an ingest would touch 10+ existing pages".
  - Source: [SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
- Index scaling: split a section past 50 entries. Past 200 entries, create `_meta/topic-map.md` grouping pages by theme. Rotate `log.md` to `log-YYYY.md` past 500 entries — [SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
- Lint has 13 checks, including orphans, broken links, index completeness, frontmatter/taxonomy, stale pages (>90 days older than the newest source mentioning the same entities), contested/low-confidence pages, source sha256 drift, page size and log rotation. It reports by severity — [SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)

**Astro-Han/karpathy-llm-wiki (prompts plus one checker script)**
- Layout: `raw/<topic>/YYYY-MM-DD-slug.md` and `wiki/<topic>/<article>.md`, with "one level only" of topic directories. A global `wiki/index.md` has a row per article (link + summary + Updated) plus `wiki/log.md`. The SKILL.md itself is the schema — [SKILL.md](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)
- **Triage before writing**: search the wiki for the source's entities and synonyms, then state a disposition of New / Update / Disputed / **No material** ("Do not force an article out of a thin source"; the raw file is kept and only logged) — [SKILL.md](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)
- Compile: merge into an article with the "same core thesis"; otherwise create a new concept article named after the concept. Content spanning topics goes in the most relevant directory with See Also links. **Cascade updates**: search the full wiki (not just the index) and update every materially affected article — [SKILL.md](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)
- No silent rewrites. Superseded claims stay in place with a `> **Status: Outdated** (date)` block; conflicts get `> **Status: Disputed**`. Article header: `> Sources:` / `> Raw:` / `> Updated:` (Updated changes only on knowledge changes, "not typo or formatting fixes"). An optional `## See Also` section is maintained during lint — [article-template](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/references/article-template.md)
- "Grounding invariant": every number, date and quote must be found in the linked raw file *before* it is written. `scripts/check_evidence.py` greps high-signal literals (quotes of 15+ characters, ISO dates, specific numbers) against the linked raws. It only reports and never edits — [SKILL.md](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md); [check_evidence.py](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/scripts/check_evidence.py)
- Query writes nothing unless asked. An archived answer always becomes a *new* page with `[Archived]` in the index and is never cascade-updated. Recall rule: "Never claim the wiki has no relevant content until both the index and the full-text search come back empty — and say that you searched" — [SKILL.md](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)
- Lint has three authority tiers: **safe auto-fixes** (index consistency, fixing a link path when exactly one match exists), **mechanical reports** (the evidence script) and **judgment reports** (contradictions, missing cross-references "suggest them; do not add silently", orphans, concepts lacking a page) — [SKILL.md](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)
- Research mode: searching may run in parallel, but "compilation must not — compile one source at a time, because index.md, log.md, and cascade updates are shared state". It deliberately searches "the opposing side" for core claims — [SKILL.md](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)

**AgriciDaniel/claude-obsidian (skills plus a Python transaction core plus hooks)**
- Vault layout: `inbox/`, `.raw/` (immutable, content-addressed copies), `wiki/`, `.vault-meta/` and `.claude-obsidian.json`. The product checkout is never treated as a vault — [README](https://github.com/AgriciDaniel/claude-obsidian)
- "One logical knowledge operation is one recoverable transaction":
  1. Read targets and record their SHA-256.
  2. Parallel workers return drafts only.
  3. Merge the drafts into one bundle.
  4. Inspect the bundle, then apply it once.
  5. Report the operation ID and changed paths.
  - Mutating commands print a JSON plan and apply only with `--approved-plan-sha256`.
  - A target that changed meanwhile is "a conflict, never a silent overwrite".
  - "Git checkpoints … remain explicit operations".
  - Source: [README](https://github.com/AgriciDaniel/claude-obsidian)
- Hooks: `SessionStart` (matcher `startup|resume|clear|compact`) and `Stop`, both calling the core CLI with a 5 s timeout — [hooks.json](https://github.com/AgriciDaniel/claude-obsidian/blob/main/hooks/hooks.json)
- Provenance: a separate `source-ledger.json` (authority `official|primary|secondary|community|synthetic|unknown`, SHA-256, `refresh_due`) and `claim-ledger.json` (assessment `accepted|provisional|contested|unsupported|deprecated`). "High-risk accepted claims need two independent sources". "Never fabricate quotations, page numbers, dates" — [provenance.md](https://github.com/AgriciDaniel/claude-obsidian/blob/main/skills/wiki/references/provenance.md)
- `save` skill (closest analogue to ms-kb's `add-knowledge`):
  - Saves "only the scope the user selected. Never run automatically, capture a whole transcript".
  - Reads `wiki/hot.md`, `wiki/index.md` and "at most five directly relevant pages".
  - "Search for an existing note before creating one. Prefer a small update over a duplicate. Obtain explicit approval before replacing an existing canonical note".
  - "Conversation assertions are not independent evidence" and cannot make a claim `accepted`.
  - One Save transaction updates the note, the index, a log entry, and a refreshed `wiki/hot.md` "under 500 words".
  - Source: [save/SKILL.md](https://github.com/AgriciDaniel/claude-obsidian/blob/main/skills/save/SKILL.md)
- `wiki-fold` produces extractive rollups of log batches (2^k entries) without touching child pages — [wiki-fold/SKILL.md](https://github.com/AgriciDaniel/claude-obsidian/blob/main/skills/wiki-fold/SKILL.md). `wiki-mode` routes new notes under Generic, LYT (MOCs), PARA or Zettelkasten conventions "without bulk-moving existing knowledge". `wiki-retrieve` does BM25 with optional cosine reranking — [README](https://github.com/AgriciDaniel/claude-obsidian)

**Ar9av/obsidian-wiki (39 skills plus a Python CLI and library)**
- Commands:
  - Ingest and capture: `/wiki-ingest`, `/wiki-update` (distill the current repo), `/wiki-capture` ("save this conversation"), `/wiki-history-ingest claude` ("mine everything you've ever asked Claude").
  - Ask: `/wiki-query`, `/wiki-narrate`, `/wiki-digest week`.
  - Maintain: `/wiki-lint`, `/wiki-dedup`, `/cross-linker`, `/wiki-status`.
  - Source: [README](https://github.com/Ar9av/obsidian-wiki)
- Session hooks are registered by `obsidian-wiki setup`. Session start injects "who you are and what's open". Session end captures "anything reusable". `index.md`, `log.md`, `hot.md`, the owner profile and the todo index all go through "one writer that takes a lock and writes atomically" — [README](https://github.com/Ar9av/obsidian-wiki)
- Additions it lists itself:
  - A delta manifest so only changed sources are re-ingested.
  - Identity resolution (`wiki-dedup` merges "RSC" and "React Server Components").
  - Automated cross-linking of unlinked mentions.
  - A tag taxonomy in `_meta/taxonomy.md`.
  - Per-claim provenance tags: extracted (default), `^[inferred]`, `^[ambiguous]`, with lint flagging pages "drifting into mostly speculation".
  - A trust ledger for human-approved reviews.
  - Tiered retrieval: titles, tags and summaries first, bodies only if needed.
  - Graph insights (hubs, bridge pages).
  - An "equilibrium" mode that detects maintenance skills undoing each other.
  - `WIKI_STAGED_WRITES=true` queues LLM pages in `_staging/` for review.
  - Source: [architecture.md](https://github.com/Ar9av/obsidian-wiki/blob/main/docs/architecture.md)

**kfchou/wiki-skills (Claude Code plugin, git-native)**
- Layout: `SCHEMA.md`, `bin/` helper scripts, `raw/`, `wiki/index.md` (generated), `wiki/overview.md` ("evolving synthesis"), and a flat `wiki/pages/` named by slug — [README](https://github.com/kfchou/wiki-skills)
- "The index is generated, not hand-maintained". `bin/generate-index.py` rebuilds it from each page's `category` and `summary` frontmatter, and the file is gitignored ("never drifts … no merge conflicts") — [README](https://github.com/kfchou/wiki-skills)
- "The operation log comes from git". Each operation is a commit with a `Wiki-Op:` trailer, and `render-log.py` renders history on demand. Skills "suggest the commit and commit on your confirmation — they never auto-commit". A tracked pre-commit hook (`core.hooksPath bin/hooks`) blocks commits that have unresolved contradiction flags, missing frontmatter, broken `[[links]]` or slug collisions — [README](https://github.com/kfchou/wiki-skills)
- `wiki-update` "always shows diffs before writing, always cites the source … sweeps all pages for the same stale claim". `wiki-ingest` asks what to emphasize before writing and runs a backlink audit. `wiki-merge` folds duplicates and rewrites every inbound link, or splits an overloaded slug (`mercury-planet` / `mercury-element`) — [README](https://github.com/kfchou/wiki-skills)
- `wiki-audit`: Phase A flags uncited claims. Phase B dispatches "one subagent per source in parallel" to verify footnotes. `strong` mode adds a different-provider review (codex or gemini CLI) — [README](https://github.com/kfchou/wiki-skills)

**ussumant/llm-wiki-compiler (Claude Code plugin; topic-based)**
- It compiles many sources into **one article per topic** under `topics/`, plus cross-cutting `concepts/` articles for patterns that appear in 3+ topics, plus `INDEX.md` and a generated, user-editable `schema.md`. Example: "383 files · 13 MB" → "13 articles · 161 KB"; per-session reads drop from ~3,200 lines to ~330 lines (author's own figures) — [README](https://github.com/ussumant/llm-wiki-compiler)
- At `/wiki-init` the plugin samples sources and **proposes a per-domain section template**, which the user approves. Example for research: Summary, Key Findings, Methodology, Evidence, Gaps & Contradictions, Open Questions, Sources. "Summary and Sources are always included" — [README](https://github.com/ussumant/llm-wiki-compiler)
- **Coverage indicators** on every section, e.g. `## Summary [coverage: high -- 15 sources]` (high 5+, medium 2–4, low 0–1). This tells the agent when to fall back to raw sources — [README](https://github.com/ussumant/llm-wiki-compiler)
- **Time-decay awareness**: claims older than 18 months on fast-moving topics get ⚠️ and `[as of YYYY-MM]` tags; stable topics use 24/48 months; "Nothing gets deleted" — [README](https://github.com/ussumant/llm-wiki-compiler)
- **Staged adoption through a SessionStart hook** in three modes: `staging` ("Wiki available"), `recommended` ("check wiki before raw files") and `primary`. It "never modifies your existing CLAUDE.md". There is a global wiki at `~/Knowledge` and per-repo local wikis — [README](https://github.com/ussumant/llm-wiki-compiler)

**nvk/llm-wiki (Claude Code and Codex plugin)**
- A hub `~/wiki/` with `wikis.json` and isolated topic wikis under `topics/<name>/` (each with inbox, raw, wiki/{concepts,topics,references}, output, `schema.md`, `log.md`). "One topic, one wiki … No cross-topic noise"; queries "peek at sibling wiki indexes" — [README](https://github.com/nvk/llm-wiki)
- Other features:
  - Parallel research agents (5 standard, 8 `--deep`, 10 "retardmax").
  - `/wiki:thesis` with supporting and opposing agent split and a verdict.
  - Query depths quick/standard/deep.
  - Dual links on every cross-reference: `[[slug|Title]] ([Title](../concepts/slug.md))`.
  - High/medium/low confidence per article.
  - Session capture to `.sessions/` and "lessons learned" extraction from the current session.
  - `llm-wiki lint --fail-on critical|warning|suggestion`.
  - Source: [README](https://github.com/nvk/llm-wiki)

**NicholasSpisak/second-brain and SamurAIGPT/llm-wiki-agent (templates)**
- second-brain layout: `raw/`, `wiki/{sources,entities,concepts,synthesis}`, `index.md`, `log.md`, `output/`, `CLAUDE.md`. The wizard generates a config per agent. qmd is used "automatically when available". Advice: lint "after every 10 ingests or monthly" — [README](https://github.com/NicholasSpisak/second-brain)
- llm-wiki-agent adds `overview.md` ("living synthesis"), `syntheses/` for filed answers, `graph/graph.json` (SHA256-cached) with a vis.js `graph.html`, and markitdown conversion of PDF/DOCX/PPTX at ingest — [README](https://github.com/SamurAIGPT/llm-wiki-agent)

**IssacW228/student-llm-wiki (learning-oriented)**
- Layout: `wiki/{concepts,courses,sources,exam-prep}`, `connections-log.md` (cross-course links found), `contradictions.md`, `glossary.md`, `overview.md`, `index.md`, `hot.md` ("AI context cache, read first each session"), plus a Dataview `Home.md` dashboard. Ingest is deduplicated by file hash — [README](https://github.com/IssacW228/student-llm-wiki)
- Concept-page frontmatter includes `confidence: low|medium|high` and `last_reviewed`. Section order: Intuition (Feynman-style) → Detailed → optional Diagram → Why it matters → Connections (incl. cross-course) → Sources → Open Questions. Course pages list weak concepts through Dataview `confidence=low`. `hot.md` (≤500 words) holds the last 3 sources, recent concepts, current weak concepts and todo — [wiki-core SKILL.md](https://github.com/IssacW228/student-llm-wiki/blob/main/.claude/skills/wiki-core/SKILL.md)
- `wiki-review` ("Feynman-technique review mode"):
  - It reviews low/medium-confidence concepts first.
  - Questions ask "why" and "what if" rather than "what is".
  - A good answer raises `confidence` and updates `last_reviewed`; gaps keep or lower it.
  - Practice questions go to `wiki/exam-prep/<course>.md` for concepts still low.
  - Source: [wiki-review SKILL.md](https://github.com/IssacW228/student-llm-wiki/blob/main/.claude/skills/wiki-review/SKILL.md)

**toolboxmd/karpathy-wiki (hooks plus background worker)**
- The agent writes "a small capture file". A detached background worker processes it into the git-versioned wiki. CLI commands: `wiki capture|ingest-now|status|issues|doctor|scheduler install` (one macOS LaunchAgent). `wiki use project|main|both`; in "both" mode the worker keeps repo-specific knowledge local or "publishes one generalized, provenance-linked capture to the main wiki" — [README](https://github.com/toolboxmd/karpathy-wiki)

### Inferences
- **Rewrite vs append.** The mature implementations allow in-place rewriting of compiled pages but gate it in one of three ways: diff and approval (karpathy-kb, kfchou, claude-obsidian), visible Status/Outdated blocks (Astro-Han), or supersession markers (ussumant, Hermes `contradictions:`). This matches the user's decision to let a topic page be rewritten, provided changed claims stay visible or approved.
- **Choosing pages to touch.** Three techniques recur. Orientation reads (index + recent log + schema) come first. Then search-before-create with synonyms. Then a bounded cascade: Hermes asks before touching 10+ pages, and claude-obsidian reads at most 5 pages for a save. The user's "one main page plus targeted link edits on neighbours" is a stricter version of the same bound.
- **Index and log.** The more engineered implementations (kfchou, compozy/kb, Ar9av) take index and log maintenance away from the LLM: generated index, git-derived log, a single locked writer. ms-kb already does this partly, with a git commit per write carrying provenance trailers.

### Gaps
- I did not read the full skill text of sdyckjq-lab/llm-wiki-skill (2.5k★, Chinese), lucasastorian/llmwiki, swarmvault, shannhk/llm-wikid or tonbistudio, so their design specifics are not covered.
- claude-obsidian's `hot.md` refresh logic and the exact behaviour of its SessionStart hook were not read beyond `hooks.json` and the `save` skill.

## 3. What implementations add beyond the gist, and fit for ms-kb

### Takeaway
The additions that recur most are:
- generated or controlled indexes;
- diff-and-approve or Status blocks instead of silent rewrites;
- backlink/cross-link audits and dedup/merge tools;
- page-size and split rules;
- claim-level provenance or confidence;
- a small "hot" context file and SessionStart hooks;
- "save this conversation" skills;
- deterministic lint scripts and commit gates;
- learning-specific review modes (Feynman quiz, confidence/`last_reviewed`).

For a Claude Code–driven personal learning KB with one consolidated page per topic, the best fits look like: a per-topic page template with Open Questions and Related sections, a diff before rewriting, a link audit limited to neighbours, a CLI-generated index/hub, mastery or review fields with a review/quiz mode, and the "No material" triage outcome. Claim ledgers, vector search, parallel research swarms and access-decay scoring look like overkill at this scale. One mature implementation explicitly rejects several of them.

### Cited Findings (feature → where seen)

**Structure and navigation**
- *Compile phase separate from ingest, plus `outputs/` folders for filed queries, briefings and lint reports*: [karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md); `output/` in [second-brain](https://github.com/NicholasSpisak/second-brain)
- *Topic-based compiled articles (one article per topic synthesizing all sources) plus cross-topic "concept" articles for patterns in 3+ topics*: [ussumant](https://github.com/ussumant/llm-wiki-compiler)
- *Per-topic sub-wikis with isolated indexes and a hub registry*: [nvk](https://github.com/nvk/llm-wiki); per-topic folders with their own `CLAUDE.md`: [karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)
- *Topic maps / MOCs*: `_meta/topic-map.md` once the index passes 200 entries ([Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)); LYT mode with Maps of Content and Canvas maps ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)); Dashboard / Concept Index / Source Index ([karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)); hub and bridge-page analysis ([Ar9av](https://github.com/Ar9av/obsidian-wiki/blob/main/docs/architecture.md))
- *Obsidian Bases / Dataview views*: a `bases/` folder and Base embeds in the Dashboard ([karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)); an `obsidian-bases` skill ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)); a Dataview Home listing `confidence=low` concepts ([student-llm-wiki](https://github.com/IssacW228/student-llm-wiki/blob/main/.claude/skills/wiki-core/SKILL.md))
- *Generated index (from frontmatter `summary`/`category`, gitignored)*: [kfchou](https://github.com/kfchou/wiki-skills)
- *`overview.md` / living synthesis page*: [kfchou](https://github.com/kfchou/wiki-skills), [SamurAIGPT](https://github.com/SamurAIGPT/llm-wiki-agent), [student-llm-wiki](https://github.com/IssacW228/student-llm-wiki)
- *Dual link format `[[slug|Title]] ([Title](path.md))` so links work outside Obsidian*: [nvk](https://github.com/nvk/llm-wiki)
- *Graph export and visualization (graph.json/html, GraphML, Canvas)*: [SamurAIGPT](https://github.com/SamurAIGPT/llm-wiki-agent), [Ar9av](https://github.com/Ar9av/obsidian-wiki), [ussumant](https://github.com/ussumant/llm-wiki-compiler)

**Write discipline**
- *Takeaways or emphasis question before drafting*: [karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md), [kfchou](https://github.com/kfchou/wiki-skills) (also in the gist as "discuss takeaways")
- *Per-change diff with Current / Proposed / Reason / Source, confirmed per page*: [karpathy-kb compilation-guide](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/references/compilation-guide.md); "always shows diffs before writing" ([kfchou](https://github.com/kfchou/wiki-skills)); plan-hash approval ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)); `_staging/` review queue ([Ar9av](https://github.com/Ar9av/obsidian-wiki/blob/main/docs/architecture.md)); review queue before publishing ([atomicstrata](https://github.com/atomicstrata/llm-wiki-compiler))
- *Status: Outdated / Disputed blocks that keep the old claim*: [Astro-Han](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/references/article-template.md); `contested`/`contradictions:` frontmatter ([Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)); a dedicated `contradictions.md` ([student-llm-wiki](https://github.com/IssacW228/student-llm-wiki))
- *Triage dispositions including "No material"*: [Astro-Han](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)
- *Page-creation thresholds (2+ sources or central to one) and split rules (~200 lines; or 4000 words / 1000-word H2)*: [Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md); [karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/references/compilation-guide.md)
- *Per-domain section templates proposed at init and approved by the user*: [ussumant](https://github.com/ussumant/llm-wiki-compiler)
- *Single serialized writer / lock / atomic writes; compile serially even when research runs in parallel*: [claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian), [Ar9av](https://github.com/Ar9av/obsidian-wiki), [Astro-Han](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)

**Links, duplicates and lint**
- *Backlink audit after every new page (grep mentions, add `[[link]]` at the first mention)*: [karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/references/compilation-guide.md), [kfchou](https://github.com/kfchou/wiki-skills); automated `cross-linker` ([Ar9av](https://github.com/Ar9av/obsidian-wiki)); deterministic `kb link` writing typed relations and backlinks ([compozy/kb](https://github.com/compozy/kb/blob/main/skills/kb/SKILL.md))
- *"See Also" section maintained by lint; missing cross-references suggested, not silently added*: [Astro-Han](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)
- *Minimum outbound links (≥2 per page)*: [Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
- *Dedup / identity resolution and merge or split with inbound-link rewriting*: `wiki-dedup` ([Ar9av](https://github.com/Ar9av/obsidian-wiki/blob/main/docs/architecture.md)); `wiki-merge` ([kfchou](https://github.com/kfchou/wiki-skills))
- *Controlled tag taxonomy (declare before use)*: [Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md), [Ar9av](https://github.com/Ar9av/obsidian-wiki/blob/main/docs/architecture.md)
- *Deterministic lint scripts; lint reports saved as dated files*: `lint-wiki.py` ([karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)); `lint-mechanical.py` ([kfchou](https://github.com/kfchou/wiki-skills)); `kb lint --save` "never calls a model" ([compozy/kb](https://github.com/compozy/kb/blob/main/skills/kb/SKILL.md)); `lint --fail-on` ([nvk](https://github.com/nvk/llm-wiki))
- *Commit-time gates (pre-commit blocks broken links or unresolved contradictions)*: [kfchou](https://github.com/kfchou/wiki-skills)
- *Lint authority tiers (auto-fix / mechanical report / judgment report)*: [Astro-Han](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)
- *Equilibrium check (maintenance skills undoing each other)*: [Ar9av](https://github.com/Ar9av/obsidian-wiki/blob/main/docs/architecture.md)

**Provenance, confidence and staleness**
- *Claim-level provenance markers*: `^[raw/…]` per paragraph on multi-source pages ([Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)); extracted / `^[inferred]` / `^[ambiguous]` ([Ar9av](https://github.com/Ar9av/obsidian-wiki/blob/main/docs/architecture.md)); citations with line ranges ([atomicstrata](https://github.com/atomicstrata/llm-wiki-compiler)); source and claim ledgers ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian/blob/main/skills/wiki/references/provenance.md))
- *Grounding check of numbers, dates and quotes against raw*: [Astro-Han check_evidence.py](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/scripts/check_evidence.py); per-source subagent verification and cross-model review ([kfchou wiki-audit](https://github.com/kfchou/wiki-skills))
- *Confidence levels*: page-level high/medium/low ([Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md), [nvk](https://github.com/nvk/llm-wiki)); section-level coverage badges ([ussumant](https://github.com/ussumant/llm-wiki-compiler)); decaying confidence with reinforcement ([LLM Wiki v2 gist, rohitg00](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2))
- *Stale-claim detection*: page older than its newest source by >90 days ([Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)); 18-month aging flags and `[as of YYYY-MM]` ([ussumant](https://github.com/ussumant/llm-wiki-compiler)); `refresh_due` per source ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian/blob/main/skills/wiki/references/provenance.md)); `llmwiki refresh --stale` ([atomicstrata](https://github.com/atomicstrata/llm-wiki-compiler))
- *Raw-source immutability rules plus sha256 drift detection*: [Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md); content-addressed `.raw/` ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)); quarantine instead of deletion ([compozy/kb](https://github.com/compozy/kb/blob/main/skills/kb/SKILL.md))

**Session integration, capture and query**
- *SessionStart/Stop hooks injecting wiki context or capturing at session end*: [claude-obsidian hooks.json](https://github.com/AgriciDaniel/claude-obsidian/blob/main/hooks/hooks.json); [Ar9av](https://github.com/Ar9av/obsidian-wiki); staged modes ([ussumant](https://github.com/ussumant/llm-wiki-compiler)); [toolboxmd](https://github.com/toolboxmd/karpathy-wiki)
- *`hot.md` context cache (≤500 words, read first each session)*: [claude-obsidian save](https://github.com/AgriciDaniel/claude-obsidian/blob/main/skills/save/SKILL.md), [Ar9av](https://github.com/Ar9av/obsidian-wiki), [student-llm-wiki](https://github.com/IssacW228/student-llm-wiki/blob/main/.claude/skills/wiki-core/SKILL.md)
- *"Save this conversation" skills*: scoped explicit `save` ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian/blob/main/skills/save/SKILL.md)); `/wiki-capture` and `/wiki-history-ingest` ([Ar9av](https://github.com/Ar9av/obsidian-wiki)); lessons learned (`@wiki ll`) ([nvk](https://github.com/nvk/llm-wiki)); capture files plus a background worker ([toolboxmd](https://github.com/toolboxmd/karpathy-wiki)); session transcripts → wiki ([Pratiyush](https://github.com/Pratiyush/llm-wiki)); "crystallization" of finished sessions into digests ([LLM Wiki v2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2))
- *Question/answer filing*: always file to `outputs/queries/` and promote durable answers ([karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md)); file only on request, as a new `[Archived]` page that is never cascade-updated ([Astro-Han](https://github.com/Astro-Han/karpathy-llm-wiki/blob/main/SKILL.md)); file only answers "painful to re-derive" ([Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md))
- *Read-only "ask the wiki" commands*: `$wiki-query` "never activates implicitly or changes wiki files" ([nvk](https://github.com/nvk/llm-wiki)); `wiki-query` "answers read-only" ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)); `/wiki-narrate` briefings and `/wiki-digest week` ([Ar9av](https://github.com/Ar9av/obsidian-wiki))
- *Tiered or one-hop retrieval*: titles, tags and summaries first ([Ar9av](https://github.com/Ar9av/obsidian-wiki/blob/main/docs/architecture.md)); one wikilink hop max ([karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md))
- *Search tools*: qmd ([karpathy-kb](https://github.com/pedronauck/skills/blob/777f89082bef1626e59bd4622fec54c8fd222a7a/skills/karpathy-kb/SKILL.md), [second-brain](https://github.com/NicholasSpisak/second-brain), [compozy/kb](https://github.com/compozy/kb)); BM25 ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)); grep-only by design ([Astro-Han](https://github.com/Astro-Han/karpathy-llm-wiki), [Hermes](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)); hybrid semantic + BM25 + graph ([atomicstrata](https://github.com/atomicstrata/llm-wiki-compiler))
- *Subagents and parallel research*: parallel research agents and thesis mode ([nvk](https://github.com/nvk/llm-wiki)); one subagent per source for audits ([kfchou](https://github.com/kfchou/wiki-skills)); workers return drafts and one orchestrator applies them ([claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian))

**Learning-specific features**
- *Feynman review mode that adjusts `confidence` and `last_reviewed`; exam-prep practice questions for weak concepts; Mermaid diagram command; cross-course connections log; glossary*: [student-llm-wiki](https://github.com/IssacW228/student-llm-wiki/blob/main/.claude/skills/wiki-review/SKILL.md)
- I found no general LLM-wiki implementation with built-in flashcards or spaced repetition. The closest are separate Obsidian plugins (Spaced Repetition, Flashcards LLM, Flashcard Gen) and standalone Claude "flashcards" skills (secondary, via search summary: [Obsidian community plugins](https://community.obsidian.md/plugins/obsidian-spaced-repetition), [claudskills flashcards](https://claudskills.com/skills/flashcards/)). "Forgetting" via an Ebbinghaus-style curve is proposed in [LLM Wiki v2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) for *knowledge* retention, not learner memory.

**Explicit "do not build" list from a mature implementation**
- Astro-Han's "Design Boundaries" come from "three months of production logs and a survey of the ecosystem". It deliberately does not build:
  - source-hash freshness tracking;
  - line-number citations;
  - "numeric confidence or quality scores — false precision";
  - "per-article review dates";
  - "access-based decay — frequently asked is not the same as true";
  - automatic hooks or scheduled runs ("belong to the agent harness, not a tool-agnostic skill");
  - vector or graph search ("at 50K–100K tokens of curated wiki, grep and read are more reliable");
  - typed relationship ontologies ("link semantics live in the prose");
  - MCP servers or UIs.
  - Source: [README](https://github.com/Astro-Han/karpathy-llm-wiki)

### Inferences (fit assessment for ms-kb, my judgment)
Context: one consolidated page per topic, explicit inter-topic links, use for review and learning, Claude Code first, a `kb` CLI that already does search/new/extend/validate/commit-per-write.

**High fit**
- **Per-topic page template with fixed sections.** A ussumant-style template such as Summary → Key ideas → Details → Open questions → Related → Sources, with Summary and Sources always present. Optional per-section coverage tags, e.g. `[coverage: low — 1 source]`. This supports one consolidated page per topic and gives kb-recall cues about where the page is thin.
- **Diff before rewrite of the main topic page.** Use the karpathy-kb/kfchou Current → Proposed → Reason → Source pattern, or keep superseded claims with `Status: Outdated`. ms-kb's `extend` is append-only today, so a new "rewrite/consolidate" path would want either a diff shown to the user or a Status-block convention, plus the git commit already in place for `kb restore`.
- **Neighbour link audit limited to links.** Run the backlink audit (grep the new topic's title and aliases in other pages), but only *add* `[[link]]` or a "Related" bullet on neighbours instead of rewriting them. This matches the user's decision. compozy/kb's deterministic `kb link` shows the CLI can own this step, not the model.
- **Generated index / hub page from frontmatter `summary`** (kfchou). This removes index drift, the most-cited failure mode, and fits a CLI that already parses frontmatter. Hermes' `_meta/topic-map.md` / MOC idea fits "make links between related topics explicit" once there are dozens of topics.
- **Triage disposition "No material".** When a research session adds nothing new, log or skip instead of forcing a page (Astro-Han). This helps keep one page per topic concise.
- **Search-before-create with synonyms, and "say that you searched" before claiming absence** (Astro-Han, Hermes orientation). Directly applicable to `add-knowledge` and `kb-recall`. ms-kb already has `find_duplicates`.
- **Learning fields and a review mode.** Add `confidence`/mastery and `last_reviewed` frontmatter plus a Feynman-style quiz that updates them (student-llm-wiki), and an Obsidian Base or Dataview view listing low-confidence or long-unreviewed topics. This is the only surveyed feature set aimed directly at "use the base when reviewing material". It does not need a day-by-day study history: it is state, not a log.
- **Scoped, explicit "save" semantics.** claude-obsidian `save`: never a transcript, read at most ~5 relevant pages, prefer a small update over a duplicate, ask before replacing a canonical note, treat conversation claims as non-independent evidence. These are close to `add-knowledge`'s purpose.

**Medium fit**
- `^[inferred]` vs extracted markers (Ar9av). Useful because ms-kb content comes from AI conversations, not immutable raw sources.
- A tag taxonomy (Hermes, Ar9av).
- Page-size and split thresholds (Hermes ~200 lines; karpathy-kb word caps). Casey Newton's experience ([Platformer](https://www.platformer.news/karpathy-llm-wiki-journalism-productivity/)) and Kunal Ganglani's ([blog](https://www.kunalganglani.com/blog/llm-wiki-karpathy-local-knowledge-base)) show pages grow too long without them.
- Deterministic lint for orphans, broken links and missing Related sections, plus a pre-commit-style gate (kfchou). ms-kb already has `validate` and integrity checks.
- A SessionStart hook in "staging" mode that tells the agent the KB exists (ussumant) instead of always loading content.

**Low fit / likely overkill**
- Claim and source ledgers with authority levels and two-source rules (claude-obsidian).
- sha256 raw drift checks (ms-kb has no immutable raw layer).
- Parallel research swarms and thesis mode (nvk).
- Vector/hybrid search below ~100K tokens of wiki.
- Typed relation ontologies.
- Access-based decay.
- A separate log.md: ms-kb's git history with trailers already plays this role, and the user does not want a study-day history. kfchou also derives the log from git.
- Background capture workers and auto-capture at session end (toolboxmd, Ar9av). These conflict with ms-kb's rule of saving only when the user asks.

### Gaps
- No implementation I found combines "one canonical page per topic, rewritten in place" with "neighbours get link-only edits" as an explicit rule. This combination would be ms-kb's own design.
- I found no measured comparison of append-only vs rewrite-in-place quality over time.

## 4. Security issues reported

### Takeaway
On Tessl, Snyk now rates the Hermes `llm-wiki` skill **Critical** at commit `f86276d`; the brief mentions an earlier "High". The cause is not malicious code. The skill text contains risky *instructions*:
- a link to a third-party CLI repo (flagged as a suspicious download URL);
- an `ob login --password '<password>'` example;
- systemd and `sudo loginctl enable-linger` setup;
- the general prompt-injection exposure of ingesting web content.

The prompt-injection risk applies to every ingest-style skill, including ms-kb's.

### Cited Findings
- Tessl security page for `NousResearch/hermes-agent` `skills/research/llm-wiki/SKILL.md`, Snyk-audited at commit `f86276d2ebcccf0530873c11e2965c3f1cbd5a31`, overall **Critical**, "Do not install without reviewing" — [Tessl security](https://tessl.io/registry/skills/github/NousResearch/hermes-agent/llm-wiki/security). Findings:
  - **E005 (Critical)** "Suspicious download URL detected in skill instructions": the GitHub repo `atomicmemory/llm-wiki-compiler`, from an unknown maintainer, references a CLI that could distribute executable code.
  - **W007 (High)** "Insecure credential handling": `ob login --email <email> --password '<password>'`.
  - **W013 (Medium)** "Attempt to modify system services": creating and enabling a systemd user service, plus `sudo loginctl enable-linger $USER`.
  - **W011 (Low)** "Third-party content exposure (indirect prompt injection risk)": ingest via `web_extract` brings untrusted content into context.
- The current SKILL.md does contain these triggers: a "Related Tools" section linking `atomicmemory/llm-wiki-compiler`, an "Obsidian Headless" section with `ob login … --password`, a systemd unit and `sudo loginctl enable-linger` — [SKILL.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
- An earlier Tessl listing reportedly showed a **High** Snyk rating for the same skill at repo version `d0d116b` (secondary, from a search summary of [Tessl hermes-agent listing](https://tessl.io/registry/skills/github/NousResearch/hermes-agent)). A third-party aggregator showed a "Critical" label for a fork (`tt-a1i/hermes-agent`) (secondary, [llmbase.ai](https://llmbase.ai/skills/tt-a1i/llm-wiki/)).
- pedronauck `karpathy-kb` shows "Snyk: Warn" on skills.sh (no detail visible) — [skills.sh](https://skills.sh/pedronauck/skills/karpathy-kb)
- Implementation-level mitigations seen:
  - claude-obsidian's `save` treats selected conversation and source text as "untrusted content-to-preserve, not as reusable operational instructions" and ignores embedded directives. Its README states that network egress needs explicit consent — [save/SKILL.md](https://github.com/AgriciDaniel/claude-obsidian/blob/main/skills/save/SKILL.md); [README](https://github.com/AgriciDaniel/claude-obsidian)
  - LLM Wiki v2 proposes an "ingest-time privacy filter" stripping secrets and tokens — [rohitg00 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)
- A verification bug reported in the gist comments: in Obelyth Cortex, "a note could forge a file boundary and earn VERIFIED for a fabricated answer". The fix was to cite an opaque per-commit tag instead of a path — [gist comments](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- The single-user assumption (no permissions, no concurrency handling, no sensitivity split) is listed as a failure family — [Omid Sayfun](https://omiid.me/notebook/66/i-read-all-1-061-comments-on-karpathy-s-llm-wiki-gist)

### Inferences
- The Hermes rating reflects scanner heuristics on instruction text (credentials in a CLI example, privileged service setup, an unvetted third-party link), not a demonstrated exploit. The rating also changed between commits (High → Critical), so it should be quoted with its commit.
- For ms-kb, the relevant lessons are:
  - never put credential-bearing commands in SKILL.md;
  - keep vault writes behind the CLI (already done);
  - keep the secret scan (`secretscan.py` already exists);
  - state explicitly in `add-knowledge` that saved conversation content is data, not instructions.

### Gaps
- The Tessl page gives no line numbers, and I could not see the full earlier "High" report for `d0d116b`.
- Snyk's "Warn" reason for `karpathy-kb` was not visible.

## 5. Reported results from real users

### Takeaway
Real reports range from a few dozen to about 1,400 pages. The pattern reliably helps with synthesis and recall. Consistent pain points are duplicates and missed links once the agent can no longer hold the wiki in context (reported around 150–200 pages), index drift, style and naming drift, unflagged contradictions, pages growing too long, and recurring maintenance time. Claude Code is reported as producing better-linked wikis than Codex or Gemini CLI.

### Cited Findings
- **Astro-Han** (skill author's own KB): "94 wiki articles across 13 topic directories, 99 source materials, 87 operation log entries in the last 7 days", "maintained daily since April 2026". Every fidelity error observed was "value absent from the source", which a whole-file grep catches — [README](https://github.com/Astro-Han/karpathy-llm-wiki)
- **Kunal Ganglani** (published 2026-04-15, reviewed 2026-09-16):
  - Three months; 147 pages from 43 sources and ~200 questions; no pages written by hand.
  - Claude Code preferred: "Codex tended to rewrite whole pages", and Gemini CLI cross-linked weakly beyond ~50 pages.
  - What broke: past ~150–200 pages agents "forgot pages existed" (duplicates, missing cross-links); style and naming drift ("transformer" vs "Transformer architecture"); contradictions coexisting for weeks; early pages never revisited; over-linking to nonexistent pages.
  - Fixes and upkeep: list affected pages first, then update only those (2–5 min per source); a master index with one-line summaries ("the biggest improvement"); 30–45 min of maintenance every 2–3 weeks.
  - Source: [blog](https://www.kunalganglani.com/blog/llm-wiki-karpathy-local-knowledge-base)
- **Casey Newton (Platformer, 2026-08-18)**:
  - More than 1,440 pages after about a month, seeded from the Platformer archive.
  - The Meta page passed 12,000 words and 1,300 links.
  - Long pages "need to be compacted". Claude's compressed house style was hard to read, so he rewrote it with another model. He would not confidently recommend the system to others.
  - Source: [Platformer](https://www.platformer.news/karpathy-llm-wiki-journalism-productivity/)
- **podcast-wiki** (gist comment, 2026-10-08): "69 concept pages from 60 episodes … running unattended every few hours". The default failure was near-duplicate pages, so the procedure now checks the index and searches before creating. Advice: never silently overwrite; keep "Disagreements & open questions"; rewrite summaries instead of appending; run a periodic "dream" pass to merge pages that drifted into the same idea — [gist comments](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- **Ar9av benchmark** (author-run; n=2 per cell, one 38-page vault, Claude Sonnet): with the skills, correct answers to structural questions went from 44% to 83% and time from 81 s to 19 s, at about the same cost. The plain agent was misled by `index.md`, which links to every page, into "short paths that mean nothing" — [README](https://github.com/Ar9av/obsidian-wiki)
- **ussumant** (author's figures): per-session reading fell from ~3,200 to ~330 lines after compiling 383 files into 13 topic articles — [README](https://github.com/ussumant/llm-wiki-compiler)
- **Omid Sayfun's survey of 1,061 gist comments** (2026-08-17), with four failure families:
  - "garbage compounds": wrong entries become priors, lost sources, write-only stores, unverified citations;
  - "notes rot against reality": silent supersession, outdated claims, index drift, orphans, unsourced numbers;
  - "relevance is task-relative";
  - "the pattern assumes one user".
  - Recurring fixes: a human promotion gate, timestamps and check dates on external claims, supersession callouts, scheduled lint (the author runs it every other day), scoped corpora, and a word cap on the map file.
  - Source: [omiid.me](https://omiid.me/notebook/66/i-read-all-1-061-comments-on-karpathy-s-llm-wiki-gist)
- **Mick Yates (2026-04-13)**: about 900 sources in 33 folders, ingesting about 10 per session. He uses Claude Cowork + Obsidian with a NUSAP-derived "pedigree matrix" per source in YAML and approval-gated ingestion batches. His motivation: unfiltered links create "an illusion of equal authority" — [yatesweb](https://www.yatesweb.com/adding-quality-control-to-andrej-karpathys-llm-wiki/)
- Secondary (search summaries only, articles not opened):
  - A six-month Obsidian + Claude run with 35 pages: the schema file mattered most; skipping lint after heavy ingest weeks left 3 orphans and an unmarked contradiction by month 3 — [openaitoolshub](https://www.openaitoolshub.org/en/blog/karpathy-llm-wiki)
  - Paulo de Assis: the wiki roughly doubled from April to July, with about a thousand epistemic markers on claims. Direct fetch returned 403 — [Medium](https://medium.com/@paulo.deassis/three-months-of-my-llm-wiki-a-follow-up-and-an-update-43d95cc9246b)
  - Michal Nasternak puts the limit near 100 sources and a few hundred pages, after which ingest "can't reliably tell which existing pages to update" — [Medium](https://michalnasternak.medium.com/the-llm-wiki-at-scale-from-personal-research-tool-to-production-rag-247710a1284c)
  - Affine puts the threshold at 200–500 notes — [Affine](https://affine.pro/blog/llm-wiki)
  - A critic argues LLMs are bad at keeping index.md in sync and suggests rebuilding it during lint — [Nate's Newsletter](https://natesnewsletter.substack.com/p/your-ai-re-derives-everything-it)

### Inferences
- The scale thresholds conflict (about 50K–100K tokens, 150–200 pages, 200–500 notes) and none is validated. They are still consistent with the gist's own "~hundreds of pages" claim.
- A personal learning KB with one page per topic will probably stay well below these limits for a long time.
- The failures most likely to hit ms-kb are drift-type, not scale-type:
  - naming and duplicate topics → dedup on title and aliases;
  - stale or contradicted claims after a page is rewritten → diff and Status blocks;
  - index drift → generated index;
  - pages growing too long → split threshold.
- Reports that Claude Code links better than Codex or Gemini, and that Codex "rewrites whole pages", support keeping rewrites CLI-mediated and diffed when Codex or Cursor are used as secondary clients.

### Gaps
- There are no controlled studies. Almost all numbers are self-reported by authors or bloggers, often promoting their own tool.
- I found no user reports specifically about learning outcomes (retention, review effectiveness) from LLM-wiki review or quiz modes. student-llm-wiki publishes no usage data.
- Searches found no Reddit threads, so community sentiment there could not be assessed.
