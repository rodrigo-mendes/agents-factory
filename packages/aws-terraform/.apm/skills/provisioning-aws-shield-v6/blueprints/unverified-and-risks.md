# Unverified Claims and Risks — hashicorp/aws 6.x Shield

Research date 2026-10-23. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-23 (latest 6.70.0). Re-verify when
  starting new work. Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 became stable on 2026-10-21.** This skill targets `~> 1.16` (1.16.6) by
  decision; re-verify before moving. Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is permanently withdrawn**; any constraint resolving to it fails `terraform init`.
- **v7 is planned.** When it ships, create a new skill `provisioning-aws-shield-v7`.
- **L7 automatic response is legacy** after 2026-03-26 in favor of the Anti-DDoS Managed Rule Group
  in AWS WAF. Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Import ID for `aws_shield_application_layer_automatic_response` — no import section on the page | (unverified) — not asserted in this skill |
| U2 | Shield Advanced monthly price amount — pricing page not fetched | (unverified) — only "1 year commitment, monthly fee" is stated |
| U3 | Shield CloudWatch metrics region claim — not verified | (unverified) — not asserted in this skill |
| U4 | Hard API dependency of proactive engagement on the DRT role association — not on the page | (unverified) — registered at always-do-detection-response §6 |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | No Security Hub Shield control — reference read fully, but `shield-controls.html` body did not render | (medium confidence) |
| M2 | Protection group `aggregation`/`pattern`/`resource_type` enums taken from page examples only | (medium confidence) |
| M3 | `skip_destroy` + `prevent_destroy` combination is an inference from documented destroy semantics | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG chunks before 6.40.0 not read |
| L2 | `data.aws_shield_protection` not covered |
| L3 | Shield pricing and Firewall Manager Shield policy resources (`aws_fms_policy`) not researched |

## Tag to Register Mapping

U1 and U3 are registered only (not present in any skill text).

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First row "Subscribing" — price amount | U2 |
| (unverified) | always-do-detection-response.md §6 Proactive Engagement — apply without DRT role | U4 |
| (medium confidence) | SKILL.md Ask First row "Subscription destroy protection" | M3 |
| (medium confidence) | always-do-subscription-protection.md §1 — `skip_destroy`/`prevent_destroy` comment | M3 |
| (medium confidence) | always-do-subscription-protection.md §3 — enum values | M2 |
| (medium confidence) | SKILL.md Quick Reference row `aws_shield_protection_group` | M2 |
| (medium confidence) | SKILL.md Quick Reference row Security Hub | M1 |
| (medium confidence) | SKILL.md Ask First rows "Health check choice" and "Protection groups and L7 mitigation" — unversioned "latest" AWS pages | not a register item (page-versioning caveat) |
| (medium confidence) | always-do-detection-response.md §4 — health check requirements | not a register item (page-versioning caveat) |

## Source Bibliography

All fetched 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — Shield Advanced global
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — no Shield entries 6.40.0–6.70.0; 6.57.0 withdrawn
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_group.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_subscription.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_health_check_association.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_role_arn_association.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_log_bucket_association.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_application_layer_automatic_response.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_proactive_engagement.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no Shield changes
12. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-standard-summary.html — Shield Standard
13. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html — supported types; NLB via EIP
14. https://docs.aws.amazon.com/waf/latest/developerguide/enable-ddos-prem.html — per-account subscription; Firewall Manager
15. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary.html — WAF fees covered
16. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html — health checks
17. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html — L7AM legacy
18. https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html — no Shield control
19. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-viewing-multiple-accounts.html
20. https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html
21. https://developer.hashicorp.com/terraform/language/backend/s3 — `use_lockfile`
22. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — `~>` semantics
23. https://releases.hashicorp.com/terraform/ and https://releases.hashicorp.com/terraform-provider-aws/ — versions
