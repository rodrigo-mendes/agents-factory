---
name: observe-aws-workload
description: "Reviews, provisions and validates observability (logs, metrics, X-Ray traces, alarms, dashboards) for an AWS Lambda workload via the aws-observability agent. Use when reviewing a spec's observability, writing its Terraform offline, or proving the five pillars live after a deploy."
argument-hint: "<function-name> region=<r> [mode=validate|provision|review] [wo=<work-order path; required for review and provision>] [nn=<NN>] [smoke-start=<epoch-s>] [api-type=REST|HTTP|NONE] [alarm-prefix=<p>] [dashboards=<n1,n2>]"
context: fork
agent: aws-observability
disable-model-invocation: true
---

# Observe AWS Workload

Routes to the `aws-observability` agent, a non-interactive executor for the infrastructure side of observability on AWS Lambda: logs, metrics, X-Ray traces, alarms and dashboards. It never applies Terraform and never instruments code. It never verifies the workload as a gate: in every mode it writes a result record `result-NN-observability.md` (kind `report`) and returns it; the orchestrator decides.

## Quick Navigation

- [How to invoke](#how-to-invoke)
- [What the agent needs](#what-the-agent-needs)
- [Blueprints & Guardrails](#blueprints--guardrails)
- [Boundaries](#boundaries)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)

## Blueprints & Guardrails

Facts live in the skills the agent loads (`monitoring-cloudwatch-observability`, `tracing-aws-xray`, `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`, `validating-aws-observability`); this command only routes. Scenarios: [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).

### ✅ Always Do

- Pass `region=` explicitly (or let the work-order carry it); do not rely on a default Region.
- Report dashboard rendering as "not provable via API"; WARN lines as inconclusive.
- Write the result record `result-NN-observability.md` (counts and evidence, never log messages) and return it; the orchestrator decides what follows.
- Run only offline Terraform checks in `provision` mode.

### ⚠️ Ask First

The agent never asks the user. These are QUESTIONS it returns to the orchestrator, which decides or asks the user:

- Which Region, when neither `region=` nor the work-order carries it?
- Which values are missing for the mode (spec path, Terraform directory, smoke start, API type, alarm prefix, dashboard names)? Omitting `mode=` is a deliberate default to `validate` (it needs a deployed workload); the agent does not ask which mode.

### 🚫 Never Do

| Do not | Do instead |
|---|---|
| Claim a dashboard renders (from `get-dashboard` or any API call) | Report "render not provable via API" |
| Run `trigger-alarm-test.py` without the relayed line `approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=<orchestrator>` for that exact alarm | Record "alarm notification not proven: no approval relayed" and ask the orchestrator |
| Run Logs Insights or X-Ray trace retrieval without the relayed line `approval: logs-insights scope=<log-group or "xray"> window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>` | Do not pass `--i-have-logs-insights-approval` / `--i-have-trace-retrieval-approval` (without them no query or retrieval is made); list the pillar as not verified and ask the orchestrator; a plan comment is not an approval |
| Run `terraform apply`, `destroy` or `import`, or edit application code | Hand the plan to `aws-lambda-deployer`; propose a work-order for the code owner named in the work-order (`quarkus-lambda-integrator` in the Quarkus profile) |

## How to invoke

```
/observe-aws-workload <function-name> region=<r> [mode=validate|provision|review] [wo=<work-order path; required for review and provision>] [nn=<NN>]
                      [smoke-start=<epoch-s>] [api-type=REST|HTTP|NONE] [alarm-prefix=<p>] [dashboards=<n1,n2>]
```

`region=` is REQUIRED unless the work-order carries it; without either, the agent returns a `needs-input` result carrying a numbered `QUESTIONS` block and runs nothing. `review` and `provision` REQUIRE `wo=<path>`: the work-order carries the spec path (review), the Terraform directory (provision), the code owner and the profile. Only `validate` can run from arguments alone (`smoke-start=`, `api-type=`, `alarm-prefix=`, `dashboards=`; the agent passes the dashboard list as one repeated `--dashboard` flag per name). A value in `wo=` wins over the same command argument. `nn=<NN>` is the record number for `result-NN-observability.md` when there is no work-order.

The agent requires a mode. When the user omits `mode=`, this command passes `mode=validate` to the agent explicitly: a deliberate default (that mode needs a deployed workload).

| mode | Agent mode | What happens |
|---|---|---|
| `review` | A | Reviews SLOs, log fields, retention, sampling, alarm list and dashboards in the spec; writes `result-NN-observability.md` |
| `provision` | B | Writes observability Terraform; runs `terraform fmt -check`, `init -backend=false`, `validate`; writes `result-NN-observability.md` |
| `validate` (passed explicitly when omitted) | C | After a deploy, runs the scripts of `validating-aws-observability` (read-only, except `trigger-alarm-test.py`, which runs only under a relayed approval line; billable reads (Logs Insights, trace retrieval) need the approval flags; scripts run from `.claude/skills/validating-aws-observability/`); writes `result-NN-observability.md` |

The agent intake accepts the mode as the letter (A, B, C) or the command word (`review`, `provision`, `validate`); the mapping is defined there. Orchestrated, the agent writes `result-NN-observability.md` at the path the work-order gives. Standalone use (no orchestrator): the agent writes `result-NN-observability.md` (path from `wo=`, otherwise the current folder) and also prints it; it needs a record number: pass `wo=<work-order>` or `nn=<NN>`, otherwise it returns `needs-input` with the QUESTIONS. Move the file into the handoff folder yourself, or re-run through the orchestrator.

Examples:
- `/observe-aws-workload items-api region=eu-west-1 mode=review wo=openspec/changes/list-tenant-items/handoff/wo-02-observability.md`
- `/observe-aws-workload items-api region=eu-west-1 mode=provision wo=openspec/changes/list-tenant-items/handoff/wo-04-observability.md`
- `/observe-aws-workload items-api region=eu-west-1 mode=validate nn=06 smoke-start=1793180400 api-type=HTTP alarm-prefix=items-api dashboards=items-api-main`

## What the agent needs

A work-order (always for `review` and `provision`; or the arguments above for `validate`) with: function name, region, mode, for mode D the code owner (and the profile when one is used), and per mode the spec path (review), the Terraform directory (provision), or the smoke start time in epoch seconds (`smoke-start`), API type (`REST`, `HTTP`, `NONE`), alarm prefix and dashboard names (validate). Anything missing comes back as numbered questions in a `needs-input` result; the agent never guesses and never asks the user directly.

## Boundaries

- Missing code instrumentation returns as a work-order proposal for the code owner named in the work-order (in the Quarkus profile `quarkus-lambda-integrator`, skills `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40`, umbrella `observing-quarkus-lambda`). These Quarkus skill names are loaded only when installed: they are not dependencies of the `aws-observability` package, so the proposal otherwise names whatever skills the work-order lists.
- Deploy is `aws-lambda-deployer`'s job; non-observability infrastructure is `aws-terraform-engineer`'s.
- Records are `result-NN-observability.md`; protocol in `coordinating-agent-handoffs` and `coordinating-quarkus-aws-handoffs`.

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
