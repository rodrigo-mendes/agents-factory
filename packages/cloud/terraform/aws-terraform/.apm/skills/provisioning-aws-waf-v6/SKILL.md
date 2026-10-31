---
name: provisioning-aws-waf-v6
description: "WAFv2 Terraform (aws 6.x): web ACLs, rule groups, IP sets, associations, logging. Use when writing HCL for WAF. Not for Shield, CloudFront distributions, API Gateway."
---

# Provisioning AWS WAF (WAFv2) with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the **6.x major line** of hashicorp/aws, reference patch 6.69.0/6.70.0, with
> **Terraform ~> 1.16**. A new major (v7) is a new skill. Research date **2026-10-22**. Scope: WAFv2
> (`aws_wafv2_*`) only; WAF Classic is out of scope. Claims tagged (unverified) or (medium confidence)
> were not fully confirmed against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-22) |
|---|---|---|
| Terraform CLI | `~> 1.16` (1.16.6); 1.17.0 is stable but not the target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0 (2026-10-23); reference 6.69.0; constraint `~> 6.69` | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | Withdrawn from GitHub and the Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region model | `aws_wafv2_*` documents optional `region` (WAFv2 is regional, not global) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown |
| Identity import | `identity` block needs Terraform >= 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_ip_set.html.markdown |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 became stable on 2026-10-21; it is not the target of this skill. Re-verify before new work.
- 6.57.0 is withdrawn; a constraint resolving to it must not be used.
- v7 is planned; when it ships, create `provisioning-aws-waf-v7`.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation: [terraform block, regional web ACL, CLOUDFRONT scope](./blueprints/always-do-foundation.md)
- Resources: [IP set, rule group, rate-based rule](./blueprints/always-do-resources.md)
- Attach and log: [separate rules, association, logging](./blueprints/always-do-attach-logging.md)
- Never-do web ACL: [inline rules, rule actions, JSON rules](./blueprints/never-do-web-acl.md)
- Never-do attachment and scope: [rule resource args, CloudFront, HTTP API, region](./blueprints/never-do-attachment-scope.md)
- Never-do limits and provider: [WCU, rate limit, backend, withdrawn version](./blueprints/never-do-limits-provider.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` (root) and `required_version = "~> 1.16"`; use `use_lockfile = true` on the S3 backend** —
  `dynamodb_table` is deprecated. See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-providers).
- **Set `scope`, `default_action` and `visibility_config` on every web ACL** — all three are required; `scope` forces a new resource.
  See [foundation §2](./blueprints/always-do-foundation.md#2-regional-web-acl).
- **Roll out new rules and managed groups in count mode first** — `override_action { count {} }` for a whole group,
  then switch to `none {}` after tuning. See [foundation §2](./blueprints/always-do-foundation.md#2-regional-web-acl).
- **For `scope = "CLOUDFRONT"` target us-east-1 and attach through `aws_cloudfront_distribution.web_acl_id`** with the ACL ARN.
  See [foundation §3](./blueprints/always-do-foundation.md#3-cloudfront-scope).
- **Size `capacity` of a rule group with headroom up front** — it forces a new resource; hard max is 5,000 WCU (AWS quota page, not the provider page).
  See [resources §4](./blueprints/always-do-resources.md#4-ip-set-and-rule-group).
- **Set `limit` of a rate-based rule at 10 or more** — 10 is the AWS minimum.
  See [resources §5](./blueprints/always-do-resources.md#5-rate-based-rule).
- **Add `lifecycle { ignore_changes = [rule] }` to a web ACL that is used with `aws_wafv2_web_acl_rule` or
  `aws_wafv2_web_acl_rule_group_association`.** See [attach §6](./blueprints/always-do-attach-logging.md#6-separate-rules-on-a-web-acl).
- **Use `web_acl_arn` on `aws_wafv2_web_acl_rule`.** See [attach §6](./blueprints/always-do-attach-logging.md#6-separate-rules-on-a-web-acl).
- **Associate regional resources with `aws_wafv2_web_acl_association`** (ALB, REST API stage, Cognito, AppSync, App Runner, Verified Access).
  See [attach §7](./blueprints/always-do-attach-logging.md#7-web-acl-association).
- **Name the log destination with the `aws-waf-logs-` prefix.**
  See [attach §8](./blueprints/always-do-attach-logging.md#8-logging-configuration).
- **Set `visibility_config.cloudwatch_metrics_enabled = true` on every rule and rule group.**
  See [foundation §2](./blueprints/always-do-foundation.md#2-regional-web-acl).

For the CloudFront distribution itself use provisioning-aws-cloudfront-v6; for the REST API stage use provisioning-aws-api-gateway-v6.

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| CLOUDFRONT scope region | Provider alias on us-east-1 (docs: "on the AWS provider") vs per-resource `region = "us-east-1"` (inferred from the `region` model, (medium confidence)). | "Use a us-east-1 provider alias (documented) or `region = \"us-east-1\"` on each WAF resource?" |
| Inline `rule` vs separate rule resources | Inline `rule` blocks have deletion-ordering errors, spurious diffs and coupled updates; separate resources need `ignore_changes = [rule]` on the web ACL. | "Manage rules inline or with `aws_wafv2_web_acl_rule` / rule group associations?" |
| Rule group `capacity` | Forces new resource; more than 1,500 WCU in a web ACL costs extra; hard max 5,000. | "What WCU headroom should the rule group reserve?" |
| Log destination | Firehose, CloudWatch log group or S3 bucket ARN; `redacted_fields` and `logging_filter` available; WAFv2 may create a generic `AWSWAF-LOGS` resource policy. | "Which destination, which fields to redact, and who manages the log resource policy?" |
| Amplify association | The API says use `CLOUDFRONT` for Amplify; the Terraform association page lists Amplify without that note (unverified). | "Is the target an Amplify application? Confirm the scope before writing the association." |
| Bot Control ML | `enable_machine_learning` now defaults to `false` in 6.x. | "Should Bot Control keep machine learning enabled (`true`)?" |
| Shield-added rules | `ShieldMitigationRuleGroup_<account-id>_<web-acl-guid>_*` rules are added by AWS; managing them may cause permission errors. | "Is Shield Advanced automatic mitigation in use on this web ACL?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use inline `rule` blocks together with `aws_wafv2_web_acl_rule` or rule group associations without `ignore_changes`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown)) | Add `lifecycle { ignore_changes = [rule] }` to the web ACL, or keep all rules inline |
| Put `web_acl_id` and `scope` on `aws_wafv2_web_acl_rule`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_rule.html.markdown)) | `web_acl_arn`; `scope` is not an argument |
| Attach a web ACL to a CloudFront distribution with `aws_wafv2_web_acl_association`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_association.html.markdown)) | `aws_cloudfront_distribution.web_acl_id = aws_wafv2_web_acl.x.arn` |
| Associate a web ACL with an HTTP API (`aws_apigatewayv2_stage`) — "REST only; HTTP is unsupported". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_association.html.markdown)) | Associate REST API stages only |
| Create `scope = "CLOUDFRONT"` resources without targeting us-east-1. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown)) | Target us-east-1 (provider alias; per-resource `region` is the Ask First option) |
| Treat 1,500 WCU as the maximum. ([source](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html)) | Hard max is 5,000 per web ACL and per rule group; above 1,500 in a web ACL is only a pricing threshold |
| Validate rate `limit >= 100`. ([source](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html)) | AWS minimum is 10 |
| Set `action` on a rule that references a rule group. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown)) | `override_action` (`count` or `none`) |
| Combine `rule_json` with `rule` and expect drift detection — "There is no drift detection at this time". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown)) | One of them only; on rule groups the argument is `rules_json` |
| S3 backend with `dynamodb_table` ([source](https://developer.hashicorp.com/terraform/language/backend/s3)); pin `version = "6.57.0"` ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)). | `use_lockfile = true`; `~> 6.69` |

## Quick Reference

Sources fetched 2026-10-22.

| Aspect | Value | Source |
|---|---|---|
| Provider / CLI constraint | `~> 6.69` / `~> 1.16` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| S3 locking | `use_lockfile = true` | https://developer.hashicorp.com/terraform/language/backend/s3 |
| Web ACL required | `default_action`, `scope` (forces new), `visibility_config` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown |
| Statement nesting | 3 levels supported; use `rule_json` for deeper | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown |
| Rule resource | `web_acl_arn` required; parent needs `ignore_changes = [rule]` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_rule.html.markdown |
| Rule group | `capacity` and `scope` force new; JSON arg is `rules_json` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_rule_group.html.markdown |
| Rate-based | window 60/120/300/600 s (default 300); key default `IP` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown |
| Rate-based limit | minimum `limit` 10 (AWS quota; not stated on the provider page) | https://docs.aws.amazon.com/waf/latest/developerguide/limits.html |
| WCU | hard max 5,000 per web ACL and rule group; above 1,500 in a web ACL costs extra | https://docs.aws.amazon.com/waf/latest/developerguide/limits.html |
| IP set | CIDR addresses, no `/0` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_ip_set.html.markdown |
| IP set size | max 10,000 addresses per set | https://docs.aws.amazon.com/waf/latest/developerguide/limits.html |
| Association | `resource_arn` + `web_acl_arn`; create timeout 5m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_association.html.markdown |
| Association rate | 1 AssociateWebACL call per 2 s per account/Region | https://docs.aws.amazon.com/waf/latest/developerguide/limits.html |
| CloudFront | `web_acl_id` takes the WAFv2 ACL ARN | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown |
| Logging | destination name prefix `aws-waf-logs-` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_logging_configuration.html.markdown |
| Security Hub | WAF.10 not empty, WAF.11 logging, WAF.12 metrics | https://docs.aws.amazon.com/securityhub/latest/userguide/waf-controls.html |

## 5.x → 6.x Migration (WAFv2)

Breaking changes in 6.0.0 that affect WAFv2
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-22):

- **`aws_wafv2_web_acl`**: the default of `managed_rule_group_configs.aws_managed_rules_bot_control_rule_set.enable_machine_learning`
  is now `false`. To keep the previous behavior set it explicitly to `true`.
- No other WAF, wafv2 or `web_acl_id` items in the guide.

Later additions (CHANGELOG 6.48.0 → 6.70.0, read in two windows (medium confidence)): 6.59.0 `pre_parse_text_transformation`
on six statement types; 6.65.0 `aws_wafv2_ip_set` List Resource and Resource Identity; 6.69.0 `monetize` action and
`monetization_config`. The version that introduced `aws_wafv2_web_acl_rule` was not located (unverified).

## External Resources

All fetched 2026-10-22.

- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Enhanced region support: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- AWS WAF quotas: https://docs.aws.amazon.com/waf/latest/developerguide/limits.html
- AWS WAF testing: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-testing.html
- CreateWebACL API: https://docs.aws.amazon.com/waf/latest/APIReference/API_CreateWebACL.html
- Security Hub WAF controls: https://docs.aws.amazon.com/securityhub/latest/userguide/waf-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
