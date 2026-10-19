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

`kb setup` also installs the `add-knowledge` and `kb-recall` skills into the chosen clients (`~/.claude/skills/` for Claude Code, `~/.agents/skills/` for Codex; Cursor reads both), and adds a short global instruction that tells the agent the knowledge base exists: a block between `<!-- ms-kb:begin -->` and `<!-- ms-kb:end -->` in `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` (`$CODEX_HOME` is respected). Only that block is ever changed; `--no-instructions` skips it. Cursor keeps its rules in the app, so `kb setup` prints the text to paste into Settings → Rules → User Rules (`kb install-skills --print-instruction` shows it again). Then open the vault folder in Obsidian with "Open folder as vault". `kb init [PATH]` creates any missing folders and files and never overwrites existing ones, so it is safe to run again or to point at an existing folder. `learning_profile.md` is your data: if it disappears from a vault in use, `kb init` does not recreate it and `kb doctor` suggests restoring it from a backup; `kb init --new-profile` starts an empty one.

## Saving knowledge

At the end of a learning conversation, invoke the skill: `/add-knowledge` in Claude Code and Cursor, `$add-knowledge` in Codex. Optionally name a topic to save only part of the conversation. The agent writes a learning-session note, creates or extends concept notes, and lists the files it changed. Before extending existing notes it shows a plan and waits for your confirmation.

## Continuing where you left off

In a new conversation, just say "let's continue with RAG" or "what did I leave unclear about transformers". The agent uses the `kb-recall` skill (or invoke it by hand: `/kb-recall`, `$kb-recall` in Codex). It reads `learning_profile.md`, searches for a few relevant notes, and answers from them: what you studied, what was concluded, what is still open, with paths to the notes. It never writes, and it says so when it finds nothing. Questions that need no personal context do not touch the knowledge base.

## History and restoring notes

The vault is its own Git repository (never this package's repository). `kb init` creates it, with a `.gitignore` for Obsidian's churn. Every `kb new` / `kb extend` is a commit `kb: create|extend <path>` whose trailers record the skill, its version, the package version and the agent. Edits made in Obsidian are committed separately as `external: …` before the next kb write or `kb sync`, so a half-finished edit never ends up in an agent's commit. If `git` is missing or a commit fails, the note is still written and `kb doctor` reports the problem.

kb refuses to write text that looks like a key or token (AWS, GitHub, `sk-…`, Slack, Google, Stripe, private keys; [gitleaks](https://github.com/gitleaks/gitleaks) too when it is installed). Outside files that contain one, or are larger than 50 MB, are not committed and are reported. If a refused string is really not a secret, pass `--allow-secret-like` yourself.

```bash
kb history concepts/RAG.md     # every version of a note, also after it was deleted
kb history --deleted           # files deleted from the vault
kb doctor                      # reports deleted, damaged or moved notes and links that stopped resolving
kb restore concepts/RAG.md     # bring back the last committed version
kb restore concepts/RAG.md --at 1a2b3c4 --dry-run
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

`kb where`, which the skills run first, warns when the installed skills come from another version than the CLI, and `add-knowledge` asks before writing in that case. Updating never touches the notes.

## The CLI

The skills write only through the CLI, which you can also use directly:

```bash
kb search rag --type concept           # text, --topic, --field created_by.skill=add-knowledge, --json
kb new concept --title RAG --topic rag --body-file notes.md
kb extend concepts/RAG.md --body-file more.md   # appends '## Section' blocks, never rewrites
kb validate                            # check every note against the schema and the manifest
kb install-skills                      # reinstall the skills and the global instruction
kb history | kb restore | kb sync | kb update   # see above
```

The configuration lives in `~/.config/ms-kb/config.toml` (`KB_CONFIG` overrides the path); see [examples/config.example.toml](examples/config.example.toml). Next to it, kb keeps state, not settings: `installed.toml` (skills, instructions, schedule), `vault-<kb>.json` (the manifest of notes and the last commit and push) and a lock file.

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
- [Note schema, vault structure and configuration v0](docs/note-schema-v0.md)
- [Client skills and instructions v0](docs/clients-v0.md)
