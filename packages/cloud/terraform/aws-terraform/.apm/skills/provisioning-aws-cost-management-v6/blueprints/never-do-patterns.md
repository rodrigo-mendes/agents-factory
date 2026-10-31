# Never-Do Patterns — provisioning-aws-cost-management-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (read 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `region` on a Cost Management resource | [never-do-budgets-and-region](./never-do-budgets-and-region.md#1-region-argument-on-cost-management-resources) |
| `cost_filter` with `filter_expression`, `metrics` with `cost_types` | [never-do-budgets-and-region](./never-do-budgets-and-region.md#2-mixing-conflicting-budget-arguments) |
| `and`/`or` with fewer than 2 operands | [never-do-budgets-and-region](./never-do-budgets-and-region.md#3-fewer-than-two-operands-in-and-or-or) |
| Budget tags expected to act as cost allocation tags | [never-do-budgets-and-region](./never-do-budgets-and-region.md#4-budget-tags-as-cost-allocation-tags) |
| `execution_role_arn` from another account | [never-do-budgets-and-region](./never-do-budgets-and-region.md#5-execution-role-in-another-account) |
| CUR without `s3_prefix` (required since 6.0) | [never-do-reporting-migration](./never-do-reporting-migration.md#1-cur-without-s3_prefix) |
| `ATHENA` with other artifacts or without `OVERWRITE_REPORT` | [never-do-reporting-migration](./never-do-reporting-migration.md#2-athena-artifact-misuse) |
| `terraform destroy` to cancel an active Savings Plan | [never-do-reporting-migration](./never-do-reporting-migration.md#3-destroying-an-active-savings-plan) |
| Pinning withdrawn provider 6.57.0 | [never-do-reporting-migration](./never-do-reporting-migration.md#4-pinning-version-6570) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-reporting-migration](./never-do-reporting-migration.md#5-s3-backend-with-dynamodb_table) |
