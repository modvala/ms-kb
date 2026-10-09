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
kb setup      # asks for the vault folder (default ~/Knowledge/main) and the clients
kb doctor     # checks the configuration and the vault
kb where      # prints the vault path
```

`kb setup` also installs the `add-knowledge` skill into the chosen clients (`~/.claude/skills/` for Claude Code, `~/.agents/skills/` for Codex; Cursor reads both). Then open the vault folder in Obsidian with "Open folder as vault". `kb init [PATH]` creates any missing folders and files and never overwrites existing ones, so it is safe to run again or to point at an existing folder.

## Saving knowledge

At the end of a learning conversation, invoke the skill: `/add-knowledge` in Claude Code and Cursor, `$add-knowledge` in Codex. Optionally name a topic to save only part of the conversation. The agent writes a learning-session note, creates or extends concept notes, and lists the files it changed. Before extending existing notes it shows a plan and waits for your confirmation.

The skill writes only through the CLI, which you can also use directly:

```bash
kb search rag --type concept           # text, --topic, --field created_by.skill=add-knowledge, --json
kb new concept --title RAG --topic rag --body-file notes.md
kb extend concepts/RAG.md --body-file more.md   # appends '## Section' blocks, never rewrites
kb validate                            # check every note against the schema
kb install-skills                      # reinstall the skills for the configured clients
```

The configuration lives in `~/.config/ms-kb/config.toml` (`KB_CONFIG` overrides the path); see [examples/config.example.toml](examples/config.example.toml).

## Development

```bash
uv sync
uv run pytest
```

## Documents

- [Requirements (user stories)](docs/personal-knowledge-user-stories-v1.md)
- [Design](docs/personal-knowledge-design-v1.md)
- [Roadmap](docs/personal-knowledge-roadmap-v1.md)
- [Note schema, vault structure and configuration v0](docs/note-schema-v0.md)
- [Client skills and instructions v0](docs/clients-v0.md)
