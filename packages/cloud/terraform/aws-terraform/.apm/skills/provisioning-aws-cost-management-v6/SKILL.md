---
name: provisioning-aws-cost-management-v6
description: "Cost Management Terraform (aws 6.x, global): budgets, Cost Anomaly Detection, cost categories, CUR, Data Exports. Use when writing HCL for cost governance. Not for S3, SNS, IAM, Organizations."
---

# Provisioning AWS Cost Management with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference patch 6.69.0 / 6.70.0) + **Terraform ~> 1.16** only.
> Sources read 2026-10-23 (Terraform 1.17.0 CHANGELOG read 2026-10-22). Claims tagged (unverified) or
> (medium confidence) were not fully confirmed against an official page.
> Cost Management is **global** per the enhanced-region guide: no resource-level `region`.

## Version Context

| Item | Value | Source (read 2026-10-23) |
|---|---|---|
| Terraform CLI | **~> 1.16** — newest 1.16.x is 1.16.7 (2026-10-23) | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest **6.70.0** (2026-10-23); reference 6.69.0 / 6.70.0 | https://releases.hashicorp.com/terraform-provider-aws/ |
| aws v7 | Not released — v7 planned | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| 6.57.0 | **Withdrawn** from GitHub and Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Provider constraint | `~> 6.69` is this skill's target for root modules (allows 6.70.x); `~>` semantics and the minimum-only style (`>=`) for reusable modules per the constraints page | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| Identity import | `identity` block needs Terraform >= 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown |
| Identity import (resources) | Documented on `ce_anomaly_monitor`, `ce_anomaly_subscription`, `ce_cost_category`, `bcmdataexports_export` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_monitor.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_subscription.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_category.html.markdown ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/bcmdataexports_export.html.markdown |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable (2026-10-21) but is not the target of this skill; re-verify when starting new work.
- 6.57.0 is withdrawn; a constraint that resolves to it must be avoided.
- v7 is planned ("`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`"); no 7.x release exists. v7 = new skill.

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`), reference patch 6.69.0/6.70.0,
Terraform ~> 1.16. A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Budgets patterns: [terraform block, budget, filters, SNS policy, budget action](./blueprints/always-do-budgets.md)
- Cost intelligence patterns: [anomaly detection, cost category, cost allocation tag](./blueprints/always-do-cost-intelligence.md)
- Reporting and commitments: [CUR, Data Exports, Savings Plan](./blueprints/always-do-reporting-commitments.md)
- Never-do budgets and region: [region, conflicts, operands, tags, role](./blueprints/never-do-budgets-and-region.md)
- Never-do reporting and migration: [s3_prefix, ATHENA, Savings Plan, 6.57.0, backend](./blueprints/never-do-reporting-migration.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated.
  See [budgets §1](./blueprints/always-do-budgets.md#1-terraform-block-and-s3-backend). https://developer.hashicorp.com/terraform/language/backend/s3
- **Use `~> 6.69` in root modules (this skill's target; allows 6.70.x)**.
  See [budgets §1](./blueprints/always-do-budgets.md#1-terraform-block-and-s3-backend). https://releases.hashicorp.com/terraform-provider-aws/
- **Let reusable modules set only a minimum provider version (`>=`)**.
  See [budgets §1](./blueprints/always-do-budgets.md#1-terraform-block-and-s3-backend). https://developer.hashicorp.com/terraform/language/expressions/version-constraints
- **Omit `region` on every Cost Management resource** — Budgets, Billing, Cost Explorer, Cost Optimization Hub, CUR, Data Exports and Savings Plans are global.
  See [budgets §2](./blueprints/always-do-budgets.md#2-budget-with-notifications). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- **Give each budget `notification` either `subscriber_email_addresses` or `subscriber_sns_topic_arns`**.
  See [budgets §2](./blueprints/always-do-budgets.md#2-budget-with-notifications). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown
- **Give every `and`/`or` in a budget `filter_expression` at least 2 operands**.
  See [budgets §3](./blueprints/always-do-budgets.md#3-budget-filter-rules). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown
- **Set `metrics` whenever `filter_expression` is used**.
  See [budgets §3](./blueprints/always-do-budgets.md#3-budget-filter-rules). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown
- **Grant `budgets.amazonaws.com` `SNS:Publish` with `aws:SourceAccount` and `aws:SourceArn` conditions** on the SNS topic.
  See [budgets §4](./blueprints/always-do-budgets.md#4-sns-topic-policy-for-budgets). https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-sns-policy.html
- **Set `ssm_action_definition.region` to the region where the SSM document runs** — it is not the resource region.
  See [budgets §5](./blueprints/always-do-budgets.md#5-budget-action). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown
- **Use an `execution_role_arn` role in the same account as the budget action**.
  See [budgets §5](./blueprints/always-do-budgets.md#5-budget-action). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown
- **Set `monitor_dimension` for `DIMENSIONAL` anomaly monitors and `monitor_specification` for `CUSTOM` ones**.
  See [cost intelligence §6](./blueprints/always-do-cost-intelligence.md#6-anomaly-monitor). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_monitor.html.markdown
- **Set `s3_prefix` on every `aws_cur_report_definition`** — required since 6.0.
  See [reporting §10](./blueprints/always-do-reporting-commitments.md#10-legacy-cur-report). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- **Set `refresh_cadence.frequency = "SYNCHRONOUS"` on `aws_bcmdataexports_export`** — the only documented value.
  See [reporting §11](./blueprints/always-do-reporting-commitments.md#11-data-exports). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/bcmdataexports_export.html.markdown
- **Use the resource `aws_savingsplans_savings_plan`**.
  See [reporting §12](./blueprints/always-do-reporting-commitments.md#12-savings-plan). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown
- **Set `upfront_payment_amount` only for All/Partial Upfront Savings Plans** — omit it for No Upfront.
  See [reporting §12](./blueprints/always-do-reporting-commitments.md#12-savings-plan). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| CUR provider region | The `aws_cur_report_definition` page says CUR is "only available in `us-east-1` currently"; configuring the provider (or an alias) for `us-east-1` is an inference from that note (medium confidence). | "Should the CUR resource use a provider or alias configured for us-east-1?" |
| Data Exports home region | The `aws_bcmdataexports_export` page states no region requirement; `us-east-1` appears in the AWS bucket-policy `aws:SourceArn` only (medium confidence). | "Should the Data Exports resource use a us-east-1 provider, given the page states no requirement?" |
| CUR vs Data Exports | AWS: "CUR 2.0 is the new and recommended way to receive your detailed AWS cost and usage data"; legacy CUR uses a different API action set. ([source](https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html)) | "Legacy CUR (`aws_cur_report_definition`) or Data Exports (`aws_bcmdataexports_export`)?" |
| Budget action type and approval | `APPLY_IAM_POLICY`, `APPLY_SCP_POLICY`, `RUN_SSM_DOCUMENTS`; `approval_model` `AUTOMATIC` or `MANUAL`. AWS: stopping EC2 in an Auto Scaling group is ineffective unless a second action removes the launch role's permissions. ([source](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html)) | "Which action type, and automatic or manual approval?" |
| Action-enabled budget cost | AWS pricing: monitoring and notifications are free; first two action-enabled budgets free per month, then $0.10/day per action-enabled budget. ([source](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/)) | "More than two action-enabled budgets — is the daily charge acceptable?" |
| Savings Plans purchase | Financial commitment; an active plan "cannot be cancelled or deleted"; provider support is "best effort" (6.62.0 note). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown)) | "Confirm the commitment, offering ID and upfront option before apply." |
| Cost allocation tag destroy | Destroy behaviour is not documented on the `aws_ce_cost_allocation_tag` page (unverified). The page says tag keys can take up to 24 hours to appear for activation. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_allocation_tag.html.markdown)) | "Is deactivation on destroy required? Confirm the behaviour before relying on it." |
| Anomaly subscription thresholds | The current page shows `threshold_expression`; any earlier deprecation of numeric `threshold` fields is not documented there (unverified). The page's `dimension.key` description reads like a cost-category copy (medium confidence). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_subscription.html.markdown)) | "Use `threshold_expression` with `ANOMALY_TOTAL_IMPACT_ABSOLUTE`/`_PERCENTAGE` as in the page examples?" |
| Budgets and SNS region | AWS says the SNS topic must be in the same account (cross-account not supported); a region requirement is not stated (unverified). ([source](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-sns-policy.html)) | "Is the SNS topic in the same account? Is a region constraint relevant?" |
| Tag activation account | Whether cost allocation tags must be activated from the management account is not stated in the AWS activation page (unverified). ([source](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html)) | "Which account activates the tags?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `region` on a Cost Management resource — Budgets, Billing, Cost Explorer, Cost Optimization Hub, CUR, Data Exports and Savings Plans are global (no `region` argument). ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown)) | Omit `region` |
| Combine `cost_filter` with `filter_expression`, or `metrics` with `cost_types` on `aws_budgets_budget` — documented conflicts. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown)) | Use one of each pair; `filter_expression` goes with `metrics` |
| Write an `and`/`or` block in `filter_expression` with fewer than 2 operands — "`and` and `or` require at least 2 operands". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown)) | Give 2+ operands, or use a single `dimensions`, `tags` or `cost_categories` root |
| Expect budget `tags` to act as cost allocation tags — "AWS Budgets does not support tags for cost allocation". ([source](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html)) | Activate tag keys with `aws_ce_cost_allocation_tag` ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_allocation_tag.html.markdown)) |
| Use an `execution_role_arn` from another account — roles and actions must be in the same account. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown)) | Use a role in the budget action's account |
| Omit `s3_prefix` on `aws_cur_report_definition` — required since 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | Set `s3_prefix` |
| Combine `ATHENA` with other `additional_artifacts`, or use it without `report_versioning = "OVERWRITE_REPORT"`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cur_report_definition.html.markdown)) | `additional_artifacts = ["ATHENA"]` alone with `report_versioning = "OVERWRITE_REPORT"` |
| Rely on `terraform destroy` to cancel an active Savings Plan — it "cannot be cancelled or deleted"; destroy only removes it from state. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown)) | Confirm the commitment before apply; only `queued` plans can be deleted |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch |
| S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |

## Quick Reference

Sources read 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Terraform / provider constraint | `~> 1.16` / `~> 6.69` are this skill's targets; `~>` semantics on the constraints page | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| S3 locking | `use_lockfile = true`; `dynamodb_table` deprecated | https://developer.hashicorp.com/terraform/language/backend/s3 |
| Global resources | No `region` argument, no `@region` import | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Not the resource region | `ssm_action_definition.region` (budget action, required) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown |
| Not the resource region | `s3_region` (CUR bucket) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cur_report_definition.html.markdown |
| Not the resource region | `s3_destination.s3_region` (Data Exports bucket) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/bcmdataexports_export.html.markdown |
| Not the resource region | Exported `region` attribute ("The AWS Region") on Savings Plans | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown |
| Budget import | `AccountID:BudgetName` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown |
| Budget action import | `AccountID:ActionID:BudgetName` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown |
| Budgets pricing (AWS page) | Monitoring and notifications free; first two action-enabled budgets free per month, then $0.10/day per action-enabled budget | https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/ |
| Budget `time_unit` | `MONTHLY`, `QUARTERLY`, `ANNUALLY`, `DAILY` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown |
| Budget action timeouts | create/update/delete 5m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown |
| Anomaly subscription `frequency` | `DAILY`, `IMMEDIATE`, `WEEKLY` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_subscription.html.markdown |
| Anomaly quotas (AWS page) | 10 email recipients and 1 SNS topic per subscription; 500 customer managed monitors per management account | https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html |
| Budget alerts (AWS page) | Up to 10 email addresses and one SNS topic per alert | https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html |
| Budgets SNS topic (AWS page) | Topic must be in the same account | https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-sns-policy.html |
| Cost allocation tag | `status` `Active` or `Inactive`; up to 24 hours to appear for activation | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_allocation_tag.html.markdown |
| CUR bucket policy | Principal `billingreports.amazonaws.com`; conditions `aws:SourceArn` and `aws:SourceAccount` | https://docs.aws.amazon.com/cur/latest/userguide/cur-s3.html |
| Data Exports bucket policy | Principal `bcm-data-exports.amazonaws.com`; `s3:PutObject` | https://docs.aws.amazon.com/cur/latest/userguide/dataexports-s3-bucket.html |
| Data Exports timeouts | create 30m, update 30m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/bcmdataexports_export.html.markdown |
| Savings Plans resource | `aws_savingsplans_savings_plan`; timeouts create/delete 30m; import `sp-…` ID | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown |
| Security Hub controls | No controls for Budgets, Billing, Cost Explorer, CUR, Data Exports or Savings Plans in the controls reference (medium confidence, absence of evidence) | https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html |

## 5.x → 6.x Migration (Cost Management)

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown (read 2026-10-23).

- Before upgrading: "Before upgrading to version `6.0.0`, first upgrade to the latest available `5.x` version of the provider."
- Run a plan that completes "without errors or unexpected changes", then "update [version constraints] to allow the `6.x` series" (this skill uses `~> 6.69`).
- Run `terraform init -upgrade` "to download the new version".
- **`aws_cur_report_definition`**: `s3_prefix` is now required.
- No other in-scope entries (budgets, `ce_*`, `bcmdataexports`, Savings Plans, Cost Optimization Hub, Billing) in the guide (medium confidence, absence of evidence).
- 6.62.0 (2026-08-26) CHANGELOG: `aws_savingsplans_savings_plan` is "best effort" ("Because we cannot easily test this functionality"); `upfront_payment_amount` is now `Computed`. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- No entries for `aws_budgets_*`, `aws_ce_*`, `aws_cur_report_definition`, `aws_bcmdataexports_export` in 6.48.0 to 6.70.0 of the same CHANGELOG (medium confidence, absence of evidence).

## External Resources

All read 2026-10-23.

- Provider releases: https://releases.hashicorp.com/terraform-provider-aws/
- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Enhanced region support: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- AWS Budgets best practices: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html
- AWS Budgets SNS policy: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-sns-policy.html
- AWS Cost Management quotas: https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html
- AWS CUR S3 bucket: https://docs.aws.amazon.com/cur/latest/userguide/cur-s3.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
