# ms-kb

A personal knowledge base on Obsidian and a set of skills for Claude Code, Codex and Cursor.
This repository contains only the package code: the vault and notes are not stored here.

## Installation

```bash
uv tool install git+https://github.com/modvala/ms-kb
kb --version
```

## First run

```bash
kb setup      # asks for the vault folder (default ~/Knowledge/main), the clients and a private remote
kb doctor     # checks the configuration, the vault, its history and its off-machine copy
kb where      # prints the vault path
```

Keep the vault outside folders synced by iCloud Drive, Google Drive, Dropbox or OneDrive (including `~/Documents` and `~/Desktop` when iCloud "Desktop & Documents" is on). The default `~/Knowledge/main` is fine.

`kb setup` also installs the `add-knowledge`, `kb-recall` and `save-source` skills into the chosen clients (`~/.claude/skills/` for Claude Code, `~/.agents/skills/` for Codex; Cursor reads both), and adds a short global instruction that tells the agent the knowledge base exists: a block between `<!-- ms-kb:begin -->` and `<!-- ms-kb:end -->` in `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` (`$CODEX_HOME` is respected). Only that block is ever changed; `--no-instructions` skips it. Cursor keeps its rules in the app, so `kb setup` prints the text to paste into Settings → Rules → User Rules (`kb install-skills --print-instruction` shows it again). Then open the vault folder in Obsidian with "Open folder as vault". `kb init [PATH]` creates any missing folders and files and never overwrites existing ones, so it is safe to run again or to point at an existing folder. `learning_profile.md` is your data: if it disappears from a vault in use, `kb init` does not recreate it and `kb doctor` suggests restoring it from a backup; `kb init --new-profile` starts an empty one.

## Saving knowledge

At the end of a research conversation, invoke the skill: `/add-knowledge` in Claude Code and Cursor, `$add-knowledge` in Codex. The agent finds the topic through `kb index` and `kb search`, and agrees the main takeaways with you. It then shows one plan: the diff of **one topic page**, the lines for pages it links to, and what it found on them. You approve the parts separately, and nothing is written before that. If nothing new was learned, it says so and writes nothing.

A topic page is `topics/<Title>.md`, one current page per topic, with fixed sections: `Summary`, `In my words`, `Key ideas`, `Details`, `Open questions`, `Related`, `Sources`. **`## In my words` is yours**: agents save there only your exact text, after your yes, and a rewrite carries it over unchanged. Headings stay in English, the content is in your language. Sections you add in Obsidian are kept.

To keep a source for later without making a page of it, say "save this source for later" (`/save-source`, `$save-source`). The agent opens the source or asks you to paste it, then shows a short card in `sources/`: what it says, the illustrations worth reusing, how it explains. Images are described with a reference to where they are, not copied.

## Continuing and reviewing

In a new conversation, say "let's continue with RAG" or "what did I leave unclear about transformers". The `kb-recall` skill (`/kb-recall`, `$kb-recall`) finds the page and starts from your own words and open questions. It names the source cards on the topic and says so when it finds nothing. Questions that need no personal context do not touch the knowledge base.

Say "let's review RAG", "quiz me on RAG" or "проверь меня по RAG" to be tested. The agent asks what you remember before showing anything, compares your answer with the page, asks "why" and "when not" questions, mixes in a related topic and lists the gaps. No review state is stored. At the end it may offer to save your formulation in `## In my words`, the only thing `kb-recall` writes.

## History and restoring notes

The vault is its own Git repository (never this package's repository). `kb init` creates it, with a `.gitignore` for Obsidian's churn. Every write is a commit `kb: create|rewrite|link|extend|my-words <path>` whose trailers record the skill, its version, the package version, the agent and the reason for the change. Edits made in Obsidian are committed separately as `external: …` before the next kb write or `kb sync`, so a half-finished edit never ends up in an agent's commit. If `git` is missing or a commit fails, the note is still written and `kb doctor` reports the problem.

kb refuses to write text that looks like a key or token (AWS, GitHub, `sk-…`, Slack, Google, Stripe, private keys; [gitleaks](https://github.com/gitleaks/gitleaks) too when it is installed). Outside files that contain one, or are larger than 50 MB, are not committed and are reported. If a refused string is really not a secret, pass `--allow-secret-like` yourself.

```bash
kb history topics/RAG.md       # every version of a page with its reason, also after it was deleted
kb history topics/RAG.md --reason rerank   # changes of a page by reason
kb history --skill add-knowledge --version 0.7.0   # what one version of a skill wrote
kb history --deleted           # files deleted from the vault
kb doctor                      # reports deleted, damaged or moved notes and links that stopped resolving
kb restore topics/RAG.md       # bring back the last committed version
kb restore topics/RAG.md --at 1a2b3c4 --dry-run
```

`kb restore` never overwrites silently. If the path is free, the note goes back there. If a different file is there, the old version is written next to it as `RAG.restored-<timestamp>.md` with a diff, so you can merge what you need. `--force` replaces the file after committing the current version to history. If a deletion was intentional, `kb doctor --ack PATH` stops reporting it. Other places to look: Obsidian's `.trash/` folder, Obsidian's File recovery core plugin and Time Machine.

## Off-machine copy

Local history does not survive losing the disk, so `kb sync` pushes the vault's repository to a **private** remote of your choice:

1. Create an empty private repository for the vault only (for example on GitHub or GitLab). Never use the ms-kb repository or a project repository.
2. Make sure `git push` to it works without a prompt: an SSH key, or, narrowest, a deploy key with write access to that one repository. kb stores no credentials.
3. Run `kb setup --remote git@github.com:<you>/<vault-repo>.git`. On macOS, `kb setup` offers to run `kb sync` hourly with a LaunchAgent (`kb sync --schedule on|off|status`; log in `~/Library/Logs/ms-kb/sync.log`).

`kb sync` commits outside edits and pushes. It never force-pushes and never pulls. A rejected or failed push is reported, local commits are kept, and the next run pushes them. `kb doctor` warns when commits have not been pushed for a day or the schedule is not loaded. After losing the computer, `git clone <remote> ~/Knowledge/main` and `kb init ~/Knowledge/main` bring the vault back.

Choosing a host: on GitHub Free, private repositories cannot forbid force-pushes. That is acceptable because the remote is one of three copies (the local `.git`, Time Machine, the remote), but stronger options exist: GitLab Free (protected branches on private projects), GitHub Pro with "Do not allow bypassing" set, or a bare repository on a NAS with `receive.denyNonFastForwards`. Keep Time Machine on as the independent local copy.

### Keeping agents away from vault files

The skills tell agents to change the vault only through `kb` and never to delete, move or rename files there. That is guidance, not protection. The settings that do protect it:

- Keep the vault outside every agent's working directories.
- Claude Code: deny `Edit(<vault>/**)`, add the vault to the sandbox's `denyWrite`, set `allowUnsandboxedCommands: false`, and let only `kb` run outside the sandbox (`excludedCommands`).
- Codex: use `workspace-write` without the vault in `writable_roots`.
- Cursor: enable File-Deletion Protection and External-File Protection.

`kb setup` never changes these settings for you.

## Updating

```bash
kb update                 # uv tool upgrade ms-kb, then the new kb reinstalls skills and instructions
kb update --ref v0.5.0    # install a specific release
```

After an update, run `kb doctor`; if it reports missing folders or templates, `kb init` adds them. What each release needs is in [CHANGELOG.md](CHANGELOG.md).

`kb where`, which the skills run first, warns when the installed skills come from another version than the CLI, and `add-knowledge` asks before writing in that case. Updating never touches the notes.

## The CLI

The skills write only through the CLI, which you can also use directly:

```bash
kb index                               # the catalogue of topic pages, grouped by tag; --tag T, --tags, --sources, --json
kb search rag --tag ml                 # ranked: title and aliases, then summary and tags, then the text; --type, --field, --json
kb new topic --title RAG --summary "One line" --tag ml/rag --alias "Retrieval" --body-file page.md
kb new source --title "An article" --summary "One line" --url https://example.com/a --tag ml/rag --body-file card.md
kb rewrite topics/RAG.md --body-file page.md --reason "Why" --dry-run      # report and approval hash, writes nothing
kb rewrite topics/RAG.md --body-file page.md --reason "Why" --approve HASH # writes exactly what the report showed
kb link topics/RAG.md "Reranking" --why "improves retrieval"               # one line in ## Related
kb extend topics/RAG.md --reason "Why" --body-file more.md                 # appends '## Section' blocks, never rewrites
kb my-words topics/RAG.md --body-file -                                    # your text, exactly as given
kb validate                            # check every note against the schema and the manifest
kb install-skills                      # reinstall the skills and the global instruction
kb history | kb restore | kb sync | kb update   # see above
```

`kb rewrite --dry-run` reports the sections changed (`--sections` flags changes elsewhere), the diff, what disappears, lines you edited by hand, hidden text and the links to check. `--since HASH` adds the change since a draft you already reviewed. `--approve` refuses when the page or the draft changed after the report, and a body under half of the current one needs your `--allow-shrink`. Older note types (`concept`, `research`, `learning-session`, `project`) stay valid and readable.

The configuration lives in `~/.config/ms-kb/config.toml` (`KB_CONFIG` overrides the path); see [examples/config.example.toml](examples/config.example.toml). Next to it, kb keeps state, not settings: `installed.toml` (skills, instructions, schedule), `vault-<kb>.json` (the manifest of notes and the last commit and push), `drafts-<kb>/` (drafts kept for `kb rewrite --since`, pruned after 7 days) and a lock file.

## Development

```bash
uv sync
uv run pytest
```

## Documents

- [Requirements (user stories) v2](docs/personal-knowledge-user-stories-v2.md)
- [Design v2](docs/personal-knowledge-design-v2.md)
- [Roadmap v2](docs/personal-knowledge-roadmap-v2.md)
- Superseded v1 documents, kept as the history of roadmap stages 0–4: [user stories](docs/personal-knowledge-user-stories-v1.md), [design](docs/personal-knowledge-design-v1.md), [roadmap](docs/personal-knowledge-roadmap-v1.md)
- [Note schema, vault structure and configuration v1](docs/note-schema-v1.md); [v0](docs/note-schema-v0.md) for the older note types and the configuration
- [Release history](CHANGELOG.md), [versioning and migration](docs/releases.md)
- [Client skills and instructions v0](docs/clients-v0.md)
