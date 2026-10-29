# E9 - Final gate, archive and commit

Back to [SKILL.md](../SKILL.md). The gate is computed by scripts; I do not judge "looks done".

## Gate checklist (all must be true)

Run in this order and keep the outputs:

```bash
python <scripts>/check_records.py <handoff> --profile <profile> [--override <ov>]   # exit 0
python <scripts>/detect_drift.py <repo> --change <handoff> --include-worktree      # exit 0 (drift = 0; agents leave code uncommitted until E9, so without the flag the check is vacuous)
python <scripts>/board.py <handoff> --profile <profile> [--override <ov>]           # NEXT: final-gate
openspec validate <id> --type change --strict --json --no-interactive               # exit 0
mvn -q verify                                                                       # exit 0 (run by me)
```

| Condition | Source |
|---|---|
| `verify-E1`, `verify-E2`, `verify-E3`, `verify-E4`, the latest E7 verify (`verify-E7`, or `verify-E7-<nn>` after a gap acceptance) all `pass` (each by a different agent than the producer) | records; the board enforces only `verify-E7`: I check E1-E4 with `ls` / `check_records.py` (register L6) |
| every task `done`, every review `approved`, no open HIGH | `board.py` |
| drift = 0, pending deltas = 0, synced SHA = HEAD or equivalent | `detect_drift.py`, `board.py` |
| no open blocking question, no `open` escalation | records |
| approvals recorded for E2, E3, E5, each apply, each delta | `status.md` `## Approvals` |

Any false condition: the gate blocks. Say which one and the command that returns to the right phase (E8 for drift, E6 for a task, E7 for deploy). Never edit a record or `status.md` to turn it green.

## After the gate

1. Show the user a summary: requirements delivered, ADRs added/superseded, deltas accepted, deploy version/alias, observability verdict, the deploy-report `## Cleanup proposal` (proposal only; the user runs it; never blocks E9), `(unverified)` items still relied on.
2. **Archive** (user-approved): ask explicitly. On "yes" (verbatim in Approvals, `gate=E9-archive`): `openspec archive <id> --yes`, then `openspec validate --specs --strict --json --no-interactive`. The change folder, with `handoff/` inside, moves whole to `openspec/changes/archive/<date>-<id>/` (exact folder naming: openspec skill; archive with incomplete tasks behaves per its doc-vs-validator blueprint: check, do not assume).
3. **Commit** (user-approved, separate question): propose a plan of path groups (code, infra, specs + archived change); never `git add -A`; commit only on approval; **never push** (the user pushes).
4. Record the final SHA with `board.py --sync-sha` before archiving if the archive moves files that `detect_drift.py` reads.

## Not archived

If the user declines the archive: leave the change open, state the open items, stop. Do not retry the question in the same turn.

## Resume after interruption

Rebuild state with the three scripts, read `## Approvals`, list the latest record per task, follow `NEXT:`. Do not trust a summary from a previous conversation.
