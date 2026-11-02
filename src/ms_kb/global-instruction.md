## Personal knowledge base (ms-kb)

The user keeps a personal knowledge base: an Obsidian vault managed by the `kb` CLI (`kb where` prints its path).

- When the user wants to continue earlier learning, asks what they have already studied, concluded, left unclear or saved as a source, or wants to be reviewed on a topic ("let's review X", "quiz me on X", "проверь меня по X"), use the `kb-recall` skill. Do not consult the knowledge base for questions that need no personal context.
- Save to the knowledge base only when the user asks, with the `add-knowledge` skill. For a source to keep for later ("save this source for later", "сохрани источник на потом"), use the `save-source` skill.
- Change the vault only through `kb`, even when other Obsidian skills are installed; never edit, move or delete vault files with other tools, and never run `git` in the vault.
