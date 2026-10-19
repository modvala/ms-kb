---
title: "Personal Knowledge System — Client Skills and Instructions v0"
document_version: "0.6"
created: "2026-10-09"
language: en
status: approved_for_mvp
design_ref: "personal-knowledge-design-v2.md"
design_version: "2.2"
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
   - **Implemented in v0.4.0 (stage 3).** `kb setup` and `kb install-skills` write the block together with the skills (`--no-instructions` skips it, `--dry-run` shows it); the begin marker carries the package version. The block is appended to existing content, replaced in place on update and removed when a client is disabled; text outside the markers is never changed. The written files are recorded under `[instructions]` in `installed.toml`. `kb install-skills --print-instruction` prints the Cursor text again. `kb doctor` reports a missing or outdated block and warns when `$CODEX_HOME/AGENTS.override.md` exists, because Codex reads it instead of `AGENTS.md`.
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

## 4. Hands-on checks

### 4.1. Stage 2: `add-knowledge`

`add-knowledge` 0.3.0 was installed with `kb setup` and run on a real learning conversation.

| Check | Claude Code | Codex | Cursor |
|---|---|---|---|
| `/add-knowledge` found and invoked | yes (desktop Code tab, 2026-10-10) | pending | pending (not installed) |
| First run: session + concepts created, no plan shown | yes: 1 session, 2 concepts, profile extended | pending | pending |
| Repeat run on the same topic: plan shown, existing concepts extended, no duplicates | yes: plan confirmed, 2 concepts extended, 1 new session and 1 new concept | pending | pending |
| `agent` in provenance | `claude-code` (from `CLAUDECODE=1`) | pending | pending |
| Skill sees duplicates | no | pending | pending |

Codex and Cursor are checked later, together with the other skills, in roadmap stage 7.

Found and fixed during the check: `kb validate` took paths relative to the current folder instead of the vault, and checked `learning_profile.md` as a note.

### 4.2. Stage 3: `kb-recall` and the global instruction

`kb-recall` 0.4.0 and the global instruction installed with `kb install-skills`, run against the vault from §4.1 in a new conversation in an unrelated repository (Claude Code desktop Code tab, 2026-10-10).

| Check | Claude Code | Codex | Cursor |
|---|---|---|---|
| Global instruction block in place, other content untouched | yes: created `~/.claude/CLAUDE.md` (no file before); `kb doctor` ok | pending | pasted by hand: pending |
| "Let's continue studying <saved topic>": `kb-recall` triggers, reads the profile and a few notes, cites conclusions and open questions with paths | yes: the request was in Russian and the skill triggered on it unprompted; 3 `kb` calls, profile + 2 sessions + 2 concepts; assumptions kept marked, its own new explanation labelled as not from the notes | pending | pending |
| A simple question ("what is 15 × 18?") runs no `kb` command | yes | pending | pending |
| An unsaved topic: says nothing was found, invents no history | yes (forced `/kb-recall` on an unrelated question) | pending | pending |
| `kb` unavailable: says so and answers from the conversation only | not checked; moved to stage 7 | pending | pending |

Codex and Cursor are checked in roadmap stage 7.

### 4.3. Stage 4: history, off-machine copy and updates

Run on the real vault `~/Knowledge/main` (Claude Code desktop Code tab, 2026-10-11). The vault had 6 notes and no repository; the remote is a private, empty GitHub repository dedicated to it, reached over HTTPS through the `gh` credential helper.

| Check | Result |
|---|---|
| `kb init` on an existing vault | yes: repository and `.gitignore` created, one `kb: init vault` commit with all notes and templates; with no `user.email`, the author fell back to `kb <kb@localhost>` (a repository-local identity was set afterwards) |
| `kb setup --remote … --schedule` | yes: `[kbs.main.sync]` written, `origin` set, LaunchAgent loaded; its `RunAtLoad` run pushed `main` within seconds (exit code 0) |
| `add-knowledge` in Claude Code commits with provenance | yes: `kb: create <session>`, `kb: extend <concept>`, `kb: extend learning_profile.md`, with `Kb-Skill: add-knowledge` and `Kb-Agent: claude-code`; the profile commit had no `Kb-Skill` (fixed: the skill now passes `--skill` for the profile) |
| An edit outside `kb` | yes: committed separately as `external: 1 file changed outside kb` and pushed by the hourly run at the top of the hour |
| A note deleted by hand | yes: `kb doctor` reported the deletion and, separately, the three links that stopped resolving; `kb restore` brought it back and `kb doctor` was clean again |
| Recovery from the remote | yes: `git clone` of the remote matched the vault; only empty folders (which Git does not keep, `kb init` recreates them) and `.DS_Store` differed |
| `kb update` after a version bump | yes: 0.4.0 → 0.5.0, skills in `~/.claude/skills` and `~/.agents/skills`, the global instruction and the LaunchAgent updated; `kb doctor` shows 0.5.0 everywhere |

Found and fixed during the check: `kb doctor` printed `kb restore concepts/Global Interpreter Lock.md` without quotes, so the suggested command failed in a shell; paths in hints are now shell-quoted.

## 5. Portable `SKILL.md` v0

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

## 6. Document history

- **0.1 — 2026-10-09:** first version, roadmap stage 0.
- **0.2 — 2026-10-09:** roadmap stage 2: environment variables for the `agent` provenance field (§2.6); hands-on results of `add-knowledge` (§4).
- **0.3 — 2026-10-10:** roadmap stage 3: the global instruction implemented (§2.4); the hands-on check of `kb-recall` (§4.2).
- **0.4 — 2026-10-11:** roadmap stage 4: the hands-on check of history, `kb sync`, `kb restore` and `kb update` on the real vault (§4.3).
- **0.5 — 2026-10-12:** the hands-on checks in Codex and Cursor move to roadmap stage 6 (stabilization), after the new stage 5 "Topic pages" ([roadmap v2.0](personal-knowledge-roadmap-v2.md)); design reference updated to [design v2](personal-knowledge-design-v2.md).
- **0.6 — 2026-10-19:** the hands-on checks in Codex and Cursor move to roadmap stage 7 (stabilization), after the new stage 6 "Sources for later" ([roadmap v2.2](personal-knowledge-roadmap-v2.md)).
