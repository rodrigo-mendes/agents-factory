---
name: provisioning-aws-parameter-store-v6
description: "Parameter Store Terraform (aws 6.x): aws_ssm_parameter, SecureString write-only values, reads, hierarchies, tiers. Use when writing HCL for Parameter Store. Not for Secrets Manager, KMS, IAM."
---

# Provisioning AWS Parameter Store with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference 6.69.0 / 6.70.0) + **Terraform ~> 1.16** only.
> Research date **2026-10-23**. Claims tagged (unverified) or (medium confidence) were not fully confirmed
> against an official page. Sibling skills: Secrets Manager (`provisioning-aws-secrets-manager-v6`),
> KMS (`provisioning-aws-kms-v6`), IAM (`provisioning-aws-iam-v6`).

## Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"`; 1.17.0 is stable (2026-10-23) but not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0; constraint `~> 6.69`; no 7.x released | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Write-only `value_wo` | Terraform CLI >= 1.11.0 (satisfied by `~> 1.16`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown |
| Identity-based import | Terraform >= 1.12.0 (satisfied by `~> 1.16`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown |
| 6.58.0 / 6.59.0 fixes | `aws_ssm_parameter`: ARN import, importing a specific version, leading-slash names | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`), reference patch 6.69.0/6.70.0,
Terraform ~> 1.16. A new major (v7) is a new skill.

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable since 2026-10-21 and is not the target of this skill; re-verify before moving to it.
- 6.57.0 is withdrawn; v7 is planned and would be a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Always-do foundation: [terraform block, hierarchy names, import](./blueprints/always-do-foundation.md)
- Always-do secrets: [SecureString write-only with a CMK](./blueprints/always-do-secrets.md)
- Ask-first ephemeral: [ephemeral read by arn](./blueprints/ask-first-ephemeral.md)
- Never-do secrets: [insecure_value, value, data sources, ephemeral name](./blueprints/never-do-secrets.md)
- Never-do names/version: [leading slash, withdrawn 6.57.0](./blueprints/never-do-names-version.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` for the provider** — it includes the 6.58.0/6.59.0 `aws_ssm_parameter` fixes (needs provider >= 6.59.0). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-version-constraints).
- **Write SecureString values with `value_wo` + `value_wo_version`** — the value is never stored in state (Terraform >= 1.11). Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown.
  See [secrets §4](./blueprints/always-do-secrets.md#4-securestring-with-value_wo-and-a-cmk).
- **Bump `value_wo_version` to push a new write-only value** — changing it is the only way. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown.
  See [secrets §4](./blueprints/always-do-secrets.md#4-securestring-with-value_wo-and-a-cmk).
- **Use `insecure_value` for non-secret `String`/`StringList`** — it is never marked sensitive, so diffs stay readable. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown.
  See [foundation §2](./blueprints/always-do-foundation.md#2-hierarchical-names-and-non-secret-values).
- **Start path names with `/`.** Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown.
  See [foundation §2](./blueprints/always-do-foundation.md#2-hierarchical-names-and-non-secret-values).
- **Keep hierarchies to 15 levels or fewer.** Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html.
  See [foundation §2](./blueprints/always-do-foundation.md#2-hierarchical-names-and-non-secret-values).
- **Import with the `identity` block** — it requires Terraform >= 1.12.0. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown.
  See [foundation §3](./blueprints/always-do-foundation.md#3-import).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Tier | `Standard`: 10,000 parameters, 4 KB values, free; `Advanced`: 100,000 parameters, 8 KB, parameter policies, cross-account sharing, charged; the default tier is set per account/Region and changing it does not affect existing parameters ([AWS](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html)). `tier` defaults to that default tier, and in Terraform `Advanced` → `Standard` recreates the resource ([TF](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown)). | "Is Advanced needed (size, count, policies, sharing)? Accept that it is charged and that a downgrade recreates the resource?" |
| `Intelligent-Tiering` | A default-tier setting, not a third tier: it creates Standard unless the request needs Advanced, then upgrades automatically and one-way. ([AWS](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-default-tier.html)) | "May parameters silently become billable Advanced?" |
| Secrets vs config | AWS recommends Secrets Manager for credentials, API keys, tokens (automatic rotation, cross-region replication); in its comparison table Parameter Store rotation is None. ([AWS](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)) | "Is this a rotating secret (use `provisioning-aws-secrets-manager-v6`) or static config?" |
| Key for SecureString | Without `key_id` AWS uses `aws/ssm`, whose access cannot be controlled by policy; a customer managed key is needed for key-policy control, and only symmetric keys are supported ([AWS](https://docs.aws.amazon.com/systems-manager/latest/userguide/secure-string-parameter-kms-encryption.html)). | "Is key-policy control (cross-account readers, separation of duties) needed? If so use `provisioning-aws-kms-v6`." |
| `overwrite` | Default `false` on create, `true` afterward; lets Terraform overwrite an existing parameter, including one created outside Terraform; the current provider page shows no deprecation marker on it. The page points to lifecycle rules (e.g. `ignore_changes`) for other update behavior. ([TF](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown)) | "Adopt an existing parameter by overwrite, or import it?" |
| Ephemeral read | Ephemeral `aws_ssm_parameter` reads by `arn` ([TF](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/ssm_parameter.html.markdown)); the page calls ephemeral resources a new feature whose usage may change and states no minimum CLI version (unverified). Ephemeral values staying out of state and plan is general Terraform behavior (medium confidence). See [ephemeral read](./blueprints/ask-first-ephemeral.md). | "Is the ephemeral read acceptable given the unstated minimum version?" |
| Many parameters | PutParameter default is 3 TPS (10 with higher throughput); throttling in large `for_each` is inferred (medium confidence). ([AWS](https://docs.aws.amazon.com/general/latest/gr/ssm.html)) | "Will many parameters be created or read at once, given the PutParameter quota?" |
| Names and path IAM | Name length, allowed characters and reserved prefixes (unverified); whether `GetParametersByPath` needs the bare path ARN besides `path/*` (unverified). | "Confirm naming limits and IAM path scoping against the AWS pages." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `insecure_value` on a `SecureString` — it cannot be used with that type. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown)) | Use `value_wo` + `value_wo_version` for SecureString; keep `insecure_value` for non-secret types |
| Write a `SecureString` with `value` expecting no plaintext in state — the page says it is stored in state as plain text. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown)) | `value_wo` + `value_wo_version` (Terraform >= 1.11) |
| Read a `SecureString` with the `aws_ssm_parameter` data source expecting a clean state — the decrypted value is stored in the raw state as plain text. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameter.html.markdown)) | Treat the data source value as stored in state; there is no documented way to hide it |
| Read a `SecureString` with the `aws_ssm_parameters_by_path` data source and `with_decryption = true` expecting a clean state — decrypted values are stored in state as plain text. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameters_by_path.html.markdown)) | Treat decrypted values from this data source as stored in state; there is no documented way to hide them |
| Set `name` on the ephemeral `aws_ssm_parameter` — it requires `arn`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/ssm_parameter.html.markdown)) | `arn = aws_ssm_parameter.x.arn` |
| Name a parameter with a path without a leading `/`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown)) | `name = "/myapp/prod/db/host"` # example |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |

## Quick Reference

Sources fetched 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Value arguments | Exactly one of `value`, `value_wo`, `insecure_value`; `value` is always sensitive | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown |
| `type` | `String`, `StringList`, `SecureString` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown |
| `data_type` | `text`, `aws:ssm:integration`, `aws:ec2:image` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown |
| Attributes | `arn`, `version`, `has_value_wo`, `tags_all` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown |
| `region` | Optional on resource, data sources and ephemeral resource | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown |
| Data source | `name` (`name:version` selects a version), `with_decryption` default `true`; every type returns a string (`split()` for `StringList`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameter.html.markdown |
| By-path data source | `path` starts with `/`, max 15 levels; `recursive` default `false`; a full parameter name as `path` returns nothing unless used as a hierarchy prefix | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameters_by_path.html.markdown |
| Versions retained | 100 per parameter | https://docs.aws.amazon.com/general/latest/gr/ssm.html |
| Tier limits | Standard 10,000 params / 4 KB; Advanced 100,000 / 8 KB | https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html |
| KMS permissions | Standard: `kms:Encrypt`; Advanced: `kms:GenerateDataKey`; decrypt: `kms:Decrypt` | https://docs.aws.amazon.com/systems-manager/latest/userguide/secure-string-parameter-kms-encryption.html |
| Encryption context | `PARAMETER_ARN`; usable in `kms:EncryptionContext:PARAMETER_ARN` conditions | https://docs.aws.amazon.com/systems-manager/latest/userguide/secure-string-parameter-kms-encryption.html |
| Parameter ARN | `arn:aws:ssm:<region>:<account>:parameter/FinancialParameters/*` shape, no extra `/` after `parameter` for hierarchical names | https://docs.aws.amazon.com/systems-manager/latest/userguide/secure-string-parameter-kms-encryption.html |
| Hierarchy | `/` separator, max 15 levels; `/parameter-name` and `parameter-name` are both root parameters | https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html |
| Security Hub SSM.1–SSM.7 | None of the seven controls evaluates Parameter Store parameters (as of 2026-10-23) | https://docs.aws.amazon.com/securityhub/latest/userguide/ssm-controls.html |

## 5.x → 6.x Migration (Parameter Store)

The 6.0.0 upgrade guide has **no entries** for `aws_ssm_parameter`, `data.aws_ssm_parameter`,
`data.aws_ssm_parameters_by_path` or patch baselines
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23).

- Adjacent, out of scope: `aws_ssm_association` — remove `instance_id`, use `targets`.
- CHANGELOG 6.58.0: correct import when given an ARN; no errors when importing a specific version. 6.59.0: names with a leading slash and no other slashes no longer lose the slash; new list resource `aws_ssm_patch_baseline`
  ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)).
- The 6.48.0–6.55.0 range was read only partly (see Coverage Limits in [unverified-and-risks](./blueprints/unverified-and-risks.md#coverage-limits)).

## External Resources

All fetched 2026-10-23.

- Resource: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown
- Data source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameter.html.markdown
- Ephemeral resource: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/ssm_parameter.html.markdown
- By-path data source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameters_by_path.html.markdown
- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- AWS Parameter Store overview: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html
- AWS SecureString and KMS: https://docs.aws.amazon.com/systems-manager/latest/userguide/secure-string-parameter-kms-encryption.html
- Security Hub SSM controls: https://docs.aws.amazon.com/securityhub/latest/userguide/ssm-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
