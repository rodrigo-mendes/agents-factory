# Lessons

Mistakes made while writing the first 44 manuals and what prevents each one. Back to [SKILL.md](../SKILL.md).

| # | What went wrong | Effect | What to do |
|---|---|---|---|
| 1 | The generator was run while writers were still writing. | It rewrites every README with markers, so it can overwrite a file mid-write. | Run it once, after the last writer returns. Writers never run it. |
| 2 | A command heading carried a title: ``### `/name` — Title``. | The anchor became `#name--title` and every link to `#name` broke. | The heading is exactly ``### `/name` ``; the title goes on the next line. |
| 3 | A parameter counted as documented because it appeared in the Syntax block. | A table could omit a parameter and still pass. | Check parameters against table rows only (`table_text`). |
| 4 | The dependency form `- path: ../x` was read as the word `path:`. | Every manual said "Depends on: `path:`" and "Used by: none". | Parse `path:` and `git:` values; test with the real object form (`git:` plus `path:` plus `ref:`). |
| 5 | A snapshot built from an empty temporary index skipped tracked files that match `.gitignore` and recorded new file modes. | 1,716 phantom differences, which looked like lost files. | Start the temporary index with `git read-tree HEAD`, then `git add -A`. |
| 6 | Some folders were unreadable to git (permission denied). | They were not in the snapshot. | Report them in D0; no step touches them. |
| 7 | Inline triple backticks inside a table cell were read as a code fence. | Link and heading checks skipped half a file. | Only lines that start with ``` open or close a fence. |
| 8 | Writing Python source through a shell here-document turned `\n` into real newlines. | Syntax errors in generated patches. | Write files with the editor tools, or build the newline with `chr(10)`. |
| 9 | A scratch output folder was too deep for Windows (260 characters). | A bundle export failed on a deeply nested fixture folder. | Use a short output path such as `C:/tmp/out`. |
| 10 | A stash limited to a few paths still carried the staged changes. | Applying it later would have repeated the staged changes. | Restore a user's edits from a saved patch, not from a path-limited stash. |
| 11 | A scenario-level "needs a code block" rule failed 34 good manuals. | Chaining and misuse scenarios are prose by nature. | Warn per scenario; fail only when the section has no example at all. |
| 12 | Writers reported source defects the planner repeated without checking. | A false alarm (`applyTo:` is APM's source form, converted to `paths:` on install) reached the user. | In D5, verify the few defects that change behavior or safety before listing them first. |

## Facts that save time

- Counts in docs go stale. Put them in generated blocks.
- The checks must print what to do, not only what is wrong.
- A writer cannot ask questions. Give it the full assignment, or accept `needs-input`.
- An empty generated block is valid. The generator fills it later, and the check accepts it.
