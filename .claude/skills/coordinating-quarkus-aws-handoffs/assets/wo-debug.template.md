---
kind: work-order
id: wo-<nn>-debug                # both modes (A and B); never wo-<nn>-verify
from: building-quarkus-aws-saas
to: aws-lambda-debugger
change: <change-id>
task: <task-id>                  # deploy for an E7 diagnosis (mode A) and for mode B; otherwise the diagnosed task
refs: [result-<nn>-deploy]       # mode B: also result-<nn>-observability (the producer's result it verifies)
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Mode: A diagnose | B post-deploy verification (stage E7). Read-only; no AWS mutation, no files written.
The orchestrator saves the returned record.

## Skills

- debugging-aws-lambda
- validating-aws-observability (mode B, read-only scripts only, never `trigger-alarm-test.py`)
- Quarkus skills the runtime needs to read logs and traces: logging-quarkus-lambda-v3-40,
  tracing-quarkus-lambda-v3-40, developing-quarkus-amazon-lambda-v3-40

## Requirements

- R1: <requirement> - symptom or scenario to confirm.

## Constraints

- mode, function, alias/version, region, entry type (REST | HTTP API | SQS | EventBridge), UTC window
- identity: AWS profile `<name>`; symptom or deploy-report path
- pillars to check (mode B): logs, metrics, traces, alarms (state only), dashboards
- Ask-First items settled here: Logs Insights allowed? invoke: never by the debugger (a real invoke is the deployer's smoke step)?

Approval lines (the orchestrator pastes the user's approval verbatim, one per line; absent = not allowed):

```
approval: logs-insights scope=<log-group or "xray"> window=<minutes> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
approval: e7-gaps pillars=<comma list> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
```

`e7-gaps` (mode B only): the user accepted these pillars as not verified; the debugger then emits `pass` and lists them
under `## Gaps` as accepted. Without the line a not-verified pillar keeps `fail`.

## Record name

- Mode A: `diagnosis-<nn>`.
- Mode B: `verify-E7` on the first run; `verify-E7-<nn>` on the relaunch after the user's gap acceptance
  (re-verification name of the profile, `verify-{stage}-{nn}.md`).

## Limits

- debug_rounds: <value>   (not a profile limit: the orchestrator counts diagnosis records per failure
  and escalates by hand when it reaches deploy_cycles)

## Acceptance criteria

- [ ] Mode A: one root cause with branch letter and allowlisted-command evidence, or `not determined`.
- [ ] Mode B: record `verify-E7` (gap-acceptance relaunch: `verify-E7-<nn>`) (kind `verify`, `outcome: pass | fail`); `## Criteria` lists every pillar `[x]`/`[ ]` and
  `## Evidence` the command and output; a pillar not verified is `[ ]` with the reason.
- [ ] Record returned inline with the frontmatter and sections of its kind; the orchestrator saves it unchanged
  (adds only `task`).
