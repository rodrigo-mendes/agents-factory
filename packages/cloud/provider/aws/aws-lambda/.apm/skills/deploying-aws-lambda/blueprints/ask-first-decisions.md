# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Each item is a user decision or rests on medium or unverified evidence. Ask, then proceed.

## Contents

- [C1 Traffic shifting](#c1-traffic-shifting)
- [C2 Upload path](#c2-upload-path)
- [C3 Rollback channel](#c3-rollback-channel)
- [C4 Code signing](#c4-code-signing)
- [C5 Provisioned concurrency](#c5-provisioned-concurrency)
- [C6 Reserved concurrency](#c6-reserved-concurrency)
- [C7 Runtime update mode](#c7-runtime-update-mode)
- [C8 HTTP API and log tail](#c8-http-api-and-log-tail)

## C1 Traffic shifting

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A all-at-once alias move | simplicity, one apply | blast radius is 100% | low traffic, strong smoke test |
| B weighted alias (Terraform-driven steps) | small blast radius, Terraform only | one approved apply (own `approval: apply` line, own saved plan) per weight step; noisy split at low traffic | production APIs |
| C CodeDeploy configurations (for example `Linear10PercentEvery2Minutes`) | automatic shifting and alarm rollback | AWS documents it only through SAM and CodeDeploy, out of scope | the organisation already standardised on CodeDeploy |

Constraints for B: [apply blueprint](./apply-waiters-publish-alias.md#alias-move-and-canary). Sources: https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html ; https://docs.aws.amazon.com/lambda/latest/api/API_AliasRoutingConfiguration.html.
Ask: "All at once, weighted canary (which weights and steps), or CodeDeploy (outside this skill)?"

## C2 Upload path

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Direct upload (up to 50 MB zipped) | fewest moving parts | 50 MB cap | small zips |
| S3 with code storage mode `COPY` (default; Lambda-managed storage, counts toward 300 GB) | above 50 MB, versioned object for audit | storage quota | most Terraform setups |
| S3 with `REFERENCE` (self-managed; Lambda keeps no separate copy) | avoids the 300 GB quota | deleting the object or revoking bucket permissions makes the function `Inactive` | many versions or large code |

Sources: https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html ; https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html. Terraform argument names live in `provisioning-aws-lambda-v6`.
Ask: "Which upload path does the Terraform module use?"

## C3 Rollback channel

Options in [rollback](./rollback-and-cleanup.md#rollback-channel). The AWS mechanics are High ([weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html), [update-alias](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-alias.html)); that Terraform reports the alias as drifted after an out-of-band `update-alias` is (medium confidence), register M4.
Ask: "Roll back through Terraform or the emergency CLI? Both are mutating and need explicit approval."

## C4 Code signing

Attach a code signing configuration (AWS Signer profiles, up to 20) with `UntrustedArtifactOnDeployment` `Warn` (default: deployment allowed, `SignatureValidationErrors` metric and CloudTrail) or `Enforce` (deployment blocked). Checks: integrity, expiry, mismatch, revocation. Layers must also be signed by an allowed profile. It prevents only new unsigned deployments; existing unsigned code keeps running. No extra charge ([code signing](https://docs.aws.amazon.com/lambda/latest/dg/configuration-codesigning.html), [create configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-codesigning-create.html)).

Conflict, both cited, none picked: the code signing page says it applies to ".zip or container image packages"; the creation page says container images "do not support code signing" (irresolvable, register I3). It does not affect .zip functions, which this skill covers.
Ask: "Does the account require signed artifacts, and Warn or Enforce?"

## C5 Provisioned concurrency

Facts: configured on a version or alias, never `$LATEST`; allocation status `IN_PROGRESS`, `READY` or `FAILED`; billed continuously; runs init code at allocation; with a weighted alias configure higher provisioned concurrency while routing is active; `AllocatedProvisionedConcurrentExecutions` fluctuates during canary deployments; provisioned concurrency must not exceed reserved concurrency when both are set; SnapStart is incompatible ([provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html), [API](https://docs.aws.amazon.com/lambda/latest/api/API_PutProvisionedConcurrencyConfig.html), [weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)).

What happens to provisioned environments when an alias is repointed to a new version is not stated on the pages read (unverified, irresolvable, register I1). Working approach: wait for status `READY` (`get-provisioned-concurrency-config`) before shifting traffic (medium confidence), register M9.
Ask: "Does the alias have provisioned concurrency? If yes, plan for allocation time and cost during the shift."

## C6 Reserved concurrency

Reserved concurrency is both floor and ceiling, no extra charge; `0` throttles all invocations until removed; changing it does not create a new version ([reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html), [versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)). A plan that sets it to 0 is a production outage by design.
Ask: "May this apply change reserved concurrency in the same release as the code?"

## C7 Runtime update mode

Auto (default) patches published versions in rollout phase 2. Function update applies the newest runtime only when you update the function, so published versions are static snapshots and an alias rollback also rolls back the runtime. Manual pins a runtime version ARN and is meant only as a temporary mitigation ([runtime updates](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-update.html), [runtime rollback](https://docs.aws.amazon.com/lambda/latest/dg/runtime-management-rollback.html)).
Ask: "Must a rollback also revert the runtime patch level (Function update mode)?"

## C8 HTTP API and log tail

- HTTP API (API Gateway v2) integration with an alias, its permission and error behaviour: not researched (unverified), register U2. Ask which API type fronts the function; for REST see [apply blueprint](./apply-waiters-publish-alias.md#api-gateway-rest-integration).
- Log tail: the Lambda guide says "first 4 KB" and the CLI reference says "last 4 KB" (irresolvable, register I2). State "4 KB, base64, synchronous only" and read CloudWatch Logs for full output ([smoke test](./smoke-test-and-verification.md#log-tail)).
Ask: "Which API type fronts the function, and is CloudWatch Logs readable for the full output?"
