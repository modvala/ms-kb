# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`ms-kb` is a Python package (the `kb` CLI) plus agent skills (`add-knowledge`, `kb-recall`) for a personal knowledge base kept as an Obsidian vault. The repository holds only package code; the vault lives elsewhere (default `~/Knowledge/main`) and must never be committed here (`vault/`, `*.vault/` are gitignored).

## Commands

```bash
uv sync                                   # install deps (Python >= 3.11, deps: ruamel.yaml, tomli-w)
uv run pytest                             # all tests
uv run pytest tests/test_write.py::test_name   # single test
uv run kb --help                          # run the CLI from the checkout
uv build                                  # wheel/sdist into dist/
```

There is no linter or formatter configured. CI (`.github/workflows/ci.yml`, Ubuntu + macOS) runs pytest, builds the wheel, installs it with `uv tool install`, and smoke-tests `kb setup/init/doctor/new/extend/search/validate/sync/restore/history` on a temporary vault with a local bare remote. When changing CLI behavior, keep that smoke script passing.

## Architecture

Everything is in `src/ms_kb/`; `cli.py` is the argparse entry point (`kb = ms_kb.cli:main`) and dispatches to `cmd_*` functions that print and return an exit code.

- **Config** (`config.py`): `~/.config/ms-kb/config.toml`, overridable with `KB_CONFIG`. Supports several named KBs with a `default_kb`; only the default is used today.
- **Vault** (`vault.py`): `init_vault` creates missing folders/templates and never overwrites. Distinguishes *regenerable* files (folders, templates, vault README) from *user data* (`learning_profile.md`), which is created only for a new vault or with `--new-profile` and otherwise reported as missing by `kb init`/`kb doctor`.
- **Notes** (`notes.py`): frontmatter parsing/rendering with ruamel.yaml (round-trip, preserves formatting; dates written double-quoted via `q()`), file naming per note type (`TYPE_DIRS`), and section-level body editing (`append_to_section`, `parse_fragment`).
- **Schema** (`schema.py`): `validate()` returns errors (block a write) and warnings (don't). Required fields per type, provenance entry checks.
- **History** (`history.py`): the vault root is its own Git repository (design §12.1). `cli._finish` takes the vault lock, refuses key-like strings (`secretscan.py`), commits outside edits (`commit_external`, excluding secrets and files over 50 MB), calls `write.save`, then commits only the written path with provenance trailers (`commit_write`). Every `GitError` becomes a warning: Git never blocks a write. `kb sync` pushes (never forced); `kb restore` reads `git show`.
- **Integrity** (`vaultstate.py`, `integrity.py`, `links.py`): `vault-<kb>.json` next to the config holds the manifest (path → sha256/size/title/writer), link targets that resolved, and last commit/push/error; `<kb>.lock` serializes runs. `integrity.check` (used by `kb doctor` and `kb validate`) reports deleted/damaged/moved notes and links that stopped resolving.
- **Schedule** (`schedule.py`): the macOS LaunchAgent running `kb sync --quiet` hourly; all `launchctl` calls go through `schedule.launchctl`, which tests replace.
- **Write** (`write.py`): the *only* code that writes notes. `new_note`/`extend_note` build the result in memory, validate, then `save()` writes and refuses if the file changed meanwhile. `extend` only appends to `##` sections and lists — existing text is never rewritten. `new` refuses exact duplicates and (unless `--allow-similar`) similar titles via `search.find_duplicates`.
- **Provenance** (`provenance.py`): the CLI, not the model, stamps `created_by` / `updates` entries (skill, skill_version, package_version, skill_ref link to the release tag, date, and `agent` only when detected from env — currently just `CLAUDECODE=1`).
- **Installer** (`installer.py`): copies bundled `skills/*` into client dirs (`~/.claude/skills/` for Claude Code, `~/.agents/skills/` for Codex; Cursor reads both), injecting `metadata.package_version` into the copied `SKILL.md`. State is recorded in `installed.toml` next to the config; only folders recorded there are overwritten or removed. Skill versions used in provenance come from `installed.toml`.
- **Instructions** (`instructions.py`): writes `global-instruction.md` into `~/.claude/CLAUDE.md` and `$CODEX_HOME/AGENTS.md` (default `~/.codex`) between `<!-- ms-kb:begin -->` / `<!-- ms-kb:end -->` markers; text outside the markers is never touched.
- **Bundled data**: `templates/` (note templates, vault README, profile) and `skills/` are package resources read via `importlib.resources`, so they ship in the wheel.

The skills (`src/ms_kb/skills/*/SKILL.md`) are instructions to agents and are part of the product: they must only use `kb` commands to touch the vault. `kb-recall` is read-only.

## Tests

`tests/conftest.py` has autouse fixtures that point `KB_CONFIG` and `HOME` at `tmp_path`, clear `CLAUDECODE`/`CODEX_HOME`, point `GIT_CONFIG_GLOBAL` at an empty file, and fake `launchctl` and Time Machine, so tests never touch real config, skills, instruction files, Git settings or launchd. Sync tests push to a local bare repository. The `vault` fixture runs `kb setup` end-to-end via `cli.main([...])`. Most CLI tests call `main()` directly and inspect `capsys` output.

## Docs and conventions

- `docs/` holds the requirements (user stories `US-xx`), design and roadmap — current versions are the `-v2.md` files; the `-v1.md` files are superseded and kept as the history of stages 0–4 — plus the note schema (`note-schema-v0.md`, to be replaced by `note-schema-v1.md` in roadmap stage 5) and client notes (`clients-v0.md`). Design v2 keeps the v1 meaning of §4.1, §9.1 and §12.1–§12.6, which the code cites. Code docstrings cite them as e.g. "note-schema-v0 §4", "design §12.4", "US-10". Keep these references accurate and update the relevant doc when behavior changes; each doc has a `document_version` and changelog.
- Work is organized by roadmap stages; each stage ends in a release commit ("Release vX.Y.0: close roadmap stage N") that bumps `version` in `pyproject.toml` (and `uv.lock`) and marks the stage ✅ in both the roadmap table and stage section. `__version__` is read from package metadata. The skills' `metadata.version` in `SKILL.md` is the skill-rules version and is asserted in `tests/test_installer.py`.
- `README.md` documents user-facing CLI behavior; keep it in sync with CLI changes.
