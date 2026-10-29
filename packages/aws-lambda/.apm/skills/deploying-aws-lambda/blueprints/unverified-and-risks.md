# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 91%, a deep run using all 3 iterations, and 8 triangulated Always-Do patterns. Its header counts 5 unverified and 2 irresolvable items; this register lists 6 and 3 because U6 was added by this skill (the research states the 14-day caveat for Java only) and I3 (code signing and container images) is a gap in the research that it did not label irresolvable. Family facts verified by the orchestrator on 2026-10-28 keep their tags. All commands in the research are representative; none was executed (L5).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- The AWS Lambda Developer Guide and CLI reference are continuously published and carry no semantic version; the snapshot is 2026-10-28 (CLI reference 2.39.0). Waiter budgets, quotas and flags can change without notice; re-read the pages before relying on them.
- Lambda Managed Instances, Web Functions and MicroVMs are documented next to Event Functions; their semantics (for example `$LATEST.PUBLISHED`) differ and are out of scope.
- The repo policy for apply (rules `aws-lambda-deployment-preflight` and `aws-terraform-skills-management`) is not an AWS fact and can change independently.

## Unverified items

6 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Whether `hashicorp/aws` 6.x waits for `LastUpdateStatus=Successful` or an active published version before apply returns | A smoke test right after apply could hit old code; always run the waiters |
| U2 | HTTP API (API Gateway v2) integration with an alias, its permission and 500 behaviour; only the REST stage-variable page was read | Ask which API type fronts the function |
| U3 | `function-exists` waiter behaviour (page not fetched; the name is confirmed by the CLI waiter index) | Do not use it in the procedure |
| U4 | Content of the Serverless Land "Lambda Version Cleanup" pattern linked from the SnapStart page | Use `list-versions-by-function` and `delete-function --qualifier` |
| U5 | Which SnapStart restore limit applies: the Quarkus guide says restoration is limited to 2 seconds, AWS says 10 seconds or `SnapStartTimeoutException` (family fact; both quotes High) | Cite both; owned by the build skill |
| U6 | Whether the 14-day snapshot deletion applies to Python and .NET SnapStart versions (family fact is stated for Java) | Treat a rollback to an old version of those runtimes as possibly slow; verify with `get-function-configuration` |

## Irresolvable items

3 irresolvable items (two official pages disagree, or no fetched page states it).

| ID | Item | Why irresolvable and what to do |
|---|---|---|
| I1 | Provisioned concurrency behaviour when an alias with it is repointed to a new version (re-allocation time, cold starts during the switch) | No fetched page states it; only weighted-alias fluctuation is documented. Ask first (C5) |
| I2 | `--log-type Tail`: "first 4 KB" (viewing logs page) vs "last 4 KB" (CLI invoke reference) | Two official pages disagree. State "4 KB, base64, synchronous only"; use CloudWatch Logs for full output |
| I3 | Code signing for container images: the code signing page says ".zip or container image packages", the creation page says container images "do not support code signing" | Two official pages disagree. No effect on .zip functions; flag it for any container-image skill |

## Medium-confidence items

10 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | `unzip -l` total equals Lambda's unzipped-size accounting | A local command, not an AWS one |
| M2 | The `jq` smoke assertion (`StatusCode`, no `FunctionError`, `ExecutedVersion`) | Internal recommendation built on documented fields |
| M3 | Secret-name heuristic over environment variable keys | Internal check, not an AWS rule; false positives such as `STRIPE_SECRET_ARN` |
| M4 | Terraform reports the alias as drifted after an emergency CLI `update-alias` | Terraform behaviour, not researched |
| M5 | `get-alias` output (`FunctionVersion`, `RevisionId`) | The `get-alias` page was not fetched |
| M6 | Alias-qualified `--function-name` in `add-permission` for API Gateway | Combines two pages; the aliases page shows `--qualifier` |
| M7 | API Gateway invoke URL host format | Not quoted from a fetched page |
| M8 | The 32768 MB memory figure in CLI output patterns belongs to Managed Instances | Attribution inferred |
| M9 | Wait for provisioned concurrency `READY` before shifting traffic | Workaround for I1 |
| M10 | Smoke payloads must be side-effect free | Internal recommendation; the smoke test executes function code |

## Coverage limits

5 coverage limits (pages partly read, not read, or commands not run).

| ID | Limit |
|---|---|
| L1 | The CLI reference pages S21 to S31 and S37 were read through a targeted extraction, not reviewed end-to-end; no verbatim quote is recorded for the waiter poll intervals, give-up budgets and exit code 255, so they carry (medium confidence, L1) wherever they appear |
| L2, L3 | L2: S35 (`$LATEST.PUBLISHED` in Managed Instances) seen only as a search snippet, not fetched. L3: S36 (`lambda-rollback`) returned an empty body |
| L4 | S16 (creating code signing configurations) was read in full but has no CLI examples |
| L5 | All CLI and Terraform commands are representative; the research executed none of them |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) provider waits after apply | always-do 3; apply blueprint Waiters | U1 |
| (unverified) HTTP API alias integration | SKILL.md Ask First; ask-first C8; apply blueprint REST section; smoke test | U2 |
| (unverified) `function-exists` waiter | apply blueprint Waiters table | U3 |
| (unverified) Serverless Land cleanup pattern | rollback-and-cleanup | U4 |
| (unverified) which SnapStart restore limit applies | always-do 9 | U5 |
| (unverified) 14-day deletion for Python and .NET | rollback-and-cleanup | U6 |
| (unverified) provisioned concurrency on alias repoint | SKILL.md Ask First; ask-first C5 | I1 (irresolvable; text tag (unverified)) |
| (unverified) first vs last 4 KB of the log tail | SKILL.md Ask First; ask-first C8; smoke test Log tail | I2 (irresolvable; text tag (unverified)) |
| (unverified) code signing and container images | SKILL.md Ask First; ask-first C4 | I3 (irresolvable; text tag (unverified)) |
| (medium confidence) `unzip -l` accounting | preflight Artifact size check | M1 |
| (medium confidence) `jq` assertion | always-do 7; smoke test | M2 |
| (medium confidence) secret-name heuristic | preflight Configuration checks | M3 |
| (medium confidence) Terraform drift after CLI rollback | SKILL.md Ask First; ask-first C3; rollback channel table | M4 |
| (medium confidence) `get-alias` output | always-do 6; preflight; rollback by alias | M5 |
| (medium confidence) alias-qualified `add-permission` | apply blueprint REST section | M6 |
| (medium confidence) invoke URL host format | smoke test | M7 |
| (medium confidence) 32768 MB attribution | migration-notes | M8 |
| (medium confidence) wait for `READY` before shifting | SKILL.md Ask First; ask-first C5 | M9 |
| (medium confidence) side-effect-free smoke payload | smoke test | M10 |
| (medium confidence, L1) waiter poll intervals, give-up budgets, rc 255, one-second `GetFunction` poll | SKILL.md Quick Reference; apply blueprint Waiters table; smoke test Verification Loop | L1 |
| (unverified) and (medium confidence) tags inside scenario expectations | evaluation-scenarios | U1, U2, U5, I1, I2, I3, M2, M4, M9 |

## Source Bibliography

All read 2026-10-28. "Full" means the page markdown was received; "extract" means read through a targeted extraction (L1). The research IDs S1 to S37 and In1 to In4 (research IDs I1 to I4, renamed here because I1 to I3 are register ids) are kept.

**AWS Lambda Developer Guide, API reference, API Gateway**

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
| S16 | Creating code signing configurations | https://docs.aws.amazon.com/lambda/latest/dg/configuration-codesigning-create.html | full, no CLI examples (L4) |
| S17 | Sending logs to CloudWatch Logs | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html | full |
| S18 | Viewing CloudWatch logs | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html | full |
| S19 | Runtime version updates | https://docs.aws.amazon.com/lambda/latest/dg/runtimes-update.html | full |
| S20 | Rolling back a runtime version | https://docs.aws.amazon.com/lambda/latest/dg/runtime-management-rollback.html | full |
| S32 | API `AliasRoutingConfiguration` | https://docs.aws.amazon.com/lambda/latest/api/API_AliasRoutingConfiguration.html | full |
| S33 | API `PutProvisionedConcurrencyConfig` | https://docs.aws.amazon.com/lambda/latest/api/API_PutProvisionedConcurrencyConfig.html | full |
| S34 | API Gateway stage variables for REST APIs | https://docs.aws.amazon.com/apigateway/latest/developerguide/amazon-api-gateway-using-stage-variables.html | full |
| S35 | `$LATEST.PUBLISHED` in Managed Instances | https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-version-publishing.html | snippet only (L2) |
| S36 | lambda-rollback | https://docs.aws.amazon.com/lambda/latest/dg/lambda-rollback.html | empty body (L3) |

**AWS CLI v2 reference (2.39.0), all extracts (L1)**

| ID | Page | URL |
|---|---|---|
| S21 | `lambda wait` index | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/index.html |
| S22 | `wait function-updated-v2` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-updated-v2.html |
| S23 | `wait function-active-v2` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-active-v2.html |
| S24 | `wait published-version-active` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/published-version-active.html |
| S25 | `wait function-updated` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-updated.html |
| S26 | `invoke` | https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html |
| S27 | `publish-version` | https://docs.aws.amazon.com/cli/latest/reference/lambda/publish-version.html |
| S28 | `update-alias` | https://docs.aws.amazon.com/cli/latest/reference/lambda/update-alias.html |
| S29 | `update-function-code` | https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html |
| S30 | `get-function-configuration` | https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html |
| S31 | `delete-function` | https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html |
| S37 | `wait function-active` | https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-active.html |

`awscli.amazonaws.com/v2/documentation/api/latest/reference/lambda/*` URLs 301-redirect to `docs.aws.amazon.com/cli/latest/reference/lambda/*` (observed 2026-10-28). The `get-alias` and `wait function-exists` pages were not fetched. Community sources: none used.

**Internal (repo policy and family inputs, not AWS facts)**

| ID | File | Used for |
|---|---|---|
| In1 | Rules `aws-lambda-deployment-preflight` (package `aws-lambda`) and `aws-terraform-skills-management` (package `aws-terraform`); `-input=false` is an internal convention | apply gate |
| In2 | `provisioning-aws-lambda-v6` skill (`publish` default false) | Terraform default, by name only |
| In3 | Family facts (provenance only, not shipped): runtimes, SnapStart (incl. the 14-day row: https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html) and restore time (https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html) | SnapStart caveats |
| In4 | Family rules 3, 4, 5, 9-12 (provenance only, not shipped); `approval-lines.md` of `coordinating-quarkus-aws-handoffs` (not an AWS fact) | scope, secrets, register format, approval line forms |
