# Research: Deploying AWS Lambda functions safely (AWS docs state 2026-10-28, Terraform hashicorp/aws 6.x as IaC)

> Unit **D1** -> future knowledge skill `deploying-aws-lambda` (package `aws-lambda`, consumer agent `aws-lambda-deployer`).
> Source item: "deploy Lambdas: artifact -> plan -> apply (only with user OK) -> smoke -> rollback".
> Runtime-agnostic. Terraform resource syntax is owned by `provisioning-aws-lambda-v6` and is referenced by name only.
> Spec followed: `.claude/skills/researching-technical-frameworks/SKILL.md` + `blueprints/output-format-template.md`.

**Citation convention.** Every claim carries a source ID `[Sn]` (AWS official page) or `[In]` (repo-internal file).
All AWS pages were read on **2026-10-28**; full URL, read date and read-completeness for each ID are in
[Source Bibliography](#source-bibliography). `[In]` sources are repo policy, **not AWS facts**.
Tags: **(unverified)** = no official page confirmed it; **(medium confidence)** = single source, inference, or partly read page.

**Version pin.** The "version" of this research is the AWS Lambda Developer Guide and AWS CLI v2 reference as published on
2026-10-28 (CLI reference pages show **AWS CLI 2.39.0** [S21]). AWS docs are continuously published and carry no
semantic version; anything read from older snapshots, blogs or the SAM/CDK guides is out of scope. IaC version:
Terraform `hashicorp/aws` **6.x** via `provisioning-aws-lambda-v6` [I2].

---

## Metadata

```yaml
Full_Name: AWS Lambda (Event Functions) deployment procedure - .zip packages, versions, aliases, smoke, rollback
Target_Version: "AWS Lambda Developer Guide + AWS CLI v2 reference as of 2026-10-28 (CLI ref 2.39.0); IaC hashicorp/aws 6.x"
Release_Date: "n/a (continuously published docs); snapshot date 2026-10-28"
Support_Status: Active (current docs)
Primary_Docs: https://docs.aws.amazon.com/lambda/latest/dg/
Official_Repo: "n/a (CLI reference https://docs.aws.amazon.com/cli/latest/reference/lambda/)"
Research_Date: 2026-10-28
Domain_Complexity: Complex   # production change procedure, security (secrets/KMS/code signing), traffic shifting, rollback, cost
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 8         # Always-Do patterns with ✓✓ badge (AWS-fact patterns); the Terraform-gate pattern is repo policy
Unverified_Count: 5
Irresolvable_Count: 2
Research_Quality_Score: 91%   # ~(84 total claims - 5 unverified - 2 irresolvable) / 84
Family_inputs: workspace/quarkus-aws-saas/_family_facts_v3.40.md (rows 11, 13, 15, 16, 21) ; _family_rules_v3.40.md (rules 3, 4, 5, 9-12)
Deviations_from_agent_workflow: "Caller forbade sub-agents and plan mode (scope approved by the user 2026-10-28, recorded in PIPELINE_STATE.md#approvals, G1/G2); all pages fetched directly; file written directly instead of via research-synthesizer."
```

---

## Executive Summary

This document captures the **safe deploy procedure for AWS Lambda Event Functions packaged as .zip archives**, as AWS
documents it on 2026-10-28, mapped onto a Terraform-driven workflow (`hashicorp/aws` 6.x; HCL owned by
`provisioning-aws-lambda-v6` [I2]). The procedure is: pre-flight the artifact and configuration -> `terraform plan -out`
-> human review -> `terraform apply` of the saved plan **only after an explicit user approval relayed by the
orchestrator** [I1] -> wait for Lambda to finish the update -> publish an immutable version -> shift an alias
(optionally weighted) -> smoke-test the alias -> roll back by repointing the alias to the previous version -> prune old
versions. Every deploy writes `$LATEST`; only a published version is an immutable snapshot of code and configuration
[S3], and aliases are the stable pointer that triggers, permissions and callers should use [S4][S6].

What is current in the 2026-10-28 docs that a skill must not get wrong: the CLI has **six** Lambda waiters
(`function-active`, `function-active-v2`, `function-exists`, `function-updated`, `function-updated-v2`,
`published-version-active`) with different APIs and polling budgets [S21-S25][S37]; `--log-type Tail` returns 4 KB of
logs, base64-encoded, synchronous invocations only [S18][S26] (the dev guide says "first 4 KB" [S18], the CLI reference
"last 4 KB" [S26]; see Research Gaps); weighted aliases take at most two **published** versions with the same execution
role and DLQ configuration and can never include `$LATEST` [S5]; SnapStart works only on published versions/aliases
[S8][S9] and, for Java, snapshots are deleted after 14 days without invocation, which matters when rolling back to an
old version [S9]. A new qualifier `$LATEST.PUBLISHED` appears in CLI patterns; it belongs to Lambda Managed Instances
and is out of scope [S24][S35].

Domain complexity tier: **Complex** - the procedure changes production traffic, touches secrets/KMS/code signing, has
cost side-effects (provisioned concurrency, SnapStart caching for non-Java runtimes, code storage) and needs a tested
rollback. Three critical patterns: (1) wait for `LastUpdateStatus = Successful` before publishing or invoking
[S7][S22]; (2) publish a version and move traffic only through an alias, never by invoking/pointing at `$LATEST` [S3][S5];
(3) roll back by `update-alias --function-version <previous> --routing-config AdditionalVersionWeights={}` [S5][S28].

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)
> Mutating commands below (`terraform apply`, `update-alias`, `publish-version`, `delete-function`, `put-*`) are listed so the
> skill can describe them; the agent executes them only under the approval rule in pattern A1. Read-only commands
> (`get-function-configuration`, `wait ...`, `invoke --invocation-type DryRun`) are safe for verification.

### ✅ Mandatory Patterns

**A1. Terraform gate: plan -out -> review -> apply the saved plan, only after explicit user approval**
> Confidence: 🟢 High as **repo policy** [I1] (not an AWS fact; triangulation n/a)
- Why: repo rule `.claude/rules/terraform-standards.md` Always-Do #6 "Always generate plan (`-out=tfplan`), review, then apply the plan file" and Never-Do #3 "Never run `terraform apply -auto-approve` in production" [I1]. Family/unit requirement: `terraform apply` runs only after an explicit user approval relayed by the orchestrator (task scope, 2026-10-28).
- Code:
  ```bash
  # Representative — adapt to your environment (repo policy [I1]; not executed by this research)
  terraform plan -input=false -out=tfplan      # review the plan output with the user
  # ...STOP: wait for explicit user approval relayed by the orchestrator...
  terraform apply -input=false tfplan          # apply exactly the reviewed plan; no -auto-approve
  ```
- Source: [I1] `.claude/rules/terraform-standards.md` (repo file, read 2026-10-28); `-input=false` is from `.claude/rules/terraform-cicd.md` (repo rule, OCI/Azure DevOps context) - use only as internal convention.

**A2. Pre-flight the .zip artifact against the documented size limits**
> Confidence: 🟢 High | [✓✓ Triangulated | S1 (2026-10-28) + S2 (2026-10-28)]
- Why: direct upload (API/SDK/console) is limited to **50 MB zipped**; larger files must be uploaded from Amazon S3; the unzipped contents including layers and custom runtimes are limited to **250 MB** [S1][S2]. The S3 bucket must be in the **same Region** as the function (may be another account) [S29]. Max **5 layers** [S1]. Code storage quota is **300 GB** (unzipped) per Region, not increasable, and **each function version and layer version consumes storage** [S1].
- Code:
  ```bash
  # Representative — adapt to your environment (portable POSIX shell)
  ZIP=target/function.zip                                   # family rule 4: artifact is the build's function.zip [I4]
  test -f "$ZIP" || { echo "artifact missing"; exit 1; }
  ZIPPED=$(wc -c < "$ZIP")                                  # bytes
  UNZIPPED=$(unzip -l "$ZIP" | tail -1 | awk '{print $1}')  # bytes, excludes layers -> add layer sizes yourself
  [ "$ZIPPED"   -le $((50*1024*1024))  ] || echo "WARN: >50 MB zipped -> upload via S3 (same Region)"
  [ "$UNZIPPED" -le $((250*1024*1024)) ] || echo "FAIL: >250 MB unzipped (incl. layers) -> not deployable as .zip"
  ```
- Note: Lambda docs use "MB" to mean 1,024 KB [S1]. The unzip-size command is a local check, not an AWS command (medium confidence that `unzip -l` totals match Lambda's accounting).
- Source: [S1] (2026-10-28), [S2] (2026-10-28), [S29] (2026-10-28)

**A3. Wait for the update to finish before publishing, invoking or updating again**
> Confidence: 🟢 High | [✓✓ Triangulated | S7 (2026-10-28) + S22/S30 (2026-10-28)]
- Why: while `LastUpdateStatus` is `InProgress`, `State` stays `Active`, **invocations keep using the previous code and configuration**, and `UpdateFunctionCode`, `UpdateFunctionConfiguration`, `PublishVersion` and `TagResource` fail [S7]. On `Failed`, `State` stays `Active` and invocations keep using the previous code [S7]. After creation, `State` is `Pending` and `Invoke`, `UpdateFunctionCode`, `UpdateFunctionConfiguration`, `PublishVersion` fail until `Active` [S7].
- Code (exact waiter names, CLI 2.39.0):
  ```bash
  # Representative — adapt to your environment (read-only)
  aws lambda wait function-active-v2  --function-name my-function   # after create: GetFunction, every 1 s, exit 255 after 300 failed checks [S23]
  aws lambda wait function-updated-v2 --function-name my-function   # after code/config update: GetFunction, every 1 s, exit 255 after 300 checks [S22]
  aws lambda get-function-configuration --function-name my-function \
    --query '{State:State,LastUpdateStatus:LastUpdateStatus,Reason:LastUpdateStatusReason,Code:LastUpdateStatusReasonCode,Sha:CodeSha256}'
  # Expected: State=Active, LastUpdateStatus=Successful. If Failed -> read LastUpdateStatusReason/ReasonCode [S30] and stop (diagnosis = D2).
  ```
- Waiter table [S21-S25][S37]:

  | Waiter | API | Poll | Gives up | Use after |
  |---|---|---|---|---|
  | `function-active` | GetFunctionConfiguration | 5 s | 60 failed checks, rc 255 | create (v1) [S37] |
  | `function-active-v2` | GetFunction | 1 s | 300 failed checks, rc 255 | create [S23] |
  | `function-updated` | GetFunctionConfiguration | 5 s | 60 failed checks, rc 255 | update (v1) [S25] |
  | `function-updated-v2` | GetFunction | 1 s | 300 failed checks, rc 255 | update [S22] |
  | `published-version-active` | GetFunctionConfiguration | 5 s | 312 failed checks, rc 255 | publish-version [S24] |
  | `function-exists` | not recorded | not recorded | not recorded | — |

  The `function-exists` detail page was not fetched (behaviour unverified; name High [S21]). All waiters accept `--qualifier` for a version or alias [S22][S23][S24][S25].
- Source: [S7], [S21], [S22], [S23], [S24], [S25], [S30], [S37] (all 2026-10-28)

**A4. Publish an immutable version for every release; never treat `$LATEST` as a release**
> Confidence: 🟢 High | [✓✓ Triangulated | S3 (2026-10-28) + S27 (2026-10-28)]
- Why: "any time you deploy your function code, you overwrite the current code in `$LATEST`"; a published version locks code, runtime, architecture, memory, layers and most configuration [S3]. Lambda publishes a new version only if code or a qualifying setting changed (code, env vars, runtime, handler, layers, memory, timeout, VPC, DLQ, role, description, architecture, ephemeral storage, package type, code storage mode, logging, file system, SnapStart, tracing); **reserved concurrency changes do not** produce a new version [S3]. Version numbers are never reused [S3]. `publish-version --code-sha256` only publishes if the hash matches; `--revision-id` only if configuration did not change since read [S27].
- Code:
  ```bash
  # Representative — CLI path (Terraform path: publishing is configured in provisioning-aws-lambda-v6, `publish` defaults to false there [I2])
  SHA=$(aws lambda get-function-configuration --function-name my-function --query CodeSha256 --output text)
  aws lambda publish-version --function-name my-function --code-sha256 "$SHA" --description "release <git-sha>"
  aws lambda wait published-version-active --function-name my-function --qualifier <N>   # 5 s x 312 [S24]
  ```
- Source: [S3], [S27], [S24], [S29] (2026-10-28); [I2] for the Terraform default

**A5. Route traffic only through an alias; point triggers and permissions at the alias ARN**
> Confidence: 🟢 High | [✓✓ Triangulated | S4 + S6 + S5 (2026-10-28)]
- Why: an alias is an updatable pointer to a version; an alias cannot point to another alias [S4][S6]. If an event source mapping or resource policy uses the alias ARN, it need not change when the version changes [S6]. An unqualified ARN implicitly invokes `$LATEST` [S3]. With a permission granted on an alias, invoking unqualified or the underlying version directly gives a permission error [S6]. You can't use an unqualified ARN to create an alias [S3].
- Code:
  ```bash
  # Representative — CLI shape only; in this project aliases are Terraform resources (provisioning-aws-lambda-v6)
  aws lambda update-alias --function-name my-function --name live --function-version <N>      # [S4][S28]
  aws lambda add-permission --function-name my-function --qualifier live --statement-id <id> \
    --principal <service>.amazonaws.com --action lambda:InvokeFunction --source-arn <arn>    # [S6]
  ```
- Source: [S3], [S4], [S6], [S28] (2026-10-28)

**A6. Smoke-test the alias, assert on `StatusCode`, `FunctionError` and `ExecutedVersion`, read the log tail**
> Confidence: 🟢 High | [✓✓ Triangulated | S26 + S18 + S5 (2026-10-28)]
- Why: `invoke` returns `StatusCode` (200 for `RequestResponse`, 202 `Event`, 204 `DryRun`), `FunctionError` (present when the function errored — a 200 can still carry a function error), `LogResult` (base64, 4 KB, `--log-type Tail`, synchronous only) and `ExecutedVersion` ("When you invoke a function with an alias, this indicates which version the alias resolved to") [S26]. Synchronous responses carry `x-amz-executed-version`; logs carry `START RequestId: ... Version: N` [S5]. `--cli-binary-format raw-in-base64-out` is required for inline JSON payloads with CLI v2 per the docs' examples [S9][S18][S26]. `--invocation-type DryRun` validates parameters and permission without running the function [S26].
- Code:
  ```bash
  # Representative — adapt to your environment
  aws lambda invoke --function-name my-function --qualifier live --invocation-type DryRun /dev/null   # permission check, no execution [S26]
  aws lambda invoke --function-name my-function --qualifier live \
    --cli-binary-format raw-in-base64-out --payload file://smoke-event.json \
    --log-type Tail out.json > meta.json                                                         # [S26]
  jq -e '.StatusCode==200 and (has("FunctionError")|not)' meta.json   # pass/fail gate
  jq -r '.ExecutedVersion' meta.json                                  # must equal the version just published
  jq -r '.LogResult' meta.json | base64 --decode                      # START/END/REPORT lines [S18]; macOS: base64 -D
  ```
- `jq` is a local tool, not AWS (assertion logic is an internal recommendation, medium confidence).
- API Gateway endpoint check: request the stage invoke URL + resource path and assert the expected status/body; a missing Lambda permission for the alias/version referenced by the integration yields `500 Internal Server Error` (REST API, stage-variable integration) [S34]. HTTP API behaviour was not researched (unverified).
- Source: [S5], [S9], [S18], [S26], [S34] (2026-10-28)

**A7. Roll back by repointing the alias to the previous published version and clearing routing**
> Confidence: 🟢 High | [✓✓ Triangulated | S5 + S28 + S20 (2026-10-28)]
- Why: "To route all traffic to version 2, use the update-alias command to change the function-version ... The command also resets the routing configuration" (example passes `--routing-config AdditionalVersionWeights={}`) [S5]. `update-alias --revision-id` avoids overwriting an alias changed since you read it [S28]. Published versions are immutable snapshots, so redirecting traffic to an earlier version rolls back code, configuration and (in **Function update** runtime mode) runtime version together [S20]. Weighted aliases exist so you "can ... quickly roll back if necessary" [S5]. `/lambda/latest/dg/lambda-rollback.html` returned no body (no dedicated rollback page found) [S36].
- Code:
  ```bash
  # Representative — mutating; run only under A1's approval rule (or the Ask-First C3 emergency path)
  PREV=<previous version number recorded before the deploy>
  REV=$(aws lambda get-alias --function-name my-function --name live --query RevisionId --output text)   # get-alias page not fetched (medium confidence)
  aws lambda update-alias --function-name my-function --name live \
    --function-version "$PREV" --routing-config 'AdditionalVersionWeights={}' --revision-id "$REV"
  aws lambda invoke --function-name my-function --qualifier live --cli-binary-format raw-in-base64-out \
    --payload file://smoke-event.json out.json   # re-smoke: ExecutedVersion must equal $PREV
  ```
- SnapStart (Java) caveat: if `$PREV` was not invoked for 14 days, its snapshot was deleted; invoking returns `SnapStartNotReadyException` and Lambda re-creates the snapshot - wait until the version is `Active` (`published-version-active`) then invoke again [S9][S24].
- Source: [S5], [S9], [S20], [S24], [S28] (2026-10-28)

**A8. SnapStart: publish, then confirm `OptimizationStatus: On` and `State: Active` on the version before shifting traffic**
> Confidence: 🟢 High | [✓✓ Triangulated | S9 + S8 + family fact 16 (I3)]
- Why: SnapStart applies only to published versions and aliases pointing to versions, never `$LATEST` [S8][S9][I3 row 16]. Publishing initializes the code and snapshots it; during that the version is `Pending` and invocations fail [S9]. Confirm with `get-function-configuration --function-name my-function:<N>` -> `SnapStart.OptimizationStatus = On`, `State = Active` [S9]. A new snapshot requires a new published version [S9]. SnapStart does not support provisioned concurrency, EFS, S3 Files or ephemeral storage > 512 MB; supported runtimes: Java 11+, Python 3.12+, .NET 8+; OS-only runtimes unsupported [S8][I3 row 16]. Restore-time limit: AWS says 10 s (`SnapStartTimeoutException`), Quarkus guide says 2 s - cite both [I3 row 21]. JVM+SnapStart vs native is an ADR, never a default [I4 rule 3].
- Code:
  ```bash
  # Representative — read-only verification after the Terraform apply that published version N
  aws lambda wait published-version-active --function-name my-function --qualifier <N>
  aws lambda get-function-configuration --function-name my-function:<N> \
    --query '{Opt:SnapStart.OptimizationStatus,ApplyOn:SnapStart.ApplyOn,State:State}'
  # Expected: {"Opt":"On","ApplyOn":"PublishedVersions","State":"Active"}  [S9]
  ```
- Source: [S8], [S9], [S24] (2026-10-28); [I3] rows 16, 21; [I4] rule 3

**A9. Keep secrets out of environment variables; resolve them at runtime from Secrets Manager / SSM Parameter Store**
> Confidence: 🟢 High | [✓✓ Triangulated | S10 + S11 + S12 (2026-10-28)]; family rule 5 [I4]
- Why: AWS recommends Secrets Manager "instead of environment variables to store database credentials and other sensitive information like API keys or authorization tokens" [S10][S11]. Env vars are encrypted at rest with an AWS managed key by default; a customer managed key (`--kms-key-arn`) is optional, incurs KMS charges, and users need `kms:Decrypt` to view/manage them [S11]. Env vars are version-specific and locked into a published version [S10]. The AWS Parameters and Secrets Lambda Extension (layer `AWS-Parameters-and-Secrets-Lambda-Extension`, port 2773, cache TTL default 300 s) supports Secrets Manager and Parameter Store; the execution role needs `secretsmanager:GetSecretValue` on the secret [S12]. Env vars: 4 KB aggregate, keys start with a letter, ≥2 chars, letters/digits/underscore, not reserved [S1][S10].
- Code:
  ```bash
  # Representative pre-flight (read-only): flag env var keys that look like secrets
  aws lambda get-function-configuration --function-name my-function --query 'Environment.Variables' --output json \
    | jq -r 'keys[]' | grep -Ei 'secret|password|passwd|token|api[_-]?key|private' && echo "FAIL: secret-like key in env vars"
  # Allowed pattern: env var holds the secret NAME/ARN (e.g. STRIPE_SECRET_ARN), value fetched at runtime [S12]
  ```
- The key-name heuristic is an internal check (medium confidence), not an AWS rule; a key such as `STRIPE_SECRET_ARN` would also match and needs human review.
- Source: [S1], [S10], [S11], [S12] (2026-10-28); [I4] rule 5

### ⚠️ Conditional Patterns

**C1. Traffic shifting strategy: all-at-once alias move vs weighted alias canary vs CodeDeploy**
> Confidence: 🟢 High for the mechanics [S5][S32]; choice is user's
- Options: (A) repoint alias to the new version in one step; (B) weighted alias: alias stays on version N, `AdditionalVersionWeights={"N+1"=0.05}`, raise weight in later applies, then move `function-version` to N+1 and clear weights; (C) CodeDeploy deployment configurations (e.g. `Linear10PercentEvery2Minutes`) - AWS documents this only via SAM + CodeDeploy [S5], which is out of scope (family rule 4) -> only as an option the user may request.
- Constraints for (B): max two versions; both published; same execution role; same DLQ config or none; never `$LATEST` [S5]; weight value 0.0-1.0, key = version number [S32]. Lambda uses a probabilistic split; at low traffic actual split can vary greatly from configured [S5]. Which version served a request: `ExecutedVersion` / `x-amz-executed-version` / `START ... Version:` log line / `ExecutedVersion` metric dimension [S5][S26].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A all-at-once | simplicity, one apply | blast radius = 100% | low traffic, strong smoke test |
  | B weighted alias (Terraform-driven steps) | small blast radius, Terraform-only | several approved applies; noisy split at low traffic | production APIs |
  | C CodeDeploy | automatic shifting + alarm rollback | adds SAM/CodeDeploy (out of family scope) | org already standardised on CodeDeploy |

- Agent: "Ask user: all-at-once, weighted canary (which weights/steps), or CodeDeploy (out of this skill's scope)?"
- Source: [S5], [S26], [S32] (2026-10-28)

**C2. Upload path: direct .zip vs S3 object (and code storage mode)**
> Confidence: 🟢 High [S1][S2][S29]
- Options: direct upload (≤ 50 MB zipped); S3 `--s3-bucket/--s3-key[/--s3-object-version]` (same Region) [S2][S29]; S3 code storage mode `COPY` (default, Lambda-managed storage, counts toward 300 GB) or `REFERENCE` (self-managed S3 code storage; Lambda does not keep a separate copy) [S2]. With `REFERENCE`, deleting the object or revoking bucket permissions makes the function `Inactive` [S7].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Direct | fewest moving parts | 50 MB cap | small zips |
  | S3 + COPY | > 50 MB, versioned object for audit | storage quota | most Terraform setups |
  | S3 + REFERENCE | avoids 300 GB quota | object deletion => Inactive function | many versions/large code |

- Agent: "Ask user which upload path the Terraform module uses; Terraform argument names live in provisioning-aws-lambda-v6."
- Source: [S1], [S2], [S7], [S29] (2026-10-28)

**C3. Rollback channel: Terraform (change alias version, plan, approved apply) vs emergency CLI `update-alias`**
> Confidence: 🟡 Medium (AWS mechanics High [S5][S28]; drift consequence is Terraform behaviour, not researched here)
- Options: (A) Terraform rollback - set the alias target to the previous version, plan -out, user approval, apply [I1]; (B) emergency CLI `update-alias` (A7), then reconcile Terraform so the next plan does not undo the rollback (medium confidence: Terraform reports the alias as drifted on the next plan).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A Terraform | single source of truth, reviewed | minutes of exposure | non-urgent regressions |
  | B CLI | seconds to restore | out-of-band change, drift to reconcile | user-approved incident response |

- Agent: "Ask user: rollback through Terraform or emergency CLI? Both are mutating and need explicit approval."
- Source: [S5], [S28] (2026-10-28); [I1]

**C4. Code signing (optional)**
> Confidence: 🟢 High [S15][S16]
- Decision: attach a code signing configuration (AWS Signer signing profiles, up to 20) with `UntrustedArtifactOnDeployment` `Warn` (default: deploy allowed, `SignatureValidationErrors` metric + CloudTrail) or `Enforce` (deployment blocked) [S15][S16]. Checks: integrity, expiry, mismatch, revocation [S15]. Layers must also be signed by an allowed profile [S15]. Only prevents new unsigned deployments; existing unsigned code keeps running [S15]. No extra charge [S15]. Container images: S16 says "do not support code signing" while S15 says code signing applies to ".zip or container image packages" - **contradiction between two AWS pages** (irrelevant for .zip; see Research Gaps).
- Agent: "Ask user whether the account requires signed artifacts and Warn vs Enforce."
- Source: [S15], [S16] (2026-10-28)

**C5. Provisioned concurrency on the alias during a deploy**
> Confidence: 🟡 Medium
- Facts: provisioned concurrency (PC) is configured on a version or alias, never `$LATEST` [S14][S33]; allocation status `IN_PROGRESS | READY | FAILED` [S14][S33]; PC is billed continuously and runs init code at allocation [S14]; with a weighted alias, configure higher PC while routing is active to avoid spillover [S5]; `AllocatedProvisionedConcurrentExecutions` fluctuates with a weighted alias during linear/canary deployments [S33]; PC ≤ reserved concurrency when both set [S14]; SnapStart is incompatible with PC [S8]. What happens to PC environments when an alias is repointed to a new version is **not stated** on the pages read (IRRESOLVABLE, see gaps).
- Agent: "Ask user whether the alias has PC; if yes, plan for allocation time (wait for READY) and cost during the shift."
- Source: [S5], [S8], [S14], [S33] (2026-10-28)

**C6. Reserved concurrency during deploy**
> Confidence: 🟢 High [S13][S3]
- Facts: reserved concurrency is both floor and ceiling, no extra charge; `0` throttles all invocations until removed; you can reserve up to unreserved account concurrency minus 100; changing it does not create a new version [S13][S3]. A deploy that sets it to 0 (e.g. to drain) is a production outage by design.
- Agent: "Ask user before any change to reserved concurrency in the same apply as a code release."
- Source: [S3], [S13] (2026-10-28)

**C7. Runtime update mode (Auto / Function update / Manual)**
> Confidence: 🟢 High [S19][S20]
- Facts: Auto (default) patches published versions in rollout phase 2; Function update applies the newest runtime only when you update the function, so published versions are static snapshots of code+config+runtime and alias rollback also rolls back the runtime; Manual pins a runtime version ARN (from the `INIT_START` log line) and is meant only as a temporary mitigation [S19][S20].
- Agent: "Ask user whether rollbacks must also revert the runtime patch level (=> Function update mode)."
- Source: [S19], [S20] (2026-10-28)

### 🚫 Forbidden Patterns

**N1. Applying without a reviewed saved plan or without relayed user approval**
> Severity: Critical
> Confidence: 🟢 High (repo policy [I1] + unit requirement)
- Why: an unreviewed apply can replace/destroy production resources; repo forbids `-auto-approve` in production and requires applying the saved plan [I1].
- Impact: unreviewed production change; plan and applied state can diverge.
- ❌ Wrong:
  ```bash
  terraform apply -auto-approve
  ```
- ✅ Correct:
  ```bash
  terraform plan -input=false -out=tfplan   # show to user; wait for explicit approval relayed by the orchestrator
  terraform apply -input=false tfplan
  ```
- Source: [I1] (repo rule, not AWS)

**N2. Publishing, invoking or updating again while `LastUpdateStatus` is `InProgress`**
> Severity: High
> Confidence: 🟢 High
- Why: `PublishVersion`/`UpdateFunction*`/`TagResource` fail during `InProgress`, and invocations still run the **previous** code, so a smoke test right after the update tests the old build [S7].
- Impact: failed publish, or a false-positive smoke test.
- ❌ Wrong:
  ```bash
  aws lambda update-function-code --function-name my-function --s3-bucket b --s3-key k
  aws lambda publish-version --function-name my-function        # may fail; or smoke runs old code
  ```
- ✅ Correct:
  ```bash
  aws lambda update-function-code --function-name my-function --s3-bucket b --s3-key k
  aws lambda wait function-updated-v2 --function-name my-function
  aws lambda publish-version --function-name my-function --code-sha256 "$SHA"
  ```
- Source: [S7], [S22], [S27] (2026-10-28)

**N3. Using `$LATEST` / unqualified ARNs as the production target, in a weighted alias, or for SnapStart**
> Severity: High
> Confidence: 🟢 High
- Why: every deploy overwrites `$LATEST` [S3]; an unqualified ARN invokes `$LATEST` [S3]; a weighted alias cannot point to `$LATEST` [S5]; SnapStart is not used on `$LATEST` [S8][S9]; PC cannot be configured on `$LATEST` [S14].
- Impact: no rollback target, untested code reaching production immediately, no SnapStart benefit.
- ❌ Wrong:
  ```bash
  aws lambda invoke --function-name my-function out.json                       # smoke on $LATEST
  aws lambda update-alias --function-name my-function --name live --routing-config 'AdditionalVersionWeights={"$LATEST"=0.1}'
  ```
- ✅ Correct:
  ```bash
  aws lambda invoke --function-name my-function --qualifier live --cli-binary-format raw-in-base64-out --payload file://e.json out.json
  aws lambda update-alias --function-name my-function --name live --function-version 7 --routing-config 'AdditionalVersionWeights={"8"=0.1}'
  ```
- Source: [S3], [S5], [S8], [S9], [S14], [S32] (2026-10-28)

**N4. Partial `--environment` update that silently drops variables**
> Severity: High
> Confidence: 🟢 High
- Why: "the entire contents of the Variables structure is replaced"; include all existing values; pass `--revision-id` from `get-function-configuration` to avoid lost updates [S10].
- Impact: missing config at runtime in the next published version.
- ❌ Wrong:
  ```bash
  aws lambda update-function-configuration --function-name my-function --environment "Variables={NEW_KEY=v}"
  ```
- ✅ Correct:
  ```bash
  # Terraform path: declare the full variables map in the module (provisioning-aws-lambda-v6). CLI path:
  aws lambda get-function-configuration --function-name my-function    # read all Variables + RevisionId
  aws lambda update-function-configuration --function-name my-function \
    --environment "Variables={EXISTING_A=a,EXISTING_B=b,NEW_KEY=v}" --revision-id <RevisionId>
  ```
- Source: [S10] (2026-10-28)

**N5. Secrets as plain environment variable values (or in .tfvars/state-visible config)**
> Severity: Critical
> Confidence: 🟢 High
- Why: AWS recommends Secrets Manager instead of env vars for credentials, API keys, tokens [S10][S11]; family rule 5 [I4].
- Impact: secret exposure to anyone who can read function configuration.
- ❌ Wrong:
  ```text
  Environment.Variables = { STRIPE_API_KEY = "sk_live_..." }
  ```
- ✅ Correct:
  ```text
  Environment.Variables = { STRIPE_SECRET_ARN = "arn:aws:secretsmanager:<region>:<acct>:secret:stripe" }
  # runtime fetch via AWS Parameters and Secrets Lambda Extension (localhost:2773) or SDK; role has secretsmanager:GetSecretValue [S12]
  ```
- Source: [S10], [S11], [S12] (2026-10-28); [I4] rule 5

**N6. Cleanup with `delete-function` without `--qualifier`, or deleting the rollback target**
> Severity: Critical
> Confidence: 🟢 High
- Why: without `Qualifier` "all versions and aliases are deleted" and a deleted function cannot be recovered; a version referenced by an alias can't be deleted [S31].
- Impact: whole function and all versions lost.
- ❌ Wrong:
  ```bash
  aws lambda delete-function --function-name my-function            # intended: remove version 3
  ```
- ✅ Correct:
  ```bash
  aws lambda delete-function --function-name my-function --qualifier 3   # keep current + previous (rollback) versions
  ```
- Retention rationale: each version consumes code storage (300 GB/Region) [S1]; for SnapStart **Python/.NET** each published version accrues caching charges while active (min 3 h) and AWS recommends deleting unused versions (`ListVersionsByFunction` + `DeleteFunction`) [S8]; for **Java** SnapStart there is no additional cost [S8][I3 row 16].
- Source: [S1], [S8], [S31] (2026-10-28)

**N7. Uploading a > 50 MB .zip directly / building a package > 250 MB unzipped**
> Severity: Medium
> Confidence: 🟢 High
- Why: direct upload limit 50 MB zipped; 250 MB unzipped including layers and custom runtimes [S1][S2].
- Impact: deploy rejected at apply time.
- ❌ Wrong:
  ```bash
  aws lambda update-function-code --function-name my-function --zip-file fileb://function.zip   # 80 MB zip
  ```
- ✅ Correct:
  ```bash
  aws lambda update-function-code --function-name my-function --s3-bucket my-bucket --s3-key function.zip --s3-object-version <v>
  ```
- Source: [S1], [S2], [S29] (2026-10-28)

**N8. Treating `StatusCode: 200` alone as a passing smoke test**
> Severity: High
> Confidence: 🟢 High
- Why: `FunctionError` "if present, indicates that an error occurred during function execution"; the synchronous status code is 200 for `RequestResponse` [S26]; with an alias, `ExecutedVersion` tells which version actually ran [S26][S5].
- Impact: broken release promoted; or smoke hit the old version of a weighted alias.
- ❌ Wrong:
  ```bash
  aws lambda invoke ... meta.json && echo PASS
  ```
- ✅ Correct:
  ```bash
  jq -e '.StatusCode==200 and (has("FunctionError")|not) and .ExecutedVersion=="8"' meta.json && echo PASS
  ```
- Source: [S5], [S26] (2026-10-28)

---

## Migration Guide

> Confidence: 🟡 Medium | AWS docs have no versioned changelog for the deploy procedure; "changes" below are differences an older-memory skill would get wrong, each sourced to the current page (2026-10-28).

**Breaking / easy-to-miss changes (current docs vs older patterns)**:
- `-v2` waiters (`function-active-v2`, `function-updated-v2`) use **GetFunction**, poll every 1 s, give up after 300 checks; the v1 `function-active` / `function-updated` use GetFunctionConfiguration, 5 s x 60 [S22][S23][S25][S37]. Prefer v2 for create/update; use `published-version-active` after publishing [S24].
- Docs now call standard Lambda functions **"Event Functions"** and separately document Lambda Web Functions, Lambda MicroVMs and Lambda Managed Instances [S1]. Limits such as timeout 1-5400 s and memory up to 32768 MB in CLI output patterns [S30] apply to Managed Instances; for Event Functions use 900 s and 128-10,240 MB [S1] (32768 attribution: medium confidence).
- `$LATEST.PUBLISHED` qualifier exists in CLI patterns (Lambda Managed Instances only; out of scope) [S24][S35].
- S3 code storage mode `COPY`/`REFERENCE` (self-managed S3 code storage) [S2]; with `REFERENCE`, losing the object makes the function `Inactive` [S7].
- `State` enumerations now include `Deactivating`, `Deactivated`, `ActiveNonInvocable`, `Deleting` [S27][S30] in addition to the four described in the guide [S7].
- No dedicated "lambda-rollback" page exists (fetched URL had no body) [S36]; rollback is documented via weighted alias routing [S5] and runtime rollback [S20].

**Upgrade Steps** (moving an existing "deploy to $LATEST" setup to this procedure):
1. Enable version publishing and create an alias in the Terraform module (`provisioning-aws-lambda-v6`; `publish` defaults to false there [I2]).
2. Repoint triggers, API Gateway integrations and resource-based permissions to the alias ARN [S6][S34].
3. Add post-apply verification: `wait function-updated-v2`, `wait published-version-active`, alias smoke test [S22][S24][S26].
4. Record the previous version number before each apply (rollback target) [S5].

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| AWS CLI | v2 (2.39.0 reference read) | — | `--cli-binary-format raw-in-base64-out` required for inline payloads per docs [S26] |
| Terraform provider | hashicorp/aws 6.x | 6.x | HCL in provisioning-aws-lambda-v6 [I2] |
| SnapStart runtimes | Java 11+, Python 3.12+, .NET 8+ | — | not OS-only runtimes (so not Quarkus native) [S8][I3 rows 13,16] |
| Java managed runtimes (family) | java17.al2023 / java21 / java25 | — | per family fact row 15 [I3] |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official CLI reference + Lambda Developer Guide]. Terraform steps follow repo policy [I1]; HCL lives in `provisioning-aws-lambda-v6`.

**Lifecycle** (the procedure the `aws-lambda-deployer` agent follows):
```bash
# Representative — adapt to your environment. M = mutating (needs relayed user approval). R = read-only.
# 0. Pre-flight (R)
#    - artifact exists, sizes within 50 MB zipped (or S3) / 250 MB unzipped incl. layers, <= 5 layers   [S1][S2]
#    - handler/runtime in the module match the artifact (family: Quarkus handler + runtime rows 11,13,15) [I3]
#    - execution role exists, has logs:CreateLogGroup/CreateLogStream/PutLogEvents (AWSLambdaBasicExecutionRole) [S17]
#      plus secretsmanager:GetSecretValue / kms:Decrypt where used                                       [S11][S12]
#    - timeout <= 900 s, memory 128-10,240 MB, env vars <= 4 KB, no secret values in env vars             [S1][S10]
#    - record current alias target as PREV:
aws lambda get-alias --function-name my-function --name live --query FunctionVersion --output text   # (get-alias page not fetched; medium)
# 1. Plan (R)
terraform plan -input=false -out=tfplan                               # [I1]
# 2. Review with the user -> STOP until explicit approval is relayed  # unit rule
# 3. Apply (M)
terraform apply -input=false tfplan                                   # [I1]
# 4. Verify Lambda finished (R)
aws lambda wait function-updated-v2 --function-name my-function       # [S22]
aws lambda wait published-version-active --function-name my-function --qualifier <NEW>   # [S24]
aws lambda get-function-configuration --function-name my-function:<NEW> \
  --query '{State:State,Upd:LastUpdateStatus,Sha:CodeSha256,Snap:SnapStart.OptimizationStatus}'  # [S9][S30]
# 5. Smoke (executes function code -> use side-effect-free payloads)
aws lambda invoke --function-name my-function --qualifier live --cli-binary-format raw-in-base64-out \
  --payload file://smoke-event.json --log-type Tail out.json > meta.json                   # [S26]
#    + HTTP check against the API Gateway stage invoke URL                                  # [S34]
# 6. Canary steps (M, if C1-B): further approved applies raising AdditionalVersionWeights, then full move   [S5]
# 7. Rollback (M, on failure): alias -> PREV, routing cleared (A7)                          [S5][S28]
# 8. Prune (M, later): delete-function --qualifier <old N>, never the alias targets          [S31]
```

**Integration**: Lambda deploy ↔ API Gateway (REST, stage-variable integration)
```bash
# Representative — a stage variable value may be a local name with alias/version, e.g. HelloWorld:alpha (not an ARN) [S34]
# Each alias/version referenced needs a Lambda permission, otherwise the method returns 500 Internal Server Error [S34]
aws lambda add-permission --function-name arn:aws:lambda:<region>:<acct>:function:HelloWorld:alpha \
  --source-arn arn:aws:execute-api:<region>:<acct>:<api-id>/*/GET/lambdav1 \
  --principal apigateway.amazonaws.com --statement-id <guid> --action lambda:InvokeFunction
curl -s -o /dev/null -w '%{http_code}\n' "https://<api-id>.execute-api.<region>.amazonaws.com/<stage>/lambdav1"   # expect 200 (local tool)
```
(The alias-qualified `--function-name` form in add-permission combines S6's `--qualifier` semantics with S34's command shape - medium confidence; S6 shows `--qualifier PROD`. The invoke URL host format is not quoted from a fetched page - medium confidence.)

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment; none of these were executed by this research
terraform fmt -check && terraform validate                         # repo rules [I1]
terraform plan -input=false -out=tfplan                            # Expected: only intended changes to function/version/alias
aws lambda wait function-updated-v2 --function-name my-function    # Expected: rc 0; rc 255 after 300 failed checks [S22]
aws lambda wait published-version-active --function-name my-function --qualifier <N>   # rc 0; rc 255 after 312 checks [S24]
aws lambda invoke --function-name my-function --qualifier live --invocation-type DryRun /dev/null
# Expected: StatusCode 204 [S26]
aws lambda invoke --function-name my-function --qualifier live --cli-binary-format raw-in-base64-out \
  --payload file://smoke-event.json --log-type Tail out.json
# Expected: {"StatusCode": 200, "ExecutedVersion": "<N>", "LogResult": "..."} and no "FunctionError" key [S26]
```

**Mocking**: no AWS mocking framework is part of the deploy procedure. Pre-apply checks are offline (`terraform validate`, fully
mocked `terraform test` per `aws-terraform-engineer` scope); the smoke test is the only live check and must use a
side-effect-free payload (internal recommendation, medium confidence). `DryRun` checks permissions without running code [S26].

---

## Production Readiness

- **Performance**: the update itself does not interrupt traffic - invocations use previous code until `LastUpdateStatus` is `Successful` [S7]. SnapStart version publish adds snapshot time while the version is `Pending` [S9]. PC allocation is asynchronous (`IN_PROGRESS` -> `READY`) [S14][S33].
- **Scalability**: per function, 1,000 execution environments every 10 s; default 1,000 concurrent executions per Region; control-plane APIs 15 req/s across all APIs, `GetFunction` 100 req/s (the v2 waiters poll `GetFunction` every 1 s) [S1][S22].
- **Monitoring**: watch the `ExecutedVersion` dimension during weighted routing [S5]; `SignatureValidationErrors` when code signing is `Warn` [S15]; logs in `/aws/lambda/<function-name>`, may take 5-10 min to appear [S17]; Live Tail has no 4 KB limit [S18].
- **Security**: secrets in Secrets Manager/SSM, not env vars [S10][S12]; optional CMK for env vars [S11]; optional code signing [S15]; permissions scoped to alias ARNs [S6]; credentials never in Terraform files [I1].
- **Cost**: PC is billed continuously [S14]; SnapStart caching for Python/.NET per published version while active, min 3 h, Java no extra cost [S8]; code storage 300 GB/Region shared by all versions [S1].

---

## Reference Implementations

- AWS weighted alias canary walkthrough (CLI) — https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html [S5]
- AWS SnapStart activate/publish/verify sequence (CLI) — https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html [S9]
- AWS log tail decode example — https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html [S18]
- AWS runtime rollback via published versions — https://docs.aws.amazon.com/lambda/latest/dg/runtime-management-rollback.html [S20]
- Lambda Version Cleanup pattern (Serverless Land, linked from S8) — not fetched (unverified content)
- Internal: `packages/aws-terraform/.apm/skills/provisioning-aws-lambda-v6/SKILL.md` (HCL) [I2]

---

## Source Bibliography

**Primary** (all read 2026-10-28; "full" = full page markdown received; "extract" = page read through a targeted extraction, not reviewed end-to-end = partly read):

| ID | Page | URL | Read |
|---|---|---|---|
| S1 | Lambda quotas | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html | full |
| S2 | Deploying Event Functions as .zip | https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html | full |
| S3 | Manage function versions | https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html | full |
| S4 | Create an alias | https://docs.aws.amazon.com/lambda/latest/dg/configuration-aliases.html | full |
| S5 | Canary deployments using a weighted alias | https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html | full |
| S6 | Aliases in event sources and permissions | https://docs.aws.amazon.com/lambda/latest/dg/using-aliases.html | full |
| S7 | Event Function states | https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html | full |
| S8 | SnapStart overview | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html | full |
| S9 | Activating and managing SnapStart | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html | full |
| S10 | Environment variables | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html | full |
| S11 | Securing environment variables | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars-encryption.html | full |
| S12 | Secrets Manager in Lambda | https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html | full |
| S13 | Reserved concurrency | https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html | full |
| S14 | Provisioned concurrency | https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html | full |
| S15 | Code signing | https://docs.aws.amazon.com/lambda/latest/dg/configuration-codesigning.html | full |
| S16 | Creating code signing configurations | https://docs.aws.amazon.com/lambda/latest/dg/configuration-codesigning-create.html | full (no CLI examples on page) |
| S17 | Sending logs to CloudWatch Logs | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html | full |
| S18 | Viewing CloudWatch logs | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html | full |
| S19 | Runtime version updates | https://docs.aws.amazon.com/lambda/latest/dg/runtimes-update.html | full |
| S20 | Rolling back a runtime version | https://docs.aws.amazon.com/lambda/latest/dg/runtime-management-rollback.html | full |
| S21 | CLI `lambda wait` index (AWS CLI 2.39.0) | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/index.html | extract |
| S22 | CLI `wait function-updated-v2` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-updated-v2.html | extract |
| S23 | CLI `wait function-active-v2` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-active-v2.html | extract |
| S24 | CLI `wait published-version-active` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/published-version-active.html | extract |
| S25 | CLI `wait function-updated` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-updated.html | extract |
| S26 | CLI `invoke` | https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html | extract |
| S27 | CLI `publish-version` | https://docs.aws.amazon.com/cli/latest/reference/lambda/publish-version.html | extract |
| S28 | CLI `update-alias` | https://docs.aws.amazon.com/cli/latest/reference/lambda/update-alias.html | extract |
| S29 | CLI `update-function-code` | https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html | extract |
| S30 | CLI `get-function-configuration` | https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html | extract |
| S31 | CLI `delete-function` | https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html | extract |
| S32 | API `AliasRoutingConfiguration` | https://docs.aws.amazon.com/lambda/latest/api/API_AliasRoutingConfiguration.html | full |
| S33 | API `PutProvisionedConcurrencyConfig` | https://docs.aws.amazon.com/lambda/latest/api/API_PutProvisionedConcurrencyConfig.html | full |
| S34 | API Gateway: stage variables for REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/amazon-api-gateway-using-stage-variables.html | full |
| S35 | `$LATEST.PUBLISHED` in Lambda Managed Instances | https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-version-publishing.html | search-result snippet only (not fetched) |
| S36 | lambda-rollback (requested by brief) | https://docs.aws.amazon.com/lambda/latest/dg/lambda-rollback.html | fetched, empty body - no content usable |
| S37 | CLI `wait function-active` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-active.html | extract |

Note: `awscli.amazonaws.com/v2/documentation/api/latest/reference/lambda/*` URLs 301-redirect to `docs.aws.amazon.com/cli/latest/reference/lambda/*` (observed 2026-10-28).

**Internal (repo policy / family inputs, not AWS facts)**:

| ID | File |
|---|---|
| I1 | `c:\agents\agents-factory\.claude\rules\terraform-standards.md` (Always-Do #6, Never-Do #3); `-input=false` from `.claude/rules/terraform-cicd.md` |
| I2 | `c:\agents\agents-factory\packages\aws-terraform\.apm\skills\provisioning-aws-lambda-v6\SKILL.md` (`publish` default false, `snap_start` block, `source_code_hash`) |
| I3 | `c:\agents\agents-factory\workspace\quarkus-aws-saas\_family_facts_v3.40.md` rows 11, 13, 15, 16, 21 |
| I4 | `c:\agents\agents-factory\workspace\quarkus-aws-saas\_family_rules_v3.40.md` rules 3, 4, 5, 9-12 |

**Validation**: no community sources used.

---

## Research Gaps

```
Gap: Provisioned concurrency behaviour when an alias with PC is repointed to a new version (re-allocation time, cold starts during the switch)
Impact: possible latency spike / double billing during deploy of PC-backed aliases
Workaround: treat as Ask-First C5; after apply, wait for PC Status READY (get-provisioned-concurrency-config) before shifting traffic (medium confidence)
Follow-up: Lambda dev guide provisioned-concurrency.html and lambda-concurrency.html; AWS::Lambda::Alias ProvisionedConcurrencyConfig docs
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: --log-type Tail returns "first 4 KB" (S18, dev guide) vs "last 4 KB" (S26, CLI reference) of the execution log
Impact: smoke assertions that grep the tail may miss lines
Workaround: state "4 KB, base64, synchronous only" without first/last; use CloudWatch Logs for full output
Follow-up: Invoke API reference LogResult field (API_Invoke.html)
§7-ref: Iteration 3 — IRRESOLVABLE (two official pages disagree)
```
```
Gap: Code signing for container images — S15 says code signing applies to ".zip or container image packages"; S16 says container images "do not support code signing"
Impact: none for this unit (.zip only); matters for any container-image skill
Workaround: scope the skill to .zip; flag the contradiction
Follow-up: AWS Signer developer guide, Lambda workflow
```
```
Gap: Whether the hashicorp/aws 6.x provider waits for LastUpdateStatus=Successful / published version Active before returning from apply (unverified)
Impact: a smoke test immediately after apply could hit old code (S7)
Workaround: always run the read-only waiters after apply (A3, A8)
Follow-up: provisioning-aws-lambda-v6 research / provider docs (owned by that skill)
```
```
Gap: HTTP API (API Gateway v2) Lambda integration referencing an alias, and its permission/500 behaviour (unverified; only REST stage-variable page read)
Impact: smoke expectations for HTTP APIs
Follow-up: API Gateway HTTP API Lambda integration docs
```
```
Gap: `aws lambda get-alias` page and `function-exists` waiter details not fetched (names High from S21; behaviour medium/unverified)
Follow-up: docs.aws.amazon.com/cli/latest/reference/lambda/get-alias.html ; .../wait/function-exists.html
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails A3 | Exact CLI waiter names (brief listed `function-updated-v2` / `function-active-v2`) | Resolved: six waiters listed with API/poll/limits | [S21]-[S25], [S37] (2026-10-28) |
| 1 | Guardrails A7 | `lambda-rollback` page | Resolved: page body empty; rollback sourced from alias routing + runtime rollback pages | [S36], [S5], [S20] (2026-10-28) |
| 2 | Guardrails A8 / N6 | "SnapStart cache cost" family framing | Updated: caching charge applies per published SnapStart version for non-Java; Java has no extra cost; Java snapshots deleted after 14 days idle (rollback caveat) | [S8], [S9] (2026-10-28) |
| 2 | Migration Guide | `$LATEST.PUBLISHED` qualifier in CLI patterns | Resolved: Lambda Managed Instances feature, out of scope | [S24], [S35] (2026-10-28) |
| 3 | Conditional C5 | PC re-allocation when alias repointed | ⚠️ IRRESOLVABLE — no fetched page states it; only weighted-alias fluctuation is documented | [S33] |
| 3 | Guardrails A6 | First vs last 4 KB of LogResult | ⚠️ IRRESOLVABLE — dev guide and CLI reference disagree | [S18], [S26] |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (package limits, S3 upload, code signing, versions, aliases, weighted routing, $LATEST, SnapStart, env vars + KMS, reserved/provisioned concurrency, states + waiters, smoke, rollback, version deletion, pre-flight, Terraform gate)
- [x] Pattern counts driven by domain needs (9 Always, 7 Conditional, 8 Forbidden)
- [x] Every anti-pattern has alternative (❌/✅ side by side); ✅ alternatives use High options only (family rule 9)
- [x] All CLI commands marked representative; none executed
- [x] Integration examples complete (API Gateway REST)
- [x] Sources dated and linked (bibliography, read 2026-10-28; partly-read pages marked "extract")
- [x] Security documented
- [x] 1+ copy-paste working example (representative)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated, except A1 (repo policy, triangulation n/a)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap that survived the loop cross-referenced in §7 (the 2 IRRESOLVABLE rows); remaining gaps are out-of-budget follow-ups

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: read-only checks — pre-flight sizes (A2), `get-function-configuration`, the waiters (A3, A8), `invoke --invocation-type DryRun`; refusing `-auto-approve` and refusing to act on `$LATEST` (N1, N3).
- **Medium Confidence (validate with user)**: secret-name heuristic (A9), `jq` assertion logic (A6), Terraform drift after CLI rollback (C3), PC timing (C5), unzip-size accounting (A2), alias-qualified add-permission form, invoke URL host format.
- **Low Confidence (must ask human)**: the two IRRESOLVABLE items; HTTP API integration behaviour; provider wait semantics.
- **Approval rule**: every mutating step (`terraform apply`, canary weight changes, `update-alias` rollback, `delete-function --qualifier`, concurrency changes) runs only after an explicit user approval relayed by the orchestrator; a relayed approval for a plan covers that saved plan only.
- **Edge Cases (pause)**: Lambda Managed Instances / `$LATEST.PUBLISHED` functions (different invocation semantics) [S35]; container-image functions (out of scope; code-signing contradiction); any SnapStart version idle > 14 days used as rollback target [S9].
- **Emergency Stop**: `LastUpdateStatus = Failed` or `State = Failed` -> stop, do not publish/shift, hand over to D2 `debugging-aws-lambda` [S7].
