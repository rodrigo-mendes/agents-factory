---
kind: work-order
id: wo-<nn>-observability
from: building-quarkus-aws-saas
to: aws-observability
change: <change-id>
task: <task-id>                  # mode A: `spec`; mode B: the infra task; mode C: `deploy` (same task as the deploy work-order)
refs: [result-<nn>-deploy]       # mode C: the deploy-report; mode B: the architecture/infra work it extends
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Mode: A review the observability section of the spec | B write observability Terraform (offline) |
C live validation after a deploy (stage E7) | D instrumentation missing. Output: `result-<nn>-observability.md`
(kind `report`, outcome `success|partial|failed|needs-input`) at `<path>`; never a name starting with `report`.
Mode C: the record carries `role: observability-live` in its frontmatter (routes it to the debugger); mode A
carries `role: observability-review` (back to the orchestrator, never to deploy); mode B carries no `role` field. The record is not the E7 verify: `aws-lambda-debugger` mode B verifies it afterwards (`verify-E7.md`).

## Skills

- validating-aws-observability, provisioning-aws-cloudwatch-v6, provisioning-aws-xray-v6,
  monitoring-cloudwatch-observability, tracing-aws-xray
- Quarkus skills the runtime needs to read what the code emits (only if listed): logging-quarkus-lambda-v3-40,
  tracing-quarkus-lambda-v3-40, monitoring-quarkus-lambda-v3-40

## Requirements

- R1: <requirement> - observability consequence: <log field, metric, alarm, trace segment to prove>.

## Constraints

- spec (mode A): `<path to the architecture spec / observability section>`
- mode: `<A|B|C|D>`; region: `<region>`; identity: AWS profile `<name>` (never credentials in text)
- function: `<name>`; alias/version: `<alias>` / `<version>`; log group: `<name>`
- API type: `REST | HTTP | NONE` (decides which access-log and metric dimensions apply)
- smoke start (mode C): `<epoch-seconds>`, copied from `smoke_start_epoch` in the deploy-report Evidence; the window starts there
- alarm prefix: `<prefix>` (only alarms with this prefix are read or tested)
- code owner: `quarkus-lambda-integrator` (receives instrumentation proposals); profile: `coordinating-quarkus-aws-handoffs`
- dashboards: `<names, or none>`; rendering is "not provable via API": report it as such
- Terraform directory (mode B): `<path>`; offline only (`fmt -check`, `init -backend=false`, `validate`; no `plan` against a real backend)

Approval lines (the orchestrator pastes the user's approval verbatim, one per line; absent = not allowed):

```
approval: alarm-test alarm=<name> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
approval: logs-insights scope=<log-group or "xray"> window=<minutes> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
```

## Limits

- build_attempts: <effective value>   (source: profile | override | args)   # the board counts failed/partial mode B reports of this task (mode A/C roles are excluded)

## Acceptance criteria

- [ ] Each pillar (logs, metrics, traces, alarms, dashboards) is `PASS | WARN | FAIL | not verified` with command and output.
- [ ] A FAIL names the skill that fixes it; nothing is fixed in mode C; no mutating AWS call without its approval line.
- [ ] `result-<nn>-observability.md` valid (kind `report`, protocol outcome; mode C: `role: observability-live`) with `## Spec impact`.
