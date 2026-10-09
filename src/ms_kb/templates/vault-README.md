# Knowledge base

This folder is a personal knowledge base managed by [ms-kb](https://github.com/modvala/ms-kb).
Notes are plain Markdown with YAML frontmatter: they are readable without Obsidian, and Obsidian opens this folder as a vault.

## Layout

| Folder | Note type | File name |
|---|---|---|
| `concepts/` | `concept` | `<Title>.md` |
| `sources/` | `source` | `<Title>.md` |
| `research/` | `research` | `<slug>.md` |
| `learning-sessions/` | `learning-session` | `YYYY-MM-DD-<slug>.md` |
| `projects/` | `project` | `<Title>.md` |
| `attachments/` | images, PDFs | embedded as `![[file.png]]` |
| `templates/` | note templates | — |

`learning_profile.md` is a short summary of what you are learning, with links to the detailed notes.

## Templates in Obsidian

Settings → Core plugins → enable **Templates**, then set **Template folder location** to `templates`.
Use the "Insert template" command in a new note.

## Rules

- `kb init` adds missing folders and files and never overwrites existing ones.
- Run `kb doctor` to check the setup and `kb where` to print this folder's path.
- Do not put this folder into Git or into the ms-kb repository. The cloud copy is made by `kb sync` (coming in a later version).
