# Verdict, Work-Order, Post-Deploy Checks and Verification Loop

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping).

## Contents

- [Diagnosis verdict](#diagnosis-verdict)
- [Work-order format](#work-order-format)
- [Record and outcome vocabulary](#record-and-outcome-vocabulary)
- [Post-deploy verification checklist](#post-deploy-verification-checklist)
- [Verification Loop](#verification-loop)

## Diagnosis verdict

One verdict per symptom. Redact secrets and personal data ([pattern 11](./always-do-patterns.md#11-redact-secrets)).

```text
Symptom:        <client status or message, UTC window, entry: REST | HTTP API | SQS | EventBridge>
Function:       <name>:<alias>  executed version <N>  Region <r>  State <..>  LastUpdateStatus <..>
Class:          invocation error | function error            (step 1)
Branch:         <letter and number, for example B1 or C3>
Evidence:       RequestId <id>; REPORT Status/Error Type/Max Memory Used vs Memory Size; metric <name> (Sum|Max) <value>;
                $context.integration.integrationStatus <..>; read-only commands used: <list>
Verdict:        <one cause, or "not determined" with the next read-only step>
Unconfirmed:    <each tag used: (unverified) or (medium confidence) with the topic>
Work-order:     <see below, or "none">
```

Rules:
- State the branch letter; a verdict without evidence from the allowlisted commands is "not determined".
- Never state an irresolvable string as seen ([C7](./ask-first-decisions.md#c7-irresolvable-strings-and-status)).
- Cite both AWS pages where they conflict (log tail, vCPU threshold, SQS pollers, memory divisor) and choose none ([register](./unverified-and-risks.md#irresolvable-items)).

## Work-order format

The debugger hands fixes back as text; it makes no AWS call that changes anything.

```text
Fix required:   <what to change, with the exact setting or policy line>
Owner:          integrator (code, handler, payload) | deployer (configuration, permission, alias, stage, concurrency, logging)
Reason:         <branch, evidence id, source id>
Risk:           <what the change affects; for example reserved concurrency 0 throttles everything>
Verify after:   <read-only checks that prove it worked>
```

Owner examples: a handler setting that does not match the code goes to the integrator (C5); a missing `lambda:InvokeFunction` statement for API Gateway, a visibility timeout below six times the function timeout, enabling API Gateway access logs, or a reserved-concurrency question go to the deployer, `deploying-aws-lambda` (S1, S25, S48, S19).

## Record and outcome vocabulary

Repo protocol vocabulary (not an AWS fact). The verdict above maps to the record the orchestrator reads:

| Mode | Record | Kind | Outcome |
|---|---|---|---|
| A, diagnosis | `diagnosis-NN.md` | `diagnosis-report` | `success` = root cause found with evidence; `partial` = a likely cause with incomplete evidence (name what is missing); `failed` = "not determined"; `needs-input` = a user or owner answer is needed before reading further |
| B, post-deploy E7 | `verify-E7-<nn>.md` | `verify` | `pass` = every required pillar verified; `fail` = at least one pillar not verified or failing |

- In mode B a pillar that is skipped, inconclusive, warned or whose billable query had no `approval: logs-insights ...` line (so the `validating-aws-observability` approval flag was not passed and the script printed `WARN ... not verified`) is `not verified`. List each under `## Gaps` with the reason; it keeps `fail`.
- Only if the work-order carries `approval: e7-gaps pillars=<comma list> by=<user> at=<UTC> relayed-by=<orchestrator>` naming exactly those pillars, emit `pass` once every other pillar is met and list the accepted ones under `## Gaps` as "accepted by the user (approval line ...)". A pillar not on the list stays `fail`.
- The debugger never edits a verdict after the orchestrator saves it, and never runs a real invoke: route that to `aws-lambda-deployer` under an `approval: smoke payload=<file or sha256> ...` line.

## Post-deploy verification checklist

Read-only evidence that a release is healthy (S8, S27, S29, S43, S50; SnapStart: https://docs.aws.amazon.com/lambda/latest/dg/snapstart-monitoring.html, S32). A real smoke invoke is [ask first C5](./ask-first-decisions.md#c5-reproducing-by-invoking); the deploy smoke assertions live in `deploying-aws-lambda`.

| Check | Healthy reading | Source |
|---|---|---|
| Version and state | `State` `Active`, `LastUpdateStatus` `Successful`, `Version` as released | S29, S42 |
| SnapStart version | `SnapStart.OptimizationStatus` `On` and `State` `Active` | S32 (https://docs.aws.amazon.com/lambda/latest/dg/snapstart-monitoring.html) |
| Errors and invocations | `Errors` (Sum) over `Invocations` (Sum) near 0 | S8 |
| Throttles | `Throttles` (Sum) is 0; `ConcurrentExecutions` (Max) below the quota | S8, S26 |
| Latency | `Duration` p99 well below the configured `Timeout`; cold-start share in line with the expected size ([D4](./tree-c-e-function-latency-network.md#branch-d-cold-start-and-latency)) | S6, S8 |
| Provisioned concurrency | `ProvisionedConcurrencySpilloverInvocations` is 0 | S8 |
| Asynchronous entry | `AsyncEventAge` low, `AsyncEventsDropped` 0 | S8 |
| API Gateway (REST) | `5XXError` (Average is the rate), `IntegrationLatency`, `Latency` | S50 |
| SQS entry | `ApproximateAgeOfOldestMessage` flat, `NumberOfMessagesDeleted` above 0, DLQ `ApproximateNumberOfMessagesVisible` 0 | S27, S43 |
| Executed version | the START log line or invoke result shows the released version (alias resolved) | S2, S5 |

Dashboards and alarm design belong to `monitoring-cloudwatch-observability` and `tracing-aws-xray`, not here.

## Verification Loop

Self-check before delivering a verdict or changing this skill. Run from this skill's folder (`D=.`); commands are representative and were not executed by the research.

```bash
D=.   # run from this skill's folder

# 1. SKILL.md length
wc -l "$D/SKILL.md"
# Expected: under 500

# 2. Blueprint length
wc -l "$D"/blueprints/*.md
# Expected: every file at most 160

# 3. Mutating verbs only inside the refused and wrong examples
grep -rnE "aws (lambda|apigateway|apigatewayv2|iam|sqs|logs|events) (update|put|add|delete|create|attach|remove|publish|purge|start-message-move|tag|untag)" "$D"
# Expected: matches only in blueprints/never-do-patterns.md (N1 wrong block) and blueprints/read-only-allowlist.md (refused table)

# 4. Register header counts equal listed rows (U, I, M, L)
grep -cE "^\| U[0-9]+ " "$D/blueprints/unverified-and-risks.md"
# Expected: 9; likewise I (8), M (10), L (6)

# 5. No secret value patterns in a verdict draft (run on the draft file)
grep -nE "AWS_SESSION_TOKEN|AKIA[0-9A-Z]{16}|Bearer " <verdict-file>
# Expected: no output
```

For a live diagnosis: list the commands used and confirm each is in the [allowlist](./read-only-allowlist.md#allowlist); confirm the verdict names a branch letter and every tag has a register row.
