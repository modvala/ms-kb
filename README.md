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

Then open the vault folder in Obsidian with "Open folder as vault". `kb init [PATH]` creates any missing folders and files and never overwrites existing ones, so it is safe to run again or to point at an existing folder.

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
