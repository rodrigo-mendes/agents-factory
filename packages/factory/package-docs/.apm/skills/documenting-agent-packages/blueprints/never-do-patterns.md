# Never-do patterns

The 🚫 list of the skill, with what to do instead and why. Back to [SKILL.md](../SKILL.md).

## Contents

- [Generating tables while a writer runs](#generating-tables-while-a-writer-runs)
- [Committing, pushing or merging](#committing-pushing-or-merging)
- [Editing sources to make a manual pass](#editing-sources-to-make-a-manual-pass)
- [Inventing a parameter or a default](#inventing-a-parameter-or-a-default)
- [Starting writers before the plan is approved](#starting-writers-before-the-plan-is-approved)
- [Letting a writer leave its assignment](#letting-a-writer-leave-its-assignment)
- [Destructive recovery](#destructive-recovery)

## Generating tables while a writer runs

| ❌ Don't | ✅ Instead | Why |
|---|---|---|
| `python docs_catalog.py --root .` during D3 | Wait for the last writer, then run it once in D4. | It rewrites every README with markers and can overwrite a file that is half written. |

## Committing, pushing or merging

| ❌ Don't | ✅ Instead | Why |
|---|---|---|
| `git commit`, `git push`, `git merge`, `gh pr create` | Propose the split in D6 and stop. | The user owns history and remotes. |

## Editing sources to make a manual pass

| ❌ Don't | ✅ Instead | Why |
|---|---|---|
| Change a `SKILL.md`, an agent file or `apm.yml` so the manual matches it | Describe what the source says, flag the conflict, list it in the known-issues page. | The manual is a view of the sources; changing the sources hides the problem and bypasses the factory's own quality loop. |
| Edit `.claude/` | Change `packages/` and regenerate in a separate task. | `.claude/` is generated. |

## Inventing a parameter or a default

| ❌ Don't | ✅ Instead | Why |
|---|---|---|
| Write `Default: 5` because it seems usual | Write `Default: not stated`. | A guessed default becomes a fact for the reader. |
| Add an example with a flag the hint does not list | Use only parameters from the hint or the skill body. | The example would fail when typed. |

## Starting writers before the plan is approved

| ❌ Don't | ✅ Instead | Why |
|---|---|---|
| Launch writers right after D1 | Show the D2 plan and wait for the user's own yes (G1). | Writers cost time and rewrite files. |

## Letting a writer leave its assignment

| ❌ Don't | ✅ Instead | Why |
|---|---|---|
| Accept a writer's report without checking `git status` | After D3, confirm only the assigned files changed. | A writer that edits a source file silently changes behavior. |

## Destructive recovery

| ❌ Don't | ✅ Instead | Why |
|---|---|---|
| `git reset --hard`, `git clean -fd`, `git checkout -- .` to undo a bad run | Restore the affected files from the snapshot ref taken in D0. | These commands also delete the user's unrelated uncommitted work. |
