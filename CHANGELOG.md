# Release history

Versioning policy and migration path: [docs/releases.md](docs/releases.md).

## 0.7.0 — 2026-11-02

Closes roadmap stages 5 and 6 in one release, because their code and skills were built together; there is no v0.6.0.

### Added

- Topic pages: `kb new topic`, one current page per topic with fixed sections and a protected `## In my words`.
- `kb rewrite`: an approved diff with a report of sections, what disappears, hand-edited lines and hidden text; `--since`, the approval hash and the shrink guard.
- `kb link`, `kb my-words`, `kb index` (`--tag`, `--tags`, `--sources`, `--json`).
- Source cards: `kb new source` with `--url` or `--ref`, duplicates refused by normalized URL, "not used yet" in `kb index --sources`.
- The `save-source` skill; the review mode in `kb-recall`.
- Tags with one nesting level; `kb search --tag`, with `--topic` as an alias.
- The structural check of linked pages in `kb new --dry-run` and `kb rewrite --dry-run`.
- A warning about hidden text on every write.
- `kb history --skill --version --reason`; reasons are shown and stored in the `Kb-Reason` trailer.

### Changed

- `add-knowledge` 0.7.0 writes one topic page after one plan and no learning sessions.
- `kb-recall` 0.7.0 starts from the user's words and open questions.
- `kb search` ranks title and aliases first, then summary and tags, then the body. JSON results carry `tags` and `summary`.
- `kb extend`: `--reason` replaces `--summary` (kept as an alias); it writes no `updates` entries.
- `kb new source` creates the new card contract; `--topic` no longer applies to it.
- The profile template has `## Current directions` and `## Preferences`.

### Migration

- Run `kb init` to get `topics/` and `templates/topic.md`; until then `kb doctor` reports them as missing.
- To get the new card template, delete `templates/source.md` in the vault and run `kb init`.
- Older notes stay valid. Moving them to topic pages is a one-off with the agent (design §11.7).

## 0.5.0 and earlier

Stages 0–4: the package and `kb setup`, writing with provenance, `kb-recall`, the vault's own Git history, `kb sync`, `kb restore`, integrity checks and `kb update`. See [the v1 roadmap](docs/personal-knowledge-roadmap-v1.md).
