---
name: provisioning-aws-secrets-manager-v6
description: "Secrets Manager Terraform (aws 6.x): secrets, versions, write-only values, rotation, policies, replicas. Use when writing HCL for Secrets Manager. Not for Parameter Store, KMS, Lambda."
---

# Provisioning AWS Secrets Manager with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference 6.69.0/6.70.0) + **Terraform ~> 1.16** only.
> Research date **2026-10-23**. Claims tagged (unverified) or (medium confidence) were not fully confirmed
> against an official page. Regional service: resources accept an optional `region`.

## Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `~> 1.16` (1.16.6 current in the 1.16 line) | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | reference 6.69.0; latest 6.70.0 (2026-10-23); constraint `~> 6.69` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Write-only args (`secret_string_wo`) | Terraform ≥ 1.11 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown |
| Ephemeral resources | Terraform ≥ 1.10 | https://developer.hashicorp.com/terraform/language/manage-sensitive-data |
| Per-resource `region` | optional; change forces replacement | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |

**Version lock:** `-v6` = the 6.x major line, reference patch 6.69.0/6.70.0, Terraform `~> 1.16`.
A new major (v7) is a new skill.

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 became stable on 2026-10-21; it is not the target of this skill. Re-verify when starting new work.
- 6.57.0 is withdrawn from GitHub and the Registry; never pin it.
- v7 is planned (the 6.0 upgrade guide lists arguments "will be removed in v7.0.0", https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown) and would need a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Always-do secrets: [terraform block, secret, write-only version, ephemeral](./blueprints/always-do-secrets.md)
- Always-do rotation and policy: [rotation, resource policy](./blueprints/always-do-rotation-policy.md)
- Never-do secrets: [removed args, secrets in state, deprecated attributes](./blueprints/never-do-secrets.md)
- Never-do rotation and policy: [rotation args, policy conflicts](./blueprints/never-do-rotation-policy.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `required_version = "~> 1.16"` and `version = "~> 6.69"`** — root modules pin providers with `~>`.
  https://developer.hashicorp.com/terraform/language/expressions/version-constraints
  See [always-do-secrets §1](./blueprints/always-do-secrets.md#1-terraform-block).
- **Seed Terraform-managed values with `secret_string_wo` + `secret_string_wo_version`** — changing `secret_string_wo_version` triggers the update (Terraform ≥ 1.11).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown
  See [always-do-secrets §3](./blueprints/always-do-secrets.md#3-secret-version-with-a-write-only-value).
- **Feed write-only arguments from the ephemeral `aws_secretsmanager_secret_version`** — Terraform does not store ephemeral resources in state or plan files.
  https://developer.hashicorp.com/terraform/language/manage-sensitive-data
  See [always-do-secrets §4](./blueprints/always-do-secrets.md#4-ephemeral-and-data-source-reads).
- **Mark variables that hold secrets `sensitive = true`** — keeps them out of logs and console output.
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown
  See [always-do-secrets §3](./blueprints/always-do-secrets.md#3-secret-version-with-a-write-only-value).
- **Read the version ARN from `secret_arn`** — `arn` is deprecated on the version resource and data source.
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown
  See [always-do-secrets §4](./blueprints/always-do-secrets.md#4-ephemeral-and-data-source-reads).
- **Set `recovery_window_in_days` explicitly** — default is 30; `0` forces deletion without recovery, otherwise 7–30.
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown
  See [always-do-secrets §2](./blueprints/always-do-secrets.md#2-secret).
- **Use the key ARN in `kms_key_id` for a key in another account** — ARN or ID is accepted, ARN is required for cross-account keys.
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown
  See [always-do-secrets §2](./blueprints/always-do-secrets.md#2-secret).
- **Replicate with the `replica` block on `aws_secretsmanager_secret`** — `region` is required, `kms_key_id` is optional per replica.
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown
  See [always-do-secrets §2](./blueprints/always-do-secrets.md#2-secret).
- **Include `AWSCURRENT` in `version_stages` when you set it** — otherwise a perpetual diff when it is the only version or the label is already there.
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown
  See [always-do-secrets §3](./blueprints/always-do-secrets.md#3-secret-version-with-a-write-only-value).
- **Configure rotation with `aws_secretsmanager_secret_rotation`** — `rotation_lambda_arn` is required unless the secret is AWS-managed.
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown
  See [always-do-rotation-policy §5](./blueprints/always-do-rotation-policy.md#5-rotation).
- **Write rotation `duration` in hours, e.g. `"3h"`** — it is the rotation window length.
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown
  See [always-do-rotation-policy §5](./blueprints/always-do-rotation-policy.md#5-rotation).
- **Set `rotation_rules` with Security Hub SecretsManager.4 in mind** — it checks rotation within 90 days (default).
  https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html
  See [always-do-rotation-policy §5](./blueprints/always-do-rotation-policy.md#5-rotation).
- **Tag secrets with `tags` / `default_tags`** — Security Hub SecretsManager.5 checks required tag keys.
  https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html
  See [always-do-secrets §2](./blueprints/always-do-secrets.md#2-secret).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| KMS key | Default `aws/secretsmanager` key (created on first use) vs a customer managed key; use the key ARN for a key in another account. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown)) | "Default AWS-managed key or a customer managed key (same or other account)?" |
| Immediate deletion | `recovery_window_in_days = 0` forces deletion without recovery; otherwise 7–30 (default 30). `force_delete_without_recovery` is not an argument in the 6.x secret doc (medium confidence, absence of evidence). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown)) | "Is deletion without recovery acceptable for this secret?" |
| Rotation owns the value | `lifecycle { ignore_changes = [secret_string] }` is a Terraform meta-argument pattern, not in the provider docs (medium confidence); the version resource tracks only its own version. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown)) | "Should rotation own the value (ignore_changes) or should Terraform keep pushing it?" |
| Rotate on apply | `rotate_immediately` defaults to `true`; enabling rotation rotates the secret once immediately. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown)) | "Rotate immediately on apply, or wait for the next window?" |
| Replication | `replica` block per Region; `force_overwrite_replica_secret` overwrites a same-named secret in the destination Region (default not stated, unverified). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown)) | "Which Regions, which KMS key per replica, and may an existing secret be overwritten?" |
| Policy location | Set `block_public_policy = true` explicitly on `aws_secretsmanager_secret_policy` (default not stated, unverified). Manage the policy in one place, inline `policy` or the policy resource, not both (medium confidence, inferred from the `policy` warning). How to remove a policy managed by the policy resource is not stated (unverified); it rejects `"{}"`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_policy.html.markdown)) | "Inline policy or the policy resource, and should public-policy blocking be on?" |
| Rotation arguments | The 6.x secret doc lists no rotation arguments; use `aws_secretsmanager_secret_rotation` (medium confidence, absence of evidence). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown)) | "Is any legacy inline rotation argument being carried over?" |
| Replica resource | No resource page for `aws_secretsmanager_secret_replica` was found in the provider docs; use the `replica` block of `aws_secretsmanager_secret` (medium confidence, absence of evidence). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown)) | "Is a separate replica resource expected?" |
| Ephemeral resource | The ephemeral `aws_secretsmanager_secret_version` page notes ephemeral resources "may evolve". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/secretsmanager_secret_version.html.markdown)) | "Accept a feature the docs say may evolve to keep secrets out of state?" |
| Managed external secrets | `type` (`SalesforceClientSecret`, `BigIDClientSecret`, `SnowflakeKeyPairAuthentication`) cannot be changed after creation. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown)) | "Which external secret type, and is it final?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| ISO-8601 rotation `duration` such as `"P7D"`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown)) | Hours such as `"3h"` |
| Put secret values in `secret_string` and call state safe — Terraform stores secrets from configuration in state and plan files, `sensitive` included. ([source](https://developer.hashicorp.com/terraform/language/manage-sensitive-data)) | `secret_string_wo` + `secret_string_wo_version` (Terraform ≥ 1.11) |
| Use the deprecated `arn` on `aws_secretsmanager_secret_version` (resource or data source). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown)) | `secret_arn` |
| Set both a plain and a write-only value — exactly one value source is allowed. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown)) | One of `secret_string`, `secret_binary` (base64) or `secret_string_wo` |
| Set `policy = null` or `""` on the secret to remove its policy (it does not delete it), or `"{}"` on `aws_secretsmanager_secret_policy` (rejected). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown)) | `policy = "{}"` on the secret (the policy resource rejects `"{}"`) |
| Keep `rotation_rules` when `rotation_enabled = false`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown)) | Omit `rotation_rules` (use a `dynamic` block to toggle) |
| Change `type` on an existing secret — cannot be changed after creation. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown)) | Create a new secret with the desired `type` |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |

## Quick Reference

Sources fetched 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Secret name | letters, digits, `/_+=.@-`; conflicts with `name_prefix` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown |
| Secret `recovery_window_in_days` | default 30; `0` = no recovery; else 7–30 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown |
| Secret `kms_key_id` default | account's `aws/secretsmanager` key | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown |
| Secret exports | `arn`, `id` (= ARN), `replica`, `tags_all` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown |
| Version value sources | `secret_string`, `secret_binary` (base64), `secret_string_wo` + `secret_string_wo_version` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown |
| Version exports | `secret_arn`, `version_id`, `has_secret_string_wo`; `arn` deprecated | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown |
| Rotation `rotate_immediately` | default `true` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown |
| Rotation `rotation_rules` | `automatically_after_days` or `schedule_expression` (`cron()`/`rate()`); `duration` in hours | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown |
| `rotation_enabled` | configurable since 6.62.0; omit `rotation_rules` when `false` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Policy resource | `secret_arn` + `policy` (JSON, `"{}"` rejected); `block_public_policy` optional | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_policy.html.markdown |
| Data source version | `version_stage` default `AWSCURRENT`; returns decrypted value | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/secretsmanager_secret_version.html.markdown |
| Security Hub controls | SecretsManager.1 to .5 (rotation, rotation success, unused, rotated within N days, tagged) | https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html |

## 5.x → 6.x Migration (Secrets Manager)

- The 6.0.0 upgrade guide has no Secrets Manager entries (no removed or renamed arguments). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown (2026-10-23)

Changes below come from https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md (2026-10-23):

- 6.47.0 deprecated `arn` in favor of `secret_arn` on the version resource and data sources, and `name` in favor of `secret_name` on `aws_secretsmanager_secret_versions`.
- 6.45.0 allowed switching `secret_string` to `secret_string_wo` without recreation; 6.50.0 fixed unnecessary replacement when switching between them.
- 6.56.0 added the list resource `aws_secretsmanager_secret_policy`; 6.57.1 added `type` and external-rotation arguments; 6.62.0 made `rotation_enabled` configurable.
- 6.70.0: reading or deleting a secret version whose non-current KMS key is disabled or deleted no longer errors (value kept from state, with a warning).

## External Resources

All fetched 2026-10-23.

- Secret: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown
- Secret version: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown
- Secret rotation: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown
- Secret policy: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_policy.html.markdown
- Terraform — manage sensitive data: https://developer.hashicorp.com/terraform/language/manage-sensitive-data
- AWS Secrets Manager best practices: https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html
- Security Hub Secrets Manager controls: https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
