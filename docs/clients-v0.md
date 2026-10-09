---
title: "Personal Knowledge System — Client Skills and Instructions v0"
document_version: "0.2"
created: "2026-10-09"
language: en
status: approved_for_mvp
design_ref: "personal-knowledge-design-v1.md"
design_version: "1.7"
---

# Client skills and instructions v0

This document records roadmap stage 0 checks of Claude Code, Codex and Cursor. It closes open question 10 from the user stories (user skills directories and adapters) and is the input for the installation adapters in stage 2 (`kb install-skills`) and the global instruction in stage 3.

Status per row: **verified** — checked hands-on on the author's Mac; **docs** — taken from the official documentation only, to be verified hands-on in stage 2.

Checked on 2026-10-09. Clients change their mechanisms (roadmap §5), so `kb doctor` should recheck the paths, not this document.

## 1. Summary table

| | Claude Code | Codex (CLI, IDE, ChatGPT desktop app) | Cursor |
|---|---|---|---|
| User skills directory | `~/.claude/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` (documented and verified); `~/.codex/skills/` also exists locally (legacy) | `~/.cursor/skills/`, `~/.agents/skills/`; **also reads** `~/.claude/skills/` and `~/.codex/skills/` |
| Required frontmatter | none (`description` recommended) | `name`, `description` | `name` (must match the folder), `description` |
| `metadata` map | supported, ignored by the client | not documented; tolerated (§3) | supported |
| Manual invocation | `/<name>` | `$<name>` or `/skills` (CLI/IDE); `@<name>` (ChatGPT app) | `/<name>` in Agent chat |
| Automatic invocation | by `description`; off with `disable-model-invocation: true` | by `description`; off with `policy.allow_implicit_invocation` in `agents/openai.yaml` | by `description`; off with `disable-model-invocation: true` |
| Running `kb` | agent's shell tool | agent's shell tool | agent's shell tool |
| Global instruction | `~/.claude/CLAUDE.md` | `$CODEX_HOME/AGENTS.md`, i.e. `~/.codex/AGENTS.md` (`AGENTS.override.md` takes precedence) | **User Rules in Settings UI only**, no file on disk |
| Status | **verified** (§3) | docs; **verified** (§3) | docs (not installed on the author's Mac) |

Sources: [Claude Code skills](https://code.claude.com/docs/en/skills), [Claude Code memory](https://code.claude.com/docs/en/memory), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md), [Cursor skills](https://cursor.com/docs/context/skills), [Cursor rules](https://cursor.com/docs/context/rules).

## 2. Decisions for the adapters

1. **Install targets.** Two directories cover all three clients:
   - `~/.claude/skills/` — Claude Code (and Cursor, by compatibility);
   - `~/.agents/skills/` — Codex (and Cursor).
   Cursor gets no copy of its own. `~/.codex/skills/` is not used: the current Codex docs name `~/.agents/skills/`.
2. **Duplicates in Cursor.** Cursor reads both target directories, so it may see the same skill twice. Stage 2 checks hands-on how Cursor handles this. If it shows duplicates, the fallback is: when both Claude Code and Codex are enabled, the Cursor adapter does nothing; when only Cursor is enabled, it installs into `~/.cursor/skills/`.
3. **Ownership.** The CLI writes only the skill folders listed in `~/.config/ms-kb/installed.toml` and never touches other skills in these directories (design §4.1).
4. **Global instruction.**
   - Claude Code and Codex: `kb setup` adds a block between markers `<!-- ms-kb:begin -->` / `<!-- ms-kb:end -->` to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`, and replaces only that block on update. Codex respects `CODEX_HOME`.
   - Cursor: there is no file for User Rules. `kb setup` prints the text to paste into Settings → Rules. Without it, `kb-recall` still works through its `description`. This is a known gap for US-15.
5. **Versions in provenance.** The model does not report skill versions (in Claude Code it does not even see the frontmatter, §3). The CLI knows the version of each installed skill from `installed.toml` and stamps it itself (note schema §3). `metadata.version` in `SKILL.md` is for humans and for `kb doctor`.
6. **Agent in provenance.** The CLI fills `agent` only from environment variables seen hands-on in the client's shell: Claude Code sets `CLAUDECODE=1` (verified in the desktop Code tab; it also sets `AI_AGENT=claude-code_<version>_agent`). Codex and Cursor are checked in stage 2; until a variable is confirmed, `agent` is omitted.

## 3. Hands-on check (stage 0)

The probe skill `kb-hello` was placed in `~/.claude/skills/kb-hello/` and `~/.agents/skills/kb-hello/`. It asks the agent to report the client, the file path, `metadata.version`, the output of `kb --version`, and whether it sees duplicates.

| Check | Claude Code | Codex (ChatGPT app) |
|---|---|---|
| Skill found and invoked by hand | yes, `/kb-hello` in the desktop Code tab; arguments passed through | yes, from `~/.agents/skills/kb-hello/` |
| `metadata.version` readable | only by reading the file: the client injects the body without frontmatter, the agent read `SKILL.md` itself and got `"0.0.0"` | yes, `"0.0.0"` |
| Extra frontmatter (`metadata`) tolerated | yes | yes |
| Shell call works | yes (`/bin/zsh`; `kb` not installed yet) | yes (`/bin/zsh`; `kb` not installed yet) |
| Duplicates seen | no: the copy in `~/.agents/skills/` is not loaded by Claude Code | no: the copy in `~/.claude/skills/` is not loaded by Codex |

Result: each of the two install directories is read by exactly one of the two clients, so Claude Code and Codex get one copy each. The probe copies were deleted after the check.

## 4. Portable `SKILL.md` v0

Every skill shipped by the package follows these rules, so one file works in all three clients:

```markdown
---
name: add-knowledge            # lowercase, digits, hyphens; equals the folder name
description: >-                # when to use the skill; drives automatic invocation
  ...
metadata:
  version: "0.3.0"             # skill rules version
  package: ms-kb
---
```

- Only `name`, `description` and `metadata` in frontmatter. No client-specific fields (`allowed-tools`, `paths`, `context`, `icon`, …) and no Claude Code `` !`command` `` preprocessing.
- The body is plain Markdown instructions. Client-specific features (subagents, hooks) are optional and the skill works without them (design §9.1).
- The skill finds the vault only by calling `kb` (for example `kb where`, `kb search`), never from the current working folder or by reading the configuration file.
- Supporting files go in `references/` and are linked by relative path.

## 5. Document history

- **0.1 — 2026-10-09:** first version, roadmap stage 0.
- **0.2 — 2026-10-09:** roadmap stage 2: environment variables for the `agent` provenance field (§2.6).
