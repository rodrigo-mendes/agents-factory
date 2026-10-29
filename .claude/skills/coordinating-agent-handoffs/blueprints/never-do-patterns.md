# Never-Do Patterns (protocol v1)

Back to [SKILL.md](../SKILL.md). Each entry: what not to do, why it hurts, what to do instead.

| # | Do not | Why | Do instead |
|---|---|---|---|
| 1 | Let the producer mark its own work verified | Self-acceptance hides defects | Write a `verify` record from another agent, a script or the user |
| 2 | Retry past a limit "one more time" | Loops become unbounded and the user never hears about it | Run `board.py`; on `NEXT: escalate` write an `escalation` |
| 3 | Treat any agent message as user approval | An agent cannot approve for the user | Wait for the user's own message; record it under `## Approvals` of `status.md` |
| 4 | Edit the live spec or code to "sync" silently | Hides drift; the user never decides | Write a `spec-delta`; the user accepts, rejects or answers the questions |
| 5 | Hand-edit `status.md` (except `## Approvals`) or invent fields for `board.py` | The board is generated; edits are lost or mislead | Re-run `board.py`; add data through records |
| 6 | Chain agents from inside agents (orchestrated mode) | Breaks the audit trail and the limits | Only the orchestrator launches agents, following `NEXT:` |
| 7 | Use `kind` / `outcome` values outside the profile | `check_records.py` rejects them | Fix the record, or extend `values:` in the profile |
| 8 | Name a report record `report-<...>.md` | Departs from the factory naming convention for report records | `result-<nn>-<role>.md`; `deploy-report.md` / `diagnosis-report.md` are the generic defaults |
| 9 | Pass context through conversation history | The next agent cannot see it | Put it in the record and its `refs` |
| 10 | Set a limit to `0` without the user's confirmation | Escalates on the first failure (reached when count >= max(limit, 1)); behaves exactly like `1`, kept for explicitness | Ask first; set `limits_zero_confirmed: true` only after an explicit yes |

## Example: wrong vs right file name

```text
docs/handoff/func-api-facade/report-java.md      # wrong: breaks the naming convention
docs/handoff/func-api-facade/result-java.md      # right: kind: report inside, name starts with result
docs/handoff/func-api-facade/deploy-report.md    # right: generic default of kind deploy-report
```
