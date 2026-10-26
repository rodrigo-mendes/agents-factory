# Unverified Claims and Risks — hashicorp/aws 6.x Cost Management

Sources read 2026-10-23 (Terraform 1.17.0 CHANGELOG read 2026-10-22). See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **Terraform 1.17.0 is stable** (2026-10-21) but is not the target of this skill (target `~> 1.16`; newest
  1.16.x is 1.16.7, 2026-10-22). Re-verify when starting new work.
  Source: https://releases.hashicorp.com/terraform/
- **hashicorp/aws latest is 6.70.0** (2026-10-21); the constraint `~> 6.69` allows 6.70.x. No 7.x release exists.
  Source: https://releases.hashicorp.com/terraform-provider-aws/
- **6.57.0 is withdrawn** from GitHub and the Registry; do not pin it.
- **v7 is planned**: the 6.0 upgrade guide says "`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`".
  When v7 ships, create a new skill `provisioning-aws-cost-management-v7`.
- `aws_savingsplans_savings_plan` is "best effort" in the provider (6.62.0 note); behaviour may change.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `aws_ce_cost_allocation_tag` behaviour on destroy (deactivate vs no-op) is not documented on the page | (unverified) |
| U2 | Earlier deprecation of numeric `threshold` fields on anomaly subscriptions is not documented on the current page | (unverified) |
| U3 | Region co-location requirement between Budgets and SNS topics; AWS says same account and is silent on region | (unverified) |
| U4 | Whether cost allocation tags must be activated from the management/payer account is not stated on the AWS activation page | (unverified) |
| U5 | Cancellation path for an active Savings Plan after purchase is not documented on the resource page | (unverified) |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | CUR provider for `us-east-1`: the page says the service is "only available in `us-east-1` currently"; configuring the provider for it is an inference | (medium confidence) |
| M2 | Data Exports home region `us-east-1`: appears only in the AWS bucket-policy `aws:SourceArn`; the Terraform page states no requirement | (medium confidence) |
| M3 | The `threshold_expression.dimension.key` description on the anomaly subscription page reads like a cost-category copy | (medium confidence) |
| M4 | The 6.0 upgrade guide has no entries for budgets, `ce_*`, `bcmdataexports`, Savings Plans, Cost Optimization Hub or Billing | (medium confidence, absence of evidence) |
| M5 | CHANGELOG 6.48.0 to 6.70.0 has no entries for `aws_budgets_*`, `aws_ce_*`, `aws_cur_report_definition`, `aws_bcmdataexports_export` | (medium confidence, absence of evidence) |
| M6 | Security Hub controls reference has no controls for Budgets, Billing, Cost Explorer, CUR, Data Exports or Savings Plans | (medium confidence, absence of evidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG was read in two windows; the second began mid-6.54.0, so early 6.54.0 entries may not have been reviewed |
| L2 | Cost Optimization Hub and Billing resources (for example `aws_costoptimizationhub_*`, billing views) are not covered |
| L3 | Data sources (`data.aws_budgets_budget`, `data.aws_ce_*`) are not covered |
| L4 | Resource pages are read from the upstream `main` branch, which may run slightly ahead of the reference patch |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Ask First — CUR provider region | M1 |
| (medium confidence) | SKILL.md Ask First — Data Exports home region | M2 |
| (unverified) | SKILL.md Ask First — cost allocation tag destroy | U1 |
| (unverified) | SKILL.md Ask First — anomaly subscription thresholds (deprecated numeric fields) | U2 |
| (medium confidence) | SKILL.md Ask First — anomaly subscription thresholds (`dimension.key` description) | M3 |
| (unverified) | SKILL.md Ask First — Budgets and SNS region | U3 |
| (unverified) | SKILL.md Ask First — tag activation account | U4 |
| (unverified) | never-do-reporting-migration.md §3 Destroying an active Savings Plan | U5 |
| (medium confidence, absence of evidence) | SKILL.md Quick Reference — Security Hub controls | M6 |
| (medium confidence, absence of evidence) | SKILL.md 5.x → 6.x Migration — guide entries | M4 |
| (medium confidence, absence of evidence) | SKILL.md 5.x → 6.x Migration — CHANGELOG entries | M5 |
| (unverified), (medium confidence) | Unverified Items and Medium-Confidence Items tables above — status column | U1–U5, M1–M6 |

## Source Bibliography

All read 2026-10-23 unless noted.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown — budget arguments, filters, import
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown — action arguments, definitions, timeouts
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_monitor.html.markdown — monitor types
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_subscription.html.markdown — subscription arguments
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_category.html.markdown — cost category arguments
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_allocation_tag.html.markdown — tag activation
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cur_report_definition.html.markdown — CUR arguments, us-east-1 note
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/bcmdataexports_export.html.markdown — Data Exports arguments
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown — Savings Plan warning and arguments
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — upgrade path, `s3_prefix`, v7 note
11. https://docs.aws.amazon.com/cur/latest/userguide/cur-s3.html — CUR bucket policy
12. https://docs.aws.amazon.com/cur/latest/userguide/dataexports-s3-bucket.html — Data Exports bucket policy
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; 6.62.0 Savings Plans entries
14. https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html — alerts, tags, SNS, action guidance
15. https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html — quotas
16. https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html — tag activation
17. https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html — CUR 2.0 recommendation
18. https://docs.aws.amazon.com/cur/latest/userguide/dataexports-create-standard.html — refresh frequency
19. https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-sns-policy.html — SNS policy for Budgets
20. https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html — controls reference
21. https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/ — Budgets pricing
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — global services
23. https://releases.hashicorp.com/terraform/ — Terraform releases
24. https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md — 1.17.0 (read 2026-10-22)
25. https://releases.hashicorp.com/terraform-provider-aws/ — provider releases
26. https://developer.hashicorp.com/terraform/language/backend/s3 — `use_lockfile`; `dynamodb_table` deprecated
27. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — constraint style
28. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown — identity import needs Terraform >= 1.12.0
