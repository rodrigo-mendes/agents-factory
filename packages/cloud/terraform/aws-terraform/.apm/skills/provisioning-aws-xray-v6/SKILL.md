---
name: provisioning-aws-xray-v6
description: "X-Ray Terraform (aws 6.x): sampling rules, groups, encryption config. Use when writing HCL for X-Ray tracing. Not for CloudWatch logs/alarms, Lambda, API Gateway, Step Functions, KMS, IAM."
---

# Provisioning AWS X-Ray with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the **6.x major line** of hashicorp/aws (reference patch 6.69.0 / 6.70.0) +
> **Terraform ~> 1.16**. A new major is a new skill. Read date **2026-10-23**. Claims tagged
> (unverified) or (medium confidence) were not fully confirmed against an official page.

## Version Context

| Item | Value | Source (read 2026-10-23) |
|---|---|---|
| Terraform CLI | `~> 1.16`; newest 1.16.x is 1.16.7 (2026-10-23) | https://releases.hashicorp.com/terraform/ |
| Terraform 1.17.0 | Stable since 2026-10-21; not the target of this skill | https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (read 2026-10-22) |
| hashicorp/aws | Latest 6.70.0 (2026-10-23); this skill uses `~> 6.69`; no 7.x release | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | Withdrawn from GitHub and the Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Regional service | Each in-scope resource documents optional `region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_sampling_rule.html.markdown ; .../r/xray_group.html.markdown ; .../r/xray_encryption_config.html.markdown |
| X-Ray SDKs and Daemon | Maintenance mode since February 25th, 2026 (security fixes only) | https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable (2026-10-21); this skill stays on `~> 1.16`. Re-verify when starting new work.
- 6.57.0 is withdrawn; v7 is planned ("`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`" — https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), no 7.x release exists; v7 = a new skill.
- The X-Ray SDKs and Daemon are in maintenance mode; AWS recommends OpenTelemetry (see Ask First).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Always-do index: [always-do-patterns](./blueprints/always-do-patterns.md)
- Foundation: [terraform block, S3 backend, encryption config](./blueprints/always-do-foundation.md)
- Sampling rules and groups: [sampling rule, group](./blueprints/always-do-sampling-groups.md)
- Other services and IAM: [cross-references](./blueprints/always-do-cross-service.md)
- Never-do index: [never-do-patterns](./blueprints/never-do-patterns.md)
- Never-do provider/migration: [withdrawn version, deprecated backend](./blueprints/never-do-provider-migration.md)
- Never-do encryption: [removing the encryption config](./blueprints/never-do-encryption.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Root modules use `~>` for providers (`~> 6.69` here); reusable modules set only a minimum (`>=`).**
  https://developer.hashicorp.com/terraform/language/expressions/version-constraints —
  see [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Use `use_lockfile = true` on the S3 backend.**
  https://developer.hashicorp.com/terraform/language/backend/s3 —
  see [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Keep `rule_name` to 1–32 characters.**
  https://docs.aws.amazon.com/xray/latest/api/API_SamplingRule.html —
  see [sampling §3](./blueprints/always-do-sampling-groups.md#3-sampling-rule).
- **Set every Required argument of `aws_xray_sampling_rule`** (`priority`, `reservoir_size`, `fixed_rate`, `host`, `http_method`, `url_path`, `service_name`, `service_type`, `resource_arn`, `version`).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_sampling_rule.html.markdown —
  see [sampling §3](./blueprints/always-do-sampling-groups.md#3-sampling-rule).
- **Give custom sampling rules a `priority` in 1–9999.**
  https://docs.aws.amazon.com/xray/latest/api/API_SamplingRule.html —
  see [sampling §3](./blueprints/always-do-sampling-groups.md#3-sampling-rule).
- **Order rules by ascending priority; services use the first match.**
  https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html —
  see [sampling §3](./blueprints/always-do-sampling-groups.md#3-sampling-rule).
- **Express `fixed_rate` as a fraction between 0 and 1.**
  https://docs.aws.amazon.com/xray/latest/api/API_SamplingRule.html —
  see [sampling §3](./blueprints/always-do-sampling-groups.md#3-sampling-rule).
- **Put sampling rules on the root (first X-Ray-enabled) service; the sampling decision is made once.**
  https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html —
  see [sampling §3](./blueprints/always-do-sampling-groups.md#3-sampling-rule).
- **Keep `group_name` to 32 characters or fewer, alphanumeric and dashes.**
  https://docs.aws.amazon.com/xray/latest/devguide/xray-console-groups.html —
  see [sampling §4](./blueprints/always-do-sampling-groups.md#4-group).
- **Use `type = "NONE"` for default encryption and `type = "KMS"` with `key_id` for your own key.**
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown —
  see [foundation §2](./blueprints/always-do-foundation.md#2-encryption-config).
- **Keep a customer managed key enabled; if X-Ray loses access to the key it stops storing data.**
  https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html —
  see [foundation §2](./blueprints/always-do-foundation.md#2-encryption-config).
- **Configure tracing for Lambda, API Gateway and Step Functions in their sibling skills (provisioning-aws-lambda-v6, provisioning-aws-api-gateway-v6, provisioning-aws-step-functions-v6).**
  See [cross-service §5](./blueprints/always-do-cross-service.md#5-tracing-in-other-services-and-iam).
- **Use Terraform ≥ 1.12.0 for identity-based import.**
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown —
  see [sampling §4](./blueprints/always-do-sampling-groups.md#4-group).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Instrumentation: X-Ray SDK/Daemon vs OpenTelemetry (2026 change) | AWS: SDKs and Daemon in maintenance mode since February 25th, 2026, security fixes only, "will not receive new feature enhancements"; "X-Ray is transitioning to OpenTelemetry (OTel) as its primary instrumentation standard"; AWS recommends OpenTelemetry SDKs / ADOT for instrumentation and the OpenTelemetry Collector or CloudWatch agent for collection, for new and existing applications. ([migration](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html), [timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html)) | "Should this application stay on the X-Ray SDK/Daemon or move to OpenTelemetry/ADOT?" |
| Encryption option | Default encryption (free), AWS managed key `aws/xray` (pay for use; audit in CloudTrail), customer managed key (pay storage + use; you manage access and rotation); asymmetric KMS keys are not supported; existing data is not re-encrypted. ([source](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html)) | "Default encryption, `aws/xray`, or a customer managed key?" |
| KMS key-policy statements for X-Ray | Statements needed for `xray.amazonaws.com` on a customer managed key are (unverified). | "Which key-policy statements does your key need? Confirm against the AWS encryption page." |
| One encryption config per region | The resource `id` is the region name, so one config per account per region is (medium confidence). | "Is an `aws_xray_encryption_config` already managed for this region?" |
| Priority uniqueness | AWS documents the 1–9999 range and ascending evaluation; whether priorities must be unique, or what happens on ties, is (unverified). | "Use unique priorities as a defensive convention?" |
| Changing a rule's name or priority | The Step Functions guide says the name and priority of existing sampling rules cannot be changed (add or clone a rule instead); whether the provider forces replacement is (medium confidence). ([source](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html)) | "Accept a new rule replacing the old one?" |
| Managing the `Default` sampling rule | AWS: priority 10000, lowest priority, cannot be deleted; rate and reservoir size can change. Managing it with `aws_xray_sampling_rule` is (unverified). ([source](https://docs.aws.amazon.com/xray/latest/devguide/xray-api-configuration.html)) | "Change the default rate through Terraform, or leave the Default rule as is?" |
| Custom rule count | The AWS quota page lists 25 custom sampling rules per region (adjustable). ([source](https://docs.aws.amazon.com/general/latest/gr/xray.html)) | "How many custom rules are planned? Check the quota first." |
| Editing a group's filter expression | AWS: updating it does not change recorded data and can result in a merged graph; to avoid this, delete the group and create a new one. ([source](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-groups.html)) | "Edit the filter in place or recreate the group?" |
| Lambda tracing mode | `Active` sends traces only for sampled requests; sampling is 1 request/s + 5 % and not configurable; `PassThrough` forwards the header without sending traces. ([source](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)) | "Is `Active` right here, given the sampling rate cannot be set?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |
| Use `dynamodb_table` in the S3 backend — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Remove `aws_xray_encryption_config` from Terraform expecting to change X-Ray encryption — "Removing this resource from Terraform does not change the encryption configuration in X-Ray." ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown)) | Apply `type = "NONE"` (default encryption per the [provider page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown)) to return to default encryption per the AWS [encryption](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html) and [configuration](https://docs.aws.amazon.com/xray/latest/devguide/xray-api-configuration.html) pages |

## Quick Reference

Sources read 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Provider / CLI constraint | `~> 6.69` / `~> 1.16` (this skill's choice; `~>` semantics per the version-constraints page) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| S3 locking | `use_lockfile = true`; `dynamodb_table` deprecated | https://developer.hashicorp.com/terraform/language/backend/s3 |
| Sampling rule resource | `aws_xray_sampling_rule`; exports `arn`, `id` (= rule name), `tags_all` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_sampling_rule.html.markdown |
| Sampling rule `rule_name` | Optional in the provider (also the resource `id` and import ID); API length 1–32 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_sampling_rule.html.markdown ; https://docs.aws.amazon.com/xray/latest/api/API_SamplingRule.html |
| Default sampling rule | Priority 10000, reservoir 1, fixed rate 0.05 | https://docs.aws.amazon.com/xray/latest/devguide/xray-api-configuration.html |
| `attributes` | X-Ray SDK ignores rules that specify attributes; API Gateway matches original request headers | https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html |
| Group resource | `aws_xray_group`; imports by ARN | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_group.html.markdown |
| Encryption resource | `aws_xray_encryption_config`; `id` = region name | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown |
| API Gateway tracing | AWS: "X-Ray only supports tracing for REST APIs through API Gateway" | https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html |
| Security Hub related controls | APIGateway.3 and Lambda.7 (low severity); XRay.* controls absent from the reference (medium confidence, absence of evidence) | https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html |
| `AWSXRayDaemonWriteAccess` | `xray:PutTraceSegments`, `PutTelemetryRecords`, `GetSamplingRules`, `GetSamplingTargets`, `GetSamplingStatisticSummaries` | https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html |

## 5.x → 6.x Migration (X-Ray)

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown (read 2026-10-23).

- The 6.0 upgrade guide has no entries for X-Ray or any `aws_xray_*` resource (medium confidence, absence of evidence).
- The provider CHANGELOG 6.48.0 to 6.70.0 has no `aws_xray_*` entries (medium confidence, absence of evidence) — https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md.
- Upgrade path (guide wording): "Before upgrading to version `6.0.0`, first upgrade to the latest available `5.x` version of the provider."
  Confirm the plan completes "without errors or unexpected changes", then update version constraints "to allow the `6.x` series"
  (this skill uses `~> 6.69`) and run `terraform init -upgrade` "to download the new version".

Optional `region` on the three X-Ray resources is documented on their resource pages (see Version Context).

## External Resources

All read 2026-10-23.

- Sampling rule: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_sampling_rule.html.markdown
- Group: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_group.html.markdown
- Encryption config: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- X-Ray sampling: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html
- X-Ray encryption: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html
- SDK/Daemon migration to OpenTelemetry: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
