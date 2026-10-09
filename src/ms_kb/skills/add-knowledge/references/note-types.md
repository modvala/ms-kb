# Note types for add-knowledge

The full schema lives in `docs/note-schema-v0.md` in the ms-kb repository. This page summarizes what the skill needs. `kb new` builds the frontmatter itself, so pass the fields as options and write only the body sections.

| Type | Use for | `kb new` options beyond `--title`, `--topic` | Body sections (`## …`) |
|---|---|---|---|
| `learning-session` | The summary of this conversation; one per run | `--slug` (ASCII), `--session-date` (default today) | Topics; Conclusions; Assumptions (not confirmed); Open questions; Related |
| `concept` | A durable explanation, in your own words | — | Explanation; Diagram (Mermaid, only if it helps); Limitations; Insights; Related |
| `research` | A comparison of options that is valid as of a date | `--slug`, `--as-of` (default today), at least one `--source` | Question and scope; Comparison; Findings; Limitations and open questions; Sources; Related |
| `source` | An article or document actually read in the conversation | `--url` (required) | Summary; Key takeaways; Why I saved it; Source; Related |
| `project` | Knowledge gained in a practical project | — | Goal; Decisions and reasons; Knowledge gained; Insights; External links |

**File names.** Concept, source and project notes are named after the title (`concepts/RAG.md`), so `[[RAG]]` links work. Research notes are `research/<slug>.md`. Sessions are `learning-sessions/YYYY-MM-DD-<slug>.md`.

**Topics** are kebab-case ASCII slugs: lowercase words joined by `-`.

**Diagrams.** Use fenced `mermaid` blocks. If an image matters, explain its meaning in text.

**Insights** (observations from practice) go in the `## Insights` section of a concept or project note, not in a separate note.

**Callouts** for content that is not plain fact:

```markdown
> [!question] Assumption
> Not confirmed in the conversation: ...

> [!warning] Contradiction
> Earlier: "...". In [[2026-10-09-rag-session]]: "..." because ...
```
