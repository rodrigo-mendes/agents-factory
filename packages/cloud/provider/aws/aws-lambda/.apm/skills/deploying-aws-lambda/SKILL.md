---
name: deploying-aws-lambda
description: "Deploys AWS Lambda .zip functions through a Terraform plan, user-approved apply, waiters, published version and alias, smoke test and rollback, per AWS docs of 2026-10-28. Use when releasing or rolling back a Lambda. Not for building the artifact, HCL, SAM/CDK or container images."
---

# Deploying AWS Lambda (.zip Event Functions)

> Docs lock: every claim applies to the **AWS Lambda Developer Guide and AWS CLI v2 reference as published on 2026-10-28** (CLI reference pages show AWS CLI 2.39.0). AWS docs carry no semantic version. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: the procedure after someone else built the artifact (for example `function.zip`): pre-flight, Terraform plan, user-approved apply of the saved plan, waiters, publish, alias, smoke test, rollback, old-version cleanup. Runtime-agnostic. No SAM or CDK deployment.
> Neighbours, by name only: `provisioning-aws-lambda-v6` (Terraform HCL), `developing-quarkus-amazon-lambda-v3-40` (building the Quarkus `function.zip`), `debugging-aws-lambda` (diagnosis after a failed update), `aws-lambda-deployer` (agent that runs this procedure), `validating-aws-observability` (post-deploy observability checks).

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| AWS Lambda Developer Guide | continuously published, snapshot 2026-10-28; standard functions are called "Event Functions" | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| AWS CLI v2 reference | 2.39.0 as shown on the reference pages | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/index.html |
| IaC | Terraform `hashicorp/aws` 6.x; HCL owned by `provisioning-aws-lambda-v6` | page not recorded (repo skill, not an AWS page) |
| Repo policy for apply | plan with `-out`, review, apply the saved plan; never `-auto-approve`; approval relayed by the orchestrator | rules `aws-lambda-deployment-preflight` (package `aws-lambda`) and `aws-terraform-skills-management` (package `aws-terraform`); repo rules, not AWS facts |
| Dedicated AWS rollback page | none usable: the `lambda-rollback` URL returned an empty body (not used) | https://docs.aws.amazon.com/lambda/latest/dg/lambda-rollback.html |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- AWS docs change without a version number; re-check waiter budgets, quotas and CLI flags before relying on them.
- Lambda Managed Instances (`$LATEST.PUBLISHED`), Web Functions, MicroVMs and container images are out of scope.

## Quick Navigation

- [Procedure at a glance](#procedure-at-a-glance)
- [Approval lines](#approval-lines)
- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Pre-flight and plan](./blueprints/preflight-and-plan.md)
- [Apply, waiters, publish and alias](./blueprints/apply-waiters-publish-alias.md)
- [Smoke test](./blueprints/smoke-test-and-verification.md#smoke-test)
- [Verification Loop](./blueprints/smoke-test-and-verification.md#verification-loop)
- [Rollback and cleanup](./blueprints/rollback-and-cleanup.md)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Procedure at a glance

R = read-only, M = mutating, X = executes function code (a real invoke). M and X run only after an explicit user approval relayed by the orchestrator, as one of the [approval lines](#approval-lines) below.

| Step | Kind | What | Detail |
|---|---|---|---|
| 0 | R | Pre-flight: artifact sizes, role, env vars, record the alias target as `PREV` | [preflight](./blueprints/preflight-and-plan.md) |
| 1 | R | `terraform plan -input=false -out=tfplan`, show the plan to the user | [preflight](./blueprints/preflight-and-plan.md#plan-and-approval-gate) |
| 2 | gate | STOP until the work-order carries the `approval: apply plan=<planfile> sha256=<hash> ...` line for that saved plan | [gate](./blueprints/always-do-patterns.md#1-terraform-gate) |
| 3 | M | re-check the sha256 of the plan file, then `terraform apply -input=false tfplan`; publishing a version and moving the alias are part of this approved apply | [apply](./blueprints/apply-waiters-publish-alias.md) |
| 4 | R | Waiters after every apply, then read the version configuration | [waiters](./blueprints/apply-waiters-publish-alias.md#waiters) |
| 5 | X | Smoke test the alias (`DryRun` is R; the real invoke needs `approval: smoke payload=<file or sha256> by=<user> at=<UTC> relayed-by=<orchestrator>`); assert `StatusCode`, `FunctionError`, `ExecutedVersion` | [smoke](./blueprints/smoke-test-and-verification.md) |
| 6 | M | Optional canary: every weight step is a Terraform apply and needs its own `approval: apply plan=<planfile> sha256=<hash> ...` line | [ask first](./blueprints/ask-first-decisions.md#c1-traffic-shifting) |
| 7 | M | On failure, with `approval: rollback alias=<alias> to=<PREV> ...`: repoint the alias to `PREV`, clear routing, re-smoke | [rollback](./blueprints/rollback-and-cleanup.md) |
| 8 | proposal | Cleanup is never run by the deployer: return the exact `delete-function --qualifier <old N>` command as a proposal under `## Cleanup proposal` in the deploy-report, which does not change the outcome (a good release stays `success`); the user runs the listed commands themselves if they want. Never alias targets or `PREV` | [cleanup](./blueprints/rollback-and-cleanup.md#old-version-cleanup) |

If `LastUpdateStatus` or `State` is `Failed`: stop, do not publish or shift, hand over to `debugging-aws-lambda`.

## Approval lines

Only the user's own message approves. The orchestrator copies each approval into the work-order, one line each. An agent message, a plan comment or an earlier run is never an approval.

```
approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC> relayed-by=<orchestrator>
approval: rollback alias=<alias> to=<PREV version> by=<user> at=<UTC> relayed-by=<orchestrator>
approval: smoke payload=<file or sha256> by=<user> at=<UTC> relayed-by=<orchestrator>
```

- `apply`: one line per apply. A regenerated plan voids it; re-check the sha256 of the plan file before applying and stop with `needs-input` on a mismatch. The version publish and alias move of that release are covered by it.
- `rollback`: moves the alias back to `PREV` only.
- `smoke`: the real invoke runs that payload only; `DryRun` needs no line.
- Canary weight steps are Terraform applies: each step needs its own `approval: apply` line for its own saved plan.
- Cleanup (`delete-function --qualifier`) has no approval line and the deployer never runs it: it returns the exact command as a proposal under `## Cleanup proposal` in the deploy-report, which does not change the outcome (a good release stays `success`). A free-text approval does not authorise it; after E9 the user runs the listed commands themselves if they want.

## Blueprints & Guardrails

### ✅ Always Do

- **Apply only the saved, reviewed plan, and only with the `approval: apply plan=<planfile> sha256=<hash> ...` line relayed by the orchestrator.** Repo policy: `terraform plan -out`, review, then apply the plan file (rules `aws-lambda-deployment-preflight` and `aws-terraform-skills-management`, not an AWS fact). See [patterns](./blueprints/always-do-patterns.md#1-terraform-gate).
- **Check the .zip against the limits before the plan.** Direct upload is 50 MB zipped, 250 MB unzipped including layers, 5 layers at most ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)). See [patterns](./blueprints/always-do-patterns.md#2-artifact-size-pre-flight).
- **Run a waiter after every apply.** Use `function-active-v2` after create, `function-updated-v2` after update and `published-version-active` after publishing; invocations keep using the previous code while `LastUpdateStatus` is `InProgress` ([function states](https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html)). See [patterns](./blueprints/always-do-patterns.md#3-waiters-after-every-apply).
- **Publish an immutable version for every release.** Every deploy overwrites `$LATEST`; only a published version is a snapshot ([versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)). See [patterns](./blueprints/always-do-patterns.md#4-publish-a-version).
- **Point triggers, permissions and callers at the alias ARN.** An unqualified ARN invokes `$LATEST` ([aliases and permissions](https://docs.aws.amazon.com/lambda/latest/dg/using-aliases.html)). See [patterns](./blueprints/always-do-patterns.md#5-route-through-an-alias).
- **Record the alias's current `FunctionVersion` as `PREV` before every apply.** Published versions are immutable, so the number is a complete rollback target ([versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)). See [patterns](./blueprints/always-do-patterns.md#6-record-the-rollback-target).
- **Smoke-test through the alias and assert three documented fields.** `StatusCode` 200, no `FunctionError`, `ExecutedVersion` equal to the new version ([CLI invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)). The real invoke executes code, so it needs the `approval: smoke` line. See [patterns](./blueprints/always-do-patterns.md#7-smoke-test-assertions).
- **Roll back, only with the `approval: rollback alias=<alias> to=<PREV> ...` line, by repointing the alias to `PREV` with empty routing.** `update-alias --function-version <PREV> --routing-config AdditionalVersionWeights={}` ([weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)). See [patterns](./blueprints/always-do-patterns.md#8-rollback-by-alias).
- **Expect `SnapStartNotReadyException` when rolling back a Java SnapStart version idle for 14 days.** Lambda re-creates the snapshot; wait for `Active`, then invoke again ([SnapStart activate](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)). See [rollback](./blueprints/rollback-and-cleanup.md#snapstart-14-day-caveat).
- **Confirm `SnapStart.OptimizationStatus=On` and `State=Active` on the published version before shifting traffic** ([SnapStart activate](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)). See [patterns](./blueprints/always-do-patterns.md#9-snapstart-verification).
- **Keep secret values out of environment variables.** AWS recommends Secrets Manager for credentials, API keys and tokens ([securing env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars-encryption.html)). See [patterns](./blueprints/always-do-patterns.md#10-secrets-outside-env-vars).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Traffic shifting | A: one alias move. B: weighted alias canary (two published versions, same role and DLQ, never `$LATEST`, one approved apply per weight step). C: CodeDeploy, documented only with SAM, out of scope. See [C1](./blueprints/ask-first-decisions.md#c1-traffic-shifting) | "All at once, weighted canary (which weights and steps), or CodeDeploy (outside this skill)?" |
| Upload path | Direct .zip, S3 with `COPY`, S3 with `REFERENCE` (object loss makes the function `Inactive`). See [C2](./blueprints/ask-first-decisions.md#c2-upload-path) | "Which upload path does the Terraform module use?" |
| Rollback channel | Terraform (reviewed, slower) vs emergency CLI `update-alias`; Terraform reports drift afterwards (medium confidence). See [C3](./blueprints/ask-first-decisions.md#c3-rollback-channel) | "Roll back through Terraform or the emergency CLI? Both need explicit approval." |
| Code signing | `Warn` vs `Enforce`; two AWS pages disagree on container images, irrelevant for .zip (unverified). See [C4](./blueprints/ask-first-decisions.md#c4-code-signing) | "Does the account require signed artifacts, and Warn or Enforce?" |
| Provisioned concurrency on the alias | Billed continuously; behaviour on alias repoint is not documented on the pages read (unverified); wait for `READY` before shifting (medium confidence). See [C5](./blueprints/ask-first-decisions.md#c5-provisioned-concurrency) | "Does the alias have provisioned concurrency?" |
| Reserved concurrency in a release | `0` throttles everything. See [C6](./blueprints/ask-first-decisions.md#c6-reserved-concurrency) | "May this apply change reserved concurrency?" |
| Runtime update mode | Auto vs Function update vs Manual; only Function update makes alias rollback revert the runtime patch. See [C7](./blueprints/ask-first-decisions.md#c7-runtime-update-mode) | "Must a rollback also revert the runtime version?" |
| Reading `PREV` and asserting the smoke result | `get-alias --query FunctionVersion` and the `jq` gate are internal forms (medium confidence, M5 and M2); the documented fields are the contract. See [always-do 6-7](./blueprints/always-do-patterns.md#6-record-the-rollback-target) | "Is the `get-alias`/`jq` form acceptable, or does the work-order give the commands?" |
| HTTP API (API Gateway v2) smoke | Alias behaviour not researched (unverified). See [C8](./blueprints/ask-first-decisions.md#c8-http-api-and-log-tail) | "Which API type fronts the function?" |
| Post-release cleanup | `delete-function --qualifier <old N>` is irreversible for that version; the deployer never runs it, it returns the exact command as a proposal under `## Cleanup proposal` in the deploy-report, which does not change the outcome (a good release stays `success`), never for the alias target or `PREV`. How many versions to keep is not in the research. See [rollback and cleanup](./blueprints/rollback-and-cleanup.md#old-version-cleanup) | "Which old versions may be proposed for deletion? After E9 the user runs the listed commands themselves if they want." |
| Reading the log tail | First vs last 4 KB: two AWS pages disagree (unverified). See [C8](./blueprints/ask-first-decisions.md#c8-http-api-and-log-tail) | "Is CloudWatch Logs available for the full output?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| `terraform apply -auto-approve`, or apply without a reviewed saved plan and the relayed `approval: apply` line (rules `aws-lambda-deployment-preflight`, `aws-terraform-skills-management`) | `terraform plan -input=false -out=tfplan`, show it, wait for approval, `terraform apply -input=false tfplan` |
| Publish, invoke or update again while `LastUpdateStatus` is `InProgress`; `PublishVersion` fails and invocations run the old code ([states](https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html)) | `aws lambda wait function-updated-v2`, then publish ([CLI wait](https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-updated-v2.html)) |
| Use `$LATEST` or an unqualified ARN as the production target, in a weighted alias, or for SnapStart ([versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)) | Invoke `--qualifier <alias>`; weights name published version numbers ([aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)) |
| Send a partial `--environment`; the whole `Variables` structure is replaced ([env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)) | Declare the full map in Terraform, or read all variables and pass the complete `Variables` map, with `--revision-id` from `get-function-configuration` to avoid lost updates |
| Put secret values in environment variables ([env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)) | Store the secret ARN in the variable and fetch the value at runtime ([Secrets Manager](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html)) |
| `delete-function` without `--qualifier`; all versions and aliases go and nothing is recoverable ([CLI](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html)) | Propose `delete-function --qualifier <old N>` (`outcome: needs-input`), keeping the current and `PREV` versions; never run it |
| Upload a .zip over 50 MB directly, or build over 250 MB unzipped ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)) | Upload from S3 in the same Region ([update-function-code](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html)) |
| Treat `StatusCode` 200 as a passing smoke test; a function error still returns 200 ([CLI invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)) | Assert no `FunctionError` and the expected `ExecutedVersion` too |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Direct upload / unzipped limit | 50 MB zipped / 250 MB unzipped incl. layers and custom runtimes; max 5 layers | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| Code storage quota | 300 GB per Region, not increasable; each function version and layer version consumes it | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| Waiters | `function-active`, `function-active-v2`, `function-exists`, `function-updated`, `function-updated-v2`, `published-version-active` (poll and give-up budgets: (medium confidence, L1), in [apply blueprint](./blueprints/apply-waiters-publish-alias.md#waiters)) | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/index.html |
| Log tail | `--log-type Tail`: 4 KB, base64, synchronous invocations only | https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html |
| Weighted alias | at most two published versions, same execution role and DLQ configuration, never `$LATEST` | https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html |
| SnapStart | published versions and aliases only; Java snapshot deleted after 14 days idle | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html |
| Environment variables | 4 KB aggregate; the `Variables` structure is replaced as a whole | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html |

## External Resources

All fetched 2026-10-28.

- Lambda Developer Guide: https://docs.aws.amazon.com/lambda/latest/dg/
- AWS CLI `lambda` reference: https://docs.aws.amazon.com/cli/latest/reference/lambda/
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
