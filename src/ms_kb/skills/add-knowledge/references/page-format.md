# Topic page format

`kb` builds the frontmatter from options: `--summary`, `--tag`, `--alias`. Write only the body.

## Frontmatter values

- `summary`: one line, about 160 characters at most; `kb index` shows it.
- `tags`: 1–3 from `kb index --tags`. Lowercase ASCII words joined by `-`, one nesting level with `/` (`python/concurrency`). Tags say what a page is about, never a status.
- `aliases`: abbreviations and the topic's names in the user's language (`GIL`, `Мультипроцессинг`). Search, links and the duplicate check work through them.

## Sections

Headings stay in English and in this order; the content is in the user's language.

| Section | Content |
|---|---|
| `## Summary` | 2–5 sentences: what the topic is and the main conclusion. Required |
| `## In my words` | The user's text, verbatim. `kb` carries it over; leave it out of drafts |
| `## Key ideas` | 3–7 bullets worth remembering |
| `## Details` | Explanation, tables, Mermaid diagrams, examples, comparisons with "as of" dates |
| `## Open questions` | Unresolved questions, `Verify: …` items, contradictions that stay open with both versions |
| `## Related` | `- [[Page]] — how the topics relate` |
| `## Sources` | `- <link or title> — what it supports — checked YYYY-MM-DD`, or `- [[<Card title>]] — what it supports — checked <card's created date>` |

Sections the user added in Obsidian stay on the page. The budget is about 200 lines; past it, propose moving a subtopic to its own page in a separate run.

## Claims

- Established explanations are plain text. A claim goes to `## Open questions` as `Verify: …` only when it is doubtful, disputed or volatile (versions, defaults, dates, limits) and was not checked in the conversation.
- A source is a document opened in the conversation. A card stands for its source only for what the card says.
- Volatile values carry "as of YYYY-MM".
- A contradiction is resolved in place: the new text replaces the old, and the reason goes to `--reason`.

## Obsidian Markdown

- Links: `[[Page]]`, `[[Page#Heading]]`, `[[Page|shown text]]`. A link target must exist, as a page or an alias.
- Embeds: `![[file.png]]`, with the meaning of the image explained in text. Images live in `attachments/`, and only the user adds them.
- Callouts: `> [!note] Title`, then `> text`.
- Diagrams: a fenced `mermaid` block in `## Details`.
- Properties are the YAML frontmatter, which `kb` owns.
