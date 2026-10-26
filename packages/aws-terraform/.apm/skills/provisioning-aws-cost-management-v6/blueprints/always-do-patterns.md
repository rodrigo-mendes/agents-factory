# Always-Do Patterns — provisioning-aws-cost-management-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL (or documented rules) and cites its
official source (read 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-budgets](./always-do-budgets.md#1-terraform-block-and-s3-backend) |
| 2 | Budget with notifications (no `region`) | [always-do-budgets](./always-do-budgets.md#2-budget-with-notifications) |
| 3 | Budget filter rules (`filter_expression`, `metrics`, operands) | [always-do-budgets](./always-do-budgets.md#3-budget-filter-rules) |
| 4 | SNS topic policy for Budgets with source conditions | [always-do-budgets](./always-do-budgets.md#4-sns-topic-policy-for-budgets) |
| 5 | Budget action (IAM and SSM definitions, same-account role) | [always-do-budgets](./always-do-budgets.md#5-budget-action) |
| 6 | Anomaly monitor (`DIMENSIONAL` / `CUSTOM`) | [always-do-cost-intelligence](./always-do-cost-intelligence.md#6-anomaly-monitor) |
| 7 | Anomaly subscription | [always-do-cost-intelligence](./always-do-cost-intelligence.md#7-anomaly-subscription) |
| 8 | Cost category | [always-do-cost-intelligence](./always-do-cost-intelligence.md#8-cost-category) |
| 9 | Cost allocation tag | [always-do-cost-intelligence](./always-do-cost-intelligence.md#9-cost-allocation-tag) |
| 10 | Legacy CUR report with `s3_prefix` and bucket policy | [always-do-reporting-commitments](./always-do-reporting-commitments.md#10-legacy-cur-report) |
| 11 | Data Exports (`SYNCHRONOUS` refresh) | [always-do-reporting-commitments](./always-do-reporting-commitments.md#11-data-exports) |
| 12 | Savings Plan (`aws_savingsplans_savings_plan`) | [always-do-reporting-commitments](./always-do-reporting-commitments.md#12-savings-plan) |
