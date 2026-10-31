# Shared files: one run at a time

Back to [SKILL.md](../../SKILL.md). Why: in past runs one package's change to the root `apm.yml` re-keyed packages owned by other runs and broke their install; a skill moved by one run was deleted from another by `apm`; every run rewrote the documented counts, so earlier numbers went stale. A second session added a package to the root `apm.yml` while another run was installing, and the install hung.

## What is shared

Root `apm.yml`, `apm.lock.yaml`, `CLAUDE.md`, `README.md`, `docs/`, `.claude/` (generated), the repo-root `scripts/`, and any package this run did not create.

## Rules

1. Touch shared files only in P5 (root `apm.yml` entry, when needed for the install rehearsal) and P8/P9. Never in P3/P4/P6 fix briefs; a worker that needs one returns a request instead.
2. Before the first change: `state_event.py <slug> shared-lock` (writes `workspace/.shared.lock`; a lock held by another slug refuses). Then `git fetch` and `git status`: if the base branch moved or foreign changes appear in shared files, stop and show them to the user.
3. After each change: `state_event.py <slug> touch <path> --note "<why>"` (HEAD vs working-copy hash). Every touched path must appear in `plan/commit-plan.json`; `check_state.py` fails G3 otherwise.
4. Documented counts are written once, in P8, from `scripts/check_counts.py`; never from a previous run's numbers.
5. Release after P9 with `shared-unlock`. In P5 release right after the rehearsal install, and take the lock again in P8.
6. A lock older than 12 h may be freed with `shared-unlock --stale`; that is logged, and the user is told whose lock it was.
7. Changing another run's package (rename, move, remove a file) is an Ask-First item: show the diff and that run's slug at G3.
