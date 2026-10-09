---
title: "Personal Knowledge System — User Stories"
document_version: "1.9"
created: "2026-10-05"
updated: "2026-10-09"
language: en
status: requirements_baseline
origin: "Decisions from discussions with the user, consolidated into user stories"
---

# Personal Knowledge System — User Stories v1.9

This document records the desired outcome and the decisions made about the personal knowledge base. It does not mean that integrations are already connected or that the system has been implemented. Acceptance criteria turn agreements into verifiable behavior; specific tools and unresolved questions are listed separately.

## Goal

As a user who studies AI/ML and conducts research together with AI agents, I want to accumulate my own knowledge in Obsidian, use it in subsequent conversations and supplement it with context from external systems, so that I can continue learning with what I have already studied taken into account and keep the useful results of my work.

**Main architectural decision:** Obsidian is the primary and canonical store of accumulated knowledge. Notion, Git/GitHub and other systems provide additional context and functionality. Obsidian's priority as the knowledge base does not override the authority of external systems in their own domains: the current status of a job application comes from the tracker, the state of an implementation comes from the repository.

**Delivery and storage decision:** GitHub hosts the source code of a versioned, installable package: the library, skills, and tools for initialization and connector setup. The package is installed locally; skills are additionally available in the user scope outside the project repository. A single installation can serve several independently initialized knowledge bases. Each knowledge base is a separate local Obsidian vault with its own configuration, connections and separate cloud storage for synchronization. Another user installs the same package and connects their own data. Personal knowledge is not part of the package repository. GitHub is used only for package code: the vault and the knowledge base's Markdown files are not stored on GitHub and are not synced to any repository. Versions and CI are maintained in the repository; whether CD is needed and how it would work is still to be determined.

| Component | Content and purpose |
|---|---|
| Project repository on GitHub | Package source code, skills, templates, documentation, versions and CI |
| Installed package | Reusable tools for working with knowledge bases and initializing them |
| User skills scope | Access to skills from supported clients and from different working directories |
| Knowledge base instance | A separate vault, its configuration, profile, sources and connections |
| Knowledge base sync storage | Data of a specific knowledge base in separate cloud storage (not GitHub) |

## MVP decisions (v1.3)

Requirements US-01…US-23 remain the target state. The first implementation is limited by the following decisions:

| Area | MVP decision |
|---|---|
| Users | One user: the project author. The "another user" scenario (US-22) is not implemented in the MVP; the architecture must not rule it out |
| Delivery | Package on GitHub in the author's personal repository. First install: `uv tool install` from GitHub, then `kb setup` (installs skills into the chosen clients, creates the vault). Updating is a single command, `kb update`. Client plugins are not used in the MVP (command names are provisional) |
| Language and tooling | Python, project management and installation via `uv` |
| AI clients | Claude Code, Codex, Cursor; they work with the vault directly. ChatGPT is out of scope at this stage |
| Vault access | The listed clients read and write the local vault's Markdown files directly; a dedicated MCP connector to one's own knowledge base is not required for the MVP |
| Knowledge base | One knowledge base, created from scratch with the package's tools; there is no existing vault. Support for multiple knowledge bases (US-21) is not implemented in the MVP; the architecture must not rule it out |
| Write policy | Only on explicit skill invocation by the user (US-24); the agent does not save knowledge on its own initiative |
| Storage and sync | The vault is a local folder outside Google Drive; agents write notes only locally. Syncing with Google Drive is a separate step. The goal is a cloud copy so the knowledge base is not lost to accidental local deletion. The vault and notes do not go into any GitHub repository. Phone access is deferred |
| Obsidian | Not required for the package and agents to work; needed for convenient reading and navigation, can be installed at any time |

## 1. Content and boundaries of the knowledge base

### US-01. A single store of accumulated knowledge

**As a user, I want to keep my knowledge in Obsidian so that I have one clear knowledge base for learning, research and reusing conclusions.**

Acceptance criteria:

- Explanations of concepts, research results, learning outcomes and durable conclusions are saved in Obsidian.
- The main content of notes is stored in Markdown and is readable without Obsidian.
- Notes can contain metadata, links to other notes and attachments.
- Connecting an additional source does not turn it into a replacement for the main knowledge base.

### US-02. A link and a short summary instead of a copy of the source

**As a user, I want to save a link and a short summary of external material so that I remember its meaning and usefulness without re-hosting the original in my knowledge base.**

Acceptance criteria:

- A source note contains the original link, the title and a short summary.
- It can record key takeaways and the reason for saving.
- The full content of an article, document or website is not copied by default.
- The link leads to the original; if further research is needed, the agent goes to the original material.
- A short summary is not presented as the full text of the source or as a check of its current state.

### US-03. Synthesis of multiple sources

**As a user, I want to save my own research, comparisons and summary tables so that the knowledge base contains the useful result of analyzing multiple sources.**

Acceptance criteria:

- A research result can include a summary table, explanations, conclusions and limitations.
- Sources are listed as links to the originals or to short source notes.
- The agent's conclusions are distinguishable from facts obtained from sources.
- Research has a date: a comparison of solutions at a specific moment is not presented as timeless knowledge.
- A separate note for each source is not required if links within the research are sufficient.

### US-04. Different kinds of notes and links between them

**As a user, I want to distinguish concepts, sources, research, learning sessions and project knowledge so that I can find material by its purpose.**

Acceptance criteria:

- Base types are provided: `concept`, `source`, `research`, `learning-session`, `project`.
- Notes are connected by topical metadata and links between notes.
- From a concept note one can navigate to the research and sources its explanation is based on.
- A project note holds knowledge, rationale and conclusions about a project; current tasks and code are kept in external systems.
- The name of a separate type for observations/insights remains a schema detail rather than a mandatory sixth type.

### US-05. External data stays in external systems

**As a user, I want to use Notion for tracking and Git for code so that I do not have to maintain them again in Obsidian.**

Acceptance criteria:

- Application statuses, tasks and operational tables are read and updated in the corresponding tracker.
- Code, commits, issues and PRs are read and updated in the corresponding repository/service.
- The agent does not create a copy of the tracker or repository in Obsidian to perform an ordinary task.
- If a new tracker is needed, the agent suggests a suitable external system; it does not treat Obsidian as the default place for tracking.
- The knowledge base can store a link to an external entity and useful context about how it relates to a topic.

### US-06. Knowledge gained from practical work

**As a user, I want to save durable conclusions from working with trackers, code and external materials so that practical experience enriches my knowledge base.**

Acceptance criteria:

- Obsidian stores a formulated piece of knowledge or an observation along with what it is based on.
- A link to an issue, document, research or tracker makes it possible to reconstruct the context of a conclusion.
- A single event is not automatically turned into a universal pattern.
- For example, the status of a single job application stays in Notion; a confirmed analysis of job search results can become a separate piece of knowledge.
- The rationale for an architectural decision can be saved in Obsidian with a link to the implementation in Git.

## 2. Reading context and learning

### US-07. Referring to what was studied before

**As a user, I want the agent to find relevant knowledge when I continue learning so that the explanation takes previous discussions and remaining questions into account.**

Acceptance criteria:

- On requests like "let's continue", "what have we already covered", "remind me what was unclear", the agent consults the knowledge base.
- The material found is used to determine what has already been studied and what the next steps are.
- If there is no suitable note, the agent continues the explanation and does not invent a history of my learning.
- Simple questions that do not need personal context do not trigger mandatory reading of the whole knowledge base.
- If the knowledge base is not accessible, the agent explicitly separates the available conversation context from unverified history in Obsidian.

### US-08. Selective search and reading

**As a user, I want the agent to retrieve suitable notes or fragments so that a large knowledge base is not loaded in full into every conversation.**

Acceptance criteria:

- The agent first searches for relevant material, then reads the notes or fragments it found.
- Search can use text, note type, topics, metadata and links between notes.
- Depending on the meaning of the request, a particular type can be preferred: explaining a concept — `concept`, past comparisons — `research`.
- Semantic search is acceptable as an additional retrieval method; the mere presence of Markdown or MCP does not mean it already works.
- The choice of a specific search backend does not change the canonical content of notes.

### US-09. A brief learning profile

**As a user, I want a compact description of my current learning context so that the agent quickly understands my topics, level and open questions.**

Acceptance criteria:

- The profile can contain current directions, known topics, recently studied material and open questions.
- It stays brief and links to detailed notes.
- Detailed knowledge is retrieved on demand rather than kept in the profile permanently.
- The profile reflects recorded information; assumptions about what I have understood are not presented as a confirmed result.
- How the profile is connected to each agent is still to be chosen: automatic loading is not assumed by default.

### US-10. Saving and updating learning outcomes

**As a user, I want to record useful outcomes of study sessions and update existing knowledge so that the next conversation continues the accumulated work.**

Acceptance criteria:

- Before creating a note, the agent searches for existing material on the topic.
- If a suitable note exists, new information extends it or a related note without repeating what is already written.
- A learning session summary can contain the topics studied, conclusions and remaining questions.
- Contradictions with an older note are flagged; an update does not erase the basis of the previous conclusion without explanation.
- After a note changes, the search index, if one is used, must reflect the new content.
- Writing happens only on explicit skill invocation by the user (see US-24); automatic saving and writing on the agent's initiative are not used.

### US-24. Saving conversation outcomes on explicit command

**As a user, after a long conversation in which I worked through a topic, I want to invoke a skill (working name `add-knowledge`) so that the agent compiles a summary of the conversation and saves it to the knowledge base for future use.**

Acceptance criteria:

- The skill is invoked explicitly by the user; without an invocation the agent does not create or modify notes.
- The agent extracts from the conversation the original question, the explanations and conclusions obtained, the sources used and the remaining questions.
- The result is distributed across note types: the conversation summary — `learning-session`; durable explanations — creating or extending a `concept`; comparisons — `research`; important external materials — `source` or links within a note.
- Before writing, the agent searches for existing notes on the topic and extends them without repetition instead of creating duplicates (US-10).
- Conclusions that were discussed in the conversation but not confirmed are marked as assumptions or open questions and are not presented as learned (US-09).
- Links to sources mentioned in the conversation are preserved; the content of sources that were not opened in the conversation is not invented.
- Provenance is recorded: the skill, its version, the date; the client and model, if known (US-12).
- After writing, the agent lists the files it created and changed.
- The whole conversation can be saved, or a part/topic specified by the user.

## 3. Skills and provenance of materials

### US-11. Working rules are defined by skills

**As a user, I want to define rules for research, summarization and knowledge updates through skills so that the agent processes materials consistently.**

Acceptance criteria:

- A skill describes when to look for context, what to read and what result to save.
- The rules follow the principle: Obsidian stores accumulated knowledge, while operational data stays in external systems.
- For saving, there are rules for finding existing notes, extending them and merging without duplication.
- A skill can specify required and optional sources for its scenario.
- A skill defines the workflow; technical access is provided by a separate integration/MCP.
- The exact set of skills and the division of their responsibilities is still to be determined.

### US-12. Metadata about the skill and its version

**As a user, I want to see which skill and which version of the rules created a piece of material so that I understand its origin and can find the results of older approaches.**

Acceptance criteria:

- Notes created through a skill record the skill identifier and the version used at creation.
- There are creation/update dates and links to sources if the result is based on them.
- The metadata makes it possible to select notes by skill and version without manually reading each note.
- A link or another unambiguous reference to the rules of the corresponding version is available; a simple tag without a version is not enough.
- When a note is updated by another skill or version, the provenance of the original result remains distinguishable from the provenance of the update.
- Data about the model, agent, template or configuration is recorded if known; unknown values are not invented.

### US-13. Revising knowledge and rules

**As a user, I want to find materials that need revision so that I can update research and the results of old skills while preserving their provenance.**

Acceptance criteria:

- It is possible to identify materials created by a chosen skill version and research as of a chosen date.
- An update of a material under new rules or with new sources can be initiated.
- New processing is not attributed to the old skill and does not change the original creation date.
- A dated research result is distinguishable from an updated concept explanation.
- The specific way of storing note version history and skill snapshots has not yet been chosen.
- Regular automatic rebuilds are not part of the approved requirements.

## 4. Additional sources and portability

### US-14. Source registry

**As a user, I want to declare the knowledge base and additional sources in a single registry so that a new agent understands where to look for the needed context.**

Acceptance criteria:

- The registry explicitly marks Obsidian as the primary knowledge base and lists supporting sources.
- For each source, its purpose, domain of authority, access method and the identifier of the relevant resource (if applicable) are specified.
- The agent picks the appropriate additional sources for the task; the presence of an entry does not force it to consult every source every time.
- When needed, knowledge from Obsidian is combined with current context from a tracker, repository or the Web.
- If sources disagree, the agent takes the domain of the fact into account: status — from the tracker, implementation — from the repository, accumulated knowledge and explanations — from Obsidian.
- The registry describes sources but does not connect MCP servers or grant access automatically.

### US-15. Working with different agents

**As a user, I want to use shared rules and a registry with different AI agents so that I do not have to explain the structure of my knowledge base to each of them from scratch.**

Acceptance criteria:

- There is an entry instruction that points the agent to the source registry and the applicable skills.
- Rules and metadata are available in portable text formats.
- An agent that has received these instructions and the necessary connections can find knowledge and the corresponding additional sources.
- Clients may require different ways of connecting instructions and MCP; universal automatic support for `AGENTS.md` is not assumed.
- Missing access is flagged explicitly, and the content of an unavailable source is not imitated.
- Compatibility with specific clients will be verified during implementation.

## 5. Visual representation

### US-16. Visual learning notes

**As a user, I want to supplement knowledge with illustrations, diagrams and topic maps so that studying and reviewing material is easier for me.**

Acceptance criteria:

- Images and other necessary attachments can be attached to notes.
- Architectures and processes can be described with Mermaid diagrams inside Markdown.
- Links between notes are used for navigation and for displaying the knowledge graph.
- A Canvas with links to notes can be used for an overview of a large topic.
- When necessary, the important meaning of an image is explained in text accessible to the agent.
- Excalidraw is acceptable as an additional tool; mandatory installation of this plugin is not approved.

## 6. Delivery, local installation and synchronization

### US-17. The project as a locally installable package with skills

**As a user, I want to install a versioned package with a library and skills from the project on GitHub so that I can reuse tools for working with knowledge bases on my computer.**

Acceptance criteria:

- The repository contains the source code of the installable package, the bundled skills, templates, configuration examples and documentation.
- There is a documented way to install the package from the GitHub project and check the installed version.
- Installing the package and initializing a knowledge base instance are separate actions: creating a new knowledge base does not require a new checkout or copying the source code.
- The library connects to a separately specified local vault; the path to the knowledge base is configured by the user.
- User notes, research, attachments and the learning profile are not included in the library repository.
- Updating or reinstalling the library does not overwrite the content of the knowledge base.
- Examples and templates in the repository are distinguishable from the user's personal knowledge and do not require publishing that knowledge.
- The package language is Python, installed from the GitHub repository via `uv`. The first install is two steps (installing the CLI and `setup`); updating the package together with the skills in all chosen clients is one command. Final command names are still to be determined.
- It is possible to check the consistency of the CLI version and the installed skills and get a hint if they diverge.

### US-18. Installing skills into the user scope

**As a user, I want to additionally install skills into my user scope so that I can use them in other repositories and supported AI clients without being tied to the project's working folder.**

Acceptance criteria:

- Bundled skills can be installed into the user scope, not only inside the library repository.
- Skills are part of the package distribution; making them available does not require manually copying them from a working checkout for each new knowledge base.
- For supported local clients, skills are available when working in another repository or outside a specific project.
- Skills find the configuration and the right knowledge base through explicit settings; the current working folder is not considered the only source of the vault location.
- When there are several knowledge bases, the chosen instance is specified explicitly or determined by an unambiguous client/project setting; data from different knowledge bases is not mixed by default.
- Installed skills retain the identifiers and versions needed for note provenance.
- Installation and updating of skills are documented for each supported client.
- Clients supported in the MVP: Claude Code, Codex, Cursor. Skills are written in a common portable format, and installation into each client is done by a separate adapter.
- ChatGPT is out of scope at this stage. Possible future integration paths are described in the design document (§12.2).
- The specific user directories and installation mechanism (client plugin, copying skills, entry instructions) for each client have not yet been approved.

### US-19. A separate local knowledge base

**As a user, I want to install and store the knowledge base locally, separate from the library repository, so that I own my data and can update the tools for working with it independently.**

Acceptance criteria:

- The vault is located in a separate user directory outside the library repository's working tree.
- It is possible to connect an existing vault or create a new knowledge base from the bundled templates.
- Notes, attachments, the personal learning profile and user metadata belong to the knowledge base/user data, not to the library source code.
- User configuration of sources and access is stored separately from the distributed configuration examples.
- The knowledge base can be read in Obsidian regardless of the library checkout and version.
- Deleting the checkout or reinstalling the library does not delete the vault.
- Local search and work with already available notes do not require synchronization on every access; external sources may require a network.

### US-20. Syncing the knowledge base through separate storage

**As a user, I want to sync a separate local knowledge base with separate cloud storage unrelated to GitHub so that the data is preserved independently of the library repository and is available on other devices.**

Acceptance criteria:

- The distribution provides and documents synchronization through the chosen cloud storage.
- The vault, notes and attachments are not stored or synced via GitHub — neither in the library repository nor in a separate repository.
- One synchronization mechanism is used per vault; support for multiple providers is not required, and the specific option is chosen before implementation.
- Notes and necessary attachments are synced; canonical knowledge does not depend on transferring a derived search index, which can be rebuilt.
- Local changes are pushed to the chosen storage, and remote changes can be pulled locally.
- Synchronization is not replaced by one-way backup; backup, if needed, is considered separately.
- When local and remote changes diverge, the conflict is detected and resolved according to defined rules without silently losing one of the versions.
- If the storage is temporarily unavailable, local data is preserved; once access is restored, synchronization can continue.
- User access settings are not included in the distributed library repository.
- MVP: the vault is stored in a local folder outside Google Drive; notes are always written locally. Syncing with Google Drive is done as a separate step and does not affect writing. The main goal is a cloud copy so the knowledge base is not lost to accidental local deletion.
- Accidental local deletion does not destroy the cloud copy; previous versions of changed and deleted files can be restored.
- The mechanism (a one-way `kb sync` via `rclone` is recommended) and how it is triggered are refined during implementation.
- Access to the knowledge base from a phone and other devices is deferred and not part of the MVP.

### US-21. Initializing multiple independent knowledge bases

**As a user of the installed package, I want to initialize a new local knowledge base with its own configuration so that I can maintain several knowledge bases without reinstalling the library.**

Acceptance criteria:

- The package provides a documented way to initialize a new knowledge base in a chosen local directory.
- For a new knowledge base, the necessary structure/templates and a separate configuration are created, not a copy of personal notes from another knowledge base.
- For each instance, the path to Markdown files, the source registry, connectors and sync storage are set separately.
- One installed package can work with several instances; supporting several knowledge bases does not require several package installations.
- Search, reading, writing and synchronization are performed in an explicitly selected knowledge base; notes and settings of another knowledge base are not changed.
- Derived indexes and sync state, if used, are distinguishable between instances.
- Initializing a new knowledge base does not overwrite an existing knowledge base or its configuration.
- Command names, the knowledge base identifier format and the way the active instance is selected have not yet been determined.

### US-22. Use of the package by another user

**As another user of the project, I want to install the package from GitHub, initialize my own knowledge base and connect its connector so that I can use the system with my own Markdown files and storage.**

Acceptance criteria:

- The instructions describe the path from installing the package to initializing a knowledge base and connecting a supported connector/AI client.
- The user can create a new knowledge base or connect their existing Markdown files/Obsidian vault.
- Configuration, local paths, external resource identifiers and access settings are set by the user themselves.
- Installation does not depend on the package author's personal knowledge base, cloud storage or connectors.
- The code and bundled skills are shared, while the content and configuration of user knowledge bases are independent.
- Connection verification and choosing the knowledge base the connector works with are documented.
- Using someone else's package does not mean gaining access to its author's knowledge.

### US-23. Package versions, CI and releasing updates

**As the project maintainer, I want to maintain package versions and CI in the GitHub repository so that users can install verified releases and understand changes to the tools.**

Acceptance criteria:

- A package release has a version identifier and is tied to a specific state of the source code in Git.
- The user can determine the installed version and install a chosen published release in the way described in the documentation.
- CI automatically checks essential scenarios: building/installing the package, presence of bundled skills, knowledge base initialization and instance independence.
- Checks use test data and do not require the author's personal knowledge or accounts.
- Package changes are described in the release history; changes to the configuration schema and skill compatibility are flagged explicitly.
- The package version is distinguishable from the version of a specific skill and the configuration schema version, so that provenance does not lose precision.
- Updating the package does not overwrite user Markdown files; if configuration changes are needed, a documented migration path is provided.
- Having CI does not imply mandatory automatic release or deployment. CD, the package publishing method and release conditions remain open decisions.

## Verifying the result against typical scenarios

| User request | Expected behavior | Where the result ends up |
|---|---|---|
| "Compile this conversation and save it to the knowledge base" (`add-knowledge`) | Extract conclusions and open questions, find existing notes, create/extend them with provenance, list changed files | Obsidian |
| "Save this article: a link and a short summary" | Create/extend a source note with the URL and metadata | Obsidian; the original stays at the link |
| "Compare several approaches to agent memory" | Study the sources and save a synthesis with a table and links | Obsidian |
| "Let's continue studying RAG" | Find previous knowledge and open questions, then continue the explanation | Learning outcomes — Obsidian |
| "What's the status of my job application?" | Read the corresponding tracker; do not create a copy of it | Notion/existing tracker |
| "What changed in the implementation?" | Consult the repository; if needed, compare against the rationale | Code — Git; useful knowledge — Obsidian |
| "Which notes were created by the old skill?" | Find them by skill/version metadata and show the selection criteria | A selection from Obsidian |
| "Update the research with the new skill" | Update the result with correct provenance and distinguishable history | Obsidian |
| "Let's connect another agent" | Hand over instructions/registry/skills and set up access for that client | The shared knowledge base content is preserved |
| "Install the project on my computer" | Install the package with skills from the GitHub project and separately initialize a knowledge base | The installed package and the user's knowledge base are independent |
| "Use the knowledge skill in another repository" | Load the skill from the user scope and access the configured vault | The skill does not depend on the current repository |
| "Update the library" | Update the tools without changing personal knowledge | The vault stays independent of the update |
| "Sync my knowledge" | Exchange changes with the chosen separate storage and flag conflicts | Separate cloud storage (not GitHub) |
| "Create a second knowledge base" | Initialize a new instance with separate settings and storage | A separate vault; the installed package is reused |
| "Another user wants to install the system" | Install the same package, create/connect their knowledge base and their connector | The data and configuration belong to that user |
| "Release a new version of the package" | Verify the package in CI and prepare a versioned release | The package repository; personal knowledge bases are not part of the release |

## What remains to be chosen

These items are not considered accepted technical decisions:

1. The specific local path to the separate vault. Local storage separate from the library and direct file access from Claude Code/Codex/Cursor are accepted for the MVP.
2. Whether an Obsidian integration/MCP is needed after the MVP (for remote clients or search); its actual search, read and write capabilities.
3. Retrieval for the first implementation: text, semantic or hybrid search; the model and indexing method if needed.
4. ~~Folder structure and metadata schema~~ — decided in v1.8: [note-schema-v0.md](note-schema-v0.md). Open: the source registry format.
5. The minimal set of skills besides `add-knowledge` and how entry instructions are connected to each client.
6. ~~Write policy~~ — decided in v1.3: only on explicit skill invocation (US-24). ~~Plan before editing~~ — decided in v1.9: new notes are created right away; before existing notes are extended, the agent shows a plan and waits for confirmation (design §11).
7. Storage of note history, exact skill versions and provenance changes.
8. ~~MVP scope~~ — decided in v1.3 (see "MVP decisions"). Open: the order in which additional sources are connected.
9. ~~Language and package manager~~ — decided in v1.3: Python + `uv`, installation from GitHub. ~~Install/update scheme~~ — decided in v1.5: `uv tool install` + `setup`, updating in a single command. Open: final command names.
10. ~~User skills directories~~ — decided in v1.8: [clients-v0.md](clients-v0.md). Open: how Cursor handles duplicate skills and how to deliver the global instruction to Cursor.
11. ~~Sync provider~~ — decided: not GitHub (v1.4), Google Drive (v1.5), local vault, sync as a separate step (v1.6). Open: the mechanism (`rclone` is recommended), how it is triggered, phone access (deferred), note change history.
14. Connecting ChatGPT — outside the current scope; revisit after the MVP (options are in design §12.2).
12. ~~Configuration format~~ — decided in v1.8: TOML at `~/.config/ms-kb/config.toml`; skills find the vault by calling the `kb` CLI ([note-schema-v0.md](note-schema-v0.md) §6).
13. The specific CI, versioning and migration policy, the release process and whether automatic publishing/CD is needed.

## Boundaries of the first implementation

- A separate Qdrant/vector DB and Neo4j are not prerequisites for getting started.
- The knowledge base must not become an archive of copies of websites, trackers and repositories.
- Loading the whole vault into every request is not intended.
- Mentioning an integration in the registry does not mean it is connected and available.
- Personal knowledge is not shipped inside the library repository and is not stored on GitHub; the vault is synced only through separate cloud storage.
- Installing user skills and giving a remote client access to the local knowledge base are different tasks.
- Supporting two sync providers at once is not a prerequisite for the first implementation.
- Each knowledge base instance has its own configuration and data; the shared package does not automatically merge knowledge from different knowledge bases.
- Maintaining CI and versions is part of the project requirements; automatic publishing/CD is not yet mandatory.
- This document records requirements; it does not install skills, plugins or connections.

## Expected outcome

The user gets a versioned package maintained on GitHub, with a library, skills, knowledge base initialization and CI. After a local install, they can create several independent knowledge bases or connect existing vaults, with each instance having its own configuration, connectors and cloud sync storage. Other users install the same package and work with their own data. Skills are available in the user scope of supported clients; personal knowledge is not part of the repository or the package release.

The knowledge base is convenient to read and extend both directly and through connected agents. Agents find relevant previously studied material, save useful summaries and research with provenance, and turn to additional sources for current statuses and implementations. The next discussion can continue from the accumulated knowledge without re-explaining the whole history.

## Requirements history

- **1.0 — 2026-10-05:** the original 16 user stories covering the knowledge base, agents, skills, provenance and additional sources.
- **1.1 — 2026-10-05:** added US-17–US-20: delivering the library from Git, user-level skills installation, a separate local vault and its synchronization. Refined the architectural decision, scenarios and open technical questions.
- **1.2 — 2026-10-05:** delivery refined as an installable package with skills; added US-21–US-23: initializing multiple independent knowledge bases, installation by another user, and maintaining versions with CI. CD left as an open decision.
- **1.3 — 2026-10-09:** added the "MVP decisions" section: one user, Python + `uv`, Claude Code/Codex/Cursor clients, a new knowledge base from scratch, tentatively syncing via GitHub. Write policy approved: explicit skill invocation only; added US-24 (`add-knowledge`). ChatGPT removed from the MVP.
- **1.4 — 2026-10-09:** GitHub excluded as knowledge base storage: the vault and notes are synced only through separate cloud storage; GitHub is used only for package code. Updated US-20, US-22, MVP decisions, scenarios and boundaries.
- **1.5 — 2026-10-09:** installation scheme (`uv tool install` + `setup`, updating in a single command, version checks); sync provider — Google Drive, the goal being a cloud copy against accidental local deletion, mobile access deferred; Obsidian not required for the package to work. Updated "MVP decisions", US-17, US-20, open questions.
- **1.6 — 2026-10-09:** the vault is stored locally outside Google Drive, sync is a separate step (US-20). ChatGPT brought back as a place for learning chats: materials arrive via a cloud inbox and are processed by `add-knowledge` (US-18, US-24). Added open question 14.
- **1.7 — 2026-10-09:** ChatGPT excluded from scope at this stage; the cloud inbox and pulling materials during sync removed. Updated "MVP decisions", US-18, US-20, US-24, open question 14.
- **1.8 — 2026-10-09:** roadmap stage 0: open questions 4, 10 and 12 decided with links to `note-schema-v0.md` and `clients-v0.md`.
- **1.9 — 2026-10-09:** roadmap stage 2: open question 6 decided (a plan before extending existing notes).
