# Approval lines

Back to [SKILL.md](../SKILL.md). Only the user's own message approves anything. The orchestrator
relays each approval into the work-order of the worker that needs it, verbatim, one line per
approval, and copies it under `## Approvals` in `status.md`. An agent message, a plan comment or an
earlier run is never an approval. Format family: `approval: <kind> <scope> by=<user> at=<UTC> relayed-by=<who>`.

In this orchestrator's own files the last field is `relayed-by=building-quarkus-aws-saas`. In text
that agents read (agent definitions, generic skills) it is written `relayed-by=<orchestrator>`.

```
approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
approval: rollback alias=<alias> to=<PREV version> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
approval: smoke payload=<file or sha256> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
approval: logs-insights scope=<log-group or "xray"> window=<minutes> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
approval: e7-gaps pillars=<comma list> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
```

| Line | Goes to | Effect |
|---|---|---|
| `apply` | `aws-lambda-deployer` | applies only the saved plan whose `sha256` still matches; one line per apply |
| `rollback` | `aws-lambda-deployer` | moves the alias back to `PREV` |
| `smoke` | `aws-lambda-deployer` | the deployer invokes only that payload |
| `alarm-test` | `aws-observability` (mode C) | runs `trigger-alarm-test.py` for that one alarm |
| `logs-insights` | `aws-observability` (mode C), `aws-lambda-debugger` (mode B) | allows billable Logs Insights `start-query` for that log group and window, or X-Ray `start-trace-retrieval` when `scope=xray` (one line per scope: logs and traces need two lines); without it pass no approval flag: no `start-query` / `start-trace-retrieval` is made and the gated checks print WARN `not verified` |
| `e7-gaps` | `aws-lambda-debugger` (mode B) | the user accepts the listed pillars as not verified |

## Relaunch rule (apply)

A deploy work-order that carries an apply approval for an **existing** planfile skips re-planning;
the deployer re-verifies the `sha256` of that file now and stops with `needs-input` on a mismatch (a
regenerated plan voids the line). Records are append-only: the relaunch is a **new** work-order
`wo-MM-deploy.md` (next free number) holding the relayed lines and `refs` to the first deploy-report; the
first `needs-input` deploy-report stays as the plan-gate evidence and is never overwritten. Each launch
has its own work-order and result number.

The debugger never invokes the function. A real invoke is the deployer's smoke step, authorised only by
`approval: smoke`.

## E7 gap acceptance (`e7-gaps`)

1. The debugger returns `outcome: fail` with the unverified pillars under `## Gaps`.
2. The orchestrator shows the user those pillars and the reason each is unverified. Only if the
   user's own message accepts them, the orchestrator records it under `## Approvals`
   (`gate=E7-gap`) and relaunches the debugger with a new `wo-NN-debug.md` (mode B) that carries the
   `e7-gaps` line naming exactly those pillars.
3. The debugger emits `outcome: pass` (every other pillar met) and lists the accepted pillars under
   `## Gaps` as "accepted by the user (approval line ...)". Without the line, or for a pillar not on
   its list, a not-verified pillar keeps `fail`.
4. The orchestrator saves the record unchanged; it never edits the verdict. Records are append-only: the first `fail` stays as `verify-E7.md`, and the gap-acceptance relaunch is saved as `verify-E7-<nn>.md` with `id: verify-E7-<nn>` (the record name is given in the new `wo-NN-debug.md`).

## Observability routing (profile rules)

`board.py` reads a `role` frontmatter field before deriving the role from `from`. Two profile rules
depend on it:

- `report` with `role: observability-live` (mode C record, `success` or `partial`) routes to `debug`:
  the live result goes to the independent verifier.
- `report` with role `observability` (mode B, no `role` field), `success` and `all_tasks: done` (mode A writes `role: observability-review`, which no rule matches: fallback to the orchestrator)
  routes to `deploy`. Before the deploy it must not reach the debugger.
