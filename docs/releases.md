---
title: "Personal Knowledge System — Versions, Releases and Migration"
document_version: "1.0"
created: "2026-11-02"
language: en
status: draft
design_ref: "personal-knowledge-design-v2.md"
design_version: "2.3"
---

# Versions, releases and migration

Implements US-23 and design §13.

## 1. What is versioned

| Version | Where | Changes when |
|---|---|---|
| Package | `version` in `pyproject.toml` and `uv.lock`; tag `vX.Y.Z` | Every release |
| Skill rules | `metadata.version` in `SKILL.md`, asserted in `tests/test_installer.py` | The rules of a skill change |
| Note schema | `document_version` of `note-schema-v1.md` | The note contract changes |
| Configuration schema | `schema_version` in `config.toml` | The configuration format changes |

Before v1.0 each roadmap stage is a minor version. From v1.0 semantic versioning applies:

- **Major:** an existing note, configuration or command stops working without a migration.
- **Minor:** a new command, flag, note type or skill rule; existing vaults keep working.
- **Patch:** a fix with no change to any contract.

## 2. Release steps

1. The stage's "Done when" criteria are met, hands-on checks included ([clients-v0.md](clients-v0.md)).
2. `CHANGELOG.md`: move "Unreleased" under the new version, with what a vault needs in "Migration".
3. A release commit "Release vX.Y.0: close roadmap stage N": bump `pyproject.toml` and `uv.lock`, mark the stage ✅ in the roadmap table and stage section.
4. Tag `vX.Y.0` and push. `skill_ref` in `created_by` links to this tag, so it must exist. CD is not used.

## 3. Migration path

**Notes.** `kb update` never touches notes, and a new contract keeps the older note types valid: readable, searchable and checked by their own contract. Moving notes to a new contract is a one-off done with the agent through `kb` commands, as in design §11.7, so every step is a reviewed commit and `kb restore` can undo it. Dropping a note type's validity needs a major version.

**Vault structure.** New folders and templates arrive through `kb init`, which adds what is missing and never overwrites; `kb doctor` reports what is missing. A template changed in the package is replaced in a vault by deleting its copy in `templates/` and running `kb init`.

**Configuration.** `schema_version` is checked at load. A change of format bumps it and ships a code path that reads the older version and rewrites it, and the change is listed under "Migration". A configuration from a newer package is refused rather than guessed at.

**State.** `installed.toml`, `vault-<kb>.json` and `drafts-<kb>/` can be rebuilt: `kb install-skills`, `kb doctor` (the manifest is seeded again) and a new dry-run.

**Rollback.** `kb update --ref vX.Y.Z` installs an earlier release. Notes written by a newer contract stay on disk; an older `kb` may report them as unknown types without changing them.
