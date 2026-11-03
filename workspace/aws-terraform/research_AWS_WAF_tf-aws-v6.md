# Research — AWS WAF (WAFv2) with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-22**. Status: **COMPLETE** (unit `waf`, flat fan-out, no sub-agents).
> Scope: **WAFv2 only** (`aws_wafv2_*`). WAF Classic (`aws_waf_*`, `aws_wafregional_*`) is legacy and out of scope.
> Registry pages render JS-only (F12); upstream raw markdown on `main` is the source for resource docs.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_WAF_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6); 1.17.0 stable but not the target | F1, F2 |
| hashicorp/aws | latest 6.70.0 ("## 6.70.0 (October 21, 2026)", released); constraint `~> 6.69`; never pin 6.57.0 | F3, F4; [2] |
| Region model | Regional resources take optional `region`; forces replacement; import `id@region` | F5 |
| Global exception list | Lists **WAF Classic (`aws_waf_*`)** only — **`aws_wafv2_*` is not mentioned** in the enhanced-region-support guide | F14; [3] |
| Identity import | `identity` block needs Terraform >= 1.12.0 (stated on `aws_wafv2_ip_set`, `aws_wafv2_web_acl_rule`) | F11; [8], [10] |

### 1.1 F14 check — `region` on `aws_wafv2_*` (reported exactly)
- The enhanced-region-support guide's only WAF mention is "WAF Classic (`aws_waf_*`)" in the Global services list. It does not mention wafv2 or wafregional. [3]
- **Every in-scope `aws_wafv2_*` resource page documents `region` as optional**: "Region where this resource will be managed. Defaults to the Region set in the provider configuration." (web_acl [4], web_acl_association [5], ip_set [8], regex_pattern_set [9], rule_group [7], web_acl_logging_configuration [6], web_acl_rule_group_association [11], web_acl_rule [10]). WAFv2 is therefore **regional**, not global, in provider 6.x.
- `scope` on web_acl / rule_group / ip_set / regex_pattern_set: "Valid values are `CLOUDFRONT` or `REGIONAL`. To work with CloudFront, you must also specify the region `us-east-1` (N. Virginia) on the AWS provider." [4][7][9] (ip_set: "…specify the Region US East (N. Virginia)." [8])
- AWS API (CreateWebACL `Scope`): "To work with CloudFront, you must also specify the Region US East (N. Virginia)… API and SDKs - For all calls, use the Region endpoint us-east-1." Also: "For an AWS Amplify application, use `CLOUDFRONT`." [12]
- Consequence for skills: CLOUDFRONT-scope WAFv2 resources need a us-east-1 provider alias **or** (6.x) `region = "us-east-1"` on the resource. The docs only literally say "on the AWS provider"; using the per-resource `region` argument for this is inferred from F5 → (medium confidence, M1).
- `aws_cloudfront_distribution.web_acl_id`: "To specify a web ACL created using the latest version of AWS WAF (WAFv2), use the ACL ARN, for example `aws_wafv2_web_acl.example.arn`… The WAF Web ACL must exist in the WAF Global (CloudFront) region…" [13]

## 2. Provider 6.x changes for WAFv2

6.0.0 upgrade guide (F13) [14] — single WAFv2 item:
- `aws_wafv2_web_acl`: default of `rule.statement.managed_rule_group_statement.managed_rule_group_configs.aws_managed_rules_bot_control_rule_set.enable_machine_learning` is now `false`. "To retain the previous behavior where the argument was omitted, explicitly set the value to `true`." ⚠️ Migration Note.
- No other WAF / wafv2 / `web_acl_id` items in the guide. [14]

CHANGELOG 6.48.0 → 6.70.0 [2]:

| Version (date) | Entry |
|---|---|
| 6.59.0 (2026-08-12) | `aws_wafv2_rule_group`, `aws_wafv2_web_acl`: add `pre_parse_text_transformation` to `byte_match_statement`, `regex_match_statement`, `regex_pattern_set_reference_statement`, `size_constraint_statement`, `sqli_match_statement`, `xss_match_statement` (#49381) |
| 6.65.0 (2026-09-16) | New List Resource `aws_wafv2_ip_set`; `aws_wafv2_ip_set` Resource Identity support (#50031) |
| 6.65.0 | Bug fix `aws_wafv2_rule_group` / `aws_wafv2_web_acl`: `field_to_match.single_header.name` and `single_query_argument.name` no longer reject values the API accepts (e.g. names with `.`) (#49984) |
| 6.69.0 (2026-10-14) | `aws_wafv2_rule_group`, `aws_wafv2_web_acl`: add `monetize` rule action and `monetization_config` argument (#48419) |
| 6.48–6.58, 6.60–6.64, 6.66–6.68, 6.69.1, 6.70.0 | No WAFv2 entries found |

- The introduction version of `aws_wafv2_web_acl_rule` was not found in 6.48–6.70 → predates 6.48 or not located (U1).

## 3. `aws_wafv2_web_acl` [4]

- **Required**: `default_action` ("One of `allow` or `block` is required"), `scope` (`CLOUDFRONT`|`REGIONAL`, **forces new**), `visibility_config` (`cloudwatch_metrics_enabled`, `metric_name`, `sampled_requests_enabled`).
- **Optional**: `name` (forces new; random if omitted; conflicts with `name_prefix`), `description`, `rule`, `rule_json` (conflicts with `rule`; "**There is no drift detection at this time**"), `token_domains`, `association_config`, `data_protection_config`, `captcha_config`, `challenge_config`, `custom_response_body`, `monetization_config` (6.69.0), `region`, `tags`.
- **Attributes**: `arn`, `id`, `capacity` (WCUs in use), `application_integration_url`, `tags_all`.
- **Import**: `ID/Name/Scope`, e.g. `a1b2c3d4-…/example/REGIONAL` (import block >= TF 1.5.0 or CLI). No timeouts section documented.

### 3.1 Known limitations (verbatim) and drift warning
- "Inline `rule` blocks in this resource have several known limitations." — **Deletion ordering errors** (rule must be detached before a referenced IP set / rule group is deleted), **Spurious diffs** ("AWS returns rules in an unpredictable order"), **Coupled updates** ("Modifying one inline rule may cause all rules to be recreated").
- WARNING: "If you use the `aws_wafv2_web_acl_rule` or `aws_wafv2_web_acl_rule_group_association` resources with this Web ACL, you must add `lifecycle { ignore_changes = [rule] }` to this resource to prevent configuration drift." → do not mix inline `rule` with these resources without that lifecycle.
- Rules named `^ShieldMitigationRuleGroup_<account-id>_<web-acl-guid>_.*` are AWS-added (Shield Advanced automatic app-layer DDoS mitigation); the provider ignores them unless configured, and managing them may cause permission errors.
- `statement` is recursive but "currently only 3 levels are supported" (use `rule_json` for deeper nesting).

### 3.2 Rule block
- Required: `name`, `priority`, `statement`, `visibility_config`.
- `action` (only for statements not referencing a rule group): `allow`, `block`, `captcha`, `challenge`, `count`, `monetize`.
- `override_action` (rule-group statements): "One of `count` or `none`… is required".
- `rule_label { name }` optional; `captcha_config` / `challenge_config` → `immunity_time_property.immunity_time` (default 300 s).
- `custom_response` (inside `block`): `response_code` (required), `custom_response_body_key` (references top-level `custom_response_body` key), `response_header { name, value }`.

### 3.3 Statements in scope
- `managed_rule_group_statement`: `name`, `vendor_name`, `version` (omit for default version), `rule_action_override` (one per rule: `name` + `action_to_use`, both required), `scope_down_statement`, `managed_rule_group_configs` ("Only one rule attribute is allowed in each config").
- `rate_based_statement`: `limit` (required; range not stated on TF page — AWS minimum is **10** [16]), `evaluation_window_sec` ∈ {60,120,300,600}, default **300**; `aggregate_key_type` ∈ {`CONSTANT`,`CUSTOM_KEYS`,`FORWARDED_IP`,`IP`}, default **`IP`**; `scope_down_statement` required when `CONSTANT`; `forwarded_ip_config` required when `FORWARDED_IP`. Window "doesn't determine how often AWS WAF checks the rate, but how far back it looks".
- `geo_match_statement`: `country_codes` (ISO alpha-2, required; max 50 per statement [16]), optional `forwarded_ip_config`.
- `ip_set_reference_statement`: `arn`, optional `ip_set_forwarded_ip_config`.
- `byte_match_statement`: `positional_constraint` ∈ {`EXACTLY`,`STARTS_WITH`,`ENDS_WITH`,`CONTAINS`,`CONTAINS_WORD`}; 6.59.0 adds `pre_parse_text_transformation`. String max 200 chars [16].
- `response_inspection` (ATP/ACFP): "available only on web ACLs that protect CloudFront distributions."

## 4. `aws_wafv2_web_acl_rule` (separate-rule resource) [10]
- Required: `name`, `priority`, `statement`, `visibility_config`, **`web_acl_arn`**. Optional `region`.
- Parent web ACL must have `lifecycle { ignore_changes = [rule] }`. To adopt an existing inline rule, names must match exactly.
- Import: `web_acl_arn,name`; identity block (TF >= 1.12.0) with `web_acl_arn`, `name`, optional `account_id`, `region`.

## 5. `aws_wafv2_web_acl_association` [5]
- Required: `resource_arn`, `web_acl_arn`. Optional `region`. Timeout `create` default 5m.
- Supported: ALB, **API Gateway stage (REST only; HTTP is unsupported)**, Cognito User Pool, AppSync GraphQL API, App Runner service, Amplify application, Bedrock AgentCore Gateway, Verified Access instance.
- NOTE: "Do not use this resource to associate a WAFv2 Web ACL with a CloudFront Distribution." Use `aws_cloudfront_distribution.web_acl_id = aws_wafv2_web_acl.x.arn` [13].
- Import: `WEB_ACL_ARN,RESOURCE_ARN`.
- AWS: AssociateWebACL limited to one call every 2 s per account/Region [16]; right after creating a web ACL, association may briefly fail as "unavailable" (propagation) [15].

## 6. `aws_wafv2_ip_set` [8]
- Required: `scope`, `ip_address_version` (`IPV4`|`IPV6`). `name` optional (generated). **Forces new**: `name`, `scope`, `ip_address_version`.
- `addresses` in CIDR; "WAF supports all IPv4 and IPv6 CIDR ranges except for `/0`." Max 10,000 per set [16].
- Import `ID/name/scope`; identity import (TF >= 1.12.0); Resource Identity + List Resource since 6.65.0 [2].

## 7. `aws_wafv2_regex_pattern_set` [9]
- Required: `scope` only; `name` (forces new) / `name_prefix`, `regular_expression { regex_string }` (one or more), `description`, `tags`, `region` optional.
- AWS limits: 10 patterns per set, 200 chars per pattern, 10 regex pattern sets per account/Region (default) [16].
- Import `ID/name/scope`.

## 8. `aws_wafv2_rule_group` [7]
- Required: **`capacity` (forces new)**, **`scope` (forces new)**, `visibility_config`. `name` optional, forces new.
- `rules_json` (note the name; not `rule_json`): conflicts with `rule`, no drift detection, import with it set causes a one-time in-place update.
- Import `ID/name/scope`. CLOUDFRONT requires us-east-1 on the provider.
- Capacity is immutable → size it with headroom up front (max 5,000 WCU per rule group [16]).

## 9. `aws_wafv2_web_acl_logging_configuration` [6]
- Required: `log_destination_configs` (Firehose, CloudWatch log group, or S3 bucket ARN), `resource_arn` (web ACL ARN). Optional `region`.
- Destination name "**must** be prefixed with `aws-waf-logs-`".
- WAFv2 "tries to create or update a generic Log Resource Policy named `AWSWAF-LOGS`" — manage a specific resource policy to avoid hitting CloudWatch Logs policy limits.
- `redacted_fields`: one of `method`, `query_string`, `single_header { name }` (lowercase), `uri_path` per block; up to 100 blocks.
- `logging_filter { default_behavior = KEEP|DROP; filter { behavior, requirement = MEETS_ALL|MEETS_ANY, condition { action_condition { action } | label_name_condition { label_name } } } }`; actions `ALLOW`,`BLOCK`,`COUNT`,`CAPTCHA`,`CHALLENGE`,`EXCLUDED_AS_COUNT`.
- Import: web ACL ARN.

## 10. `aws_wafv2_web_acl_rule_group_association` [11]
- Exists. Required: `rule_name` (1–128), `priority`, `web_acl_arn`, and exactly one of `rule_group_reference` / `managed_rule_group` (conflict).
- `override_action`: `none` (default) or `count`.
- Managed groups: "WAF silently ignores any override that uses an invalid rule name"; custom groups: invalid names make the update fail.
- Parent web ACL needs `lifecycle { ignore_changes = [rule] }`.
- Import: `WebACLARN,RuleName,custom,RuleGroupARN` or `WebACLARN,RuleName,managed,VendorName:RuleGroupName[:Version]`. Timeouts create/update/delete 30m.

## 11. AWS guidance

### 11.1 Best practices
- Test in staging first, "Then test and tune the rules in count mode with your production traffic before enabling them." Applies to managed groups too (also follow vendor guidance, e.g. Bot Control/ATP/ACFP deployment pages). [15] In TF: `override_action { count {} }` for a whole group, or `rule_action_override { action_to_use { count {} } }` per rule [4].
- Changes propagate in seconds to minutes; expect temporary inconsistencies (rule/IP set updates not yet effective everywhere). [15]
- WCU: hard max 5,000 per web ACL and per rule group; **>1,500 WCU in a web ACL incurs extra cost** (not a limit). [16] Read `capacity` attribute to track. [4]
- Rate-based rules: min rate 10, max 10 per web ACL / 4 per rule group. Body inspection default 16 KB (CloudFront, API GW, Cognito, App Runner, Verified Access, AgentCore), max 64 KB; ALB/AppSync fixed 8 KB. [16]
- Priority: lower numbers evaluated first [11]; detailed AWS priority semantics page not fetched (L2).

### 11.2 Security Hub CSPM controls [17]

| ID | Title | Severity | Resource type | Applies |
|---|---|---|---|---|
| WAF.1 | WAF Classic Global Web ACL logging should be enabled | Medium | AWS::WAF::WebACL | Classic |
| WAF.2 | WAF Classic Regional rules should have at least one condition | Medium | AWS::WAFRegional::Rule | Classic |
| WAF.3 | WAF Classic Regional rule groups should have at least one rule | Medium | AWS::WAFRegional::RuleGroup | Classic |
| WAF.4 | WAF Classic Regional web ACLs should have at least one rule or rule group | Medium | AWS::WAFRegional::WebACL | Classic |
| WAF.6 | WAF Classic global rules should have at least one condition | Medium | AWS::WAF::Rule | Classic |
| WAF.7 | WAF Classic global rule groups should have at least one rule | Medium | AWS::WAF::RuleGroup | Classic |
| WAF.8 | WAF Classic global web ACLs should have at least one rule or rule group | Medium | AWS::WAF::WebACL | Classic |
| **WAF.10** | AWS WAF web ACLs should have at least one rule or rule group (`wafv2-webacl-not-empty`) | Medium | AWS::WAFv2::WebACL | **v2** |
| **WAF.11** | AWS WAF web ACL logging should be enabled (`wafv2-logging-enabled`; does not count Security Lake) | **Low** | AWS::WAFv2::WebACL | **v2** |
| **WAF.12** | AWS WAF rules should have CloudWatch metrics enabled (`wafv2-rulegroup-logging-enabled`) | Medium | AWS::WAFv2::RuleGroup | **v2** |

TF mapping: WAF.10 → at least one `rule` / `aws_wafv2_web_acl_rule` / rule-group association; WAF.11 → `aws_wafv2_web_acl_logging_configuration`; WAF.12 → `visibility_config.cloudwatch_metrics_enabled = true` on every rule and rule group. (No WAF.5 / WAF.9 on the page.)

## 12. Legacy-file claims found wrong (checklist `workspace/terraform/research_AWS_WAF_aws-v6.x.md`)
1. **"1,500 WCU limit" / "max 1500"** — wrong: hard max is 5,000; 1,500 is only the pricing threshold [16].
2. **Rate limit validation `>= 100`** — wrong: AWS minimum is 10 [16].
3. **`aws_wafv2_web_acl_rule` with `web_acl_id` + `scope`** — wrong: argument is `web_acl_arn`; `scope` is not an argument [10].
4. **Association for HTTP APIs (`aws_apigatewayv2_stage`)** — wrong: "REST only; HTTP is unsupported" [5].
5. **S3 backend with `dynamodb_table`** — deprecated; use `use_lockfile = true` (F7). `required_version ">= 1.7"`/`~> 6.0` superseded (F1, F3).
6. **"CloudFront WAF state must be in us-east-1 backend"** — no official source; backend region is unrelated to WAF scope (unverified claim, treat as wrong).
7. **`WAFUnavailableEntityException` on WCU overflow** / scope-mismatch error text — not found in fetched docs (unverified).
8. Omits that WAFv2 resources accept `region` (6.x) — see §1.1.

## 13. Unverified / medium confidence / limits
- **U1** — Provider version introducing `aws_wafv2_web_acl_rule` (not in 6.48–6.70 CHANGELOG ranges read).
- **U2** — Exact AWS error names for WCU overflow and CLOUDFRONT-scope-in-wrong-region.
- **U3** — Whether Amplify associations via `aws_wafv2_web_acl_association` require a CLOUDFRONT-scope web ACL in us-east-1 (API says "For an AWS Amplify application, use `CLOUDFRONT`" [12]; TF page lists Amplify without that note [5]).
- **M1** — Using per-resource `region = "us-east-1"` (F5) instead of a provider alias for CLOUDFRONT scope: consistent with docs, not literally stated (docs say "on the AWS provider").
- **M2** — CHANGELOG read via two windows (0–200k chars); entries for 6.55.0 head section partially visible; no WAFv2 entries seen.
- **L1** — Managed rule group catalog/WCU per group (CommonRuleSet etc.) not re-verified this round; skills must not hard-code WCU numbers.
- **L2** — AWS rule-priority, logging-destination and Bot Control/ATP deployment pages not fetched.
- **L3** — Data sources (`data.aws_wafv2_*`) out of scope.

## 14. Security note
None. No instruction-like / prompt-injection text observed in fetched pages.

## Source Bibliography
All accessed 2026-10-22.
1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown (via F13/F15)
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_association.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_logging_configuration.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_rule_group.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_ip_set.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_regex_pattern_set.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_rule.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_rule_group_association.html.markdown
12. https://docs.aws.amazon.com/waf/latest/APIReference/API_CreateWebACL.html
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown (WAFv2 section)
15. https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-testing.html
16. https://docs.aws.amazon.com/waf/latest/developerguide/limits.html
17. https://docs.aws.amazon.com/securityhub/latest/userguide/waf-controls.html
18. https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-features.html
