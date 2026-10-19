# Obsidian-ecosystem sync and versioning options, and how each coexists with an external CLI writer (as of 2026-10-10)

Scope: a single macOS user with a local Obsidian vault. The Python CLI `kb` is the only writer for AI agents, and the user also edits in Obsidian. The MVP needs protection against accidental deletion and, optionally, an off-machine copy. Phone access and multi-device sync are deferred. Git is covered in depth by another researcher, so it appears here only briefly.

All facts below were fetched or searched on 2026-10-10 unless stated otherwise.

## Q1. Obsidian Sync: pricing, version history, deleted files, E2EE, selective sync, external writers, use as backup; File recovery core plugin

### Takeaway
Obsidian Sync is a paid, end-to-end-encrypted (E2EE), two-way sync service.
- **Plans:** Standard costs $4/mo billed annually and keeps note history for 1 month. Plus costs $8/mo billed annually and keeps note history for 12 months.
- **Restore:** it has a UI for restoring deleted files. Attachment history lasts only 2 weeks on every plan.
- **Not a backup:** it is a sync service and only runs while Obsidian is open. Obsidian's own docs say not to combine it with another sync service on the same files.
- **File recovery:** this core plugin is a local-only safety net (5-minute snapshots kept 7 days by default, `.md` and `.canvas` files only). Its snapshots live outside the vault and do not sync.

### Cited Findings
**Pricing (dated 2026-10-10)**
- The Sync landing page lists two tiers:
  - **Sync Standard:** $4/mo billed annually or $5/mo billed monthly. 1 synced vault, 1 GB total storage, 5 MB max file size, 1 month of version history.
  - **Sync Plus:** $8/mo billed annually or $10/mo billed monthly. 10 vaults, 10 GB storage (can be raised to 100 GB), 200 MB max file size, 12 months of version history.
  - Source: [obsidian.md/sync](https://obsidian.md/sync)
- **Conflicting source:** the general pricing page, fetched the same day, showed a single Sync entry at "$4 per user per month annually / $5 monthly". It listed features but no tiers. This is most likely just the starting price, but it does not match the landing page. — [obsidian.md/pricing](https://obsidian.md/pricing)
- The help page "Plans and storage limits" confirms the same tier limits:

  | | Standard | Plus |
  |---|---|---|
  | Vaults | 1 | 10 |
  | Max file size | 5 MB | 200 MB |
  | Storage | 1 GB | 10–100 GB |
  | History | 1 month | 12 months |

  Storage is one limit for the whole account, and version history and attachments count toward it. — [obsidian.md/help/sync/plans](https://obsidian.md/help/sync/plans)
- Refunds are available within 7 days. — [obsidian.md/sync](https://obsidian.md/sync)

**Version history and deleted files**
- "On the Standard plan, notes are retained for 1 month, while on the Plus plan, they are kept for 12 months." For attachments, "older versions are stored for two weeks" on every plan. — [obsidian.md/help/sync/version-history](https://obsidian.md/help/sync/version-history)
- **Deleted files:** go to Settings → Core plugins → Sync → "Deleted files" → View, pick a version, then Restore. "The note will be restored to its original location in the filesystem." Bulk restore works with checkboxes or shift+click, but files restored in bulk cannot be reviewed in that menu. — [version-history](https://obsidian.md/help/sync/version-history)
- **Vault configuration** changes also have history and can be restored. The docs do not say how often a new version is recorded, only that Sync "regularly checks for updates". — [version-history](https://obsidian.md/help/sync/version-history)

**Encryption**
- Sync uses end-to-end encryption with AES-256. — [obsidian.md/sync](https://obsidian.md/sync)

**Selective sync**
- By default, all files and folders sync. You can exclude folders.
- Selective sync for file types is on by default for images, audio, video and PDF. "Sync all other types" must be turned on for anything else.
- Hidden items whose names start with "." are excluded, except `.obsidian`.
- Vault configuration sync is split into categories: main settings, appearance, themes/snippets, hotkeys, core plugin list/settings, and community plugin lists, which are opt-in.
- "Sync settings do not sync across devices."
- "Adding a file to the Excluded files list does not remove it from the remote vault if it has already been synced."
- Source: [obsidian.md/help/sync/settings](https://obsidian.md/help/sync/settings)

**Conflicts**
- **Markdown:** merged with Google's diff-match-patch. This "may sometimes create duplicate text or formatting problems."
- **Other files, including canvas:** "last modified wins".
- **Settings JSON:** local keys are applied over the remote ones.
- **Optional mode:** "Create conflict file" instead of merging. This is set per device.
- **Notes created on two devices close together:** Sync "will keep the remote version without merging the two". The local copy can then be recovered only through File recovery.
- Source: [obsidian.md/help/sync/troubleshoot](https://obsidian.md/help/sync/troubleshoot)
- **Duplication bug:** a long forum thread (93+ posts) reports "Obsidian Sync incorrectly duplicates sections of files". — [forum.obsidian.md/t/94732](https://forum.obsidian.md/t/obsidian-sync-incorrectly-duplicates-sections-of-files/94732/93)
- **Resurrected deletions:** search surfaced a thread titled "Obsidian Sync silently resurrects deleted/moved files when offline device reconnects" (URL from search, now 404) and an older one, "Obsidian Sync on iPhone Overwrites Newer Data, Causing Data Loss". Treat both as user reports, not confirmed bugs. — [forum.obsidian.md/t/85214](https://forum.obsidian.md/t/obsidian-sync-on-iphone-overwrites-newer-data-causing-data-loss/85214?page=3)

**External writers**
- The official docs do not say how Sync handles files changed while Obsidian is closed, or files changed by an external program. — [troubleshoot](https://obsidian.md/help/sync/troubleshoot), [settings](https://obsidian.md/help/sync/settings)
- **User reports** (forum, not official):
  - Sync detects files modified by external tools and uploads them, even files never opened in Obsidian.
  - Sync runs only while the app is running. Quitting quickly after a write can leave changes unsynced.
  - On network drives the OS file watcher can miss external edits, and older remote versions then overwrite them.
  - Sources: search summary of [forum.obsidian.md/t/80363](https://forum.obsidian.md/t/finish-syncing-even-if-window-app-is-closed/80363) and [forum.obsidian.md/t/22710](https://forum.obsidian.md/t/file-changes-on-a-network-drive-made-outside-obsidian-are-not-shown/22710)
- **Claude agent edits reverted:** a Claude-related GitHub issue reports agent edits to a vault being reverted by "external synchronization (likely Obsidian sync or OneDrive)". The vault was also inside OneDrive, so the cause is unconfirmed. — [github.com/anthropics/claude-code/issues/52493](https://github.com/anthropics/claude-code/issues/52493)

**Coexistence with other sync services and backups**
- "Avoid using multiple solutions to sync the same files." Folders likely managed by a third-party service include the macOS Desktop and Documents folders, the iCloud folder, and Dropbox or Drive folders. The recommended macOS location is `/users/username/vaults`. If a linked vault sits inside a syncing service, Sync settings shows a warning.
- On backups the docs say only that "cloud storage services may play a role in your backup strategy". They do not mention Git.
- Source: [obsidian.md/help/sync/switch](https://obsidian.md/help/sync/switch)

**File recovery core plugin**
- Snapshots are taken at least 5 minutes apart and kept for 7 days by default. Both values are configurable.
- Snapshots are stored "in the Global settings, outside of the vault" and hold full content.
- Only `.md` and `.canvas` files can be restored.
- It is unavailable under Apple Lockdown mode unless Obsidian is exempted.
- Snapshots may become inaccessible if the vault is moved without the vault switcher.
- "File recovery snapshots will not sync between devices."
- Source: [obsidian.md/help/plugins/file-recovery](https://obsidian.md/help/plugins/file-recovery)

### Inferences
- **Not a backup:** Sync works as a recovery tool only within its history window (1 month for notes on Standard, 2 weeks for attachments). Since it only runs while Obsidian is open, a `kb` write made while Obsidian is closed is uploaded only on the next launch.
- **Cannot be used as backup only:** there is no documented one-way or backup-only mode. It is always two-way, and deletions in the vault propagate as deletions, recoverable only inside the history window.
- **File recovery and `kb` writes:** File recovery is triggered by Obsidian, and the docs don't say whether it snapshots files changed by external programs. Relying on it to catch `kb` writes is unverified.
- **Vault location:** if the vault lives under `~/Documents` and iCloud "Desktop & Documents" is on, that already counts as a second sync mechanism by Obsidian's own definition. The vault should go in a non-synced path such as `~/vaults`.

### Gaps
- I found no official statement on how Obsidian Sync reconciles changes made while Obsidian is closed, for example whether it compares mtime or hash at startup.
- I found no official snapshot interval for Sync version history.
- I could not resolve the pricing-page vs Sync-page discrepancy. It may be a page simplification, not a plan change.

## Q2. Community sync plugins: Remotely Save, Self-hosted LiveSync, Obsidian Git (brief)

### Takeaway
- **Self-hosted LiveSync** is very actively maintained (four stable releases between 27 Sep and 5 Oct 2026). It is complex, needs CouchDB or object storage, and explicitly forbids running alongside any other sync, iCloud included.
- **Remotely Save** supports S3, Dropbox, OneDrive and WebDAV for free and has paid "PRO" backends and smart merge. Its latest visible release (0.5.25, "20 Oct", year not shown, at least a year old) suggests slowing maintenance.
- **Both plugins** run only inside Obsidian, so their view of `kb` writes depends on Obsidian being open. Both warn users to back up before use.

### Cited Findings
**Remotely Save**
- **Backends:**
  - Free: S3/S3-compatible, Dropbox, OneDrive personal (App Folder), WebDAV, Webdis.
  - PRO (paid): OneDrive full, Google Drive, Box, pCloud, Yandex Disk, Koofr, Azure Blob.
  - Source: [github.com/remotely-save/remotely-save](https://github.com/remotely-save/remotely-save)
- **Conflicts:** the free version "can detect conflicts" and lets the user pick a version. PRO "Smart Conflict" can "merge small markdown files". — [README](https://github.com/remotely-save/remotely-save)
- **E2EE:** supported "using openssl / rclone crypt format" when a password is set. "the vault name itself is not encrypted". — [README](https://github.com/remotely-save/remotely-save)
- **Warnings in the README:**
  - "ALWAYS, ALWAYS, backup your vault before using this plugin."
  - "Auto sync only works when Obsidian is being opened."
  - "some config files' modified times are changed everytime when Obsidian is opened … destroys the assumptions of the plugin."
  - Mobile has performance issues with files of 50 MB or more.
  - Source: [README](https://github.com/remotely-save/remotely-save)
- **Recent releases** (years not shown on the page):
  - 0.5.25 (20 Oct) and 0.5.24 (30 Sep): version bumps.
  - 0.5.23: ".obsidian path issue".
  - 0.5.22: Google Drive auth and a ".obsidian folder mis-synced issue".
  - 0.5.21 (08 Sep): allow/ignore list logic and "vault being empty" logic.
  - Source: [releases](https://github.com/remotely-save/remotely-save/releases)
- Obsidian's sync guide names Remotely Save and LiveSync as iOS options but notes "these methods aren't officially supported, and results may vary." — [obsidian.md/help/sync-notes](https://obsidian.md/help/sync-notes)

**Self-hosted LiveSync**
- **Backends:** CouchDB or object storage (MinIO, S3, R2), plus WebRTC peer-to-peer (which still needs a signalling relay). It supports E2EE. Version 1.0 requires Obsidian 1.7.2 or later. — [github.com/vrtmrz/obsidian-livesync](https://github.com/vrtmrz/obsidian-livesync)
- **Warnings:**
  - "Do not enable this plug-in alongside another synchronisation solution (including iCloud and Obsidian Sync)."
  - "Before installing or upgrading this plug-in, please back up your vault."
  - Avoid closing Obsidian until progress indicators clear, "to prevent file and database corruption".
  - Source: [README](https://github.com/vrtmrz/obsidian-livesync)
- **Releases:** 1.0.35 (5 Oct 2026), 1.0.34 (2 Oct 2026, a security fix for sensitive data in exported config, "Updating is recommended"), 1.0.33 (1 Oct 2026), 1.0.32 (27 Sep 2026). — [releases](https://github.com/vrtmrz/obsidian-livesync/releases)
- **Fix in 1.0.32:** a pre-release bug where "a receiving device could leave files from other devices absent from the Vault". — [releases](https://github.com/vrtmrz/obsidian-livesync/releases)
- **Breaking changes in 1.0.33:** some settings changes require updating all devices or a "Rebuild and Fetch". — [releases](https://github.com/vrtmrz/obsidian-livesync/releases)

**Obsidian Git** (brief)
- Obsidian's guide: "Git provides strong version control, but syncing isn't automatic. You must manually push and pull changes."
- On iOS, the Git client Working Copy is not officially supported, but "many users have successfully used it".
- Sources: [obsidian.md/help/sync-notes](https://obsidian.md/help/sync-notes)
- **Newer Git-based plugins** list workspace-file handling as a feature:
  - Git Vault Sync works on mobile without system Git.
  - GitSync Portal treats workspace layout files as device-local.
  - Silence Git Sync keeps the local text on conflict and writes the remote copy as `*.sync-remote.md`.
  - Sources: [community.obsidian.md/plugins/git-vault-sync](https://community.obsidian.md/plugins/git-vault-sync), [gitsync-portal](https://community.obsidian.md/plugins/gitsync-portal), [silence-git-sync](https://community.obsidian.md/plugins/silence-git-sync)

### Inferences
- **Mismatch with `kb`:** both plugin-based syncs live inside Obsidian. Deletions or edits made by `kb` while Obsidian is closed are seen only as filesystem state at the next scan. Plugins that infer deletions from a "previous sync" database (Remotely Save, LiveSync) are exactly where an external writer that renames or deletes files can cause surprises.
- **LiveSync's model:** LiveSync keeps a database copy of the vault and rebuilds files from it. This adds a second source of truth next to the files `kb` writes, which makes it the hardest option to reason about with an external writer.
- **Remotely Save's maintenance:** the cadence looks low. Combined with paid features for Google Drive, this makes it a weaker long-term foundation, though it remains the most common free iOS route to S3 or WebDAV.

### Gaps
- No Remotely Save PRO price was found on the README.
- The years for Remotely Save releases are not shown on the releases page.
- I found no specific Remotely Save or LiveSync data-loss issue threads in this pass. Searches returned unrelated tools.
- The 2026 maintenance status of Obsidian Git was not checked (another researcher covers it).

## Q3. Syncthing, iOS (Möbius Sync and alternatives), the Android fork situation, and versioning modes

### Takeaway
Syncthing is peer-to-peer, two-way, file-level sync that does not need Obsidian running, so it sees `kb` writes immediately. Its versioning archives only changes *received from other devices*, never local edits or deletions, so on a single machine it provides no protection against accidental deletion.
- **Android:** the official app ended with the December 2024 release. The community "Syncthing-Fork" (F-Droid and Play, now under `researchxxl`) is the line Obsidian's docs point to.
- **iOS:** Möbius Sync and Synctrain work but are fiddly because of sandboxing and background-sync limits.

### Cited Findings
**Versioning**
- "Versioning applies to changes received from other devices." Local edits: "Syncthing will not and can not archive the old version." Folders default to no versioning. — [docs.syncthing.net/users/versioning.html](https://docs.syncthing.net/users/versioning.html)
- **Modes:**
  - **trashcan:** the last copy of each file goes to `.stversions`. `cleanoutDays` sets expiry, and 0 keeps copies forever.
  - **simple:** keeps N versions per file, plus `cleanoutDays`.
  - **staggered:** thinned over time — one version per 30 s for the first hour, per hour for the first day, per day up to 30 days, then per week up to `maxAge`.
  - **external:** runs a user command before a file is replaced.
  - The `.stversions` folder is created inside the shared folder by default.
  - Source: [docs.syncthing.net/users/versioning.html](https://docs.syncthing.net/users/versioning.html)

**Android**
- The official syncthing-android app was retired. The last release came with the December 2024 Syncthing version, because Google Play publishing had become something "between hard and impossible" and the app had "no active maintenance". — [forum.syncthing.net/t/discontinuing-syncthing-android/23002](https://forum.syncthing.net/t/discontinuing-syncthing-android/23002/16)
- Obsidian's sync guide says Android requires the community "Syncthing-Fork", since the official app is "no longer maintained". — [obsidian.md/help/sync-notes](https://obsidian.md/help/sync-notes)
- **Syncthing-Fork in 2026:**
  - It is still published on F-Droid under the package `com.github.catfriend1.syncthingfork`, version 2.1.x bundling Syncthing 2.1.x. The repo is now `researchxxl/syncthing-android`. — [f-droid.org](https://f-droid.org/it/packages/com.github.catfriend1.syncthingfork/), [IzzyOnDroid](https://apt.izzysoft.de/fdroid/index/apk/com.github.catfriend1.syncthingfork?repo=main)
  - A January 2026 discussion says that after the original maintainer (catfriend1) disappeared, the two forks "joined hands" into one line, published on F-Droid and Play. Trust and signing questions remain open, and F-Droid paused updates for a while during the confusion. — [discuss.privacyguides.net](https://discuss.privacyguides.net/t/which-syncthing-fork-should-one-use-after-the-projects-handover/34966/2.md), [piefed.jeena.net](https://piefed.jeena.net/post/384821)
  - BasicSync and Syncthing Tray builds are mentioned as alternatives. — [discuss.privacyguides.net](https://discuss.privacyguides.net/t/which-syncthing-fork-should-one-use-after-the-projects-handover/34966/2.md)

**iOS**
- Obsidian lists Syncthing as unsupported on iOS. — [obsidian.md/help/sync-notes](https://obsidian.md/help/sync-notes)
- **Möbius Sync** embeds Syncthing:
  - Background sync runs at intervals iOS decides (reportedly 5–15 min, and up to 24 h at first).
  - Synced folders sit in Möbius's sandbox unless you use "Pick external folder" to bookmark the Obsidian folder. Results vary between users.
  - Synctrain is an alternative client.
  - Sources: [forum.obsidian.md/t/72022](https://forum.obsidian.md/t/sync-mac-pc-and-ios-using-syncthing-mobius-sync/72022), [forum.obsidian.md/t/69569](https://forum.obsidian.md/t/syncthing-mobius-sync-on-ios/69569), [stephanmiller.com (2026 guide)](https://www.stephanmiller.com/sync-obsidian-iphone-ipad-free/)

### Inferences
- **Backup suitability:** with one Mac only, Syncthing provides no off-machine copy and no deletion protection. With a second always-on device (NAS or server) using versioning, *that* device keeps the Mac's deletions and overwrites in `.stversions`, because from its side they are received changes. Even then it is a sync mechanism, not one-way backup, unless the remote folder is set to "Receive Only".
- **Interaction with Git:** `.stversions` lives inside the vault folder by default and should be excluded from Git and from Obsidian's index.

### Gaps
- Möbius Sync's current price and maintenance status in 2026 could not be verified. Sources conflict on whether it is free or a one-time purchase.
- Default numeric values for `keep`, `cleanoutDays` and `maxAge` are not stated on the docs page.

## Q4. iCloud Drive, Dropbox and Google Drive as the vault location (official guidance and mobile implications)

### Takeaway
- Obsidian officially supports only its own Sync. It names Obsidian Sync and iCloud as the recommended iOS options.
- Dropbox, Google Drive, OneDrive and Syncthing are unsupported on iOS.
- Google Drive is "not officially supported for syncing Obsidian vaults" at all.
- For a future iPhone, the vault would have to be in iCloud Drive's Obsidian folder or use Obsidian Sync (or a plugin or Git client workaround).

### Cited Findings
- "The most straightforward and officially supported sync method is our first-party solution" (Obsidian Sync). — [obsidian.md/help/sync-notes](https://obsidian.md/help/sync-notes)
- **iCloud:**
  - It works between iOS and macOS. On iOS the vault should sit in the Obsidian app folder.
  - "iCloud Drive on Windows may lead to file duplication or corruption."
  - Source: [sync-notes](https://obsidian.md/help/sync-notes)
- **Google Drive:** "not officially supported for syncing Obsidian vaults", and not supported on iOS. — [sync-notes](https://obsidian.md/help/sync-notes)
- **OneDrive:** keep files offline and avoid Files On-Demand. Not supported on iOS. — [sync-notes](https://obsidian.md/help/sync-notes)
- **Dropbox:** appears only in the list of services not supported on iOS. — [sync-notes](https://obsidian.md/help/sync-notes)
- **iOS/iPadOS:** the recommended options are Obsidian Sync and iCloud. — [sync-notes](https://obsidian.md/help/sync-notes)
- **Multiple services:** avoid "syncing the same vault across multiple services". — [sync-notes](https://obsidian.md/help/sync-notes)
- **Moving away from iCloud:** to use Obsidian Sync, move the vault out of the iCloud, Desktop or Documents folders. On mobile, move it to "On My iPhone" and delete the iCloud copy. — [obsidian.md/help/sync/switch](https://obsidian.md/help/sync/switch)
- **workspace.json churn:** OneDrive-synced vaults produce many `workspace.json` conflict copies. The advice is to quit Obsidian on the other machine before switching and to exclude `.obsidian/workspace*.json`. — [forum.obsidian.md/t/115229](https://forum.obsidian.md/t/vault-synced-over-onedrive-across-multiple-machines-generates-many-copies-of-workspace-json/115229)

### Inferences
- **Upgrade path out of iCloud:** putting the vault in iCloud Drive now (the "free iPhone path") later forces a migration if the user moves to Obsidian Sync, because the vault must leave iCloud.
- **iCloud vs `kb`:** iCloud's macOS "Optimize Mac Storage" can evict files. The documented exclusion problems (no `.gitignore`-style control) make it awkward to run alongside a Git repo in the same folder. This is an inference; I found no source specific to `kb`-style writers.

### Gaps
- I found no official Obsidian doc on iCloud file eviction or `.git` folders inside iCloud.

## Q5. Conflicts between a sync mechanism and an external CLI writer (`.obsidian/`, `workspace.json`, exclusions)

### Takeaway
- `.obsidian/workspace*.json` (and `.obsidian/cache`) is per-device UI state that changes constantly. It should be excluded from Git and from any two-way sync.
- External writes are generally picked up by Obsidian's file watcher. They are lost or reverted mainly when (a) the file watcher misses them (network or virtual filesystems) or (b) a sync layer replays an older remote version.

### Cited Findings
- **Git conflicts:** `workspace.json` "maintains the state of the current workspace" and keeps causing Git conflicts across machines. The usual workaround is to gitignore it. Ignoring all of `.obsidian` stops settings from syncing. — [forum.obsidian.md/t/31717](https://forum.obsidian.md/t/refactor-workspace-file-to-be-git-friendly/31717)
- **Recommended ignores:** `.obsidian/workspace.json`, `workspace-mobile.json`, the cache folder and `.trash/`. Already-tracked files need `git rm --cached`. Without these rules, desktop and phone "fight over layout state on every sync". — [community.obsidian.md/plugins/gitlab-gitless-sync](https://community.obsidian.md/plugins/gitlab-gitless-sync)
- **Obsidian Sync and workspace files:** "Obsidian Sync problem with Workspace file" is a known forum topic. — [forum.obsidian.md/t/70364](https://forum.obsidian.md/t/obsidian-sync-problem-with-workspace-file/70364)
- **Remotely Save and config files:** the README says Obsidian rewrites config-file mtimes on each launch, which breaks mtime-based sync assumptions. — [github.com/remotely-save/remotely-save](https://github.com/remotely-save/remotely-save)
- **External edits and Obsidian Sync:** external edits are picked up by Obsidian Sync when Obsidian is running. On a network drive, missed watcher events led to "older versions from other devices overwriting the external edits". — [forum.obsidian.md/t/22710](https://forum.obsidian.md/t/file-changes-on-a-network-drive-made-outside-obsidian-are-not-shown/22710)
- **Agent edits reverted:** a Claude-related report of agent edits being reverted in a vault using Obsidian Sync together with OneDrive. — [github.com/anthropics/claude-code/issues/52493](https://github.com/anthropics/claude-code/issues/52493)

### Inferences
- **Practical rules for `kb`:**
  - Write atomically (temp file + rename) so watchers never see half-written files.
  - Never write inside `.obsidian/`.
  - Exclude `.obsidian/workspace*.json`, `.obsidian/cache`, `.trash/`, `.stversions/` and any `*.sync-conflict-*` or conflict files from Git.
  - Keep the vault outside iCloud, Dropbox and Drive folders (including `~/Documents` if iCloud Desktop & Documents is on).
- **Under a future two-way sync** (Obsidian Sync or Syncthing), the main risk for `kb` is a stale device replaying old content or resurrecting deleted files. A one-way history layer (Git) on the primary Mac is what makes such events recoverable after the sync service's history window has passed.

### Gaps
- I found no official Obsidian documentation on recommended ignore lists or on external-writer best practices.

## Q6. Combining mechanisms safely (one two-way sync + one-way history or backup)

### Takeaway
Every official and plugin source says to use at most one *two-way sync* per vault: Obsidian docs, LiveSync's README and Obsidian Sync's switch guide. One-way, history-only layers do not propagate anything back into the vault, so they are not "sync" in that sense and are compatible. These layers are local Git commits on the primary Mac, a Git push to a private remote, Time Machine, and an rclone one-way copy.

### Cited Findings
- "Avoid using multiple solutions to sync the same files." — [obsidian.md/help/sync/switch](https://obsidian.md/help/sync/switch)
- "Do not enable this plug-in alongside another synchronisation solution (including iCloud and Obsidian Sync)." — [github.com/vrtmrz/obsidian-livesync](https://github.com/vrtmrz/obsidian-livesync)
- Obsidian notes that "cloud storage services may play a role in your backup strategy" and links a separate backup guide. — [obsidian.md/help/sync/switch](https://obsidian.md/help/sync/switch)
- File recovery (local) can run alongside Sync. Its snapshots are outside the vault and never sync. — [obsidian.md/help/plugins/file-recovery](https://obsidian.md/help/plugins/file-recovery)
- Remotely Save and LiveSync both say to back up before use, which implies they expect a separate backup layer. — [remotely-save](https://github.com/remotely-save/remotely-save), [obsidian-livesync](https://github.com/vrtmrz/obsidian-livesync)

### Inferences
- **Safe combinations:**
  - Obsidian Sync (two-way, future phone) + Git on the Mac only (commit locally and push to a private remote; the phone never touches Git) + Time Machine.
  - Syncthing (two-way) + Git on one node only, with `.git/` and `.stversions/` excluded via `.stignore`.
  - The `.git` directory is a hidden "." folder, so Obsidian Sync already excludes it (hidden items other than `.obsidian` are not synced, per [settings](https://obsidian.md/help/sync/settings)).
- **Unsafe combinations:**
  - The vault in iCloud plus Obsidian Sync.
  - Obsidian Git pulling from a remote that another device also pushes to, alongside Obsidian Sync (two two-way mechanisms).
  - LiveSync plus anything.
  - A Git repo inside a Syncthing or iCloud folder that syncs `.git/` across devices.
- **Rule for the MVP:** Git must stay one-way (commit and push from the Mac only, no pull merges) once a two-way mechanism is added. Then it does not conflict with the "one sync mechanism per vault" rule.

### Gaps
- I found no practitioner write-up in this pass that specifically reports long-term results of Obsidian Sync + Git together. The combination is inferred from the documented hidden-folder exclusion and the one-way design.

## Q7. Which MVP choice best keeps the door open for adding phone access later?

### Takeaway
- **Recommended MVP:** local Git, optionally pushed to a private remote, with the vault in a non-synced path such as `~/vaults/...`. It gives deletion protection (full history), an optional off-machine copy, and plain files with no lock-in. It does not occupy the vault's single two-way slot.
- **Adding a phone later:** turn on Obsidian Sync (the simplest and only official route; it requires the vault to be outside iCloud anyway) or Syncthing on Android. Git then keeps running as the one-way history layer.
- **Choices to avoid:** an rclone one-way copy to Drive keeps the door equally open but gives only snapshot-level, not per-change, recovery. Putting the vault in iCloud Drive now is the choice most likely to need undoing later.

### Cited Findings
- **iOS options:** Obsidian Sync and iCloud are the recommended iOS options. Git on iOS (Working Copy) works but is unofficial, and Git sync "isn't automatic". — [obsidian.md/help/sync-notes](https://obsidian.md/help/sync-notes)
- **Obsidian Sync placement:** it needs the vault outside iCloud, Dropbox, Drive, and the macOS Desktop or Documents folders. — [obsidian.md/help/sync/switch](https://obsidian.md/help/sync/switch)
- **Obsidian Sync history is time-limited:** 1 month for notes on Standard, 12 months on Plus, 2 weeks for attachments. A separate long-term history layer is therefore still valuable after a phone is added. — [obsidian.md/help/sync/version-history](https://obsidian.md/help/sync/version-history)
- **Syncthing:** versioning does not protect against local deletions on the editing machine. — [docs.syncthing.net](https://docs.syncthing.net/users/versioning.html)
- **Android Syncthing** depends on a community fork with a messy 2025–26 handover. — [discuss.privacyguides.net](https://discuss.privacyguides.net/t/which-syncthing-fork-should-one-use-after-the-projects-handover/34966/2.md)

### Inferences
- **Ranking for "keeps the door open":**
  1. **Local Git + private remote:** history plus an off-machine copy. Compatible with any later two-way sync if Git stays one-way.
  2. **Local Git only:** history but no off-machine copy. Same compatibility.
  3. **rclone one-way copy to Drive:** off-machine copy with a coarse history, and only if `--backup-dir` or similar is used. Compatible.
  4. **None:** relies on Time Machine or File recovery only, and File recovery covers 7 days and `.md`/`.canvas` only.
  5. **iCloud vault folder:** gives a free iPhone path now but blocks Obsidian Sync later and mixes poorly with Git.
- **iPhone vs Android:** for an iPhone, the realistic future choice is Obsidian Sync (paid, low effort) or iCloud (free, but it means moving the vault and dropping the "outside sync folders" rule). For Android, Syncthing-Fork or Obsidian Sync both fit next to a one-way Git layer.

### Gaps
- I did not verify current costs of a private Git remote or Drive storage (out of scope for this researcher).
