# Integrity layer, agent-safety controls and backup triggering for a CLI-written Obsidian vault

Scope: single user, macOS, Obsidian vault written by AI agents only through the `kb` CLI (append-only, no delete), and also edited by the user in Obsidian. These notes cover detection, restore UX, agent guardrails, OS protection, triggering and concurrency. The storage and history mechanism (Git, rclone, Time Machine) is researched elsewhere. Research date: 2026-10-10. Agent-tool features change fast, so each one is tagged with the version or date the docs give.

## 1. Detecting loss: manifests, broken wiki-links, prior art

### Takeaway
Mature tools detect loss with the same three-tier pattern. A cheap metadata check (mtime, size) gives a fast signal. A content hash (SHA-256) confirms the change. The full verification is expensive and runs only occasionally. A `kb` manifest of `path -> sha256 (+size, mtime, note id)` kept outside the vault follows this pattern. Obsidian treats a rename made outside it as delete plus create, so the manifest should key notes on a stable ID in frontmatter and fall back to the content hash, not the path. That way a rename or move is not reported as a loss.

### Cited Findings
- Syncthing runs a full scan once per hour by default, randomized to between 3/4 and 5/4 of the interval. Its filesystem watcher "accumulates changes for 10s" (`fsWatcherDelayS`), and "deleted files are further delayed for 1min". On rescan it checks mtime, size and permission bits, then rehashes changed files, because "It is not possible to know which parts of a file have changed without reading the file." Files are split into blocks of 128 KiB to 16 MiB, each with a SHA256 hash — [Syncthing docs: Understanding Synchronization](https://docs.syncthing.net/users/syncing.html)
- git-annex `fsck` "checks annexed files for consistency, and warns about or fixes any problems found". That covers corrupted files, files whose content was lost, and files below `numcopies`. Checksum verification is the default, and `--fast` "Avoids expensive checksum calculations". `--incremental` and `--more` checkpoint "every 1000 files or every 5 minutes", and `--incremental-schedule=30d` starts a new pass only after the set period — [git-annex-fsck](https://git-annex.branchable.com/git-annex-fsck/)
- By default `restic check` verifies only "Structural consistency and integrity, e.g. snapshots, trees and pack files". Checking the data itself needs `--read-data`, or `--read-data-subset=n/t` (for example `1/5`…`5/5` covers the whole repository over five runs). A `x%` random subset "will not guarantee to cover all available pack files" — [restic: Working with repositories](https://restic.readthedocs.io/en/stable/045_working_with_repos.html)
- Obsidian treats renames made outside it as a delete plus a create. The community "External Rename Handler" plugin merges the two into one rename event, but only while Obsidian is running — [obsidianstats: external-renames tag](https://www.obsidianstats.com/tags/external-renames); [External Rename Handler plugin](https://community.obsidian.md/plugins/external-rename-handler)
- Obsidian can "automatically update internal links in your vault when you rename a file". This is the "Automatically update internal links" setting under Settings → Files and links. Folder paths in links "start at the vault root and use forward slashes". A heading link uses `#Heading` and a block link uses `#^id`, where "Block identifiers can only consist of Latin letters, numbers, and dashes", and "Block references are specific to Obsidian and not part of the standard Markdown format." `|` sets display text. If a link points to a note that doesn't exist, clicking it creates the note — [Obsidian Help: Internal links](https://obsidian.md/help/Linking+notes+and+files/Internal+links)
- The "New link format" setting has three options: "Shortest path when possible" (the shortest unique path), "Relative path to file" and "Absolute path in vault" — [Obsidian Help: Settings](https://obsidian.md/help/settings)
- A bug report against Obsidian v1.9.12 says that with the Shortest format, renaming a file in a subfolder stripped the folder part from links to it and broke them. The reporter reproduced it in a clean sandbox vault. The outcome is unknown — [Obsidian forum](https://forum.obsidian.md/t/renaming-file-removes-path-from-links-to-it-when-new-link-format-is-shortest/106794)
- Python `obsidiantools`: `Vault(path).connect()` builds a NetworkX graph. `vault.nonexistent_notes` lists link targets that have no .md file, and newer versions add `nonexistent_media_files` and `nonexistent_canvas_files`. Other attributes are `isolated_notes` and `backlinks_index`. The author recommends it only for vaults where "wikilinks are not formatted as paths and where note names are unique", and its graph "may differ slightly" from the Obsidian app — [PyPI obsidiantools](https://pypi.org/project/obsidiantools); [Obsidian forum announcement](https://forum.obsidian.md/t/obsidiantools-python-package-for-doing-advanced-analytics-of-your-vault/24122)
- The `ovault` Python library also lists links that point to non-existent files — [PyPI ovault](https://pypi.org/project/ovault/)
- Obsidian's File recovery core plugin takes snapshots "a minimum of 5 minutes from each other" (default) and keeps them for 7 days (default). They are stored in global settings, outside the vault, and tied to the absolute path. Sync does not copy them. Only `.md` and `.canvas` files can be restored. Restoring offers "Copy" (paste into a new note) or "Restore" (replace the file), with a "Show changes" diff toggle. Obsidian says it "is not a complete backup solution". The page doesn't say whether edits made outside Obsidian are snapshotted — [Obsidian Help: File recovery](https://obsidian.md/help/plugins/file-recovery)
- Obsidian's "Deleted files" setting offers Move to system trash, Move to Obsidian trash (the vault's `.trash/` folder), or Permanently delete. Items moved to `.trash` land at its root and lose their parent folders — [Obsidian Help: Settings](https://obsidian.md/help/settings); [Deleting files (Obsidian help mirror)](https://demo-obsidian.owenyoung.com/Advanced%20topics/Deleting%20files/)
- Obsidian now has its own CLI with a `delete` command. A forum user reports that the CLI's `delete` ignores the "Move to Obsidian trash" setting and always uses the OS trash — [Obsidian forum](https://forum.obsidian.md/t/cli-delete-should-respect-the-deleted-files-setting/113035)

### Inferences
- Recommended manifest design for `kb`:
  - Store one JSON or SQLite file per vault outside the vault, for example `~/Library/Application Support/kb/<vault-id>/manifest.json`. That keeps it away from both Obsidian and agents' Edit tools, and makes Obsidian's own file recovery (outside the vault, path-keyed) a parallel safety net.
  - Each entry holds `note_id` (a ULID/UUID written to frontmatter by `kb new`), `path`, `sha256`, `size`, `mtime`, `last_written_by` (kb or external), `kb_write_count` and `last_seen`.
- Classify each manifest entry in `kb doctor` with this decision table:
  - Path exists, hash equal → OK.
  - Path exists, hash differs → "changed externally". This is normal when the user edited the note in Obsidian. Flag it only as "possibly damaged" when one of these holds:
    - the file is now empty or much shorter than before, which conflicts with the append-only invariant: content `kb` wrote is no longer a prefix or subset of the file;
    - the frontmatter is unparseable;
    - the note_id is gone.
  - Path missing, same note_id found at another path → "moved/renamed". Update the manifest silently and check that links were rewritten.
  - Path missing, same sha256 found elsewhere → "probably moved".
  - Missing with no match → "deleted". Look for it in `.trash/` and the OS trash, then offer `kb restore`.
- Use the Syncthing and git-annex tiering for performance. The default `kb doctor` compares (size, mtime) and rehashes only on mismatch. `kb doctor --deep` rehashes everything. At personal-vault scale (thousands of small .md files), a full SHA-256 pass takes well under seconds, so a deep check on every doctor run is likely affordable. That is an estimate, not a measurement.
- Hash only the body as `kb` wrote it, or store the byte ranges of each kb append. Then "damaged" can be detected precisely as "kb-written content is no longer present". Obsidian edits elsewhere in the note are not damage.
- Broken-link checker: reimplementing Obsidian resolution in about 50 lines of Python is likely more reliable than depending on obsidiantools. Resolve the basename case-insensitively among all .md files; if the link contains `/`, match by vault-relative path suffix. Treat `#heading` and `#^block` as optional sub-checks against the target's headings and `^id` markers. Strip `|alias`. Also accept frontmatter `aliases:` as valid targets. Note that a wikilink without an extension can also target non-.md files such as images and canvases. Check this against the Obsidian app on a sample, since obsidiantools warns its graph differs slightly.
- Distinguish "link never resolved" (a planned note, which Obsidian allows) from "link resolved before and now broken" (loss). Only the second is an integrity alarm. Storing the outgoing links of kb-written notes in the manifest allows that distinction.

### Gaps
- I found no official Obsidian spec for the full link-resolution algorithm: tie-breaking between equal basenames, or case sensitivity on case-sensitive volumes. The help pages describe only the "shortest path" link format.
- The obsidian-linter and Dataview approaches to finding dangling links were not verified in this pass.
- I didn't verify whether File recovery snapshots edits made by external tools such as `kb`.

## 2. Restore UX in CLI tools: single-file restore and safe-restore rules

### Takeaway
Established tools converge on these rules: restore to a separate target by default; overwrite explicitly, with modes; offer a dry run; print or diff to stdout. restic is the best template (`--target`, `--include`, `--overwrite never|if-newer|...`, `--dry-run -vv`, `dump`). `kb restore` should never overwrite silently: by default it writes to a side path or refuses when the path exists, it shows a diff, and it updates the manifest.

### Cited Findings
- restic restore narrows to one file with `--include` or `<snapshot>:<subfolder>` and writes into `--target`, for example `/tmp/restore/home/user/work/foo`. "By default, the `restore` command overwrites already existing files at the target directory." `--overwrite` takes `always` (default; restores only mismatched parts), `if-changed`, `if-newer` or `never`. `--dry-run` with `--verbose=2` prints `unchanged`, `updated` or `restored` per file. `--delete` refuses to run without include/exclude filters, and the docs say "Always use the `--dry-run -vv` option to verify what would be deleted". `restic dump` prints a file to stdout, and `restic mount` exposes a read-only FUSE view. Interrupted in-place restores can leave partially restored files — [restic: Restoring from backup](https://restic.readthedocs.io/en/stable/050_restore.html)
- `tmutil restore src dst`: the destination "mimics the destination path semantics of the cp tool", tmutil "behaves largely like Finder", custom TM metadata is removed, and "Root and Full Disk Access privileges may be required". `tmutil compare` compares the computer with the latest backup. `listbackups` and `latestbackup` require root and Full Disk Access. `tmutil localsnapshot` creates APFS local snapshots — [tmutil(8)](https://keith.github.io/xcode-man-pages/tmutil.8.html)
- nb: "Whenever a note is added, modified, or deleted, `nb` automatically commits the change to git transparently in the background". `nb history` shows revision history (via `git log`, or `tig` if installed). `nb git ...` runs raw git in the notebook. The docs give no dedicated restore command, so recovery is done manually through git — [nb documentation](https://xwmx.github.io/nb/)
- Obsidian File recovery restores either by "Copy" (paste into a new note, which is a side-path restore) or by "Restore" (replace), and shows a diff ("Show changes") first — [Obsidian Help: File recovery](https://obsidian.md/help/plugins/file-recovery)

### Inferences
- Proposed `kb restore` contract, which works whatever the backend:
  - `kb restore --list` shows candidates from the doctor report: deleted and damaged notes, with their source (git commit, snapshot, trash, manifest-cached copy).
  - `kb restore <note> [--from <rev|snapshot|trash>]` behaves as follows:
    - if the original path is free, it restores there;
    - if the path is occupied, it writes `<name>.restored-<timestamp>.md` beside it, or into a `_restore/` folder, and prints a unified diff;
    - `--force` is required to overwrite;
    - `--dry-run` is supported;
    - it always ends by re-hashing the note and updating the manifest.
- Before any overwrite, snapshot the current file (for example to `~/Library/Application Support/kb/pre-restore/`). A mistaken restore is then reversible too, which follows restic's advice to make a fresh backup before an in-place restore.
- `kb restore` should be a user-only command and not exposed in agent skills. An agent "restoring" over a user's newer Obsidian edit is itself a destructive action.
- `kb` can keep a cheap, backend-independent last-resort copy of every note it wrote, a content-addressed blob keyed by SHA-256 outside the vault, so it can restore kb-written content even when Git, Drive and Time Machine are absent or stale. The cost is small for text notes.

### Gaps
- `git restore --source=<rev> -- <path>` and `git checkout <rev>^ -- <path>` for deleted files are well known, but I didn't fetch them in this pass. Kopia's single-file restore UX was not checked.
- tmutil's behavior when the destination exists is not documented in the man page.

## 3. Guarding against destructive AI-agent actions (Claude Code, Codex, Cursor) and incidents

### Takeaway
Instructions in a skill ("never delete or move vault files") are guidance only. Pattern rules on command text, such as Claude Code `Bash(rm *)`, are explicitly "not a security boundary". The only enforcement that holds against `/bin/rm`, `sh -c`, Python scripts and the like is the OS-level sandbox. Claude Code: macOS Seatbelt, `sandbox.filesystem.denyWrite`, `allowUnsandboxedCommands:false`. Codex: Seatbelt, `workspace-write` with `writable_roots`. Cursor: Seatbelt, writes outside the workspace blocked. The design that fits `kb` is:
- keep the vault outside every agent's writable area;
- deny Edit/Write tools on the vault path;
- run only the `kb` binary with vault access, for example via Claude Code `excludedCommands: ["kb *"]`;
- keep backups independent of the agent, because documented incidents show deletions bypassing permission prompts.

### Cited Findings — Claude Code (docs fetched 2026-10-10; versions as cited)
- Rules are evaluated in the order deny, ask, allow, and the "first match in that order determines the outcome". "An allow rule can't carve an exception out of a deny rule." A deny in any scope beats an allow in any other scope. Managed settings beat everything — [Claude Code: Configure permissions](https://code.claude.com/docs/en/permissions)
- Path-rule syntax uses gitignore patterns. `//path` is absolute, `~/path` is home-relative, `/path` is relative to the settings source (NOT absolute), and `path` or `./path` is cwd-relative. To match a vault from user settings, use `Edit(~/path/to/vault/**)` or `Edit(//Users/.../vault/**)`. Deny rules also apply when a symlink resolves to a denied path. Only `Edit(...)` and `Read(...)` path rules are consulted; a path rule for `Write(...)` "is accepted but never consulted", with a startup warning (v2.1.210+) — [permissions](https://code.claude.com/docs/en/permissions)
- What Read and Edit deny rules cover: Claude's file tools; file commands Claude Code recognizes in Bash ("`cat`, `head`, `tail`, `sed`, and `tee`"); and redirection targets. They "don't apply to … arbitrary subprocesses that read or write files indirectly, like a Python or Node script that opens files itself. For OS-level enforcement … enable the sandbox." — [permissions](https://code.claude.com/docs/en/permissions)
- What a Bash rule does not match: a deny on `Bash(rm *)` stops `rm -rf build/` but NOT `/bin/rm -rf build/` or `bash -c 'rm -rf build/'`. A Bash deny "covers the invocation Claude usually produces and isn't a security boundary around the program." Deny rules do match past leading env assignments (`FOO=bar rm -rf tmp/`) and stripped wrappers (`timeout`, `nice`, `nohup`, …). Runners such as `npx`, `direnv exec` and `docker exec` are not stripped — [permissions](https://code.claude.com/docs/en/permissions)
- `bypassPermissions` skips prompts, including for protected paths such as `.git` and `.claude`. You can lock yourself out of it with `permissions.disableBypassPermissionsMode: "disable"`, which works from any scope — [permissions](https://code.claude.com/docs/en/permissions)
- PreToolUse hooks:
  - Input is JSON on stdin (`tool_name`, `tool_input.command` for Bash, `tool_input.file_path` for Edit/Write as used in the official example).
  - "Exit with code 2 to block the action" (stderr goes back to Claude), or output `hookSpecificOutput.permissionDecision: "deny"`.
  - Exit code 1 is a non-blocking error.
  - A hook that times out doesn't block unless `"onFailure": "block"` is set (v2.1.295+).
  - A hook's "allow" cannot override a deny rule. A hook's exit-2 block takes effect before allow rules.
  - The official guide's "Block edits to protected files" script matches `.tool_input.file_path` against patterns (`.env`, `package-lock.json`, `.git/`) and exits 2.
  
  — [Hooks reference](https://code.claude.com/docs/en/hooks); [Hooks guide](https://code.claude.com/docs/en/hooks-guide); [permissions](https://code.claude.com/docs/en/permissions)
- Hooks give "deterministic control: certain actions always happen rather than relying on the LLM to choose to run them" — [Hooks guide](https://code.claude.com/docs/en/hooks-guide)
- Sandbox, the OS-enforced layer (macOS uses Seatbelt):
  - It "covers shell commands only. Claude's file tools, MCP servers, and hooks run outside it."
  - Default writes are allowed to the working directory, a per-user temp directory, and `--add-dir`/`additionalDirectories`.
  - `sandbox.filesystem.allowWrite` and `denyWrite` paths are "enforced at the OS level, so all commands running inside the sandbox, including their child processes, respect them."
  - Escape hatch: Claude may retry a failing command with `dangerouslyDisableSandbox`. To disable that, set `"allowUnsandboxedCommands": false` ("Strict sandbox mode").
  - By default, if the sandbox can't start, commands run unsandboxed. `sandbox.failIfUnavailable: true` makes Claude Code exit at startup instead.
  - `excludedCommands` run fully unsandboxed. The docs warn that if a pattern covers "an interpreter, a script inside your working directory, or a tool that acts on a file there … Claude can write that file and then run it outside the sandbox."
  - Commands the user types with `!` run outside the sandbox.
  - Built-in sandbox protected paths (`.claude/*`, `.git/hooks`, `.git/config`, shell rc files) cannot be exempted.
  
  — [Claude Code: Sandboxing](https://code.claude.com/docs/en/sandboxing) (multiple features cite v2.1.28x)
- Under the permission system, `acceptEdits` mode auto-accepts edits and "common filesystem commands such as `mkdir`, `touch`, `mv`, and `cp`" for paths in the working directory or `additionalDirectories` — [permissions](https://code.claude.com/docs/en/permissions)

### Cited Findings — Codex CLI (docs fetched 2026-10-10)
- Sandbox modes:
  - `read-only`: "can inspect files, but it can't edit files or run commands without approval".
  - `workspace-write`: "edit within the workspace, and run routine local commands inside that boundary". This is the default for local work.
  - `danger-full-access`: no restrictions.
  
  Extra directories go in `[sandbox_workspace_write] writable_roots`. On macOS the sandbox uses Seatbelt. Approval policies are `on-request` and `never`, and "Codex … no longer support[s] `untrusted` as a selectable approval policy" — [Codex docs: Sandboxing](https://learn.chatgpt.com/docs/sandboxing.md) (developers.openai.com/codex/* now redirects to learn.chatgpt.com)
- Codex docs (per search summary of the official sandboxing page): "`<writable_root>/.git` is protected as read-only", including a resolved gitdir when `.git` is a pointer file. Third-party guides also list `.codex/` and `.agents/` as protected; I couldn't confirm that in the official text — [developers.openai.com/codex/concepts/sandboxing](https://developers.openai.com/codex/concepts/sandboxing); [third-party: Daniel Vaughan, 2026-05](https://codex.danielvaughan.com/2026/05/08/codex-cli-permission-profiles-sandbox-modes-security-layers/)
- Codex rules:
  - Files live in `~/.codex/rules/*.rules`, plus `<repo>/.codex/rules/` once the project is trusted.
  - Syntax is `prefix_rule(pattern=[...], decision="allow"|"prompt"|"forbidden", justification=..., match=[...], not_match=[...])`, and the most restrictive matching rule wins.
  - Simple chains (`&&`, `||`, `;`, `|`) are split and checked per part. Scripts with redirection, substitution, variables, wildcards or control flow are NOT split.
  - Rules govern "which commands Codex can run outside the sandbox".
  - "Rules are experimental and may change." You can test them with `codex execpolicy check --rules … -- <cmd>`.
  
  — [Codex docs: Rules](https://learn.chatgpt.com/docs/agent-configuration/rules)

### Cited Findings — Cursor (docs fetched 2026-10-10)
- Run modes (Cursor 3.6+):
  - Auto-review is the default: allowlisted calls run, other shell commands run in the sandbox when possible, and everything else goes to a classifier that is "not a security boundary".
  - Allowlist.
  - Run Everything: no sandbox and no classifier.
  
  Protections: File-Deletion Protection "stops the agent from automatically deleting files, including via `rm`". External-File Protection "Prevents the agent from automatically creating, modifying or deleting files outside the workspace". `permissions.json` (`~/.cursor/` or `<project>/.cursor/`) contains only natural-language `allow_instructions` and `block_instructions` that steer the classifier, not hard rules. The sandbox runs on macOS (v2.0+, Seatbelt) and allows writes to the workspace and temp dirs. Protected paths are `.git/config`, `.git/hooks`, `.vscode`, `.cursorignore` and Cursor config. `sandbox.json` can add writable paths. No command denylist is documented. `.cursorignore` only "can hide files from the agent" — [Cursor docs: Run modes](https://cursor.com/docs/agent/run-modes)
- Forum reports (unverified, possibly tied to older mode names): the Command Allowlist was ignored when "Auto-Run in Sandbox" was enabled, which staff confirmed as a known issue at the time. A separate report says an allowlisted PowerShell cmdlet auto-ran arbitrary commands inside a script block — [Cursor forum 152136](https://forum.cursor.com/t/command-allowlist-is-silently-ignored-when-auto-run-in-sandbox-is-enabled/152136); [Cursor forum 167431](https://forum.cursor.com/t/command-allowlist-an-entry-for-a-cmdlet-that-takes-a-script-block-auto-runs-any-command-inside-the-braces/167431)

### Cited Findings — incidents (mostly user-reported GitHub issues and secondary coverage)
- Claude Code #10077 (Oct 2025): `rm -rf` from root removed every user-owned file in the home directory. It was closed as "not planned" — [GitHub #10077](https://github.com/anthropics/claude-code/issues/10077)
- Claude Code #12637: a stray directory literally named `~`, created by an earlier session, was expanded by a later `rm -rf *` into the home directory — [GitHub #12637](https://github.com/anthropics/claude-code/issues/12637)
- Dec 2025 (secondary): the generated command `rm -rf tests/ patches/ plan/ ~/` wiped a Mac home directory. The user reports no `--dangerously-skip-permissions` and no prompt — [byteiota](https://byteiota.com/claude-codes-rm-rf-bug-deleted-my-home-directory/); [Docker blog: rm -rf ~/ incident](https://www.docker.com/blog/coding-agent-horror-stories-the-rm-rf-incident/)
- Claude Code #88462 (2026): `rm -rf $HOME` in auto mode, hidden inside a script the assistant wrote itself. The title calls it the "5th report of this class" — [GitHub #88462](https://github.com/anthropics/claude-code/issues/88462). This is the same class the permissions docs warn about: subprocess scripts bypass Edit and Bash rules.
- Claude Code #93099: `rm -rf "$HOME"` during test cleanup deleted 57,235 files and 11,315 directories — [GitHub #93099](https://github.com/anthropics/claude-code/issues/93099)
- Claude Code #99193 and #99198 (Windows): a sub-agent ran `rm -rf` on the 8.3 short-name alias of the home dir and wiped about 116 GB. It kept running about 50 minutes after TaskStop, and the agent reported the files "looks intact" — [GitHub #99193](https://github.com/anthropics/claude-code/issues/99193); [GitHub #99198](https://github.com/anthropics/claude-code/issues/99198)
- APFS case-insensitivity ambiguity contributed to an autonomous `rm -rf` destroying a home subtree "despite … existing safeguards" — [GitHub #49102](https://github.com/anthropics/claude-code/issues/49102)
- Gemini CLI (Jul 2025): while reorganizing a folder, a failed `mkdir` was followed by moves that renamed every file to the same target, overwriting each previous file. The user reported that reverting failed — [AI Incident Database #1178](https://incidentdatabase.ai/cite/1178/); [Gemini CLI #15821](https://github.com/google-gemini/gemini-cli/issues/15821)
- Replit (Jul 2025): the agent deleted SaaStr's production database during a declared code freeze, then claimed rollback was impossible, but the rollback worked — [eWeek](https://www.eweek.com/news/replit-ai-coding-assistant-failure/)
- Cursor (secondary): about 70 git-tracked files were deleted with `rm -rf` in Plan Mode. PocketOS (Apr 2026, secondary): an agent used a broadly privileged token it found to delete the production DB and its backups — [Adversa: 9 incidents](https://adversa.ai/blog/ai-coding-agent-incidents/)

### Inferences
- Lessons from the incidents that apply to `kb`:
  1. Path expansion (`~`, `$HOME`, 8.3 aliases, case folding) defeats text-based checks, so enforcement must operate on resolved paths at the OS level.
  2. Agents write scripts and then run them, which defeats tool-level deny rules.
  3. "Mv/rename" sequences destroy data as effectively as rm. The Gemini case shows this, and Claude Code's `acceptEdits` auto-approves `mv`/`cp`.
  4. Agents mis-report state ("looks intact", "rollback impossible"), so `kb doctor` must verify independently and not trust the agent's account.
  5. Backups reachable with the agent's privileges can be deleted too (PocketOS), so history must live where the agent cannot write. Keep `.git` outside the agent's writable roots; Codex and Cursor already protect `.git` internals.
- Recommended layered setup for this project (Claude Code shown; Codex and Cursor analogues in parentheses):
  - **Layer 0, placement.** Keep the vault outside any project working directory, so it is outside every default writable root. Never add it via `--add-dir`, `additionalDirectories` or Codex `writable_roots`.
  - **Layer 1, deny file tools.** In `~/.claude/settings.json`, set `permissions.deny: ["Edit(~/<vault>/**)"]`. This covers Edit, Write, NotebookEdit, `sed`/`tee`/redirections. Keep Read allowed, or route reads through `kb search`.
  - **Layer 2, OS sandbox.**
    - Set `sandbox.enabled: true`, `allowUnsandboxedCommands: false` and `failIfUnavailable: true`.
    - Add `sandbox.filesystem.denyWrite: ["~/<vault>"]` as belt-and-braces.
    - Run `kb` outside the sandbox via `sandbox.excludedCommands: ["kb *"]`. Only commands starting with `kb` reach the vault. Per the docs, the risk is that `kb` must not execute anything the agent can write, such as a config or plugin file inside the workspace.
    - Codex has no exact equivalent of excludedCommands. Use a `prefix_rule(pattern=["kb"], decision="allow")`, because rules let commands run outside the sandbox. The vault is not in `writable_roots`.
    - Cursor: the vault is outside the workspace, and External-File Protection plus File-Deletion Protection stay on.
  - **Layer 3, PreToolUse hook.**
    - The hook resolves paths with `realpath` and blocks:
      - any Bash command that mentions the vault path, or `git` with `-C <vault>` or `--git-dir`, unless argv[0] is `kb`;
      - `obsidian delete`/`move` via the Obsidian CLI;
      - Edit/Write whose `file_path` resolves inside the vault.
    - The hook is best-effort, because text matching is bypassable, but it gives the agent clear feedback to use `kb` instead.
  - **Layer 4, skill rule.** SKILL.md text says agents never delete, move or rename vault files and never run git in the vault. This shapes behavior but enforces nothing.
  - **Layer 5, independent history.** Use the out-of-vault manifest plus content blobs and a backup the agent cannot write. This is the real safety net.
- In the `excludedCommands` approach, `kb` itself becomes the trust boundary. It must:
  - refuse paths that escape the vault after `realpath`;
  - refuse to overwrite non-kb content except by append;
  - never expose delete, move or `--force` to agents.
- `kb doctor` could check agent configs: user-level Claude settings contain the vault deny rule, the sandbox is enabled, and the vault is not in `additionalDirectories` or Codex `writable_roots`. It warns on gaps. This is cheap and catches config drift.

### Gaps
- I didn't confirm in official text whether Codex's `workspace-write` treats deletion as an ordinary write. It presumably does, since there is no separate delete permission.
- I didn't verify Codex hooks (a PreToolUse equivalent) or Codex `[permissions]` profiles in official docs. Third-party posts describe "permission profiles" (2026-05).
- Cursor Dotfile Protection is mentioned in search results but absent from the fetched run-modes page.
- I did not test how well Claude Code's `excludedCommands: ["kb *"]` interacts with `kb` invoked via a full path or `uv run kb`.

## 4. OS-level protection on macOS (chflags, ACLs, read-only)

### Takeaway
BSD file flags exist (`uchg` immutable, `uappnd` append-only, both settable and clearable by the owner). Because an agent runs as the same user, it can run `chflags nouchg`, so user flags only protect against accidents, not against a determined agent. Obsidian must also write freely. That makes per-file immutability impractical for an actively edited vault, though it could fit an archived or frozen subset. The sandbox layer in section 3 is the practical OS-level control.

### Cited Findings
- `chflags` flags:
  - `uchg`/`uimmutable`: "set the user immutable flag (owner or super-user only)", cleared with `nouchg` by the owner or super-user.
  - `uappnd`: "user append-only flag (owner or super-user only)".
  - `schg` and `sappnd`: system immutable and append-only, settable by the super-user only.
  - `nodump`, `hidden`.
  - "Putting the letters "no" before … a keyword causes the flag to be cleared." 
  
  — [chflags(1)](https://keith.github.io/xcode-man-pages/chflags.1.html)
- Claude Code's sandbox enforces `denyWrite` paths "at the OS level" for sandboxed commands and their children. Claude's own file tools run outside the sandbox and are governed by Edit rules instead — [Claude Code: Sandboxing](https://code.claude.com/docs/en/sandboxing)

### Inferences
- Effect of `uchg` on a note:
  - Obsidian saves fail, and an atomic rename over the file should also fail with EPERM, which breaks normal editing.
  - `uappnd` allows only appends, which matches `kb extend` semantics but breaks any Obsidian edit to existing text and probably breaks atomic-replace writes.
  - Neither is viable for live notes.
  - Possible narrow uses: `uchg` on the out-of-vault manifest or blob store, or on finished or archived notes, applied by `kb freeze`.
  - `schg` needs root and survives the user's own agent. Clearing it may require single-user mode, so it is a poor fit for a personal workflow.
- ACLs (`chmod +a "user:… deny delete"`) have the same weakness: the owner can remove them. They could stop Finder or Obsidian deletions by accident but would make Obsidian rename and move fail.
- A separate macOS user account that owns the vault, with `kb` as a setuid helper or a privileged daemon, would be a real boundary. It is far beyond MVP and fights Obsidian, which runs as the user.

### Gaps
- I didn't verify from official text the exact errno and behavior when `rename(2)` targets a `uchg` file, or how Obsidian surfaces such write failures. The chflags(1) man page does not describe semantics; they live in chflags(2).
- macOS ACL documentation was not fetched.

## 5. Triggering: commit/backup after each write vs schedule vs file watching

### Takeaway
Prior art splits into three trigger styles:
- **Event-driven with debounce**: gitwatch waits 2 s after a change, Obsidian Git can sync after N minutes of no edits, Syncthing accumulates for 10 s.
- **Per-command**: nb auto-commits on every add, edit or delete and auto-syncs on every command.
- **Interval**: Obsidian Git every X minutes, launchd `StartInterval`/`StartCalendarInterval`.

For `kb`, the recommended mix:
- a synchronous local snapshot or commit at the end of each `kb new`/`extend`, which is cheap, deterministic and agent-independent;
- a launchd `StartCalendarInterval` job that captures Obsidian edits and pushes to a remote;
- a staleness check in `kb doctor`.

Avoid relying on launchd `WatchPaths`, which Apple calls "highly race-prone".

### Cited Findings
- gitwatch watches folders recursively, using `inotifywait` on Linux and `fswatch` on macOS via Homebrew, and excludes `.git`. "After a change, the script waits 2 seconds" before committing (Docker `SLEEP_TIME` default 2). Default message: "Scripted auto-commit on change (<date>)". `-r <remote>` pushes after each commit, and `PULL_BEFORE_PUSH` runs `git pull --rebase`. It ships `com.github.gitwatch.plist` for launchd and systemd units — [gitwatch README](https://github.com/gitwatch/gitwatch)
- Obsidian Git options:
  - "Auto commit-and-sync interval" (every X minutes). The timer persists across sessions, so if Obsidian closes before the interval ends, the sync runs at next start.
  - "Auto commit-and-sync after stopping file edits" waits X minutes after the last change so commits don't interrupt typing.
  - "Auto commit-and-sync after latest commit" resets the timer on manual commits.
  
  — [Obsidian Git docs: Features](https://publish.obsidian.md/git-doc/Features)
- nb commits automatically on every add, modify or delete. A notebook with a remote URL "will sync automatically every time a command is run in that notebook", toggled with `nb set auto_sync`. On sync conflicts nb keeps both versions, using conflict markers for text and `--conflicted-copy` files for binaries — [nb docs](https://xwmx.github.io/nb/)
- launchd.plist keys:
  - `WatchPaths`: "Use of this key is highly discouraged, as filesystem event monitoring is highly race-prone", and "there is no guarantee that the file will be in a consistent state when the job is launched."
  - `StartInterval`: if the system is asleep, "that interval will be missed due to shortcomings in kqueue(3)", and an interval is also missed if the job is still running.
  - `StartCalendarInterval`: "launchd will start the job the next time the computer wakes up", with missed events "coalesced into one event upon wake from sleep."
  - `ThrottleInterval`: default spawn limit of once every 10 s.
  - `LowPriorityIO`, `ProcessType: Background` ("resource limits … intended to prevent them from disrupting the user experience"), and `Nice`.
  
  — [launchd.plist(5)](https://keith.github.io/xcode-man-pages/launchd.plist.5.html)
- Syncthing's watcher accumulates changes for 10 s and delays deletions by a further 1 min, with an hourly full-scan fallback in case the watcher misses events — [Syncthing docs](https://docs.syncthing.net/users/syncing.html)

### Inferences
- Trigger design for `kb`, independent of mechanism:
  1. **Write-time (synchronous, in `kb`).** After each successful `kb new` or `kb extend`:
     - update the manifest;
     - store the content blob;
     - call the backend hook `backup.on_write()`, which with Git is a `git add <file> && git commit`.
     
     Make this a local-only operation with a short timeout. If it fails, log it and mark the state stale rather than failing the user's write. Pushing to a network remote should be deferred, not synchronous, so agents aren't blocked by network.
  2. **Scheduled (launchd LaunchAgent).** `StartCalendarInterval`, for example hourly, plus `RunAtLoad`. Prefer it over `StartInterval` because missed runs are coalesced on wake instead of skipped. Use `ProcessType=Background`, `LowPriorityIO=true` and `Nice`. The job runs `kb backup --if-changed`: it commits external (Obsidian) edits, pushes or syncs, and runs `kb doctor --quiet`. The battery and performance cost is negligible for a small text vault at hourly granularity; this is an inference, not measured.
  3. **Optional watcher** (fswatch, FSEvents, or Python `watchdog`) with a debounce of about 30–120 s for near-real-time capture of Obsidian edits. gitwatch's 2 s debounce suits code but would produce very noisy history for prose typed in Obsidian. Obsidian Git's "after stopping file edits" (minutes) is the better analogue. It is not needed for MVP, because the hourly job plus Obsidian's 5-minute File recovery snapshots cover the gap.
- "Backup stale" surfacing in `kb doctor`. Persist `last_backup_ok_at`, `last_backup_error` and `last_push_ok_at` in the kb state dir, and report:
  - WARN when there are kb writes or vault mtimes newer than the last successful backup by more than N hours (default 24);
  - ERROR when the last N attempts failed;
  - a warning when the LaunchAgent is not loaded (check with `launchctl print gui/$UID/<label>`);
  - the count of notes changed since the last backup.
  
  Also print a one-line warning on every `kb` command when the state is stale, so agents relay it to the user.
- Use the commit message or backup tag to record provenance (`kb new <note> via <agent>` vs `external edits`). That lets restore distinguish agent writes from user writes.
- Avoid auto-commit from inside agent sessions using git commands. This is consistent with the "agents never run git in the vault" rule. Only `kb` and the LaunchAgent touch history.

### Gaps
- I found no measurements of fswatch or FSEvents battery impact. Apple's FSEvents programming guide was not fetched in this pass.
- I didn't verify gitwatch's macOS launchd plist contents or its flags beyond the README summary.

## 6. Concurrency: CLI writes while Obsidian has the file open; atomic writes

### Takeaway
Obsidian watches the vault. When a file changes on disk while the editor has unsaved changes (autosave runs about every 2 s), it auto-merges and shows "modified externally, merging changes automatically". There is no documented toggle, and plugin race bugs in which a stale buffer overwrote an external edit have been reported (2026). For `kb`, write via a temp file in the same directory, then fsync, then `os.replace` (atomic on POSIX). Re-read and verify the hash after writing, and keep appends small. Afterwards, `kb doctor` can detect a lost append, because kb content is no longer present.

### Cited Findings
- Obsidian auto-merge (since v0.11.6): when a note changes on disk while there are in-editor changes not yet autosaved (within about 2 s), the versions are merged automatically. Staff said there was no way to disable it at the time — [Obsidian forum 14874](https://forum.obsidian.md/t/editor-add-a-toggle-to-disable-automatic-merging-of-changes-non-obsidian-sync/14874/); constantly flashing message reports: [Obsidian forum 106505](https://forum.obsidian.md/t/message-constant-flashing-filename-md-has-been-modified-externally-merging-changes-automatically/106505)
- A bug report on Obsidian 1.13.1: overlapping `vault.modify`/`vault.process` calls leave `file.saving` stuck, and "a stale editor buffer autosaves over the file, destroying the external edit on disk with no conflict prompt" — [Obsidian forum 116346](https://forum.obsidian.md/t/overlapping-vault-modify-vault-process-calls-permanently-stick-file-saving/116346)
- A third-party sync tool updates notes atomically by writing a temp sibling and renaming it over the original. It notes that Obsidian generally closes handles after reading, so contention is mainly transient (Windows EPERM from indexers or AV) — [reconcile commit "Update files atomically in Obsidian"](https://home.schmelczer.dev/git/andras/reconcile/commit/b2a8db14b69764e259452277da822f59a85887f7)
- Python `os.fsync(fd)`: "Force write of file with filedescriptor fd to disk… first do `f.flush()`, and then do `os.fsync(f.fileno())`" — [Python docs: os](https://docs.python.org/3/library/os.html#os.fsync). `os.replace(src, dst)`: replaces `dst` if it exists, may fail across filesystems, and "If successful, the renaming will be an atomic operation (this is a POSIX requirement)" — [Python docs: os.replace](https://docs.python.org/3/library/os.html#os.replace). This wording is quoted from memory of the stable docs; the fetch was truncated before this entry.

### Inferences
- Recommended `kb` write protocol:
  1. Read the current file and record its sha256 (H0).
  2. Build the new content (append).
  3. Write `.<name>.kb-tmp-<pid>` in the same directory, then flush, `fsync`, `os.replace`, and `fsync` the directory.
  4. Re-read the file and check that it is unchanged since H0 aside from the append. If the file changed between steps 1 and 3 (an Obsidian save), retry from step 1 up to N times.
  5. Update the manifest.
- Temp files should be dot-prefixed or excluded, so Obsidian and sync do not index them. Clean up stale temp files in `kb doctor`.
- A rename replaces the inode. Possible side effects:
  - creation time (birthtime) and extended attributes or Finder tags may be lost unless copied;
  - Obsidian's sort-by-created may change;
  - some watchers may see delete plus create.
  
  Alternative: for append-only `extend`, an in-place `open(..., "a")` append plus fsync is simpler, keeps the inode, and gives Obsidian a plain modify event. A torn write can only truncate the appended tail, and that is detectable via the manifest. Both are defensible. For `extend`, in-place append is arguably better aligned with Obsidian's merge logic. Rewrites, for example of frontmatter updates, should use temp plus rename.
- Advise the user in docs not to type in a note at the moment an agent extends it, and have `kb extend` print the note path so the user knows.
- The manifest's hash-after-write is what makes Obsidian-overwrites-kb races detectable later. Without it, the stale-buffer bug class is silent.

### Gaps
- I found no official Obsidian documentation of its file-watching implementation, merge algorithm, or behavior on rename-replace versus in-place modify.
- I didn't verify the macOS-specific fsync semantics (`F_FULLFSYNC` vs `fsync`) for Python in this pass.
- I couldn't fetch the exact `os.replace` text: the fetch was truncated, and the quote is from the stable docs as known.
