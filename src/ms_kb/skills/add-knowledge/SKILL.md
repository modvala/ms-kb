---
name: add-knowledge
description: >-
  Save the outcomes of the current conversation to the user's personal knowledge
  base (an Obsidian vault managed by the `kb` CLI): a learning-session summary
  plus new or extended concept, research and source notes, without duplicates.
  Use only when the user explicitly asks to save, record or add what was learned
  to the knowledge base, or invokes add-knowledge; never on your own initiative.
metadata:
  version: "0.3.0"
  package: ms-kb
---

# add-knowledge

Collect what was learned in this conversation and save it to the user's knowledge base. The invocation itself is the permission to write. Write **only** through the `kb` CLI (`kb new`, `kb extend`). It stamps provenance, validates notes and refuses duplicates. Never create or edit note files with your own file tools.

If the user named a topic or part of the conversation, save only that. Otherwise save the whole conversation.

## 1. Check the CLI

Run `kb where`.

- If the shell says `kb` is not found, the tool directory is not on this shell's PATH. Try `~/.local/bin/kb where`; `uv tool dir --bin` prints the directory if it is elsewhere. If that works, use that full path for every `kb` command below.
- If `kb where` itself fails, stop and tell the user to run `kb setup`. Keep any `kb: warning:` lines you see later (for example "run kb install-skills") for the final report.

## 2. Collect

Go through the conversation and extract:

- the original question and why it came up;
- explanations and conclusions;
- comparisons with their criteria and date;
- sources that were actually mentioned (URLs, titles);
- open questions.

Mark every point as one of two kinds:

- **confirmed:** backed by a source that was opened in the conversation, by a test or run, or explicitly agreed by the user;
- **assumption:** discussed but not confirmed.

Never invent the content of a source that was not opened. Keep only its link.

If the beginning of the conversation looks compacted or summarized, tell the user that early details may be incomplete.

## 3. Classify

See [references/note-types.md](references/note-types.md) for the sections of each type.

- Exactly one **`learning-session`** per run: topics, conclusions, assumptions, open questions.
- A **`concept`** for each durable explanation worth reusing. Keep it to the few central concepts.
- A **`research`** note only for a dated comparison of options.
- A **`source`** note only for material that was actually read in the conversation. Otherwise the link goes into `--source` of another note.

Topics are kebab-case slugs (`agent-memory`, `rag`). Reuse topics that already exist in the vault.

## 4. Search before writing

For every concept, research or source candidate:

```bash
kb search "<title or key term>" --type concept --json
kb search --topic <topic> --json
```

Open the top hits (the `path` field) and read them. Decide:

- **extend** if a note on the same subject exists. Plan to add only what is not already written there.
- **create** if nothing matches.

## 5. Contradictions and assumptions

- If new material contradicts an existing note, do not remove or reword the old text. Append a callout to the relevant section, and add an open question about it to the session note:
  ```markdown
  > [!warning] Contradiction
  > Earlier: "<old claim>". In [[<session note>]]: "<new claim>" because <reason>.
  ```
- Assumptions never go into concept notes as fact. Put them in the session's `## Assumptions (not confirmed)` section, or into a concept as a `> [!question] Assumption` callout.

## 6. Plan gate for existing notes

If you are going to extend at least one existing note, first show a short plan and **wait for the user's yes**:

| Note | Action | Sections | What is added |
|---|---|---|---|
| concepts/RAG.md | extend | Insights, Limitations | reranking trade-offs |
| learning-sessions/… | create | — | session summary |

Drop whatever the user rejects. If only new notes will be created, skip the plan and write.

## 7. Write

Pass bodies through stdin with a quoted heredoc. Always pass `--skill add-knowledge`.

Create the session first. Its name is `learning-sessions/<YYYY-MM-DD>-<slug>.md`. Pass `--slug` with an ASCII slug whenever the title is not in English.

```bash
kb new learning-session --title "<Title>" --slug <ascii-slug> --topic <t1> --topic <t2> \
  --related "<Concept A>" --skill add-knowledge --body-file - <<'EOF'
## Topics
...
## Conclusions
...
## Assumptions (not confirmed)
...
## Open questions
...
EOF
```

Create a concept, linking it back to the session:

```bash
kb new concept --title "<Concept>" --topic <t> --related "<session file name without .md>" \
  --source "<url>" --skill add-knowledge --body-file - <<'EOF'
## Explanation
...
## Limitations
...
EOF
```

Extend an existing note. Each `## Section` block is appended to that section, and the section is created if missing. Existing text is never changed.

```bash
kb extend "<path from kb search>" --summary "<one line: what was added>" \
  --related "<session file name>" --skill add-knowledge --body-file - <<'EOF'
## Insights
- ...
EOF
```

Rules:

- `--related` takes note names. The CLI adds them as `[[links]]` both in frontmatter and under `## Related`.
- If `kb new` says the note already exists, or that similar notes exist, extend that note instead. Use `--allow-similar` only if it is really a different subject.
- If a command fails validation, fix the arguments (usually topics or dates) and run it again.
- Use `--dry-run` when unsure. It prints the result without writing.

## 8. Learning profile

Add the session to the profile:

```bash
kb extend learning_profile.md --body-file - <<'EOF'
## Recently studied
- <YYYY-MM-DD> — [[<session file name>]]
## Open questions
- <question> — from [[<session file name>]]
EOF
```

## 9. Report

Run `kb validate <paths you touched>`. Then list for the user:

- created notes and extended notes, with sections;
- anything skipped as already present;
- assumptions and open questions that were recorded;
- `kb` warnings.

Use vault-relative paths.
