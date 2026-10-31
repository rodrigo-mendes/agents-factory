---
name: provisioning-aws-lambda-v6
description: "Lambda Terraform (aws 6.x): functions, aliases, permissions, URLs, event sources, layers, concurrency. Use when writing HCL for Lambda. Not for SAM, API Gateway, EventBridge, SQS, SNS."
---

# Provisioning AWS Lambda with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the **6.x major line**; reference patch 6.69.0 / 6.70.0; Terraform **~> 1.16**.
> Provider pages read **2026-10-23**. Claims tagged (unverified) or (medium confidence) were not fully
> confirmed against an official page. A new major (v7) is a new skill.

## Version Context

| Item | Value | Source (read date) |
|---|---|---|
| Terraform CLI | `~> 1.16` (this skill's target); the constraint admits 1.17.x, which this skill was not verified against | https://releases.hashicorp.com/terraform/ (2026-10-23) |
| hashicorp/aws | latest 6.70.0; constraint `~> 6.69` admits every 6.x release from 6.69 on | https://releases.hashicorp.com/terraform-provider-aws/ (2026-10-23) |
| 6.57.0 | Withdrawn — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (2026-10-23) |
| `region` | Optional on every Lambda resource; change forces replacement; import `id@region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (2026-10-23) |
| Identity-based import (Terraform version) | Requires Terraform ≥ 1.12 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown (2026-10-23) |
| Identity-based import (resources) | Identity import is documented on the function page; for the other Lambda resources see each resource page | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown (2026-10-23) |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable since 2026-10-21 (read 2026-10-23). `~> 1.16` admits it, but this skill was verified against 1.16.x only; re-verify before relying on 1.17.
- aws provider v7 is planned; the upgrade guide already mentions v7 removals
  (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown).
- Lambda runtime support and deprecation dates are time-sensitive. Dates in this skill were read on
  **2026-10-23** from https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html — re-read before choosing a runtime.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Always-do index: [always-do-patterns](./blueprints/always-do-patterns.md)
  - [Function, role, log group](./blueprints/always-do-function.md) · [Image, VPC, KMS, tracing, DLQ](./blueprints/always-do-function-config.md)
  - [Alias, permission, URL, event invoke](./blueprints/always-do-invocation.md) · [Event source mapping, layers, signing](./blueprints/always-do-events-layers.md)
- Never-do index: [never-do-patterns](./blueprints/never-do-patterns.md)
  - [Function arguments](./blueprints/never-do-function.md) · [Event sources](./blueprints/never-do-events.md) · [Role, permissions, provider](./blueprints/never-do-access-provider.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Set `required_version = "~> 1.16"`** — this skill's Terraform target; `~>` semantics:
  https://developer.hashicorp.com/terraform/language/expressions/version-constraints. See [always-do §1](./blueprints/always-do-function.md#1-terraform-block-and-provider-constraint).
- **Set the provider `version = "~> 6.69"`** — this skill's provider target; `~>` semantics:
  https://developer.hashicorp.com/terraform/language/expressions/version-constraints. See [always-do §1](./blueprints/always-do-function.md#1-terraform-block-and-provider-constraint).
- **Give the function exactly one code source** (`filename`, `s3_bucket` + `s3_key`, or `image_uri`) —
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown. See [always-do §3](./blueprints/always-do-function.md#3-zip-function-with-managed-log-group).
- **Set `handler` and `runtime` when `package_type` is `Zip`** —
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown. See [always-do §3](./blueprints/always-do-function.md#3-zip-function-with-managed-log-group).
- **Allow `lambda.amazonaws.com` to call `sts:AssumeRole` in the execution role trust policy** —
  https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html. See [always-do §2](./blueprints/always-do-function.md#2-execution-role).
- **Grant `logs:CreateLogGroup`, `logs:CreateLogStream` and `logs:PutLogEvents` for function logging** —
  https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html. See [always-do §2](./blueprints/always-do-function.md#2-execution-role).
- **Keep the execution role and its VPC policy attachment until the function is destroyed** —
  https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html. See [always-do §5](./blueprints/always-do-function-config.md#5-vpc-attachment).
- **Set `function_response_types = ["ReportBatchItemFailures"]` on SQS mappings** —
  https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html. See [always-do §12](./blueprints/always-do-events-layers.md#12-sqs-event-source-mapping).
- **When setting `scaling_config.maximum_concurrency` on an SQS mapping, use at least 2** —
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown. See [always-do §12](./blueprints/always-do-events-layers.md#12-sqs-event-source-mapping).
- **Set at least one of `on_success` / `on_failure` in an event invoke `destination_config`, or omit the block** —
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_event_invoke_config.html.markdown. See [always-do §11](./blueprints/always-do-invocation.md#11-event-invoke-config).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Runtime choice | Support and deprecation dates change. Read 2026-10-23 ([runtimes page](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)): `python3.10` deprecates 2026-10-31; `dotnet8` and `dotnet9` 2026-11-10; `java11` stays supported until 2027-06-30 and `java11.al2023` until 2029; `nodejs26.x` and `python3.15` are preview. Full table in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk) | "Which runtime, and who maintains the allow-list as dates change?" |
| Function URL `NONE` | Public endpoint; the provider adds invoke permissions at create and does not remove them on destroy ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_url.html.markdown)); `AWS_IAM` is the alternative | "Is public access intended, and who cleans up the permissions?" |
| VPC attachment | Security Hub Lambda.3 (low severity) flags functions outside a VPC; VPC functions need ENI permissions, NAT for internet, and slower ENI cleanup ([source](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)). With a VPC, Lambda.5 (medium severity) expects at least 2 AZs ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html)) | "Does this function need VPC resources? If yes, which subnets in at least 2 AZs?" |
| Active tracing | `tracing_config { mode = "Active" }` satisfies Lambda.7 (low severity) ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html)); the IAM permissions the role needs for X-Ray are (unverified) | "Enable active tracing? Which X-Ray permissions does the role get?" |
| `source_account` for S3 invokers | Lambda.1 fails for S3-principal permissions without `AWS:SourceAccount` ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html)); the permission page lists S3 among the uses of `source_account`, but how it maps to that condition is (medium confidence) | "Which source account and bucket ARN?" |
| `arm64` vs `x86_64` | All supported runtimes support both; the function default is `x86_64` ([runtimes page](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), [function page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown)) | "Which architecture do the dependencies support?" |
| Provisioned or reserved concurrency | Provisioned concurrency with `skip_destroy = true` stays dangling and billable ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_provisioned_concurrency_config.html.markdown)); `reserved_concurrent_executions = 0` disables invocation ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown)) | "Is the cost of pre-warmed capacity acceptable?" |
| `vpc_config` with `capacity_provider_config` | The function page lists them as mutually exclusive, but the provider version that introduced `capacity_provider_config` is not pinned (medium confidence) | "Is Lambda Managed Instances in use, and does the provider version support it?" |
| SnapStart | `snap_start { apply_on = "PublishedVersions" }` exists; which runtimes and architectures support it is (unverified) | "Which runtime? Confirm SnapStart support on the AWS page first." |
| Log levels | `application_log_level` (TRACE..FATAL) and `system_log_level` (DEBUG, INFO, WARN) defaults are (unverified) | "Which levels should be set explicitly?" |
| Log group retention | Retention of a Lambda-created log group is (unverified); a Terraform-managed group sets `retention_in_days` | "What retention is required?" |
| `aws_lambda_resource_policy` | New in 6.65.0; its arguments and interaction with `aws_lambda_permission` are (unverified) | "Read the resource page before using it; is whole-policy management needed?" |
| `skip_destroy` on the function | The provider text refers to "Lambda Layer"; actual function semantics are (medium confidence) | "Is retaining the function on destroy required?" |
| Custom runtime `provided.al2023` | Supported by Lambda but absent from the Lambda.2 list; failing Lambda.2 is (medium confidence) | "Is Lambda.2 enforced on this account?" |
| Newer function blocks | `durable_config`, `tenancy_config`, `capacity_provider_config`, `publish_to` and `aws_lambda_function_scaling_config` exist on `main`; introducing versions and arguments were not pinned (medium confidence) | "Confirm the provider version supports the block before use." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Combine `filename`, `s3_bucket` and `image_uri` on one function — they conflict ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown)) | Use exactly one code source |
| Set `source_kms_key_arn` with `image_uri` — conflicts ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown)) | Drop `source_kms_key_arn`; use `kms_key_arn` for environment variables |
| Use `source_code_hash` to detect out-of-band source changes — the page says they will not be captured ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown)) | Read `code_sha256` |
| Attach more than 5 layers — the function accepts up to 5 layer version ARNs ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown)) | List at most 5 `aws_lambda_layer_version.arn` values |
| Set `starting_position` on an SQS mapping — must not be set ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown)) | Omit `starting_position` for SQS |
| Set `scaling_config.maximum_concurrency` below 2, e.g. `min(reserved, 1000)` — the page says it must be ≥ 2 ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown)) | Use a value of at least 2 (above 1000 needs a quota request) |
| Use `provisioned_poller_config` on SQS, Kinesis or DynamoDB — "Only valid for Amazon MSK or self-managed Apache Kafka sources." ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown)) | Use `scaling_config.maximum_concurrency` for SQS |
| Leave `destination_config` empty on an event invoke config — perpetual differences ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_event_invoke_config.html.markdown)) | Set `on_success` or `on_failure`, or remove the block |
| Set a function timeout above the SQS queue visibility timeout ([source](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)) | Keep the timeout at or below the visibility timeout |
| Delete the execution role before the VPC ENI is deleted — it prevents cleanup ([source](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)) | Keep the role and VPC policy attachment until the function is destroyed |
| Create an S3-principal permission without `source_account` — Lambda.1 fails without `AWS:SourceAccount` for S3 principals ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html)) | Set `source_arn` and `source_account` on `aws_lambda_permission` (medium confidence: how `source_account` maps to the Lambda.1 condition) ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_permission.html.markdown)) |
| Pin `version = "6.57.0"` — withdrawn ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch |

## Quick Reference

Sources read 2026-10-23 unless stated.

| Aspect | Value | Source |
|---|---|---|
| Function defaults | `package_type` `Zip`; `architectures` `["x86_64"]`; `memory_size` 128 (128–32768); `timeout` 3 (1–900); `reserved_concurrent_executions` -1; `publish` false | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown |
| Ephemeral storage | `ephemeral_storage { size }` 512–10240 MB | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown |
| Function timeouts | create, update, delete 10m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown |
| Tracing modes | `Active` or `PassThrough` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown |
| Event invoke | `maximum_retry_attempts` 0–2 (default 2); `maximum_event_age_in_seconds` 60–21600 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_event_invoke_config.html.markdown |
| Mapping defaults | `batch_size` 10 (SQS), 100 (Kinesis, DynamoDB, MQ, MSK); `enabled` true; timeouts 10m/10m/5m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown |
| Function URL | `invoke_mode` default `BUFFERED`; `cors.max_age` up to 86400; create timeout 10m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_url.html.markdown |
| Code signing | `policies.untrusted_artifact_on_deployment` `Warn` (default) or `Enforce`; up to 20 signing profile version ARNs | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_code_signing_config.html.markdown |
| Security Hub Lambda.1 | Function policies should prohibit public access (critical severity) | https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html |
| Security Hub Lambda.2 | Use supported runtimes (medium severity; `Image` ignored) | https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html |
| Security Hub Lambda.3 | Functions should be in a VPC (low severity) | https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html |
| Security Hub Lambda.5 | VPC functions in at least 2 AZs, `availabilityZones` default 2 (medium severity) | https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html |
| Security Hub Lambda.6 | Functions should be tagged, `requiredTagKeys` (low severity) | https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html |
| Security Hub Lambda.7 | X-Ray active tracing enabled (low severity); there is no Lambda.4 on the page | https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html |

## 5.x → 6.x Migration (Lambda)

- No Lambda items were found in the 6.0.0 upgrade guide: no removed or renamed `aws_lambda_*` arguments; only the general `region` addition applies
  (medium confidence, absence of evidence; [source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23).
- No BREAKING Lambda entries were found in CHANGELOG 6.48.0 → 6.70.0 (medium confidence, absence of evidence; part of the 6.55.0 CHANGELOG section was not read). Notable: 6.48.0 fixes alias plan drift and a
  provisioned concurrency update error; 6.54.0 adds `aws_lambda_function_scaling_config` and configurable
  timeouts for mappings and permissions; 6.64.0 adds a list resource for `aws_lambda_alias`; 6.65.0 adds
  `aws_lambda_resource_policy` ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md), 2026-10-23).
- Upgrade path (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown):
  "Before upgrading to version `6.0.0`, first upgrade to the latest available `5.x` version of the provider";
  the plan must complete "without errors or unexpected changes"; then update version constraints "to allow the `6.x` series"
  and run `terraform init -upgrade` "to download the new version". This skill uses `~> 6.69`.

## External Resources

All read 2026-10-23 unless stated.

- Provider docs (raw markdown): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown
- Provider CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Lambda runtimes: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
- Lambda execution role: https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html
- Lambda VPC access: https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html
- Lambda best practices: https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
- Security Hub Lambda controls: https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html
- Sibling skills: provisioning-aws-api-gateway-v6, provisioning-aws-eventbridge-v6, provisioning-aws-sqs-v6,
  provisioning-aws-sns-v6, provisioning-aws-iam-v6, provisioning-aws-kms-v6, provisioning-aws-cloudwatch-v6,
  provisioning-aws-vpc-v6, provisioning-aws-sam-v6
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
