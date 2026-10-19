# Non-Git backup and cloud-copy options for a small personal Markdown vault on macOS (state as of 2026-10-10)

Scope: one user, macOS, a local Obsidian vault (Markdown plus a few attachments, tens of MB) outside any synced folder, and a Python CLI `kb` (installed via `uv tool install`). Baseline under evaluation: `kb sync` = one-way rclone copy to Google Drive that keeps old and deleted versions in an archive folder. Two-way multi-device sync is out of scope.

## 1. rclone + Google Drive: copy vs sync vs backup-dir, bisync, Drive trash/revisions, OAuth burden, invocation from Python

### Takeaway
`rclone sync --backup-dir` (or `copy`) to Google Drive works as a one-way, deletion-safe mirror. The big October 2026 finding is about setup: **rclone's shared Google client_id is being retired during 2026**, so each user has to create their own Google Cloud OAuth client. That client must also be **published (moved out of "Testing")**, otherwise the token dies after 7 days and the nightly copy silently stops. This makes rclone+Drive the option with the heaviest setup in this comparison.

### Cited Findings
**copy / sync / backup-dir / suffix**
- `--backup-dir`: "any files which would have been overwritten or deleted are moved in their original hierarchy into this directory". The remote "must support server-side move or copy and you must use the same remote as the destination of the sync", and the backup dir "must not overlap the destination directory without it being excluded by a filter rule" — [rclone docs](https://rclone.org/docs/)
- `--suffix` adds a suffix to files that would be overwritten or deleted during sync/copy/move. With `sync --suffix` and no `--backup-dir`, the docs recommend excluding the suffix with a filter so sync doesn't delete the backups. `--suffix-keep-extension` turns `file.txt` into `file-2019-01-01.txt` — [rclone docs](https://rclone.org/docs/)
- Exit codes: 0 success, 1 uncategorised error, 2 usage error, 3 directory not found, 4 file not found, 5 temporary error (retry may fix), 6 less serious errors, 7 fatal error, 8 `--max-transfer` reached, 9 nothing transferred (only with `--error-on-no-transfer`), 10 `--max-duration` reached — [rclone docs](https://rclone.org/docs/)
- `--use-json-log` streams log messages as JSON objects with `level`, `msg`, `source` and `time` fields — [rclone docs](https://rclone.org/docs/)
- The default config path on non-Windows systems is `~/.config/rclone/rclone.conf`, overridable with `--config`. Remotes can be defined entirely through env vars named `RCLONE_CONFIG_<NAME>_<OPTION>` plus `RCLONE_CONFIG_<NAME>_TYPE`. Config can be encrypted (nacl secretbox), with the password taken from `RCLONE_CONFIG_PASS` or from `--password-command` / `RCLONE_PASSWORD_COMMAND`. A lost config password means the config can't be recovered — [rclone docs](https://rclone.org/docs/)

**bisync**
- bisync was added in v1.58 and reworked heavily in v1.66 (`--compare`, snapshot model, `--backup-dir1/2`, `--track-renames`). The docs call it "an **advanced command**, so use with care" but no longer describe it as beta. The first run needs `--resync`, and later runs must not use it, or deletions and renames can be undone. `--max-delete` defaults to 50% (abort above that). `--check-access` needs manually created `RCLONE_TEST` files. Some critical errors lock out future runs until a `--resync` — [rclone bisync](https://rclone.org/bisync/)

**Google Drive backend facts**
- "The shared client_id is being retired and will stop working during 2026, so creating your own is now strongly recommended". Elsewhere the page says creating one "is now required rather than merely recommended". The default Google quota is 10 transactions/s — [rclone Drive](https://rclone.org/drive/)
- Own-client steps: create a GCP project, enable the Drive API, configure an External OAuth consent screen, add scopes, add yourself as a test user, then create a "Desktop app" OAuth client and paste its ID and secret into rclone. In testing mode "any grants will expire after a week". Publishing the app avoids this. If PUBLISH is greyed out, add a homepage and privacy-policy URL under Branding. For personal use (<100 users) you "can leave the app unverified, accept the warning screen, and publish it" — [rclone Drive](https://rclone.org/drive/)
- Google's own doc: an External project in "Testing" status gets "a refresh token expiring in 7 days" (unless only name/email/profile scopes are requested). Refresh tokens also stop working after six months unused. There's a limit of 100 refresh tokens per Google Account per client ID, and the oldest is silently invalidated — [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- Developer reports say tokens issued while the app was in Testing may keep the 7-day life after publishing, so a fresh consent is needed. This is forum evidence, not official — [Google Groups thread (2022)](https://groups.google.com/g/adwords-api/c/EXh0Cjg5auw?pli=1)
- Scopes: `drive` (default, full access), `drive.readonly`, `drive.file` (rclone sees only files it created; files uploaded via the web UI are hidden), `drive.appfolder` (private area that the user can't see in the web UI), `drive.metadata.readonly` — [rclone Drive](https://rclone.org/drive/)
- Deletes: `--drive-use-trash` defaults to true ("Send files to the trash instead of deleting permanently"). `rclone cleanup remote:` empties the trash — [rclone Drive](https://rclone.org/drive/)
- Revisions: uploading over an existing path creates a new revision. Revisions are removed "after 30 days or 100 revisions (whatever comes first)" and don't count toward quota. `--drive-keep-revision-forever` pins each new head revision — [rclone Drive](https://rclone.org/drive/). Google help says the same: a version may be deleted after 30 days or 100 newer versions unless marked "Keep forever" — [Google Drive help](https://support.google.com/drive/answer/2409045?hl=en)
- Since 2020-10-13, Drive trash auto-deletes after 30 days, and items in trash still consume quota — [Google Workspace Updates](https://workspaceupdates.googleblog.com/2020/09/drive-trash-auto-delete-30-days.html)
- Limits: about 750 GiB/day upload, about 2 files/s throughput (irrelevant at tens of MB) — [rclone Drive](https://rclone.org/drive/)

### Inferences
- A plain `rclone sync` without `--backup-dir` propagates local deletions to Drive. They land in Drive trash and are gone after 30 days. `rclone copy` never deletes but accumulates stale files and renames as duplicates. `sync --backup-dir` is the right baseline: the mirror equals the vault, and every overwritten or deleted file is moved, still on Drive, into a dated archive that rclone never prunes.
- A suggested command for `kb sync`: `rclone sync ~/Knowledge/main gdrive:kb/current --backup-dir gdrive:kb/archive/$(date +%Y-%m-%dT%H%M%S) --exclude ".obsidian/workspace*.json" --exclude ".trash/**" --use-json-log --stats-one-line -v`. Both paths sit on the same remote, and archive sits outside `current`, as required.
- Restoring a single note means `rclone copy gdrive:kb/archive/<stamp>/path/note.md ~/Knowledge/main/path/` or downloading it via the Drive web UI. Drive revisions (30 days/100) add a second, shorter safety net.
- From Python, call `subprocess.run(["rclone", ...])`, branch on the exit codes above (5 → retry, 7 → fatal, 3/4 → path problem), and parse `--use-json-log` from stderr. Keep a dedicated config file such as `--config ~/.config/kb/rclone.conf` so `kb` doesn't touch the user's own rclone.conf.
- `kb doctor` freshness: `kb` should write its own `last_sync.json` (timestamp and exit code) after each successful run and warn if it's older than N days. To detect expired OAuth, run a cheap `rclone lsd gdrive:kb --max-depth 1`. A token or auth error suggests the 7-day Testing-mode trap or a revoked token.
- Setup burden: install rclone (`brew install rclone`), create a GCP project, a consent screen, a Desktop client and publish it, then `rclone config` with browser OAuth. That's roughly 15–30 minutes of clicking through Google Cloud Console for a non-developer. This is the main argument against the baseline as an MVP default.
- `drive.file` scope limits the blast radius (rclone only sees its own uploads) and fits a dedicated backup folder. It's a sensible privacy choice for `kb`.

### Gaps
- I couldn't confirm the exact date the shared rclone client_id stops working, or whether it already has as of October 2026. The docs only say "during 2026".
- I didn't verify whether `--drive-use-trash` applies to moves into `--backup-dir` (it shouldn't, since those are server-side moves, not deletes).
- The page didn't state which rclone version is current as of October 2026. The bisync changelog lists versions up to v1.74.2.

## 2. Putting the vault inside a synced folder (Google Drive for desktop, iCloud Drive, Dropbox, OneDrive)

### Takeaway
All consumer sync clients are **two-way**: a local deletion or corruption propagates to the cloud. Recovery then relies on the provider's trash or version history, typically 30 days on free tiers. Obsidian officially tolerates iCloud and only weakly supports others. Placeholder/offload ("optimize storage") is the main Obsidian-specific failure mode. This option is sync, not backup.

### Cited Findings
- Obsidian: iCloud can sync vaults between iOS and macOS. Keeping the vault downloaded is "strongly recommended", and on macOS 14 and earlier you must disable Optimize Mac Storage. iOS vaults must live in `iCloud Drive/Obsidian/<Vault>`. OneDrive: mark the folder "Always keep on this device" and avoid Files On-Demand. Google Drive: "not officially supported", set files "Available Offline". The help warns against using multiple sync services on one vault ("data conflicts or corruption") and points to Obsidian Sync as the official method — [Obsidian Help: Sync your notes](https://obsidian.md/help/Getting+started/Sync+your+notes+across+devices)
- Forum reports: vaults emptied in iCloud. One user deleted a vault on a phone and the deletion propagated to all devices. Another lost iCloud files unrecoverable from iCloud.com. Evicted files show up as hidden `.name.icloud` placeholders. Running iCloud and Obsidian Sync together causes fights. All of this is anecdotal — [forum: vaults disappearing from iCloud](https://forum.obsidian.md/t/vaults-notes-disappearing-from-icloud-drive/6602), [forum: files disappear from macOS](https://forum.obsidian.md/t/files-and-folders-disappear-from-macos/117162), [forum: my vault has disappeared](https://forum.obsidian.md/t/my-obsidian-vault-has-disappeared/78355)
- iCloud Drive: deleted files stay in Recently Deleted for 30 days, and permanently removed files can't be restored. Also see icloud.com/recovery → Restore Files — [Apple: If you're missing files in iCloud Drive](https://support.apple.com/en-au/111763)
- Google Drive for desktop: Mirror keeps a full local copy plus the cloud copy. Stream keeps the cloud primary with on-demand local files. A local delete equals a cloud delete into Drive Trash (30 days). These are third-party sources only — [CBackup](https://cbackup.com/articles/stream-files-vs-mirror-files.html), [infoinspired](https://infoinspired.com/how-to-guides/how-to-delete-files-on-google-drive-on-my-pc-without-affecting-the-web-stored-files/). The trash window is confirmed by [Google Workspace Updates](https://workspaceupdates.googleblog.com/2020/09/drive-trash-auto-delete-30-days.html)
- Dropbox Basic/Plus/Family: 30 days of version history and deleted-file recovery. Professional gets 180 days — [Dropbox data retention](https://help.dropbox.com/account-settings/data-retention-policy), [Dropbox version history](https://help.dropbox.com/en-us/delete-restore/version-history-overview)
- OneDrive personal: the recycle bin auto-deletes after 30 days, or after 3 days for the oldest items if the bin fills. Version history keeps the last 25 versions for personal accounts. "Files Restore" (roll back 30 days) is for Microsoft 365 subscribers only — [Microsoft: Restore your OneDrive files](https://support.microsoft.com/en-US/onedrive/restore-your-onedrive-files), [Microsoft: Restore a previous version](https://support.microsoft.com/office/159cad6d-d76e-4981-88ef-de6e96c93893)

### Inferences
- Moving the vault into iCloud or Drive would contradict the project's decision to keep it outside synced folders. It would also expose `kb` writes to placeholder files (a `.icloud` stub instead of the `.md`), which can break `kb` search and indexing.
- Protection against loss of the computer: yes, while the cloud copy is intact. Protection against accidental deletion: only within the 30-day trash window, and only if noticed. A mass deletion or corruption (a buggy agent, ransomware) syncs out within seconds.
- `kb doctor` can't easily verify freshness here. It could at most check for `.icloud` stubs inside the vault, or that the vault path is inside `~/Library/Mobile Documents` or `~/Library/CloudStorage`.

### Gaps
- I didn't fetch a Google primary help page specifically confirming the Drive-for-desktop delete propagation and the Mirror/Stream details. Third-party sources were used.
- I found no official Apple statement on `.icloud` placeholders for third-party apps on current macOS (the Obsidian help says the Optimize-storage requirement applies to macOS 14 and earlier).

## 3. Snapshot backup tools: restic, Kopia, Borg, Arq, Duplicacy

### Takeaway
For a <1 GB vault, **restic** is the most CLI-friendly choice for a Python wrapper: a single static binary, many backends including `rclone:`, password via command or env, `--json` output, and clear retention flags. **Kopia** is a close second with a GUI and sane default retention. **Borg 1.x** needs an SSH server (Borg 2 with cloud backends is still beta). **Arq** is the polished commercial macOS GUI. **Duplicacy** CLI is free for personal use. Storage cost for <1 GB is effectively $0 on B2's free 10 GB.

### Cited Findings
**restic**
- Backends: local, SFTP, REST Server, S3, MinIO and S3-compatible, Wasabi, Alibaba OSS, Swift, B2, Azure Blob, GCS, plus anything rclone supports via `rclone:<remote>:<path>`. restic starts rclone itself (`serve restic --stdio`). For B2 the docs recommend the S3-compatible API over the native B2 backend — [restic: preparing a repository](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html)
- Passwords come from `RESTIC_PASSWORD`, `--password-file`/`RESTIC_PASSWORD_FILE`, or `--password-command`/`RESTIC_PASSWORD_COMMAND`. "Losing your password means that your data is irrecoverably lost" — [restic docs](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html)
- Retention: `forget --keep-last/--keep-hourly/--keep-daily/--keep-weekly/--keep-monthly/--keep-yearly/--keep-within`. `forget` only removes snapshot references, and `prune` (or `forget --prune`) is needed to free data. `prune` locks the repo. Run `restic check` afterwards. Empty policies are refused. In append-only setups, use `--keep-within` — [restic: removing snapshots](https://restic.readthedocs.io/en/stable/060_forget.html)

**Kopia**
- Reported default global retention: latest 10, hourly 48, daily 7, weekly 4, monthly 24, annual 3. Apart from "latest", these are time spans, not counts. This is forum-reported; confirm with `kopia policy show --global` — [Kopia forum](https://kopia.discourse.group/t/understanding-global-retention-policies/564), [Kopia retention demystified](https://kopia.discourse.group/t/kopia-snapshot-retention-policies-demystified/2941)

**Borg**
- Borg 2.0 has no final release. 2.0.0b22 (changelog dated 2026-07-22) is marked "do not use on production repositories". Borg 2 uses borgstore with `file:`, `sftp:`, `rclone:` and `s3:/b2:` backends (rclone since 2.0.0b11) — [Borg 2.0 preliminary info](https://www.borgbackup.org/releases/borg-2.0.html), [AlternativeTo news 2024-10](https://alternativeto.net/news/2024/10/borgbackup-2-0-now-supports-rclone-with-over-70-cloud-providers-in-addition-to-ssh), [newreleases 2.0.0b22](https://newreleases.io/project/github/borgbackup/borg/release/2.0.0b22)
- Borg 1.x doesn't speak S3 natively. The common pattern is a local repo synced with rclone — [Linux Junkies guide](https://linuxjunkies.org/guides/offsite-backups-to-b2-r2-s3)

**Arq**
- Arq 7: $49.99 per computer, a one-time license with 12 months of updates, using your own storage. Arq Premium: $5.99/month or $59.99/year for 5 computers plus 1 TB. Both were announced to rise on 2026-09-01 to $59.99, and $6.99/month or $69.99/year, respectively — [Arq pricing](https://arqbackup.com/pricing/), [Arq store](https://store.arqbackup.com)

**Duplicacy**
- The CLI is free for personal use. Restore, check, copy and prune are free for anyone. Commercial CLI costs $50 per computer per year. The Web GUI is paid for backup (personal about $20 first year; verify) — [Duplicacy buy page](https://www.duplicacy.com/buy.html), [Duplicacy README](https://cdn.jsdelivr.net/gh/gilbertchen/duplicacy@master/README.md)

**Storage cost**
- Backblaze B2 pay-as-you-go: $6.95/TB/month, first 10 GB always free. Egress is free up to 3x stored, then $0.01/GB. Class A/B/C calls are free, and Class D costs $0.004 per 10k (2,500/day free). No minimum storage duration (page viewed 2026-10-10, no effective date shown) — [Backblaze B2 pricing](https://www.backblaze.com/cloud-storage/pricing)

### Inferences
- Snapshot tools invert the deletion-propagation problem: a local deletion only affects new snapshots, and old snapshots keep the file until retention prunes them. That makes them true backup, unlike sync.
- A restic recipe for `kb`: `restic -r rclone:gdrive:kb-restic init` (or `-r s3:s3.<region>.backblazeb2.com/<bucket>`). Back up with `restic backup ~/Knowledge/main --tag kb --json`, prune with `restic forget --keep-hourly 24 --keep-daily 30 --keep-weekly 12 --keep-monthly 24 --prune`, and restore one note with `restic restore latest --target /tmp/r --include "/Users/<u>/Knowledge/main/path/note.md"` (or `restic dump latest <path>`). For `kb doctor`, run `restic snapshots --latest 1 --json` and compare the `time` field to now.
- Password storage for `kb`: put the repo password in macOS Keychain and pass `--password-command "security find-generic-password -s kb-restic -w"`. This avoids plaintext in config.
- restic over `rclone:gdrive:` keeps the same Google OAuth burden as the baseline. Using B2 instead swaps it for a B2 account, application key and bucket, with the data free under 10 GB.
- Complexity ranking for an MVP called from Python: restic ≈ Kopia (single binary, JSON output) < Duplicacy (CLI, less common) < Borg (Python package with SSH/server requirement, Borg 2 still beta). Arq is GUI-only for configuration, so `kb` can't drive it and could at most detect it.

### Gaps
- I didn't fetch Kopia's official retention or encryption docs (the URL 404'd). Defaults are from forum posts.
- I didn't verify whether Arq's 2026-09-01 price rise took effect, current restic/Kopia version numbers, or exact Kopia JSON-output flags.
- I didn't verify whether B2's account signup requires a payment card for the free 10 GB.

## 4. Time Machine as backup and as an MVP

### Takeaway
Time Machine backs up the whole Mac (home folder included unless excluded) hourly to an external disk or NAS, keeping hourly backups for 24 h, daily for a month and weekly until the disk is full. Local APFS snapshots live only 24 h and sit on the same disk. It protects well against accidental deletion and damage, but **only against loss of the computer if the backup disk is kept elsewhere**. A typical external disk next to the laptop doesn't cover theft, fire or ransomware.

### Cited Findings
- Hourly backups for the past 24 hours, daily for the past month, weekly for all previous months. The oldest are deleted when the disk is full. Since Ventura the frequency can be changed (Options → Back up frequency) — [Wikipedia: Time Machine](https://en.wikipedia.org/wiki/Time_Machine_(macOS)), [Apple Community quoting Apple](https://discussions.apple.com/thread/254406208)
- Local snapshots: about hourly snapshots of the startup disk, each kept 24 h, plus one snapshot of the last successful backup until space is needed. They exist only on APFS and only when "Back Up Automatically" is on — [Apple: About Time Machine local snapshots](https://support.apple.com/102154), [Mac User Guide](https://support.apple.com/guide/mac-help/about-time-machine-local-snapshots-mh35933/15.0/mac/15.0)
- A user report (not official) says that with Time Machine set to manual, no local snapshots are created — [Apple Community](https://discussions.apple.com/thread/254406208)
- tmutil: `latestbackup`, `listbackups`, `restore [-v] src ... dst`, `listlocalsnapshots /`, `localsnapshot`, `addexclusion`, `isexcluded <path>`, `destinationinfo`, `startbackup`. ss64 states that `latestbackup` and `listbackups` require root and Full Disk Access, and `restore` may require them — [ss64 tmutil](https://ss64.com/mac/tmutil.html)

### Inferences
- `~/Knowledge/main` is covered by default, since Time Machine backs up the home folder unless excluded. `kb doctor` can confirm with `tmutil isexcluded ~/Knowledge/main`, `tmutil destinationinfo` (is any destination configured?) and `tmutil latestbackup` (freshness). Because of the Full Disk Access/root requirement, `kb doctor` should treat failures as "unknown", not "no backup".
- Restoring one note: in Finder, use Enter Time Machine. Or run `tmutil restore /Volumes/<TM>/<…>/Knowledge/main/note.md ~/Knowledge/main/`.
- "Time Machine plus local history" is a reasonable MVP for the accidental deletion or damage risk, and costs zero setup if Time Machine already runs. It doesn't meet the "loss of computer" requirement unless the disk lives elsewhere or is a network or offsite target. Many laptop users have no Time Machine disk at all, so `kb doctor` should warn when `destinationinfo` shows none.
- Local snapshots alone (24 h, same disk) are no backup.

### Gaps
- I didn't fetch Apple's primary "Back up your Mac with Time Machine" page. The schedule is cited via Wikipedia and an Apple Community quote.
- I didn't confirm whether `tmutil latestbackup` works without sudo for an ordinary user whose terminal has Full Disk Access on macOS 26/27. ss64 says root is required, while practitioners often run it without sudo.

## 5. The 3-2-1 rule, ransomware and sync-propagated deletion

### Takeaway
3-2-1 means three copies, two media and one offsite. For a personal vault, the practical form is: the working vault, plus Time Machine (local, versioned), plus one offsite *versioned* copy. The offsite copy must keep history. A mirror that propagates deletions doesn't count as an independent copy against deletion or ransomware.

### Cited Findings
- 3-2-1 means three copies (original plus two backups), two different media, one offsite. It originates with Peter Krogh (The DAM Book, 2005). Backblaze now calls it "a starting point" because of ransomware, and variants like 3-2-1-1-0 have appeared — [Backblaze: 3-2-1 strategy](https://www.backblaze.com/blog/the-3-2-1-backup-strategy/), [HYCU](https://www.hycu.com/blog/3-2-1-backup-rule-explained-how-it-works-why-it-matters)
- A forum lesson: a user lost iCloud files after a deletion synced, and recovery came only from a machine that hadn't synced — [Obsidian forum](https://forum.obsidian.md/t/vaults-notes-disappearing-from-icloud-drive/6602)

### Inferences
- The project's baseline (sync plus backup-dir archive) satisfies "offsite and versioned for deletes and overwrites". But anything that can authenticate as the user (malware, a confused agent with rclone access) can also delete the archive, because the same token has full write access. Snapshot tools with append-only keys (B2 application keys without delete permission, restic's append-only REST server) are stronger against ransomware. That's beyond MVP needs.
- Recommended layering: Time Machine as copy 2 (local, hourly) and one offsite versioned copy as copy 3 (rclone archive, Git remote, or restic/Kopia).

### Gaps
- I found no reliable practitioner survey specific to personal-notes backup habits, only general guides and anecdotes.

## 6. Privacy: provider access to plaintext and client-side encryption

### Takeaway
Drive, iCloud (in standard mode), Dropbox and OneDrive can technically read uploaded plaintext. Client-side options are rclone `crypt` (an overlay on any remote) or the built-in encryption of restic, Kopia, Borg, Arq and Duplicacy. All of them make the password a single point of failure.

### Cited Findings
- rclone crypt: contents use NaCl SecretBox (XSalsa20 plus Poly1305). File names use AES-256-EME (deterministic). Directory names are encrypted by default. File size (within 16 bytes), modtime and directory structure aren't hidden. The `obfuscate` mode "cannot be relied upon for strong protection". The crypt password in rclone.conf is only lightly obscured unless config encryption is used. Losing or changing the password makes old data undecryptable — [rclone crypt](https://rclone.org/crypt/)
- restic repositories are always encrypted with a password, and a lost password means data is "irrecoverably lost" — [restic docs](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html)
- rclone config encryption uses `RCLONE_CONFIG_PASS` or `--password-command` — [rclone docs](https://rclone.org/docs/)

### Inferences
- For `kb sync`, wrapping the Drive remote in crypt (`gdrive-crypt:` → `gdrive:kb-enc`) is possible, but it removes the "open the note in Drive web UI" restore path. Restore then always goes through rclone. For an MVP, plaintext with the `drive.file` scope is a defensible trade-off. Offer crypt as an option.
- Store secrets (crypt password, restic password) in macOS Keychain via `security find-generic-password -w`, used as `--password-command`.

### Gaps
- I didn't verify whether `--backup-dir` works through a crypt remote (it should, if both paths are on the same crypt remote; unconfirmed).
- I didn't research iCloud Advanced Data Protection (end-to-end encryption for iCloud Drive) in this pass.

## 7. Per-option matrix: deletion propagation, single-note restore, freshness check for `kb doctor`

### Takeaway
Only snapshot-style mechanisms (Time Machine, restic/Kopia/Arq/Duplicacy, Git) and `sync --backup-dir` keep a deleted note beyond about 30 days. Each option exposes a machine-checkable "last success" signal except synced folders.

### Cited Findings
(Facts are from the sections above; sources are cited there.)
- rclone `sync` without backup-dir propagates deletions to Drive trash (30 days) — [rclone Drive](https://rclone.org/drive/), [Workspace Updates](https://workspaceupdates.googleblog.com/2020/09/drive-trash-auto-delete-30-days.html)
- `sync --backup-dir` moves deleted and overwritten files into the archive dir — [rclone docs](https://rclone.org/docs/)
- iCloud, Dropbox Basic and OneDrive personal recover deletions for 30 days — [Apple](https://support.apple.com/en-au/111763), [Dropbox](https://help.dropbox.com/account-settings/data-retention-policy), [Microsoft](https://support.microsoft.com/en-US/onedrive/restore-your-onedrive-files)
- Time Machine keeps hourly/daily/weekly versions until the disk is full — [Wikipedia](https://en.wikipedia.org/wiki/Time_Machine_(macOS))

### Inferences
| Option | Local delete propagates? | Restore single note | Freshness check for `kb doctor` | Setup burden |
|---|---|---|---|---|
| `rclone copy` → Drive | No (copy never deletes) | Download from Drive or `rclone copy` back | `kb`'s own last-run stamp plus `rclone lsd` auth probe | High (own GCP OAuth client, publish app) |
| `rclone sync` → Drive | Yes, to Drive trash for 30 days | Drive Trash | same | High |
| `rclone sync --backup-dir` → Drive (baseline) | Mirror yes, but file preserved in archive indefinitely | `rclone copy gdrive:kb/archive/<stamp>/…` or web UI | same | High |
| Vault in iCloud / Drive desktop / Dropbox / OneDrive | Yes, immediately | Provider trash or versions, about 30 days (OneDrive: 25 versions) | Hard. Only detect location or `.icloud` stubs | Low, but conflicts with Obsidian/`kb` |
| restic/Kopia → B2/S3/rclone | No (old snapshots keep it until pruned) | `restic restore latest --include <path>` / `restic dump` | `restic snapshots --latest 1 --json` | Medium (binary, repo, password, B2 key) |
| Arq | No | Arq GUI | Not scriptable (detect app only) | Low–medium (GUI, $) |
| Time Machine | No (versions remain) | Finder TM browser or `tmutil restore` | `tmutil latestbackup` / `destinationinfo` / `isexcluded` (may need Full Disk Access) | Zero if already set up, needs a disk |

- MVP judgement: "Time Machine plus local history only" is the cheapest and covers deletion and damage, but not computer loss (unless the disk is offsite). Rclone-to-Drive with backup-dir covers computer loss, but in 2026 it needs every user to create and publish their own Google OAuth client. A restic/Kopia repo on B2 (free under 10 GB) covers both with lower Google friction, at the cost of a password and a B2 account.

### Gaps
- I didn't compare against Git plus a private remote here (covered by another researcher).
- I didn't verify the exact JSON fields of `restic snapshots --json` or Kopia's equivalent.
