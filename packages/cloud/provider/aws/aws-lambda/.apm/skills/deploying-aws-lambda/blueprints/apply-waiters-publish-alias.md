# Apply, Waiters, Publish and Alias

Back to [SKILL.md](../SKILL.md). Representative commands, none executed by the research.

## Contents

- [Apply](#apply)
- [Waiters](#waiters)
- [Publish](#publish)
- [Alias move and canary](#alias-move-and-canary)
- [SnapStart check](#snapstart-check)
- [API Gateway REST integration](#api-gateway-rest-integration)

## Apply

Mutating (M). Only with the `approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC> relayed-by=<orchestrator>` line (gate in [preflight](./preflight-and-plan.md#plan-and-approval-gate)); re-check the sha256 of the plan file first. Publishing the version and moving the alias of this release are part of the approved apply step.

```bash
terraform apply -input=false tfplan     # the saved, reviewed plan; no -auto-approve
```

Then run the waiters below before any publish, invoke or further update.

## Waiters

The CLI has six Lambda waiters ([index](https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/index.html)). The poll intervals, give-up budgets and exit code 255 below, and the `--qualifier` option, come from pages read through a targeted extraction, not end-to-end, with no verbatim quote recorded (coverage limit L1): treat every number in the table as (medium confidence, L1).

| Waiter | API polled | Poll | Gives up | Use after |
|---|---|---|---|---|
| `function-active` | GetFunctionConfiguration | 5 s | 60 failed checks, rc 255 (medium confidence, L1) | create (v1) |
| `function-active-v2` | GetFunction | 1 s | 300 failed checks, rc 255 (medium confidence, L1) | create |
| `function-updated` | GetFunctionConfiguration | 5 s | 60 failed checks, rc 255 (medium confidence, L1) | update (v1) |
| `function-updated-v2` | GetFunction | 1 s | 300 failed checks, rc 255 (medium confidence, L1) | update |
| `published-version-active` | GetFunctionConfiguration | 5 s | 312 failed checks, rc 255 (medium confidence, L1) | publish-version |
| `function-exists` | page not recorded | page not recorded | page not recorded | not recorded (unverified), register U3 |

Sources: https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/index.html (list of six), then `.../wait/function-active.html`, `function-active-v2.html`, `function-updated.html`, `function-updated-v2.html`, `published-version-active.html`.

- Prefer the v2 waiters for create and update; use `published-version-active` after publishing.
- The v2 waiters poll `GetFunction` every second (medium confidence, L1); control-plane APIs allow 15 requests per second across all APIs and `GetFunction` 100 requests per second ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)).
- `State` after creation is `Pending`; `Invoke`, `UpdateFunctionCode`, `UpdateFunctionConfiguration` and `PublishVersion` fail until `Active`. On `LastUpdateStatus=Failed`, `State` stays `Active` and invocations keep using the previous code ([function states](https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html)).
- `State` values also include `Deactivating`, `Deactivated`, `ActiveNonInvocable` and `Deleting` ([publish-version](https://docs.aws.amazon.com/cli/latest/reference/lambda/publish-version.html), [get-function-configuration](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html)).
- The provider's own waiting is (unverified), register U1: always run the waiter even if apply returned success.

```bash
aws lambda wait function-updated-v2 --function-name my-function
aws lambda get-function-configuration --function-name my-function \
  --query '{State:State,Upd:LastUpdateStatus,Reason:LastUpdateStatusReason,Code:LastUpdateStatusReasonCode}'
```

On `Failed`: read `LastUpdateStatusReason` and `LastUpdateStatusReasonCode`, stop, do not publish or shift, hand over to `debugging-aws-lambda`.

## Publish

Lambda publishes a new version only if code or a qualifying setting changed (code, environment variables, runtime, handler, layers, memory, timeout, VPC, DLQ, role, description, architecture, ephemeral storage, package type, code storage mode, logging, file system, SnapStart, tracing). A reserved concurrency change does not produce a version ([versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)).

In this project the Terraform module normally publishes (the `publish` argument defaults to false in `provisioning-aws-lambda-v6`, so confirm the module enables it). CLI shape, for a pipeline that publishes outside Terraform (mutating: it is part of the approved apply step and needs the `approval: apply` line; without that line, do not run it):

```bash
SHA=$(aws lambda get-function-configuration --function-name my-function --query CodeSha256 --output text)
aws lambda publish-version --function-name my-function --code-sha256 "$SHA" --description "release <git-sha>"   # inside the approved apply only
aws lambda wait published-version-active --function-name my-function --qualifier <N>
```

`--code-sha256` publishes only if the hash matches the current code; `--revision-id` only if configuration is unchanged since you read it ([CLI](https://docs.aws.amazon.com/cli/latest/reference/lambda/publish-version.html)).

## Alias move and canary

All-at-once: `update-alias --function-version <NEW>` (inside the approved apply only; [CLI](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-alias.html)). Weighted canary: the alias stays on the stable version and `AdditionalVersionWeights={"<NEW>"=0.05}` sends a fraction to the new one; raise the weight in later Terraform applies, each with its own `approval: apply` line, then move `function-version` to `<NEW>` and clear weights. Constraints: at most two versions, both published, same execution role, same DLQ configuration or none, never `$LATEST`; weight 0.0 to 1.0, key is the version number ([weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html), [AliasRoutingConfiguration](https://docs.aws.amazon.com/lambda/latest/api/API_AliasRoutingConfiguration.html)). The split is probabilistic; at low traffic the observed split can differ greatly from the configured one. Which version served a request: `ExecutedVersion`, header `x-amz-executed-version`, the log line `START RequestId: ... Version: N`, or the `ExecutedVersion` metric dimension. Each step is an approved apply with its own `approval: apply` line ([C1](./ask-first-decisions.md#c1-traffic-shifting)).

## SnapStart check

```bash
aws lambda wait published-version-active --function-name my-function --qualifier <N>
aws lambda get-function-configuration --function-name my-function:<N> \
  --query '{Opt:SnapStart.OptimizationStatus,ApplyOn:SnapStart.ApplyOn,State:State}'
# Expected: {"Opt":"On","ApplyOn":"PublishedVersions","State":"Active"}
```

SnapStart supports Java 11+, Python 3.12+ and .NET 8+ managed runtimes, not OS-only runtimes; not with provisioned concurrency, EFS, S3 Files or ephemeral storage above 512 MB; a new snapshot needs a new published version ([SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html), [activate](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)). JVM with SnapStart versus native is the build skill's decision, never a default here.

## API Gateway REST integration

A REST API stage variable can hold a local function name with an alias or version (for example `HelloWorld:alpha`, not an ARN). Each alias or version referenced needs a Lambda permission, otherwise the method returns `500 Internal Server Error` ([stage variables](https://docs.aws.amazon.com/apigateway/latest/developerguide/amazon-api-gateway-using-stage-variables.html)).

```bash
aws lambda add-permission --function-name arn:aws:lambda:<region>:<acct>:function:HelloWorld:alpha \
  --source-arn arn:aws:execute-api:<region>:<acct>:<api-id>/*/GET/lambdav1 \
  --principal apigateway.amazonaws.com --statement-id <guid> --action lambda:InvokeFunction   # inside the approved apply only
```

Combining the alias-qualified `--function-name` form with that command shape is (medium confidence), register M6; the unqualified-function `--qualifier` form is the one the aliases page shows. HTTP API (v2) behaviour was not researched (unverified), register U2.
