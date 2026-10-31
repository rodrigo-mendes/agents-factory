---
name: provisioning-aws-shield-v6
description: "Shield Advanced Terraform (aws 6.x, global): subscription, protections, groups, health checks, SRT access. Use when writing aws_shield_* HCL. Not for WAF rules, CloudFront or Route 53 resources."
---

# Provisioning AWS Shield with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference 6.70.0) + **Terraform ~> 1.16** only.
> Research date **2026-10-23**. Claims tagged (unverified) or (medium confidence) were not fully confirmed
> against an official page. Shield Standard needs no Terraform resource; this skill covers Shield Advanced.

## Version Context

| Item | Value | Source (fetched 2026-10-23) |
|---|---|---|
| Terraform CLI | `~> 1.16` (1.16.6); 1.17.0 is stable but not targeted | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | **6.70.0** latest; constraint `~> 6.69` | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region model | Shield Advanced is **global**: no `region` argument on `aws_shield_*` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Provider constraint | `~> 6.69` (root modules); `>= 6.0` (reusable modules) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 became stable on 2026-10-21; this skill still targets `~> 1.16`. Re-verify before moving.
- 6.57.0 is permanently withdrawn; any constraint resolving to it fails init.
- v7 is planned; it is a new skill (`provisioning-aws-shield-v7`).

**Version lock:** `-v6` = 6.x major line, reference patch 6.70.0 (6.69.0 at first research), Terraform ~> 1.16.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Always-do hub: [always-do-patterns](./blueprints/always-do-patterns.md)
- Subscription, protections, groups: [always-do-subscription-protection](./blueprints/always-do-subscription-protection.md)
- Health checks, SRT access, proactive engagement: [always-do-detection-response](./blueprints/always-do-detection-response.md)
- Never-do hub: [never-do-patterns](./blueprints/never-do-patterns.md)
- Never-do Shield: [never-do-shield](./blueprints/never-do-shield.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Set `required_version = "~> 1.16"` and `version = "~> 6.69"`** in the root `terraform {}` block.
  See [subscription §1](./blueprints/always-do-subscription-protection.md#1-terraform-block-and-subscription).
  https://developer.hashicorp.com/terraform/language/expressions/version-constraints
- **Omit `region` on every `aws_shield_*` resource** — the guide lists Shield Advanced under global services.
  See [subscription §1](./blueprints/always-do-subscription-protection.md#1-terraform-block-and-subscription).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- **Create one `aws_shield_protection` per resource you want protected** — Shield Advanced does not automatically protect resources.
  See [subscription §2](./blueprints/always-do-subscription-protection.md#2-protections).
  https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html
- **Protect a Network Load Balancer through its Elastic IP allocation ARN** — NLBs are supported only through associations to Elastic IP addresses.
  See [subscription §2](./blueprints/always-do-subscription-protection.md#2-protections).
  https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html
- **Subscribe each account you want to protect with `aws_shield_subscription`** — Shield Advanced subscription is per account.
  See [subscription §1](./blueprints/always-do-subscription-protection.md#1-terraform-block-and-subscription).
  https://docs.aws.amazon.com/waf/latest/developerguide/enable-ddos-prem.html
- **Set `members` only with `pattern = "ARBITRARY"` and `resource_type` only with `pattern = "BY_RESOURCE_TYPE"`** in protection groups.
  See [subscription §3](./blueprints/always-do-subscription-protection.md#3-protection-groups).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_group.html.markdown
- **Add `aws_shield_protection_health_check_association` where you need health-based detection or proactive engagement** — hosted zones cannot use it, proactive engagement requires health checks, otherwise it is optional.
  See [detection §4](./blueprints/always-do-detection-response.md#4-health-check-association).
  https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html
- **Attach `AWSShieldDRTAccessPolicy` to the role passed to `aws_shield_drt_access_role_arn_association`** before applying.
  See [detection §5](./blueprints/always-do-detection-response.md#5-srt-access).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_role_arn_association.html.markdown
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated.
  See [subscription §1](./blueprints/always-do-subscription-protection.md#1-terraform-block-and-subscription).
  https://developer.hashicorp.com/terraform/language/backend/s3

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Subscribing | The provider page warns a subscription requires a 1 year commitment with a monthly fee; the amount was not verified on a fetched official page (unverified). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_subscription.html.markdown)) | "Is a 1-year Shield Advanced commitment approved for this account?" |
| Subscription destroy protection | Destroy sets `auto_renew = DISABLED`, which AWS allows only in the last 30 days; `skip_destroy = true` plus `prevent_destroy = true` is an inference (medium confidence). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_subscription.html.markdown)) | "Should the production subscription get `skip_destroy` and `prevent_destroy`?" |
| `aws_shield_application_layer_automatic_response` | Legacy: from 2026-03-26 the Anti-DDoS Managed Rule Group in AWS WAF is the default and supersedes L7 auto mitigation; adds a 150-WCU rule group and needs a WAFv2 web ACL on the resource. ([source](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html)) | "Use the Anti-DDoS managed rule group in `aws_wafv2_web_acl` (see provisioning-aws-waf-v6) instead?" |
| `aws_shield_proactive_engagement` | Contacts defined here replace any contacts already configured in AWS; at least one contact needs a phone number; requires health checks. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_proactive_engagement.html.markdown)) | "Should Terraform own the emergency contacts, replacing existing ones?" |
| Health check choice | AWS says the health check must report healthy when associated, be relevant to the resource, and not be deleted while used (page is an unversioned "latest" page, medium confidence). ([source](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html)) | "Which healthy Route 53 health check is relevant to this resource?" |
| Protection groups and L7 mitigation | AWS says automatic L7 mitigation does not interact with protection groups, so mitigations apply per resource (unversioned "latest" page, medium confidence). ([source](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html)) | "Is per-resource mitigation planning acceptable instead of relying on groups?" |
| Firewall Manager vs per-resource protections | Firewall Manager can automate subscriptions and protections across an organization but supports all protected types except Route 53 and Global Accelerator. ([source](https://docs.aws.amazon.com/waf/latest/developerguide/enable-ddos-prem.html)) | "Manage protections per resource in Terraform or via a Firewall Manager policy?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Add `region` to an `aws_shield_*` resource — no resource page documents it and the guide lists Shield Advanced as global. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Omit `region` |
| Put an NLB ARN in `aws_shield_protection.resource_arn`. ([source](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html)) | Use the EIP allocation ARN `arn:${partition}:ec2:${region}:${account}:eip-allocation/${id}` |
| Associate a health check with a Route 53 hosted-zone protection — health-based detection works with any type except hosted zones. ([source](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html)) | Omit the association for hosted-zone protections |
| Set `members` without `pattern = "ARBITRARY"`, or `resource_type` without `pattern = "BY_RESOURCE_TYPE"`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_group.html.markdown)) | Match the argument to the pattern |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |
| Pin `version = "6.57.0"` — withdrawn. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |

## Quick Reference

Sources fetched 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| Region | none on `aws_shield_*` (global) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| `aws_shield_subscription` | `auto_renew` `ENABLED` (default) or `DISABLED`; `skip_destroy`; import by account ID | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_subscription.html.markdown |
| `aws_shield_protection` | required `name`, `resource_arn`; supports CloudFront, ELB, Global Accelerator, Elastic IP, Route 53 hosted zones; NLB only via its EIP allocation ARN | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection.html.markdown |
| `aws_shield_protection_group` | required `protection_group_id`, `aggregation`, `pattern`; enums from examples only (medium confidence) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_group.html.markdown |
| Health check association | `health_check_arn` + `shield_protection_id`; import `<protection_id>+<health_check_arn>` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_health_check_association.html.markdown |
| SRT role | `role_arn`; managed policy `AWSShieldDRTAccessPolicy` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_role_arn_association.html.markdown |
| SRT log bucket | `log_bucket` + `role_arn_association_id`; import by bucket name | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_log_bucket_association.html.markdown |
| Automatic response | `resource_arn` (CloudFront, ALB), `action` `COUNT` or `BLOCK`; legacy | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_application_layer_automatic_response.html.markdown |
| Security Hub | no Shield control found in the controls reference (medium confidence) | https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html |
| S3 locking | `use_lockfile = true` | https://developer.hashicorp.com/terraform/language/backend/s3 |

## 5.x → 6.x Migration (Shield)

Per the 6.0.0 upgrade guide
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23):

- No mention of Shield; no `aws_shield_*` breaking change is documented.
- The CHANGELOG from 6.40.0 to 6.70.0 has no entry for `aws_shield_*`
  ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)).
- Do not add `region` during the upgrade: Shield Advanced stays global.

Upgrade path (per https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown): move to latest 5.x, get a clean plan, set `~> 6.0`, run `terraform init -upgrade`.

## External Resources

All fetched 2026-10-23.

- Enhanced region support guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Shield Advanced protected resources: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html
- Shield Advanced health checks: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html
- Shield Advanced subscription: https://docs.aws.amazon.com/waf/latest/developerguide/enable-ddos-prem.html
- Automatic application layer response: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
