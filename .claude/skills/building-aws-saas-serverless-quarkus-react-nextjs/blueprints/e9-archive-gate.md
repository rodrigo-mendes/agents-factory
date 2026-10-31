# E9 - Final gate, archive and commit

Back to [SKILL.md](../SKILL.md). The gate is computed by scripts; I do not judge "looks done".

## Gate checklist (all must be true)

Run in this order and keep the outputs:

```bash
python <scripts>/check_records.py <handoff> --profile <profile> [--override <ov>]   # exit 0
python <scripts>/detect_drift.py <repo> --change <handoff> --include-worktree      # exit 0 (drift = 0; agents leave code uncommitted until E9, so without the flag the check is vacuous)
python <scripts>/board.py <handoff> --profile <profile> [--override <ov>]           # NEXT: final-gate
openspec validate <id> --type change --strict --json --no-interactive               # exit 0
mvn -q verify                                                                       # exit 0 (run by me); plus pnpm build/test and terraform validate when the change has a front end or infrastructure
```

| Condition | Source |
|---|---|
| `verify-E1`, `verify-E2a`, `verify-E2b`, `verify-E2c`, `verify-E3`, `verify-E3b` (UI changes), `verify-E4-<each flow>`, `verify-E4-index`, `verify-E4-infra`, `verify-E5`, the latest `verify-E7` (or `verify-E7-<nn>` after a gap acceptance) and `verify-E7-site` (changes with a front end) all `pass` (each by a different agent than the producer) | records; the board enforces only `verify-E7`: I check the others with `ls` / `check_records.py` (register L6) |
| the last `result-NN-pipeline` of role `pipeline-cd` for prod is `success`, with its `run_url`; `gate=E7-merge` recorded | records, `gh run view` (read-only) |
| every task `done`, every review `approved`, no open HIGH | `board.py` |
| drift = 0, pending deltas = 0, synced SHA = HEAD or equivalent | `detect_drift.py`, `board.py` |
| no open blocking question, no `open` escalation | records |
| approvals recorded for E2, E3, E3b, E5, bootstrap-apply, E7-merge, prod release, each delta | `status.md` `## Approvals` |

Any false condition: the gate blocks. Say which one and the command that returns to the right phase (E8 for drift, E6 for a task, E7 for deploy). Never edit a record or `status.md` to turn it green.

## After the gate

1. Show the user a summary: requirements delivered, ADRs added/superseded, deltas accepted, the prod pipeline run (`run_url`), observability and site verdicts, any cleanup proposal found by the verifiers (proposal only; the user runs it; never blocks E9), `(unverified)` items still relied on.
2. **Archive** (user-approved): ask explicitly. On "yes" (verbatim in Approvals, `gate=E9-archive`): `openspec archive <id> --yes`, then `openspec validate --specs --strict --json --no-interactive`. The change folder, with `handoff/` inside, moves whole to `openspec/changes/archive/<date>-<id>/` (exact folder naming: openspec skill; archive with incomplete tasks behaves per its doc-vs-validator blueprint: check, do not assume).
3. **Commit** (user-approved, separate question): propose a plan of path groups (code, `frontend/`, infra, `.github/`, specs + archived change); never `git add -A`; commit only on approval; **never push** (the user pushes). The archive itself goes in a PR the user opens and merges.
4. Record the final SHA with `board.py --sync-sha` before archiving if the archive moves files that `detect_drift.py` reads.

## Two archive paths (tracker enabled)

- **Local** (default, above): I run `openspec archive <id> --yes` after the user's yes; with the tracker enabled, then `close --apply`.
- **Actions** (only if the user chose it and `--install-workflows` was applied): the user answers `/approve E9` on the change issue or answers in chat, which I record as for any gate (no `pull` involved); the `openspec-archive` workflow re-runs the final gate and opens a pull request. Prerequisite: the user has pushed the committed work first (I never push). The user merges the pull request; then I run `close --apply`.
- The gate checks above are unchanged and always re-run locally by me; a workflow result never replaces them. Detail: [tracker](tracker-github-projects.md).

## Not archived

If the user declines the archive: leave the change open, state the open items, stop. Do not retry the question in the same turn.

## Resume after interruption

Rebuild state with the three scripts, read `## Approvals`, list the latest record per task, follow `NEXT:`. Do not trust a summary from a previous conversation.
