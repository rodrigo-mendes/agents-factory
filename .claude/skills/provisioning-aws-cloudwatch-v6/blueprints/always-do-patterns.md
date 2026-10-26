# Always-Do Patterns — provisioning-aws-cloudwatch-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-14).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-s3-backend) |
| 2 | Log group with `retention_in_days` and `deletion_protection_enabled` | [always-do-foundation](./always-do-foundation.md#2-log-group-with-retention-and-deletion-protection) |
| 3 | Metric alarm with `alarm_actions` and `actions_enabled` (CloudWatch.15/17) | [always-do-alarms](./always-do-alarms.md#3-metric-alarm-with-required-actions) |
| 4 | Composite alarm with `trimspace()` on `alarm_rule` | [always-do-alarms](./always-do-alarms.md#4-composite-alarm-with-trimspace) |
| 5 | CIS metric filter + metric alarm pattern (CloudWatch.1–14) | [always-do-alarms](./always-do-alarms.md#5-cis-metric-filter-and-alarm-pattern) |
| 6 | Subscription filter with recursion guard and confused-deputy conditions | [always-do-security](./always-do-security.md#6-subscription-filter-with-recursion-guard) |
| 7 | Data protection policy (`aws_cloudwatch_log_data_protection_policy`) | [always-do-security](./always-do-security.md#7-data-protection-policy) |
| 8 | `terraform test` with `mock_provider` and CI commands | [always-do-security](./always-do-security.md#8-terraform-test-and-ci) |
