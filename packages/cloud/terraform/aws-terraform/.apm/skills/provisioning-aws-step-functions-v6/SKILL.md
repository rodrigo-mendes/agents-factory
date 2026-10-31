---
name: provisioning-aws-step-functions-v6
description: "Step Functions Terraform (aws 6.x): state machines, aliases, activities, logging, KMS, IAM role. Use when writing HCL for Step Functions. Not for Lambda, EventBridge, CloudWatch, IAM, X-Ray."
---

# Provisioning AWS Step Functions with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the 6.x major line, reference patch 6.70.0 (latest), Terraform ~> 1.16.
> Pages read 2026-10-23 unless a source says otherwise. Claims tagged (unverified) or (medium confidence) are not fully confirmed
> against an official page. Resources: `aws_sfn_state_machine`, `aws_sfn_alias`, `aws_sfn_activity`,
> data source `aws_sfn_state_machine_versions`. Step Functions is regional: the resource pages
> document an optional `region`, for example
> https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown

## Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"`; newest 1.16.x is 1.16.7 (2026-10-23) | https://releases.hashicorp.com/terraform/ (read 2026-10-23) |
| Terraform 1.17.0 | Stable since 2026-10-21, not the target | https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (read 2026-10-22) |
| hashicorp/aws | latest 6.70.0; constraint `~> 6.69`; no 7.x released | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | Withdrawn — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Provider constraint | root `~> 6.69`; reusable module minimum such as `>= 6.0` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| 6.55.0 | Added a list resource for `aws_sfn_state_machine` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable since 2026-10-21; re-verify when starting new work.
- v7 is planned; the 6.0 upgrade guide lists removals:
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
  v7 = a new skill.

**Related skills:** `provisioning-aws-lambda-v6`, `provisioning-aws-eventbridge-v6`,
`provisioning-aws-cloudwatch-v6`, `provisioning-aws-iam-v6`, `provisioning-aws-kms-v6`,
`provisioning-aws-xray-v6`.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation: [terraform block, execution role](./blueprints/always-do-foundation.md)
- State machine: [definition, logging, alias, activity](./blueprints/always-do-state-machine.md)
- Encryption and testing: [customer managed key, terraform test](./blueprints/always-do-encryption-testing.md)
- Never-do configuration: [log ARN, names, alias, backend, version](./blueprints/never-do-configuration.md)
- Never-do IAM and definition: [ViaService, Express, States.ALL, Lambda ARN, logging scope](./blueprints/never-do-iam-asl.md)
- [Corrections and limits](./blueprints/corrections-and-limits.md) — claims seen elsewhere that no provider page supports
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated: https://developer.hashicorp.com/terraform/language/backend/s3
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Set the role trust principal to `states.amazonaws.com` with `sts:AssumeRole`**: https://docs.aws.amazon.com/step-functions/latest/dg/procedure-create-iam-role.html
  See [foundation §2](./blueprints/always-do-foundation.md#2-iam-execution-role).
- **Add the `aws:SourceArn` and `aws:SourceAccount` conditions to the trust policy** — AWS recommends them against confused deputy: https://docs.aws.amazon.com/step-functions/latest/dg/procedure-create-iam-role.html
  See [foundation §2](./blueprints/always-do-foundation.md#2-iam-execution-role).
- **Grant the logging actions, including `logs:CreateLogStream`, on `Resource = "*"`** — they do not support resource scoping: https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html
  See [foundation §2](./blueprints/always-do-foundation.md#2-iam-execution-role).
- **Turn logging on** — Security Hub StepFunctions.1 (medium severity) checks that state machines have logging turned on: https://docs.aws.amazon.com/securityhub/latest/userguide/stepfunctions-controls.html
  See [state machine §3](./blueprints/always-do-state-machine.md#3-state-machine-with-logging-tracing-and-a-published-version).
- **Name CloudWatch log groups with the `/aws/vendedlogs/` prefix**: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html
  See [state machine §3](./blueprints/always-do-state-machine.md#3-state-machine-with-logging-tracing-and-a-published-version).
- **Grant the X-Ray actions `xray:PutTraceSegments`, `xray:PutTelemetryRecords`, `xray:GetSamplingRules` and `xray:GetSamplingTargets` when `tracing_configuration.enabled = true`**: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html
  See [foundation §2](./blueprints/always-do-foundation.md#2-iam-execution-role).
- **Set `publish = true` to publish a version at creation** — it exposes `state_machine_version_arn`: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown
  See [state machine §3](./blueprints/always-do-state-machine.md#3-state-machine-with-logging-tracing-and-a-published-version).
- **Make alias weights total 100 across at most two versions**: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html
  See [state machine §4](./blueprints/always-do-state-machine.md#4-alias-with-weighted-routing).
- **Set `TimeoutSeconds` on Task states** — ASL has no default timeout: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html
  See [state machine §3](./blueprints/always-do-state-machine.md#3-state-machine-with-logging-tracing-and-a-published-version).
- **Retry `Lambda.ServiceException`, `Lambda.AWSLambdaException`, `Lambda.SdkClientException` and `Lambda.ClientExecutionTimeoutException`** on Lambda tasks: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html
  See [state machine §3](./blueprints/always-do-state-machine.md#3-state-machine-with-logging-tracing-and-a-published-version).
- **Tag activities** — Security Hub StepFunctions.2 (low severity) checks that activities are tagged: https://docs.aws.amazon.com/securityhub/latest/userguide/stepfunctions-controls.html
  See [state machine §5](./blueprints/always-do-state-machine.md#5-activity-with-tags).
- **Give the execution role `kms:Decrypt` and `kms:GenerateDataKey`, scoped by `kms:EncryptionContext:aws:states:stateMachineArn`, when using a customer managed key**: https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html
  See [encryption §6](./blueprints/always-do-encryption-testing.md#6-customer-managed-key-encryption).
- **Allow `delivery.logs.amazonaws.com` only `kms:Decrypt` in the key policy when a customer managed key and logging are combined**: https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html
  See [encryption §6](./blueprints/always-do-encryption-testing.md#6-customer-managed-key-encryption).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Definition authoring | `jsonencode({...})` keeps ASL in HCL with native references; `templatefile("x.asl.json", {...})` keeps ASL in a separate file. Both produce the JSON string `definition` requires ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown)). The choice is a team convention (medium confidence). | "Should the definition be inline `jsonencode` or a `templatefile` ASL file?" |
| Unit tests | `terraform test` can use `mock_provider "aws"` and `command = plan` ([source](https://developer.hashicorp.com/terraform/language/tests/mocking)); whether to add it is a team choice. |
| Sync Express encryption | For Sync Express workflows the execution role needs only `kms:Decrypt` ([source](https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html)). | "Is this a Sync Express workflow with a customer managed key?" | "Should this module ship `.tftest.hcl` tests?" See [encryption §7](./blueprints/always-do-encryption-testing.md#7-terraform-test-and-ci). |
| Standard or Express | Express only if under 5 minutes, at-least-once is acceptable, and no `.sync`/`.waitForTaskToken`; Standard for long-running non-idempotent work; Express can be nested in Standard ([source](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html)). Changing `type` forces replacement in Terraform (medium confidence). | "Is this workflow Standard or Express? Replacement is needed to switch later." |
| Definition changes and versions | AWS `UpdateStateMachine` changes definition, role, tracing and logging per revision; in-flight Standard executions keep their revision ([source](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-version.html)). Terraform applies definition changes in place (medium confidence). Whether `publish = true` publishes a new version on each update is (unverified); the page says "during creation". | "Do you need a new version per change? If yes, confirm with `terraform plan` how publishing behaves." |
| Definition formatting diffs | Whether reformatting the JSON (whitespace, key order) causes a permanent diff is (unverified). | "Should we verify with a no-change `terraform plan` after formatting?" |
| Activity encryption type | The provider page documents `AWS_KMS_KEY` or `CUSTOMER_MANAGED_KMS_KEY`; AWS documents `AWS_OWNED_KEY`, so the provider enum may be a doc error (medium confidence). AWS says activity configuration is immutable, so an encryption change needs a new activity (medium confidence for the Terraform replacement behavior) ([source](https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html)). | "Which encryption type for the activity? Test the value before use." |
| Cross-account logging | Whether cross-account log destinations need an explicit CloudWatch Logs resource policy is (unverified). | "Is the log group in another account? Confirm the log policy requirement." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `log_destination` to a log group ARN without `:*` — it must end with `:*`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown)) | Use the log group ARN followed by `:*` |
| Set `name` and `name_prefix` together — `name_prefix` conflicts with `name`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown)) | Set one of the two |
| Point an alias at another alias or an unpublished revision — aliases point only to versions. ([source](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html)) | Use version ARNs from `state_machine_version_arn` or the data source `aws_sfn_state_machine_versions` |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |
| Put `kms:ViaService` on the execution role — it can break executions. ([source](https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html)) | Scope with `kms:EncryptionContext:aws:states:stateMachineArn` |
| Use `.sync` or `.waitForTaskToken` in an EXPRESS state machine — Express supports only Request Response. ([source](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html)) | Use a STANDARD state machine for those patterns |
| Mix `States.ALL` with other names in an `ErrorEquals` array, or use it in a retrier or catcher that is not the last in its `Retry`/`Catch` array — it must appear alone in `ErrorEquals` and in the last retrier/catcher. ([source](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html)) | Put specific errors in earlier retriers/catchers and `States.ALL` alone in the last one |
| Grant `lambda:InvokeFunction` on the unqualified function ARN when invoking with a qualifier, version or alias — Access Denied. ([source](https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html)) | Include the qualifier or `:*` in the Resource |
| Scope the logging delivery actions to a log group ARN — they do not support resource scoping. ([source](https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html)) | `Resource = "*"` for those actions |

## Quick Reference

Pages read 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Required arguments | `definition` (ASL JSON string), `role_arn` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown |
| `type` | `STANDARD` (default) or `EXPRESS` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown |
| Logging `level` | `ALL`, `ERROR`, `FATAL`, `OFF` (default `OFF`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown |
| Encryption type | State machine (provider page): `AWS_OWNED_KEY` or `CUSTOMER_MANAGED_KMS_KEY`; activity enum: see Ask First; reuse period 60-900 s, default 300 (AWS) | https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html |
| Timeouts (state machine) | create 5m, update 1m, delete 5m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown |
| Alias timeouts | create/update/delete 30m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_alias.html.markdown |
| Versions | `publish = true` or data source `aws_sfn_state_machine_versions` (`statemachine_arn` in, `statemachine_versions` out); no page found for an `aws_sfn_state_machine_version` resource (medium confidence, absence of evidence; see [corrections](./blueprints/corrections-and-limits.md)) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/sfn_state_machine_versions.html.markdown |
| Definition substitution | `definition_substitutions` is not listed on the resource page (medium confidence, absence of evidence); `definition` is an ASL JSON string (resource page); `templatefile()` and `jsonencode()` are the substitutes (medium confidence) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown |
| Import | identity `{ arn = "..." }`, `import` block, or `terraform import` (resource page); identity import needs Terraform >= 1.12.0 (vpc page) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown |
| Lambda integration | `arn:aws:states:::lambda:invoke`; result nested under `Payload` | https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html |
| Retry defaults | `IntervalSeconds` 1, `MaxAttempts` 3, `BackoffRate` 2.0, `JitterStrategy` `NONE` | https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html |
| Logging resource policies | 10 per Region per account; 5,120-character size limit | https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html |
| Security Hub | StepFunctions.1 logging (medium severity); StepFunctions.2 activities tagged (low severity) | https://docs.aws.amazon.com/securityhub/latest/userguide/stepfunctions-controls.html |

## 5.x → 6.x Migration (Step Functions)

No entry mentioning `aws_sfn_*` or Step Functions was found in the 6.0.0 upgrade guide, so no
removed or renamed arguments are listed for these resources (medium confidence, absence of evidence)
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown, 2026-10-23).
Regional resources accept an optional `region`, and import into another region uses `<arn>@<region>`
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown).
Upgrade path, per the same guide: "Before upgrading to version `6.0.0`, first upgrade to the latest
available `5.x` version of the provider"; the plan should complete "without errors or unexpected
changes"; update version constraints "to allow the `6.x` series" (this skill uses `~> 6.69`); run
`terraform init -upgrade` "to download the new version".

## External Resources

All read 2026-10-23.

- State machine: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown
- Alias: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_alias.html.markdown
- Activity: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_activity.html.markdown
- Versions data source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/sfn_state_machine_versions.html.markdown
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Step Functions best practices: https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html
- Encryption at rest: https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html
- Logging: https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html
- Security Hub Step Functions controls: https://docs.aws.amazon.com/securityhub/latest/userguide/stepfunctions-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
