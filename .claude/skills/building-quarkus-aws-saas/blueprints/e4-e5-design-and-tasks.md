# E4 design and E5 tasks

Back to [SKILL.md](../SKILL.md). Precondition: E2 and E3 accepted (verifies `pass` + user approvals recorded).

## E4 - Design of the change (`openspec/changes/<id>/design.md`)

Links E3 to E2. Content (orchestrator writes):

| Section | Content |
|---|---|
| Requirement map | table: `R*` -> E2 component(s) -> ADR(s) -> skill(s) that carry the technical facts |
| Flow | request/event path per scenario group (API Gateway -> Lambda -> data/events); where tenant identity comes from (token claims) |
| Architecture delta | present only if the change alters E2: new service, tenancy, runtime; plus the new ADR (re-enter [E2](e2-architecture-and-adrs.md) acceptance) |
| Observability impact | new log fields, metrics, alarms, dashboards the change needs (feeds an `aws-observability` task) |
| Risks | each `(unverified)` / `(medium confidence)` item the design relies on, with the skill that tags it |

**Acceptance E4:** every `R*` of the change maps to E2 components; every architecture change has delta + ADR.
**Verifier:** `aws-architect` (brief in [worker briefs](worker-briefs.md#aws-architect)); I save the inline answer as `verify-E4.md` (`from: aws-architect`).
`fail` -> fix the design (not the verifier's record) and re-run.

## E5 - Tasks (`tasks.md` + one work-order per task)

Each task row: ID (`T1`), requirements covered (`R1, R2`), E2 component, owner role (`code`, `stripe`, `infra`, `observability`), dependencies, skills the work-order must list.
Size rule: a task fits one I0-I9 cycle (one endpoint or one event consumer, one Terraform module set, one observability set).
Keep OpenSpec's own checkbox convention in `tasks.md` (the openspec apply tracking reads it, see the openspec skill); IDs live in the task text.

### Choosing owner and skills

| Task type | Owner | Skills the work-order lists (see [knowledge map](knowledge-map.md)) |
|---|---|---|
| Lambda handler / HTTP endpoint | `quarkus-lambda-integrator` | `developing-quarkus-amazon-lambda-http-v3-40` (HTTP endpoint: also `developing-quarkus-rest-v3-40`; HTTP or REST variant per the API ADR), `testing-quarkus-amazon-lambda-v3-40`, `developing-quarkus-junit-v3-40`, `refactoring-quarkus-java`, `structuring-quarkus-lambda-projects` |
| Cognito-secured resource | same | + `securing-quarkus-lambda-cognito-v3-40` |
| DynamoDB / S3 access | same | + `integrating-quarkus-amazon-data-v3-40` |
| SQS / SNS / EventBridge consumer | same | + `integrating-quarkus-amazon-messaging-v3-40` |
| Instrumentation in code | same | + `logging-`, `tracing-`, `monitoring-quarkus-lambda-v3-40` (or umbrella `observing-quarkus-lambda`) |
| Stripe | `stripe-integrator` | + `integrating-stripe-quarkus-v3-40`, stripe-java 34 skills |
| Terraform | `aws-terraform-engineer` | matching `provisioning-aws-<service>-v6` |
| CloudWatch / X-Ray / dashboards / alarms | `aws-observability` | `validating-aws-observability`, `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`, `monitoring-cloudwatch-observability` |
| LangChain4j / AI | `quarkus-lambda-integrator` | + `integrating-quarkus-langchain4j-v1-15` (pre-release 1.15.0.CR1); create the task only after the user's yes to its Ask First D1; record it under `## Approvals` as `gate=D1-langchain4j` (verbatim words) and write `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)` in the work-order's settles line |

### Work-order per task

Write `wo-NN-<role>.md` from the profile template (`coordinating-quarkus-aws-handoffs/assets/wo-*.template.md`): required sections
Scope, Skills, Requirements (with scenarios), Constraints (ADR paths, `limits`, `coverage_min`), Acceptance criteria. Frontmatter: `kind: work-order`,
`status: pending`, `from: building-quarkus-aws-saas`, `to: <agent>`, `change`, `task`, `requirements`, `createdAt` real UTC (`date -u +%Y-%m-%dT%H:%M:%SZ`).
Then `check_records.py`.

### Acceptance E5

1. Every `R*` of the change is covered by >= 1 task (**manual check by me**: list `R*` ids from the delta specs, list `requirements:` of all work-orders; the board does not read `tasks.md`, see [risks](unverified-and-risks.md)).
2. Every task has owner, skills, dependencies; no dependency cycle (check by reading the table).
3. `board.py` runs without error and shows all tasks `pending`.
4. The user approves the task list (verbatim, `gate=E5`) before the first launch.

### E5 drift baseline (after the approval, before the first work-order)

`detect_drift.py` exits 1 until a `lastSyncedSha` exists, and only `board.py --sync-sha` sets it. Right after the task-list approval and **before the first work-order** run:

```
python <scripts>/board.py <handoff-dir> --profile <profile> --sync-sha $(git rev-parse HEAD)
```

Record it under `## Approvals` as `gate=E5-baseline` (`subject=<sha>`; the user's words are the E5 approval just given; the baseline hides no drift because no code of this change exists yet). Later `--sync-sha` calls happen only after an accepted delta ([E8](e8-reverse-sync.md)).

Independent tasks may run in parallel (<= 4, disjoint files); dependent ones in order.
