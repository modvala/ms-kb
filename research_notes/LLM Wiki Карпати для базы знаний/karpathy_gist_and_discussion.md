# Karpathy's "LLM Wiki" / "LLM Knowledge Bases": the gist, the X posts and the gist discussion

Scope and method (read first):
- Primary sources read in full: the gist text (raw file, 11,985 chars, fetched from `gist.githubusercontent.com`), and **all 1,137 gist comments** (2026-04-04 → 2026-10-08) pulled through the GitHub API (`/gists/442a6bf555914893e9891c11519de94f/comments`, 12 pages). The "~137k characters" figure in the brief corresponds to the HTML page, which shows only part of the thread; the API holds about 1.75M characters of comment text. Every comment was read. Long comments were first read at 1,300–1,500 chars, and about 45 substantive long ones were then read in full.
- Karpathy's X posts were read as primary text through the fxtwitter JSON mirror (`api.fxtwitter.com`), because x.com does not render without JavaScript.
- Labels used below: **[KARPATHY]** means his own words (gist or X). **[COMMENTER @x]** means a gist comment. **[X-REPLY @x]** means someone else on X. Gist URL = G = https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f. Comment links have the form `G#gistcomment-<id>`.

---

## 1. Three layers (raw sources, wiki, schema), and what goes in the schema file

### Takeaway
[KARPATHY] The gist names three layers: immutable **raw sources** (the source of truth, read but never modified by the LLM), **the wiki** (LLM-generated markdown that the LLM "owns entirely"), and **the schema** (CLAUDE.md / AGENTS.md). The schema tells the LLM the wiki structure, the conventions, and the workflows for ingest, query and maintenance, and the human and the LLM co-evolve it. Karpathy gives no concrete schema contents, folder layout or page format. He leaves these to "your domain, your preferences, and your LLM of choice".

### Cited Findings
- [KARPATHY] Raw sources are "your curated collection of source documents. Articles, papers, images, data files. These are immutable — the LLM reads from them but never modifies them. This is your source of truth." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] The wiki is "a directory of LLM-generated markdown files. Summaries, entity pages, concept pages, comparisons, an overview, a synthesis. The LLM owns this layer entirely. It creates pages, updates them when new sources arrive, maintains cross-references, and keeps everything consistent. You read it; the LLM writes it." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] The schema is "a document (e.g. CLAUDE.md for Claude Code or AGENTS.md for Codex) that tells the LLM how the wiki is structured, what the conventions are, and what workflows to follow when ingesting sources, answering questions, or maintaining the wiki." He calls it "the key configuration file — it's what makes the LLM a disciplined wiki maintainer rather than a generic chatbot. You and the LLM co-evolve this over time as you figure out what works for your domain." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] The ingest workflow itself belongs in the schema: "It's up to you to develop the workflow that fits your style and document it in the schema for future sessions." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] The pattern is deliberately unspecified: "This document is intentionally abstract. It describes the idea, not a specific implementation. The exact directory structure, the schema conventions, the page formats, the tooling — all of that will depend on your domain…" and "Everything mentioned above is optional and modular." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] The gist is an "idea file" meant to be pasted into an agent (Codex, Claude Code, OpenCode/Pi). "Your agent will build out the specifics in collaboration with you." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY, X] The original X post does not mention a schema file. It describes a `raw/` directory and an LLM that "incrementally 'compile[s]' a wiki, which is just a collection of .md files in a directory structure." — [X post, 2026-04-02](https://x.com/karpathy/status/2039805659525644595) (text via [fxtwitter mirror](https://api.fxtwitter.com/karpathy/status/2039805659525644595))
- [COMMENTER @None/gnusupport] points out an internal inconsistency: the human co-edits CLAUDE.md, so "the human *does* write some wiki files directly. The actual pattern is: LLM owns content pages; human owns the meta-layer (schema)." The same comment notes that downloading images into the vault modifies the "immutable" raw markdown (URLs change). — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6093292)
- [COMMENTER] Practitioners call the schema the most important artifact:
  - "The schema file is everything… it co-evolved into the single most important file in the repo" (@distorx, ~4,000 concepts) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6223068)
  - "Every correction I give the LLM gets filed back into CLAUDE.md so it never repeats the same mistake" (@denniscarpio30-jpg) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6084790)
  - "The CLAUDE.md schema is the highest-leverage artifact… Worth defining in the schema which files are LLM-owned vs. human-owned" (@aadjadj-bit) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6142662)
- [COMMENTER] Suggested schema contents, compiled from the thread:
  - One template per entity type with required sections (about 7 types was the "sweet spot"), plus a domain tag in frontmatter from day one (@bluewater8008) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079549)
  - Entity/relationship types, how to ingest each kind of source, when to create a page vs update one, quality standards, contradiction handling, consolidation schedule, private vs shared (rohitg00's "LLM Wiki v2", a separate gist) — [LLM Wiki v2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)
- [COMMENTER] Keep CLAUDE.md small and stable, because it is auto-loaded every turn. Put volatile state in wiki pages loaded on demand. One user cut CLAUDE.md from 108 to 26 lines: "rules (auto-loaded, stable, ~30 lines)" vs `wiki/state.md` (session-start context) vs `wiki/*` (on demand) (@benjimixvidz) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102240)
- [COMMENTER] Place the "answer from wiki first" logic directly in CLAUDE.md with explicit fallback steps. This "worked noticeably better for me than routing it through a skill" (@olegiv, 200k-line Go codebase) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6103528)
- [COMMENTER] Schema prose is only an instruction, so enforce what matters in code:
  - "If you want a few specific fields in a particular format, either add them programmatically (like the current date) or make them required parameters in the tool call" (@securityguy) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6372312)
  - IWE / document-schema tools offer "deterministic validation… instead of agent instructions" (@gimalay) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6317613)
- [COMMENTER] Role-mapping pitfall when pasting the gist as a schema: "You" means the human, but agents read "You" as themselves, so remap to "User"/"Assistant" (@justinzhang2039) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6083879)
- [COMMENTER] Some propose a 4th layer: an "infrastructure layer with design records for the agents, rules, hooks, and conventions themselves", once the schema has rationale worth preserving (@n7-ved) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6095277)
- [COMMENTER] Karpathy published no official starter prompt. People asking for "Karpathy's base prompt" were told "there is no official prompt from Karpathy" — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6268995), [reply](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6269557). One user reports that "Claude Code is doing just fine with a basic prompt: Help me set up a LLM wiki that fits my needs and workflows <gist URL>" — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6133573)

### Inferences
- "LLM owns the wiki" really means: the LLM owns content pages, the human owns the schema and source selection. For ms-kb, that maps to: the `kb` CLI + skills are the schema/enforcement layer, topic pages are LLM-written.
- Karpathy specifies *what the schema governs*, not its contents. Every concrete rule (page templates, create-vs-edit rule, contradiction policy) is a community or implementer choice.
- Several practitioners converge on keeping mechanical invariants in deterministic tooling rather than in schema prose. That is close to how ms-kb already splits work (`kb validate`, `kb extend` append-only rules).

### Gaps
- Karpathy has never published his own CLAUDE.md/AGENTS.md or directory tree. Neither the gist (1 revision, never edited) nor the X posts include one.
- He gives no guidance on whether the raw layer should be in the same git repo as the wiki.

---

## 2. Ingest, query and lint: exact steps, pages touched, update style, contradictions, filing answers back

### Takeaway
[KARPATHY] **Ingest**: the LLM reads the source → discusses takeaways with you → writes a summary page → updates the index → updates relevant entity and concept pages "across the wiki" → appends to the log. One source may touch **10–15 pages**. He prefers one source at a time, with supervision.
**Query**: the LLM searches/reads the index, then the relevant pages, then synthesizes an answer with citations in a chosen output format. "Good answers can be filed back into the wiki as new pages."
**Lint**: a periodic health check for contradictions, stale/superseded claims, orphans, missing concept pages, missing cross-references, and data gaps fillable by web search. It also suggests new questions and sources.
Pages are **revised in place** ("updating entity pages, revising topic summaries"), not append-only. Contradictions are "noted"/"flagged", but the gist gives no format and no resolution policy.

### Cited Findings
- [KARPATHY] Ingest flow, verbatim: "the LLM reads the source, discusses key takeaways with you, writes a summary page in the wiki, updates the index, updates relevant entity and concept pages across the wiki, and appends an entry to the log. A single source might touch 10-15 wiki pages." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Supervision preference: "Personally I prefer to ingest sources one at a time and stay involved — I read the summaries, check the updates, and guide the LLM on what to emphasize. But you could also batch-ingest many sources at once with less supervision." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Update semantics (in-place synthesis): when a source is added the LLM "integrates it into the existing wiki — updating entity pages, revising topic summaries, noting where new data contradicts old claims, strengthening or challenging the evolving synthesis. The knowledge is compiled once and then *kept current*, not re-derived on every query." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Compounding claim: "The cross-references are already there. The contradictions have already been flagged. The synthesis already reflects everything you've read." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Query: "The LLM searches for relevant pages, reads them, and synthesizes an answer with citations. Answers can take different forms… a markdown page, a comparison table, a slide deck (Marp), a chart (matplotlib), a canvas." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Filing back: "good answers can be filed back into the wiki as new pages. A comparison you asked for, an analysis, a connection you discovered — these are valuable and shouldn't disappear into chat history. This way your explorations compound in the knowledge base just like ingested sources do." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY, X] Earlier wording of the same idea: "Often, I end up 'filing' the outputs back into the wiki to enhance it for further queries. So my own explorations and queries always 'add up' in the knowledge base." — [X post](https://x.com/karpathy/status/2039805659525644595)
- [KARPATHY] Lint list: "contradictions between pages, stale claims that newer sources have superseded, orphan pages with no inbound links, important concepts mentioned but lacking their own page, missing cross-references, data gaps that could be filled with a web search. The LLM is good at suggesting new questions to investigate and new sources to look for." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY, X] Lint in the X post: "find inconsistent data, impute missing data (with web searchers), find interesting connections for new article candidates, etc., to incrementally clean up the wiki and enhance its overall data integrity." — [X post](https://x.com/karpathy/status/2039805659525644595)
- [KARPATHY] Why LLMs suit this: "LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [COMMENTER] The gist never says who resolves contradictions: "Does the LLM decide automatically (by recency or authority) or flag for human review? The doc is silent." — [@gnusupport](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6093292). Similarly, contradiction policy "is left entirely up to the schema author… becomes the main failure mode" — [@skynet](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6110770)
- [COMMENTER] Ways commenters record contradictions:
  - `[!contradiction]` Obsidian callouts "instead of silently overwriting" (claude-obsidian) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6091186)
  - a "Disagreements & open questions" section with sources, "the most interesting section" (podcast wiki) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6414983)
  - a `questions/` folder; a question stays until a later ingest answers it, then moves to the topic (@403-html) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102269)
  - `open-questions.md` (@bluejaeha) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6253883)
  - severity tokens soft / scope-mismatch / hard. Hard contradictions block the commit through a deterministic grep gate for `Status: Unresolved`, and lint is scoped to changed pages plus their 1st/2nd-degree link neighbours (@hmbseaotter) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6209868)
- [COMMENTER] Contradiction is not always a defect. In humanities, contradiction "is information", so lint should look for *missing* contradictions, and typed `contradicts` edges need a policy that preserves them (@pursultani) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6183984)
- [COMMENTER] Contradiction surfacing seen as the main practical value. A first compile of a Go CMS's docs "surfaced 10 real contradictions in my own documentation… effectively a consistency linter for prose" (@olegiv) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6103528)
- [COMMENTER] "Every task produces two outputs": the deliverable, plus updates to the relevant wiki articles. "If you don't make this explicit in your schema, the LLM will do the work and let the knowledge evaporate into chat history" (@bluewater8008) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079549). The same rule is in xoai/sage-wiki — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6082547)
- [COMMENTER] Write-back is "the single most important part… The knowledge base should grow through use, not just ingestion" (@bitsofchris, 4,000+ notes, 2 years) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6086278)
- [COMMENTER] File back whole conversations, not single answers: "File-back works best at the *conversation* granularity… filing the whole thread preserves the reasoning path" (@manavgup) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6088113)
- [COMMENTER] Counter-evidence on filing back:
  - one builder "built that loop and deleted it whole. Not fabrication, dormancy" (@sturlese) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6306038)
  - a confident wrong answer filed back "then it **is** a source", so the schema should say "the wiki has no confident answer on this… and such an answer is never filed back" (@antondzi-legacy) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6285217)
- [COMMENTER] The "discuss takeaways" step matters for trust. A builder whose v1 skipped it said it "felt like the AI rewriting your notes behind your back". Takeaways plus a checkbox plan of proposed updates, approved before writing, "fixed the trust problem" (@frankchu91) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6302183)
- [COMMENTER] Review the generated diff, not the plan: "Reviewing 'what the LLM intends to do' catches far fewer problems than reviewing what it actually wrote" (@huachen-wang) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6316883)
- [COMMENTER] Rewrite vs append, from practice:
  - "Rewrite the summary, don't append" and "Extend, don't create" (podcast wiki, 69 concept pages / 60 episodes) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6414983)
  - "Append-only is a trap. Compaction is the answer": an Actuel/Archive section pattern plus per-file line budgets (@benjimixvidz) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102240)
  - the opposite design (immutable Zettelkasten atoms that the LLM never edits, plus separate synthesis notes citing them) — [@SEO-Warlord](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6113434)
- [COMMENTER] Human corrections get overwritten by later LLM rewrites. Record each human fix as a "pin" (intent plus claim plus section anchor) and re-check pins after every regeneration (@huachen-wang) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6316883)
- [COMMENTER] The new-page-vs-edit question was asked on day one (@alinawab) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6078975). Answers:
  - "*new page* when it is a distinct entity/concept you would link to from elsewhere; *edit in place* when it is an attribute/update of an existing one", right "~90% of the time once the schema enumerates the page types" — [@distorx](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6223068)
  - update if the source "answers the same canonical question and has >60% entity overlap", else create — [@KevinYoung-Kw](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6104347)
- [COMMENTER] Ingestion order biases the wiki toward early sources. Run lint in batches with a randomised source order and a persistent scratchpad (@brtrx) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6172613). Alternatively, make ingest idempotent by keying claims on their citation (@watsonrm) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6184513)
- [COMMENTER] A "reflect" step: ingest → compile → reflect → query → lint, with every knowledge change carrying a decision record of what it replaced and why (@bendetro) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6082335)
- [COMMENTER] "Divergence Check": each concept-page update must produce a "Counter-Arguments & Data Gaps" section to counter confirmation bias (@localwolfpackai) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079697)
- [COMMENTER] The agent consults the wiki at session start but not mid-task. In 2 of 9 audited sessions it re-diagnosed a failure that already had a written lesson. Fix: an explicit schema trigger saying when to check the wiki (@orcosto-lab) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6381418). Relatedly, "Just putting a 'remember to update...' in claude.md wont do it" (@dtmoura) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6161727)

### Inferences
- Karpathy's model is closest to ms-kb's new direction (one consolidated topic page that may be rewritten), not to append-only. "Revising topic summaries" plus "touch 10–15 pages" is the key wording. The user's decision (one main page rewritten, neighbours get only targeted link edits) is a narrower, lower-risk version of the 10–15-page fan-out.
- The two-outputs rule maps directly onto `add-knowledge`: the conversation's answer is output one, the topic-page update is output two.
- The thread's main warnings about in-place rewrites are human corrections being reverted, nuance compressed away, and fabrications filed back as sources. They argue for: a diff the user sees before commit (Karpathy's own "discuss takeaways"), source links per claim, and a protected human-authored section.

### Gaps
- The gist gives no contradiction format, resolution rule, or "who wins" policy. Commenters' solutions are all ad hoc.
- No source states how Karpathy decides between a new page and an edit, or how many pages his own ingests actually touch beyond "might touch 10–15".

---

## 3. index.md and log.md: format, prefixes, purpose, navigation without embeddings, and stated scale

### Takeaway
[KARPATHY] `index.md` is a content-oriented catalog: one line per page with a link, a one-line summary and optional metadata (date, source count), grouped by category. The LLM updates it on every ingest and reads it *first* at query time, then drills into pages. This "works surprisingly well at moderate scale (~100 sources, ~hundreds of pages)" without embedding RAG.
`log.md` is chronological and append-only (ingests, queries, lint passes). Each entry starts with a greppable prefix like `## [2026-04-02] ingest | Article Title`.
Past that scale he recommends proper search (qmd) or a self-built search script.

### Cited Findings
- [KARPATHY] index.md: "content-oriented. It's a catalog of everything in the wiki — each page listed with a link, a one-line summary, and optionally metadata like date or source count. Organized by category (entities, concepts, sources, etc.). The LLM updates it on every ingest. When answering a query, the LLM reads the index first to find relevant pages, then drills into them. This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] log.md: "chronological. It's an append-only record of what happened and when — ingests, queries, lint passes. A useful tip: if each entry starts with a consistent prefix (e.g. `## [2026-04-02] ingest | Article Title`), the log becomes parseable with simple unix tools — `grep "^## \[" log.md | tail -5` gives you the last 5 entries. The log gives you a timeline of the wiki's evolution and helps the LLM understand what's been done recently." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Both files "help the LLM (and you) navigate the wiki as it grows. They serve different purposes." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY, X] Scale stated in the X post: "once your wiki is big enough (e.g. mine on some recent research is ~100 articles and ~400K words)… I thought I had to reach for fancy RAG, but the LLM has been pretty good about auto-maintaining index files and brief summaries of all the documents and it reads all the important related data fairly easily at this ~small scale." — [X post](https://x.com/karpathy/status/2039805659525644595). Note the shift: the X post says "~100 articles… ~small scale", the gist says "~100 sources, ~hundreds of pages… moderate scale".
- [KARPATHY] Beyond that: "at small scale the index file is enough, but as the wiki grows you want proper search." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [COMMENTER] Where the index breaks, by the commenters' estimates:
  - the "~100-200 pages" past which "index.md itself overflows the context window" (@skynet) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6110770)
  - works "at 20 pages. At 100+ it blows the context window" (@singularityjason, promoting OMEGA) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085372)
  - "a few hundred pages" (@distorx) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6223068)
  - "low thousands of pages" (@sturlese, hippocampus) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6264580)
  - 1,602 sources → 161 pages still fine, but around ~150 pages the graph view replaced index.md for human navigation (@kdsz001) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6111804)
- [COMMENTER] The index misses facts buried deep in page bodies. Fix: take the **union** of index-selected pages and BM25 full-text top-k; "additive-only means recall can never get *worse*" (@huachen-wang, ~200 pages) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6316883)
- [COMMENTER] Token-budgeted progressive disclosure: L0 ~200 tokens of project context each session, L1 1–2K the index, L2 2–5K search results, L3 5–20K full articles. "The discipline of not reading full articles until you've checked the index first is what makes this scale" (@bluewater8008) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079549)
- [COMMENTER] Alternatives to a single index:
  - a federated per-project index.md (@Lukaschub) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6084572)
  - "No index.md - the AI scans summaries and tags at query time… nothing gets stale" (@asakin) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6086743)
  - "just instruct llm to do ls" (@panakh) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6088963)
  - routing tables built in the *user's* vocabulary, because an AI-organized index categorizes "the way the AI sees it" (@superimpactful) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6131689)
  - TL;DR at the top of each page so the agent does index scan → TL;DR → full page (@YokoPunk) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079272)
  - "Shouldn't index.md and log.md rather be database tables" (@rjbudzynski) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6082396)
- [COMMENTER] Pushing the index into context automatically: `@~/Vault/Wiki/index.md` in `~/.claude/CLAUDE.md` makes Claude Code expand it at session start, so "the original pattern requires you to remember to query — this makes it automatic" (@vitalii-ivanov-rakuten) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6090303). Keep the auto-loaded index "surgically small" (one line, ~150 chars per entry) so it survives Claude Code compaction (@KarabutRom) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6095072)
- [COMMENTER] Is log.md needed?
  - "having a log locally for each agent seems to only confuse less intelligent models… [git] can do it" (@aakarim) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085832)
  - "Git history doubles as the `log.md` audit trail for free" (@distorx) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6223068)
  - log backlinks turned the Obsidian graph into "all roads led to the log… LLMs don't actively use them; it's for audit purposes only", so all links from the log were stripped (@403-html) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102269)
  - log.md "append + compact (sessions > 30 days become one-line-per-week summaries)" (@benjimixvidz) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102240)

### Inferences
- In Karpathy's design the index is the retrieval mechanism, not just a table of contents. ms-kb already has `kb search`, so a hand-maintained index would duplicate it unless it carries one-line summaries the agent reads first.
- The user doesn't need "what I studied on which day". That removes most of log.md's stated purpose. The remaining purpose ("helps the LLM understand what's been done recently") is already covered by ms-kb's git commit per write, which is what several commenters substitute.
- Practitioners agree the index fails around 100–300 pages. Below that, an index plus full-text search (union) is the cheap, well-supported option.

### Gaps
- Karpathy gives no exact index.md layout beyond "link + one-line summary + optional metadata, by category", and no log entry body format beyond the header prefix.
- No benchmark from Karpathy on index-based navigation accuracy.

---

## 4. Page types and how they link

### Takeaway
[KARPATHY] Named page types: **summaries** (one per source), **entity pages**, **concept pages**, **comparisons**, **an overview**, **a synthesis**. Query outputs can be filed back as new pages. Index categories: "entities, concepts, sources, etc." The domain example for a book uses characters, themes and plot threads. Linking is called "cross-references" and "backlinks", browsed through Obsidian's graph view. The gist never prescribes a link syntax, typed relations or frontmatter, apart from optional YAML for Dataview.

### Cited Findings
- [KARPATHY] "Summaries, entity pages, concept pages, comparisons, an overview, a synthesis." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Index "Organized by category (entities, concepts, sources, etc.)" — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Book example: "filing each chapter as you go, building out pages for characters, themes, plot threads, and how they connect… Think of fan wikis like Tolkien Gateway" — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY, X] "The wiki includes summaries of all the data in raw/, backlinks, and then it categorizes data into concepts, writes articles for them, and links them all." — [X post](https://x.com/karpathy/status/2039805659525644595)
- [KARPATHY] Browsing: "following links, checking the graph view, reading the updated pages"; the graph view shows "which pages are hubs, which are orphans". — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Frontmatter is optional: "If your LLM adds YAML frontmatter to wiki pages (tags, dates, source counts), Dataview can generate dynamic tables and lists." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [COMMENTER] Untyped wikilinks were the most repeated structural complaint:
  - "Typed edges rather than a flat list. Supports, contradicts, evolved_into, depends_on" (@H179922) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6082610)
  - "A typed entity system with explicit relation types (is-a, part-of, contradicts) produces much cleaner wikis than free-form linking"; concept dedup ("attention mechanism" vs "self-attention") is "where the LLM struggles most" (@xoai) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6082547)
  - three named problems: Identity (duplicate concept pages under different names), Level (life-scale themes flat next to tactical findings), Relationship (link type lost) (@nowissan) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6149080)
  - a `relates_to: [{page, rel: contradicts|extends}]` frontmatter block queryable by Dataview (@pursultani) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6183984)
- [COMMENTER] Wikilinks are harder than they look. "Asking the LLM to guess related titles at compile time hallucinates 404s; they have to be resolved against the existing article set at write time" (@manavgup) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6088113). Claude created "ghost backlinks" that produce empty files when clicked. Fix: `[[path_to_file|Name]]` (@403-html) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102269)
- [COMMENTER] The opposite view: keep unresolved links as "speculative linking… Red links are features, not bugs", because they resolve when the page is later created (@xoai) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085123). A broken link is "unwritten knowledge to file, not an error" (@sidleo) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6371101)
- [COMMENTER] Mechanical rather than LLM cross-links: "Title mentions in body text, slug pattern matching, journal co-occurrence. This avoids hallucinated connections" (@peas) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079483)
- [COMMENTER] Added page types:
  - decision pages with rationale and reversal conditions, plus an assumption register (@AliMahmoud15486, PM wiki) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6230677)
  - a synthesis folder for the human's own hypotheses, and MOC/hub notes for 3+ related topics (@403-html) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102269)
  - a "hot cache" `wiki/hot.md` of ~500 words of session context (claude-obsidian) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6091186)
  - "document passports", a one-line immutable header saying whether a file is append-only, may contradict newer docs, or is kept current (@gserdyuk) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6250368)
- [COMMENTER] "Keep pages to the absolute min" (@kibotu) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6222233). Measured evidence (code repo): 28 per-entity pages "saved nothing" vs grep, and pages were larger than the files they described. One dense page "compresses facts scattered across many sources" and cut 4-lookup cost from 27.3k to 13.8k tokens. "Mirrors of small greppable files are negative value" (@blurman-ai) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6232070)

### Inferences
- The user's "one consolidated page per topic" corresponds to Karpathy's concept page plus synthesis/overview, merged. Source summaries and entity pages are optional in his scheme ("pick what's useful").
- Making "links between related topics explicit" is where the thread most consistently says plain wikilinks are not enough. A minimal typed relation (a "related / prerequisite / contrasts" note next to each link, or a frontmatter list) addresses the "Relationship" problem without a graph database.
- blurman-ai's measurement supports the user's consolidation decision: value comes from pages that compress many sources, not from per-entity mirrors.

### Gaps
- Karpathy gives no page templates, no link syntax, and no rule for when a concept deserves its own page beyond lint's "important concepts mentioned but lacking their own page".

---

## 5. Tools and tips: Obsidian, graph view, Web Clipper, local images, qmd, Marp, Dataview, git

### Takeaway
[KARPATHY] Every tool is optional. Obsidian is the human-facing "IDE" for browsing what the LLM writes. Web Clipper gets web articles into `raw/` as markdown. A hotkey downloads images locally so the LLM can view them. The graph view shows the shape of the wiki (hubs, orphans). Marp turns wiki content into slides. Dataview queries frontmatter. git gives history, branching and collaboration. qmd (local hybrid BM25/vector search plus LLM re-ranking, with CLI and MCP) is the suggested search tool once the index isn't enough. Alternatively, vibe-code a naive search script.

### Cited Findings
- [KARPATHY] Obsidian role: "I have the LLM agent open on one side and Obsidian open on the other. The LLM makes edits based on our conversation, and I browse the results in real time… Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY, X] "I use Obsidian as the IDE 'frontend' where I can view the raw data, the compiled wiki, and the derived visualizations… the LLM writes and maintains all of the data of the wiki, I rarely touch it directly." — [X post](https://x.com/karpathy/status/2039805659525644595)
- [KARPATHY] Web Clipper: "a browser extension that converts web articles to markdown. Very useful for quickly getting sources into your raw collection." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Local images: "In Obsidian Settings → Files and links, set 'Attachment folder path' to a fixed directory (e.g. `raw/assets/`). Then in Settings → Hotkeys, search for 'Download' to find 'Download attachments for current file' and bind it to a hotkey (e.g. Ctrl+Shift+D)… lets the LLM view and reference images directly instead of relying on URLs that may break. Note that LLMs can't natively read markdown with inline images in one pass — the workaround is to have the LLM read the text first, then view some or all of the referenced images separately." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Graph view "is the best way to see the shape of your wiki — what's connected to what, which pages are hubs, which are orphans." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] Marp: "a markdown-based slide deck format. Obsidian has a plugin for it. Useful for generating presentations directly from wiki content." Dataview: "runs queries over page frontmatter." git: "The wiki is just a git repo of markdown files. You get version history, branching, and collaboration for free." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [KARPATHY] qmd: "a local search engine for markdown files with hybrid BM25/vector search and LLM re-ranking, all on-device. It has both a CLI (so the LLM can shell out to it) and an MCP server… You could also build something simpler yourself — the LLM can help you vibe-code a naive search script as the need arises." — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (links https://github.com/tobi/qmd)
- [KARPATHY, X] His own tooling: "I vibe coded a small and naive search engine over the wiki, which I both use directly (in a web ui), but more often I want to hand it off to an LLM via CLI as a tool for larger queries." — [X post](https://x.com/karpathy/status/2039805659525644595)
- [COMMENTER] The first-party Obsidian **Bases** plugin was offered as a better choice than Dataview (@ppeirce) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079004)
- [COMMENTER] Images: pre-generate text descriptions so the LLM can read everything in one pass (@jamesalmeida) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079011)
- [COMMENTER] Obsidian is proprietary, so a "personal" KB should not depend on it (@gnusupport) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6093292). Several implementations ship their own viewer. Hide tooling folders via `.obsidian/app.json` `userIgnoreFilters` to clean the graph from "420 nodes of noise" to 18 pages (@benjimixvidz) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102240)
- [COMMENTER] Use deterministic scripts for bulk edits. An added CLAUDE.md rule: "Prefer scripts for bulk operations… Agent-driven file-by-file edits are slow and expensive" (@vysogot) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6092114). The token burn comes from re-reading AGENTS.md, index and manifests every session, so deterministic Python handles intake, validation and routing (@Motya-cobol) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6203805)
- [COMMENTER] Editing mechanics: exact-match search/replace tools make models "thrash"; "Line-number-based tools seem to work best" (@securityguy) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6372312)
- [X-REPLY @kepano, Obsidian CEO, 2026-04-02] "Keep your personal vault clean and create a messy vault for your agents… Keeping a separation between your personally-created artifacts and agent-created artifacts prevents contaminating your primary vault with ideas you can't source… Search, bases, quick switcher, backlinks, graph, etc, will no longer be scoped to your knowledge. Only once your agent-facing workflow produces useful artifacts would I bring those into the primary vault." — [X](https://x.com/kepano/status/2039831289533227446) (via [fxtwitter](https://api.fxtwitter.com/kepano/status/2039831289533227446))
- [X-REPLY @lexfridman, 2026-04-02] Similar setup (Obsidian + Cursor + vibe-coded web front-ends). He generates "dynamic html (with js)" for sort/filter, and "a temporary focused mini-knowledge-base for a particular topic that I then load into an LLM for voice-mode interaction on a long 7-10 mile run." — [X](https://x.com/lexfridman/status/2039841897066414291)

### Inferences
- For ms-kb, Obsidian is already the viewer and git is already built in through `kb` commits. Karpathy's git rationale ("version history… for free") matches ms-kb's design. Web Clipper, Marp and image handling are optional extras that matter little for a chat-outcome-driven KB.
- kepano's "contamination" point bears directly on a personal vault that receives LLM-written topic pages. The thread's answers are: mark agent-written vs human-written content, or keep separate areas.

### Gaps
- Karpathy did not say whether he uses qmd himself (the X post says he vibe-coded his own search) or which Obsidian plugins besides Marp he uses.

---

## 6. What the community proposed in the gist comments: extensions, implementations, criticisms, failure modes, scaling, alternatives, Karpathy replies

### Takeaway
1,137 comments from 757 accounts (2026-04-04 → 2026-10-08). About half include a link to some GitHub repo, so the thread is dominated by self-promoted implementations. Late in April it degenerated into a flame war (a now-deleted account, "GNU Support"/@gnusupport) and spam.
**Karpathy never commented in the gist.** The substantive community contributions cluster into:
(a) truth maintenance / provenance (per-claim citations, source hashes, verification status, review-gated diffs)
(b) contradiction policy
(c) growth control (compaction, budgets, dedup, create-vs-edit rules)
(d) index scaling and hybrid search
(e) typed links / graphs
(f) human-learning critiques (the Generation Effect: an LLM writing your notes removes the learning)
(g) separating human from AI content
(h) multi-agent / team concurrency and security
(i) the absence of benchmarks, plus a few small measurements

### Cited Findings
**Thread metadata and Karpathy's participation**
- No comment from the account `karpathy` among all 1,137 (API dump). The gist has **1 revision** (never edited) and shows "5,000+" stars and forks on the page — [Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- On X, Karpathy invited contributions: "people can adjust the idea or contribute their own in the Discussion which is cool." — [X follow-up, 2026-04-04](https://x.com/karpathy/status/2040470801506541998)
- Early unanswered questions from Karpathy's audience: "What's the failure mode? Where does it start fighting you?" and "How do you decide when to create a new page vs edit an existing one?" (@alinawab) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6078974); "how can I share the knowledge base with my team?" (@geetansharora) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6078979); "rules on periodic cleaning and pruning?" (@MironV) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079264); how to remove/reverse a bad ingestion (@vincent-pli) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6109494). All answered only by other commenters.
- Meta-criticism of the thread: ">90% of the comments are transparently written by LLMs" and "50 out of the 435 current comments are plugging their own projects" (@joshwand, 2026-04-12/13) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6094660), [follow-up](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6094666)

**Truth maintenance and provenance (most-discussed theme)**
- "the hardest part is understated a bit: truth maintenance… the risky sentence is effectively 'the LLM owns this layer entirely'… the robust version of this pattern is not 'autonomous wiki,' but 'source-grounded, citation-first, review-gated wiki.'" Proposed constraints: separate facts / inferences / open questions; passage-level source links; idempotent ingest; "the LLM [should] propose diffs instead of silently overwriting pages"; lint for unsupported claims and "source loss" (@laphilosophia, 2026-04-04) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079377)
- "No content invention… The LLM must be an editor, not a writer — every sentence must trace to something the user actually said. Gaps get `[TODO: ...]` markers" (@peas) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079483)
- "The human owns verification… The LLM is the writer. You're the editor-in-chief." (@bluewater8008) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079549)
- Structural provenance: each proposition records its source files and content hashes; a mismatch at query time marks it stale (@Jwcjwc12) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6082231). The same approach with frontmatter `source_hash` and a `provenance_check.py` (@Ss1024sS) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085348)
- Four claim types as callouts: Source (verbatim quote), Analysis (inference with reasoning shown), Unverified, Gap ("never fill with a plausible guess"). "The Analysis / Unverified split is the one that earned its keep" (@n7-ved) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6095277)
- Verification status on every page. AI content enters through a quarantined inbox as `unverified` and "cannot be cited as grounds for any other page until checked… An unverified page citing another unverified page is exactly the circular evidence auditors are trained to reject" (@bluejaeha, accountant) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6253883)
- Lossy-summary drift goes undetected because "health checks… only checked whether summaries agreed with each other, not whether they still matched the original documents… the knowledge base had been confidently wrong for months" (@ranjankumar-gh) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6109652)
- "we're trading _ephemeral hallucinations_ for **persistent errors**" (@Shagun0402) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6090491). "A great cache, but… there's always the risk of cache poisoning" (@sovahc) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085044)
- The wiki gradually cites itself: "Derived pages end up in the same index as sources with equal standing". Fix: "a quote is a pointer into an immutable source, not a copy"; breaks "somewhere around a thousand files" (@AbleVarghese) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6305974)
- Measured confidence decoupling: off-domain queries ("bathyscaphe Trieste") still returned 12 confident hits; nothing said "I found nothing" (@antondzi-legacy, n=6, self-described limits) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6285217)
- Lint cannot see drift against reality: a note said a dashboard required admin while the code allowed everyone. "Lint checks notes against notes." Fix: claims carry file+lines and are flagged when code changes (@pollockchris083-arch) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6312158)
- "a note documents the shape of a contract, never its current value", i.e. don't copy moving values (SHAs, counts, dates) into prose (@WadeGIMPBC) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6325264). This was adopted as a "state rule" by MindBase — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6368378)
- A commenter cited "LLMs Corrupt Your Documents When You Delegate" (arXiv 2604.15597) as relevant evidence (@mauceri, not verified by me) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6116491)

**Growth, duplication, compaction**
- "Every append-only wiki eventually becomes the same mess it was supposed to replace"; per-file line budgets (whole project wiki ~300 lines); Actuel/Archive; "Don't automate the update. You know when a session matters." (@benjimixvidz) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102240)
- Concurrent ingest caused 38% semantic near-duplicates (`eori` vs `eori-number`). Fix: reserve target slugs as "planned" placeholders through an atomic conditional write (@huachen-wang) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6316883)
- An entity registry with canonical names and aliases catches duplicates, because "50 pages about the same thing with slightly different titles" was "one of the first failure modes" (@SonicBotMan) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6095544)
- "dream" / sleep consolidation passes: fix references, merge, weaken pages untouched for 60 days, archive at 90 (@AfzalivE) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102181). Consolidate "after a large feature is completed… like how your memories are consolidated as you sleep" (@joshwand) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6100879)
- Formation problem: "'Every conclusion goes back to the wiki' is a rule, not a mechanism. What deserves to become a memory vs. what's noise?" (@singularityjason) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085372). "a quality gate before storage mattered more than anything else" (@7xuanlu) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6120148)
- Lifecycle states, confidence scores, supersession and forgetting curves (rohitg00 "LLM Wiki v2", widely referenced as "v2") — [LLM Wiki v2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2), linked in [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6099069). Also emergence → validation → crystallization → dormancy → invalidation (@V-interactions) — [gist](https://gist.github.com/V-interactions/a0d2a62c1b16d1fecf1bd81e8f611fba)
- Corpus/surface split: stop promising currency for most docs (dated, append-only, periodically rewritten as vN), and keep only a tiny "surface" current. "Staleness is solved by not promising currency — except where you can actually afford the promise" (@gserdyuk) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6250368)

**Scaling and retrieval**
- At thousands of messy personal notes "naive semantic search returns 10 versions of your loudest thought". Overfetch 3x, dedupe, re-rank for diversity (MMR) (@bitsofchris) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6086278)
- "scoping should be deterministic, reasoning should be probabilistic", i.e. don't make the LLM do set operations in context (@gulliveruk) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6109752)
- Large sources need retrieval *during ingest* ("For a 400-page book… This is, ironically, exactly what RAG is for") (@skynet) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6110770)
- "LLM Wiki excels at 50-200 entries… but faces 'false coherence' challenges at scale" (@dhruvil-1990) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6092104). At under 50 docs "the wiki alone is enough", with a vector layer only at 500+ (@tashisleepy) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6081913)
- Context-vs-RAG threshold: below ~50–100k tokens (~150–200 pages) pure context wins; millions of tokens need RAG (@Shilren) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6177837)

**Human learning and cognition critiques (relevant to a learning KB)**
- "Summaries don't replace thinking… The cognitive work happens in the writing itself. The note is a byproduct… The grunt work you want to automate is, in a lot of cases, exactly where the learning happens." (@pssah4, 3 years of Zettelkasten) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6084927)
- No "Generation Effect, where YOU engage with what you're capturing… See also: The Outsourcing Trap" (@robertandrews) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085004)
- "If the LLM authors, you've built a personalized research index, not a second brain." The inverse pattern is an LLM that only *maintains* notes you write (@gpkc) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6092774)
- "Raw resources may be better than LLM Wiki for beginners… [the wiki is suited for] review and summary, not getting started"; add a `type` field marking human-written vs AI-generated (@iBlinkQ) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6101061)
- The wiki stores only knowledge that "passed through your own thinking", and the LLM challenges your understanding before writing (@JieqLuo) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6088562). A "Socrates–Plato–Bayes" loop has the user propose, the AI challenge, and only surviving ideas get promoted (@Archimondstat) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6183986)
- Spaced repetition over decision/insight pages, because "Your wiki stays current; your memory of why you decided things doesn't" (@suwonleee) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6265997). Flashcards with FSRS, plus an `insights/` directory "the agent never touches", prompted by kepano's point (@arturseo-geo) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6084954)
- Drift of the human mental model: "eventually the data and your mental model drift and diverge… you no longer have an understanding of the beast you've created"; "The metamodel is the message" (@joshwand) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6100879)
- Keep "the framing and the decisions… authored by me — otherwise the continuity quietly stops being mine" (@hegu-1) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6176154)
- Related idea flagged early: Karpathy's 2025 "append-and-review note" blog post as a possible complement (@expectfun) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6078984)

**Multi-agent, teams, security**
- Multi-agent writes: concurrent ingests fork the wiki (see above); partition writers by file and keep writes append-only so merges commute; "A clean merge isn't a correct merge" (@watsonrm) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6184491). Agents differ, so per-agent entry files (CLAUDE.md/CODEX.md/GEMINI.md) "drift… into different views of the user" (@AEVYRA) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6125361)
- A symlink of CLAUDE.md → AGENTS.md lets the same schema work across Claude Code/Codex/OpenCode (@zhurudong) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6132340)
- An autonomously ingesting wiki is "an indirect-prompt-injection surface… A crafted source can plant instructions that persist into the wiki." Lint checks correctness, "not adversariality" (@NicoBleh) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6176649)
- Team audience separation: compile a second wiki from only the external-safe sources rather than filtering by labels (@huachen-wang) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6316883)

**Evidence and benchmarks (scarce)**
- "the hype is way ahead of the evidence. There is no benchmark, no task definition, no scale curve, and no comparison against serious baselines… an LLM Wiki is lossy compression… the reasonable claim is narrow: … small-to-medium, slow-moving, human-curated research folders" (@a-a-k) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6130180). Late question "did anyone run… benchmarks to verify… 'Why this works'?" got no answer (@oefi) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6384222)
- Query-type split from 469 logged runs (31 hand-labeled): the wiki/graph side was better for topical questions (15/21), worse for entity lookups (1/10). The same comment disputes the "21x more expensive than RAG" figure attributed to arXiv:2605.18490 (query-side reproduces, ingest-side over-counted by the authors' own admission) (@tonydzi) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6321233)
- Code-repo A/B: per-entity wiki ≈ grep; one dense page halves tokens (@blurman-ai) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6232070). Wiki vs RAG on a 50k-LOC codebase, where the "Combined" approach "never lost a single round" (@Eyaldavid7) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6091440)
- Claimed but not verified by me: "ETH Zurich found that LLM-generated context files hurt agent performance in 5 of 8 tested settings" (@asakin) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6093103)
- "after spending two days building… it appears too niche compared to building a local RAG system in a single day" (@grishasen) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6087524)

**Alternatives and "it's not new" critiques**
- Already done by:
  - AGENTS.md hierarchy + skills; "But I do like the lint passing concept" (@skpalan) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079055)
  - Zettelkasten — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6083662), [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6084720)
  - OpenClaw MEMORY.md (@MoserMichael) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085302)
  - Engelbart's 1992 OHS / CODIAK (@gnusupport) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6093292)
  - NotebookLM sources (@A13x3i) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6221568)
- Start from a database: "Instead of files that slowly become a database, start from structured data that renders as markdown. The index isn't a file the agent maintains by hand. It's a query" (@mpazik, Binder) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079689); "a local sqlite database was the best abstraction for agents" after 6–12 months on files (@bradwmorris) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6082446)
- Immutable atoms instead of mutable wiki pages: "The librarian writes index cards and essays, not revised encyclopedia entries… The Memex analogy… is actually closer to Zettelkasten than to wiki" (@SEO-Warlord) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6113434)
- A sustained hostile critique from a deleted account ("GNU Support"):
  - "markdown is not a database. No foreign keys = broken links… Works at 100 files. Dies at 10,000" — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6100846)
  - "A book index points to pages… It doesn't rewrite the book… LLM-Wiki does all three"
  - "it isn't a Wiki" because it is not collaborative
  - a DokuWiki newsletter critique (cited, 2026-04-15) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6105453)
  The thread largely treated this as trolling.
- "LLMs aren't 'consistent'… an LLM can't be trusted to create AND maintain its own wiki with (almost) no human supervision" (@LudoE11) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6103209)
- "Good advice for a new project… Bad advice if you're working in a mature codebase with a well-maintained wiki, because your LLM wiki is just an AI slop layer to maintain" (@Yuncun) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6085281)

**Conversation-as-source (closest to ms-kb's add-knowledge)**
- An end-of-session skill "to summarize and touch and update what is known… Now I don't need bootstraps anymore, the wiki is the bootstrap" (@vanillaflava) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6098334)
- Chatbot conversations distilled into atomic notes enter "through the same quarantined inbox as any other unverified material" (@bluejaeha) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6253883)
- "Capturing everything is easy; deciding what deserves to become knowledge is the harder problem"; new findings get fused into existing pages via a "broadcast" step (@XBlueSky) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6237806), [update](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6284110)
- "Memory is chronological — knowledge is topical. Separating the two… was the key unlock" (@zhayujie, CowAgent) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6093294)
- A Stop hook fired on every response, not at session end, so updates went back to a manual trigger (@benjimixvidz) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6102240)

**Notable implementations linked (selection, for later lookup)**
- Claude Code skill/plugin form:
  - Astro-Han/karpathy-llm-wiki — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079715)
  - kfchou/wiki-skills — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079456)
  - AgriciDaniel/claude-obsidian (hot cache, contradiction callouts, 8-category lint) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6091186)
  - Ar9av/obsidian-wiki — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6083543)
  - theafh/ai-modules (per-repo wiki + deterministic linter; "many implementations are at the border of over engineering") — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6256980)
- CLIs:
  - atomicmemory/llm-wiki-compiler (`compile --review`, claim-level provenance `^[paper.md:42-58]`, 1K+ stars by May) — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6135386)
  - xoai/sage-wiki — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6079555)
  - swarmclawai/swarmvault (repeated self-promotion called "spam" by others — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6131973))
  - kytmanov/obsidian-llm-wiki-local → Synto (local Ollama)
  - gowtham0992/link (review-gated memory, benchmarks on LoCoMo)
- Curated list: gavischneider/awesome-llm-wiki — [comment](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#gistcomment-6266938)

### Inferences
- The thread's center of gravity is not "how to build it" (hundreds of near-identical builds) but "how to keep it trustworthy". The recurring answers are citations per claim, a human-visible diff before write, a human/AI content distinction, dedup before create, and deterministic lint. ms-kb already has several of these (git per write, `kb validate`, duplicate refusal in `kb new`).
- The strongest critiques for a *learning* KB are cognitive (pssah4, robertandrews, gpkc, iBlinkQ), not technical. If the purpose is learning and review, the LLM writing everything may undercut retention. The proposed mitigations are human-authored sections, Socratic challenge before writing, and spaced repetition.
- Karpathy's silence in the discussion means none of the community's policies (contradiction handling, compaction, verification states) carries his endorsement.

### Gaps
- There are no Karpathy replies in the gist to weigh against commenters.
- Most performance and scale claims are anecdotal or vendor-authored. The only measurements found (blurman-ai, tonydzi, antondzi-legacy, huachen-wang's 38% duplicates) are small and self-reported.
- External papers cited by commenters (arXiv 2604.15597, arXiv 2605.18490, the "ETH Zurich" study) were not checked.

---

## 7. Karpathy's X posts: use case, outputs, follow-ups

### Takeaway
[KARPATHY] The original X post ("LLM Knowledge Bases", 2026-04-02 20:42 UTC) describes **research**: "personal knowledge bases for various topics of research interest". He says a large fraction of his token throughput moved from manipulating code to manipulating knowledge. Sections: Data ingest (raw/ → LLM-compiled .md wiki), IDE (Obsidian), Q&A (~100 articles / ~400K words, no fancy RAG), Output (markdown, Marp slides, matplotlib images, filed back), Linting (health checks), Extra tools (vibe-coded search engine with web UI + CLI), Further explorations (synthetic data + fine-tuning so the LLM "knows" the data in its weights).
The follow-up (2026-04-04 16:45 UTC) introduced the gist as an "idea file". He replied once more on the theme on 2026-04-10, calling it "the tractable form of brain upload".

### Cited Findings
- [KARPATHY, X] Use case and motivation: "Something I'm finding very useful recently: using LLMs to build personal knowledge bases for various topics of research interest. In this way, a large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge (stored as markdown and images). The latest LLMs are quite good at it." — [X post, 2026-04-02](https://x.com/karpathy/status/2039805659525644595)
- [KARPATHY, X] Ingest: "I index source documents (articles, papers, repos, datasets, images, etc.) into a raw/ directory, then I use an LLM to incrementally 'compile' a wiki… To convert web articles into .md files I like to use the Obsidian Web Clipper extension, and then I also use a hotkey to download all the related images to local so that my LLM can easily reference them." — [X post](https://x.com/karpathy/status/2039805659525644595)
- [KARPATHY, X] Outputs: "Instead of getting answers in text/terminal, I like to have it render markdown files for me, or slide shows (Marp format), or matplotlib images, all of which I then view again in Obsidian. You can imagine many other visual output formats depending on the query." — [X post](https://x.com/karpathy/status/2039805659525644595)
- [KARPATHY, X] Fine-tuning direction, absent from the gist: "As the repo grows, the natural desire is to also think about synthetic data generation + finetuning to have your LLM 'know' the data in its weights instead of just context windows." — [X post](https://x.com/karpathy/status/2039805659525644595)
- [KARPATHY, X] TL;DR and product remark: "raw data from a given number of sources is collected, then compiled by an LLM into a .md wiki, then operated on by various CLIs by the LLM to do Q&A and to incrementally enhance the wiki, and all of it viewable in Obsidian. You rarely ever write or edit the wiki manually, it's the domain of the LLM. I think there is room here for an incredible new product instead of a hacky collection of scripts." — [X post](https://x.com/karpathy/status/2039805659525644595)
- Engagement at fetch time (2026-10-12): 61,002 likes, 7,385 reposts, 2,941 replies, ~21.96M views, 108,513 bookmarks — [fxtwitter mirror](https://api.fxtwitter.com/karpathy/status/2039805659525644595). Secondary write-ups give conflicting dates (April 2 vs 3) and smaller view counts captured earlier ([agentpedia](https://agentpedia.codes/blog/karpathy-llm-knowledge-bases), [VentureBeat, 2026-04-03](https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an)). The primary timestamp is Thu 2026-04-02 20:42:21 UTC.
- [KARPATHY, X] Follow-up introducing the gist: "Wow, this tweet went very viral! I wanted share a possibly slightly improved version of the tweet in an 'idea file'. The idea of the idea file is that in this era of LLM agents, there is less of a point/need of sharing the specific code/app, you just share the idea, then the other person's agent customizes & builds it for your specific needs… You can give this to your agent and it can build you your own LLM wiki and guide you on how to use it etc. It's intentionally kept a little bit abstract/vague because there are so many directions to take this in." — [X follow-up, 2026-04-04](https://x.com/karpathy/status/2040470801506541998) (26,817 likes, ~7.33M views at fetch)
- [KARPATHY, X] Reply on 2026-04-10 to @jenzhuscott. Her tweet: building a 2nd brain in Obsidian "using @karpathy's wiki idea", which kids "could inherit [as] an interactive map to your mind". Karpathy: "Yes it's the tractable form of brain upload… we're about to get a lossy and approximate version of that *a lot* sooner via LLM simulators… a 'brain upload' startup… use all that data with an LLM finetuning process to 'upload' you and give you an API endpoint of your simulation… Trippy and admittedly kind of dystopian but in principle quite possible around now." — [X reply](https://x.com/karpathy/status/2042626702459674801); [jenzhuscott](https://x.com/jenzhuscott/status/2042622041371873282)
- [X-REPLY @FarzaTV, 2026-04-04, quoting Karpathy's follow-up] "Farzapedia": an LLM turned 2,500 diary / Apple Notes / iMessage entries into 400 articles with backlinks, "not built for me! I built it for my agent!" Starting at index.md, the agent drills down; "I built a similar system to this a year ago with RAG but it was ass"; adding new items "will likely update 2-3 different articles… or, just creates a new article." — [X](https://x.com/FarzaTV/status/2040563939797504467)
- [X-REPLY] kepano's "messy vault for your agents" and Lex Fridman's dynamic-HTML / voice-mode mini-KB replies (see Q5) — [kepano](https://x.com/kepano/status/2039831289533227446), [lexfridman](https://x.com/lexfridman/status/2039841897066414291)

### Inferences
- Karpathy's own use case is research: going deep on topics, reading papers and articles, and asking complex questions. The gist broadens it to personal, book-reading, team, competitive analysis, trip planning and course notes. Reviewing and learning fit his "research" and "course notes" framing, but he describes no spaced repetition or self-testing.
- Outputs are meant to be viewed and filed back. That supports ms-kb using chat outcomes (Claude Code sessions) as the "source" layer instead of a raw/ folder, an adaptation he does not discuss but which several commenters made.

### Gaps
- Secondary sources say Karpathy quote-reposted "Farzapedia" with commentary. I could not retrieve that post's ID or text, so its wording is unverified.
- Other in-thread replies by Karpathy on X were not enumerated, because x.com's reply tree isn't accessible without login. Only the posts above are confirmed.
- No Karpathy statement after April 2026 on how his setup evolved, whether he adopted qmd, or any failure modes he hit was found.
