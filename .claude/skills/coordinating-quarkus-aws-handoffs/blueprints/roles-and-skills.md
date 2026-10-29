# Roles and skills per work-order

Back to [SKILL.md](../SKILL.md). The orchestrator lists in each work-order's `## Skills` only what
the task needs; an agent loads those and nothing else (a needed skill that is not listed becomes a
question, outcome `needs-input`). Skill names below are the installed names (checked against the
package folders on 2026-10-28).

## Code work-order (`quarkus-lambda-integrator`)

| Task type | Skills to list |
|---|---|
| Any code task, I4/I5 | `refactoring-quarkus-java` (always) |
| Lambda handler, event function, packaging, JVM/native/SnapStart | `developing-quarkus-amazon-lambda-v3-40` |
| REST endpoint behind API Gateway | `developing-quarkus-amazon-lambda-http-v3-40`, `developing-quarkus-rest-v3-40` |
| Authenticated or role-based endpoint | `securing-quarkus-lambda-cognito-v3-40` |
| DynamoDB or S3 access | `integrating-quarkus-amazon-data-v3-40` |
| SQS / SNS / EventBridge consumer or producer, SSM/Secrets config | `integrating-quarkus-amazon-messaging-v3-40` |
| Tests (every code task) | `testing-quarkus-amazon-lambda-v3-40`, `developing-quarkus-junit-v3-40` |
| CDI wiring | `developing-quarkus-arc-v3-40` |
| Logging / tracing / metrics in code | `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40`, or the umbrella `observing-quarkus-lambda` |
| New project layout | `structuring-quarkus-lambda-projects` |
| LLM calls (AI services with OpenAI, Anthropic, Bedrock) | `integrating-quarkus-langchain4j-v1-15` (locked to the 1.15.0.CR1 pre-release; list it only after the user's yes to its Ask First D1, recorded under `## Approvals` as `gate=D1-langchain4j` (verbatim words) and written in the code work-order's settles line as `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`) |

## Stripe work-order (`stripe-integrator`, review by `stripe-advisor`)

`integrating-stripe-quarkus-v3-40` (+ the Stripe Java skills the work-order names), plus the same
Quarkus skills as a code task for the endpoint (`developing-quarkus-amazon-lambda-http-v3-40`,
`securing-quarkus-lambda-cognito-v3-40` when the route is authenticated). The raw webhook body must
stay intact for the signature (see the Stripe skill). Review order: `stripe-advisor` first;
`quarkus-code-reviewer` only after the advisor's review is `approved`. Hold: right after the advisor's
`approved` and before `board.py`, the orchestrator writes the second review work-order with `status: pending`;
the task's work-orders are set `done` only after the second `approved`, so `all_tasks: done` cannot fire
`NEXT: deploy` early; any `changes-requested` goes back to
`stripe-integrator` before the other review runs. Each `changes-requested` is one `review_rounds` round
(review records with that outcome per task), so a project may raise `limits.review_rounds` for Stripe tasks
in `openspec/handoff-profile.yaml`.

## Terraform work-order (`aws-terraform-engineer`)

The work-order carries the engineer's closed requirement (services, root vs module, region/account scope,
naming and tags, state backend or "no backend", mocked test wanted); it runs offline checks only and never
plans (the deployer plans in E7). One `provisioning-aws-<service>-v6` per service in the task. Names present in the repo:
`lambda`, `api-gateway`, `iam`, `dynamodb`, `s3`, `cognito`, `sqs`, `sns`, `eventbridge`, `kms`,
`secrets-manager`, `parameter-store`, `vpc`, `waf`, `cloudfront`, `acm`, `route53`, `step-functions`,
`ses`, `shield`, `cloudtrail`, `cost-management`, `organizations`, `sam`, `cloudwatch`, `xray`
(each `provisioning-aws-<name>-v6`). Log groups, alarms, dashboards and X-Ray groups belong to the
observability work-order, not to Terraform tasks.

## Review work-order (`quarkus-code-reviewer`)

`refactoring-quarkus-java` (reviewer checklist) + every skill the code work-order listed (their
Never-Do items are the review criteria) + the accepted ADRs. Stripe: also `integrating-stripe-quarkus-v3-40`
for `stripe-advisor`, who reviews first (sequential, see above). Design changes: a second review by `aws-architect` (separate work-order).
The review work-order's Constraints carry the code work-order's settles line copied verbatim (e.g.
`D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)` when `integrating-quarkus-langchain4j-v1-15` is listed).

## Deploy work-order (`aws-lambda-deployer`)

`deploying-aws-lambda`. Runtime-agnostic: no Quarkus skills.

## Debug / verify work-order (`aws-lambda-debugger`)

`debugging-aws-lambda` (the debugger never invokes the function); mode B adds `validating-aws-observability` (read-only scripts only). When the
runtime is Quarkus list `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`,
`developing-quarkus-amazon-lambda-v3-40` so it can read logs, traces and handler settings.

## Observability work-order (`aws-observability`)

`validating-aws-observability`, `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`,
`monitoring-cloudwatch-observability` and `tracing-aws-xray` (aws-skills); the observability section
of the architecture spec is the input. The alarm firing test only with the user's approval.

## Architect and sync work-orders

- `aws-architect` (E2/E4, advisory): the aws-skills the question needs (e.g. `architecting-aws-saas-multitenant`,
  `designing-dynamodb-nosql`, `designing-aws-api-gateway-serverless`) plus the specs and ADRs.
- `spec-synchronizer`: `coordinating-agent-handoffs`, `specifying-changes-with-openspec-v1-15`.

## Rule of thumb

List the smallest set; the reviewer's Never-Do checklist is exactly the union of listed skills, so
an unlisted skill is an unreviewed risk. Every listed skill keeps its `(unverified)` /
`(medium confidence)` tags in the agent's result.
