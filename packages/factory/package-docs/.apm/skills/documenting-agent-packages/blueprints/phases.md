# Phases in detail

Each phase: what runs, what "done" means, and what to do when it fails. Back to [SKILL.md](../SKILL.md).

## Contents

- [D0 Preflight](#d0-preflight)
- [D1 Coverage](#d1-coverage)
- [D2 Plan](#d2-plan)
- [D3 Fan-out](#d3-fan-out)
- [D4 Generate and check](#d4-generate-and-check)
- [D5 Consolidate](#d5-consolidate)
- [D6 Report](#d6-report)

## D0 Preflight

1. Resolve the repository root and read `docs-catalog.json` if present. Print the layout in use (packages folder,
   bundles folder, docs folder, required pages). A missing folder stops the run with a plain message.
2. `git status --short`. Record it. Foreign uncommitted changes are expected: note them and never touch them.
3. **Snapshot the working tree** (skip this in `mode=check`, which writes nothing) so nothing a writer does can lose uncommitted work. Start from the current
   commit and add the working tree on top, in a temporary index, so the real index is untouched:

   ```text
   GIT_INDEX_FILE=<tmp> git read-tree HEAD
   GIT_INDEX_FILE=<tmp> git add -A
   tree=$(GIT_INDEX_FILE=<tmp> git write-tree)
   git update-ref refs/backup/pre-docs-<date> $(git commit-tree $tree -p HEAD -m "backup: working tree before documenting")
   ```

   Starting from `read-tree HEAD` matters: a snapshot from an empty index skips tracked files that match
   `.gitignore` and records default file modes. See [lessons](lessons.md).
4. Run `docs_catalog.py --root <repo> --check` and note which generated blocks are already stale, so you can
   tell later which staleness is yours.

**Done when** the layout is printed, the snapshot ref exists and `git status` is recorded.

## D1 Coverage

1. `python scripts/docs_catalog.py --root <repo> --check-manuals`. Read the coverage table and the problem list.
2. Present gaps per package: missing sections, entry points with no section, parameters missing from a table.
3. `check_manual.py --all --skip-stale` adds structure, link and presence problems.

**Done when** you can say, per package, whether its manual is complete. `mode=check` stops here and changes nothing.

## D2 Plan

1. Select packages from the mode: `package=` as given, `changed since=` from `git diff --name-only <ref>` mapped to
   package folders, `all`, or `bundles`.
2. Group by family, at most `writers` groups, packages with many commands (for example a family of 15 siblings)
   getting their own writer.
3. For each group, list the files the writer may write. Check that no file is in two groups.
4. Show the plan: packages per writer, files that will change, the checks that will run, and the snapshot ref.

**Gate G1.** Wait for the user's yes. A change to the plan goes back through step 3.

## D3 Fan-out

1. Fill [TEMPLATE.WORK-ORDER.md](../assets/TEMPLATE.WORK-ORDER.md) per group.
2. Start all writers in one message with the Agent tool, `model: "sonnet"`. Parallel, because their files are disjoint.
3. A writer that returns `needs-input` has its questions shown to the user, answered, and is started again with the answers.
4. When every writer has returned, `git status` must show changes only in the files named in the assignments.

**Done when** every writer returned and no file outside the assignments changed. If one did, stop and show it.

## D4 Generate and check

1. `python scripts/docs_catalog.py --root <repo>` once, now that no writer is running. It fills `contents`,
   `installation`, `agents-reference` and the docs tables.
2. `docs_catalog.py --check`, `docs_catalog.py --check-manuals`, `check_manual.py --all`, `check_links.py`.
3. If the repository has a sensitive-data check, run it too.
4. A problem in a manual goes back to the writer that owns it, with the exact message. At most 2 rounds, then show
   the problem to the user.

**Done when** all four checks exit 0.

## D5 Consolidate

1. Merge the writers' defect lists into the known-issues page using
   [TEMPLATE.KNOWN-SOURCE-ISSUES.md](../assets/TEMPLATE.KNOWN-SOURCE-ISSUES.md): where, what, how serious.
2. Mark each item *checked* (you verified it against the file) or *reported* (a writer's claim). Verify the
   few that decide behavior or safety yourself before listing them first.
3. Never fix a source defect in this phase.

**Gate G2.** Show the list. The user decides which defects to fix, in another task.

## D6 Report

Coverage before and after, files changed, items left *unverified*, source defects found, and the checks that
passed. Propose a commit split, for example scripts, docs pages, package manuals, bundle READMEs. Name the
snapshot ref. Do not commit.
