---
name: aws-observability-skills
description: "Routing table from trigger keywords to the AWS observability skills (live validation, CloudWatch and X-Ray design, Terraform, Quarkus code instrumentation). Use when editing Terraform or observability files for CloudWatch, X-Ray, alarms or dashboards of an AWS Lambda workload."
applyTo: "**/*.tf,**/observability/**"
---

# AWS observability skills routing

The rule's path glob covers Terraform files and any `observability/` folder, because the infrastructure side of observability is Terraform. Application code (Java) is not matched by that glob: for code instrumentation, name the code skills below. Facts live in the skills; this rule only routes. Docs lock of the skills: AWS docs of 2026-10-28. The family facts are carried by those skills. Because the glob matches every Terraform file, apply this rule only when the work concerns CloudWatch, X-Ray, alarms or dashboards of a Lambda workload; otherwise ignore it. Tags `(unverified)` and `(medium confidence)` from a skill apply here too.

## Skill routing

| Trigger keywords | Skill | Use for |
|---|---|---|
| validate observability, prove, smoke test, live check, five pillars, alarm notification test | `validating-aws-observability` | read-only AWS CLI scripts: logs, metrics, traces, alarms, dashboards |
| CloudWatch design, SLO, SLI, log retention, metric alarm, EMF, dashboard design, cardinality | `monitoring-cloudwatch-observability` | design decisions |
| X-Ray, trace, sampling, OpenTelemetry, Transaction Search, service map | `tracing-aws-xray` | design decisions |
| log group, retention, metric filter, alarm, dashboard, `aws_cloudwatch_*` | `provisioning-aws-cloudwatch-v6` | Terraform HCL |
| X-Ray group, sampling rule, `aws_xray_*` | `provisioning-aws-xray-v6` | Terraform HCL |
| JSON logs in code, spans in code, custom metrics in code, instrument the Lambda | `observing-quarkus-lambda` (umbrella over `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40`) | Quarkus code instrumentation; owner is `quarkus-lambda-integrator`, not `aws-observability` |

Executors: `aws-observability` (command `/observe-aws-workload`) for review, offline Terraform and live validation; `aws-lambda-deployer` applies; `aws-terraform-engineer` owns non-observability infrastructure.

## Composition: single pillar vs umbrella

- A single pillar (only alarms, only X-Ray sampling, only retention): load the one design skill and the one provisioning skill that match. Do not load the others.
- A full observability layer (logs, metrics, traces, alarms, dashboards): load both design skills and both provisioning skills, compose in this order: log groups and retention, metrics and alarms, X-Ray group and sampling, dashboards.
- Code instrumentation: load `observing-quarkus-lambda` once as the umbrella; load one of its three child skills directly only for a single signal. Never load the umbrella together with its children.
- Live validation is separate from provisioning: after a deploy, load `validating-aws-observability`; it reports FAIL and names the provisioning skill, it never fixes.

## Cross-cutting rules

### Always Do

- Keep logs JSON with `requestId` and `tenantId`, and no PII in any log field, metric dimension or trace annotation (family rule).
- Set `retentionInDays` explicitly on every log group.
- Bound metric dimensions; a per-tenant dimension needs a stated bound, otherwise tenant stays a log field.
- Decide X-Ray SDK vs OpenTelemetry in an ADR or an Ask-First: the X-Ray SDKs and Daemon are in maintenance mode since 2026-02-25 (security fixes only) and AWS recommends OpenTelemetry.
- Match the API type: an HTTP API has no X-Ray tracing, a trace starts at the Lambda segment; a REST API supports it.
- Check the trace segment destination before reading traces: with Transaction Search enabled, `BatchGetTraces` does not find traces.
- Run only offline Terraform checks (`fmt -check`, `init -backend=false`, `validate`) from observability work; apply belongs to `aws-lambda-deployer`.

### Ask First

- X-Ray SDK or OpenTelemetry; sampling rate; Transaction Search on or off (account-wide).
- Per-tenant metric dimensions or alarms.
- Sending a test ALARM state to an alarm (notifies real subscribers): needs the user's approval, relayed by the orchestrator.
- Custom metric namespace, names and exact dimension set.

### Never Do

- Never run `terraform apply`, `destroy` or `import` from observability work. Alternative: return the plan for `aws-lambda-deployer`.
- Never hardcode account ids, ARNs or secrets in `.tf` files. Alternative: variables with `validation`.
- Never put PII or unbounded identifiers (user id, request id) in metric dimensions. Alternative: log field.
- Never claim a dashboard renders from `get-dashboard` alone. Alternative: report "render not provable via API".
- Never use `--unmask` or print log messages when validating. Alternative: counts from Logs Insights.
- Never edit application code from an observability task. Alternative: a work-order proposal for `quarkus-lambda-integrator`.

## Verification

Check that each routed skill name is installed: the folder `.claude/skills/<name>/` must exist for `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`, `monitoring-cloudwatch-observability`, `tracing-aws-xray`, `validating-aws-observability` and `observing-quarkus-lambda`. A missing folder means the routing row is stale or the package is not installed.
