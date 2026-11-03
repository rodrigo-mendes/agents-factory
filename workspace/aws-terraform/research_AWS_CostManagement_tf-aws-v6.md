# Research — AWS Cost Management with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `cost-management`, P4 fan-out, flat — no sub-agents).
> Registry pages render JS-only (F12); upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`) is the source for resource docs.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_CostManagement_aws-v6.x.md` (6.47.0, Terraform 1.9 — superseded). Claims found wrong are listed in §9.
> All URLs below were read on 2026-10-23 unless a family fact (F#) says otherwise.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI target | `required_version = "~> 1.16"` (1.16.7 newest 1.16.x); 1.17.0 stable but not the target | F1, F2 |
| hashicorp/aws | latest 6.70.0 (2026-10-21); constraint `version = "~> 6.69"`; no 7.x | F3, F18 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Constraint style | root `~>`, reusable modules `>=` | F6 |
| S3 backend | `use_lockfile = true`; `dynamodb_table` deprecated | F7 |
| Identity-based import | `identity` block needs Terraform >= 1.12.0 (documented on ce_anomaly_monitor, ce_anomaly_subscription, ce_cost_category, bcmdataexports_export) | F11; [3][4][5][8] |
| Region model | Budgets, Billing, Cost Explorer, Cost Optimization Hub, CUR, Data Exports, Savings Plans are **global** — no `region` argument, no `@region` import | F5, F14 |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

### 1.1 Per-page `region` / us-east-1 verification (requested check)

| Resource | `region` argument documented? | us-east-1 statement on the TF page | AWS-doc statement |
|---|---|---|---|
| `aws_budgets_budget` | No | None | — [1] |
| `aws_budgets_budget_action` | No (only `ssm_action_definition.region`, *required*, "the region to run the SSM document") | None | — [2] |
| `aws_ce_anomaly_monitor` | No | None | — [3] |
| `aws_ce_anomaly_subscription` | No (only `account_id`) | None | — [4] |
| `aws_ce_cost_category` | No | None | — [5] |
| `aws_ce_cost_allocation_tag` | No | None | — [6] |
| `aws_cur_report_definition` | No (only `s3_region` for the bucket) | **Yes**: "The AWS Cost and Usage Report service is only available in `us-east-1` currently." | CUR bucket policy `aws:SourceArn` = `arn:aws:cur:us-east-1:${AccountId}:definition/*` [11] |
| `aws_bcmdataexports_export` | No (only `s3_destination.s3_region`) | **No** requirement stated; us-east-1 appears only in example import ARNs | Data Exports bucket policy `aws:SourceArn` = `arn:aws:bcm-data-exports:us-east-1:{source-account-id}:export/*` [12] |
| `aws_savingsplans_savings_plan` | No (`region` is an exported *attribute*, "The AWS Region") | None | — [9] |

Consequence: per F14 none of these accept `region`; for CUR the page says the service is us-east-1-only, so run it with a provider (or alias) configured for `us-east-1` (M1 — the page states availability, not explicitly "configure the provider in us-east-1"). For Data Exports the TF page states no provider-region requirement; the us-east-1 ARN in the AWS bucket policy implies the service home region is us-east-1 (M2).

## 2. Provider 6.x changes for this service

- **6.0.0 upgrade guide (F13)** — the only in-scope entry: `aws_cur_report_definition`: "`s3_prefix` is now required." No entries for budgets, `ce_*`, bcmdataexports, savingsplans, costoptimizationhub or billing. [10]
- **CHANGELOG 6.48.0 (2026-06-03) → 6.70.0 (2026-10-21)** [13]:
  - 6.62.0 (2026-08-26) NOTES: "resource/aws_savingsplans_savings_plan: Because we cannot easily test this functionality, it is best effort".
  - 6.62.0 BUG FIXES: `aws_savingsplans_savings_plan` — "Mark `upfront_payment_amount` as `Computed`…".
  - No entries for `aws_budgets_*`, `aws_ce_*`, `aws_cur_report_definition`, `aws_bcmdataexports_export` in the range (last `aws_budgets_budget` entry is 6.41.0, out of range). See L1 for a coverage gap around 6.54.0.

## 3. `aws_budgets_budget` [1]

- **Required**: `budget_type` (cost/usage tracking; COST, USAGE, RI_UTILIZATION etc. per examples), `time_unit` (`MONTHLY` | `QUARTERLY` | `ANNUALLY` | `DAILY`).
- **Optional**: `account_id` (default current account); `name` / `name_prefix` (unique within account); `limit_amount` + `limit_unit` (no defaults stated); `time_period_start` / `time_period_end` (format `2017-01-01_12:00`; start defaults to start of the chosen period and must precede end; no end default documented); `cost_filter` (repeatable `name` + `values`, names include `Service`, `Region`, `TagKeyValue`, `CostCategory`…); `cost_types` (most `include_*` default `true`; `use_amortized`, `use_blended` default `false`); `filter_expression`; `metrics`; `notification` (repeatable); `planned_limit` (repeatable: `amount`, `start_time`, `unit` all required); `auto_adjust_data` (`auto_adjust_type` = `FORECAST` | `HISTORICAL`; `HISTORICAL` requires `historical_options.budget_adjustment_period`); `billing_view_arn`; `tags`.
- **notification**: required `comparison_operator`, `notification_type` (ACTUAL / FORECASTED), `threshold`, `threshold_type`; supply `subscriber_email_addresses` or `subscriber_sns_topic_arns`.
- **Conflicts (documented)**: `cost_filter` ⟂ `filter_expression`; `metrics` ⟂ `cost_types`; `filter_expression` requires `metrics` and vice-versa.
- **filter_expression rules**: exactly one root per block (`and`, `or`, `not`, `dimensions`, `tags`, `cost_categories`); "`and` and `or` require **at least 2 operands**", each its own block; max nesting depth 2; `ABSENT` not supported in `match_options`.
- **RI utilization example**: limit 100, `cost_types` defined, service cost filter.
- **Exports**: `arn`, `id`, `tags_all`, `auto_adjust_data.last_auto_adjust_time`, `historical_options.lookback_available_periods`.
- **Import**: `AccountID:BudgetName` (e.g. `123456789012:myBudget`), `import` block (TF >= 1.5) or CLI.

## 4. `aws_budgets_budget_action` [2]

- **Required**: `action_threshold` {`action_threshold_type` = `PERCENTAGE` | `ABSOLUTE_VALUE`, `action_threshold_value`}, `action_type` (`APPLY_IAM_POLICY` | `APPLY_SCP_POLICY` | `RUN_SSM_DOCUMENTS`), `approval_model` (`AUTOMATIC` | `MANUAL`), `budget_name`, `definition`, `execution_role_arn` (role for execution *and reversion*; roles and actions must be in the same account), `notification_type` (`ACTUAL` | `FORECASTED`), `subscriber` {`address`, `subscription_type` = `SNS` | `EMAIL`}.
- **Optional**: `account_id`, `tags`.
- **definition**: `iam_action_definition` {`policy_arn` req.; `groups`/`roles`/`users` optional, each ≥1 entry when set}; `scp_action_definition` {`policy_id`, `target_ids` req.}; `ssm_action_definition` {`action_sub_type` = `STOP_EC2_INSTANCES` | `STOP_RDS_INSTANCES`, `instance_ids`, `region` — all required}.
- No NOTE/WARNING blocks; no subscriber limit stated on the page.
- **Timeouts**: create/update/delete 5m. **Import**: `AccountID:ActionID:BudgetName`.
- AWS guidance: use the two AWS managed policies (user pass-role + budgets execution); stopping EC2 in an Auto Scaling group is ineffective unless a second action removes the launch role's permissions. [14]

## 5. Cost Anomaly Detection

### 5.1 `aws_ce_anomaly_monitor` [3]
- Required: `name`, `monitor_type` (`DIMENSIONAL` | `CUSTOM`). `monitor_dimension` required for DIMENSIONAL (`COST_CATEGORY` | `LINKED_ACCOUNT` | `SERVICE` | `TAG`); `monitor_specification` (JSON Expression string) required for CUSTOM. Optional `tags`.
- Import: monitor ARN (`id`), or `identity { arn }` (TF >= 1.12).

### 5.2 `aws_ce_anomaly_subscription` [4]
- Required: `name`, `frequency` (`DAILY` | `IMMEDIATE` | `WEEKLY`), `monitor_arn_list`, `subscriber` {`type` = `SNS` | `EMAIL`, `address`}. Optional: `account_id`, `threshold_expression`, `tags`.
- `threshold_expression` operators: `and`, `or`, `not`, `dimension`, `tags`, `cost_category`; dimension keys in examples: `ANOMALY_TOTAL_IMPACT_ABSOLUTE`, `ANOMALY_TOTAL_IMPACT_PERCENTAGE` (page's `key` description says "Unique name of the Cost Category" — doc copy-paste error, M3).
- No deprecated numeric `threshold` argument appears on the current page.
- SNS example grants `Service` principal `costalerts.amazonaws.com`.
- Import: subscription ARN, or `identity { arn }` (TF >= 1.12).

### 5.3 Quotas (AWS) [15]
AWS managed monitors: 1 for AWS services per account; 2 total per management account; 5,000 values tracked each. Customer managed monitors: 500 per management account. Alert subscriptions: 100 per account; 10 email recipients and **1 SNS topic** per subscription; detection up to 24 h after usage; 10 days minimum history; analyzes Usage charge type and NetUnblendedCost only.

## 6. Cost allocation

### 6.1 `aws_ce_cost_category` [5]
- Required: `name`, `rule` (repeatable), `rule_version`. Optional: `default_value`, `effective_start` (billing start date; default first day of current month, e.g. `2022-11-01T00:00:00Z`), `split_charge_rule` (`parameter` required only for `FIXED`), `tags`.
- Import: cost category ARN, or `identity { arn }` (TF >= 1.12).

### 6.2 `aws_ce_cost_allocation_tag` [6]
- Required: `tag_key`, `status` (`Active` | `Inactive`). Exports `id` (= key), `type`.
- NOTE: "it can take up to 24 hours for the tag keys to appear on Cost Allocation tag page for activation." Page says nothing about destroy behaviour (U1).
- AWS: activation then takes up to a further 24 h; bulk API `UpdateCostAllocationTagsStatus`; `awsApplication` tag auto-activated and not counted against quota. [16]
- Import: tag key.
- Budgets' own tags are **not** cost-allocation tags ("AWS Budgets does not support tags for cost allocation"). [14]

## 7. Reporting exports

### 7.1 `aws_cur_report_definition` (legacy CUR) [7]
- NOTE: CUR "only available in `us-east-1` currently".
- Required: `report_name` (≤256 chars), `time_unit` (`DAILY` | `HOURLY` | `MONTHLY`), `format` (`textORcsv` | `Parquet`), `compression` (`GZIP` | `ZIP` | `Parquet`; Parquet ⇔ Parquet both ways), `additional_schema_elements` (`RESOURCES`, `SPLIT_COST_ALLOCATION_DATA`, `MANUAL_DISCOUNT_COMPATIBILITY`), `s3_bucket` (existing), `s3_region`, `s3_prefix` (required since 6.0 [10]; empty prefix makes the report non-editable in console), `additional_artifacts` (`REDSHIFT` | `QUICKSIGHT` | `ATHENA`; `ATHENA` must be alone and needs `report_versioning = "OVERWRITE_REPORT"`).
- Optional: `refresh_closed_reports`, `report_versioning` (`CREATE_NEW_REPORT` | `OVERWRITE_REPORT`), `tags`. Page does not mention a bucket policy.
- **S3 bucket policy (AWS)**: principal `billingreports.amazonaws.com`; `s3:GetBucketAcl` + `s3:GetBucketPolicy` on the bucket and `s3:PutObject` on `bucket/*`; conditions `aws:SourceArn = arn:aws:cur:us-east-1:${AccountId}:definition/*` and `aws:SourceAccount`. Changing the policy or bucket owner stops delivery; AWS recommends ACLs disabled. [11]
- Import: `report_name`.

### 7.2 `aws_bcmdataexports_export` (Data Exports / CUR 2.0) [8]
- Required: `export` {`name`, `data_query` {`query_statement`, optional `table_configurations`}, `destination_configurations.s3_destination` {`s3_bucket`, `s3_prefix`, `s3_region`, `s3_output_configurations` {`compression` GZIP|PARQUET, `format` TEXT_OR_CSV|PARQUET, `output_type` CUSTOM, `overwrite` CREATE_NEW_REPORT|OVERWRITE_REPORT}}, `refresh_cadence.frequency` = `SYNCHRONOUS` only}; optional `export.description`, `tags`.
- Caveat: if `table_configurations` is set, all its values must be set; for `COST_AND_USAGE_REPORT`, `BILLING_VIEW_ARN` is required.
- Timeouts: create 30m, update 30m. Import: export ARN or `identity { arn }`.
- AWS: "CUR 2.0 is the new and recommended way to receive your detailed AWS cost and usage data"; legacy CUR uses a different API action set. [17] Bucket policy principal `bcm-data-exports.amazonaws.com`, `s3:PutObject`, `ArnLike aws:SourceArn arn:aws:bcm-data-exports:us-east-1:…:export/*` + `aws:SourceAccount`; cross-account bucket delivery supported. [12] Billing/cost exports refresh up to once per day. [18]

## 8. `aws_savingsplans_savings_plan` (brief) [9]
- WARNING: a financial commitment; an active plan "cannot be cancelled or deleted" — only `queued` plans can be deleted; destroying an active plan only removes it from state.
- Required `savings_plan_offering_id`, `commitment` (hourly USD); optional `purchase_time`, `upfront_payment_amount` (required for All/Partial Upfront, omit for No Upfront), `tags`. Timeouts create/delete 30m. Import `sp-…` ID. Provider support is "best effort" (6.62.0 note) [13].
- The resource is named `aws_savingsplans_savings_plan`; `savingsplans_plan.html.markdown` returns 404.

## 9. AWS guidance, controls, quotas, pricing

**Best practices (AWS Budgets)** [14]:
- Prefer recurring budgets over fixed-period ones so alerts don't stop; custom-period budgets expire at end date (end ≤ 3 years after start).
- Billing data updates at least once per day; ACTUAL alerts fire once per budget period; FORECASTED alerts may fire repeatedly; forecasts need ~5 weeks of usage data.
- Alerts: up to **10 email addresses and one SNS topic per alert**.
- SNS: budget needs publish permission and subscriptions must be confirmed. Policy principal `budgets.amazonaws.com`, `SNS:Publish`, conditions `aws:SourceAccount` + `ArnLike aws:SourceArn arn:aws:budgets::<account-id>:*`; SNS topic must be in the **same account** (cross-account not supported); encrypted topics need a KMS key policy granting Budgets. [19]
- Use a dedicated role for programmatic Budgets API access; review budgets when a member account leaves the organization.

**Security Hub controls**: none — the controls reference contains no Budgets, Billing, Cost Explorer, CUR, Data Exports or Savings Plans control prefixes (full page scanned). [20] Related controls on dependencies (SNS, S3, IAM) belong to those units.

**Quotas** [15]: 2 free budgets with actions per account; 10 actions per budget; 100 budget actions per account; 20,000 budgets per management account; 150 budgets using a custom billing view; budget name chars `0-9 A-Z a-z space _.:/=+-%@`. Budget reports: 50 max, 50 budgets each.

**Pricing** [21]: budget monitoring and notifications free; first two action-enabled budgets free per month, then $0.10/day per action-enabled budget; budget reports $0.01 per delivered report.

**Legacy-file claims found wrong** (checklist only):
1. "First 2 budgets free; $0.01/day per additional budget; budget actions $0.10/day per action" — wrong: monitoring is free; $0.10/day applies per *action-enabled budget* beyond two [21].
2. "maximum 5 email subscribers per notification; maximum 10 SNS topics" — wrong: 10 emails + 1 SNS topic [14].
3. "500 monitors per account (customer managed)" — imprecise: 500 per *management* account [15].
4. `required_version ">= 1.9"`, `~> 6.0`, `dynamodb_table` backend — superseded (F1, F3, F7).
5. "Cost Anomaly Detection uses threshold_expression rather than deprecated numeric threshold fields" — no numeric threshold field appears on the current page (cannot confirm "deprecated" history; U2).
6. "SNS must be in the same region as the budget subscription" — AWS docs say same *account*; region not stated (U3).
7. Example `budgets.amazonaws.com` SNS grant lacked the documented `aws:SourceAccount`/`aws:SourceArn` conditions [19].

## 10. Unverified / medium-confidence items and coverage limits

- **U1** Behaviour of `aws_ce_cost_allocation_tag` on destroy (deactivate vs. no-op) — not documented. (unverified)
- **U2** Historical deprecation of a numeric `threshold` on anomaly subscriptions — not checked (only current page read). (unverified)
- **U3** Region co-location requirement between Budgets and SNS topics. (unverified)
- **U4** Legacy claim that cost allocation tags must be activated from the management/payer account — not stated on [6] or [16]. (unverified)
- **U5** Cost Explorer API per-request pricing ($0.01) — not read. (unverified)
- **M1** CUR: configure provider for `us-east-1` — inferred from the TF page NOTE + AWS policy ARN (medium confidence).
- **M2** Data Exports home region us-east-1 — inferred only from the AWS bucket-policy ARN; TF page states no requirement (medium confidence).
- **M3** `threshold_expression.dimension.key` description on [4] appears copy-pasted from cost category (medium confidence it is a doc error).
- **L1** CHANGELOG read in two windows (chars 0–200,000); the second window started mid-6.54.0, so early 6.54.0 entries may be unseen.
- **L2** Cost Optimization Hub and Billing resources (e.g. `aws_costoptimizationhub_*`, billing views) not covered — out of brief scope.
- **L3** Data sources (`data.aws_budgets_budget`, `data.aws_ce_*`) not covered.

## 11. Security note

No prompt-injection or instruction-like text was observed in any fetched page.

## Source Bibliography

All read 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/budgets_budget_action.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_monitor.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_anomaly_subscription.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_category.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ce_cost_allocation_tag.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cur_report_definition.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/bcmdataexports_export.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
11. https://docs.aws.amazon.com/cur/latest/userguide/cur-s3.html
12. https://docs.aws.amazon.com/cur/latest/userguide/dataexports-s3-bucket.html
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
14. https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html
15. https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html
16. https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html
17. https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html
18. https://docs.aws.amazon.com/cur/latest/userguide/dataexports-create-standard.html
19. https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-sns-policy.html
20. https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html
21. https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (via F14)
