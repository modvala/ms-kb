---
name: kb-recall
description: >-
  Recall what the user has already studied from their personal knowledge base
  (an Obsidian vault managed by the `kb` CLI): past learning sessions, concepts,
  research, conclusions and open questions. Use when the user, in any language, wants to continue
  earlier learning ("let's continue with X", "where did we stop"), asks what
  they have already covered, studied or concluded, or asks to be reminded what
  was unclear. Read-only. Do not use for general questions that need no
  personal context.
metadata:
  version: "0.5.0"
  package: ms-kb
---

# kb-recall

Find what the user has already learned on a topic in their knowledge base, and continue from there. This skill only reads. Never create, edit, move or delete vault files, never run `git` in the vault, and never run `kb new`, `kb extend`, `kb restore` or `kb sync` here.

Read only what is relevant: the learning profile and a few notes found by search, never the whole vault.

## 1. Check the CLI

Run `kb where`. It prints the vault path.

- If the shell says `kb` is not found, the tool directory is not on this shell's PATH. Try `~/.local/bin/kb where`; `uv tool dir --bin` prints the directory if it is elsewhere. If that works, use that full path for every `kb` command below.
- If `kb where` fails, the knowledge base is not available. Tell the user this in one line, for example: "I couldn't reach your knowledge base (`kb where` failed), so this is based only on our current conversation." Then answer from the conversation alone. Never guess what the notes might say.

## 2. Read the learning profile

Read `<vault>/learning_profile.md`, where `<vault>` is the path printed by `kb where`. It is short. It has these sections:

- `## Current directions`
- `## Known topics`: links to concept notes
- `## Recently studied`: dated links to learning sessions
- `## Open questions`

Use it to pick the note names, topic slugs and sessions that match the request. If the profile is missing, skip this step and go straight to search.

## 3. Search

Make 1–3 searches. Always pass `--json`. Search terms must all occur, so use one or two key words, not a sentence.

| Request | Search first |
|---|---|
| "Let's continue with X", "where did we stop" | `kb search --topic <x> --type learning-session --json` (with no terms, the newest come first), then `kb search "<x>" --type concept --json` |
| "How does X work, as I learned it" | `kb search "<x>" --type concept --json` |
| "What did I compare / decide about X" | `kb search "<x>" --type research --json` |
| "What was unclear", "what have I covered" | the profile's `## Open questions` and `## Recently studied`, then the sessions they link to |

Topics are kebab-case slugs (`agent-memory`). If `--topic` finds nothing, retry with a text term. To find notes that link to a note: `kb search --field "related=[[<Note name>]]" --json`.

## 4. Read the notes

Open the best hits by the `path` field, up to about 5 notes. Prefer the most recent learning sessions and the central concepts. Read first:

- learning-session: `## Conclusions`, `## Assumptions (not confirmed)`, `## Open questions`;
- concept: `## Explanation`, `## Limitations`, `## Insights`, any `> [!warning] Contradiction` or `> [!question] Assumption` callouts;
- research: the `as_of` date, `## Findings`, `## Limitations and open questions`.

Follow a `related` link only when the request clearly needs it.

## 5. Answer

Continue the conversation grounded in what you read:

- what was already studied and the main conclusions;
- what was left open or unclear;
- a proposed next step, starting from the open questions;
- the notes you used, as vault-relative paths (`concepts/RAG.md`).

Rules:

- Keep the notes' assumptions and contradictions marked as such. Never present them as confirmed.
- A research note is valid as of its `as_of` date. Say so if it may be outdated.
- Keep what comes from the notes separate from what you add now.

## 6. Nothing found

If the profile and the searches find nothing on the topic, say so plainly ("I found nothing about X in your knowledge base") and continue the explanation from scratch. Never invent a learning history, past sessions or what the user "already knows".

## 7. After the conversation

Do not save anything. If the conversation produces something worth keeping, you may suggest that the user run `add-knowledge` at the end.
