# A dedicated Git repository as change history and off-machine copy of an Obsidian vault (state as of 2026-10-10)

Scope: single user, macOS, vault at e.g. `~/Knowledge/main`, Python CLI `kb` (append-only, no delete) as the only writer for AI agents, the user may also edit in Obsidian. Question (a): make the vault root a local Git repo with `kb` auto-committing; (b): push it to a private remote. Time Machine is assumed as the second copy.

Method note: primary sources (docs.github.com, docs.gitlab.com, docs.codeberg.org, project READMEs) were fetched on 2026-10-10. Items marked "(background knowledge, not re-verified)" come from general Git knowledge and were not checked against a page in this session; treat them as well established but uncited.

## 1. Local Git as history: restoring deletions, commit-per-write, provenance, capturing outside edits

### Takeaway
A local repo at the vault root gives a full undo history with nothing to host. The workable pattern is: `kb` commits right after each write, and before each write it first commits any pending changes made outside the CLI as a separate commit. Prior art (`nb`) does exactly this, committing on every add, edit or delete. Edits made only in Obsidian need a second trigger: the Obsidian Git plugin's interval or idle timer, or a launchd job.

### Cited Findings
- Prior art for commit-per-write: `nb` says that "whenever a note is added, modified, or deleted, `nb` automatically commits the change to git transparently in the background." `nb history` uses `git log`, or `tig` when it is installed, to show history for a notebook, folder or item. Its conflict example labels commits `[nb] Commit`, so the message format is generic, not descriptive. — [nb docs](https://xwmx.github.io/nb/)
- Obsidian Git plugin automation (official docs). "Auto commit-and-sync interval" runs every X minutes, and the timer persists across sessions: if Obsidian closes before the interval ends, the run happens at the next start. "Auto commit-and-sync after stopping file edits" waits X minutes after the last change so it does not interrupt typing. "Auto commit-and-sync after latest commit" measures the timer from the most recent commit, including manual ones. The commit message date uses Moment.js formatting. — [Obsidian Git docs: Features](https://publish.obsidian.md/git-doc/Features)
- In the plugin, "Commit-and-sync" means stage, commit, pull and push. Pull or push can be switched off, leaving commit only, commit and pull, or commit and push. The older term "Backup" is marked "no longer in use." The docs also note that Git "is not a live syncing service." — [Obsidian Git docs: Start here](https://publish.obsidian.md/git-doc/Start+here)
- Other plugin features: a Source Control view (stage, unstage, commit, diff), a History view, a Diff view, line-level editor signs (desktop only), opt-in submodule support (desktop only), and an option to pull automatically on startup. — [Obsidian Git README](https://github.com/Vinzent03/obsidian-git)
- Practitioner report on commit frequency: one forum user went from backing up every 5 minutes to hourly, and was considering daily, because frequent commits filled the history with meaningless entries. The same thread restores an old state by finding the commit by time, downloading it as a zip and opening it as a new vault. — [Obsidian forum: Obsidian Git plugin thread](https://forum.obsidian.md/t/obsidian-git-plugin-for-automatic-vault-backup-with-git/7790/5)
- Restore commands (background knowledge, not re-verified; official reference pages linked):
  - Find deletions: `git log --diff-filter=D --name-only` ([git-log](https://git-scm.com/docs/git-log)).
  - Restore a deleted file: `git restore --source=<deleting-commit>^ -- <path>` ([git-restore](https://git-scm.com/docs/git-restore)).
  - See a file's history across renames: `git log --follow -- <path>`.

### Inferences
- Recommended `kb` commit flow:
  1. Before writing, run `git status --porcelain`. If anything is dirty, commit it first with `git add -A` and a message like `external: N files changed outside kb`. This keeps the user's Obsidian edits separate from agent writes, which is useful for blame and provenance.
  2. Write the note.
  3. Run `git add -- <exact paths>` and then `git commit`, with a structured message.
- Suggested message format: subject `kb: create|append <relative path>`, plus Git trailers in the body, for example `Kb-Agent: claude-code`, `Kb-Command: add-note`, `Kb-Version: 0.4.0`, `Kb-Session: <id>`. Trailers can be parsed with `git interpret-trailers` or `git log --format=%(trailers)` (background knowledge).
- Because `kb` has no delete command, every deletion in history comes from outside the CLI: Obsidian, Finder or an agent using raw file tools. `git log --diff-filter=D` therefore works as an audit of "who removed things outside the sanctioned path."
- To capture Obsidian-only sessions without the plugin, a user LaunchAgent (`~/Library/LaunchAgents/*.plist` with `StartInterval`, or `WatchPaths` on the vault) can run `kb snapshot` or `git add -A && git commit`. This is background knowledge about launchd and was not fetched. Commit only when the tree is dirty, to avoid empty commits.
- Use a vault-root `.gitignore` for `.obsidian/workspace*.json`, `.obsidian/cache`, `.trash/` (debatable) and `.DS_Store`. Workspace files change on every UI action and would add noise.

### Gaps
- I did not fetch the plugin's full list of commit-message placeholders (for example `{{date}}`, `{{numFiles}}`, `{{hostname}}`, `{{files}}`) or its exact default intervals. They are not on the Features page, so check the plugin's settings UI or source.
- I found no current (2026) release number or date for obsidian-git: the README fetch showed no releases section content.

## 2. Using Git from Python; git not installed; concurrency and `index.lock`

### Takeaway
Shelling out to the system `git` with `subprocess` is the simplest and most faithful option, and GitPython needs the `git` binary anyway. GitPython is officially in maintenance mode. The real risk is two writers, `kb` and the Obsidian Git plugin, colliding on `.git/index.lock`. The CLI should retry with a short back-off and never delete the lock automatically.

### Cited Findings
- GitPython: "This project is in maintenance mode", with "no feature development, unless these are contributed". It "needs the `git` executable to be installed on the system and available in your `PATH` for most operations." It is "not suited for long-running processes (like daemons) as it tends to leak system resources." — [GitPython README](https://github.com/gitpython-developers/GitPython)
- `index.lock` collisions with Obsidian Git are reported in practice. One user got `fatal: Unable to create '.../.git/index.lock': File exists`. A forum moderator advised first finding "which other program has acquired the lock" and making sure it has finished before deleting anything. — [Obsidian forum: plugin causing error in git](https://forum.obsidian.md/t/obsidian-git-plugin-causing-error-in-git/75527)
- Another report: Obsidian Git complained about `index.lock` even though no such file existed, and git worked fine in the terminal. The thread had no confirmed fix. — [Obsidian forum: index.lock bug](https://forum.obsidian.md/t/bug-obsidian-git-complaining-about-index-lock-even-when-file-index-lock-doesn-t-exist/110021)
- Do not confuse this with Obsidian's own IndexedDB/LevelDB `LOCK` file, which is unrelated to Git. — [Obsidian forum: IndexedDB backing store](https://forum.obsidian.md/t/internal-error-opening-backing-store-for-indexeddb-open/91070)

### Inferences
- Options compared (pygit2 and dulwich are described from background knowledge, not re-verified this session):
  - **subprocess + `git`**: no Python dependency, and it matches what the user runs by hand, including hooks such as a gitleaks pre-commit. It requires git on PATH. On macOS, `/usr/bin/git` is a shim that triggers the Command Line Tools install dialog if they are absent, so detect this with `xcode-select -p` or by trying `git --version`, and fail gracefully.
  - **pygit2** (libgit2 bindings): ships wheels with libgit2 bundled, so it works without system git. It does not run git hooks by default, and its config and credential handling differs from CLI git.
  - **dulwich** (pure Python): no native dependency. It is slower on large histories and has partial hook support.
- Recommended for `kb`:
  - Use subprocess git as the primary path. If git is missing, keep writing notes (Git must never block a write) and print a one-line warning such as "history disabled: git not found".
  - Make history opt-in or auto-detected: if the vault root contains `.git`, commit; otherwise do not.
- Concurrency:
  - On `index.lock` failure, retry about 5 times with jittered back-off over about 2–3 seconds.
  - If the lock is still present and older than N minutes with no `git` process running (`pgrep -x git`), report it to the user instead of deleting it.
  - Serialize `kb`'s own invocations, since several agents may write at once, with an advisory lock such as `fcntl.flock` on `.git/kb.lock`.
  - Stage only `kb`'s own paths for its commit. A broad `git add -A` racing with the plugin could mix the user's half-finished edits into an agent commit.
- If the Obsidian Git plugin is also installed, the simplest split is that the plugin only commits Obsidian edits (no pull or push in the MVP) and `kb` commits its own writes. Two auto-committers are fine as long as both retry on lock contention.

### Gaps
- I found no authoritative benchmark of pygit2 vs dulwich vs subprocess on vault-sized repos (thousands of small Markdown files).
- I did not verify the current pygit2 and dulwich release versions or wheel availability for macOS arm64 as of October 2026.

## 3. Private remotes: GitHub limits and protections, and alternatives

### Takeaway
GitHub Free private repos have generous size headroom for a Markdown vault (100 MiB per-file block, about 1 GB recommended repo size, 10 GiB LFS). However, **branch protection and rulesets on private repos need GitHub Pro (or Team/Enterprise)**, so on Free you cannot block force-push or branch deletion. GitLab Free does offer protected branches on private projects. Codeberg allows only about 100 MB of private content and is not meant for backups. A bare repo on another disk or NAS is the simplest remote that can refuse history rewrites.

### Cited Findings
- File and repo size on GitHub:
  - Git warns on files over 50 MiB, and "GitHub blocks files larger than 100 MiB."
  - Browser uploads are capped at 25 MiB.
  - Repositories should be "ideally less than 1 GB, and less than 5 GB is strongly recommended."
  - There is no published numeric hard repo limit, but GitHub Support may contact owners of repos that strain infrastructure.
  — [GitHub Docs: About large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
- Git LFS free quota (2026 docs): 10 GiB storage and 10 GiB bandwidth for GitHub Free and Pro; 250 GiB of each for Team and Enterprise Cloud. Pre-paid data packs "have been removed and replaced with metered billing." The fetched page gave no per-GiB price. — [GitHub Docs: Git LFS billing](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)
  - Conflict: an older practitioner post says the free LFS tier is capped at 2 GB ([ndumas blog](https://code.ndumas.com/ndumas/blog.ndumas.com/commit/c69bfa64e80658303d1fc6d6e28c563749182f77)). This reflects the pre-metered-billing era; the current docs say 10 GiB.
- Plan comparison: "Protected branches" appear under GitHub Pro's "Advanced tools and insights in private repositories" and are not listed for Free personal accounts. — [GitHub Docs: GitHub's plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans)
- Rulesets are available "in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, and GitHub Enterprise Cloud." Push rulesets (blocking by file path, extension or size) are tied to Team or Enterprise Cloud, depending on the docs version, and are not offered on Pro. — [GitHub Docs: Creating rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository); [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- Branch protection behavior: a protection rule by default disables force pushes and prevents deletion of matching branches. However, restrictions "don't apply to people with admin permissions" unless "Do not allow bypassing the above settings" is enabled. On a personal repo the owner is the admin, so this box must be ticked or the protection does not stop the owner's own CLI. — [GitHub Docs: About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- GitLab protected branches are available on "Tier: Free, Premium, Ultimate." Force push is a per-rule toggle ("Allowed to force push"). Protected branches can be deleted only through the UI or API, by Maintainer or Owner, not with local Git commands. Group-level protected branches need Premium. — [GitLab Docs: Protected branches](https://docs.gitlab.com/user/project/repository/branches/protected/)
- Codeberg on private repos: "Keeping software private is obviously not our primary use case." It allows "up to 100 MB of private content for your convenience", for example "your personal notes", for people who contribute to free/libre software. Without such contributions "Codeberg is unfortunately not the right place for you." Request resources before using more than 750 MiB of Git storage, and media backups are discouraged. — [Codeberg FAQ](https://docs.codeberg.org/getting-started/faq/)
- Self-hosted Gitea with LFS for a vault full of PDFs and screenshots is described as a working alternative. — [ndumas: Gitea, git-lfs, and syncing Obsidian vaults](https://code.ndumas.com/ndumas/blog.ndumas.com/blame/commit/c69bfa64e80658303d1fc6d6e28c563749182f77/content/gitea-lfs-and-syncing-obsidian-vaults.md)
- Privacy caveat from a beginner guide: you do not control your data on GitHub, and a private repo carries no guarantee against data mining. — [obsidian.rocks: Backing up your vault on GitHub](https://obsidian.rocks/backing-up-your-obsidian-vault-on-github-for-free/)

### Inferences
- **Free GitHub** gives no server-side guard against `git push --force` rewriting `main`, from `kb` or from a stray agent. Mitigations:
  - Keep `kb` from ever passing `--force`.
  - Set `receive.denyNonFastForwards` and `receive.denyDeletes`. This only works on remotes you control, such as a bare repo (`git init --bare` then `git config receive.denyNonFastForwards true`), not on GitHub (background knowledge).
  - Pay for **GitHub Pro** to get rulesets on a private repo, with "block force pushes" and "restrict deletions" and the admin bypass removed.
- A **bare repo on an external disk or NAS** (`git remote add nas /Volumes/NAS/kb.git`) gives deny-non-fast-forward protection, no size limits and no third-party privacy exposure. It overlaps with Time Machine, though, because both are usually in the same house.
- For a mostly-Markdown vault, size limits are irrelevant. Attachments (PDFs, images) are the only risk. A pre-commit size guard (for example, refuse files over 25 MB) is cheaper than adopting LFS.
- Pushing on every write is chatty. Push from `kb` at most every N minutes, or via an explicit `kb sync`, or a launchd job. Never block a write on network failure.

### Gaps
- I did not get exact 2026 LFS overage prices; the docs point to the pricing calculator.
- I did not verify Bitbucket Free's current private-repo branch restrictions or size limits (Bitbucket historically capped free workspaces at about 1 GB and 5 users, but this was not checked).
- I did not verify that Forgejo or Gitea protected branches block force push by default on self-hosted instances.

## 4. Secrets and privacy: GitHub scanning, local pre-commit scanning, encryption

### Takeaway
Do not count on GitHub to catch secrets in a **private** personal repo. Default push protection covers public repos only, and repository-level Secret Protection is a paid product sold to organizations. A local `gitleaks` pre-commit hook, or a `gitleaks dir` call from `kb` on the staged files, is the practical guard. For encryption at rest on a hosted remote, git-remote-gcrypt hides everything but makes every push a force push and re-uploads history on non-rsync backends. git-crypt leaves file names and commit messages in cleartext.

### Cited Findings
- GitHub "push protection for users" is enabled by default but "stops you from pushing secrets to public repositories on GitHub." Repository push protection "requires GitHub Secret Protection to be enabled" and is disabled by default. — [GitHub Docs: About push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection)
- Since April 1, 2025, GitHub Advanced Security was split into the standalone products GitHub Secret Protection and GitHub Code Security. Secret Protection costs $19 per active committer per month and is available to GitHub Team customers. — [GitHub changelog 2025-03-04](https://github.blog/changelog/2025-03-04-introducing-github-secret-protection-and-github-code-security/)
- The Secret Protection price estimator is documented for organizations on Team, Enterprise Cloud and Enterprise Server; personal accounts are not mentioned. — [GitHub Docs: Estimate price](https://docs.github.com/en/code-security/how-tos/secure-at-scale/configure-organization-security/configure-specific-tools/estimating-the-price-of-secret-protection)
- Since March 2024, new **public** repos have secret scanning and push protection on by default. — [GitHub changelog 2024-03-11](https://github.blog/changelog/2024-03-11-secret-scanning-and-push-protection-are-enabled-by-default-on-new-public-repositories/)
- gitleaks:
  - Install with `brew install gitleaks`; use the pre-commit framework hook `id: gitleaks` (README example pins `v8.24.2`).
  - Scanning commands: `gitleaks dir <path>` (files) and `gitleaks git` (history via `git log -p`). `gitleaks protect` has been deprecated since v8.19.0 but still works.
  - Exit code 1 means leaks found; it can be changed with `--exit-code`. Config is read from `.gitleaks.toml`, and `[extend] useDefault = true` extends the default rules.
  - The README says gitleaks "is feature complete." Future releases will be security patches only, and the maintainer is moving to "Betterleaks."
  — [gitleaks README](https://github.com/gitleaks/gitleaks)
- git-crypt:
  - It "does not encrypt file names, commit messages, symlink targets, gitlinks, or other metadata", and leaks whether a file changed, its length, and whether two files are identical.
  - Encrypted files are not compressible, and previously granted access cannot be revoked.
  - It "cannot be used securely unless the entire repository is protected against tampering."
  - Latest version is 0.8.0 (2025-09-23), described as not yet mature.
  — [git-crypt README](https://github.com/AGWA/git-crypt)
- git-remote-gcrypt:
  - It encrypts packfiles and the manifest (branch list, pack list) with GnuPG and hides participant key IDs.
  - "Every git push effectively has `--force`. Be sure to pull before pushing."
  - With plain git URLs or sftp, a push "requires uploading the entire repository history with each push." rsync is recommended but "won't work with a repository hosting service like Gitolite, GitHub or GitLab."
  - It may repack the remote without warning, and the rclone backend is experimental.
  — [git-remote-gcrypt README](https://github.com/spwhitton/git-remote-gcrypt)

### Inferences
- For `kb`, the cheapest guard is to run `gitleaks dir` on the exact files being committed, or install a pre-commit hook, and refuse or warn on hits. If gitleaks is absent, skip the scan with a warning. Agent-written notes are a plausible place for pasted tokens, such as an agent copying an `.env` value into a research note.
- detect-secrets (Yelp) and trufflehog are alternatives. trufflehog emphasizes verifying live credentials, which needs network calls. Neither was fetched this session.
- **git-crypt** suits "encrypt a few sensitive files" but not a notes vault, where file names and commit messages are themselves sensitive.
- **git-remote-gcrypt** hides everything, but its force-push semantics conflict with any server-side "no force push" protection, and it does not scale for history on GitHub.
- **age**: encrypt the whole repo bundle (`git bundle create` then `age -r`) and upload it as an opaque blob. This is a backup rather than a remote and gives up incremental pushes (background knowledge).
- If privacy matters more than convenience, a NAS or external-disk bare repo with no encryption (protected by disk encryption) is simpler than any of these tools.

### Gaps
- No primary GitHub doc explicitly says "Secret Protection cannot be purchased for personal-account private repos." The conclusion rests on the docs being organization-only, not on an explicit statement, so verify in the repo's Settings → Security page.
- I did not verify current versions or maintenance status of detect-secrets or trufflehog.

## 5. Authenticating push from a CLI on macOS

### Takeaway
For a single repo, a **deploy key with write access** (an SSH key attached to that one repo) is the narrowest credential that needs no token rotation. Its downsides are no expiry and usually no passphrase. Alternatives are the user's normal SSH key, `gh auth` with the osxkeychain credential helper, or a fine-grained PAT scoped to one repo with an expiry.

### Cited Findings
- Deploy keys:
  - They are SSH keys that "only grant access to a single repository", attached to the repo rather than the account. They are read-only by default, with opt-in "Allow write access."
  - Cons: typically no passphrase, so a compromised machine exposes them; they are "credentials that don't have an expiry date."
  - Alternatives listed: HTTPS with OAuth or personal tokens (revocable), machine users, and GitHub App installation tokens that expire after 1 hour.
  — [GitHub Docs: Managing deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)
- Obsidian Git on mobile has no SSH authentication, only HTTPS. Some Git hosts need extra HTTPS or SSH setup. — [Obsidian Git README](https://github.com/Vinzent03/obsidian-git)

### Inferences
- MVP recommendation: `kb` does not handle credentials at all. It runs `git push`, which inherits whatever the user configured, and on failure prints a clear message. Document two setups:
  1. A dedicated SSH deploy key in `~/.ssh/kb_vault_ed25519` with a host alias in `~/.ssh/config`, stored in the macOS Keychain via `ssh-add --apple-use-keychain` (background knowledge).
  2. `gh auth login` plus `gh auth setup-git`, or a fine-grained PAT limited to one repo with Contents read/write, stored by `git-credential-osxkeychain`. Fine-grained PAT details were not re-fetched this session.
- Run pushes non-interactively with `GIT_TERMINAL_PROMPT=0` and `GIT_SSH_COMMAND="ssh -o BatchMode=yes"`, so an agent-invoked `kb` never hangs on a password prompt.

### Gaps
- I did not fetch the current GitHub docs on fine-grained PAT limits (maximum lifetime, repo selection) for 2026.

## 6. Failure modes: why Git is not a backup, and practitioner experience

### Takeaway
Git gives history, not durability. One local `.git` can be corrupted or deleted along with the vault, `reset --hard` or a force push can discard work, and a hosted remote without enforced protection can be rewritten by the same credentials. Pairing local Git (history) with Time Machine (byte-level copy, including `.git`) and an optional append-only remote covers the main failure modes. Users report that noisy auto-commit histories, `index.lock` errors and mobile instability are the main pains.

### Cited Findings
- Admin bypass is on by default for GitHub branch protection, so an owner's credential can still force push unless bypass is disabled. — [GitHub Docs: About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- With git-remote-gcrypt, every push is effectively a force push, so a stale clone pushing can overwrite the remote. — [git-remote-gcrypt README](https://github.com/spwhitton/git-remote-gcrypt)
- Obsidian Git on mobile:
  - The README calls it "very unstable" or "highly unstable."
  - It uses isomorphic-git, with no SSH, limited repo size due to memory, no rebase, and no submodules.
  - Obsidian may crash on clone or pull, hit buffer overflows, or run indefinitely.
  - The author recommends other sync services for mobile.
  — [Obsidian Git README](https://github.com/Vinzent03/obsidian-git)
- Obsidian may hang on indexing when the vault contains git-lfs-stored files: when LFS objects are not pulled, the pointer files are what Obsidian sees. — [Obsidian forum: git-lfs indexing hang](https://forum.obsidian.md/t/obsidian-vault-hangs-on-indexing-when-the-vault-contains-files-stored-with-git-lfs/51759)
- Users reduce commit frequency because fine-grained auto-commits produce meaningless history. — [Obsidian forum thread](https://forum.obsidian.md/t/obsidian-git-plugin-for-automatic-vault-backup-with-git/7790/5)
- Setup pitfalls show up when a Git repo sits inside a cloud-synced folder such as OneDrive and several apps point at it. — [Obsidian forum: GitDesktop + GitHub + ObsidianGit](https://forum.obsidian.md/t/using-gitdesktop-github-obsidiangit-to-backup-vaults/14219?page=2)

### Inferences
- Main failure modes for this project, with mitigations:
  1. **Agent runs `git reset --hard`, `git checkout -- .` or `git clean -fdx`.** Commits made before the destructive command survive in the reflog, so restore from history; uncommitted Obsidian edits are lost. This is an argument for committing external changes promptly (the launchd snapshot).
  2. **`.git` corruption** (disk error, or interrupted writes when the vault also sits in iCloud or Dropbox). Never put a Git repo inside iCloud Drive; Time Machine plus a remote remain independent copies.
  3. **The vault directory is deleted together with `.git`.** Only Time Machine or a remote helps.
  4. **Force push or branch deletion on the remote.** Use Pro rulesets, or a bare repo with `receive.denyNonFastForwards`.
  5. **Secrets pushed to a hosted remote.** Removing them after the fact requires history rewriting (`git filter-repo`) and key rotation; prevent with gitleaks before commit.
- Time Machine already copies `.git`, so local Git plus Time Machine provides history and an on-site copy. A remote is the only off-site copy in this design.

### Gaps
- I found no dedicated 2025–2026 post-mortem of a vault Git corruption incident. Reports are anecdotal forum threads.
- Reddit threads were not fetched this session.

## 7. Prior art: CLI note tools with built-in Git sync

### Takeaway
`nb` is the closest analogue. It auto-commits every add, edit or delete, auto-syncs (pull, merge, push) on every command when a remote is set (toggle with `nb set auto_sync`), and handles conflicts by leaving Git conflict markers in text files and `--conflicted-copy` duplicates for binary files.

### Cited Findings
- nb:
  - "Any notebook with a remote URL will sync automatically every time a command is run in that notebook." `nb sync` syncs manually, and "automatic git syncing can be turned on or off with `nb set auto_sync`."
  - On sync it "merges changes"; on overlapping edits it "saves both versions within the file separated by git conflict markers."
  - For binary or encrypted files it saves both versions, appending `--conflicted-copy` to the remote version's filename.
  - `nb git` and `nb run` are escape hatches for manual resolution.
  - Notes can be individually encrypted (AES-256 via OpenSSL by default, or GPG).
  — [nb docs](https://xwmx.github.io/nb/)
- The Obsidian Git plugin links to a conflict-resolution guide for pulls or syncs stopped by conflicts. — [Obsidian Git README](https://github.com/Vinzent03/obsidian-git)

### Inferences
- For `kb`'s MVP, which is single-device, push-only and has no pull, conflicts cannot arise from the remote, so `nb`'s merge machinery is backlog material. The useful parts to copy now are:
  - Commit on every write, transparently.
  - A single toggle for auto-sync.
  - A history command that wraps `git log` per note, e.g. `kb history <note>`.
  - A restore command that wraps `git restore --source` and appends or recreates rather than deletes.
- For later multi-device work, nb's `--conflicted-copy` approach for binaries is a proven pattern.

### Gaps
- zk, GitJournal, Foam and Dendron docs were not fetched in this session, so no claims about their commit and push triggers. From background knowledge: zk has no built-in Git sync, GitJournal is a mobile Git-backed notes app, and Foam and Dendron rely on VS Code's Git. All of this is unverified.
