# Unverified Claims and Risks — hashicorp/aws 6.x WAFv2

Research date 2026-10-22. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-22 (latest 6.70.0, reference 6.69.0).
  Re-verify when starting new work or after 30 days. Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 is stable since 2026-10-21.** This skill targets `~> 1.16` (1.16.6) and does not
  adopt 1.17; re-verify before moving the constraint. Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is withdrawn** from GitHub and the Registry; never pin it.
- **v7 is planned** (not released). When it ships, create `provisioning-aws-waf-v7`.
- WAF Classic (`aws_waf_*`, `aws_wafregional_*`) is legacy and out of scope.

## Unverified Items

Register order: U (unverified), M (medium confidence), L (coverage limits). There are no I items.

| Tag | Item | Status |
|---|---|---|
| U1 | Provider version that introduced `aws_wafv2_web_acl_rule` — not in the 6.48–6.70 CHANGELOG ranges read | (unverified) — it predates 6.48 or was not located |
| U2 | Exact AWS error names for WCU overflow and CLOUDFRONT scope in the wrong region | (unverified) — do not quote error text |
| U3 | Whether an Amplify association needs a CLOUDFRONT-scope web ACL in us-east-1 (API says use `CLOUDFRONT`; Terraform page lists Amplify without a note) | (unverified) — ask before writing |
| U4 | Claim that the CloudFront-scope WAF state must live in a us-east-1 backend | (unverified) — no official source; treated as wrong |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `region = "us-east-1"` on a WAF resource instead of a provider alias for CLOUDFRONT scope | (medium confidence) — consistent with the `region` model, docs literally say "on the AWS provider" |
| M2 | CHANGELOG read in two windows; 6.55.0 head section partly visible; no WAFv2 entries seen there | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Managed rule group catalog and WCU per group not re-verified; do not hard-code WCU numbers |
| L2 | AWS rule-priority, logging-destination and Bot Control/ATP deployment pages not fetched |
| L3 | Data sources (`data.aws_wafv2_*`) out of scope |
| L4 | Inner arguments of `rule_group_reference` / `managed_rule_group` in `aws_wafv2_web_acl_rule_group_association` not detailed in the research; no HCL provided for it |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Ask First — CLOUDFRONT scope region | M1 |
| (medium confidence) | always-do-foundation.md §3 CLOUDFRONT scope | M1 |
| (medium confidence) | never-do-attachment-scope.md §7 alternative `region = "us-east-1"` | M1 |
| (medium confidence) | SKILL.md 5.x → 6.x Migration — CHANGELOG windows | M2 |
| (unverified) | SKILL.md Ask First — Amplify association | U3 |
| (unverified) | SKILL.md 5.x → 6.x Migration — `aws_wafv2_web_acl_rule` introduction version | U1 |
| (unverified) | never-do-limits-provider.md §8 WCU overflow error name | U2 |
| (unverified) | never-do-limits-provider.md §10 backend-region claim | U4 |

## Source Bibliography

All accessed 2026-10-22. Numbers match the unit research.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
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
19. https://releases.hashicorp.com/terraform/ and https://releases.hashicorp.com/terraform-provider-aws/
20. https://developer.hashicorp.com/terraform/language/backend/s3
