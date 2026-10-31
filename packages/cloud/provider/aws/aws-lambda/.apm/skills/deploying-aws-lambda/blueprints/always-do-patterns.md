# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). All commands are representative (adapt to your environment); the research executed none of them. Medium and unverified items live in [ask-first decisions](./ask-first-decisions.md).

## Contents

- [1. Terraform gate](#1-terraform-gate)
- [2. Artifact size pre-flight](#2-artifact-size-pre-flight)
- [3. Waiters after every apply](#3-waiters-after-every-apply)
- [4. Publish a version](#4-publish-a-version)
- [5. Route through an alias](#5-route-through-an-alias)
- [6. Record the rollback target](#6-record-the-rollback-target)
- [7. Smoke test assertions](#7-smoke-test-assertions)
- [8. Rollback by alias](#8-rollback-by-alias)
- [9. SnapStart verification](#9-snapstart-verification)
- [10. Secrets outside env vars](#10-secrets-outside-env-vars)

## 1. Terraform gate

Repo policy, not an AWS fact: the rules `aws-lambda-deployment-preflight` (package `aws-lambda`: saved plan, relayed approval, apply `tfplan` only) and `aws-terraform-skills-management` (package `aws-terraform`: plan with `-out`, never `-auto-approve`). `-input=false` is an internal convention.

```bash
terraform plan -input=false -out=tfplan      # show the plan output to the user
# STOP: wait for the line  approval: apply plan=tfplan sha256=<hash> by=<user> at=<UTC> relayed-by=<orchestrator>
sha256sum tfplan                             # must equal <hash>; a regenerated plan voids the approval
terraform apply -input=false tfplan          # exactly the reviewed plan; no -auto-approve
```

- An approval relayed for one saved plan covers that saved plan only. A new or regenerated plan needs a new approval; on a sha256 mismatch stop with `needs-input`.
- Publishing the version and moving the alias of that release are part of the approved apply step.
- Other mutating steps use their own relayed approval: `approval: rollback alias=<alias> to=<PREV version> ...` for a rollback; each canary weight step is a Terraform apply with its own `approval: apply` line for its own saved plan. `delete-function --qualifier` is never run by the deployer: return the exact command as a proposal under `## Cleanup proposal`; the outcome is unchanged (a good release stays `success`).

## 2. Artifact size pre-flight

Direct upload is limited to 50 MB zipped; larger files must come from S3 in the same Region; the unzipped contents including layers and custom runtimes are limited to 250 MB; at most 5 layers ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [.zip deployment](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html), [update-function-code](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html)). Lambda docs use "MB" for 1,024 KB. Full script: [preflight](./preflight-and-plan.md#artifact-size-check).

## 3. Waiters after every apply

While `LastUpdateStatus` is `InProgress`, `State` stays `Active`, invocations keep using the previous code, and `UpdateFunctionCode`, `UpdateFunctionConfiguration`, `PublishVersion` and `TagResource` fail ([function states](https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html)).

```bash
aws lambda wait function-updated-v2 --function-name my-function            # after update
aws lambda wait function-active-v2  --function-name my-function            # after create
aws lambda wait published-version-active --function-name my-function --qualifier <N>   # after publish
aws lambda get-function-configuration --function-name my-function \
  --query '{State:State,LastUpdateStatus:LastUpdateStatus,Reason:LastUpdateStatusReason,Code:LastUpdateStatusReasonCode,Sha:CodeSha256}'
# Expected: State=Active, LastUpdateStatus=Successful
```

Whether the `hashicorp/aws` 6.x provider already waits before returning from apply is (unverified), so the waiters always run. Budgets and exit codes: [apply blueprint](./apply-waiters-publish-alias.md#waiters).

## 4. Publish a version

"Any time you deploy your function code, you overwrite the current code in `$LATEST`"; a published version locks code, runtime, architecture, memory, layers and most configuration; version numbers are never reused ([versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)). `publish-version --code-sha256` publishes only if the hash matches ([CLI](https://docs.aws.amazon.com/cli/latest/reference/lambda/publish-version.html)). Whether Terraform or the CLI publishes is in [apply blueprint](./apply-waiters-publish-alias.md#publish).

## 5. Route through an alias

An alias is an updatable pointer to a version and cannot point to another alias; event source mappings and resource policies that use the alias ARN need not change when the version changes. A permission granted on an alias gives a permission error when invoked unqualified or through the underlying version ([aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuration-aliases.html), [using aliases](https://docs.aws.amazon.com/lambda/latest/dg/using-aliases.html)).

```bash
aws lambda add-permission --function-name my-function --qualifier live --statement-id <id> \
  --principal <service>.amazonaws.com --action lambda:InvokeFunction --source-arn <arn>   # inside the approved apply only
```

In this project aliases are Terraform resources (`provisioning-aws-lambda-v6`); the CLI shape is shown only to explain the semantics.

## 6. Record the rollback target

```bash
PREV=$(aws lambda get-alias --function-name my-function --name live --query FunctionVersion --output text)
```

Published versions are immutable, so the version number is a complete rollback target ([versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)). The `get-alias` reference page was not fetched; its use here is (medium confidence), register M5.

## 7. Smoke test assertions

The real invoke needs `approval: smoke payload=<file or sha256> by=<user> at=<UTC> relayed-by=<orchestrator>`; `DryRun` needs none. `invoke` returns `StatusCode` (200 for `RequestResponse`, 202 `Event`, 204 `DryRun`), `FunctionError` when the function errored, `LogResult` (base64, `--log-type Tail`, synchronous only) and `ExecutedVersion`, which tells the version an alias resolved to ([CLI invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)). Full commands: [smoke test](./smoke-test-and-verification.md#smoke-test).

```bash
jq -e '.StatusCode==200 and (has("FunctionError")|not) and .ExecutedVersion=="<NEW>"' meta.json && echo PASS
```

The `jq` assertion is an internal recommendation (medium confidence), register M2.

## 8. Rollback by alias

Mutating: runs only with `approval: rollback alias=<alias> to=<PREV version> by=<user> at=<UTC> relayed-by=<orchestrator>`.

"To route all traffic to version 2, use the update-alias command to change the function-version ... The command also resets the routing configuration" ([weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)). Published versions are snapshots, so repointing rolls back code and configuration together ([runtime rollback](https://docs.aws.amazon.com/lambda/latest/dg/runtime-management-rollback.html)).

```bash
aws lambda update-alias --function-name my-function --name live \
  --function-version "$PREV" --routing-config 'AdditionalVersionWeights={}' --revision-id "$REV"   # only with the approval: rollback line
```

`--revision-id` is a concurrency guard: it avoids overwriting an alias changed since you read it ([CLI](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-alias.html)). Full procedure and SnapStart caveat: [rollback](./rollback-and-cleanup.md).

## 9. SnapStart verification

SnapStart applies only to published versions and aliases pointing to versions, never `$LATEST`; during publish the version is `Pending` and invocations fail ([SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html), [activate](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)).

```bash
aws lambda wait published-version-active --function-name my-function --qualifier <N>
aws lambda get-function-configuration --function-name my-function:<N> \
  --query '{Opt:SnapStart.OptimizationStatus,ApplyOn:SnapStart.ApplyOn,State:State}'
# Expected: {"Opt":"On","ApplyOn":"PublishedVersions","State":"Active"}
```

Restore-time limit conflict (Quarkus guide 2 s vs AWS 10 s) is owned by `developing-quarkus-amazon-lambda-v3-40`; here it only matters as a reason a version can fail to become `Active` (unverified, register U5).

## 10. Secrets outside env vars

AWS recommends Secrets Manager "instead of environment variables to store database credentials and other sensitive information like API keys or authorization tokens"; environment variables are encrypted at rest with an AWS managed key by default and are locked into a published version ([env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html), [encryption](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars-encryption.html)). The AWS Parameters and Secrets Lambda Extension (port 2773, default cache TTL 300 s) reads Secrets Manager and Parameter Store; the execution role needs `secretsmanager:GetSecretValue` ([Secrets Manager](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html)). The pre-flight key-name check is in [preflight](./preflight-and-plan.md#configuration-checks).
