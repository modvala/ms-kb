---
title: "Personal Knowledge System — User Stories"
document_version: "2.2"
created: "2026-10-12"
updated: "2026-10-19"
language: en
status: requirements_baseline
supersedes: "personal-knowledge-user-stories-v1.md (1.11)"
origin: "The v1 requirements, revised after roadmap stage 4 with the user's restated intent and the LLM Wiki research"
---

# Personal Knowledge System — User Stories v2.2

This document records the desired outcome and the decisions made about the personal knowledge base. Version 2 replaces [v1.11](personal-knowledge-user-stories-v1.md), which stays in the repository as history.

**Why a v2.** Stages 0–4 (package v0.5.0) built the storage, the CLI and the skills around learning sessions and append-only notes. After four days of real use the vault held six notes on one topic: half of the bytes were session notes, the same rules were written in two places, and one page contradicted itself because `kb extend` could not change old text. On 2026-10-12 the user restated the intent, and a study of Andrej Karpathy's "LLM Wiki" pattern and its community implementations (`reports/LLM Wiki Карпати для базы знаний.md`) showed which parts of it fit. The content model changes; delivery, storage, history and data protection stay as built.

## Goal

**As a user who studies topics together with AI agents, I want each topic I have researched to have one concise, current page in my Obsidian knowledge base, with explicit links to related topics, so that when I review material or study something new I can build on what I already know.**

The knowledge base is a set of topic pages, not a learning tracker: it does not record what was studied on which day.

Principles:

1. **One topic, one page, kept current.** A research session rewrites the page into its best current form instead of appending to it.
2. **One page per session.** A session changes mainly one topic page. Neighbouring pages get only targeted edits: a link line or an open-question line, never a rewrite.
3. **Nothing is written without the user.** Writing happens only on explicit command, every change is shown as a diff before it is written, and Git keeps every earlier version.
4. **The agent writes the page; the user owns "In my words".** That section holds only the user's own words, verbatim.
5. **Learning comes from recall, not rereading.** The base supports review: the user recalls first, then compares with the page.
6. **Obsidian is the canonical store.** Notes are Markdown, readable without Obsidian.

**Delivery and storage decision** (unchanged from v1). GitHub hosts the source code of a versioned, installable package: the CLI, skills and templates. The package is installed locally; skills are installed into the user scope of the AI clients. A knowledge base is a separate local Obsidian vault with its own configuration, its own Git history and an off-machine copy in a private remote dedicated to it. Personal knowledge is never part of the package repository.

| Component | Content and purpose |
|---|---|
| Project repository on GitHub | Package source code, skills, templates, documentation, versions and CI |
| Installed package | The `kb` CLI and the bundled skills |
| User skills scope | Skills available in the supported clients from any working directory |
| Knowledge base instance | A separate vault, its configuration and profile |
| Knowledge base history and copy | The vault's own Git repository and its private remote (never the package repository) |

## Scope decisions

| Area | Decision |
|---|---|
| Users | One user: the project author. Other users (US-22) are not planned; the architecture must not rule them out |
| Delivery | `uv tool install` from GitHub, then `kb setup`; updating is `kb update` |
| Language and tooling | Python, `uv` |
| AI clients | Claude Code (primary), Codex, Cursor. ChatGPT is out of scope |
| Vault access | Agents read notes directly and change them only through the `kb` CLI |
| Knowledge base | One knowledge base (US-21 not planned) |
| Content model | Topic pages (`topic`) and, from v0.7, source cards (`source`, US-02). The v1 types `concept`, `research`, `learning-session` and `project` and the v1 `source` format are no longer created; existing notes are migrated |
| Write policy | Only on explicit command; one topic page or one source card per run; a diff approved by the user before an existing page changes |
| Storage and history | Local vault outside synced folders; its own Git repository with a commit per `kb` write; `kb sync` pushes to a private remote hourly and on demand |
| Obsidian | Not required for the package and agents; used for reading and navigation |

**Story status.** *Done* — implemented in v0.5.0 and still valid. *Changed* — the acceptance criteria are revised in v2. *New* — added in v2. *Kept* — unchanged in meaning, not fully implemented yet. *Frozen* — kept as a possible future direction, not planned; skills do not use it.

## 1. Content of the knowledge base

### US-01. A single store of accumulated knowledge — Kept

**As a user, I want to keep my knowledge in Obsidian so that I have one clear knowledge base for learning, research and reusing conclusions.**

Acceptance criteria:

- Explanations, research results and durable conclusions are saved as topic pages in Obsidian.
- The main content of notes is Markdown and is readable without Obsidian.
- Notes can contain metadata, links to other notes and attachments.

### US-04. Topic pages and links between them — Changed

**As a user, I want one page per topic, linked to related topics, so that I find everything about a topic in one place and can move between topics.**

Acceptance criteria:

- The main note type is `topic`: one page per topic, kept current.
- A topic page has a one-line summary, the user's own words, the key ideas, details, open questions, related topics and sources (design §6).
- A topic too large for one page (about 200 lines) is split: a subtopic gets its own page linked from the parent.
- A second page on the same topic is not created: the CLI refuses a page with the same title or alias or a similar title, and before creating a page the agent names the closest existing pages and why the topic is new.
- A page carries aliases for other names of the topic: abbreviations and names in the user's language, so that search and links find it in either language.
- The user may add sections of their own; they are kept when the page is rewritten.
- Notes of the v1 types (`concept`, `source`, `research`, `learning-session`, `project`) remain readable and valid; skills do not create them. From v0.7 `save-source` creates source cards, the revised `source` type (US-02).
- Comparisons and dated facts live on the topic page, marked "as of" a date, not in separate research notes.

### US-02. A source card instead of a copy of the source — Changed

**As a user, when I find an interesting source but do not want to write a topic page from it yet, I want to save a short summary of it, so that when a related topic comes up I can use its content, its illustrations or its way of explaining.**

Acceptance criteria:

- The `save-source` skill is invoked explicitly ("save this source for later", "сохрани источник на потом"); one run creates one source card (design §6.9).
- A card is made only from a source the agent opened in the conversation or from text the user pasted (for paywalled pages, videos, books); otherwise the agent says so and creates no card. The content of a source is never invented.
- A card holds a one-line summary, a short summary in the agent's own words, the key ideas, the illustrations worth reusing, how the source explains its subject, the topics it may serve, and related pages. It never holds the full text, and at most a couple of short quotes with attribution.
- Illustrations are referenced and described — where they are (figure, page, anchor, timestamp), what they show and why they work — and may be redrawn in Mermaid. Images are not copied into the vault.
- A card has `url` or, for a book, local file or talk, `ref`; one of them is required.
- One card per source; a book or a course gets one card that later runs extend. A card with the same normalized URL, the same title or alias, or a similar title is refused, and the agent offers to extend the existing card instead.
- A card has 1–3 tags from the same vocabulary as topic pages (US-28); new tags are confirmed by the user.
- Before writing, the agent shows the card; it writes only after the user's yes. If a related topic page exists, the agent may propose one `## Sources` line on it pointing to the card, approved separately.
- No "to read" or "processed" status is stored. Whether a card is used is computed: a card no topic page links to is shown as "not used yet" by `kb index --sources` (US-08).
- A card has no `## In my words` section: its summary is already written in its own words; the user's formulation belongs on topic pages (US-29).
- Topic pages keep listing their sources in `## Sources` with what each supports and the date it was checked (design §6.4); a line may point to a card instead of the source.

### US-03. Synthesis of multiple sources — Frozen

Separate dated research notes are not created. A comparison belongs to the topic page it is about, with its date and sources. A dedicated `research` skill stays a possible future direction.

### US-05. External data stays in external systems — Kept as a boundary

**As a user, I want trackers and code to stay in their own systems so that I do not maintain them again in Obsidian.**

Acceptance criteria:

- The knowledge base does not hold copies of trackers, task lists, application statuses or repositories.
- A topic page may link to an external resource and say how it relates to the topic.
- Connecting external systems (Notion, GitHub) as sources is not planned (see US-14).

### US-06. Knowledge gained from practical work — Frozen

Project notes are not created. A durable conclusion from practice goes to the topic page it is about, with a link to the issue, commit or document behind it.

## 2. Reading, recall and review

### US-07. Continuing a topic — Changed

**As a user, I want the agent to find what I already know about a topic when I continue it, so that the explanation starts from my current understanding and my open questions.**

Acceptance criteria:

- On requests like "let's continue X", "what do I know about X", "remind me what was unclear", the agent consults the knowledge base.
- The agent finds the topic through the index and text search, then reads that topic page and, if needed, a few linked pages.
- The agent starts from the page's `## In my words` and `## Open questions`, and separates what comes from the page from its new explanation.
- The agent also finds source cards on the topic (US-02) and says what they offer — an illustration, a way of explaining — and uses them when the user wants.
- If no page exists, the agent says so only after both the index and the search came back empty, and does not invent a history.
- Simple questions that need no personal context do not read the knowledge base.
- If the knowledge base is not accessible, the agent says so and answers from the conversation only.

### US-08. Selective search and the topic index — Changed

**As a user, I want the agent to find the right pages without loading the whole knowledge base into the conversation.**

Acceptance criteria:

- `kb index` prints a catalogue of topic pages grouped by tags, one line each: link, summary, number of open questions. It is generated from the notes, never written by the model.
- `kb index --sources` prints the source cards separately, grouped by tags, with their summaries and the number of topic pages linking to each ("not used yet" when none).
- `kb search` finds pages by text, tags and metadata, ranking matches in the title and aliases first, then the summary and tags, then the body. Results show the note type; `--type source` limits them to source cards.
- The agent reads the pages it found, not the whole vault.
- A rebuildable full-text cache and, later, semantic or hybrid search may be added as optional backends; they never change the content of notes.

### US-09. A brief profile — Changed

**As a user, I want a short profile with my current directions and preferences so that the agent adapts its explanations to me.**

Acceptance criteria:

- The profile holds only current directions and preferences (for example, "explain with code first", "answer in Russian").
- It holds no dated history, no list of known topics (the index replaces it) and no open questions (they live on topic pages).
- It is read on demand by `kb-recall`, never loaded automatically.
- It is user data: it is changed only by the user or through an approved diff, and is never silently recreated.

### US-25. Reviewing a topic from the knowledge base — New

**As a user, I want the agent to help me review a topic by asking me first and only then showing the page, so that review strengthens my memory instead of being rereading.**

Acceptance criteria:

- On requests like "let's review X", "quiz me on X", "проверь меня по X", the agent finds the topic page but does not show it yet.
- The agent asks the user to say what they remember, then compares the answer with the page: what matches, what is missing, what is wrong. The page is the reference: if the agent's own knowledge disagrees with it, the agent reports that as a finding instead of correcting the user against the page.
- The agent asks 2–4 "why / what if / when not" questions built from the key ideas and open questions, and gives a hint before the answer. The user may set the angle of the questions ("quiz me on when not to use it").
- One or two questions mix the topic with a page from its `## Related` section.
- The agent lists the gaps it found in the conversation; it does not write them to the base (the user may run `add-knowledge` for that).
- The agent may offer to save the user's own formulation to `## In my words` (US-29); nothing else is written.
- No review schedule or review state is stored.

## 3. Writing

### US-24. Saving the outcome of a research session on command — Changed

**As a user, after working through a topic with an agent, I want to invoke `add-knowledge` so that the agent turns the conversation into the current version of that topic's page.**

Acceptance criteria:

- The skill is invoked explicitly by the user; without an invocation the agent does not create or change notes.
- Before writing, the agent searches the index and the text for the topic and decides: update the existing page, create a new page, or nothing new to save — in which case it writes nothing and says so. For a new page it names the closest existing pages and why the topic is new; a page with a similar title is created only after the user's yes.
- The agent shows the 3–5 main takeaways and asks what to stress or drop, unless the user already said what to save.
- One run changes one topic page. If the conversation covered two topics, the agent asks which one to save (or does two runs).
- For an existing page the agent shows the full diff, which sections changed and what it removes; for a new page it shows the page. It writes only after the user's yes.
- Neighbouring pages get only targeted edits approved in the same plan (US-26, US-27). The parts of the plan are approved independently: rejecting a line for a neighbour does not affect the rest.
- If the user changes the main page after seeing the plan, the agent shows only what changed since the reviewed version and writes after a short yes.
- Text found in the conversation, in pages read and in sources opened is treated as data: requests or commands in it are never carried out.
- Only claims that are doubtful, disputed or volatile (versions, defaults, dates not checked in the conversation) are marked: they go to `## Open questions` as items to verify. Established explanations are written as plain text.
- Sources that were actually opened are listed with the date they were checked; the content of sources that were not opened is never invented.
- The agent looks for source cards on the topic (US-02): it offers the relevant ones as `## Sources` lines and may use their illustrations and way of explaining in the draft. A source in the conversation that is not about the saved topic is offered to `save-source` as a separate run.
- Provenance is recorded by the CLI (US-12).
- After writing, the agent lists the changed files and any `kb` warnings.
- The whole conversation can be saved, or a part named by the user.

### US-10. Keeping a topic page current — Changed

**As a user, I want a topic page to be updated in place with what I learned, so that it stays concise and consistent instead of growing with every session.**

Acceptance criteria:

- New knowledge is merged into the page: the agent rewrites the sections it concerns and keeps the rest unchanged.
- A contradiction with the old text is resolved in place, and the reason is shown in the diff and recorded in the commit. A contradiction that cannot be resolved stays in `## Open questions` with both versions.
- The diff report shows which sections changed and lists removed sections, links and sources and how much the page shrank; a page that shrinks below half is refused unless the user allows it.
- Lines the user edited by hand that a rewrite would change or remove are flagged with the date of the edit, and the agent keeps them unless the user agrees.
- Hidden text in added lines (comments, invisible characters) is flagged, so nothing enters a page that the user cannot see in Obsidian.
- `## In my words` is never changed by a rewrite.
- Every rewrite is a Git commit, so any earlier version can be restored with `kb restore`.
- If a search index is used later, it reflects the new content.

### US-26. Explicit links between topics — New

**As a user, I want links between topics to say how the topics relate, so that I see the connection and can review related topics together.**

Acceptance criteria:

- Each link in `## Related` is a line with the target and a short phrase on the relation, for example `- [[Global Interpreter Lock]] — why threads do not speed up CPU-bound code`.
- A link is added only to a page that exists (or to its alias); the CLI refuses links to pages that do not exist.
- Adding a link to a neighbouring page changes only that line, not the rest of the page.
- When a page is written, existing topics it mentions without a link are proposed as links on that page; other pages are not searched for mentions of it.
- Links are stored once, in the page body.

### US-27. Checking linked pages when writing — New

**As a user, I want the pages my new page links to be checked against what I just learned, while all other pages stay untouched.**

Acceptance criteria:

- Only the pages the written page links to are checked (one step, not their neighbours). Other pages are not read or changed. There is no check of the whole knowledge base by the model.
- A structural check is done by the CLI as part of the preview: links that do not resolve, unlinked mentions of existing topics on the written page, neighbours that do not link back, links from other pages to headings the rewrite removed, pages that share a tag but are not linked, new tags, page length.
- A content check is done by the agent: it reads each linked page (about 5 at most, the most relevant first) and compares it with the outcome of the session: contradictions, outdated facts, things the session refines.
- Findings are shown in the same plan as the main page. For each finding the user chooses: leave it, add one line to the neighbour's `## Open questions`, or update the neighbour in a separate run.
- A neighbour is never rewritten in the same run.

### US-28. Tags with a controlled vocabulary — New

**As a user, I want pages tagged with a small set of consistent tags so that the index is grouped by area and related pages are easy to find.**

Acceptance criteria:

- Tags use Obsidian's native `tags` property and may be nested one level (`python/concurrency`).
- A page has 1–3 tags.
- `kb index --tags` lists the existing tags with the number of pages.
- A tag that does not exist yet is reported, and the agent puts it into the plan for the user's confirmation; existing tags are reused.
- Search filters by tag, including nested tags.
- Tags describe what a page is about; they are not statuses (no `to-verify`, `reviewed`).
- Source cards (US-02) use the same vocabulary and the same rules, so a topic and the cards for it share tags.

### US-29. My own words — New

**As a user, I want a section on each topic page with my own formulation of the topic, which the agent never rewrites, so that the page keeps my understanding next to the agent's text.**

Acceptance criteria:

- `## In my words` is the second section of a topic page, right after `## Summary`. It may be empty.
- The section contains only the user's text. The user writes it in Obsidian, or dictates or types it in the conversation and the agent saves it **verbatim**: no rewording, no corrections, no translation. Both skills can save it: `kb-recall` at the end of a review, `add-knowledge` when the user says "put this in my words".
- Before saving, the agent shows the exact text that will be written and saves it only after the user's yes.
- A rewrite of the page carries the section over byte for byte; a draft that changes it is refused.
- If the user's formulation contradicts the page, the agent says so in the conversation and may propose an open question; it does not edit the section.

## 4. Skills and provenance

### US-11. Working rules are defined by skills — Kept

**As a user, I want the rules for saving, recalling and reviewing to live in skills so that the agent processes material consistently.**

Acceptance criteria:

- The bundled skills are `add-knowledge` (save a research session to a topic page), `kb-recall` (continue, recall and review; read-only except saving the user's confirmed "In my words" text) and, from v0.7, `save-source` (save one source as a source card, US-02).
- Rules that can be checked by code (schema, links, diffs, shrink guard, protected section, secrets) are enforced by the CLI, not only described in the skills.
- Skills change the vault only through `kb` commands, also when other Obsidian skills are installed; the note format the skills need is described in their own references.
- Skill texts contain no examples with passwords, tokens, `sudo` or system services.

### US-12. Provenance of every change — Changed

**As a user, I want to know which skill and version created or changed a page so that I understand its origin and can find the results of older rules.**

Acceptance criteria:

- Every `kb` write is a Git commit whose trailers record the skill, the skill version, the package version, the agent when known, and the reason for the change.
- A page records in its frontmatter only how it was created (`created_by`); it does not accumulate a list of updates.
- `kb history` lists the changes of a page with their provenance; selecting changes by skill and version is done over the commit trailers (roadmap stage 7).
- Unknown values (for example the agent) are not invented.

### US-13. Revising knowledge and rules — Changed

**As a user, I want to update a page under new rules or with new knowledge while its history stays available.**

Acceptance criteria:

- Revising a page is an ordinary rewrite through `add-knowledge` with an approved diff.
- The creation date and `created_by` never change.
- Every earlier version is in the vault's Git history and can be restored.
- Automatic rebuilds of pages are not done.

## 5. Agents and visual content

### US-14. Source registry — Frozen

A registry of supporting sources (Notion, GitHub, Web) with their domains of authority is not planned. The principle stays: the current state of a tracker or a repository is taken from that system, not from a note.

### US-15. Working with different agents — Kept

**As a user, I want the same rules to work in Claude Code, Codex and Cursor so that I do not explain my knowledge base to each agent from scratch.**

Acceptance criteria:

- A global instruction tells each client that the knowledge base exists and which skills apply, including the review triggers.
- Rules are portable text (`SKILL.md`, Markdown).
- All clients write through the same CLI, with the same diff gate and guards.
- Missing access is stated explicitly; the content of an unavailable source is not imitated.

### US-16. Visual learning notes — Kept

**As a user, I want diagrams and images in topic pages so that studying and reviewing is easier.**

Acceptance criteria:

- Images and other attachments can be attached to pages.
- Processes and architectures can be drawn with Mermaid inside Markdown.
- Links between pages are used for navigation and the graph view; a Canvas may give an overview of a large area.
- The important meaning of an image is explained in text the agent can read.
- Illustrations of a source are referenced and described on its source card, not copied into the vault (US-02).

## 6. Delivery, installation and storage

### US-17. A locally installable package with skills — Done

**As a user, I want to install a versioned package with the CLI and skills from GitHub so that I can use the tools on my computer.**

Acceptance criteria:

- The repository contains the package source, the bundled skills, templates, configuration examples and documentation.
- The package is installed from GitHub with `uv`, and the installed version can be checked.
- Installing the package and creating a knowledge base are separate actions.
- The vault path is configured by the user; notes are never part of the package repository.
- Updating or reinstalling the package does not overwrite the content of the knowledge base.
- Updating the package together with the skills in all chosen clients is one command, `kb update`.
- A mismatch between the CLI version and the installed skills is reported.

### US-18. Skills in the user scope — Done

**As a user, I want the skills installed into my user scope so that I can use them from any repository in the supported clients.**

Acceptance criteria:

- `kb setup` / `kb install-skills` copy the bundled skills into `~/.claude/skills/` (Claude Code; Cursor reads it too) and `~/.agents/skills/` (Codex) ([clients-v0.md](clients-v0.md)).
- Skills find the vault through `kb where`, not through the current working folder.
- Installed skills carry the versions needed for provenance.
- The CLI manages only the skills it installed.

### US-19. A separate local knowledge base — Done

**As a user, I want the knowledge base stored locally, separate from the package, so that I own my data and update the tools independently.**

Acceptance criteria:

- The vault is a separate user directory outside the package working tree.
- Notes, attachments and the profile are user data, not package code.
- The vault can be read in Obsidian regardless of the package version.
- Removing or reinstalling the package does not delete the vault.

### US-20. History and an off-machine copy of the knowledge base — Done

**As a user, I want my knowledge base to have its own change history and an off-machine copy so that accidental deletion or loss of the computer does not destroy my knowledge.**

Acceptance criteria (implemented in v0.5.0, design §12):

- The vault root is its own Git repository; every `kb` write is a commit with provenance; edits made outside `kb` are committed separately.
- A deleted or damaged note is detected by `kb doctor` and can be restored with `kb restore` without silently overwriting a newer version.
- `kb sync` pushes the history to a private remote dedicated to the vault, hourly and on demand, never with force; pushing never blocks writing.
- Notes with key-like strings are not written; large files are not committed.
- The vault is kept outside folders synced by iCloud Drive, Google Drive, Dropbox or OneDrive.

After the MVP (target): phone and multi-device access through one two-way sync mechanism, and optionally a second cloud copy independent of the Git host.

### US-21. Multiple knowledge bases — Frozen

Several independent knowledge bases on one installation stay possible (the configuration already allows `[kbs.<name>]`), but are not planned.

### US-22. Use of the package by another user — Frozen

Installation by another user with their own data stays possible in principle (nothing personal is in the package), but is not planned or documented beyond the README.

### US-23. Package versions, CI and releases — Kept

**As the maintainer, I want versions and CI in the repository so that releases are verified and changes are traceable.**

Acceptance criteria:

- A release has a version and a Git tag; the package version is distinguishable from the skill versions and the configuration schema version.
- CI checks building and installing the package, the bundled skills, initializing a knowledge base and the main CLI scenarios on test data, without personal data.
- Changes are described in a release history; changes to the note schema and the configuration need a documented migration path.
- CD and automatic publishing are not required.

## Typical scenarios

| User request | Expected behavior | Where the result ends up |
|---|---|---|
| "Save this to the knowledge base" (`add-knowledge`) | Find the topic, agree the takeaways, show the diff of one topic page plus link lines and open-question lines for linked pages, write after "yes" | One topic page; a few lines on linked pages |
| "Save only the part about X" | The same for the named part | The page of topic X |
| `add-knowledge` when nothing new was learned | Say there is nothing new to save; write nothing | — |
| "Let's continue X" | Read the page of X (its own words and open questions first), then continue the explanation | Nothing is written |
| "What do I know about X?" | Find X through the index and search; summarize the page; say plainly if there is none | Nothing is written |
| "Let's review X" / "quiz me on X" | Ask what the user remembers, compare with the page, ask "why" questions, mix in a related topic, list gaps; offer to save the user's formulation verbatim | Only `## In my words`, after "yes" |
| "Put this in my words: …" | Show the exact text and save it verbatim after "yes" (either skill) | `## In my words` of the page |
| "Which topics do I have?" | `kb index`, grouped by tags | Nothing is written |
| "Save this source for later: <link>" (`save-source`) | Open the source (or ask for its text), check for an existing card, show one card with summary, illustrations and how it explains, write after "yes" | One source card; optionally one `## Sources` line on a topic page |
| "Which sources did I save on X?" | `kb index --sources --tag x` and `kb search --type source`; say which cards no topic uses yet | Nothing is written |
| "What changed on this page and why?" | `kb history PATH` with reasons from the commits | Nothing is written |
| "I accidentally deleted a page" | `kb doctor` reports it; `kb restore` returns it without overwriting a newer version | The vault's Git history |
| "Sync my knowledge" | Commit outside edits and push to the private remote; report failures | The vault's repository and remote |
| "Update the tools" | `kb update`: upgrade the package and reinstall the skills | The vault is not touched |
| "What's the status of my job application?" | Read the tracker; do not copy it into the vault | The external system |

## What remains to be chosen

1. The exact shrink threshold of the rewrite guard (50% as a start) and the page budget (about 200 lines): calibrate on the first real rewrites.
2. The Git host of the vault's remote (the user's choice).
3. The release process and whether CD is needed.
4. How Cursor handles skills it sees in two directories; which environment variables identify Codex and Cursor for provenance ([clients-v0.md](clients-v0.md)).
5. When the base is large enough for an optional search backend (qmd) and whether to add a "related pages" suggestion command.
6. Whether spaced repetition is wanted at all; if it is, its state lives outside the vault.
7. Whether the flags for hand-edited lines are enough, or explicit "keep" markers are needed; whether duplicate detection by embeddings is needed.
8. Whether a browser capture of source cards without an agent (an Obsidian Web Clipper template) is worth adding after stage 6.

## Boundaries

- The knowledge base is not a learning tracker: no per-day history, no review schedule, no status tags.
- No raw-source folder and no copies of articles, trackers or repositories. A source card holds a summary written by the agent, not a copy of the text or the images.
- No `log.md` and no index file maintained by the model: Git keeps the log, the CLI generates the index.
- No check of the whole knowledge base by the model; checks are limited to the written page and the pages it links to.
- No cascade of edits across many pages: one rewritten page per run, targeted lines elsewhere.
- No automatic saving of answers or conversations; no hooks that write.
- Loading the whole vault into a request is not intended.
- Personal knowledge never goes into the package repository.

## Requirements history

- **2.0 — 2026-10-12:** requirements restated around topic pages after roadmap stage 4 and the LLM Wiki research. Changed: US-04 (topic pages), US-07, US-08 (generated index), US-09 (profile without history), US-10 (in-place rewrite through an approved diff), US-12 (provenance in commit trailers), US-13, US-24 (one topic page per run, "nothing new" outcome, marking only doubtful claims). New: US-25 (review), US-26 (explicit links), US-27 (checking linked pages when writing), US-28 (tags), US-29 (In my words). Frozen: US-02, US-03, US-06, US-14, US-21, US-22. US-05 kept as a boundary. US-17–US-20 marked done. ChatGPT stays out of scope. The history of versions 1.0–1.11 is in [personal-knowledge-user-stories-v1.md](personal-knowledge-user-stories-v1.md).
- **2.1 — 2026-10-19:** after checking design 2.0 against the research. US-04: duplicate topics refused by the CLI and checked by the agent against the index, aliases in the user's language, the user's own sections kept. US-08: ranked search, a full-text cache later. US-10: section summary, flags for hand-edited lines and hidden text. US-11: skills write only through `kb` even with other Obsidian skills installed, no risky examples in skill texts. US-24: closest pages for a new page, independent approval of the plan's parts, only the change shown after the plan is edited, text from pages and sources treated as data. US-25: the page as the reference, the user sets the angle. US-26 and US-27: unlinked mentions on the written page. US-29: both skills can save "In my words".
- **2.2 — 2026-10-19:** sources for later, decided by the user after `reports/Источники на потом: захват и summary.md`. US-02 moves from Frozen to Changed: the `save-source` skill saves one source card from an opened or pasted source, with illustrations referenced and described, `url` or `ref`, one card per source, duplicates refused by normalized URL, shared tags, no stored status and no `## In my words`. US-04 and the scope decisions: source cards as the revised `source` type. US-07 and US-24: the skills find and use the cards; `add-knowledge` offers `save-source` for unrelated sources. US-08: `kb index --sources`, the type in search results. US-11: the third skill. US-16, US-28, scenarios, open choices and boundaries updated. Trailer queries move to roadmap stage 7.
